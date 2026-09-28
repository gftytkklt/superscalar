/* M1-P5 RV64 privilege/CSR directed test. Exit through NEMU's ebreak host hook. */
.option norvc
.option norelax
.section .text
.globl _start
_start:
  la t0, m_trap
  csrw mtvec, t0
  la t0, s_trap
  csrw stvec, t0

  /* Fixed ISA identifies M/S/U and omits A until P6. */
  csrr t0, misa
  li t1, 0x141100  /* I|M|S|U */
  and t0, t0, t1
  bne t0, t1, fail
  csrr t0, mhartid
  bnez t0, fail

  /* Exercise register/immediate CSR forms and zero-source write suppression. */
  csrw mscratch, zero
  csrrsi t0, mscratch, 1
  bnez t0, fail
  csrr t0, mscratch
  li t1, 1
  bne t0, t1, fail
  csrrci t0, mscratch, 1
  bne t0, t1, fail
  csrrwi t0, mscratch, 3
  bnez t0, fail
  csrrs t0, mscratch, zero
  li t1, 3
  bne t0, t1, fail
  csrrsi t0, mhartid, 0 /* read-only CSR read, no write */
  bnez t0, fail
  csrw misa, zero    /* WARL: fixed ISA bits remain set */
  csrr t0, misa
  li t1, 0x141100
  and t0, t0, t1
  bne t0, t1, fail

  /* sstatus UXL is read-only even when writing through the alias. */
  csrr t0, sstatus
  li t1, 0x300000000
  and t0, t0, t1
  li t1, 0x200000000
  bne t0, t1, fail
  csrw sstatus, zero
  csrr t0, sstatus
  li t1, 0x300000000
  and t0, t0, t1
  li t1, 0x200000000
  bne t0, t1, fail

  /* sstatus aliases only supervisor-visible mstatus fields. */
  li t0, 2
  csrs mstatus, t0
  csrr t1, sstatus
  and t1, t1, t0
  bne t1, t0, fail
  csrc sstatus, t0
  csrr t1, mstatus
  and t1, t1, t0
  bnez t1, fail

  /* sie/sip reflect only the delegated interrupt bits. */
  csrw mideleg, t0
  csrs mie, t0
  csrr t1, sie
  bne t1, t0, fail
  csrs sip, t0
  csrr t1, mip
  and t1, t1, t0
  bne t1, t0, fail
  csrc sip, t0
  csrr t1, sip
  bnez t1, fail

  li t0, ((1 << 2) | (1 << 8))
  csrw medeleg, t0
  /* M-mode traps must not be delegated. */
  li s3, 1
  ecall
  csrr t0, mstatus
  li t1, 0x1888 /* MPP=U, MPIE=1, MIE=0 after MRET */
  and t0, t0, t1
  li t1, 0x80
  bne t0, t1, fail
  li s3, 9
  li t0, 1
  csrrw zero, mhartid, t0 /* read-only write -> M illegal instruction */
  li s3, 10
  csrr t0, 0x7ff /* unimplemented M CSR -> M illegal instruction */

  /* MRET to S. SPIE is set to establish a clean S interrupt stack. */
  la t0, s_entry
  csrw mepc, t0
  li t0, 0x1800
  csrc mstatus, t0
  li t0, 0x800
  csrs mstatus, t0
  mret

s_entry:
  li t0, 2
  csrs sstatus, t0 /* SIE=1, copied to SPIE on delegated trap */
  /* Illegal M CSR read and MRET in S must delegate to S. */
  li s3, 2
  csrr t0, mstatus
  csrr t0, sstatus
  andi t0, t0, 0x22
  li t1, 0x22 /* SIE=1, SPIE=1 after SRET */
  bne t0, t1, fail
  li s3, 7
  mret
  /* S ecall goes to M because medeleg[9] is clear. */
  li s3, 3
  ecall
  /* SRET to U. */
  la t0, u_entry
  csrw sepc, t0
  li t0, 0x100
  csrc sstatus, t0
  sret

u_entry:
  li s3, 4
  csrr t0, stvec /* U cannot read an S CSR */
  li s3, 8
  sret           /* U cannot execute SRET */
  li s3, 5
  ecall          /* U ecall delegates to S */
  li a0, 0
  ebreak

m_trap:
  csrr t0, mcause
  li t1, 1
  beq s3, t1, m_ecall
  li t1, 3
  beq s3, t1, m_s_ecall
  li t1, 9
  beq s3, t1, m_illegal
  li t1, 10
  beq s3, t1, m_illegal
  j fail
m_ecall:
  li t1, 11
  bne t0, t1, fail
  csrr t0, mstatus
  li t2, 0x1800
  and t0, t0, t2
  li t1, 0x1800
  bne t0, t1, fail
  j m_resume
m_s_ecall:
  li t1, 9
  bne t0, t1, fail
  csrr t0, mstatus
  li t2, 0x1800
  and t0, t0, t2
  li t1, 0x800
  bne t0, t1, fail
  j m_resume
m_illegal:
  li t1, 2
  bne t0, t1, fail
  csrr t0, mtval
  beqz t0, fail
m_resume:
  csrr t0, mepc
  addi t0, t0, 4
  csrw mepc, t0
  mret

s_trap:
  csrr t0, scause
  li t1, 2
  beq s3, t1, s_illegal_s
  li t1, 7
  beq s3, t1, s_illegal_s
  li t1, 4
  beq s3, t1, s_illegal_u
  li t1, 8
  beq s3, t1, s_illegal_u
  li t1, 5
  beq s3, t1, s_u_ecall
  j fail
s_illegal_s:
  li t1, 2
  bne t0, t1, fail
  csrr t0, sstatus
  andi t1, t0, 0x100
  beqz t1, fail
  andi t0, t0, 0x22
  li t1, 0x20 /* SIE=0, SPIE=1 during trap */
  bne t0, t1, fail
  j s_check_tval
s_illegal_u:
  li t1, 2
  bne t0, t1, fail
  csrr t0, sstatus
  andi t0, t0, 0x100
  bnez t0, fail
s_check_tval:
  csrr t0, stval
  beqz t0, fail
  j s_resume
s_u_ecall:
  li t1, 8
  bne t0, t1, fail
  csrr t0, stval
  bnez t0, fail
  csrr t0, sstatus
  andi t0, t0, 0x100
  bnez t0, fail
s_resume:
  csrr t0, sepc
  addi t0, t0, 4
  csrw sepc, t0
  sret

fail:
  li a0, 1
  ebreak
