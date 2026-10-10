// Link actual RV64 CSR/trap/arbiter code; only the device inputs are controlled.
#include <isa.h>
#include "../src/isa/riscv32/local-include/reg.h"
CPU_state cpu;
FILE *log_fp;
static bool legacy = true, level;
bool log_enable(void) { return false; }
void assert_fail_msg(void) { abort(); }
bool nemu_timer_legacy(void) { return legacy; }
bool nemu_timer_mtip(void) { return level; }
uint64_t nemu_timer_time(void) { return 123456; }
static void reset(unsigned priv) { memset(&cpu, 0, sizeof(cpu)); cpu.priv = priv; legacy = true; level = false; }
static word_t readcsr(unsigned address) { word_t v; assert(riscv_csr_read(address, &v)); return v; }
int main(void) {
  log_fp = stdout;
  unsigned cases = 0;
  unsigned privileges[] = {0, 1, 3};
  for (unsigned p = 0; p < 3; p++) for (unsigned delegate = 0; delegate < 2; delegate++)
  for (unsigned global = 0; global < 2; global++) for (unsigned source = 0; source < 2; source++) {
    reset(privileges[p]);
    csr(MIP) = 1ull << 5;
    csr(MIDELEG) = delegate ? 1ull << 5 : 0;
    csr(MIE) = source ? 1ull << 5 : 0;
    csr(MSTATUS) = global ? MSTATUS_MIE | MSTATUS_SIE : 0;
    bool expected = source && (delegate ? (cpu.priv == 0 || (cpu.priv == 1 && global)) : (cpu.priv < 3 || global));
    assert((isa_query_intr() != INTR_EMPTY) == expected);
    assert(csr(MIP) == (1ull << 5)); // software pending is never consumed by trap
    cases++;
  }
  reset(3); cpu.INTR = true;
  assert(readcsr(MIP) == 128 && isa_query_intr() == INTR_EMPTY && cpu.INTR);
  csr(MIE) = 128; csr(MSTATUS) = MSTATUS_MIE;
  assert(isa_query_intr() == ((1ull << 63) | 7));
  assert(!cpu.INTR && readcsr(MIP) == 0);
  reset(3); legacy = false; level = true; cpu.INTR = true;
  csr(MIE) = 128; csr(MSTATUS) = MSTATUS_MIE;
  assert(isa_query_intr() == ((1ull << 63) | 7));
  assert(readcsr(MIP) == 128 && cpu.INTR);
  level = false; assert(readcsr(MIP) == 0 && isa_query_intr() == INTR_EMPTY);
  reset(3); assert(riscv_csr_write(MIP, ~0ull)); assert(readcsr(MIP) == 0x22);
  assert(riscv_csr_write(MIDELEG, 0x22)); cpu.priv = 1;
  assert(readcsr(SIP) == 0x22); assert(riscv_csr_write(SIP, 0));
  assert(readcsr(SIP) == 0x20); // S cannot clear STIP
  assert(riscv_csr_write(SIE, 0x22)); assert(readcsr(SIE) == 0x22);
  cpu.priv = 3; assert(riscv_csr_write(MIP, 0));
  reset(3); csr(MIP) = (1ull << 11) | (1ull << 5); csr(MIE) = csr(MIP); csr(MSTATUS) = MSTATUS_MIE;
  assert(isa_query_intr() == ((1ull << 63) | 11));
  csr(MIE) &= ~(1ull << 11); assert(isa_query_intr() == ((1ull << 63) | 5));
  const unsigned order[] = {11, 3, 7, 9, 1, 5};
  reset(3); legacy = false; level = true;
  csr(MSTATUS) = MSTATUS_MIE;
  for (unsigned i = 0; i < 6; i++) csr(MIP) |= 1ull << order[i];
  csr(MIE) = csr(MIP);
  for (unsigned i = 0; i < 6; i++) {
    assert(isa_query_intr() == ((1ull << 63) | order[i]));
    csr(MIE) &= ~(1ull << order[i]);
  }
  // An undeliverable delegated high-priority input must not block an M input.
  reset(3); csr(MSTATUS) = MSTATUS_MIE;
  csr(MIP) = csr(MIE) = (1ull << 11) | (1ull << 5);
  csr(MIDELEG) = 1ull << 11;
  assert(isa_query_intr() == ((1ull << 63) | 5));
  // Nor may a globally masked S input hide a nondelegated M input in S mode.
  reset(1); csr(MIP) = csr(MIE) = (1ull << 11) | (1ull << 5);
  csr(MIDELEG) = 1ull << 11;
  assert(isa_query_intr() == ((1ull << 63) | 5));
  reset(0); csr(MIDELEG) = 1ull << 5; csr(MIP) = csr(MIE) = 1ull << 5; csr(STVEC) = 0x1001;
  assert(isa_query_intr() == ((1ull << 63) | 5));
  assert(isa_raise_intr((1ull << 63) | 5, 0x80000100) == 0x1014);
  assert(cpu.priv == 1 && csr(SEPC) == 0x80000100 && csr(SCAUSE) == ((1ull << 63) | 5));
  assert(!(csr(MSTATUS) & MSTATUS_SPP));
  reset(1); csr(MTVEC) = 0x2001; csr(MSTATUS) = MSTATUS_MIE;
  assert(isa_raise_intr((1ull << 63) | 7, 0x80000200) == 0x201c);
  assert(cpu.priv == 3 && csr(MEPC) == 0x80000200 && (csr(MSTATUS) & MSTATUS_MPIE));
  assert(!(csr(MSTATUS) & MSTATUS_MIE) && ((csr(MSTATUS) & MSTATUS_MPP) >> 11) == 1);
  reset(0); assert(!riscv_csr_access(TIME, false));
  csr(MCOUNTEREN) = 2; assert(!riscv_csr_access(TIME, false));
  csr(SCOUNTEREN) = 2; assert(readcsr(TIME) == 123456 && !riscv_csr_access(TIME, true));
  printf("CPU interrupt matrix: %u cases + pending/CSR/trap/time checks PASS\n", cases);
}
