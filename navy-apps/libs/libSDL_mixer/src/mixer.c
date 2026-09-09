#include <SDL_mixer.h>
#include <vorbis.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>

#define MAX_CHANNELS 16

/* ---- internal layout of the opaque Mix_Music / Mix_Chunk handles ---- */

typedef struct {
  stb_vorbis *vorbis;      // OGG decoder
  stb_vorbis_info info;    // sample_rate / channels
  int playing;
  int loops;               // -1 = infinite, 0 = play once, n = n replays
  int volume;              // 0 .. MIX_MAX_VOLUME
} Music;

typedef struct {
  uint8_t *data;           // 16-bit interleaved PCM
  uint32_t len;            // bytes
  uint32_t freq;
  int channels;
} Chunk;

typedef struct {
  Chunk *chunk;
  uint32_t pos;            // 16.16 fixed-point position in source frames
  int loops;
  int volume;
  int playing;
  int paused;
} Channel;

static int audio_freq = 44100;
static int num_channels = 0;
static Channel channels[MAX_CHANNELS];
static void (*channel_finished_cb)(int channel) = NULL;
static Music *cur_music = NULL;

static inline int16_t clip(int v) {
  if (v > 32767) return 32767;
  if (v < -32768) return -32768;
  return v;
}

/* ---- mixing helpers ---- */

// Mix the BGM into a stereo 16-bit buffer of `out_n` frames at device freq.
static void mix_music(int16_t *out, int out_n) {
  Music *m = cur_music;
  uint32_t src_rate = m->info.sample_rate;
  int src_ch = m->info.channels;
  int need = (int)(((uint64_t)out_n * src_rate + audio_freq - 1) / audio_freq);
  int16_t *tmp = malloc(need * src_ch * 2);
  assert(tmp);
  int got = stb_vorbis_get_samples_short_interleaved(m->vorbis, src_ch, tmp, need * src_ch);
  if (got < need) {
    // reached the end of the stream: restart if looping
    if (m->loops < 0) {
      stb_vorbis_seek_start(m->vorbis);
    } else if (m->loops > 0) {
      m->loops --;
      stb_vorbis_seek_start(m->vorbis);
    } else {
      m->playing = 0;
    }
  }
  // resample (duplicate on up-sampling) + up-channel (mono -> stereo) + volume
  for (int i = 0; i < out_n; i ++) {
    int s = (int)(((uint64_t)i * src_rate) / audio_freq);
    if (s >= got) { if (got == 0) break; s = got - 1; }
    int16_t l, r;
    if (src_ch == 2) { l = tmp[s * 2]; r = tmp[s * 2 + 1]; }
    else { l = r = tmp[s]; }
    out[i * 2]     = clip(out[i * 2]     + (int32_t)l * m->volume / MIX_MAX_VOLUME);
    out[i * 2 + 1] = clip(out[i * 2 + 1] + (int32_t)r * m->volume / MIX_MAX_VOLUME);
  }
  free(tmp);
}

// Mix one channel's chunk into `out`. Advances the 16.16 position and stops the
// channel (with loop handling) when the chunk is exhausted.
static void mix_chunk(Channel *c, int16_t *out, int out_n) {
  Chunk *ch = c->chunk;
  int src_frames = ch->len / (2 * ch->channels);
  int16_t *pcm = (int16_t *)ch->data;
  uint32_t step = (uint32_t)(((uint64_t)ch->freq << 16) / audio_freq);
  for (int i = 0; i < out_n; i ++) {
    int f = c->pos >> 16;
    if (f >= src_frames) break;
    int16_t l, r;
    if (ch->channels == 2) { l = pcm[f * 2]; r = pcm[f * 2 + 1]; }
    else { l = r = pcm[f]; }
    out[i * 2]     = clip(out[i * 2]     + (int32_t)l * c->volume / MIX_MAX_VOLUME);
    out[i * 2 + 1] = clip(out[i * 2 + 1] + (int32_t)r * c->volume / MIX_MAX_VOLUME);
    c->pos += step;
  }
  if ((c->pos >> 16) >= src_frames) {
    if (c->loops < 0) { c->pos = 0; }
    else if (c->loops > 0) { c->loops --; c->pos = 0; }
    else { c->playing = 0; }
  }
}

