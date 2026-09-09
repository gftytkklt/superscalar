# 阶段 D/E 启动入口（flash, VMA=LMA=flash, .bootloader 段）：
#   1) 设栈指针 sp = SRAM 栈顶（绝对地址）
#   2) 跳 C bootloader（boot_sram.c 的 _boot_loader，也在 flash 段），由它用
#      搬移循环把主程序从 flash(LMA) 搬入目标区(VMA) 并跳 _trm_init。
.section entry, "ax"
.globl _start
.type _start, @function
_start:
  la   sp, _stack_pointer
  call _boot_loader
1:
  j 1b
.size _start, . - _start