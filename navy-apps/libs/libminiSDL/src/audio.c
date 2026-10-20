#include <NDL.h>
#include <SDL.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sdl-wav-internal.h>

static SDL_AudioSpec audio_spec;
static int audio_paused = 1;   // 打开后处于暂停状态
static uint32_t audio_last = 0;
static int audio_in_callback = 0;  // 重入保护标志
static uint64_t audio_generation;
static int audio_open;

// 定期调用应用回调，获取 PCM 数据写入流缓冲区。
// Nanos-lite 无信号机制，只能在被频繁调用的 API 中主动查询时间。
void CallbackHelper() {
  // 重入保护：若回调函数内部又调用了会触发 CallbackHelper 的 SDL API
  // （如 SDL_GetTicks/SDL_PollEvent），直接返回，避免死递归。
  if (audio_in_callback) return;
  SDL_TimerHelper(); // fire registered SDL timers (always, independent of audio)
  if (audio_paused || audio_spec.callback == NULL) return;

  uint32_t now = NDL_GetTicks();
  uint32_t interval = (uint32_t)((uint64_t)audio_spec.samples * 1000 / audio_spec.freq);
  if (now - audio_last < interval) return;
  audio_last = now;

  int frame_bytes = audio_spec.channels * 2;
  int bytes = audio_spec.size;
  // 不超过流缓冲区空闲空间，避免阻塞写入
  int space = NDL_QueryAudio();
  if (space < bytes) bytes = space;
  if (bytes > 0) bytes -= bytes % frame_bytes;
  if (bytes <= 0) return;

  uint8_t *stream = malloc(bytes);
  assert(stream);
  audio_in_callback = 1;       // 进入回调，标记"正在回调中"
  uint64_t generation = audio_generation;
  audio_spec.callback(audio_spec.userdata, stream, bytes);
  audio_in_callback = 0;       // 退出回调
  if (audio_open && audio_generation == generation) NDL_PlayAudio(stream, bytes);
  free(stream);
}

int SDL_OpenAudio(SDL_AudioSpec *desired, SDL_AudioSpec *obtained) {
  if (desired == NULL || desired->format != AUDIO_S16 || desired->freq <= 0 ||
      (desired->channels != 1 && desired->channels != 2) ||
      desired->samples == 0 || desired->callback == NULL) return -1;
  SDL_AudioSpec spec = *desired;
  spec.size = (uint32_t)spec.samples * spec.channels * 2;
  if (audio_open) SDL_CloseAudio();
  NDL_OpenAudio(desired->freq, desired->channels, desired->samples);
  audio_spec = spec;
  audio_generation ++;
  audio_open = 1;
  if (obtained != NULL) *obtained = audio_spec;
  audio_paused = 1;
  audio_last = NDL_GetTicks();
  return 0;
}

void SDL_CloseAudio() {
  audio_paused = 1;
  audio_spec.callback = NULL;
  audio_spec.userdata = NULL;
  audio_generation ++;
  audio_open = 0;
  NDL_CloseAudio();
}

void SDL_PauseAudio(int pause_on) {
  audio_paused = pause_on;
  audio_last = NDL_GetTicks();
}

void SDL_LockAudio() {
}

void SDL_UnlockAudio() {
}

void SDL_MixAudio(uint8_t *dst, uint8_t *src, uint32_t len, int volume) {
  if (volume < 0) volume = 0;
  if (volume > SDL_MIX_MAXVOLUME) volume = SDL_MIX_MAXVOLUME;
  for (uint32_t i = 0; i < len / 2 * 2; i += 2) {
    int16_t d = (int16_t)(dst[i] | (dst[i + 1] << 8));
    int16_t s = (int16_t)(src[i] | (src[i + 1] << 8));
    int32_t v = d + (int32_t)s * volume / SDL_MIX_MAXVOLUME;
    if (v > 32767) v = 32767;
    if (v < -32768) v = -32768;
    dst[i] = (uint8_t)(v & 0xff);
    dst[i + 1] = (uint8_t)((v >> 8) & 0xff);
  }
}

SDL_AudioSpec *SDL_LoadWAV(const char *file, SDL_AudioSpec *spec, uint8_t **audio_buf, uint32_t *audio_len) {
  if (file == NULL || spec == NULL || audio_buf == NULL || audio_len == NULL) return NULL;
  SDL_RWops *src = SDL_RWFromFile(file, "rb");
  if (src == NULL) return NULL;
  int ok = load_pcm_wav(src, spec, audio_buf, audio_len);
  SDL_RWclose(src);
  return ok ? spec : NULL;
}

void SDL_FreeWAV(uint8_t *audio_buf) {
  free(audio_buf);
}
