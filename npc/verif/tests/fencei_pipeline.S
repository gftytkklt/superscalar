# B4-Q4：fence.i 反例（自修改代码 SMC）——"无 fence.i 冲刷则流水线出错"
#
# 流程：
#   1) 向可缓存 PSRAM(0x80002000) 写入 stub_v1（li a0,0x11; jr ra），fence.i 使其对取指可见；
#   2) 执行 stub_v1 → 期望 a0=0x11，存 SRAM+0；
#   3) 自修改：把 stub 第一条改成 li a0,0x22（dcache 脏行）；
#   4) **fence.i**（流水线冲刷 + icache 失效 + dcache 脏行回写）；
#   5) 再次执行 → 期望 a0=0x22，存 SRAM+8；校验并写 marker；
#   6) ebreak 结束；若校验失败 → 写 0xBAD 并进入 fail_loop（由 VTB_MAXT 超时报 FAIL，
#      不会永久卡死；正常运行时长远小于上限）。
# 若第 4 步的 fence.i 失效：icache 仍持旧行 → 第二次执行返回 0x11 → 走 fail 分支。
	.section .text
	.globl _start
_start:
	li   t0, 0x80002000          # 目标代码区（可缓存 PSRAM）
	li   t1, 0x01100513          # addi a0, x0, 0x11
	sw   t1, 0(t0)
	li   t1, 0x00008067          # jalr x0, 0(ra)  = jr ra
	sw   t1, 4(t0)
	fence.i                      # 让初始 stub 对取指可见

	li   s0, 0x0f000000          # 结果区（SRAM，tb dump）
	jal  ra, call_stub
	sw   a0, 0(s0)               # 第一次：期望 0x11

	li   t0, 0x80002000
	li   t1, 0x02200513          # addi a0, x0, 0x22（自修改）
	sw   t1, 0(t0)

	fence.i                      # ★ 关键指令：失效则本测试必失败

	jal  ra, call_stub
	sw   a0, 8(s0)               # 第二次：期望 0x22

	li   t2, 0x22
	bne  a0, t2, fail
	li   t0, 0x5A5A
	sw   t0, 16(s0)              # marker = 成功
	ebreak

call_stub:
	li   t3, 0x80002000
	jr   t3                      # 进入 stub；stub 末尾 jr ra 返回

fail:
	li   t0, 0xBAD
	sw   t0, 16(s0)              # marker = 失败
1:	j    1b                      # 有界等待：harness VTB_MAXT 超时 → FAIL
