# B4-Q7/OPT-11 定向：load→use 紧邻消费（去 MEM 项后由 MEM 拍 rvalid 数据前递覆盖）
# 覆盖 ld/lw/lwu/lh/lhu/lb/lbu、ALU/分支/store 数据/store 地址/load 地址依赖，
# 以及命中（已由 sd 填充行）、冷缺失（0x80020000）、MMIO（0x0f000000 非缓存）三类延迟。
# 自校验：每例实际值与期望值 XOR 后累积到 s1（分支用例失败则 s1+1）；
#         s1==0 -> 写 PASS 标记 0x600d... 到 SRAM 后 ebreak；否则写错误码后死循环
#         （由 harness VTB_MAXT 超时报 FAIL）。
	.section .text
	.globl _start
_start:
	li    s0, 0x80000000            # PSRAM（可缓存）
	li    s1, 0                     # 错误累积
	li    s3, 0x0f000000            # SRAM 结果区（tb dump）

	li    t0, 0x8877665544332211
	sd    t0, 0(s0)                 # 填充行：后续 load 命中
	li    t0, 0x1122334455667788
	sd    t0, 8(s0)
	li    t0, 0x80000008
	sd    t0, 16(s0)                # load→load 地址依赖用指针

	# 1) ld -> addi（64 位）
	li    t3, 0x8877665544332212
	ld    t0, 0(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 2) ld -> sd（store 数据依赖）
	li    t3, 0x1122334455667788
	ld    t0, 8(s0)
	sd    t0, 24(s0)
	ld    t1, 24(s0)
	xor   t4, t1, t3
	or    s1, s1, t4

	# 3) lw（正数符号扩展）-> addi
	li    t3, 0x44332212
	lw    t0, 0(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 4) lw（负数符号扩展）-> addi
	li    t3, -0x778899AA           # 0xFFFFFFFF88776655 + 1
	lw    t0, 4(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 5) lwu（零扩展）-> addi
	li    t3, 0x44332212
	lwu   t0, 0(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 6) lh（负）-> addi
	li    t3, -0x7788               # 0xFFFFFFFFFFFF8877 + 1
	lh    t0, 6(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 7) lhu -> addi
	li    t3, 0x8878
	lhu   t0, 6(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 8) lb（负）-> addi
	li    t3, -0x77                 # 0xFFFFFFFFFFFFFF88 + 1
	lb    t0, 7(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 9) lbu -> addi
	li    t3, 0x89
	lbu   t0, 7(s0)
	addi  t1, t0, 1
	xor   t4, t1, t3
	or    s1, s1, t4

	# 10) ld -> beq（分支立即消费）
	li    t3, 0x8877665544332211
	ld    t0, 0(s0)
	beq   t0, t3, 10f
	addi  s1, s1, 1
10:

	# 11) ld -> ld（地址依赖）
	li    t3, 0x1122334455667788
	ld    t0, 16(s0)
	ld    t1, 0(t0)
	xor   t4, t1, t3
	or    s1, s1, t4

	# 12) ld -> sd（作为 store 基址）
	li    t4, 0x00000000deadbeef
	ld    t0, 16(s0)
	sd    t4, 32(t0)
	ld    t1, 40(s0)
	li    t3, 0x00000000deadbeef
	xor   t5, t1, t3
	or    s1, s1, t5

	# 13) 冷缺失 load（0x80020000 首次访问）-> addi
	li    t3, 1
	li    t4, 0x80020000
	ld    t0, 0(t4)
	addi  t1, t0, 1
	xor   t5, t1, t3
	or    s1, s1, t5

	# 14) MMIO load（0x0f000000 非缓存，初值 0）-> addi
	li    t3, 1
	li    t4, 0x0f000000
	ld    t0, 0(t4)
	addi  t1, t0, 1
	xor   t5, t1, t3
	or    s1, s1, t5

	# 15) rs1+rs2 来自紧邻两条 load
	li    t3, 0x9999999999999999   # 0x8877665544332211 + 0x1122334455667788
	ld    t0, 0(s0)
	ld    t5, 8(s0)
	add   t1, t0, t5
	xor   t4, t1, t3
	or    s1, s1, t4

	beq   s1, x0, pass
	sd    s1, 0(s3)                 # 失败：错误累积写 SRAM
fail:
	j     fail                      # 死循环 → VTB_MAXT 超时 → FAIL
pass:
	li    t0, 0x600d000000000001
	sd    t0, 0(s3)
	ebreak
