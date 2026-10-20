#include <memory.h>
#include <proc.h>

void* new_page(size_t nr_page) {
  uintptr_t cursor = (uintptr_t)heap.start;
  uintptr_t limit = (uintptr_t)heap.end;
  if (cursor > UINTPTR_MAX - (PGSIZE - 1)) return NULL;
  uintptr_t start = (cursor + PGSIZE - 1) & ~(uintptr_t)(PGSIZE - 1);
  if (start > limit || nr_page > (limit - start) / PGSIZE) return NULL;
  if (nr_page != 0) heap.start = (void *)(start + nr_page * PGSIZE);
  return (void *)start;
}

#ifdef HAS_VME
// Optional internal AM preflight; the supported NEMU Sv39 target counts exactly.
extern size_t __am_map_table_pages(AddrSpace *, uintptr_t, uintptr_t)
  __attribute__((weak));
static uintptr_t table_next, table_end;

static void* pg_alloc(int n) {
  panic_on(n <= 0 || n % PGSIZE != 0, "Invalid page allocation size");
  void *p;
  if (table_end != 0) {
    // mm_brk reserved the entire transaction before touching any PTE.
    panic_on(table_next > table_end || (uintptr_t)n > table_end - table_next,
             "Page table reservation exhausted");
    p = (void *)table_next;
    table_next += n;
  } else {
    p = new_page((size_t)n / PGSIZE);
    panic_on(p == NULL, "Out of physical pages");
  }
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
  if (current == NULL) return -1;
  uintptr_t lo = (uintptr_t)current->as.area.start;
  uintptr_t hi = (uintptr_t)current->as.area.end;
  if (hi < lo || hi - lo < STACK_SIZE) return -1;
  uintptr_t limit = hi - STACK_SIZE;
  if (current->brk_start < lo || current->brk_start > limit ||
      current->max_brk < current->brk_start || current->max_brk > limit ||
      brk < current->brk_start || brk > limit ||
      brk > UINTPTR_MAX - (PGSIZE - 1) ||
      current->max_brk > UINTPTR_MAX - (PGSIZE - 1)) return -1;
  if (brk > current->max_brk) {
    uintptr_t start = ROUNDUP(current->max_brk, PGSIZE);
    uintptr_t end = ROUNDUP(brk, PGSIZE);
    if (end > limit) return -1;
    size_t pages = (end - start) / PGSIZE;
    if (pages == 0) {
      current->max_brk = brk;
      return 0;
    }
    if (pages > SIZE_MAX / 4) return -1;
    // Other existing AM targets have at most three intermediate table levels.
    size_t tables = __am_map_table_pages ?
      __am_map_table_pages(&current->as, start, end) : 3 * pages;
    if (tables > SIZE_MAX - pages) return -1;
    void *data = new_page(pages + tables);
    if (data == NULL) return -1;
    table_next = (uintptr_t)data + pages * PGSIZE;
    table_end = table_next + tables * PGSIZE;
    for (uintptr_t va = start; va < end; va += PGSIZE) {
      void *pa = (void *)((uintptr_t)data + (va - start));
      map(&current->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);
    }
    heap.start = (void *)table_next;  // release any unused conservative budget
    table_next = table_end = 0;
    current->max_brk = brk;
  }
#endif
  return 0;
}

void init_mm() {
  void *first = new_page(0);
  panic_on(first == NULL, "Invalid physical heap");
  Log("free physical pages starting from %p", first);

#ifdef HAS_VME
  vme_init(pg_alloc, free_page);
#endif
}
