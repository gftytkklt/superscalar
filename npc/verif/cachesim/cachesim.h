#ifndef YSYX_CACHESIM_H
#define YSYX_CACHESIM_H
// ============================================================================
// cachesim.h —— 参数化 cache 模拟器（元数据 only，不存数据）。
// 面向"一生一芯 B3 性能分析"：用 trace 判定命中率；按访存区间 + 缺失行为参数化
// 计算 refill / 写回(脏块) / MMIO 直达 延迟，累积 TMT / AMAT。
//
// 约束（由构造/配置保证，见 make_cache_from_srams()）：
//   缓存总量 8KB = 8 × (128bit×64) SRAM；每颗 = 16B(128bit) × 64 行 = 1KB；
//   分配/组织以整颗 SRAM 为单位：ways × block_size = 16 × SRAM_num，sets = 64。
//
// 成本模型（每区域可配置，本文件只做初值，测量/配置可校正）：
//   命中            : hit_lat（默认 2）
//   读缺失(缓存区)  : refill_cycles = base[reg] · (block_bytes / 32)   // refill 长度按块大小线性
//   写缺失(写分配)  : refill_cycles + (被替换块 dirty ? wb_cycles : 0)
//   wb_cycles       : wb_base[reg] · (block_bytes / 32)
//   非缓存区(MMIO)  : mmio_cycles[reg]
// 区域按地址：PSRAM [0x80000000,0x80400000) flash [0x30000000,0x40000000)
//             SDRAM [0xa0000000,0xa8000000) SRAM [0x0f000000,0x0f002000) 其它=MMIO
// ============================================================================
#include <cstdint>
#include <vector>
#include <string>
#include <cstdio>

namespace ysyx {

enum Region { R_SRAM=0, R_PSRAM, R_FLASH, R_SDRAM, R_MMIO, R_NUM };
enum OpType { OP_IFETCH=0, OP_READ, OP_WRITE };

// 每区域成本（单位：周期；块大小按 32B 基准；block>32 时按比例放大，block<32 时按比例缩小）
struct RegionCost {
  uint64_t base[5];     // 读 refill / 写 refill 基准（32B 时），按区域
  uint64_t wb[5];       // 脏块写回基准（32B 时），按区域
  uint64_t mmio[5];     // 非缓存区直达延迟，按区域
  uint64_t hit;         // 命中延迟
  // 默认初值来自当前 npc sim（microbench test）实测，可被配置覆盖
  RegionCost();
};

struct CacheParams {
  uint64_t block_bytes;   // cacheline 字节
  uint32_t sets;          // 行数(=2^set_bits，约束下=64)
  uint32_t ways;          // 路数
  bool     is_icache;     // icache 只读(无 dirty)
  RegionCost cost;
  CacheParams(uint64_t blk=32, uint32_t s=64, uint32_t w=2, bool ic=true)
    : block_bytes(blk), sets(s), ways(w), is_icache(ic) {}
};

// 按"8KB=8×1KB SRAM，整颗为单位"约束，用 SRAM 数构造一个合法 CacheParams。
// 返回 true 表示合法：ways*block_bytes == 16*nsram 且 sets==64。
bool make_cache_from_srams(int nsram, bool is_icache, uint64_t want_block,
                           uint32_t want_ways, CacheParams* out, std::string* err);

// 单条 trace 访问记录
struct Access {
  OpType op;      // IFETCH/READ/WRITE
  uint32_t addr;  // PC 或数据地址
  uint32_t asid;  // 未用，保留
  Access(OpType o, uint32_t a): op(o), addr(a), asid(0) {}
};

class Cache {
 public:
  Cache(const CacheParams& p);
  // 访问一次：返回所用周期（hit_lat / refill(+wb) / mmio）。同时更新 metadata。
  uint64_t access(OpType op, uint32_t addr);

  // 统计
  uint64_t hits() const { return hits_; }
  uint64_t misses() const { return misses_; }
  uint64_t mandatory_, capacity_, conflict_;   // 3C 近似统计
  uint64_t refill_cycles() const { return refill_cycles_; }
  uint64_t wb_cycles() const { return wb_cycles_; }
  uint64_t mmio_cycles() const { return mmio_cycles_; }
  uint64_t direct_cycles() const { return direct_cycles_; } // 命中
  // 额外停顿（不含命中延迟）：missing refill + 脏写回 + MMIO 直达 —— 这才是真正"内存拖慢"的部分
  uint64_t stall_cycles() const { return refill_cycles_ + wb_cycles_ + mmio_cycles_; }
  double hit_rate() const { return (hits_+misses_)? (double)hits_/(hits_+misses_) : 0.0; }
  uint64_t accesses() const { return hits_+misses_; }
  const CacheParams& params() const { return p_; }
  void print(FILE* f, const char* tag) const;

 private:
  CacheParams p_;
  struct Line { uint64_t tag; bool valid, dirty; Line(): tag(0), valid(false), dirty(false){} };
  std::vector<std::vector<Line> > cache_;   // [set][way]
  uint32_t set_mask_, tag_shift_;
  uint64_t hits_, misses_, refill_cycles_, wb_cycles_, mmio_cycles_, direct_cycles_;
  Region region_of(uint32_t addr) const;
  uint64_t refill_cost(uint32_t addr) const;  // 读 refill 周期
  uint64_t writeback_cost(uint32_t addr) const;
  uint64_t mmio_cost(uint32_t addr) const;
};

// 逐条回放 trace，更新 cache。thread/重放用。
uint64_t replay(Cache& c, const std::vector<Access>& tr);

} // namespace ysyx
#endif
