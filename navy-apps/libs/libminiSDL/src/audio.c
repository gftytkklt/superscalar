#include <NDL.h>
#include <SDL.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static SDL_AudioSpec audio_spec;
static int audio_paused = 1;   // 打开后处于暂停状态
static uint32_t audio_last = 0;

// 定期调用应用回调，获取 PCM 数据写入流缓冲区。
// Nanos-lite 无信号机制，只能在被频繁调用的 API 中主动查询时间。
void CallbackHelper() {
  if (audio_paused || audio_spec.callback == NULL) return;

  uint32_t now = NDL_GetTicks();
  uint32_t interval = (uint32_t)((uint64_t)audio_spec.samples * 1000 / audio_spec.freq);
  if (now - audio_last < interval) return;
  audio_last = now;

  int bytes = audio_spec.samples * audio_spec.channels * (audio_spec.format == AUDIO_S16 ? 2 : 1);
  // 不超过流缓冲区空闲空间，避免阻塞写入
  int space = NDL_QueryAudio();
  if (space < bytes) bytes = space;
  if (bytes <= 0) return;

  uint8_t *stream = malloc(bytes);
  assert(stream);
  audio_spec.callback(audio_spec.userdata, stream, bytes);
  NDL_PlayAudio(stream, bytes);
  free(stream);
}

int SDL_OpenAudio(SDL_AudioSpec *desired, SDL_AudioSpec *obtained) {
  assert(desired != NULL);
  audio_spec = *desired;
  NDL_OpenAudio(desired->freq, desired->channels, desired->samples);
  if (obtained != NULL) *obtained = audio_spec;
  audio_paused = 1;
  audio_last = NDL_GetTicks();
  return 0;
}

void SDL_CloseAudio() {
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
  for (uint32_t i = 0; i < len; i += 2) {
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
  FILE *fp = fopen(file, "r");
  if (fp == NULL) return NULL;

  // RIFF 头
  char riff[4];
  uint32_t riff_size;
  char wave[4];
  assert(1 == fread(riff, 4, 1, fp));
  assert(memcmp(riff, "RIFF", 4) == 0);
  assert(1 == fread(&riff_size, 4, 1, fp));
  assert(1 == fread(wave, 4, 1, fp));
  assert(memcmp(wave, "WAVE", 4) == 0);

  // 遍历块，找到 fmt 与 data
  while (1) {
    char id[4];
    uint32_t size;
    if (fread(id, 4, 1, fp) != 1) break;
    assert(1 == fread(&size, 4, 1, fp));
    if (memcmp(id, "fmt ", 4) == 0) {
      uint16_t format, channels, bits;
      uint32_t freq, byte_rate;
      assert(1 == fread(&format, 2, 1, fp));
      assert(1 == fread(&channels, 2, 1, fp));
      assert(1 == fread(&freq, 4, 1, fp));
      assert(1 == fread(&byte_rate, 4, 1, fp));
      fseek(fp, 2, SEEK_CUR);             // block align
      assert(1 == fread(&bits, 2, 1, fp));
      assert(format == 1);                // PCM
      spec->freq = freq;
      spec->channels = channels;
      spec->samples = 4096;
      spec->format = (bits == 8) ? AUDIO_U8 : AUDIO_S16;
      if (size > 16) fseek(fp, size - 16, SEEK_CUR);
    } else if (memcmp(id, "data", 4) == 0) {
      uint8_t *buf = malloc(size);
      assert(buf);
      assert(size == fread(buf, 1, size, fp));
      fclose(fp);
      *audio_buf = buf;
      *audio_len = size;
      return spec;
    } else {
      fseek(fp, size, SEEK_CUR);
    }
  }

  fclose(fp);
  return NULL;
}

void SDL_FreeWAV(uint8_t *audio_buf) {
  free(audio_buf);
}