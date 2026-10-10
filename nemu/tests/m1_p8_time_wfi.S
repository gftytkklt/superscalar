.option norvc
.section .text
.globl _start
_start:
  la t0, trap
  csrw mtvec, t0
  li s0, 0
  li s1, 0
  rdtime s2
  csrw time, zero // illegal: read-only
  csrw mcounteren, zero
  li t0, 0x200800 // S-mode, TW=1
  csrw mstatus, t0
  la t0, supervisor
  csrw mepc, t0
  mret
supervisor:
  rdtime t0 // illegal: mcounteren.TIME=0
  wfi       // illegal: TW=1
  li s1, 1
  ecall
  rdtime t0
  wfi       // legal hint
  csrw scounteren, zero
  la t0, user
  csrw sepc, t0
  csrw sstatus, zero
  sret
user:
  rdtime t0 // illegal: scounteren.TIME=0
  wfi       // illegal in U
  li s1, 2
  ecall
  rdtime t0 // allowed after M opens both gates
  li s1, 3
  ecall
  j fail
trap:
  csrr t0, mcause
  li t1, 2
  beq t0, t1, illegal
  li t1, 9
  beq t0, t1, service
  li t1, 8
  bne t0, t1, fail
service:
  li t0, 3
  beq s1, t0, finish
  li t0, 2
  csrw mcounteren, t0
  csrw scounteren, t0
  li t0, 0x200000
  csrc mstatus, t0
  j advance
illegal:
  addi s0, s0, 1
advance:
  csrr t0, mepc
  addi t0, t0, 4
  csrw mepc, t0
  mret
finish:
  li t0, 5
  bne s0, t0, fail
  li a0, 0
  ebreak
fail:
  li a0, 1
  ebreak
