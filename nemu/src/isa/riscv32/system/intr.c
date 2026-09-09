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

word_t isa_raise_intr(word_t NO, vaddr_t epc) {
  /* TODO: Trigger an interrupt/exception with ``NO''.
   * Then return the address of the interrupt/exception vector.
   */
  word_t mie = BITS(cpu.csr[1],3,3);
  cpu.csr[0] = epc;
  // trap entry: set MPP = current privilege, MPIE = MIE, then clear MIE
  cpu.csr[1] = (cpu.csr[1] & ~0x1888ul) | (cpu.priv << 11) | (mie << 7);
  cpu.csr[2] = NO;// mcause = NO
  cpu.priv = 3; // the trap handler always runs in M mode
  IFDEF(CONFIG_ETRACE, Log("etrace: ecall/epc=0x%lx NO=0x%lx vector=0x%lx", epc, NO, cpu.csr[3]));
  return cpu.csr[3];
}

word_t isa_query_intr() {
  // deliver the timer interrupt only when the INTR line is raised and interrupts
  // are enabled (mstatus.MIE). The only interrupt in PA is the timer.
  if (cpu.INTR && BITS(cpu.csr[1], 3, 3)) {
    cpu.INTR = false;
    return 0x8000000000000007; // IRQ_TIMER for riscv64
  }
  return INTR_EMPTY;
}
