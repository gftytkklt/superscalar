/* CCR-F0015: exercise production comparison and difftest_step, not a model of them.
 * Only REF transport, memory transport and diagnostic-display dependencies are stubs.
 * Each case runs in a fresh process, so production skip/detach statics start clean.
 */
#include <isa.h>
#include <cpu/difftest.h>
#include <memory/paddr.h>
#include <stddef.h>

_Static_assert(sizeof(word_t) == 8 && sizeof(vaddr_t) == 8, "RV64 required");
_Static_assert(sizeof(((CPU_state *)0)->gpr) == 32 * 8, "32 GPRs required");
_Static_assert(offsetof(CPU_state, pc) == 32 * 8, "PC packet offset");
_Static_assert(DIFFTEST_REG_SIZE == 33 * 8, "public packet stays 33 words");
_Static_assert(offsetof(CPU_state, csr) == DIFFTEST_REG_SIZE, "CSR outside packet");

CPU_state cpu;
NEMUState nemu_state;
FILE *log_fp;
/* Dependency names match reg.c; the register comparison helper is the real header. */
const char *regs[] = {
  "$0", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
  "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
  "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
  "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"
};
static CPU_state ref_state;
static unsigned exec_calls, to_ref, to_dut, displays, memory_calls;
static uint64_t memory_bytes;
static uint8_t page[4096];

bool log_enable(void) { return false; }
void assert_fail_msg(void) { fprintf(stderr, "FIXTURE_OR_PRODUCTION_ASSERT\n"); }
void isa_reg_display(void) { displays++; }

uint8_t *guest_to_host(paddr_t addr) {
  assert((uint64_t)addr >= CONFIG_MBASE);
  assert((uint64_t)addr < (uint64_t)CONFIG_MBASE + CONFIG_MSIZE);
  return page; /* No guest RAM contents are simulated or claimed tested. */
}
static void mock_memcpy(paddr_t addr, void *buf, size_t n, bool direction) {
  assert(direction == DIFFTEST_TO_REF && buf == page);
  assert((uint64_t)addr == CONFIG_MBASE + memory_bytes);
  assert(n > 0 && n <= sizeof(page));
  assert(memory_bytes + n <= CONFIG_MSIZE);
  memory_calls++;
  memory_bytes += n;
}
static void mock_regcpy(void *state, bool direction) {
  /* Match the adapter: only the public prefix is transferred. */
  if (direction == DIFFTEST_TO_REF) {
    memcpy(&ref_state, state, DIFFTEST_REG_SIZE);
    to_ref++;
  } else {
    assert(direction == DIFFTEST_TO_DUT);
    memcpy(state, &ref_state, DIFFTEST_REG_SIZE);
    to_dut++;
  }
}
static void mock_exec(uint64_t n) {
  assert(n == 1);
  exec_calls++; /* REF result is supplied by the case, not computed from DUT. */
}

#define CHECK(c) do { if (!(c)) { \
  fprintf(stderr, "CASE_FAIL %s:%d: %s\n", __func__, __LINE__, #c); \
  return 1; \
} } while (0)

static void setup(void) {
  memset(&cpu, 0, sizeof(cpu));
  memset(&ref_state, 0xa5, sizeof(ref_state));
  for (unsigned i = 1; i < 32; i++)
    cpu.gpr[i] = UINT64_C(0x8000000000000000) + i;
  cpu.pc = UINT64_C(0x0000000180000104);
  memcpy(&ref_state, &cpu, DIFFTEST_REG_SIZE);
  nemu_state.state = NEMU_RUNNING;
  nemu_state.halt_pc = UINT64_C(0xdeadbeef);
  ref_difftest_memcpy = mock_memcpy;
  ref_difftest_regcpy = mock_regcpy;
  ref_difftest_exec = mock_exec;
  log_fp = stderr;
}

