# Test Bug3: signed divide by zero, negative dividend.
# RISC-V spec: DIV x,neg,/0 = -1 (0xFFFF..F), REM x,y,0 = x.
# Suspected: radix2_div gives quotient +1 for negative dividend / 0.
	.section .text
	.globl _start
_start:
	li   t0, 0x0f000000
	li   a0, 5
	li   a4, 0
	neg  a1, a0            # a1 = -5
	div  a2, a1, a4        # spec -1 (0xff..f), suspect +1
	rem  a3, a1, a4        # spec -5
	sd   a2, 0(t0)
	sd   a3, 8(t0)
	div  a5, a0, a4        # spec -1 (0xff..f), positive divd
	sd   a5, 16(t0)
	li   a6, 100
	div  a7, a1, a6        # -5/100 = 0 (control)
	sd   a7, 24(t0)
	ebreak