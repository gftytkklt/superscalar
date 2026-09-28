/* M1-P7: RV64 Sv39 leaf sizes, A/D, faults, cross-page and sfence. */
.option norvc
.option norelax
.section .text
.globl _start
_start:
  la t0, m_fail
  csrw mtvec, t0
  la t0, s_trap
  csrw stvec, t0

  /* root[2]: identity 1 GiB map for text, tables and physical test data. */
  la t0, root
  li t1, 0x80000000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0xcf
  sd t1, 16(t0)

  /* root[1] -> level 1 table. */
  la t1, level1
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 1
  sd t1, 8(t0)

  /* level1[0]: 2 MiB map; level1[1] -> level 0 table. */
  la t0, level1
  li t1, 0x80200000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0xc7
  sd t1, 0(t0)
  la t1, level0
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 1
  sd t1, 8(t0)

  /* level0[0,1] map nonadjacent physical pages; A/D start clear. */
  la t0, level0
  li t1, 0x80010000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 7
  sd t1, 0(t0)
  li t1, 0x80012000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 7
  sd t1, 8(t0)
  /* level0[2]: readable but not executable or writable. */
  li t1, 0x80014000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0x43
  sd t1, 16(t0)
  /* level0[3]: U page; level0[4]: execute-only S page. */
  li t1, 0x80016000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0x1f
  sd t1, 24(t0)
  li t1, 0x80018000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 9
  sd t1, 32(t0)
  /* level0[7]: writable data for LR/SC/AMO under translation. */
  li t1, 0x8001c000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 7
  sd t1, 56(t0)

  li t0, 0x80200000
  li t1, 0x12345678
  sd t1, 0(t0)
  li t0, 0x80010000
  li t1, 0x1122334455667788
  sd t1, 0(t0)
  li t0, 0x80010ffc
  li t1, 0x55667788
  sw t1, 0(t0)
  li t0, 0x80012000
  li t1, 0x11223344
  sw t1, 0(t0)
  li t0, 0x80014000
  li t1, 0x55667788
  sw t1, 0(t0)
  li t0, 0x80016000
  li t1, 0x10203040
  sw t1, 0(t0)
  li t0, 0x80018000
  li t1, 0x50607080
  sw t1, 0(t0)
  li t0, 0x8001c000
  li t1, 5
  sd t1, 0(t0)

  li t0, ((1 << 1) | (1 << 5) | (1 << 7) | (1 << 8) | (1 << 12) | (1 << 13) | (1 << 15))
  csrw medeleg, t0
  la t0, root
  srli t0, t0, 12
  li t1, (8 << 60)
  or t0, t0, t1
  csrw satp, t0
  sfence.vma zero, zero
  /* MPRV translates M-mode data as S while instruction fetch stays direct. */
  li t0, 0x1800
  csrc mstatus, t0
  li t0, ((1 << 17) | (1 << 11))
  csrs mstatus, t0
  li t0, 0x40200000
  ld t1, 0(t0)
  li t2, 0x1122334455667788
  bne t1, t2, fail
  li t0, (1 << 17)
  csrc mstatus, t0
  la t0, s_start
  csrw mepc, t0
  li t0, 0x1800
  csrc mstatus, t0
  li t0, 0x800
  csrs mstatus, t0
  mret

s_start:
  li s3, 0
  li s6, 0
  /* 1 GiB identity leaf. */
  la t0, marker
  ld t1, 0(t0)
  li t2, 0xabcdef1234567890
  bne t1, t2, fail
  /* 2 MiB leaf. */
  li t0, 0x40000000
  ld t1, 0(t0)
  li t2, 0x12345678
  bne t1, t2, fail
  /* 4 KiB leaf, A then D update. */
  li t0, 0x40200000
  ld t1, 0(t0)
  li t2, 0x1122334455667788
  bne t1, t2, fail
  la t3, level0
  ld t4, 0(t3)
  andi t4, t4, 0x40
  beqz t4, fail
  li t1, 0x1234abcd
  sw t1, 0(t0)
  ld t4, 0(t3)
  andi t4, t4, 0x80
  beqz t4, fail

  /* S data access to U page requires SUM; execute-only read requires MXR. */
  li t0, 0x40203000
  li s3, 13
  mv s4, t0
  la s5, sum_fault
