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

#ifndef __ISA_RISCV_H__
#define __ISA_RISCV_H__

#include <common.h>

typedef struct {
  word_t gpr[MUXDEF(CONFIG_RVE, 16, 32)];
  vaddr_t pc;
  word_t csr[MUXDEF(CONFIG_RV64, 18, 6)];
  word_t priv; // current privilege level (0 = U, 3 = M)
  bool INTR;
#ifdef CONFIG_RV64
  // Single-hart LR/SC reservation. An exact address/width match is required.
  vaddr_t lr_addr;
  uint8_t lr_len;
  bool lr_valid;
#endif
} MUXDEF(CONFIG_RV64, riscv64_CPU_state, riscv32_CPU_state);

// decode
typedef struct {
  union {
    uint32_t val;
  } inst;
} MUXDEF(CONFIG_RV64, riscv64_ISADecodeInfo, riscv32_ISADecodeInfo);

#ifdef CONFIG_RV64
int riscv64_mmu_check(vaddr_t vaddr, int len, int type);
#define isa_mmu_check(vaddr, len, type) riscv64_mmu_check(vaddr, len, type)
#else
// Preserve the RV32 pre-M1 path.
#define isa_mmu_check(vaddr, len, type) \
  (BITS(cpu.csr[4], 63, 60) ? MMU_TRANSLATE : MMU_DIRECT)
#endif

#endif
