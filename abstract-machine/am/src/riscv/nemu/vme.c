#include <am.h>
#include <nemu.h>
#include <klib.h>

static AddrSpace kas = {};
static void* (*pgalloc_usr)(int) = NULL;
static void (*pgfree_usr)(void*) = NULL;
static int vme_enable = 0;

static Area segments[] = {      // Kernel memory mappings
  NEMU_PADDR_SPACE
};

#define USER_SPACE RANGE(0x40000000, 0x80000000)

static inline void set_satp(void *pdir) {
  uintptr_t mode = 1ul << (__riscv_xlen - 1);
  asm volatile("csrw satp, %0" : : "r"(mode | ((uintptr_t)pdir >> 12)));
}

static inline uintptr_t get_satp() {
  uintptr_t satp;
  asm volatile("csrr %0, satp" : "=r"(satp));
  return satp << 12;
}

bool vme_init(void* (*pgalloc_f)(int), void (*pgfree_f)(void*)) {
  pgalloc_usr = pgalloc_f;
  pgfree_usr = pgfree_f;

  kas.ptr = pgalloc_f(PGSIZE);

  int i;
  for (i = 0; i < LENGTH(segments); i ++) {
    void *va = segments[i].start;
    for (; va < segments[i].end; va += PGSIZE) {
      map(&kas, va, va, 0);
    }
  }

  set_satp(kas.ptr);
  vme_enable = 1;

  return true;
}

void protect(AddrSpace *as) {
  PTE *updir = (PTE*)(pgalloc_usr(PGSIZE));
  as->ptr = updir;
  as->area = USER_SPACE;
  as->pgsize = PGSIZE;
  // map kernel space
  memcpy(updir, kas.ptr, PGSIZE);
}

void unprotect(AddrSpace *as) {
}

void __am_get_cur_as(Context *c) {
  // pdir == NULL marks a kernel-thread context (created by kcontext()).
  // Keep the marker so that __am_switch() does not switch the address space
  // when resuming a kernel thread (all address spaces share the kernel mapping).
  if (c->pdir == NULL) return;
  c->pdir = (vme_enable ? (void *)get_satp() : NULL);
}

void __am_switch(Context *c) {
  if (vme_enable && c->pdir != NULL) {
    set_satp(c->pdir);
  }
}

void map(AddrSpace *as, void *va, void *pa, int prot) {
  // Sv39 three-level page table: VPN[2]=va[38:30], VPN[1]=va[29:21], VPN[0]=va[20:12]
  uintptr_t vaddr = (uintptr_t)va;
  uintptr_t vpn[3] = {
    (vaddr >> 30) & 0x1ff,
    (vaddr >> 21) & 0x1ff,
    (vaddr >> 12) & 0x1ff,
  };

  PTE *pt[3];
  pt[0] = (PTE *)as->ptr;
  for (int i = 1; i < 3; i ++) {
    if (!(pt[i - 1][vpn[i - 1]] & PTE_V)) {
      PTE *pg = (PTE *)pgalloc_usr(PGSIZE);
      assert(pg != NULL);
      memset(pg, 0, PGSIZE);
      // store the next-level page table's physical page number in Sv39 PPN (bits 53:10)
      pt[i - 1][vpn[i - 1]] = (((uintptr_t)pg >> 12) << 10) | PTE_V;
    }
    pt[i] = (PTE *)((((pt[i - 1][vpn[i - 1]] >> 10) & 0xfffffffff) << 12));
  }

  // leaf entry: Sv39 PPN + R/W/X/U/A/D bits
  pt[2][vpn[2]] = (((uintptr_t)pa >> 12) << 10) | prot | PTE_V | PTE_R | PTE_W | PTE_X | PTE_U | PTE_A | PTE_D;
}

Context *ucontext(AddrSpace *as, Area kstack, void *entry) {
  Context *cp = (Context*)kstack.end - 1;
  // MPP = U mode, plus MXR/SUM (for DiffTest with the reference design)
  cp->mstatus = 0xa0000000 | MSTATUS_MXR | MSTATUS_SUM | MSTATUS_MPIE;
  cp->mepc = (uintptr_t)entry;
  cp->gpr[2] = (uintptr_t)kstack.end; // Navy _start will set sp from a0 anyway
  cp->np = USER_MODE;
  cp->pdir = (as ? as->ptr : NULL);
  return cp;
}
