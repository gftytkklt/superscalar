/* Verify TVM and TSR turn S-mode SATP access/SRET into M illegal traps. */
.option norvc
.option norelax
.section .text
.globl _start
_start:
  la t0, m_trap
  csrw mtvec, t0
  csrw medeleg, zero
  li t0, ((1 << 20) | (1 << 22))
  csrs mstatus, t0
  li t0, 0x1800
  csrc mstatus, t0
  li t0, 0x800
  csrs mstatus, t0
  la t0, s_entry
  csrw mepc, t0
  mret
s_entry:
  li s3, 1
  csrr t0, satp /* TVM: illegal in S */
  li s3, 2
  sret          /* TSR: illegal in S */
  la t0, u_entry
  csrw sepc, t0
  sret
u_entry:
  li a0, 0
  ebreak
m_trap:
  csrr t0, mcause
  li t1, 2
  bne t0, t1, fail
  csrr t0, mtval
  beqz t0, fail
  csrr t0, mstatus
  li t1, 0x1800
  and t0, t0, t1
  li t1, 0x800 /* fault came from S */
  bne t0, t1, fail
  li t0, 1
  beq s3, t0, clear_tvm
  li t0, 2
  beq s3, t0, clear_tsr
  j fail
clear_tvm:
  li t0, (1 << 20)
  csrc mstatus, t0
  j resume
clear_tsr:
  li t0, (1 << 22)
  csrc mstatus, t0
resume:
  csrr t0, mepc
  addi t0, t0, 4
  csrw mepc, t0
  mret
fail:
  li a0, 2
  ebreak