sum_fault:
  lw t1, 0(t0)
  li t1, (1 << 18)
  csrs sstatus, t1
  li t0, 0x40203000
  lw t1, 0(t0)
  li t2, 0x10203040
  bne t1, t2, fail
  li t1, (1 << 18)
  csrc sstatus, t1

  li t0, 0x40204000
  li s3, 13
  mv s4, t0
  la s5, mxr_fault
mxr_fault:
  lw t1, 0(t0)
  li t1, (1 << 19)
  csrs sstatus, t1
  li t0, 0x40204000
  lw t1, 0(t0)
  li t2, 0x50607080
  bne t1, t2, fail
  li t1, (1 << 19)
  csrc sstatus, t1

  /* Crossing a 4 KiB boundary uses two unrelated physical pages. */
  li t0, 0x40200000
  li t6, 0xffc
  add t6, t0, t6
  ld t1, 0(t6)
  li t2, 0x1122334455667788
  bne t1, t2, fail
  li t1, 0xaabbccddeeff0011
  sd t1, 0(t6)
  li t3, 0x80010ffc
  lwu t4, 0(t3)
  li t2, 0xeeff0011
  bne t4, t2, fail
  li t3, 0x80012000
  lwu t4, 0(t3)
  li t2, 0xaabbccdd
  bne t4, t2, fail

  /* Second-page fault leaves destination and RAM data unchanged. */
  la t3, level0
  ld t4, 0(t3)
  li t2, -129 /* clear D on first leaf before the failing store */
  and t4, t4, t2
  sd t4, 0(t3)
  ld s7, 8(t3)
  sd zero, 8(t3)
  sfence.vma t0, zero
  li s3, 13
  li s4, 0x40201000
  la s5, cross_fault
  li t5, 0x1234
cross_fault:
  ld t5, 0(t6)
  li t2, 0x1234
  bne t5, t2, fail
  li t3, 0x80010ffc
  lwu t4, 0(t3)
  li t2, 0xeeff0011
  bne t4, t2, fail
  li s3, 15
  li s4, 0x40201000
  la s5, cross_store_fault
  li t1, 0
cross_store_fault:
  sd t1, 0(t6)
  li t3, 0x80010ffc
  lwu t4, 0(t3)
  li t2, 0xeeff0011
  bne t4, t2, fail
  la t3, level0
  ld t4, 0(t3)
  andi t4, t4, 0x80
  bnez t4, fail
  sd s7, 8(t3)
  sfence.vma zero, zero

  /* Invalid leaf: load page fault. */
  li t0, 0x40205000
  li s3, 13
  mv s4, t0
  la s5, invalid_load
invalid_load:
  lw t1, 0(t0)

  /* Read-only leaf: store/AMO page fault and no data write. */
  li t0, 0x40202000
  li s3, 15
  mv s4, t0
  la s5, readonly_store
readonly_store:
  sw t1, 0(t0)
  li t3, 0x80014000
  lw t4, 0(t3)
  li t2, 0x55667788
  bne t4, t2, fail

  /* Non-canonical virtual address. */
  li t0, 0x0000008000000000
  li s3, 13
  mv s4, t0
  la s5, noncanonical
noncanonical:
  lw t1, 0(t0)

  /* Misaligned 2 MiB leaf. */
  la t3, level1
  ld s7, 0(t3)
  li t1, 0x80201000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0xc7
  sd t1, 0(t3)
  li t0, 0x40000000
  li s3, 13
  mv s4, t0
  la s5, misaligned_superpage
misaligned_superpage:
  lw t1, 0(t0)
  sd s7, 0(t3)

  /* PTE physical read failure is a load access fault. */
  ld s7, 8(t3)
  li t1, 0x90000000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 1
  sd t1, 8(t3)
  li t0, 0x40200000
  li s3, 5
  mv s4, t0
  la s5, pte_access_fault
pte_access_fault:
  lw t1, 0(t0)
  sd s7, 8(t3)

  /* Fetch from a non-executable leaf: epc and tval are target VA. */
  li t0, 0x40202000
  li s3, 12
  mv s4, t0
  mv s5, t0
  la s6, after_fetch_fault
  jalr zero, t0, 0
