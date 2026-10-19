# F0003: IALIGN=32 faults share ECALL entry/return; no link writeback.
.option nopic
.option norvc
.option norelax
.section .text
.globl _start
_start:
  li s0, 0
  li s1, 0
  la t0, handler
  csrw mtvec, t0
  li t0, 0x55
  la s2, bad_jal
  addi s3, s2, 2
  la s4, after_jal
bad_jal:
  .word 0x002002ef             # jal t0,+2
  j fail
after_jal:
  li t3, 0x55
  bne t0, t3, fail
  la s2, bad_jalr
  addi t1, s2, 3
  addi s3, s2, 2
  mv s5, t1
  la s4, after_jalr
bad_jalr:
  .word 0x00030367             # jalr t1,0(t1): preserve rs1/rd on fault
  j fail
after_jalr:
  bne t1, s5, fail
  la s2, bad_branch
  addi s3, s2, 2
  la s4, after_branch
bad_branch:
  .word 0x00000163             # beq zero,zero,+2
  j fail
after_branch:
  li t1, 1
  .word 0x00030163             # beq t1,zero,+2 is not taken

  li t3, 3
  bne s0, t3, fail
  li s1, 11
  li s3, 0                    # ECALL must clear the preceding nonzero mtval
  la s2, ecall_site
  la s4, after_ecall
ecall_site:
  ecall
  j fail
after_ecall:
  li t3, 4
  bne s0, t3, fail
  li t0, 0x0f000000
  li t1, 0x600d000000000001
  sd t1, 8(t0)                # existing bare-core PASS marker
  li a0, 0
  ebreak
handler:
  csrr t3, mcause
  bne t3, s1, fail
  csrr t3, mepc
  bne t3, s2, fail
  csrr t3, mtval
  bne t3, s3, fail
  addi s0, s0, 1
  csrw mepc, s4
  mret
fail:
  li t0, 0x0f000000
  li t1, 0xbad0000000000000
  sd t1, 16(t0)
  li a0, 1
  ebreak
