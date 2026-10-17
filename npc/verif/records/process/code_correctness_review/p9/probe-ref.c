#include <isa.h>
#include "nemu/src/isa/riscv32/local-include/reg.h"
#include <stdio.h>
CPU_state cpu;
FILE *log_fp;
void assert_fail_msg(void){abort();}
extern void difftest_raise_intr(word_t);
int main(void) {
  cpu.pc=0x80000080;cpu.priv=3;csr(MTVEC)=0x80000100;csr(MSTATUS)=8;
  difftest_raise_intr((1ull<<63)|7);
  printf("pc=%lx expected=%lx mepc=%lx mcause=%lx priv=%lu\n",cpu.pc,csr(MTVEC),csr(MEPC),csr(MCAUSE),cpu.priv);
  return !(cpu.pc==0x80000080 && csr(MEPC)==0x80000080 && csr(MCAUSE)==((1ull<<63)|7));
}
