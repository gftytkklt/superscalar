# 阶段 G 一级 bootloader 入口（FSBL，VMA=LMA=flash，.fsbl 段）：
#   1) 设栈指针 sp = SRAM 栈顶（绝对地址）
#   2) 跳 C FSBL（fsbl.c 的 _fsbl_loader，也在 flash 段），由它把 SSBL 从 flash 搬入
#      SRAM 并跳 SSBL 入口（_ssbl_entry，SRAM）执行。
.section entry, "ax"
.globl _start
.type _start, @function
_start:
  la   sp, _stack_pointer
  call _fsbl_loader
1:
  j 1b
.size _start, . - _start