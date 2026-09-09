# 缓存区微测试：验证 icache/dcache 在可缓存区 [0x80000000,0x88000000) 的真实缓存路径。
# 流程：
#   1) 本程序在 flash(0x30000000) 启动；
#   2) 把"缓存区代码段"(copy_target 到 copy_end) 从 flash 拷贝到 0x80001000；
#   3) jal 到 0x80001000 执行：在 0x80000000 段内做指令取指 + 数据 ld/st；
#   4) 结果写回 flash 区(0x0f000000) 供 tb dump，然后 ebreak。
# 预期（未重构/重构后）：
#   - 指令取指地址 0x8000xxxx 触发 icache 缓存路径(RD_HIT/RD_MISS/RELOAD)；
#   - 数据 ld/st 0x8000xxxx 触发 dcache 缓存路径。
# 注：具体缓存行为(命中/缺失/替换)用 DST 基址+步长控制，下面给一组覆盖 load 命中与 store。
	.section .text
	.globl _start
_start:
	# 拷贝缓存区代码到 0x80001000
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
	# fence.i：把 dcache 里刚写好的脏行回写到 pmem，并失效 icache
	fence.i
	# 跳到缓存区执行
	li   t0, 0x80001000
	jr   t0

# ---- 以下代码在缓存区 0x80001000 执行 ----
copy_target:
	li   t0, 0x80000000      # 缓存区数据基址
	# store 一些数据到缓存区
	li   t1, 0x1122334455667788>>32
	slli t1, t1, 32
	li   t2, 0x1122334455667788 & 0xffffffff
	or   t1, t1, t2
	sd   t1, 0(t0)
	li   t1, 0xaabbccdd
	sd   t1, 8(t0)
	# load 回读（触发 dcache 命中/缺失）
	ld   t3, 0(t0)
	ld   t4, 8(t0)
	# 计算校验和
	add  t5, t3, t4
	# 写结果到 flash 区 SRAM 供 tb 检查
	li   t6, 0x0f000000
	sd   t5, 0(t6)
	sd   t3, 8(t6)
	sd   t4, 16(t6)
	# 收尾
	li   a0, 0
	ebreak
	1: j 1b
copy_end: