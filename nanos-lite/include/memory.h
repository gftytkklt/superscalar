#ifndef __MEMORY_H__
#define __MEMORY_H__

#include <common.h>

#ifndef PGSIZE
#define PGSIZE 4096
#endif

#define PG_ALIGN __attribute((aligned(PGSIZE)))

// NULL on overflow/exhaustion; failure and zero pages do not advance heap.start.
void* new_page(size_t);

/* The brk() system call handler. */
int mm_brk(uintptr_t brk);

#endif
