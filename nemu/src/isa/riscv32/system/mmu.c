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
#include <memory/vaddr.h>
#include <memory/paddr.h>

paddr_t isa_mmu_translate(vaddr_t vaddr, int len, int type) {
  // Sv39 three-level page table walk.
  //   VPN[2] = va[38:30], VPN[1] = va[29:21], VPN[0] = va[20:12], offset = va[11:0]
  uintptr_t satp = cpu.csr[4];
  assert(BITS(satp, 63, 60) == 8); // only Sv39 is used in PA

  // physical address of the root page directory
  uintptr_t pte_addr = BITS(satp, 43, 0) << 12;
  uintptr_t vpn[3] = {
    BITS(vaddr, 38, 30),
    BITS(vaddr, 29, 21),
    BITS(vaddr, 20, 12),
  };

  uintptr_t pte = 0;
  for (int i = 0; i < 3; i ++) {
    pte_addr += vpn[i] * 8;
    pte = paddr_read(pte_addr, 8);
    assert(pte & 0x1); // the present (V) bit must be set
    pte_addr = BITS(pte, 53, 10) << 12; // PPN -> next-level page table / physical page
  }

  // the leaf PTE's PPN gives the physical page; OR in the page offset
  return (BITS(pte, 53, 10) << 12) | (vaddr & 0xfff);
}
