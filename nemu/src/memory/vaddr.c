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
#include <memory/paddr.h>
#include <memory/vaddr.h>

// FILE* itrace;
// FILE* dtrace;

word_t vaddr_ifetch(vaddr_t addr, int len) {
  // fprintf(itrace, "r %08lx\n", addr);
  if (isa_mmu_check(addr, len, MEM_TYPE_IFETCH) == MMU_TRANSLATE) {
    return paddr_read(isa_mmu_translate(addr, len, MEM_TYPE_IFETCH), len);
  }
  return paddr_read(addr, len);
}

word_t vaddr_read(vaddr_t addr, int len) {
  // fprintf(dtrace, "r %08lx\n", addr);
  if (isa_mmu_check(addr, len, MEM_TYPE_READ) == MMU_TRANSLATE) {
    return paddr_read(isa_mmu_translate(addr, len, MEM_TYPE_READ), len);
  }
  return paddr_read(addr, len);
}

void vaddr_write(vaddr_t addr, int len, word_t data) {
  // Any local store ends the single-hart reservation, including an AMO or SC.
#ifdef CONFIG_RV64
  cpu.lr_valid = false;
#endif
  // fprintf(dtrace, "w %08lx\n", addr);
  if (isa_mmu_check(addr, len, MEM_TYPE_WRITE) == MMU_TRANSLATE) {
    paddr_write(isa_mmu_translate(addr, len, MEM_TYPE_WRITE), len, data);
  } else {
    paddr_write(addr, len, data);
  }
}

#ifdef CONFIG_RV64
typedef struct {
  paddr_t pa;
  vaddr_t va;
  int len;
} RV64AccessPart;

static void rv64_access_fault(VAddrFault *fault, int type, vaddr_t va) {
  static const int cause[] = {1, 5, 7};
  fault->cause = cause[type];
  fault->tval = va;
}

static bool rv64_prepare_access(vaddr_t addr, int len, int type,
                                RV64AccessPart part[2], int *count,
                                VAddrFault *fault) {
  assert(len == 1 || len == 2 || len == 4 || len == 8);
  int first_len = PAGE_SIZE - (addr & PAGE_MASK);
  if (first_len > len) first_len = len;
  *count = first_len == len ? 1 : 2;
  part[0] = (RV64AccessPart){.va = addr, .len = first_len};
  if (*count == 2)
    part[1] = (RV64AccessPart){.va = addr + first_len, .len = len - first_len};

  for (int i = 0; i < *count; i++) {
    if (!riscv64_mmu_translate_checked(part[i].va, type, &part[i].pa, fault))
      return false;
    // Cross-page accesses are byte-wise in the interpreter. Reject an MMIO
    // target rather than changing a device callback's access width/side effects.
    bool mapped = *count == 1 ? paddr_try_access(part[i].pa, part[i].len)
                              : paddr_is_region(part[i].pa, part[i].len);
    if (!mapped) {
      rv64_access_fault(fault, type, part[i].va);
      return false;
    }
  }
  return true;
}

static bool rv64_try_read(vaddr_t addr, int len, int type,
                          word_t *data, VAddrFault *fault) {
  assert(len == 1 || len == 2 || len == 4 || len == 8);
  if ((addr & PAGE_MASK) + len <= PAGE_SIZE) {
    // A single checked read already validates the complete physical range.
    // There is no second page to preflight before touching the first one.
    paddr_t pa;
    if (!riscv64_mmu_translate_checked(addr, type, &pa, fault)) return false;
    if (paddr_try_read(pa, len, data)) return true;
    rv64_access_fault(fault, type, addr);
    return false;
  }

  RV64AccessPart part[2];
  int count;
  if (!rv64_prepare_access(addr, len, type, part, &count, fault)) return false;
  if (count == 1) {
    if (paddr_try_read(part[0].pa, len, data)) return true;
    rv64_access_fault(fault, type, addr);
    return false;
  }

  word_t value = 0;
  int shift = 0;
  for (int i = 0; i < count; i++) {
    for (int j = 0; j < part[i].len; j++, shift += 8) {
      word_t byte;
      bool ok = paddr_try_read_region(part[i].pa + j, 1, &byte);
      assert(ok); // preflight validated both registered-memory ranges
      value |= byte << shift;
    }
  }
  *data = value;
  return true;
}

bool vaddr_try_ifetch(vaddr_t addr, int len, word_t *data, VAddrFault *fault) {
  return rv64_try_read(addr, len, MEM_TYPE_IFETCH, data, fault);
}

bool vaddr_try_read(vaddr_t addr, int len, word_t *data, VAddrFault *fault) {
  return rv64_try_read(addr, len, MEM_TYPE_READ, data, fault);
}

bool vaddr_try_amo_read(vaddr_t addr, int len, word_t *data, VAddrFault *fault) {
  return rv64_try_read(addr, len, MEM_TYPE_WRITE, data, fault);
}

bool vaddr_try_probe_write(vaddr_t addr, int len, VAddrFault *fault) {
  RV64AccessPart part[2];
  int count;
  return rv64_prepare_access(addr, len, MEM_TYPE_WRITE, part, &count, fault);
}

bool vaddr_try_write(vaddr_t addr, int len, word_t data, VAddrFault *fault) {
  // Preserve P6's conservative single-hart rule for every attempted store.
  cpu.lr_valid = false;
  RV64AccessPart part[2];
  int count;
  if (!rv64_prepare_access(addr, len, MEM_TYPE_WRITE, part, &count, fault))
    return false;
  // Mark D only once all target pages and physical ranges have passed
  // preflight. A failed SC uses probe_write and never reaches this point.
  for (int i = 0; i < count; i++) {
    if (!riscv64_mmu_mark_dirty(part[i].va, fault)) return false;
  }
  if (count == 1) {
    if (paddr_try_write(part[0].pa, len, data)) return true;
    rv64_access_fault(fault, MEM_TYPE_WRITE, addr);
    return false;
  }

  int shift = 0;
  for (int i = 0; i < count; i++) {
    for (int j = 0; j < part[i].len; j++, shift += 8) {
      bool ok = paddr_try_write_region(part[i].pa + j, 1, data >> shift);
      assert(ok); // preflight validated both registered-memory ranges
    }
  }
  return true;
}
#endif
