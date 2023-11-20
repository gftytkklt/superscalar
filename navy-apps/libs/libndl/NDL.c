#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/time.h>
#include <time.h>
#include <fcntl.h>

static int evtdev = -1;
static int fbdev = -1;
static int fbctl = -1;
static int screen_w = 0, screen_h = 0;
static int canvas_w = 0, canvas_h = 0;
static struct timeval timevar = {};

uint32_t NDL_GetTicks() {
  gettimeofday(&timevar, NULL);
  return (timevar.tv_sec*1000 + (timevar.tv_usec)/1000);
}

int NDL_PollEvent(char *buf, int len) {
  return read(evtdev, buf, len) ? 1 : 0;
}

void NDL_OpenCanvas(int *w, int *h) {
  if (getenv("NWM_APP")) {
    int fbctl = 4;
    fbdev = 5;
    screen_w = *w; screen_h = *h;
    char buf[64];
    int len = sprintf(buf, "%d %d", screen_w, screen_h);
    // let NWM resize the window and create the frame buffer
    write(fbctl, buf, len);
    while (1) {
      // 3 = evtdev
      int nread = read(3, buf, sizeof(buf) - 1);
      if (nread <= 0) continue;
      buf[nread] = '\0';
      if (strcmp(buf, "mmap ok") == 0) break;
    }
    close(fbctl);
  }
  if ((*w==0) || (*h==0)){*w = screen_w;*h = screen_h;}
  canvas_w = *w;canvas_h = *h;
  printf("canvas: %d*%d\n",canvas_w, canvas_h);
}

void NDL_DrawRect(uint32_t *pixels, int x, int y, int w, int h) {
  int offset_y = screen_w*((screen_h-canvas_h)/2+y);
  int offset_x = (screen_w-canvas_w)/2 + x;
  int offset = offset_y + offset_x;
  uint32_t *current_row = pixels;
  // arbitrary canvas
  // this is correct for native
  for (int i=0;i<h;i++){
    lseek(fbdev, offset*4, SEEK_SET);
    write(fbdev, current_row, w*4);
    current_row += w;
    offset += screen_w;
  }
}

void NDL_OpenAudio(int freq, int channels, int samples) {
}

void NDL_CloseAudio() {
}

int NDL_PlayAudio(void *buf, int len) {
  return 0;
}

int NDL_QueryAudio() {
  return 0;
}

int NDL_Init(uint32_t flags) {
  if (getenv("NWM_APP")) {
    evtdev = 3;
  }
  else {
    evtdev = open("/dev/events", 0, 0);
  }
  fbctl = open("/dev/dispinfo", 0, 0);
  char buf[64];
  read(fbctl, buf, 64);
  sscanf(buf, "%d, %d", &screen_w, &screen_h);
  close(fbctl);
  fbdev = open("/dev/fb", 0, 0);
  printf("screen_size: %d*%d\n", screen_w, screen_h);
  printf("boot time: %d ms\n", NDL_GetTicks());
  return 0;
}

void NDL_Quit() {
  close(evtdev);
  close(fbdev);
}
