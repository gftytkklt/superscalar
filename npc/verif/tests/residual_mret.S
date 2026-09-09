# 残留隐患 B 验证：mret 读在飞 csrw 写入的新 mepc
#   mtvec -> handler（隔离变量）；csrw mepc,verify 后立刻 mret
#   正确行为：跳到 verify，写 PASS 标记 0x600d_0000_0000_0001 到 SRAM[8]
#   修复前行为：读到旧 mepc=0 -> PC 跑飞
	.section .text
	.globl _start
_start:
	li   t0, 0x0f000000
	la   t1, trap_handler
	csrw mtvec, t1
	csrrwi x0, mstatus, 0     # 与前一条 csrw 拉开一拍窗口使用
	la   a0, verify           # mepc 目标 = verify 标签地址
	csrw mepc, a0             # 在飞写 mepc
	mret                      # 紧邻读取，必须看到新 mepc

verify:
	li   t2, 0x600d000000000001
	sd   t2, 8(t0)
	ebreak

trap_handler:                 # 误入 trap 则记 FAIL 标记
	li   t3, 0xbad0000000000000
	li   t4, 0x0f000000
	sd   t3, 16(t4)
	mret