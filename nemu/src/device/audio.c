/***************************************************************************************
* Copyright (c) 2014-2022 Zihao Yu, Nanjing University
*
* NEMU is licensed under Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*          http://license.coscl.org.cn/MulanPSL2
*
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
* EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
* MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
*
* See the Mulan PSL v2 for more details.
***************************************************************************************/

#include <common.h>
#include <device/map.h>
#include <SDL2/SDL.h>

enum {
  reg_freq,
  reg_channels,
  reg_samples,
  reg_sbuf_size,
  reg_init,
  reg_count,
  nr_reg
};

static uint32_t rd_index = 0;
static uint8_t *sbuf = NULL;
static uint32_t *audio_base = NULL;
static bool audio_initialized = false;
static bool audio_opened = false;
static bool init_pending = false;
static bool reset_pending = false;
SDL_AudioSpec s = {};

static uint32_t audio_freq() {
  return MUXDEF(CONFIG_TARGET_AM, io_read(AM_AUDIO_CTRL).freq, audio_base[reg_freq]);
}

static uint32_t audio_channels() {
  return MUXDEF(CONFIG_TARGET_AM, io_read(AM_AUDIO_CTRL).channels, audio_base[reg_channels]);
}

static uint32_t audio_samples() {
  return MUXDEF(CONFIG_TARGET_AM, io_read(AM_AUDIO_CTRL).samples, audio_base[reg_samples]);
}

static void audio_play(void *userdata, uint8_t *stream, int len){
  // actual rd buf len
  int nread = len;
  if (audio_base[reg_count] < len) nread = audio_base[reg_count];
  //int b = 0;
  //while (b < nread) {
  //  int n = read(rfd, stream, nread);
  //  if (n > 0) b += n;
  //}
  for(int i=0;i<nread;i++){
    if(rd_index >= audio_base[reg_sbuf_size]) {rd_index = rd_index - audio_base[reg_sbuf_size];}
    stream[i] = sbuf[rd_index];
    rd_index++;
  }

  audio_base[reg_count] -= nread;
  if (len > nread) {
    memset(stream + nread, 0, len - nread);
  }
}

static void audio_disable() {
  audio_base[reg_init] = 0;
  // Discard queued PCM while preserving alignment with the AM write cursor.
  rd_index = (rd_index + audio_base[reg_count]) % audio_base[reg_sbuf_size];
  audio_base[reg_count] = 0;
}

static void SDL_audio_init(bool reset_stream){
  SDL_AudioSpec s = {};
  s.freq = audio_freq();
  s.format = AUDIO_S16SYS;
  s.channels = audio_channels();
  s.samples = audio_samples();
  s.callback = audio_play;
  s.userdata = NULL;
  //printf("%d %d %d\n",s.freq,s.channels,s.samples);
  if (audio_opened) {
    SDL_CloseAudio();
    audio_opened = false;
  }
  // CloseAudio has stopped the old callback before resetting the queue.
  if (reset_stream) {
    rd_index = 0;
    audio_base[reg_count] = 0;
  }
  if (!audio_initialized) {
    if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) {
      fprintf(stderr, "audio: SDL_InitSubSystem failed: %s; audio disabled\n", SDL_GetError());
      audio_disable();
      return;
    }
    audio_initialized = true;
  }
  if (SDL_OpenAudio(&s, NULL) != 0) {
    fprintf(stderr, "audio: SDL_OpenAudio failed: %s; audio disabled\n", SDL_GetError());
    audio_disable();
    return;
  }
  audio_opened = true;
  SDL_PauseAudio(0);
}

static void audio_io_handler(uint32_t offset, int len, bool is_write) {
  if (!is_write || len != sizeof(uint32_t)) return;
  if (offset == reg_init * sizeof(uint32_t)) {
    init_pending = audio_base[reg_init] != 0;
    reset_pending = audio_base[reg_init] == 2;
  } else if (offset != reg_freq * sizeof(uint32_t) &&
             offset != reg_channels * sizeof(uint32_t) &&
             offset != reg_samples * sizeof(uint32_t)) {
    return;
  }
  // Keep the existing AM init-before-CTRL sequence working: an early init
  // request waits for the configuration, then opens exactly once.
  if (init_pending && audio_freq() && audio_channels() && audio_samples()) {
    init_pending = false;
    bool reset_stream = reset_pending;
    reset_pending = false;
    SDL_audio_init(reset_stream);
  }
}

void init_audio() {
  uint32_t space_size = sizeof(uint32_t) * nr_reg;
  audio_base = (uint32_t *)new_space(space_size);
#ifdef CONFIG_HAS_PORT_IO
  add_pio_map ("audio", CONFIG_AUDIO_CTL_PORT, audio_base, space_size, audio_io_handler);
#else
  add_mmio_map("audio", CONFIG_AUDIO_CTL_MMIO, audio_base, space_size, audio_io_handler);
#endif

  sbuf = (uint8_t *)new_space(CONFIG_SB_SIZE);
  add_mmio_map("audio-sbuf", CONFIG_SB_ADDR, sbuf, CONFIG_SB_SIZE, NULL);
  audio_base[reg_sbuf_size] = CONFIG_SB_SIZE;
  audio_base[reg_freq] = 0;
  audio_base[reg_channels] = 0;
  audio_base[reg_samples] = 0;
  audio_base[reg_count] = 0;
  audio_base[reg_init] = 0;
}
