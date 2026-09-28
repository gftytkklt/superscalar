/* M1-P7: sfence.vma is illegal in S with TVM and always illegal in U. */
.option norvc
.option norelax
.section .text
.globl _start
_start:
  la t0, m_fail
  csrw mtvec, t0
  la t0, s_trap
  csrw stvec, t0
  li t0, (1 << 2)
  csrw medeleg, t0
  la t0, s_entry
  csrw mepc, t0
  li t0, 0x1800
  csrc mstatus, t0
  li t0, ((1 << 11) | (1 << 20))
  csrs mstatus, t0 /* MPP=S, TVM=1 */
  mret

s_entry:
  li s0, 0
s_sfence:
  sfence.vma zero, zero
s_after:
  li s0, 1
  la t0, u_sfence
  csrw sepc, t0
  li t0, (1 << 8)
  csrc sstatus, t0 /* SPP=U */
  sret

u_sfence:
  sfence.vma zero, zero
  j fail

s_finish:
  li a0, 0
  ebreak

s_trap:
  csrr t0, scause
  li t1, 2
  bne t0, t1, fail
  csrr t0, stval
  li t1, 0x12000073
  bne t0, t1, fail
  csrr t0, sepc
  beqz s0, 1f
  la t1, u_sfence
  bne t0, t1, fail
  la t0, s_finish
  csrw sepc, t0
  li t0, (1 << 8)
  csrs sstatus, t0 /* return to S */
  sret
1:
  la t1, s_sfence
  bne t0, t1, fail
  la t0, s_after
  csrw sepc, t0
  sret

m_fail:
fail:
  li a0, 1
  ebreak
