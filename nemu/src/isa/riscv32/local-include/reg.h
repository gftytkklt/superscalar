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

#ifndef __RISCV_REG_H__
#define __RISCV_REG_H__

#include <common.h>

#define MEPC 0x341
#define MSTATUS 0x300
#define MCAUSE 0x342
#define MTVEC 0x305
#define SATP 0x180
#define MSCRATCH 0x340
#ifdef CONFIG_RV64
#define SSTATUS 0x100
#define SIE 0x104
#define STVEC 0x105
#define SCOUNTEREN 0x106
#define SSCRATCH 0x140
#define SEPC 0x141
#define SCAUSE 0x142
#define STVAL 0x143
#define SIP 0x144
#define MISA 0x301
#define MEDELEG 0x302
#define MIDELEG 0x303
#define MIE 0x304
#define MCOUNTEREN 0x306
#define MTVAL 0x343
#define MIP 0x344
#define MVENDORID 0xf11
#define MARCHID 0xf12
#define MIMPID 0xf13
#define MHARTID 0xf14

// Preserve the first six indices: existing M-mode users and REF PC/GPR ABI rely
// on their layout. Supervisor CSRs are added after them; aliases use read/write.
enum {
  CSR_MEPC = 0, CSR_MSTATUS, CSR_MCAUSE, CSR_MTVEC, CSR_SATP,
  CSR_MSCRATCH, CSR_MEDELEG, CSR_MIDELEG, CSR_MIE, CSR_MIP,
  CSR_MTVAL, CSR_MCOUNTEREN, CSR_STVEC, CSR_SCOUNTEREN,
  CSR_SSCRATCH, CSR_SEPC, CSR_SCAUSE, CSR_STVAL, CSR_COUNT
};

#define MSTATUS_SIE  (1ull << 1)
#define MSTATUS_MIE  (1ull << 3)
#define MSTATUS_SPIE (1ull << 5)
#define MSTATUS_MPIE (1ull << 7)
#define MSTATUS_SPP  (1ull << 8)
#define MSTATUS_MPP  (3ull << 11)
#define MSTATUS_MPRV (1ull << 17)
#define MSTATUS_SUM  (1ull << 18)
#define MSTATUS_MXR  (1ull << 19)
#define MSTATUS_TVM  (1ull << 20)
#define MSTATUS_TW   (1ull << 21)
#define MSTATUS_TSR  (1ull << 22)

bool riscv_csr_read(uint32_t addr, word_t *value);
bool riscv_csr_write(uint32_t addr, word_t value);
bool riscv_csr_access(uint32_t addr, bool write);
word_t riscv_raise_exception(word_t cause, vaddr_t epc, word_t tval);
#endif

static inline int check_reg_idx(int idx) {
  IFDEF(CONFIG_RT_CHECK, assert(idx >= 0 && idx < MUXDEF(CONFIG_RVE, 16, 32)));
  return idx;
}

static inline int check_csr_idx(int idx) {
  IFDEF(CONFIG_RT_CHECK, assert(idx >= 0 && idx < 4096));
  int csr_idx;
  switch(idx){
    case MEPC: csr_idx=0;break;
    case MSTATUS: csr_idx=1;break;
    case MCAUSE: csr_idx=2;break;
    case MTVEC: csr_idx=3;break;
    case SATP: csr_idx=4;break;
    case MSCRATCH: csr_idx=5;break;
#ifdef CONFIG_RV64
    case MEDELEG: csr_idx=CSR_MEDELEG;break;
    case MIDELEG: csr_idx=CSR_MIDELEG;break;
    case MIE: csr_idx=CSR_MIE;break;
    case MIP: csr_idx=CSR_MIP;break;
    case MTVAL: csr_idx=CSR_MTVAL;break;
    case MCOUNTEREN: csr_idx=CSR_MCOUNTEREN;break;
    case STVEC: csr_idx=CSR_STVEC;break;
    case SCOUNTEREN: csr_idx=CSR_SCOUNTEREN;break;
    case SSCRATCH: csr_idx=CSR_SSCRATCH;break;
    case SEPC: csr_idx=CSR_SEPC;break;
    case SCAUSE: csr_idx=CSR_SCAUSE;break;
    case STVAL: csr_idx=CSR_STVAL;break;
#endif
    default: panic("csr idx %x is not implemented!\n",idx);
  }
  return csr_idx;
}

#define gpr(idx) (cpu.gpr[check_reg_idx(idx)])
#define csr(idx) (cpu.csr[check_csr_idx(idx)])

static inline const char* reg_name(int idx) {
  extern const char* regs[];
  return regs[check_reg_idx(idx)];
}

#endif
