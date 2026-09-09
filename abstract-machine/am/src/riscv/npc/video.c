#include <am.h>

// 阶段 J4：GPU（VGA 帧缓冲）IOE。
// 帧缓冲在 SoC 外设 vga_top_apb.v（APB 从端，基址 0x21000000，2MB=640x480x4 RGBA，
// mmio 区 / difftest skip）。CPU 直接对帧缓冲"词"写 32bit 像素；**无需软件侧二次缓冲**
// （讲义：帧缓冲暂以 RTL reg 阵列实现，注意"帧缓冲放内存"的带宽/一致性问题）。
//   AM_GPU_FBDRAW{x,y,pixels,w,h,sync} → 按 RGBA 写到 fb[(y*640+x)]；sync 在 RTL 持续扫描
//   的帧缓冲上无意义，忽略。
//   像素格式：RTL 取 px[23:16]=R、px[15:8]=G、px[7:0]=B，故 AM 用 0x00RRGGBB。
#define VGA_BASE 0x21000000UL
#define VGA_W    640
#define VGA_H    480

void __am_gpu_init() {
}

void __am_gpu_config(AM_GPU_CONFIG_T *cfg) {
  *cfg = (AM_GPU_CONFIG_T) {
    .present = true, .has_accel = false,
    .width = VGA_W, .height = VGA_H,
    .vmemsz = VGA_W * VGA_H * 4
  };
}

void __am_gpu_status(AM_GPU_STATUS_T *stat) {
  stat->ready = true;
}

void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *ctl) {
  int x = ctl->x, y = ctl->y, w = ctl->w, h = ctl->h;
  if (w <= 0 || h <= 0) return;              // sync-only 调用（0x0 尺寸）忽略
  volatile uint32_t *fb = (volatile uint32_t *)VGA_BASE;
  uint32_t *pix = (uint32_t *)ctl->pixels;
  for (int j = 0; j < h; j++)
    for (int i = 0; i < w; i++)
      fb[(y + j) * VGA_W + (x + i)] = pix[j * w + i];
}
