#ifndef __SDL_WAV_INTERNAL_H__
#define __SDL_WAV_INTERNAL_H__

// Shared by the two PCM WAV wrappers; this is not a public SDL API.
#include <limits.h>
#include <stdlib.h>
#include <string.h>

static uint32_t wav_le32(const uint8_t *p) {
  return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
         (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static uint16_t wav_le16(const uint8_t *p) {
  return (uint16_t)p[0] | (uint16_t)p[1] << 8;
}

static int load_pcm_wav(SDL_RWops *src, SDL_AudioSpec *spec,
                        uint8_t **audio_buf, uint32_t *audio_len) {
  if (src == NULL) return 0;
  int64_t start = SDL_RWtell(src), total = SDL_RWsize(src);
  uint8_t header[16];
  if (start < 0 || total < start || total - start < 12 ||
      SDL_RWread(src, header, 1, 12) != 12 ||
      memcmp(header, "RIFF", 4) != 0 || memcmp(header + 8, "WAVE", 4) != 0) return 0;
  uint32_t riff_size = wav_le32(header + 4);
  if (riff_size < 4 || (uint64_t)riff_size > (uint64_t)(total - start - 8)) return 0;
  int64_t end = start + 8 + riff_size, pos = start + 12;
  SDL_AudioSpec parsed = {0};
  unsigned align = 0;
  int have_fmt = 0;
  while (end - pos >= 8) {
    if (SDL_RWread(src, header, 1, 8) != 8) return 0;
    uint32_t size = wav_le32(header + 4);
    pos += 8;
    uint64_t padded = (uint64_t)size + (size & 1);
    if (padded > (uint64_t)(end - pos)) return 0;
    int64_t next = pos + padded;
    if (memcmp(header, "fmt ", 4) == 0) {
      if (have_fmt || size < 16 || SDL_RWread(src, header, 1, 16) != 16) return 0;
      unsigned channels = wav_le16(header + 2), bits = wav_le16(header + 14);
      uint32_t freq = wav_le32(header + 4);
      if (wav_le16(header) != 1 || (channels != 1 && channels != 2) ||
          (bits != 8 && bits != 16) || freq == 0 || freq > INT_MAX) return 0;
      align = channels * (bits / 8);
      uint64_t byte_rate = (uint64_t)freq * align;
      if (wav_le16(header + 12) != align || byte_rate > UINT32_MAX ||
          wav_le32(header + 8) != byte_rate) return 0;
      parsed.freq = freq;
      parsed.channels = channels;
      parsed.format = bits == 8 ? AUDIO_U8 : AUDIO_S16;
      parsed.samples = 4096;
      parsed.size = parsed.samples * align;
      have_fmt = 1;
    } else if (memcmp(header, "data", 4) == 0) {
      if (!have_fmt || size % align != 0) return 0;
      uint8_t *data = malloc(size ? size : 1);
      if (data == NULL) return 0;
      if (SDL_RWread(src, data, 1, size) != size ||
          SDL_RWseek(src, next, RW_SEEK_SET) != next) { free(data); return 0; }
      *spec = parsed;
      *audio_buf = data;
      *audio_len = size;
      return 1;
    }
    if (SDL_RWseek(src, next, RW_SEEK_SET) != next) return 0;
    pos = next;
  }
  return 0;
}

#endif
