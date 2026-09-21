# B4-Q6 定向探针：移位结果被下一条指令消费（形式化 depth-20 剩余反例的实测对照）
# slli x16, t0, 45 => 0x8000_0000_0000；紧跟 andi x4, x16, -1214 应仍为 0x8000_0000_0000。
# 把 x4 的高低 32 位写 SRAM，供 tb dump 检查（期望 +0:0x00000000 low, +4:0x80000000 high）。
	.section .text
	.globl _start
_start:
	lui   t0, 0x30000
	addi  t0, t0, 4
	slli  x16, t0, 45
	andi  x4, x16, -1214
	li    t1, 0x0f000000
	sw    x4, 0(t1)
	srli  t2, x4, 32
	sw    t2, 8(t1)
	ebreak
