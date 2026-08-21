#ifndef __NAVY_H__
#define __NAVY_H__

#include <stdio.h>

// libam 采用 riscv 风格的 Context 布局（与 AM riscv 平台一致），
// 使 guest 可以通过 GPR1..GPRx / mepc 访问"陷入现场"。
#define NR_REGS 32

struct Context {
  union {
    void *pdir;
    struct { uintptr_t gpr[NR_REGS], mcause, mstatus, mepc, np; };
  };
};

#define GPR1 gpr[17]  // a7
#define GPR2 gpr[10]  // a0
#define GPR3 gpr[11]  // a1
#define GPR4 gpr[12]  // a2
#define GPRx gpr[10]  // a0

#endif