static int run_case(const char *name) {
  const vaddr_t instruction_pc = cpu.pc - 4;
  if (!strcmp(name, "abi")) {
    unsigned char packet[DIFFTEST_REG_SIZE];
    memset(packet, 0x5a, sizeof(packet));
    mock_regcpy(packet, DIFFTEST_TO_DUT);
    CHECK(memcmp(packet, &cpu, sizeof(packet)) == 0);
    CHECK(ref_state.csr[0] == UINT64_C(0xa5a5a5a5a5a5a5a5));
    printf("ABI word=8 gpr=32 pc_offset=256 packet=264\n");
  } else if (!strcmp(name, "equal")) {
    CHECK(instruction_pc != cpu.pc);
    CHECK(isa_difftest_checkregs(&ref_state, instruction_pc));
  } else if (!strcmp(name, "pc-low") || !strcmp(name, "pc-high")) {
    ref_state.pc ^= !strcmp(name, "pc-low") ? 4 : UINT64_C(0x100000000);
    printf("INPUT ref_pc=" FMT_WORD " dut_pc=" FMT_WORD "\n", ref_state.pc, cpu.pc);
    bool same = isa_difftest_checkregs(&ref_state, instruction_pc);
    printf("OBSERVED compare=%s\n", same ? "true" : "false");
    CHECK(!same);
  } else if (!strcmp(name, "pc-gpr")) {
    ref_state.pc ^= 4;
    ref_state.gpr[7] ^= UINT64_C(0x100000000);
    CHECK(!isa_difftest_checkregs(&ref_state, instruction_pc));
  } else if (!strncmp(name, "gpr-", 4)) {
    char *end;
    long index = strtol(name + 4, &end, 10);
    CHECK(*end == '\0' && index >= 0 && index < 32);
    ref_state.gpr[index] ^= UINT64_C(0x100000001);
    CHECK(!isa_difftest_checkregs(&ref_state, instruction_pc));
  } else if (!strcmp(name, "step-equal")) {
    difftest_step(instruction_pc, cpu.pc);
    CHECK(nemu_state.state == NEMU_RUNNING && displays == 0);
    CHECK(nemu_state.halt_pc == UINT64_C(0xdeadbeef));
    CHECK(exec_calls == 1 && to_dut == 1 && to_ref == 0);
  } else if (!strcmp(name, "step-pc-low") || !strcmp(name, "step-pc-high")) {
    ref_state.pc ^= !strcmp(name, "step-pc-low") ? 4 : UINT64_C(0x100000000);
    difftest_step(instruction_pc, cpu.pc);
    printf("OBSERVED state=%d halt_pc=" FMT_WORD " displays=%u\n",
           nemu_state.state, nemu_state.halt_pc, displays);
    CHECK(nemu_state.state == NEMU_ABORT && displays == 1);
    CHECK(nemu_state.halt_pc == instruction_pc);
    CHECK(exec_calls == 1 && to_dut == 1);
  } else if (!strcmp(name, "skip-ref")) {
    ref_state.pc ^= 4;
    ref_state.gpr[4] ^= 1;
    difftest_skip_ref();
    difftest_step(instruction_pc, cpu.pc);
    CHECK(nemu_state.state == NEMU_RUNNING && displays == 0);
    CHECK(exec_calls == 0 && to_dut == 0 && to_ref == 1);
    CHECK(memcmp(&ref_state, &cpu, DIFFTEST_REG_SIZE) == 0);
    difftest_step(instruction_pc, cpu.pc);
    CHECK(nemu_state.state == NEMU_RUNNING && exec_calls == 1 && to_dut == 1);
    ref_state.pc ^= 4;
    difftest_step(instruction_pc, cpu.pc);
    CHECK(nemu_state.state == NEMU_ABORT && displays == 1);
    CHECK(exec_calls == 2 && to_dut == 2 && to_ref == 1);
    CHECK(nemu_state.halt_pc == instruction_pc);
  } else if (!strcmp(name, "skip-dut")) {
    ref_state.pc = cpu.pc + 8;
    ref_state.gpr[3] ^= 1;
    difftest_skip_dut(1, 3);
    difftest_step(instruction_pc, cpu.pc);
    CHECK(nemu_state.state == NEMU_RUNNING && displays == 0);
    CHECK(exec_calls == 1 && to_dut == 1);
    cpu.pc = ref_state.pc;
    difftest_step(cpu.pc - 4, cpu.pc);
    /* A GPR mismatch proves catch-up re-enters the real comparison. */
    CHECK(nemu_state.state == NEMU_ABORT && displays == 1);
    CHECK(nemu_state.halt_pc == cpu.pc); /* Existing skip-dut label convention. */
    nemu_state.state = NEMU_RUNNING;
    displays = 0;
    ref_state.gpr[3] = cpu.gpr[3];
    difftest_step(cpu.pc - 4, cpu.pc);
    CHECK(nemu_state.state == NEMU_RUNNING && displays == 0 && exec_calls == 2);
    ref_state.pc ^= 4;
    difftest_step(cpu.pc - 4, cpu.pc);
    CHECK(nemu_state.state == NEMU_ABORT && displays == 1 && exec_calls == 3);
    CHECK(nemu_state.halt_pc == cpu.pc - 4 && to_dut == 4);
  } else if (!strcmp(name, "detach-attach")) {
    difftest_detach();
    ref_state.pc ^= 4;
    ref_state.gpr[8] ^= 1;
    difftest_skip_ref(); /* Detach must also disable skip requests. */
    difftest_skip_dut(2, 4);
    difftest_step(instruction_pc, cpu.pc);
    CHECK(exec_calls == 0 && to_dut == 0 && to_ref == 0 && displays == 0);
    CHECK(nemu_state.state == NEMU_RUNNING);
    difftest_attach();
    CHECK(memory_bytes == CONFIG_MSIZE && memory_calls == CONFIG_MSIZE / 4096);
    CHECK(to_ref == 1 && memcmp(&ref_state, &cpu, DIFFTEST_REG_SIZE) == 0);
    CHECK(ref_state.csr[0] == UINT64_C(0xa5a5a5a5a5a5a5a5));
    difftest_attach(); /* Already attached: no extra transfer. */
    CHECK(to_ref == 1 && memory_bytes == CONFIG_MSIZE);
    difftest_step(instruction_pc, cpu.pc);
    CHECK(exec_calls == 1 && to_dut == 1 && nemu_state.state == NEMU_RUNNING);
    ref_state.pc ^= UINT64_C(0x100000000);
    difftest_step(instruction_pc, cpu.pc);
    CHECK(nemu_state.state == NEMU_ABORT && displays == 1);
    CHECK(nemu_state.halt_pc == instruction_pc && exec_calls == 2 && to_dut == 2);
  } else {
    fprintf(stderr, "UNKNOWN_CASE %s\n", name);
    return 2;
  }
  printf("CASE_PASS %s\n", name);
  return 0;
}

int main(int argc, char **argv) {
  if (argc != 2) return 2;
  setup();
  return run_case(argv[1]);
}
