#include <am.h>
#include <klib.h>

#ifndef __ISA_NATIVE__

void *__dso_handle = &__dso_handle;

// Completion-byte protocol for non-concurrent initialization. Synchronization
// across concurrent constructors is not supplied by this minimal runtime.
int __cxa_guard_acquire(uint64_t *guard) {
  return *(unsigned char *)guard == 0;
}

void __cxa_guard_release(uint64_t *guard) {
  *(unsigned char *)guard = 1;
}

int __cxa_atexit(void (*destructor)(void *), void *arg, void *dso) {
  assert(0);
  return -1;
}

#endif
