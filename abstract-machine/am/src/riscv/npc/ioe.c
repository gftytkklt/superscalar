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
void __am_gpu_config(AM_GPU_CONFIG_T *);
void __am_gpu_status(AM_GPU_STATUS_T *);
void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *);

static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = true; }
static void __am_input_config(AM_INPUT_CONFIG_T *cfg) { cfg->present = true; }
static void __am_uart_config(AM_UART_CONFIG_T *cfg) { cfg->present = true; }
static void __am_uart_tx(AM_UART_TX_T *tx) { putch(tx->data); }
static void __am_audio_config(AM_AUDIO_CONFIG_T *cfg) {
  *cfg = (AM_AUDIO_CONFIG_T) { .present = false, .bufsize = 0 };
}
static void __am_disk_config(AM_DISK_CONFIG_T *cfg) {
  *cfg = (AM_DISK_CONFIG_T) { .present = false, .blksz = 0, .blkcnt = 0 };
}
static void __am_net_config(AM_NET_CONFIG_T *cfg) {
  *cfg = (AM_NET_CONFIG_T) { .present = false };
}

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
  [AM_UART_TX     ] = __am_uart_tx,
  [AM_UART_RX     ] = __am_uart_rx,
  [AM_GPU_CONFIG  ] = __am_gpu_config,
  [AM_GPU_STATUS  ] = __am_gpu_status,
  [AM_GPU_FBDRAW  ] = __am_gpu_fbdraw,
  [AM_AUDIO_CONFIG] = __am_audio_config,
  [AM_DISK_CONFIG ] = __am_disk_config,
  [AM_NET_CONFIG  ] = __am_net_config,
};

// Direction follows the WR declarations in amdev.h; all other known registers are RD.
static const bool write_only[LENGTH(lut)] = {
  [AM_UART_TX] = true,
  [AM_GPU_FBDRAW] = true, [AM_GPU_MEMCPY] = true, [AM_GPU_RENDER] = true,
  [AM_AUDIO_CTRL] = true, [AM_AUDIO_PLAY] = true,
  [AM_DISK_BLKIO] = true,
  [AM_NET_TX] = true, [AM_NET_RX] = true,
};

static void fail(void *buf) { panic("access nonexist register"); }

bool ioe_init() {
  for (int i = 0; i < LENGTH(lut); i++)
    if (!lut[i]) lut[i] = fail;
  __am_timer_init();
  return true;
}

void ioe_read(int reg, void *buf) {
  if (reg < 1 || reg >= (int)LENGTH(lut) || write_only[reg]) {
    fail(buf);
    return;
  }
  ((handler_t)lut[reg])(buf);
}
void ioe_write(int reg, void *buf) {
  if (reg < 1 || reg >= (int)LENGTH(lut) || !write_only[reg]) {
    fail(buf);
    return;
  }
  ((handler_t)lut[reg])(buf);
}
