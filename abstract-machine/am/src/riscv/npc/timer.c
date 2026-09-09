#include <am.h>

// 阶段 J4：定时器。CLINT mtime（基址 0x02000000，mtime @ +0xbff8）每拍 +1。
// 注意：RTL 的 mtime 读写按"全地址严格相等"译码（无 size 检查，见 ysyx_22040750.clint
//   I_clint_araddr == MTIME_ADDR），且只支持对寄存器地址的整 8B 访问；若拆成 4B 读写
//   会因地址不精确匹配而读不到/请求挂起（见 STAGE_J4 记录 caveat）。
// 故这里用内联汇编 `ld` 对 0x0200bff8 做**单一 64 位对齐读**（编译器独立保证 arsize=8、
//   araddr=0x0200bff8），避免拆成两次 lw。
#define CLINT_MTIME 0x0200bff8L

void __am_timer_init() {
}

// AM_TIMER_UPTIME：把 mtime（计拍数）按"1 拍 ≈ 1us"换算为微秒。
// （仿真无真实时钟，mtime 每拍 +1；视频等按时基匀速推进即可，无需精确。）
// ⚠️ 时间基准说明（2026-09-02 定夺）：mtime 是"时钟周期数"。AM 规范 AM_TIMER_UPTIME.us
//   本意是"微秒"，换算需 us = mtime / cycles_per_us，而 cycles_per_us 依赖真实 CPU 频率
//   —— 仿真里没定义频率，除以任何数都是臆测。故此处保持 us = mtime（相对基准），
//   不硬编码 divisor；若日后已知真实频率，应由外层软件按 us = mtime/freq_MHz 换算。
void __am_timer_uptime(AM_TIMER_UPTIME_T *uptime) {
  uint64_t mt;
  asm volatile("ld %0, 0(%1)" : "=r"(mt) : "r"(CLINT_MTIME));
  uptime->us = mt;
}

// RTC：SoC 无真实 CMOS/墙钟，仅能由 mtime 粗略推导（此处保持合理占位）。
// 硬件层只提供单调 mtime 计数器，不能回真实时刻。
void __am_timer_rtc(AM_TIMER_RTC_T *rtc) {
  rtc->second = 0;
  rtc->minute = 0;
  rtc->hour   = 0;
  rtc->day    = 1;
  rtc->month  = 1;
  rtc->year   = 1970;
}
