// ============================================================================
// cachesim main —— 读 trace、按 8KB/整颗SRAM 约束扫配置、算命中率与 TMT、推荐最优。
//
// 用法:
//   cachesim <trace>                        # 扫全部合法配置，打印排序 + 推荐
//   cachesim <trace> --i sram=4:blk=32:ways=2 --d sram=4:blk=32:ways=2   # 指定配置
// trace 格式（每行一种）:
//   F <hex_addr>   指令取指(PC)   -> icache
//   R <hex_addr>   数据读        -> dcache
//   W <hex_addr>   数据写        -> dcache
// 约束: icache_sram + dcache_sram == 8; 每 cache 内 ways*block == 16*sram, sets==64。
// 成本模型见 cachesim.cpp（RegionCost 初值=microbench 实测，可用 --set 覆盖）。
// ============================================================================
#include "cachesim.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <sstream>
#include <algorithm>

using namespace ysyx;

static bool line_is(const std::string& l, char t, uint32_t* os) {
  if (l.empty() || l[0]!=t) return false;
  return sscanf(l.c_str()+2, "%x", os)==1;
}

static std::vector<Access> load_trace(const char* path) {
  std::vector<Access> v;
  FILE* f=fopen(path,"r"); if(!f){perror(path); exit(1);} 
  std::string l; char line[256];
  uint32_t a; 
  while (fgets(line,sizeof line,f)) {
    l=line;
    if (line_is(l,'F',&a)) v.push_back(Access(OP_IFETCH,a));
    else if (line_is(l,'R',&a)) v.push_back(Access(OP_READ,a));
    else if (line_is(l,'W',&a)) v.push_back(Access(OP_WRITE,a));
  }
  fclose(f);
  return v;
}

// 从 "sram=N:blk=B:ways=W" 解析并构造 cache
static bool parse_cfg(const char* s, bool ic, CacheParams* out) {
  int sram=0; long long blk=32; int ways=2;
  std::istringstream ss(s); std::string tok;
  while (std::getline(ss,tok,':')) {
    if (tok.rfind("sram=",0)==0) sram=atoi(tok.c_str()+5);
    else if (tok.rfind("blk=",0)==0) blk=atoll(tok.c_str()+4);
    else if (tok.rfind("ways=",0)==0) ways=atoi(tok.c_str()+5);
  }
  std::string err; out->cost=RegionCost();
  if (!make_cache_from_srams(sram, ic, blk, ways, out, &err)){ 
    fprintf(stderr,"bad config '%s': %s\n",s,err.c_str()); return false; }
  return true;
}

static const CacheParams* baseline;
static bool matches_baseline(const CacheParams& p, bool ic) {
  // 当前实现基线: icache 4 颗/32B/2路 ; dcache 4 颗/32B/2路
  return (ic ? (p.block_bytes==32&&p.ways==2) : (p.block_bytes==32&&p.ways==2));
}

struct Result { int ni,nd; CacheParams pi,pd; uint64_t it,dt,tot,ti,td; double rate_i,rate_d; };
static bool bytot(const Result&a,const Result&b){ return a.tot<b.tot; }