after_fetch_fault:
  li s6, 0
  sfence.vma zero, zero
  li t0, 0x40200000
  sfence.vma t0, zero
  li t1, 1
  sfence.vma zero, t1
  /* A changed PTE is immediately visible in the no-TLB implementation. */
  li t0, 0x80012008
  li t1, 0x5a5a5a5a
  sw t1, 0(t0)
  la t3, level0
  ld s7, 0(t3)
  li t1, 0x80012000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0xc7
  sd t1, 0(t3)
  li t0, 0x40200008
  sfence.vma t0, zero
  lwu t1, 0(t0)
  li t2, 0x5a5a5a5a
  bne t1, t2, fail
  sd s7, 0(t3)
  sfence.vma zero, zero

  /* A extension uses the same checked path under Sv39. */
  li t0, 0x40207000
  lr.d t1, (t0)
  li t2, 5
  bne t1, t2, fail
  li t3, 9
  sc.d t4, t3, (t0)
  bnez t4, fail
  amoadd.d t5, t2, (t0)
  bne t5, t3, fail
  li t3, 14
  ld t4, 0(t0)
  bne t4, t3, fail
  /* AMO and failed SC report store/AMO page fault on read-only leaf. */
  li t0, 0x40202000
  li s3, 15
  mv s4, t0
  la s5, amo_fault
  li t2, 1
amo_fault:
  amoadd.w t1, t2, (t0)
  li s3, 15
  li s4, 0x40202000
  la s5, sc_fault
sc_fault:
  sc.w t1, t2, (t0)
  li t3, 0x80014000
  lw t4, 0(t3)
  li t2, 0x55667788
  bne t4, t2, fail

  /* A valid leaf to absent physical memory is an access fault. */
  la t3, level0
  ld s7, 56(t3)
  li t1, 0x90000000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 0xc7
  sd t1, 56(t3)
  li t0, 0x40207000
  li s3, 5
  mv s4, t0
  la s5, leaf_access_fault
leaf_access_fault:
  lw t1, 0(t0)

  /* Reserved high PTE bit and illegal W-without-R are page faults. */
  li t1, (1 << 63)
  or t1, t1, s7
  sd t1, 56(t3)
  li s3, 13
  li s4, 0x40207000
  la s5, reserved_pte_fault
reserved_pte_fault:
  lw t1, 0(t0)
  li t1, 0x8001c000
  srli t1, t1, 12
  slli t1, t1, 10
  ori t1, t1, 5
  sd t1, 56(t3)
  li s3, 13
  la s5, write_without_read_fault
write_without_read_fault:
  lw t1, 0(t0)
  sd s7, 56(t3)

  /* U executes through an alias of this code page; S-only data must fault. */
  la t3, level0
  la t0, u_code
  srli t1, t0, 12
  slli t1, t1, 10
  ori t1, t1, 0x1b  /* V|R|X|U */
  sd t1, 48(t3)
  sfence.vma zero, zero
  li t1, 0xfff
  and t0, t0, t1
  li t2, 0x40206000
  add t0, t0, t2
  csrw sepc, t0
  li s3, 13
  li s4, 0x80000000
  la s5, u_fault_inst
  and s5, s5, t1
  add s5, s5, t2
  la s10, after_u_mode
  li s9, 1
  li s11, 0
  li t1, (1 << 8)
  csrc sstatus, t1 /* SPP=U */
  sret
after_u_mode:
  li s9, 0
  li a0, 0
  ebreak

s_trap:
  csrr t0, scause
  li t1, 8
  beq t0, t1, u_ecall_return
  bne t0, s3, fail
  csrr t0, stval
  bne t0, s4, fail
  csrr t0, sepc
  bne t0, s5, fail
  beqz s9, 2f
  li s11, 1
2:
  beqz s6, 1f
  csrw sepc, s6
  sret
1:
  addi t0, t0, 4
  csrw sepc, t0
  sret

u_ecall_return:
  li t0, 1
  bne s9, t0, fail
  bne s11, t0, fail
  csrw sepc, s10
  li t0, (1 << 8)
  csrs sstatus, t0 /* return to S */
  sret

u_code:
  li t0, 0x80000000
u_fault_inst:
  lw t1, 0(t0)
  ecall

m_fail:
fail:
  li a0, 1
  ebreak

.section .rodata
.balign 8
marker:
  .dword 0xabcdef1234567890

.section .bss
.balign 4096
root:
  .space 4096
.balign 4096
level1:
  .space 4096
.balign 4096
level0:
  .space 4096
