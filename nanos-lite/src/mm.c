#include <memory.h>
#include <proc.h>

static void *pf = NULL;

void* new_page(size_t nr_page) {
  void *p = pf;
  pf += nr_page * PGSIZE;
  return p;
}

#ifdef HAS_VME
static void* pg_alloc(int n) {
  void *p = new_page(n / PGSIZE);
  memset(p, 0, n);
  return p;
}
#endif

void free_page(void *p) {
  panic("not implement yet");
}

/* The brk() system call handler. */
int mm_brk(uintptr_t brk) {
#ifdef HAS_VME
  if (brk > current->max_brk) {
    uintptr_t start = ROUNDUP(current->max_brk, PGSIZE);
    uintptr_t end = ROUNDUP(brk, PGSIZE);
    for (uintptr_t va = start; va < end; va += PGSIZE) {
      void *pa = new_page(1);
      map(&current->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);
    }
    current->max_brk = brk;
  }
#endif
  return 0;
}

void init_mm() {
  pf = (void *)ROUNDUP(heap.start, PGSIZE);
  Log("free physical pages starting from %p", pf);

#ifdef HAS_VME
  vme_init(pg_alloc, free_page);
#endif
}
