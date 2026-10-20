#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>
#include <time.h>
#include <fcntl.h>
#include <limits.h>

static int evtdev = -1;
static int fbdev = -1;
static int screen_w = 0, screen_h = 0;
static int canvas_w = 0, canvas_h = 0;
static struct timeval timevar = {};

uint64_t NDL_GetTicks64(void) {
  gettimeofday(&timevar, NULL);
  return (uint64_t)timevar.tv_sec * 1000 + (uint64_t)timevar.tv_usec / 1000;
}

uint32_t NDL_GetTicks() {
  return (uint32_t)NDL_GetTicks64();
}

int NDL_PollEvent(char *buf, int len) {
  if (buf == NULL || len <= 0) return 0;
  buf[0] = '\0';
  if (evtdev < 0 || len == 1) return 0;
  int nread = read(evtdev, buf, len - 1);
  if (nread <= 0) return 0;
  // The native device shim may return snprintf's untruncated length.
  buf[nread < len ? nread : len - 1] = '\0';
  return 1;
}

void NDL_OpenCanvas(int *w, int *h) {
  if (w == NULL || h == NULL || fbdev < 0 || screen_w <= 0 || screen_h <= 0) return;
  int width = *w, height = *h;
  if (width == 0 && height == 0) { width = screen_w; height = screen_h; }
  if (width <= 0 || height <= 0 || width > screen_w || height > screen_h) return;
  if (getenv("NWM_APP")) {
    int fbctl = 4;
    // NWM's resize path stores its framebuffer byte count in an int.
    if ((uint64_t)width * height > INT_MAX / 4) return;
    char buf[64];
    int len = sprintf(buf, "%d %d", width, height);
    // let NWM resize the window and create the frame buffer
    if (write(fbctl, buf, len) != len) return;
    while (1) {
      // 3 = evtdev
      int nread = read(3, buf, sizeof(buf) - 1);
      if (nread <= 0) continue;
      buf[nread < sizeof(buf) ? nread : sizeof(buf) - 1] = '\0';
      if (strcmp(buf, "mmap ok") == 0) break;
    }
    close(fbctl);
    fbdev = 5;
    screen_w = width; screen_h = height;
  }
  canvas_w = width; canvas_h = height;
  *w = width; *h = height;
}

static int write_pixels(const uint8_t *pixels, size_t bytes) {
  while (bytes > 0) {
    ssize_t done = write(fbdev, pixels, bytes);
    // Both framebuffer implementations advance by the returned byte count.
    // Retrying a partial pixel would misalign the next nanos-lite fb_write.
    if (done <= 0 || (size_t)done > bytes || done % 4 != 0) return 0;
    pixels += done;
    bytes -= done;
  }
  return 1;
}

void NDL_DrawRect(uint32_t *pixels, int x, int y, int w, int h) {
  if (fbdev < 0 || pixels == NULL || canvas_w <= 0 || canvas_h <= 0 ||
      x < 0 || y < 0 || w <= 0 || h <= 0 ||
      x > canvas_w || y > canvas_h || w > canvas_w - x || h > canvas_h - y) return;
  uint64_t row_bytes = (uint64_t)w * 4;
  uint64_t bytes = row_bytes * h;
  uint64_t offset = ((uint64_t)screen_w * ((screen_h - canvas_h) / 2 + y) +
                     (screen_w - canvas_w) / 2 + x) * 4;
  uint64_t end = offset + (uint64_t)(h - 1) * screen_w * 4 + row_bytes;
  if (bytes > SIZE_MAX || bytes > LONG_MAX || end > LONG_MAX) return;
  // full-width rects are contiguous rows in the framebuffer: one shot
  if (w == screen_w) {
    if (lseek(fbdev, (off_t)offset, SEEK_SET) != (off_t)offset) return;
    write_pixels((const uint8_t *)pixels, (size_t)bytes);
    return;
  }
  const uint8_t *current_row = (const uint8_t *)pixels;
  // arbitrary canvas
  // this is correct for native
  for (int i=0;i<h;i++){
    if (lseek(fbdev, (off_t)offset, SEEK_SET) != (off_t)offset ||
        !write_pixels(current_row, (size_t)row_bytes)) return;
    current_row += row_bytes;
    offset += (uint64_t)screen_w * 4;
  }
}

static int sbctl_fd = -1, sb_fd = -1;

void NDL_OpenAudio(int freq, int channels, int samples) {
  sbctl_fd = open("/dev/sbctl", 0, 0);
  assert(sbctl_fd != -1);
  sb_fd = open("/dev/sb", 0, 0);
  assert(sb_fd != -1);
  int p[3] = {freq, channels, samples};
  write(sbctl_fd, p, sizeof(p));
}

void NDL_CloseAudio() {
  if (sbctl_fd >= 0) close(sbctl_fd);
  if (sb_fd >= 0) close(sb_fd);
  sbctl_fd = sb_fd = -1;
}

int NDL_PlayAudio(void *buf, int len) {
  if (sb_fd < 0 || len <= 0) return 0;
  return write(sb_fd, buf, len);
}

int NDL_QueryAudio() {
  if (sbctl_fd < 0) return 0;
  int free = 0;
  read(sbctl_fd, &free, sizeof(free));
  return free;
}

int NDL_Init(uint32_t flags) {
  if (evtdev >= 0 && fbdev >= 0) return 0;
  int nwm = getenv("NWM_APP") != NULL;
  int event_fd = nwm ? 3 : open("/dev/events", 0, 0);
  if (event_fd < 0) return -1;
  int fbctl = open("/dev/dispinfo", 0, 0);
  if (fbctl < 0) goto fail;
  char buf[128];
  int nread = read(fbctl, buf, sizeof(buf) - 1);
  close(fbctl);
  if (nread <= 0 || nread >= sizeof(buf)) goto fail;
  buf[nread] = '\0';
  int width = 0, height = 0;
  // format: "WIDTH : <w>\nHEIGHT:<h>\n", whitespace around ':' is flexible
  // (see navy-apps/README.md)
  const char *p = strstr(buf, "WIDTH");
  if (p != NULL) {
    p = strchr(p, ':');
    if (p != NULL) { p ++; while (*p == ' ' || *p == '\t') p ++; width = atoi(p); }
  }
  p = strstr(buf, "HEIGHT");
  if (p != NULL) {
    p = strchr(p, ':');
    if (p != NULL) { p ++; while (*p == ' ' || *p == '\t') p ++; height = atoi(p); }
  }
  if (width <= 0 || height <= 0) goto fail;
  int framebuffer_fd = open("/dev/fb", 0, 0);
  if (framebuffer_fd < 0) goto fail;
  evtdev = event_fd;
  fbdev = framebuffer_fd;
  screen_w = width; screen_h = height;
  return 0;

fail:
  // NWM's inherited event pipe is only adopted after successful initialization.
  if (!nwm) close(event_fd);
  return -1;
}

void NDL_Quit() {
  if (evtdev >= 0) close(evtdev);
  if (fbdev >= 0) close(fbdev);
  evtdev = fbdev = -1;
  screen_w = screen_h = canvas_w = canvas_h = 0;
}
