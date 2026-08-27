# 纯 dcache 缓存路径测试：
#   指令留在 flash(0x30000000, MMIO 取指)，仅数据访存走可缓存区 0x80000000。
# 验证 dcache 在缓存区的写分配/命中/读：
#   - sd 到 0x80000000 / 0x80000008（同一 cacheline）
#   - ld 回读；换 cacheline 触发新一轮 miss
# 校验和写回 flash SRAM(0x0f000000) 供 tb 检查，然后 ebreak。
	.section .text
	.globl _start
_start:
	li   s0, 0x80000000        # 缓存区数据基址(偶数寄存器)
	# 写两个 64 位值到同一 cacheline
	li   s1, 0x1122334455667788>>32
	slli s1, s1, 32
	li   s2, 0x1122334455667788 & 0xffffffff
	or   s1, s1, s2            # s1 = 0x1122334455667788
	sd   s1, 0(s0)             # dcache 写分配
	li   s1, 0xaabbccdd
	sd   s1, 8(s0)             # 同 line 另一 8B
	# 读回
	ld   s3, 0(s0)
	ld   s4, 8(s0)
	add  s5, s3, s4            # 校验和
	# 换个 cacheline（不同索引，触发新一轮 miss）
	li   s6, 0x80002000
	sd   s5, 0(s6)
	ld   s7, 0(s6)
	# 结果写回 flash SRAM
	li   s6, 0x0f000000
	sd   s3, 0(s6)             # 0x1122334455667788
	sd   s4, 8(s6)             # 0xaabbccdd
	sd   s5, 16(s6)            # 校验和
	sd   s7, 24(s6)            # 第二 line 读回
	# 收尾
	li   a0, 0
	ebreak
	1: j 1b
