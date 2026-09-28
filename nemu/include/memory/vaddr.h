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

#ifndef __MEMORY_VADDR_H__
#define __MEMORY_VADDR_H__

#include <common.h>

word_t vaddr_ifetch(vaddr_t addr, int len);
word_t vaddr_read(vaddr_t addr, int len);
void vaddr_write(vaddr_t addr, int len, word_t data);

#ifdef CONFIG_RV64
typedef struct {
  word_t cause;
  vaddr_t tval;
} VAddrFault;

// Explicit fault result for the RV64 CPU path. Legacy interfaces stay intact.
bool riscv64_mmu_translate_checked(vaddr_t va, int type, paddr_t *pa, VAddrFault *fault);
bool riscv64_mmu_mark_dirty(vaddr_t va, VAddrFault *fault);
bool vaddr_try_ifetch(vaddr_t addr, int len, word_t *data, VAddrFault *fault);
bool vaddr_try_read(vaddr_t addr, int len, word_t *data, VAddrFault *fault);
bool vaddr_try_amo_read(vaddr_t addr, int len, word_t *data, VAddrFault *fault);
bool vaddr_try_probe_write(vaddr_t addr, int len, VAddrFault *fault);
bool vaddr_try_write(vaddr_t addr, int len, word_t data, VAddrFault *fault);
#endif

#define PAGE_SHIFT        12
#define PAGE_SIZE         (1ul << PAGE_SHIFT)
#define PAGE_MASK         (PAGE_SIZE - 1)

#endif
