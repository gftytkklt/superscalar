#include <am.h>
#include <klib.h>
#include <klib-macros.h>

extern char _heap_start, _heap_end, _bss_start, _bss_end, _sidata, _sdata, _edata;
int main(const char *args);

Area heap = RANGE(&_heap_start, &_heap_end);
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

// UART 波特率除数：由 npc.mk 按 WITH_SDL 注入（见 abstract-machine/scripts/platform/npc.mk）。
//   NVBoard（WITH_SDL）→ 1：位周期 16 clk 周期，匹配 NVBoard UART 默认 divisor 16；
//   否则 → 54：115200 波特（真实）。默认 54。
#ifndef UART_DIVISOR
#define UART_DIVISOR 54
#endif

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
  // 除数由 UART_DIVISOR 决定：NVBoard 时 1（位周期 16 匹配 nvboard divisor 16）；
  // 否则 54（115200 波特，真实）。
  *(volatile char *)(UART_LDL) = UART_DIVISOR;
  *(volatile char *)(UART_MDL) = 0;
  *(volatile char *)(UART_LCR) &= ~div_enable_mask;// disable div access
}

void loader() {
  // 把 .data 从 flash(LMA, _sidata) 拷贝到 SRAM(VMA, _sdata)。
  // 注意：_sdata 是 VMA，拷贝源必须用 LMA（LOADADDR 所得 _sidata）。
  memcpy(&_sdata, &_sidata, (size_t)(&_edata - &_sdata));
  char *bss_start = &_bss_start;
  char *bss_end = &_bss_end;
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
