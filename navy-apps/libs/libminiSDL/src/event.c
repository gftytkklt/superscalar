#include <NDL.h>
#include <SDL.h>
#include <string.h>

#define keyname(k) #k,

static const char *keyname[] = {
  "NONE",
  _KEYS(keyname)
};

#define NR_KEYS (sizeof(keyname) / sizeof(keyname[0]))
#define MAX_EVENTS 256

static SDL_Event ev_queue[MAX_EVENTS];
static int ev_head = 0, ev_tail = 0, ev_count = 0;
static uint8_t keystate[NR_KEYS];

static int push_event(SDL_Event *ev) {
  if (ev_count == MAX_EVENTS) return 0;
  ev_queue[ev_tail] = *ev;
  ev_tail = (ev_tail + 1) % MAX_EVENTS;
  ev_count ++;
  if (ev->type == SDL_KEYDOWN) keystate[ev->key.keysym.sym & 0xff] = 1;
  else if (ev->type == SDL_KEYUP) keystate[ev->key.keysym.sym & 0xff] = 0;
  return 1;
}

static int pop_event(SDL_Event *ev) {
  if (ev_count == 0) return 0;
  if (ev != NULL) *ev = ev_queue[ev_head];
  ev_head = (ev_head + 1) % MAX_EVENTS;
  ev_count --;
  return 1;
}

// remove the event at ring index `idx` by shifting later events forward.
// Keystate is NOT reverted: it reflects the last key state (already recorded by
// push_event), regardless of whether a queued key event is consumed later.
static void remove_event(int idx) {
  int i = (idx - ev_head + MAX_EVENTS) % MAX_EVENTS;
  for (; i < ev_count - 1; i ++) {
    ev_queue[(ev_head + i) % MAX_EVENTS] = ev_queue[(ev_head + i + 1) % MAX_EVENTS];
  }
  ev_tail = (ev_tail - 1 + MAX_EVENTS) % MAX_EVENTS;
  ev_count --;
}

// position (from the head) of the first event at/after `pos` whose type matches mask
static int find_matching(int pos, uint32_t mask) {
  for (int i = pos; i < ev_count; i ++) {
    if (SDL_EVENTMASK(ev_queue[(ev_head + i) % MAX_EVENTS].type) & mask) return i;
  }
  return -1;
}

static int name_to_sym(const char *name) {
  for (int i = 1; i < NR_KEYS; i ++) {
    if (strcmp(keyname[i], name) == 0) return i;
  }
  return SDLK_NONE;
}

// convert an NDL event ("kd A\n" / "ku A\n") into an SDL_Event
static int fetch_ndl(SDL_Event *ev) {
  char buf[128];
  if (NDL_PollEvent(buf, sizeof(buf)) == 0) return 0;
  char *nl = memchr(buf, '\n', sizeof(buf) - 1);
  if (nl == NULL) return 0;
  *nl = '\0';
  if (strncmp(buf, "kd ", 3) == 0) {
    ev->type = SDL_KEYDOWN;
    ev->key.keysym.sym = name_to_sym(buf + 3);
    return 1;
  }
  if (strncmp(buf, "ku ", 3) == 0) {
    ev->type = SDL_KEYUP;
    ev->key.keysym.sym = name_to_sym(buf + 3);
    return 1;
  }
  return 0;
}

int SDL_PushEvent(SDL_Event *ev) {
  if (ev == NULL) return 0;
  return push_event(ev);
}

int SDL_PollEvent(SDL_Event *ev) {
  CallbackHelper();
  if (ev == NULL) return 0;
  if (ev_count > 0) return pop_event(ev);
  SDL_Event e;
  if (fetch_ndl(&e)) {
    push_event(&e);
    return pop_event(ev);
  }
  return 0;
}

int SDL_WaitEvent(SDL_Event *ev) {
  while (1) {
    CallbackHelper();
    if (ev_count > 0) return pop_event(ev);
    SDL_Event e;
    if (fetch_ndl(&e)) {
      push_event(&e);
      return pop_event(ev);
    }
  }
}

int SDL_PeepEvents(SDL_Event *ev, int numevents, int action, uint32_t mask) {
  switch (action) {
    case SDL_ADDEVENT: {
      if (ev == NULL) return 0;
      int added = 0;
      for (int i = 0; i < numevents && ev_count < MAX_EVENTS; i ++)
        if (push_event(&ev[i])) added ++;
      return added;
    }
    case SDL_PEEKEVENT:
    case SDL_GETEVENT: {
      if (ev == NULL || numevents <= 0) return 0;
      int got = 0, pos = 0;
      while (got < numevents) {
        int m = find_matching(pos, mask);
        if (m < 0) break;
        int idx = (ev_head + m) % MAX_EVENTS;
        ev[got] = ev_queue[idx];
        got ++;
        if (action == SDL_GETEVENT) {
          remove_event(idx);
          pos = m; // after removal, the following events shift into position m
        } else {
          pos = m + 1;
        }
      }
      return got;
    }
    default:
      return 0;
  }
}

uint8_t* SDL_GetKeyState(int *numkeys) {
  if (numkeys != NULL) *numkeys = NR_KEYS;
  return keystate;
}