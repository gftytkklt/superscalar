/***************************************************************************************
* Copyright (c) 2014-2022 Zihao Yu, Nanjing University
*
* NEMU is licensed under Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*          http://license.coscl.org.cn/MulanPSL2
*
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
* EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
* MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
*
* See the Mulan PSL v2 for more details.
***************************************************************************************/

#include <isa.h>
#include "../local-include/reg.h"
#include <device/timer.h>

#ifdef CONFIG_RV64
static word_t trap_vector(word_t tvec, word_t cause) {
  word_t base = tvec & ~3ull;
  if ((cause >> 63) && (tvec & 3ull) == 1) {
    return base + 4 * (cause & ~(1ull << 63));
  }
  return base;
}

word_t riscv_raise_exception(word_t cause, vaddr_t epc, word_t tval) {
  word_t code = cause & ~(1ull << 63);
  bool interrupt = (cause >> 63) != 0;
  word_t delegation = interrupt ? csr(MIDELEG) : csr(MEDELEG);
  bool to_s = cpu.priv != 3 && code < 64 && ((delegation >> code) & 1);
  word_t status = csr(MSTATUS);

  if (to_s) {
    csr(SEPC) = epc & ~3ull;
    csr(SCAUSE) = cause;
    csr(STVAL) = tval;
    status = (status & ~(MSTATUS_SPP | MSTATUS_SPIE | MSTATUS_SIE)) |
             (cpu.priv == 1 ? MSTATUS_SPP : 0) |
             ((status & MSTATUS_SIE) ? MSTATUS_SPIE : 0);
    csr(MSTATUS) = status;
    cpu.priv = 1;
    IFDEF(CONFIG_ETRACE, Log("etrace: S trap epc=0x%lx cause=0x%lx", epc, cause));
    return trap_vector(csr(STVEC), cause);
  }

  csr(MEPC) = epc & ~3ull;
  csr(MCAUSE) = cause;
  csr(MTVAL) = tval;
  status = (status & ~(MSTATUS_MPP | MSTATUS_MPIE | MSTATUS_MIE)) |
           (cpu.priv << 11) |
           ((status & MSTATUS_MIE) ? MSTATUS_MPIE : 0);
  csr(MSTATUS) = status;
  cpu.priv = 3;
  IFDEF(CONFIG_ETRACE, Log("etrace: M trap epc=0x%lx cause=0x%lx", epc, cause));
  return trap_vector(csr(MTVEC), cause);
}

word_t isa_raise_intr(word_t NO, vaddr_t epc) {
  return riscv_raise_exception(NO, epc, 0);
}

word_t riscv_interrupt_pending(void) {
  // MTIP is a device input, not software-writable CSR storage. Other pending
  // bits include SSIP/STIP and any connected interrupt-controller inputs.
  word_t pending = csr(MIP) & ~(1ull << 7);
  if (nemu_timer_legacy() ? cpu.INTR : nemu_timer_mtip()) pending |= 1ull << 7;
  return pending;
}

word_t isa_query_intr() {
  word_t ready = riscv_interrupt_pending() & csr(MIE);
  static const unsigned priority[] = {11, 3, 7, 9, 1, 5};
  for (unsigned i = 0; i < sizeof(priority) / sizeof(priority[0]); i++) {
    unsigned cause = priority[i];
    word_t bit = 1ull << cause;
    if (!(ready & bit)) continue;
    bool delegated = (csr(MIDELEG) & bit) != 0;
    bool enabled = delegated
      ? (cpu.priv < 1 || (cpu.priv == 1 && (csr(MSTATUS) & MSTATUS_SIE)))
      : (cpu.priv < 3 || (cpu.priv == 3 && (csr(MSTATUS) & MSTATUS_MIE)));
    if (!enabled) continue;
    // Only the legacy one-shot latch is acknowledged here. MTIMER remains
    // asserted until software moves the comparison point into the future.
    if (cause == 7 && nemu_timer_legacy()) cpu.INTR = false;
    return (1ull << 63) | cause;
  }
  return INTR_EMPTY;
}
#else
word_t isa_raise_intr(word_t NO, vaddr_t epc) {
  word_t mie = BITS(cpu.csr[1],3,3);
  cpu.csr[0] = epc;
  cpu.csr[1] = (cpu.csr[1] & ~0x1888ul) | (cpu.priv << 11) | (mie << 7);
  cpu.csr[2] = NO;
  cpu.priv = 3;
  IFDEF(CONFIG_ETRACE, Log("etrace: ecall/epc=0x%lx NO=0x%lx vector=0x%lx", epc, NO, cpu.csr[3]));
  return cpu.csr[3];
}

word_t isa_query_intr() {
  if (cpu.INTR && BITS(cpu.csr[1], 3, 3)) {
    cpu.INTR = false;
    return 0x8000000000000007;
  }
  return INTR_EMPTY;
}
#endif
