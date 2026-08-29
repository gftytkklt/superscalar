# PSRAM 可缓存区 32B burst 读写检查（主存模式 ptest）
# 验证可缓存区 [0x80000000, 0x80040000) 支持 32B cacheline 对齐 burst 读写：
#   - 数据区 0x80010000（远离代码区 0x80000000）：写 4×sd = 32B，读回校验
#   - 4MB 上界附近 0x8003ffc0：burst [0x8003ffc0, 0x80040000) 在 PSRAM 内
# 任何校验失败 err++，err 写回 SRAM(0x0f000000) 供 tb 检查，然后 ebreak。
	.section .text
	.globl _start
_start:
	li   s9, 0                    # err 计数

	# ---- 32B burst @ 0x80010000 ----
	li   t0, 0x80010000
	li   t1, 0x1111111100000001
	sd   t1, 0(t0)
	li   t1, 0x2222222200000002
	sd   t1, 8(t0)
	li   t1, 0x3333333300000003
	sd   t1, 16(t0)
	li   t1, 0x4444444400000004
	sd   t1, 24(t0)
	ld   t2, 0(t0)
	li   t1, 0x1111111100000001
	bne  t2, t1, e1
	ld   t2, 8(t0)
	li   t1, 0x2222222200000002
	bne  t2, t1, e1
	ld   t2, 16(t0)
	li   t1, 0x3333333300000003
	bne  t2, t1, e1
	ld   t2, 24(t0)
	li   t1, 0x4444444400000004
	bne  t2, t1, e1
	j    ok1
e1:
	addi s9, s9, 1
ok1:

	# ---- 32B burst @ 4MB 上界附近 0x8003ffc0 ----
	li   t0, 0x8003ffc0
	li   t1, 0x5555555500000005
	sd   t1, 0(t0)
	li   t1, 0x6666666600000006
	sd   t1, 8(t0)
	li   t1, 0x7777777700000007
	sd   t1, 16(t0)
	li   t1, 0x8888888800000008
	sd   t1, 24(t0)
	ld   t2, 0(t0)
	li   t1, 0x5555555500000005
	bne  t2, t1, e2
	ld   t2, 8(t0)
	li   t1, 0x6666666600000006
	bne  t2, t1, e2
	ld   t2, 16(t0)
	li   t1, 0x7777777700000007
	bne  t2, t1, e2
	ld   t2, 24(t0)
	li   t1, 0x8888888800000008
	bne  t2, t1, e2
	j    ok2
e2:
	addi s9, s9, 1
ok2:

	# ---- 结果写回 SRAM ----
	li   s0, 0x0f000000
	sd   s9, 0(s0)
	ebreak