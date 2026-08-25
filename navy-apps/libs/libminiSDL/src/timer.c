#include <NDL.h>
#include <sdl-timer.h>
#include <stdbool.h>
#include <stddef.h>

#define MAX_TIMERS 16

typedef struct {
  bool used;
  uint32_t interval;
  SDL_NewTimerCallback callback;
  void *param;
  uint32_t last;
} SDL_Timer;

static SDL_Timer timers[MAX_TIMERS];

SDL_TimerID SDL_AddTimer(uint32_t interval, SDL_NewTimerCallback callback, void *param) {
  for (int i = 0; i < MAX_TIMERS; i ++) {
    if (!timers[i].used) {
      timers[i].used = true;
      timers[i].interval = interval;
      timers[i].callback = callback;
      timers[i].param = param;
      timers[i].last = NDL_GetTicks();
      return &timers[i];
    }
  }
  return NULL; // no free slot
}

int SDL_RemoveTimer(SDL_TimerID id) {
  SDL_Timer *t = (SDL_Timer *)id;
  if (t < timers || t >= timers + MAX_TIMERS) return 0;
  t->used = false;
  return 1;
}

uint32_t SDL_GetTicks() {
  CallbackHelper();
  return NDL_GetTicks();
}

void SDL_Delay(uint32_t ms) {
  uint32_t start = NDL_GetTicks();
  while (NDL_GetTicks() - start < ms) CallbackHelper();
}

// Check all registered timers and fire those whose interval has elapsed.
// The callback may return 0 to stop the timer, or a new interval to reschedule.
// Called from CallbackHelper, which itself is invoked by frequently-polled
// SDL APIs (SDL_GetTicks / SDL_PollEvent / SDL_Delay), mirroring the way the
// audio callback is fed.
void SDL_TimerHelper() {
  uint32_t now = NDL_GetTicks();
  for (int i = 0; i < MAX_TIMERS; i ++) {
    if (timers[i].used && now - timers[i].last >= timers[i].interval) {
      uint32_t next = timers[i].callback(timers[i].interval, timers[i].param);
      if (next == 0) {
        timers[i].used = false;
      } else {
        timers[i].interval = next;
        timers[i].last = NDL_GetTicks();
      }
    }
  }
}