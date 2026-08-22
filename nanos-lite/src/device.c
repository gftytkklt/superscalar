#include <common.h>

#if defined(MULTIPROGRAM) && !defined(TIME_SHARING)
# define MULTIPROGRAM_YIELD() yield()
#else
# define MULTIPROGRAM_YIELD()
#endif

#define NAME(key) \
  [AM_KEY_##key] = #key,

static const char *keyname[256] __attribute__((used)) = {
  [AM_KEY_NONE] = "NONE",
  AM_KEYS(NAME)
};

static AM_GPU_CONFIG_T cfg = {};

size_t serial_write(const void *buf, size_t offset, size_t len) {
  MULTIPROGRAM_YIELD();
  char *tmp = (char*) buf;
  size_t write_size = 0;
  while (write_size < len){
    putch(tmp[write_size]);
    write_size++;
  }
  return write_size;
}

size_t events_read(void *buf, size_t offset, size_t len) {
  MULTIPROGRAM_YIELD();
  AM_INPUT_KEYBRD_T kbd = {};
  bool keydown = 0;
  int keycode = 0;
  kbd = io_read(AM_INPUT_KEYBRD);
  keydown = kbd.keydown;
  keycode = kbd.keycode;
  if(!keycode) {return 0;}
  char *tmp = (char *)buf;
  char *down_const = "kd ";
  char *up_const = "ku ";
  
  if(keydown){strcpy(tmp, down_const);}
  else{strcpy(tmp, up_const);}
  strcat(tmp, keyname[keycode]);
  strcat(tmp, "\n");
  return strlen(tmp);
}

size_t dispinfo_read(void *buf, size_t offset, size_t len) {
  cfg = io_read(AM_GPU_CONFIG);
  int w = cfg.width, h = cfg.height;
  char tmp[64];
  int n = sprintf(tmp, "WIDTH : %d\nHEIGHT:%d\n", w, h);
  if (len > 0) {
    int cpy = (n < len) ? n : len;
    strncpy((char *)buf, tmp, cpy);
    return cpy;
  }
  return 0;
}

size_t fb_write(const void *buf, size_t offset, size_t len) {
  MULTIPROGRAM_YIELD();
  cfg = io_read(AM_GPU_CONFIG);
  size_t px = offset / 4, left = len / 4, done = 0;
  while (left > 0) {
    int y = px / cfg.width, x = px % cfg.width;
    int w = (left < (size_t)(cfg.width - x)) ? left : (cfg.width - x);
    io_write(AM_GPU_FBDRAW, x, y, (uint32_t *)buf + done, w, 1, 1);
    done += w; px += w; left -= w;
  }
  return done * 4;
}

static int audio_sbuf_size = 0;

size_t audio_init() {
  AM_AUDIO_CONFIG_T cfg = io_read(AM_AUDIO_CONFIG);
  audio_sbuf_size = cfg.bufsize;
  return 0;
}

size_t audio_read(void *buf, size_t offset, size_t len) {
  AM_AUDIO_STATUS_T stat = io_read(AM_AUDIO_STATUS);
  int free = audio_sbuf_size - stat.count;
  if (free < 0) free = 0;
  if (len > sizeof(int)) len = sizeof(int);
  if (len > (size_t)free) len = free;
  *(int *)buf = free;
  return sizeof(int);
}

size_t audio_ctrl_write(const void *buf, size_t offset, size_t len) {
  if (len == 12) {
    const int *p = (const int *)buf;
    io_write(AM_AUDIO_CTRL, p[0], p[1], p[2]);
  }
  return len;
}

size_t audio_play_write(const void *buf, size_t offset, size_t len) {
  io_write(AM_AUDIO_PLAY, (Area){(void *)buf, (void *)((uintptr_t)buf + len)});
  return len;
}

void init_device() {
  Log("Initializing devices...");
  ioe_init();
}