int main(int argc,char**argv){
  if (argc<2){ fprintf(stderr,"usage: cachesim <trace> [--i cfg] [--d cfg] [--set r:base,wb,mmio]\n"); return 1; }
  std::vector<Access> tr = load_trace(argv[1]);
  // 分离 icache(F) 与 dcache(R/W) trace
  std::vector<Access> t_i, t_d;
  for (auto&a:tr) { if (a.op==OP_IFETCH) t_i.push_back(a); else t_d.push_back(a); }

  // 单配置模式：--i <cfg> --d <cfg>（用于 RTL 对账：打印完整统计含按区缺失）
  // --cal：使用 2026-09-21 校准成本集（r=3.5 实测缺失代价，口径见 PE_CACHESIM_DIFF 记录）
  const char* ci_s = nullptr; const char* cd_s = nullptr; bool cal = false;
  int total = 8; bool tsv = false;          // --total T：SRAM 总颗数（1KB/颗）；--tsv：机器可读输出
  for (int k=2;k<argc;k++) {
    if (!strcmp(argv[k],"--i") && k+1<argc) ci_s = argv[++k];
    else if (!strcmp(argv[k],"--d") && k+1<argc) cd_s = argv[++k];
    else if (!strcmp(argv[k],"--cal")) cal = true;
    else if (!strcmp(argv[k],"--total") && k+1<argc) total = atoi(argv[++k]);
    else if (!strcmp(argv[k],"--tsv")) tsv = true;
  }
  // 校准成本集（RTL 实测，r=3.5）：icache flash 4285 / sdram 1346；dcache psram 读 1676、
  // flash 读 4529、sdram 读 1370；wb psram 927 / sdram 63；MMIO sram 18 / 其它 7。
  auto apply_cal = [](CacheParams& p, bool ic) {
    RegionCost c;
    if (ic) { c.base[R_FLASH]=4285; c.base[R_PSRAM]=1676; c.base[R_SDRAM]=1346; c.hit=1; }
    else    { c.base[R_PSRAM]=1676; c.base[R_FLASH]=4529; c.base[R_SDRAM]=1370;
              c.base_w[R_PSRAM]=2244; c.base_w[R_SDRAM]=1422;   // 写缺失均含脏回写
              c.wb[R_PSRAM]=0; c.wb[R_SDRAM]=0; c.wb[R_FLASH]=0; c.hit=2; }
    c.mmio[R_SRAM]=18; c.mmio[R_MMIO]=7;
    p.cost=c;
  };
  if (ci_s && cd_s) {
    CacheParams pi, pd; pi.cost=RegionCost(); pd.cost=RegionCost();
    if (!parse_cfg(ci_s,true,&pi) || !parse_cfg(cd_s,false,&pd)) return 1;
    if (cal) { apply_cal(pi,true); apply_cal(pd,false); }
    Cache ci(pi), cd(pd);
    replay(ci,t_i); replay(cd,t_d);
    ci.print(stdout,"I"); cd.print(stdout,"D");
    printf("single-config: I_hit=%.3f%% D_hit=%.3f%%  TMT(refill+wb+mmio)=%llu\n",
      ci.hit_rate()*100.0, cd.hit_rate()*100.0,
      (unsigned long long)(ci.stall_cycles()+cd.stall_cycles()));
    return 0;
  }

  // 枚举合法配置
  std::vector<Result> results;
  for (int ni=1; ni<=total-1; ++ni) {
    int nd = total-ni;
    // icache block/ways 组合: ways*block==16*ni, block>=16 且 ni*16%block==0
    for (uint64_t blk=16; blk<=16*ni; blk+=16) if ((16ull*ni)%blk==0) {
      uint32_t ways = (uint32_t)(16ull*ni/blk);
      CacheParams pi; std::string e; pi.cost=RegionCost();
      if (cal) apply_cal(pi,true);
      if (!make_cache_from_srams(ni,true,blk,ways,&pi,&e)) continue;
      for (uint64_t bd=16; bd<=16*nd; bd+=16) if ((16ull*nd)%bd==0) {
        uint32_t wd=(uint32_t)(16ull*nd/bd);
        CacheParams pd; pd.cost=RegionCost();
        if (cal) apply_cal(pd,false);
        if (!make_cache_from_srams(nd,false,bd,wd,&pd,&e)) continue;
        Cache ci(pi), cd(pd);
        replay(ci,t_i); replay(cd,t_d);
        Result r; r.ni=ni; r.nd=nd; r.pi=pi; r.pd=pd;
        r.tot = ci.stall_cycles() + cd.stall_cycles();   // 仅额外停顿(refill+wb+mmio)
        r.it = ci.stall_cycles(); r.dt = cd.stall_cycles();
        r.rate_i=ci.hit_rate(); r.rate_d=cd.hit_rate();
        results.push_back(r);
      }
    }
  }
  if (results.empty()){ fprintf(stderr,"no valid config\n"); return 1; }
  std::sort(results.begin(),results.end(),bytot);

  // 找基线（当前实现: ic4/32/2 + dc4/32/2）
  uint64_t base_tot=0; const Result* base=NULL;
  for (auto&r:results) if (r.ni==4&&r.nd==4&&r.pi.block_bytes==32&&r.pi.ways==2&&r.pd.block_bytes==32&&r.pd.ways==2){ base=&r; base_tot=r.tot; }
  if (!base) { base=&results[0]; base_tot=base->tot; }
  double p_mem = 0.5947; // 基线内存相关占时（未校准，microbench 实测约 59.5%）

  if (tsv) {
    // 机器可读：total ni nd iblk iways dblk dways I_hit D_hit TMT
    for (auto&r:results)
      printf("TSV\t%d\t%d\t%d\t%llu\t%u\t%llu\t%u\t%.4f\t%.4f\t%llu\n",
        total,r.ni,r.nd,(unsigned long long)r.pi.block_bytes,r.pi.ways,
        (unsigned long long)r.pd.block_bytes,r.pd.ways,
        r.rate_i*100.0,r.rate_d*100.0,(unsigned long long)r.tot);
    return 0;
  }
  printf("=== cachesim sweep (trace=%zu: I=%zu D=%zu, total=%d SRAM) baseline I=4SRAM/32B/2W D=4SRAM/32B/2W  TMT=%llu ===\n",
         tr.size(),t_i.size(),t_d.size(),total,(unsigned long long)base_tot);
  printf("%-16s %-18s %-18s %8s %8s %8s %10s\n","cfg I/D","icache(blk/w)","dcache(blk/w)","I_hit","D_hit","TMT","vs_base");
  for (auto&r:results) {
    double s = base_tot? (double)base_tot/(double)r.tot : 1.0;
    double amd = 1.0/( (1-p_mem) + p_mem/s );
    printf("I%dSR/D%dSR %-18s %-18s %7.2f%% %7.2f%% %8llu  %7.3fx(Amdahl~%.2fx)\n",
      r.ni,r.nd, (std::to_string(r.pi.block_bytes)+"B/"+(std::to_string(r.pi.ways))+"w").c_str(),
      (std::to_string(r.pd.block_bytes)+"B/"+(std::to_string(r.pd.ways))+"w").c_str(),
      r.rate_i*100.0, r.rate_d*100.0, (unsigned long long)r.tot, s, amd);
  }
  printf("\n=== 推荐（TMT 最小）===\n");
  Result& best=results[0];
  double s = base_tot?(double)base_tot/(double)best.tot:1.0;
  double amd = 1.0/((1-p_mem)+p_mem/s);
  printf("icache %d SRAM, %lluB, %u way; dcache %d SRAM, %lluB, %u way\n",
    best.ni,(unsigned long long)best.pi.block_bytes,best.pi.ways,
    best.nd,(unsigned long long)best.pd.block_bytes,best.pd.ways);
  printf("icache hit=%.2f%%  dcache hit=%.2f%%  TMT=%llu (baseline %llu)  stall_ratio=%.3fx  Amdahl≈%.2fx\n",
    best.rate_i*100.0,best.rate_d*100.0,(unsigned long long)best.tot,(unsigned long long)base_tot,s,amd);
  return 0;
}
