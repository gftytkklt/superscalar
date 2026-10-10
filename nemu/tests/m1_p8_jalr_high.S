.option norvc
.section .text
.globl _start
_start:
  la t0, root
  li t1, 0x200000cf // 1GiB executable mapping, physical 0x80000000
  sd t1, 16(t0)
  li t2, 4080
  add t2, t2, t0
  sd t1, 0(t2) // VPN2=510, VA ffffffff80000000
  srli t0, t0, 12
  li t1, 0x8000000000000000
  or t0, t0, t1
  csrw satp, t0
  la t0, high
  li t1, 0xffffffff00000000
  or t0, t0, t1
  csrw mepc, t0
  li t0, 0x800
  csrw mstatus, t0
  mret
high:
  jal ra, function
  auipc t0, 0
  bgez t0, fail
  la t0, target
  jalr t0, 0(t0) // rd=rs1 must still use the pre-write source
  j fail
target:
  bgez t0, fail
  li a0, 0
  ebreak
function:
  ret
fail:
  li a0, 1
  ebreak
.balign 4096
root:
  .zero 4096
