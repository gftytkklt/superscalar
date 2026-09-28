/* M1-P6: reservation lifecycle and RV64 W sign-extension checks. */
.section .text
.globl _start
_start:
  csrr t0, misa
  andi t0, t0, 1
  beqz t0, fail

  la t0, word_a
  li t1, 0x80000000
  sw t1, 0(t0)
  lr.w.aq t2, (t0)
  li t3, -2147483648
  bne t2, t3, fail
  sc.w.rl t4, t1, (t0)
  bnez t4, fail
  sc.w t4, t1, (t0)         /* A second SC has no reservation. */
  li t3, 1
  bne t4, t3, fail

  lr.w t2, (t0)
  addi t5, t0, 8
  sc.w t4, t1, (t5)         /* Wrong address fails and consumes LR. */
  bne t4, t3, fail
  sc.w t4, t1, (t0)
  bne t4, t3, fail

  lr.w t2, (t0)
  sw zero, 0(t0)           /* Ordinary store ends the reservation. */
  sc.w t4, t1, (t0)
  bne t4, t3, fail
  lw t2, 0(t0)
  bnez t2, fail

  li t1, 0x123456789abcdef0
  lr.d t2, (t0)
  sc.d t4, t1, (t0)
  bnez t4, fail
  ld t2, 0(t0)
  bne t2, t1, fail

  li t1, -1
  sw t1, 0(t0)
  li t1, 1
  amoadd.w.aqrl t2, t1, (t0)
  li t3, -1
  bne t2, t3, fail
  lw t2, 0(t0)
  bnez t2, fail

  la t5, misaligned_trap
  csrw mtvec, t5
  li s2, 0
  addi s1, t0, 1
  li s0, 4
  lr.w t2, (s1)            /* LR alignment exception: load cause 4. */
  li t3, 1
  bne s2, t3, fail
  li s0, 6
  amoadd.w t2, t1, (s1)    /* AMO alignment exception: store cause 6. */
  li t3, 2
  bne s2, t3, fail

  li a0, 0
  ebreak
misaligned_trap:
  csrr t6, mcause
  bne t6, s0, fail
  csrr t6, mtval
  bne t6, s1, fail
  csrr t6, mepc
  addi t6, t6, 4
  csrw mepc, t6
  addi s2, s2, 1
  mret
fail:
  li a0, 1
  ebreak

.section .data
.balign 8
word_a:
  .dword 0
  .dword 0
