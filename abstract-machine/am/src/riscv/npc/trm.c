#include <am.h>
#include <klib-macros.h>

extern char _heap_start, _bss_start, _sidata, _sdata, _edata;
int main(const char *args);

extern char _pmem_start;
#define PMEM_SIZE (128 * 1024 * 1024)
#define PMEM_END  ((uintptr_t)&_pmem_start + PMEM_SIZE)

Area heap = RANGE(&_heap_start, PMEM_END);
#ifndef MAINARGS
#define MAINARGS ""
#endif
static const char mainargs[] = MAINARGS;

void putch(char ch) {
  *(volatile char *)(0x10000000L) = ch;
}

void halt(int code) {
  asm volatile("mv a0, %0; ebreak" : :"r"(code));
  while (1);
}

void loader() {
  char *src = &_sidata;
  char *dst = &_sdata;
  while (dst < &_edata) {
        *dst++ = *src++;
  }
  char *bss_start = &_bss_start;
  char *bss_end = &_heap_start;
  while (bss_start < bss_end){
    *bss_start++ = (char)0;
  }
}

void _trm_init() {
  loader();
  int ret = main(mainargs);
  halt(ret);
}
