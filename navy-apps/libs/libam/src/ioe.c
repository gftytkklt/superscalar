#include <am.h>
#include <NDL.h>
#include <string.h>

#define KEYNAME(k) #k,
static const char *keyname[] = {
  "NONE",
  AM_KEYS(KEYNAME)
};
#define NR_KEYS (sizeof(keyname) / sizeof(keyname[0]))

static int screen_w = 0, screen_h = 0;

static int name_to_keycode(const char *name, int len) {
  for (int i = 1; i < NR_KEYS; i ++) {
    if (strlen(keyname[i]) == (size_t)len && strncmp(keyname[i], name, len) == 0) {
      return i;
    }
  }
  return AM_KEY_NONE;
}

bool ioe_init() {
  NDL_Init(0);
  NDL_OpenCanvas(&screen_w, &screen_h);
  return true;
}

void ioe_read(int reg, void *buf) {
  switch (reg) {
    case AM_TIMER_CONFIG: {
      AM_TIMER_CONFIG_T *cfg = (AM_TIMER_CONFIG_T *)buf;
      cfg->present = true;
      cfg->has_rtc = false;
      break;
    }
    case AM_TIMER_UPTIME: {
      AM_TIMER_UPTIME_T *t = (AM_TIMER_UPTIME_T *)buf;
      t->us = (uint64_t)NDL_GetTicks() * 1000;
      break;
    }
    case AM_INPUT_CONFIG: {
      AM_INPUT_CONFIG_T *cfg = (AM_INPUT_CONFIG_T *)buf;
      cfg->present = true;
      break;
    }
    case AM_INPUT_KEYBRD: {
      AM_INPUT_KEYBRD_T *kbd = (AM_INPUT_KEYBRD_T *)buf;
      char ev[128];
      if (NDL_PollEvent(ev, sizeof(ev))) {
        char *nl = strchr(ev, '\n');
        int len = nl ? (int)(nl - (ev + 3)) : (int)strlen(ev + 3);
        kbd->keydown = (ev[1] == 'd');
        kbd->keycode = name_to_keycode(ev + 3, len);
      } else {
        kbd->keydown = false;
        kbd->keycode = AM_KEY_NONE;
      }
      break;
    }
    case AM_GPU_CONFIG: {
      AM_GPU_CONFIG_T *cfg = (AM_GPU_CONFIG_T *)buf;
      cfg->present = true;
      cfg->has_accel = false;
      cfg->width = screen_w;
      cfg->height = screen_h;
      cfg->vmemsz = 0;
      break;
    }
    case AM_GPU_STATUS: {
      AM_GPU_STATUS_T *st = (AM_GPU_STATUS_T *)buf;
      st->ready = true;
      break;
    }
    default:
      break;
  }
}

void ioe_write(int reg, void *buf) {
  if (reg == AM_GPU_FBDRAW) {
    AM_GPU_FBDRAW_T *fb = (AM_GPU_FBDRAW_T *)buf;
    if (fb->pixels != NULL && fb->w > 0 && fb->h > 0) {
      NDL_DrawRect((uint32_t *)fb->pixels, fb->x, fb->y, fb->w, fb->h);
    }
  }
}