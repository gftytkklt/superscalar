// CCR-P2 diagnostic harness: links unmodified CPU/ISA/MMU/memory sources.
// Device requests/time are controlled inputs; no device correctness claim.
#include <isa.h>
#include <cpu/cpu.h>
#include <memory/paddr.h>
#include <memory/vaddr.h>
#include "local-include/reg.h"
#include <limits.h>

FILE *log_fp;
bool log_enable(void) { return false; }
uint64_t get_time(void) { static uint64_t t; return ++t; }
void device_update(void) {}
bool nemu_timer_legacy(void) { return true; }
bool nemu_timer_mtip(void) { return false; }
uint64_t nemu_timer_time(void) { return 0; }
bool mmio_range_mapped(paddr_t a, int n) { (void)a; (void)n; return false; }
word_t mmio_read(paddr_t a, int n) { (void)a; (void)n; abort(); }
void mmio_write(paddr_t a, int n, word_t v) { (void)a; (void)n; (void)v; abort(); }

static const vaddr_t pc0 = 0x80000000ull;
static void reset(void) {
  memset(&cpu, 0, sizeof(cpu)); cpu.priv = 3; cpu.pc = pc0;
  cpu.csr[CSR_MSTATUS] = 0xa00000000ull;
  cpu.csr[CSR_MTVEC] = pc0 + 0x100;
  nemu_state.state = NEMU_STOP;
}
static void step(uint32_t inst) {
  paddr_write((paddr_t)cpu.pc, 4, inst); cpu_exec(1);
}
static uint32_t rinst(unsigned f7, unsigned f3, unsigned op) {
  return (f7 << 25) | (7 << 20) | (6 << 15) | (f3 << 12) | (5 << 7) | op;
}
static void show(const char *name) {
  printf("OBS %s pc=%016lx x5=%016lx cause=%lu epc=%016lx tval=%016lx state=%d\n",
    name, cpu.pc, cpu.gpr[5], cpu.csr[CSR_MCAUSE], cpu.csr[CSR_MEPC],
    cpu.csr[CSR_MTVAL], nemu_state.state);
}
int main(int argc, char **argv) {
  assert(argc == 2); log_fp = stdout; setbuf(stdout, NULL); reset();
  const char *name = argv[1];
  printf("ABI word=%zu sword=%zu paddr=%zu int=%zu pointer=%zu\n",
    sizeof(word_t), sizeof(sword_t), sizeof(paddr_t), sizeof(int), sizeof(void *));
  if (!strcmp(name, "addiw")) {
    cpu.gpr[6] = INT32_MAX; step((1 << 20) | (6 << 15) | (5 << 7) | 0x1b);
  } else if (!strcmp(name, "addw")) {
    cpu.gpr[6] = INT32_MAX; cpu.gpr[7] = 1; step(rinst(0, 0, 0x3b));
  } else if (!strcmp(name, "subw")) {
    cpu.gpr[6] = 0x80000000; cpu.gpr[7] = 1; step(rinst(32, 0, 0x3b));
  } else if (!strcmp(name, "mul")) {
    cpu.gpr[6] = INT64_MAX; cpu.gpr[7] = 2; step(rinst(1, 0, 0x33));
  } else if (!strcmp(name, "mulw")) {
    cpu.gpr[6] = INT32_MAX; cpu.gpr[7] = 2; step(rinst(1, 0, 0x3b));
  } else if (!strcmp(name, "sllw")) {
    cpu.gpr[6] = UINT64_MAX; cpu.gpr[7] = 1; step(rinst(0, 1, 0x3b));
  } else if (!strcmp(name, "jal")) {
    cpu.gpr[5] = 0x55; step(0x002002ef); // jal x5,+2
  } else if (!strcmp(name, "jalr")) {
    cpu.gpr[5] = 0x55; cpu.gpr[6] = pc0 + 3;
    step((6 << 15) | (5 << 7) | 0x67);
  } else if (!strcmp(name, "branch")) {
    step(0x00000163); // beq x0,x0,+2
  } else if (!strcmp(name, "high-bare")) {
    paddr_write(0x80002000, 8, 0x1122334455667788ull);
    cpu.gpr[6] = 0x180002000ull;
    step((6 << 15) | (3 << 12) | (5 << 7) | 3);
    VAddrFault f = {0}; bool ok = vaddr_try_write(0x180002000ull, 8, 0xabcdef, &f);
    printf("OBS high-store ok=%d low-memory=%lx cause=%lu\n", ok, paddr_read(0x80002000,8), f.cause);
  } else if (!strcmp(name, "high-pt")) {
    paddr_write(0x80001000, 8, ((0x80002000ull >> 12) << 10) | 1);
    paddr_write(0x80002000, 8, ((0x80003000ull >> 12) << 10) | 1);
    paddr_write(0x80003000, 8, ((0x180004000ull >> 12) << 10) | 0xc7);
    paddr_write(0x80004000, 8, 0x8877665544332211ull);
    cpu.priv = 1; cpu.csr[CSR_SATP] = (8ull << 60) | (0x80001000ull >> 12);
    VAddrFault f = {0}; word_t data = 0;
    bool ok = vaddr_try_read(0, 8, &data, &f);
    printf("OBS high-leaf ok=%d data=%lx cause=%lu\n", ok, data, f.cause);
    cpu.csr[CSR_SATP] = (8ull << 60) | (0x180001000ull >> 12);
    ok = vaddr_try_read(0, 8, &data, &f);
    printf("OBS high-root ok=%d data=%lx cause=%lu\n", ok, data, f.cause);
  } else if (!strcmp(name, "unaligned")) {
    cpu.gpr[6] = 0x80002001;
    step((6 << 15) | (3 << 12) | (5 << 7) | 3);
  } else if (!strcmp(name, "fencei")) {
    step(0x0000108f); // funct3=001, rd=1 reserved and required ignored
  } else if (!strcmp(name, "inv-end")) {
    cpu.pc = CONFIG_MBASE + CONFIG_MSIZE - 4; step(0xffffffff);
  } else { fprintf(stderr, "unknown scenario\n"); return 2; }
  show(name); return 0;
}
