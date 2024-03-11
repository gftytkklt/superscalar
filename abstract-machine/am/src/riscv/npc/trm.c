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

#define UART_BASE 0x10000000L
#define UART_THR UART_BASE + 0x00
#define UART_LDL UART_BASE + 0x00
#define UART_MDL UART_BASE + 0x01
#define UART_LCR UART_BASE + 0x03
#define UART_LSR UART_BASE + 0x05

#define UART_LCR_DLAB 0x80
#define UART_LSR_THRE 0x20

void putch(char ch) {
  while(!(*(volatile char *)(UART_LSR) & UART_LSR_THRE));
  *(volatile char *)(UART_THR) = ch;
}

void halt(int code) {
  asm volatile("mv a0, %0; ebreak" : :"r"(code));
  while (1);
}

void uart_config_divisor() {
  char div_enable_mask = UART_LCR_DLAB;
  *(volatile char *)(UART_LCR) |= div_enable_mask;// enable div access
  // 100MHz/(16*115200) = 54
  *(volatile char *)(UART_LDL) = 54;
  *(volatile char *)(UART_MDL) = 0;
  *(volatile char *)(UART_LCR) &= ~div_enable_mask;// disable div access
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
  uart_config_divisor();
  loader();
  int ret = main(mainargs);
  halt(ret);
}
