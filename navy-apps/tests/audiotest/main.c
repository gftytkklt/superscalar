#include <SDL.h>
#include <NDL.h>
#include <fixedptc.h>
#include <stdio.h>

static fixedpt phase = 0;

void sine_cb(void *userdata, uint8_t *stream, int len) {
  int16_t *s = (int16_t *)stream;
  int n = len / 2;
  for (int i = 0; i < n; i++) {
    fixedpt v = fixedpt_muli(fixedpt_sin(phase), 3000);
    s[i] = (int16_t)fixedpt_toint(v);
    phase += FIXEDPT_ONE / 30;
    if (phase >= FIXEDPT_TWO_PI) phase -= FIXEDPT_TWO_PI;
  }
}

int main() {
  SDL_Init(0);
  SDL_AudioSpec spec;
  spec.freq = 44100;
  spec.channels = 2;
  spec.samples = 1024;
  spec.format = AUDIO_S16;
  spec.userdata = NULL;
  spec.callback = sine_cb;

  printf("audiotest: open audio\n");
  SDL_OpenAudio(&spec, NULL);
  printf("audiotest: audio opened, free=%d\n", NDL_QueryAudio());
  SDL_PauseAudio(0);

  for (int i = 0; i < 40; i++) {
    SDL_Delay(50);
    if (i % 4 == 0) printf("audiotest: t=%dms free=%d\n", i * 50, NDL_QueryAudio());
  }

  SDL_CloseAudio();
  printf("audiotest: done\n");
  return 0;
}