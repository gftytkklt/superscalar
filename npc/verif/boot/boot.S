# S3 bootloader (FSBL): 在 flash(0x30000000) 直接执行(XIP, 由 icache 缓存取指加速)。
#   1) 设栈: SRAM 顶;
#   2) 把 mem-test 的 LMA 区间 [_sidata, _text_lma_end) 搬运到 VMA (_sdata, SRAM);
#   3) 清 bss;
#   4) 跳 SRAM 的 _start (mem-test 程序本体, 在 SRAM 运行, 测试 PSRAM)。
# 符号来自 linker-sram.ld。
.section entry, "ax"
.globl _boot_start
.type _boot_start, @function
_boot_start:
  la   sp, _stack_pointer
  # 拷贝 LMA(flash) -> VMA(sram)
  la   t0, _sidata
  la   t1, _text_lma_end
  la   t2, _sdata
copy_loop:
  bgeu t0, t1, copy_done
  lw   t3, 0(t0)
  sw   t3, 0(t2)
  addi t0, t0, 4
  addi t2, t2, 4
  j    copy_loop
copy_done:
  # 清 bss
  la   t0, _bss_start
  la   t1, _bss_end
bss_loop:
  bgeu t0, t1, bss_done
  sw   zero, 0(t0)
  addi t0, t0, 4
  j    bss_loop
bss_done:
  la   t3, _start
  jr   t3              # 跳 SRAM mem-test 入口
  .globl _heap_start
  .globl _stack_pointer