// 阶段 G 一级 bootloader（FSBL，驻留 flash，VMA=LMA=flash，见 linker-psram-ssbl.ld 的 .fsbl 段）。
//
// 职责：
//   1) 用搬移循环把 SSBL 从 flash(LMA, _ssbl_lma) 搬入 SRAM(VMA, _ssbl_vma)，
//      长度 = _ssbl_size（链接器符号，值为字节数）；
//   2) 跳 SSBL 入口 _ssbl_entry（SRAM，已搬好），由 SSBL 负责把主程序搬入 PSRAM。
//
// 注意：
//   - 本文件所有代码必须留在 flash 段（.fsbl），不依赖会被搬走的 .text/.rodata
//     （因此自带搬移循环，不调用 klib memcpy）。
//   - SRAM 不可缓存，搬入即生效，无需 fence.i。
#include <stddef.h>
#include <stdint.h>

__attribute__((section(".fsbl")))
static void fsbl_copy_bytes(char *dst, const char *src, size_t n) {
  while (n--) *dst++ = *src++;
}

// 由 linker-psram-ssbl.ld 提供：SSBL 的 LMA(flash) / VMA(SRAM) / 字节数。
extern char _ssbl_lma[], _ssbl_vma[], _ssbl_size[];
extern void _ssbl_entry();

__attribute__((section(".fsbl")))
void _fsbl_loader() {
  size_t n = (size_t)&_ssbl_size;
  if (n > 0) fsbl_copy_bytes(_ssbl_vma, _ssbl_lma, n);

  // 跳 SSBL（SRAM）执行；SSBL 不返回
  _ssbl_entry();
  for (;;) ;   // 防意外返回
}