static void mix_audio(void *userdata, uint8_t *stream, int len) {
  int out_n = len / (2 * 2); // 16-bit, 2 channels
  int16_t *out = (int16_t *)stream;
  memset(out, 0, len);

  if (cur_music && cur_music->playing) mix_music(out, out_n);

  for (int i = 0; i < num_channels; i ++) {
    Channel *c = &channels[i];
    if (c->playing && !c->paused) {
      int was_playing = c->playing;
      mix_chunk(c, out, out_n);
      if (was_playing && !c->playing && channel_finished_cb) channel_finished_cb(i);
    }
  }
}

/* ---- General ---- */

int Mix_OpenAudio(int frequency, uint16_t format, int channels, int chunksize) {
  audio_freq = frequency;
  SDL_AudioSpec spec = {
    .freq = frequency,
    .format = format,
    .channels = channels,
    .samples = chunksize,
    .callback = mix_audio,
    .userdata = NULL,
  };
  if (SDL_OpenAudio(&spec, NULL) != 0) return -1;
  SDL_PauseAudio(0);
  return 0;
}

void Mix_CloseAudio() {
  SDL_CloseAudio();
}

char *Mix_GetError() {
  return "Navy SDL_mixer error";
}

int Mix_QuerySpec(int *frequency, uint16_t *format, int *channels) {
  if (frequency) *frequency = audio_freq;
  if (format) *format = AUDIO_S16;
  if (channels) *channels = 2;
  return 0;
}

/* ---- WAV loading ---- */

static Chunk *parse_wav(SDL_RWops *src) {
  char riff[4], wave[4];
  uint32_t riff_size;
  if (SDL_RWread(src, riff, 1, 4) != 4 || memcmp(riff, "RIFF", 4) != 0) return NULL;
  if (SDL_RWread(src, &riff_size, 4, 1) != 1) return NULL;
  if (SDL_RWread(src, wave, 1, 4) != 4 || memcmp(wave, "WAVE", 4) != 0) return NULL;

  uint32_t freq = 0;
  int channels = 0, bits = 0;
  uint8_t *data = NULL;
  uint32_t data_size = 0;

  for (;;) {
    char id[4];
    uint32_t size;
    if (SDL_RWread(src, id, 1, 4) != 4) break;
    if (SDL_RWread(src, &size, 4, 1) != 1) break;
    if (memcmp(id, "fmt ", 4) == 0) {
      uint16_t format;
      if (SDL_RWread(src, &format, 2, 1) != 1) return NULL;
      if (SDL_RWread(src, &channels, 2, 1) != 1) return NULL;
      if (SDL_RWread(src, &freq, 4, 1) != 1) return NULL;
      SDL_RWseek(src, 6, RW_SEEK_CUR); // byte rate + block align
      if (SDL_RWread(src, &bits, 2, 1) != 1) return NULL;
      if (format != 1) return NULL; // only PCM
      if (size > 16) SDL_RWseek(src, size - 16, RW_SEEK_CUR);
    } else if (memcmp(id, "data", 4) == 0) {
      data = malloc(size);
      if (data == NULL) return NULL;
      if (SDL_RWread(src, data, 1, size) != size) { free(data); return NULL; }
      data_size = size;
      break;
    } else {
      SDL_RWseek(src, size, RW_SEEK_CUR);
    }
  }
  if (data == NULL) return NULL;

  Chunk *ch = malloc(sizeof(Chunk));
  assert(ch);
  ch->freq = freq;
  ch->channels = channels;
  if (bits == 8) {
    // convert unsigned 8-bit to 16-bit
    uint16_t *pcm16 = malloc(data_size * 2);
    assert(pcm16);
    for (uint32_t i = 0; i < data_size; i ++) pcm16[i] = ((int)data[i] - 128) << 8;
    free(data);
    ch->data = (uint8_t *)pcm16;
    ch->len = data_size * 2;
  } else {
    ch->data = data;
    ch->len = data_size;
  }
  return ch;
}

Mix_Chunk *Mix_LoadWAV_RW(SDL_RWops *src, int freesrc) {
  Chunk *ch = parse_wav(src);
  if (freesrc) SDL_RWclose(src);
  return (Mix_Chunk *)ch;
}

