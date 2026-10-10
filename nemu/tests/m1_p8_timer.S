.option norvc
.section .text
.globl _start
_start:
  la t0, mtrap
  csrw mtvec, t0
  li s0, 0
  li s1, 0x02004000
  li s2, 0x0200bff8
  li s3, 0
  li t0, 128
  csrw mie, t0
  ld t0, 0(s2)
  li t1, 20000
  add t0, t0, t1
  sd t0, 0(s1)
1: csrr t0, mip
  andi t0, t0, 128
  beqz t0, 1b
  bnez s0, fail
  li t0, 8
  csrs mstatus, t0
2: beqz s0, 2b
  li t0, 1
  bne s0, t0, fail
  csrr t0, mip
  andi t0, t0, 128
  bnez t0, fail
  // Forward a second MTIP through software STIP to S-mode, like non-SSTC SBI.
  li s3, 1
  li s4, 0
  la t0, strap
  csrw stvec, t0
  li t0, 32
  csrw mideleg, t0
  li t0, 0xa0
  csrw mie, t0
  li t0, 0x882
  csrw mstatus, t0
  la t0, supervisor
  csrw mepc, t0
  ld t0, 0(s2)
  li t1, 10000
  add t0, t0, t1
  sd t0, 0(s1)
  mret
supervisor:
  wfi
  beqz s4, supervisor
  li s3, 2
  ecall
  j fail
strap:
  csrr t0, scause
  li t1, 0x8000000000000005
  bne t0, t1, fail
  addi s4, s4, 1
  ecall // M clears STIP, S-mode cannot write it directly
  sret
mtrap:
  csrr t0, mcause
  li t1, 9
  beq t0, t1, service
  li t1, 0x8000000000000007
  bne t0, t1, fail
  li t0, -1
  sd t0, 0(s1)
  addi s0, s0, 1
  beqz s3, 3f
  li t0, 32
  csrs mip, t0
3: mret
service:
  li t0, 32
  csrc mip, t0
  li t0, 2
  beq s3, t0, finish
  csrr t0, mepc
  addi t0, t0, 4
  csrw mepc, t0
  mret
finish:
  li t0, 2
  bne s0, t0, fail
  li t0, 1
  bne s4, t0, fail
  li a0, 0
  ebreak
fail:
  li a0, 1
  ebreak
