// ============================================================================
// trace.cpp —— cachesim trace 导出的 DPI-C 落点（由 perf_counters.sv 的 DPI import 调用）。
// 仅当环境变量 CACHESIM_TRACE 设置了目标文件路径时才逐行落盘，否则 no-op（不影响其它仿真）。
// 每行: F <pc> / R <addr> / W <addr>，交给 npc/verif/cachesim 回放做设计空间探索。
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
