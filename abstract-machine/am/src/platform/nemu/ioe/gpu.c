#include <am.h>
#include <nemu.h>
// #include <stdio.h>
#define SYNC_ADDR (VGACTL_ADDR + 4)
static int w = 400;
static int h = 300;
void __am_gpu_init() {
  // int i;
  w = inw(VGACTL_ADDR+2);  // TODO: get the correct width
  h = inw(VGACTL_ADDR);  // TODO: get the correct height
  // uint32_t *fb = (uint32_t *)(uintptr_t)FB_ADDR;
  // for (i = 0; i < w * h; i ++) fb[i] = i;
  // outl(SYNC_ADDR, 1);
}

void __am_gpu_config(AM_GPU_CONFIG_T *cfg) {
  *cfg = (AM_GPU_CONFIG_T) {
    .present = true, .has_accel = false,
    // .width = inw(VGACTL_ADDR+2), .height = inw(VGACTL_ADDR),
    // .vmemsz = cfg->width*cfg->height*4,
    .width = w, .height = h,
    .vmemsz = w*h*4,
  };
}

void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *ctl) {
  if (ctl->sync) {
    outl(SYNC_ADDR, 1);
  }
  int x = ctl->x;
  int y = ctl->y;
  int blk_w = ctl->w;
  int blk_h = ctl->h;
  if(blk_w == 0 || blk_h == 0) {return;}
  // printf("%d, %d: %d*%d\n", x, y, blk_w, blk_h);
  int *pixels = (int *)ctl->pixels;
  int base = w*y+x;
  // int base = FB_ADDR + (w*y+x)*4;// tl of rect area
  // int offt = 0;
  // int index = 0;
  for (int row=0;row<blk_h;row++){
    // offt = 0;
    for(int col=0;col<blk_w;col++){
      // outl(base+offt, pixels[index++]);
      // offt += 4;
      int index = row*blk_w+col;
      int offset = row*w+col;
      outl(FB_ADDR+(base+offset)*4, pixels[index]);
    }
    // base += w*4;
  }
}

void __am_gpu_status(AM_GPU_STATUS_T *status) {
  status->ready = true;
}