void Mix_FreeChunk(Mix_Chunk *chunk) {
  if (chunk == NULL) return;
  Chunk *ch = (Chunk *)chunk;
  free(ch->data);
  free(ch);
}

/* ---- Channels ---- */

int Mix_AllocateChannels(int n) {
  if (n < 0) n = 0;
  if (n > MAX_CHANNELS) n = MAX_CHANNELS;
  num_channels = n;
  return num_channels;
}

int Mix_Volume(int channel, int volume) {
  if (channel < 0) { // all channels
    int prev = channels[0].volume;
    for (int i = 0; i < num_channels; i ++) channels[i].volume = volume;
    return prev;
  }
  if (channel >= num_channels) return -1;
  int prev = channels[channel].volume;
  channels[channel].volume = volume;
  return prev;
}

int Mix_PlayChannel(int channel, Mix_Chunk *chunk, int loops) {
  if (chunk == NULL) return -1;
  if (channel < 0) {
    channel = -1;
    for (int i = 0; i < num_channels; i ++)
      if (!channels[i].playing) { channel = i; break; }
    if (channel < 0) return -1; // no free channel
  }
  if (channel >= num_channels) return -1;
  Channel *c = &channels[channel];
  c->chunk = (Chunk *)chunk;
  c->pos = 0;
  c->loops = loops;
  c->volume = MIX_MAX_VOLUME;
  c->playing = 1;
  c->paused = 0;
  return channel;
}

void Mix_Pause(int channel) {
  if (channel < 0) {
    for (int i = 0; i < num_channels; i ++) channels[i].paused = 1;
  } else if (channel < num_channels) {
    channels[channel].paused = 1;
  }
}

void Mix_ChannelFinished(void (*channel_finished)(int channel)) {
  channel_finished_cb = channel_finished;
}

/* ---- Music ---- */

Mix_Music *Mix_LoadMUS_RW(SDL_RWops *src) {
  int64_t pos = SDL_RWtell(src);
  if (SDL_RWseek(src, 0, RW_SEEK_SET) != 0) return NULL;
  int64_t size = SDL_RWsize(src);
  if (size <= 0) return NULL;
  uint8_t *data = malloc(size);
  if (data == NULL) return NULL;
  if (SDL_RWread(src, data, 1, size) != (size_t)size) { free(data); return NULL; }
  SDL_RWseek(src, pos, RW_SEEK_SET);

  int err = 0;
  stb_vorbis *v = stb_vorbis_open_memory(data, size, &err, NULL);
  if (v == NULL) { free(data); return NULL; }

  Music *m = malloc(sizeof(Music));
  assert(m);
  m->vorbis = v;
  m->info = stb_vorbis_get_info(v);
  m->playing = 0;
  m->loops = 0;
  m->volume = MIX_MAX_VOLUME;
  return (Mix_Music *)m;
}

Mix_Music *Mix_LoadMUS(const char *file) {
  SDL_RWops *src = SDL_RWFromFile(file, "rb");
  if (src == NULL) return NULL;
  Mix_Music *m = Mix_LoadMUS_RW(src);
  SDL_RWclose(src);
  return m;
}

void Mix_FreeMusic(Mix_Music *music) {
  if (music == NULL) return;
  Music *m = (Music *)music;
  if (m == cur_music) cur_music = NULL;
  stb_vorbis_close(m->vorbis);
  free(m);
}

int Mix_PlayMusic(Mix_Music *music, int loops) {
  Music *m = (Music *)music;
  if (m == NULL) return -1;
  cur_music = m;
  m->playing = 1;
  m->loops = loops;
  stb_vorbis_seek_start(m->vorbis);
  return 0;
}

int Mix_VolumeMusic(int volume) {
  if (cur_music == NULL) return -1;
  int prev = cur_music->volume;
  cur_music->volume = volume;
  return prev;
}

int Mix_HaltMusic() {
  if (cur_music) cur_music->playing = 0;
  return 0;
}

int Mix_PlayingMusic() {
  return (cur_music && cur_music->playing) ? 1 : 0;
}

/* ---- not required by the PA, kept as stubs ---- */

int Mix_SetMusicPosition(double position) { return -1; }
int Mix_SetMusicCMD(const char *command) { return -1; }
void Mix_HookMusicFinished(void (*music_finished)()) { }