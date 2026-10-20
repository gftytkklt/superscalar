#include <SDL_mixer.h>
#include <vorbis.h>
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <sdl-wav-internal.h>


/* ---- internal layout of the opaque Mix_Music / Mix_Chunk handles ---- */

typedef struct {
  stb_vorbis *vorbis;      // OGG decoder
  stb_vorbis_info info;    // sample_rate / channels
  uint8_t *encoded;        // borrowed by the decoder until close
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
  uint64_t pos;            // 48.16 fixed-point position in source frames
  int loops;
  int volume;
  int playing;
  int paused;
} Channel;

static int audio_freq = 44100;
static int num_channels = 0;
static Channel *channels;
static int mixer_open;
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
  uint64_t need64 = ((uint64_t)out_n * src_rate + audio_freq - 1) / audio_freq;
  if (src_ch < 1 || src_ch > 2 || need64 > INT_MAX / (src_ch * 2) ||
      need64 > SIZE_MAX / (src_ch * 2)) { m->playing = 0; return; }
  int need = need64;
  int16_t *tmp = malloc((size_t)need * src_ch * 2);
  if (tmp == NULL) { m->playing = 0; return; }
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

// Mix one channel's chunk into `out`. Advances the 48.16 position and stops the
// channel (with loop handling) when the chunk is exhausted.
static void mix_chunk(Channel *c, int16_t *out, int out_n) {
  Chunk *ch = c->chunk;
  int src_frames = ch->len / (2 * ch->channels);
  int16_t *pcm = (int16_t *)ch->data;
  uint64_t step = ((uint64_t)ch->freq << 16) / audio_freq;
  for (int i = 0; i < out_n; i ++) {
    uint64_t f = c->pos >> 16;
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
  if (frequency <= 0 || format != AUDIO_S16 || channels != 2 ||
      chunksize <= 0 || chunksize > UINT16_MAX) return -1;
  SDL_AudioSpec spec = {
    .freq = frequency,
    .format = format,
    .channels = channels,
    .samples = chunksize,
    .callback = mix_audio,
    .userdata = NULL,
  };
  if (SDL_OpenAudio(&spec, NULL) != 0) return -1;
  audio_freq = frequency;
  mixer_open = 1;
  SDL_PauseAudio(0);
  return 0;
}

void Mix_CloseAudio() {
  SDL_CloseAudio();
  mixer_open = 0;
  for (int i = 0; i < num_channels; i ++) channels[i].playing = 0;
  if (cur_music) cur_music->playing = 0;
}

char *Mix_GetError() {
  return "Navy SDL_mixer error";
}

int Mix_QuerySpec(int *frequency, uint16_t *format, int *channels) {
  if (!mixer_open) return 0;
  if (frequency) *frequency = audio_freq;
  if (format) *format = AUDIO_S16;
  if (channels) *channels = 2;
  return 1;
}

/* ---- WAV loading ---- */

static Chunk *parse_wav(SDL_RWops *src) {
  SDL_AudioSpec spec;
  uint8_t *data;
  uint32_t size;
  if (!load_pcm_wav(src, &spec, &data, &size)) return NULL;
  if (spec.format == AUDIO_U8) {
    if (size > UINT32_MAX / 2 || size > SIZE_MAX / 2) { free(data); return NULL; }
    int16_t *pcm = malloc(size ? (size_t)size * 2 : 1);
    if (pcm == NULL) { free(data); return NULL; }
    for (uint32_t i = 0; i < size; i ++) pcm[i] = ((int)data[i] - 128) * 256;
    free(data);
    data = (uint8_t *)pcm;
    size *= 2;
  }
  Chunk *ch = malloc(sizeof(Chunk));
  if (ch == NULL) { free(data); return NULL; }
  *ch = (Chunk){ .data = data, .len = size, .freq = spec.freq, .channels = spec.channels };
  return ch;
}

Mix_Chunk *Mix_LoadWAV_RW(SDL_RWops *src, int freesrc) {
  Chunk *ch = parse_wav(src);
  if (freesrc && src != NULL) SDL_RWclose(src);
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
  if (n < 0) return num_channels;
  if (n == num_channels) return n;
  if (n == 0) {
    free(channels);
    channels = NULL;
  } else {
    if ((size_t)n > SIZE_MAX / sizeof(Channel)) return num_channels;
    Channel *next = realloc(channels, (size_t)n * sizeof(Channel));
    if (next == NULL) return num_channels;
    if (n > num_channels) memset(next + num_channels, 0, (n - num_channels) * sizeof(Channel));
    channels = next;
  }
  num_channels = n;
  return num_channels;
}

int Mix_Volume(int channel, int volume) {
  if (channel < 0) { // all channels
    if (num_channels == 0) return 0;
    int prev = channels[0].volume;
    if (volume >= 0) for (int i = 0; i < num_channels; i ++)
      channels[i].volume = volume > MIX_MAX_VOLUME ? MIX_MAX_VOLUME : volume;
    return prev;
  }
  if (channel >= num_channels) return -1;
  int prev = channels[channel].volume;
  if (volume >= 0) channels[channel].volume = volume > MIX_MAX_VOLUME ? MIX_MAX_VOLUME : volume;
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
  if (src == NULL) return NULL;
  int64_t pos = SDL_RWtell(src);
  if (SDL_RWseek(src, 0, RW_SEEK_SET) != 0) return NULL;
  int64_t size = SDL_RWsize(src);
  if (pos < 0 || size <= 0 || size > INT_MAX || (uint64_t)size > SIZE_MAX) return NULL;
  uint8_t *data = malloc(size);
  if (data == NULL) return NULL;
  size_t got = SDL_RWread(src, data, 1, size);
  int restored = SDL_RWseek(src, pos, RW_SEEK_SET) == pos;
  if (got != (size_t)size || !restored) { free(data); return NULL; }

  int err = 0;
  stb_vorbis *v = stb_vorbis_open_memory(data, size, &err, NULL);
  if (v == NULL) { free(data); return NULL; }

  Music *m = malloc(sizeof(Music));
  if (m == NULL) { stb_vorbis_close(v); free(data); return NULL; }
  m->vorbis = v;
  m->encoded = data;
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
  free(m->encoded);
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
  if (volume >= 0) cur_music->volume = volume > MIX_MAX_VOLUME ? MIX_MAX_VOLUME : volume;
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
