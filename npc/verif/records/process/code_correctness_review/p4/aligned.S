.section .text._trm_init,"ax"
.global _trm_init
_trm_init:
 la a0, test_bss
 la a1, test_data
 la a2, aligned_rodata
 ret
.section .data,"aw"
.global test_data
test_data: .byte 7
.section .bss,"aw",@nobits
.global test_bss
test_bss: .space 1

.section .rodata,"a"
.balign 64
.global aligned_rodata
aligned_rodata: .quad 0x1122334455667788
