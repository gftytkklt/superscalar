/* Unmatched opcode must invoke NEMU's INV debug stop, not enter a guest trap. */
.section .text
.globl _start
_start:
  .word 0xffffffff
  ebreak
