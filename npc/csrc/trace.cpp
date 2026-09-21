// ============================================================================
// trace.cpp —— cachesim trace / 性能计数器快照 导出的 DPI-C 落点（由 perf_counters.sv 调用）。
// 仅当环境变量设置了目标文件路径时才落盘，否则 no-op（不影响其它仿真）：
//   CACHESIM_TRACE  : 逐行 F <pc> / R <addr> / W <addr>（cachesim 回放用）
//   PERF_CTR_TRACE  : 每 10 万周期一行性能计数器 CSV（讲义"性能计数器的trace"，绘图用）
// ============================================================================
#include <cstdio>
#include <cstdlib>

static FILE* tb = nullptr;
static bool tb_on() {
  static int init = -1;
  if (init < 0) {
    init = 0;
    const char* p = getenv("CACHESIM_TRACE");
    if (p && *p) {
      tb = fopen(p, "w");
      if (tb) { setvbuf(tb, nullptr, _IOLBF, 0); init = 1; }
    }
  }
  return init == 1 && tb;
}

extern "C" void csim_ifetch(int pc)  { if (tb_on()) fprintf(tb, "F %08x\n", (unsigned)pc); }
extern "C" void csim_dread(int addr) { if (tb_on()) fprintf(tb, "R %08x\n", (unsigned)addr); }
extern "C" void csim_dwrite(int addr){ if (tb_on()) fprintf(tb, "W %08x\n", (unsigned)addr); }

// ---- 性能计数器周期快照（CSV，首行表头） ----
static FILE* ct = nullptr;
static bool ct_on() {
  static int init = -1;
  if (init < 0) {
    init = 0;
    const char* p = getenv("PERF_CTR_TRACE");
    if (p && *p) {
      ct = fopen(p, "w");
      if (ct) {
        setvbuf(ct, nullptr, _IOLBF, 0);
        fprintf(ct, "cycle,retire,deliver,decode,exu,ifu_miss,lsu,bubble,mem,csr,branch,compute,other,lsu_lat,st_lat\n");
        init = 1;
      }
    }
  }
  return init == 1 && ct;
}

extern "C" void ctr_snap(unsigned long long cyc, unsigned long long retire,
                         unsigned long long deliver, unsigned long long decode,
                         unsigned long long exu, unsigned long long ifu_miss,
                         unsigned long long lsu, unsigned long long bubble,
                         unsigned long long mem, unsigned long long csr,
                         unsigned long long branch, unsigned long long compute,
                         unsigned long long other, unsigned long long lsu_lat,
                         unsigned long long st_lat) {
  if (ct_on())
    fprintf(ct, "%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu,%llu\n",
            cyc, retire, deliver, decode, exu, ifu_miss, lsu, bubble,
            mem, csr, branch, compute, other, lsu_lat, st_lat);
}
