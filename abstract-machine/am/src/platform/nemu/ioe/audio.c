#include <am.h>
#include <nemu.h>
#include <klib.h>

#define AUDIO_FREQ_ADDR      (AUDIO_ADDR + 0x00)
#define AUDIO_CHANNELS_ADDR  (AUDIO_ADDR + 0x04)
#define AUDIO_SAMPLES_ADDR   (AUDIO_ADDR + 0x08)
#define AUDIO_SBUF_SIZE_ADDR (AUDIO_ADDR + 0x0c)
#define AUDIO_INIT_ADDR      (AUDIO_ADDR + 0x10)
#define AUDIO_COUNT_ADDR     (AUDIO_ADDR + 0x14)
static uint32_t bufsize = 0;
static uint32_t wr_index = 0;

void __am_audio_init() {
  bufsize = inl(AUDIO_SBUF_SIZE_ADDR);
  // CTRL commits a complete configuration; do not open while it is being set.
  outl(AUDIO_INIT_ADDR, 0);
}

void __am_audio_config(AM_AUDIO_CONFIG_T *cfg) {
  cfg->present = true;
  cfg->bufsize = inl(AUDIO_SBUF_SIZE_ADDR);// 64K
}

void __am_audio_ctrl(AM_AUDIO_CTRL_T *ctrl) {
  outl(AUDIO_FREQ_ADDR, ctrl->freq);
  outl(AUDIO_CHANNELS_ADDR, ctrl->channels);
  outl(AUDIO_SAMPLES_ADDR, ctrl->samples);
  wr_index = 0;
  // INIT=2 reopens with an empty stream; legacy INIT=1 preserves its cursor.
  outl(AUDIO_INIT_ADDR, 2);
}

void __am_audio_status(AM_AUDIO_STATUS_T *stat) {
  // stat->count = 0;
  stat->count = inl(AUDIO_COUNT_ADDR);
}

void __am_audio_play(AM_AUDIO_PLAY_T *ctl) {
  uintptr_t start = (uintptr_t)ctl->buf.start;
  uintptr_t end = (uintptr_t)ctl->buf.end;
  assert(end >= start);
  size_t remaining = end - start;
  if (remaining == 0) return;
  assert(bufsize != 0);
  const uint8_t *play_buf = ctl->buf.start;
  while (remaining != 0) {
    // A failed backend clears INIT: remain silent without writing the ring.
    if (inl(AUDIO_INIT_ADDR) == 0) return;
    uint32_t len = remaining < bufsize ? remaining : bufsize;
    while (bufsize - inl(AUDIO_COUNT_ADDR) < len) {
      if (inl(AUDIO_INIT_ADDR) == 0) return;
    }
    for (uint32_t i = 0; i < len; i++) {
      if (wr_index >= bufsize) wr_index -= bufsize;
      outb(AUDIO_SBUF_ADDR + wr_index, play_buf[i]);
      wr_index++;
    }
    // Preserve the existing count interface; its asynchronous update race is
    // tracked separately as F0043.
    outl(AUDIO_COUNT_ADDR, inl(AUDIO_COUNT_ADDR) + len);
    play_buf += len;
    remaining -= len;
  }
}
