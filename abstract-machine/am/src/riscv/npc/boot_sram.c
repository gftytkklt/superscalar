// 阶段 D/E 的 C bootloader（驻留 flash，VMA=LMA=flash，见 linker-sram/psram.ld 的 .bootloader 段）。
//
// 职责（复用 trm.c loader() 的 memcpy 搬运思路，用 C 实现而非手写汇编）：
//   1) 用搬移循环（等价 memcpy）把 .text+.rodata+.data 从 flash(LMA) 搬入目标(VMA)
//      —— 目标为 SRAM(阶段 D, 不可缓存, 无需 fence.i) 或 PSRAM(阶段 E, 可缓存, 需 fence.i)；
//   2) 清零 .bss；
//   3) 若目标是可缓存区(PSRAM)，执行 fence.i（写回 dcache 脏行 + icache 失效），
//      否则跳过（避免无谓的清空缓存开销）；
//   4) 跳转到目标区里的 _trm_init（其内部 loader() 会再搬 .data，与本处幂等）。
//
// 注意：本文件所有代码必须留在 flash 段（.bootloader），不得依赖会被搬走的 .text/.rodata
// （因此自带搬移循环，不调用 klib memcpy）。
#include <stddef.h>
#include <stdint.h>

__attribute__((section(".bootloader")))
static void copy_bytes(char *dst, const char *src, size_t n) {
  while (n--) *dst++ = *src++;
}

// 由 linker 提供：LMA(flash) / VMA(目标区) 边界。
extern char _text_lma[], _text_vma[], _sidata[], _sdata[], _edata[];
extern char _bss_start[], _bss_end[];
extern void _trm_init();

__attribute__((section(".bootloader")))
void _boot_loader() {
  char *dst, *src;
  long n;

  // 搬 .text+.rodata: flash[_text_lma .. _sidata) -> VMA[_text_vma .. _sdata)
  // 注意 LMA 与 VMA 区间长度一致（链接器保证段连续）。
  src = _text_lma;
  dst = _text_vma;
  n   = _sdata - _text_vma;
  if (n > 0) copy_bytes(dst, src, (size_t)n);

  // 搬 .data: flash[_sidata .. +len) -> VMA[_sdata .. _edata)
  n = _edata - _sdata;
  if (n > 0) copy_bytes(_sdata, _sidata, (size_t)n);

  // 清 .bss
  for (dst = _bss_start; dst < _bss_end; dst++) *dst = 0;

  // 目标区若为可缓存内存（PSRAM），搬移写入在 dcache 脏行，跳转执行前需
  // fence.i（写回 + icache 失效），否则 icache 取指读到旧数据。
  // SRAM(0x0f000000) 不可缓存，无需 fence.i。
  if ((uintptr_t)_text_vma >= 0x80000000UL) {
    asm volatile("fence.i");
  }

  // 跳转到目标区执行（_trm_init 在 .text，已被搬入目标区；它不返回）
  _trm_init();
  for (;;) ;   // 防意外返回
}