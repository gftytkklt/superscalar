#include <am.h>
#include <klib-macros.h>

// 阶段 J2：UART RX。UART16550 基址 0x10000000，RBR/THR=+0、LSR=+5。
#define UART_BASE    0x10000000L
#define UART_RBR     (UART_BASE + 0x00)
#define UART_LSR     (UART_BASE + 0x05)
#define UART_LSR_DR  0x01

void __am_timer_init();
void __am_timer_rtc(AM_TIMER_RTC_T *);
void __am_timer_uptime(AM_TIMER_UPTIME_T *);
void __am_input_keybrd(AM_INPUT_KEYBRD_T *);

static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = true; }
static void __am_input_config(AM_INPUT_CONFIG_T *cfg) { cfg->present = true; }
static void __am_uart_config(AM_UART_CONFIG_T *cfg) { cfg->present = true; }

// AM_UART_RX：读 UART RBR，无数据返回 0xff（AM 规范）。
static void __am_uart_rx(AM_UART_RX_T *rx) {
  if (*(volatile char *)(UART_LSR) & UART_LSR_DR) {
    rx->data = *(volatile char *)(UART_RBR);
  } else {
    rx->data = 0xff;
  }
}

typedef void (*handler_t)(void *buf);
static void *lut[128] = {
  [AM_TIMER_CONFIG] = __am_timer_config,
  [AM_TIMER_RTC   ] = __am_timer_rtc,
  [AM_TIMER_UPTIME] = __am_timer_uptime,
  [AM_INPUT_CONFIG] = __am_input_config,
  [AM_INPUT_KEYBRD] = __am_input_keybrd,
  [AM_UART_CONFIG ] = __am_uart_config,
  [AM_UART_RX     ] = __am_uart_rx,
};

static void fail(void *buf) { panic("access nonexist register"); }

bool ioe_init() {
  for (int i = 0; i < LENGTH(lut); i++)
    if (!lut[i]) lut[i] = fail;
  __am_timer_init();
  return true;
}

void ioe_read (int reg, void *buf) { ((handler_t)lut[reg])(buf); }
void ioe_write(int reg, void *buf) { ((handler_t)lut[reg])(buf); }