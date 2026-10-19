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

#ifdef CONFIG_RV64
#include "../local-include/reg.h"

static void mmu_fault(VAddrFault *fault, int type, bool access, vaddr_t va) {
  static const int page_cause[] = {12, 13, 15};
  static const int access_cause[] = {1, 5, 7};
  fault->cause = access ? access_cause[type] : page_cause[type];
  fault->tval = va;
}

int riscv64_mmu_check(vaddr_t vaddr, int len, int type) {
  (void)vaddr;
  (void)len;
  word_t privilege = cpu.priv;
  if (type != MEM_TYPE_IFETCH && privilege == 3 && (csr(MSTATUS) & MSTATUS_MPRV))
    privilege = (csr(MSTATUS) & MSTATUS_MPP) >> 11;
  if (privilege == 3 || (csr(SATP) >> 60) == 0) return MMU_DIRECT;
  return MMU_TRANSLATE;
}

static bool rv64_translate(vaddr_t va, int type, bool update_dirty,
                           paddr_t *pa, VAddrFault *fault) {
  if (riscv64_mmu_check(va, 1, type) == MMU_DIRECT) {
    // Keep the full RV64 address until it is safe to use the physical ABI.
    if (va > (paddr_t)-1) {
      mmu_fault(fault, type, true, va);
      return false;
    }
    *pa = va;
    return true;
  }

  word_t upper = va >> 39;
  if (upper != ((va & (1ull << 38)) ? ((1ull << 25) - 1) : 0)) {
    mmu_fault(fault, type, false, va);
    return false;
  }

  word_t status = csr(MSTATUS);
  word_t privilege = cpu.priv;
  if (type != MEM_TYPE_IFETCH && privilege == 3 && (status & MSTATUS_MPRV))
    privilege = (status & MSTATUS_MPP) >> 11;

  word_t table = (csr(SATP) & ((1ull << 44) - 1)) << 12;
  for (int level = 2; level >= 0; level--) {
    word_t pte_addr = table + (((va >> (12 + 9 * level)) & 0x1ff) << 3);
    word_t pte;
    if (pte_addr > (paddr_t)-1 || !paddr_try_read_region(pte_addr, 8, &pte)) {
      mmu_fault(fault, type, true, va);
      return false;
    }
    bool valid = pte & 1, readable = pte & 2, writable = pte & 4;
    bool executable = pte & 8, user = pte & 16;
    if (!valid || (!readable && writable) || (pte >> 54) != 0) {
      mmu_fault(fault, type, false, va);
      return false;
    }
    if (!readable && !executable) {
      // Reserved U/A/D bits in a non-leaf PTE must be zero.
      if (level == 0 || (pte & ((1ull << 4) | (1ull << 6) | (1ull << 7)))) {
        mmu_fault(fault, type, false, va);
        return false;
      }
      table = ((pte >> 10) & ((1ull << 44) - 1)) << 12;
      continue;
    }

    word_t ppn = (pte >> 10) & ((1ull << 44) - 1);
    word_t lower_ppn_mask = level ? ((1ull << (level * 9)) - 1) : 0;
    if (ppn & lower_ppn_mask) {
      mmu_fault(fault, type, false, va);
      return false;
    }

    if ((privilege == 0 && !user) ||
        (privilege == 1 && user &&
         (type == MEM_TYPE_IFETCH || !(status & MSTATUS_SUM))) ||
        (type == MEM_TYPE_IFETCH && !executable) ||
        (type == MEM_TYPE_READ && !(readable || (executable && (status & MSTATUS_MXR)))) ||
        (type == MEM_TYPE_WRITE && !writable)) {
      mmu_fault(fault, type, false, va);
      return false;
    }

    word_t offset_mask = (1ull << (12 + 9 * level)) - 1;
    word_t full_pa = ((ppn << 12) & ~offset_mask) | (va & offset_mask);
    if (full_pa > (paddr_t)-1) {
      mmu_fault(fault, type, true, va);
      return false;
    }

    word_t updated = pte | (1ull << 6);
    if (update_dirty) updated |= 1ull << 7;
    if (updated != pte && !paddr_try_write_region(pte_addr, 8, updated)) {
      mmu_fault(fault, type, true, va);
      return false;
    }

    *pa = full_pa;
    return true;
  }

  mmu_fault(fault, type, false, va);
  return false;
}

bool riscv64_mmu_translate_checked(vaddr_t va, int type, paddr_t *pa, VAddrFault *fault) {
  return rv64_translate(va, type, false, pa, fault);
}

bool riscv64_mmu_mark_dirty(vaddr_t va, VAddrFault *fault) {
  paddr_t ignored;
  return rv64_translate(va, MEM_TYPE_WRITE, true, &ignored, fault);
}
#endif

paddr_t isa_mmu_translate(vaddr_t vaddr, int len, int type) {
#ifdef CONFIG_RV64
  paddr_t pa = 0;
  VAddrFault fault = {};
  bool ok = riscv64_mmu_translate_checked(vaddr, type, &pa, &fault);
  Assert(ok, "legacy RV64 translation failed at " FMT_WORD " cause=%lu",
         vaddr, fault.cause);
  return pa;
#else
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
#endif
}
