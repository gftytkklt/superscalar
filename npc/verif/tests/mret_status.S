# F0046 DUT dependency: MRET pops MPP; the next M-mode trap saves M again.
# Real SoC difftest and the existing bare-core SRAM PASS marker both apply.
.option nopic
.section .text
.globl _start
_start:
  la t0, handler
  csrw mtvec, t0
  li t0, 0xa00001880
  csrw mstatus, t0
  la t0, resumed
  csrw mepc, t0
  mret
resumed:
  csrr t0, mstatus
  li t1, 0xa00000088
  bne t0, t1, fail
  li s0, 0
  li s1, 0
loop:
  andi s2, s0, 1
  slli s2, s2, 3
  li t0, 0xa00000000
  or t0, t0, s2
  csrw mstatus, t0
  ecall
  csrr t0, mstatus
  li t1, 0xa00000080
  or t1, t1, s2
  bne t0, t1, fail
  addi s0, s0, 1
  li t0, 8
  bltu s0, t0, loop
  bne s0, s1, fail
  li t0, 0x0f000000
  li t1, 0x600d000000000001
  sd t1, 8(t0)
  li a0, 0
  ebreak
handler:
  csrr t0, mcause
  li t1, 11
  bne t0, t1, fail
  csrr t0, mstatus
  li t1, 0xa00001800
  slli t2, s2, 4
  or t1, t1, t2
  bne t0, t1, fail
  addi s1, s1, 1
  csrr t0, mepc
  addi t0, t0, 4
  csrw mepc, t0
  mret
fail:
  li t0, 0x0f000000
  li t1, 0xbad0000000000000
  sd t1, 16(t0)
  li a0, 1
  ebreak
