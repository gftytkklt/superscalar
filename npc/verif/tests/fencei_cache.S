# S1.2c 验证：完整 fence.i（dcache 脏行回写 + icache 失效）
# 流程：
#   1) 本程序在 flash(0x30000000) 启动（MMIO 取指）；
#   2) 把一段代码(copy_target..copy_end)从 flash 拷到可缓存区 0x80001000（写回 dcache）；
#   3) fence.i：应触发 dcache 把脏行回写到 pmem + icache 失效；
#   4) jal 到 0x80001000 执行（icache 从 pmem 取回刚写好的代码）；
#   5) 结果写回 flash SRAM(0x0f000000) 供 tb 检查，然后 ebreak。
# 若 fence.i 回写不成立，则 0x80001000 取到的是 pmem 旧值(0)，程序会跑飞/卡死。
	.section .text
	.globl _start
_start:
	la   t0, copy_target
	la   t1, copy_end
	li   t2, 0x80001000
copy_loop:
	bgeu t0, t1, copy_done
	lw   t3, 0(t0)
	sw   t3, 0(t2)
	addi t0, t0, 4
	addi t2, t2, 4
	j    copy_loop
copy_done:
	fence.i
	li   t0, 0x80001000
	jr   t0

# ---- 以下代码在缓存区 0x80001000 执行 ----
copy_target:
	li   t6, 0x0f000000
	li   t0, 0x12345678
	sd   t0, 0(t6)     # 校验值写回 SRAM
	li   a0, 0
	ebreak
	1: j 1b
copy_end:
