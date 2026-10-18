#include <am.h>
#include <klib.h>
#include <klib-macros.h>

#if !defined(__ISA_NATIVE__) || defined(__NATIVE_USE_KLIB__)
static unsigned long int next = 1;

int rand(void) {
  // RAND_MAX assumed to be 32767
  next = next * 1103515245 + 12345;
  return (unsigned int)(next/65536) % 32768;
}

void srand(unsigned int seed) {
  next = seed;
}

int abs(int x) {
  return (x < 0 ? -x : x);
}

int atoi(const char* nptr) {
  int x = 0;
  while (*nptr == ' ' || (*nptr >= '\t' && *nptr <= '\r')) { nptr ++; }
  int negative = (*nptr == '-');
  if (*nptr == '+' || *nptr == '-') { nptr ++; }
  // Accumulate negatively so INT_MIN does not require a positive int value.
  while (*nptr >= '0' && *nptr <= '9') {
    x = x * 10 - (*nptr - '0');
    nptr ++;
  }
  return negative ? x : -x;
}

void *malloc(size_t size) {
  // On native, malloc() will be called during initializaion of C runtime.
  // Therefore do not call panic() here, else it will yield a dead recursion:
  //   panic() -> putchar() -> (glibc) -> malloc() -> panic()
#if !(defined(__ISA_NATIVE__) && defined(__NATIVE_USE_KLIB__))
  uintptr_t start = (uintptr_t)heap.start, end = (uintptr_t)heap.end;
  const size_t alignment = _Alignof(max_align_t);
  size_t padding = (alignment - start % alignment) % alignment;
  if (start > end || padding > end - start) { return NULL; }
  uintptr_t addr = start + padding;
  if (size > end - addr) { return NULL; }
  // nanos new_page() shares heap.start; publish only a successful allocation.
  heap.start = (void *)(addr + size);
  return (void *)addr;
#endif
  return NULL;
}

void free(void *ptr) {
}

#endif
