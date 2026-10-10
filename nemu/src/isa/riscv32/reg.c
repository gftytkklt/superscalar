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
#include "local-include/reg.h"
#include <device/timer.h>

const char *regs[] = {
  "$0", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
  "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
  "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
  "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"
};

const char *csrs[] = {
  "mepc", "mstatus", "mcause", "mtvec", "satp", "mscratch"
#ifdef CONFIG_RV64
  , "medeleg", "mideleg", "mie", "mip", "mtval", "mcounteren",
  "stvec", "scounteren", "sscratch", "sepc", "scause", "stval"
#endif
};

void isa_reg_display() {
  for(int i=0;i<32;i++){
    printf("%s: %lx ", regs[i], cpu.gpr[i]);
    if((i % 8) == 7){printf("\n");}
  }
  for (int i=0;i<(sizeof(csrs)/sizeof(char*));i++){
    printf("%s: %lx\n", csrs[i], cpu.csr[i]);
  }
}

word_t isa_reg_str2val(const char *s, bool *success) {
  char a[10];
  sscanf(s,"%s",a);
  if (!strcmp(a,"pc")){*success = true;return cpu.pc;}
  for (int i=0;i<(sizeof(regs)/sizeof(char*));i++){
    if (!strcmp(a,regs[i])){*success = true;return cpu.gpr[i];}
  }
  printf("invalid reg name\n");
  *success = false;
  return 0;
}

#ifdef CONFIG_RV64
// RV64 M/S CSR subset used by the staged Linux bring-up. Unimplemented CSRs
// raise illegal-instruction traps instead of aborting the host emulator.
#define SSTATUS_WRITE_MASK (MSTATUS_SIE | MSTATUS_SPIE | MSTATUS_SPP | \
                            MSTATUS_SUM | MSTATUS_MXR)
#define SSTATUS_READ_MASK (SSTATUS_WRITE_MASK | (3ull << 32))
#define MSTATUS_WRITABLE (MSTATUS_SIE | MSTATUS_MIE | MSTATUS_SPIE | \
                          MSTATUS_MPIE | MSTATUS_SPP | MSTATUS_MPP | \
                          MSTATUS_MPRV | MSTATUS_SUM | MSTATUS_MXR | \
                          MSTATUS_TVM | MSTATUS_TW | MSTATUS_TSR)
#define INTERRUPT_MASK ((1ull << 1) | (1ull << 3) | (1ull << 5) | \
                        (1ull << 7) | (1ull << 9) | (1ull << 11))
#define S_INTERRUPT_MASK ((1ull << 1) | (1ull << 5) | (1ull << 9))
#define EXCEPTION_DELEG_MASK ((1ull << 0) | (1ull << 1) | (1ull << 2) | \
  (1ull << 3) | (1ull << 4) | (1ull << 5) | (1ull << 6) | \
  (1ull << 7) | (1ull << 8) | (1ull << 9) | (1ull << 12) | \
  (1ull << 13) | (1ull << 15))
#define MISA_VALUE ((2ull << 62) | (1ull << 0) | (1ull << 8) | \
                    (1ull << 12) | (1ull << 18) | (1ull << 20)) // RV64 A/I/M/S/U

static bool csr_implemented(uint32_t addr) {
  switch (addr) {
    case SSTATUS: case SIE: case STVEC: case SCOUNTEREN:
    case SSCRATCH: case SEPC: case SCAUSE: case STVAL: case SIP: case SATP:
    case MSTATUS: case MISA: case MEDELEG: case MIDELEG: case MIE:
    case MTVEC: case MCOUNTEREN: case MSCRATCH: case MEPC: case MCAUSE:
    case MTVAL: case MIP: case MVENDORID: case MARCHID: case MIMPID:
    case MHARTID: case TIME:
      return true;
    default:
      return false;
  }
}

bool riscv_csr_access(uint32_t addr, bool write) {
  if (!csr_implemented(addr) || cpu.priv < ((addr >> 8) & 3)) return false;
  if (write && ((addr >> 10) & 3) == 3) return false;
  if (addr == TIME && cpu.priv < 3 && !(csr(MCOUNTEREN) & 2)) return false;
  if (addr == TIME && cpu.priv == 0 && !(csr(SCOUNTEREN) & 2)) return false;
  // TVM prevents S-mode from accessing satp; M-mode remains unrestricted.
  if (addr == SATP && cpu.priv == 1 && (csr(MSTATUS) & MSTATUS_TVM)) return false;
  return true;
}

bool riscv_csr_read(uint32_t addr, word_t *value) {
  if (!riscv_csr_access(addr, false)) return false;
  switch (addr) {
    case SSTATUS: *value = csr(MSTATUS) & SSTATUS_READ_MASK; break;
    case SIE: *value = csr(MIE) & csr(MIDELEG); break;
    case SIP: *value = riscv_interrupt_pending() & csr(MIDELEG); break;
    case MIP: *value = riscv_interrupt_pending(); break;
    case TIME: *value = nemu_timer_time(); break;
    case MISA: *value = MISA_VALUE; break;
    case MVENDORID: case MARCHID: case MIMPID: case MHARTID:
      *value = 0; break;
    default: *value = csr(addr); break;
  }
  return true;
}

bool riscv_csr_write(uint32_t addr, word_t value) {
  if (!riscv_csr_access(addr, true)) return false;
  switch (addr) {
    case SSTATUS:
      csr(MSTATUS) = (csr(MSTATUS) & ~SSTATUS_WRITE_MASK) |
                     (value & SSTATUS_WRITE_MASK);
      break;
    case SIE:
      csr(MIE) = (csr(MIE) & ~csr(MIDELEG)) | (value & csr(MIDELEG));
      break;
    case SIP:
      // Only SSIP is software writable in this staged device model.
      csr(MIP) = (csr(MIP) & ~(csr(MIDELEG) & 2ull)) |
                 (value & csr(MIDELEG) & 2ull);
      break;
    case MSTATUS: {
      word_t next = (csr(MSTATUS) & ~MSTATUS_WRITABLE) |
                    (value & MSTATUS_WRITABLE);
      // Privilege 2 is reserved. Choose U as the legal WARL value.
      if (((next & MSTATUS_MPP) >> 11) == 2) next &= ~MSTATUS_MPP;
      csr(MSTATUS) = next;
      break;
    }
    case MISA: break; // fixed supported ISA; writable CSR with WARL bits
    case MEDELEG: csr(MEDELEG) = value & EXCEPTION_DELEG_MASK; break;
    case MIDELEG: csr(MIDELEG) = value & S_INTERRUPT_MASK; break;
    case MIE: csr(MIE) = value & INTERRUPT_MASK; break;
    case MIP: csr(MIP) = (csr(MIP) & ~0x22ull) | (value & 0x22ull); break;
    case MTVEC: case STVEC:
      csr(addr) = (value & ~3ull) | ((value & 3ull) == 1 ? 1ull : 0ull);
      break;
    case MEPC: case SEPC: csr(addr) = value & ~3ull; break;
    case SATP:
      if ((value >> 60) == 0 || (value >> 60) == 8) csr(SATP) = value;
      break;
    default: csr(addr) = value; break;
  }
  return true;
}
#endif
