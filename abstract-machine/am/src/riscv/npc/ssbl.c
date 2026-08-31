// 阶段 G 二级 bootloader（SSBL，VMA=SRAM、LMA=flash，见 linker-psram-ssbl.ld 的 .ssbl 段）。
//
// 由 FSBL 从 flash 搬入 SRAM 后在此执行。职责（与阶段 D/E boot_sram.c 的 _boot_loader 相同）：
//   1) 用搬移循环把主程序 .text+.rodata+.data 从 flash(LMA) 搬入 PSRAM(VMA)；
//   2) 清零主程序 .bss；
//   3) PSRAM 可缓存 → fence.i（写回 dcache 脏行 + icache 失效）；
//   4) 跳转主程序里的 _trm_init（其内部 loader() 会再搬 .data，与本处幂等）。
//
// 注意：本文件所有代码/数据必须留在 .ssbl 段（VMA=SRAM，已被 FSBL 搬好），
// 不得依赖主程序（.text 在 PSRAM，FSBL 阶段尚未就绪；.rodata 同理）。
// 因此自带搬移循环，不调用 klib memcpy。
#include <stddef.h>
#include <stdint.h>

__attribute__((section(".ssbl")))
static void ssbl_copy_bytes(char *dst, const char *src, size_t n) {
  while (n--) *dst++ = *src++;
}

// 由 linker 提供：主程序 LMA(flash) / VMA(PSRAM) 边界。
extern char _text_lma[], _text_vma[], _sidata[], _sdata[], _edata[];
extern char _bss_start[], _bss_end[];
extern void _trm_init();

__attribute__((section(".ssbl")))
void _ssbl_entry() {
  char *dst, *src;
  long n;

  // 搬 .text+.rodata: flash[_text_lma .. _sidata) -> VMA[_text_vma .. _sdata)
  src = _text_lma;
  dst = _text_vma;
  n   = _sdata - _text_vma;
  if (n > 0) ssbl_copy_bytes(dst, src, (size_t)n);

  // 搬 .data: flash[_sidata .. +len) -> VMA[_sdata .. _edata)
  n = _edata - _sdata;
  if (n > 0) ssbl_copy_bytes(_sdata, _sidata, (size_t)n);

  // 清 .bss
  for (dst = _bss_start; dst < _bss_end; dst++) *dst = 0;

  // 目标区为可缓存 PSRAM → fence.i（写回 + icache 失效）
  if ((uintptr_t)_text_vma >= 0x80000000UL) {
    asm volatile("fence.i");
  }

  // 跳主程序执行（_trm_init 在 .text，已被搬入 PSRAM；它不返回）
  _trm_init();
  for (;;) ;   // 防意外返回
}