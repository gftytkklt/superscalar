# 验证 WR_ALLOCATE 写 sram 时是否保留 pmem 已存在的非零数据（部分 store 场景）。
# 关键：cache 是写回(write-back)的，WR_MISS 会先从 pmem 读整行再 merge store。
# 若 WR_ALLOCATE 拍把 sram 写 0（覆盖 pmem 读回值），则非 store 字节会丢失。
# 流程：
#   1) sd 0x1122334455667788 -> 0x80000000（WR_MISS 写 cache）
#   2) fence.i -> 脏行写回 pmem，pmem[0..7] = 0x1122334455667788
#   3) sw 0xdeadbeef -> 0x80000008（另一 8B 槽位；WR_MISS 重新读行，再部分写）
#   4) ld 0x80000000 读回，应仍 = 0x1122334455667788（槽位0 必须保留 pmem 值）
#   5) 结果写回 SRAM 供 tb 检查，然后 ebreak
	.section .text
	.globl _start
_start:
	# 1) 先写满一个 8B 槽位并回写 pmem
	li   s0, 0x80000000
	li   s1, 0x1122334455667788>>32
	slli s1, s1, 32
	li   s2, 0x1122334455667788 & 0xffffffff
	or   s1, s1, s2
	sd   s1, 0(s0)            # WR_MISS 写 0x80000000
	fence.i                    # 写回 pmem

	# 3) 部分 store 到另一 8B 槽位（触发新一轮 WR_MISS + WR_RELOAD）
	li   s3, 0xdeadbeef
	sw   s3, 8(s0)            # 写 0x80000008 低 4 字节

	# 4) 读回槽位0，验证 pmem 旧数据保留
	ld   s4, 0(s0)            # 应为 0x1122334455667788

	# 5) 校验和写回 SRAM
	li   s6, 0x0f000000
	sd   s4, 0(s6)            # 槽位0 读回
	ld   s5, 8(s0)
	sd   s5, 8(s6)            # 槽位1 读回
	li   a0, 0
	ebreak
	1: j 1b
