#include "cachesim.h"
#include <cstring>
#include <cstdlib>

namespace ysyx {

RegionCost::RegionCost() {
  // 初值：来自当前 npc sim（microbench test）实测，可被配置覆盖（见 load_params）。
  // 已测：PSRAM 读refill 490 / 写refill 657(含脏回写) ；flash 读refill 1309；
  //      SRAM MMIO 直达 ≈8；其它 MMIO ≈4；SDRAM 无样本(暂取≈PSRAM)。
  for (int i=0;i<R_NUM;i++){ base[i]=0; wb[i]=0; mmio[i]=0; }
  base[R_PSRAM] = 490;  base[R_FLASH] = 1309; base[R_SDRAM] = 490;
  base[R_SRAM]  = 0;    base[R_MMIO]  = 0;
  wb[R_PSRAM]   = 167;  wb[R_FLASH]  = 1000; wb[R_SDRAM] = 167;
  wb[R_SRAM]    = 0;    wb[R_MMIO]   = 0;
  mmio[R_SRAM]  = 8;    mmio[R_MMIO]  = 4;    mmio[R_PSRAM]=mmio[R_FLASH]=mmio[R_SDRAM]=0;
  hit = 2;
}

bool make_cache_from_srams(int nsram, bool is_icache, uint64_t want_block,
                           uint32_t want_ways, CacheParams* out, std::string* err) {
  // 约束：ways*block_bytes == 16*nsram；sets==64；block 为 16 的倍数（整 SRAM 宽度）。
  uint64_t need = 16ull * nsram;
  if (err) err->clear();
  if (want_block < 16 || (want_block % 16) != 0) { if (err)*err="block must be >=16 and multiple of 16"; return false; }
  if (want_ways == 0) { if (err)*err="ways must >0"; return false; }
  // 允许调用方自由指定 block/ways，但必须满足 ways*block==16*nsram；否则报错提示合法组合。
  if (want_ways * want_block != need) {
    if (err) { char b[128]; snprintf(b,sizeof b,"ways*block(=%llu) != 16*nsram(=%llu); try (ways,block) among:",
      (unsigned long long)(want_ways*want_block),(unsigned long long)need); *err=b; }
    return false;
  }
  out->block_bytes = want_block;
  out->sets = 64;
  out->ways = want_ways;
  out->is_icache = is_icache;
  return true;
}

Cache::Cache(const CacheParams& p) : p_(p) {
  cache_.assign(p_.sets, std::vector<Line>(p_.ways));
  uint64_t off_bits = 0; { uint64_t b=p_.block_bytes; while(b>1){b>>=1; off_bits++;} }
  uint64_t set_bits = 0; { uint32_t s=p_.sets; while(s>1){s>>=1; set_bits++;} }
  set_mask_ = (1u<<set_bits)-1;
  tag_shift_ = off_bits + set_bits;
  hits_=misses_=refill_cycles_=wb_cycles_=mmio_cycles_=direct_cycles_=0;
  mandatory_=capacity_=conflict_=0;
}

Region Cache::region_of(uint32_t a) const {
  if (a>=0x80000000u && a<0x80400000u) return R_PSRAM;
  if (a>=0x30000000u && a<0x40000000u) return R_FLASH;
  if (a>=0xa0000000u && a<0xa8000000u) return R_SDRAM;
  if (a>=0x0f000000u && a<0x0f002000u) return R_SRAM;
  return R_MMIO;
}

uint64_t Cache::refill_cost(uint32_t addr) const {
  Region r = region_of(addr);
  double scale = (double)p_.block_bytes / 32.0;   // refill 长度按块大小比例
  return (uint64_t)((double)p_.cost.base[r] * scale);
}
uint64_t Cache::writeback_cost(uint32_t addr) const {
  Region r = region_of(addr);
  double scale = (double)p_.block_bytes / 32.0;
  return (uint64_t)((double)p_.cost.wb[r] * scale);
}
uint64_t Cache::mmio_cost(uint32_t addr) const {
  return p_.cost.mmio[region_of(addr)];
}

uint64_t Cache::access(OpType op, uint32_t addr) {
  Region r = region_of(addr);
  // 非缓存区（SRAM / 其它MMIO）：不缓存，直接访问。
  if (r==R_SRAM || r==R_MMIO) { mmio_cycles_ += mmio_cost(addr); return mmio_cost(addr); }

  uint64_t tag = addr >> tag_shift_;
  uint64_t off_bits=0,b=p_.block_bytes; while(b>1){b>>=1;off_bits++;}
  uint32_t set = (addr >> off_bits) & set_mask_;

  std::vector<Line>& s = cache_[set];
  // 命中
  int hit_way=-1;
  for (int w=0;w<(int)p_.ways;w++) if (s[w].valid && s[w].tag==tag) { hit_way=w; break; }
  if (hit_way>=0) {
    if (!p_.is_icache && op==OP_WRITE) s[hit_way].dirty=true;
    hits_++; direct_cycles_ += p_.cost.hit; return p_.cost.hit;
  }
  // 缺失
  misses_++;
  bool filled=false;
  int evict_way=0; bool evict_dirty=false; uint64_t evict_tag=0; bool evict_valid=false;
  int empty_way=-1;
  for (int w=0;w<(int)p_.ways;w++) if (!s[w].valid) { empty_way=w; break; }
  if (empty_way>=0) {
    mandatory_++; s[empty_way].tag=tag; s[empty_way].valid=true; s[empty_way].dirty=false;
    filled=true;
  } else {
    // 替换：选一个 way（此处用最简单的"命中时已更新时间戳"的伪 LRU：取第一个，即方式序）
    for (int w=0;w<(int)p_.ways;w++) { evict_way=w; }
    evict_dirty = s[evict_way].dirty; evict_tag=s[evict_way].tag; evict_valid=s[evict_way].valid;
    // 3C：全部 valid 且发生替换 → 容量或冲突。此处区分：若该 set 本来可多路放更多不同 tag 但被替换=conflict；
    // 简化：只要替换就计入 capacity（冲突判定见 explain）。
    capacity_++;
    if (evict_dirty && !p_.is_icache) { wb_cycles_ += writeback_cost(addr); }  // 脏块写回
    s[evict_way].tag=tag; s[evict_way].valid=true; s[evict_way].dirty=false;
  }
  (void)evict_tag;(void)evict_valid;
  // 写分配：缺失后置 dirty（写回语义）
  if (!p_.is_icache && op==OP_WRITE) {
    for (int w=0;w<(int)p_.ways;w++) if (s[w].valid && s[w].tag==tag) { s[w].dirty=true; break; }
  }
  uint64_t rc = refill_cost(addr);
  refill_cycles_ += rc;
  return rc;
}

uint64_t replay(Cache& c, const std::vector<Access>& tr) {
  uint64_t total=0;
  for (auto& a : tr) total += c.access(a.op, a.addr);
  return total;
}

void Cache::print(FILE* f, const char* tag) const {
  fprintf(f, "[%s] blk=%lluB sets=%u ways=%u  access=%llu hit=%llu miss=%llu rate=%.3f%% "
             "refill=%llu wb=%llu mmio=%llu direct=%llu total_costs=%llu\n",
    tag, (unsigned long long)p_.block_bytes, p_.sets, p_.ways,
    (unsigned long long)(hits_+misses_),(unsigned long long)hits_,(unsigned long long)misses_,
    hit_rate()*100.0,
    (unsigned long long)refill_cycles_,(unsigned long long)wb_cycles_,
    (unsigned long long)mmio_cycles_,(unsigned long long)direct_cycles_,
    (unsigned long long)(refill_cycles_+wb_cycles_+mmio_cycles_+direct_cycles_));
}

} // namespace ysyx
