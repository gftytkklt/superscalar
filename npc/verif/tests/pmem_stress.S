# pmem 主存压力测试：在 0x80000000 启动，验证 cache 的替换/脏行写回/双缓存一致性。
# 设计：
#   - 代码在 0x80000000（pmem 装载，icache 服务），数据区独立放 0x80200000
#     （与代码区完全分离，避免写回 pmem 时覆盖代码——否则 icache miss 重读会
#      读到被覆盖的"数据"而非指令，造成假阳性跑飞）；
#   - 写 N 个 64 位伪随机值到 0x80200000+，数据量 > cache 容量(4KB)，强制替换
#     与脏行写回(WR_ALLOCATE 前读旧行、WR_HIT 补写、eviction 写回 pmem)；
#   - 再整区读回校验，错误计数写入 flash SRAM(0x0f000000) 供 tb 检查，然后 ebreak。
# 若替换/回写/一致性有 bug，读回校验会产生大量错误。
	.section .text
	.globl _start
_start:
	li   t0, 0x80200000         # 数据基址（远离代码区 0x80000000）
	li   t1, 0                  # i
	li   t2, 1024               # N：8KB，> 4KB cache，更大压力
	li   t3, 0x9e3779b1         # golden ratio（伪随机乘数）

write_loop:
	bge  t1, t2, write_done
	slli t4, t1, 3              # i*8
	add  t4, t4, t0             # addr = 0x80200000 + i*8
	mul  t5, t1, t3             # pattern = i * 0x9e3779b1
	li   s2, 0x1234567
	add  t5, t5, s2
	sd   t5, 0(t4)              # 写数据区（可能触发 miss/reload/eviction）
	addi t1, t1, 1
	j    write_loop
write_done:

	li   t0, 0x80200000
	li   t1, 0
	li   t6, 0                  # err 计数
	li   t3, 0x9e3779b1
read_loop:
	bge  t1, t2, read_done
	slli t4, t1, 3
	add  t4, t4, t0
	ld   t5, 0(t4)              # 读回（hit / miss->从 pmem reload）
	mul  s0, t1, t3
	li   s2, 0x1234567
	add  s0, s0, s2
	beq  t5, s0, read_next
	addi t6, t6, 1              # 校验失败计数
read_next:
	addi t1, t1, 1
	j    read_loop
read_done:

	# 结果写回 flash SRAM 供 tb 检查
	li   s1, 0x0f000000
	sd   t6, 0(s1)              # err count（应为 0）
	sd   t1, 8(s1)              # total = N
	li   a0, 0
	ebreak
	1: j 1b