#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out=$(mktemp -d /tmp/m1p8-nodevice.XXXXXX)
trap 'rm -rf "$out"' EXIT
mkdir "$out/generated"
# Do not change the active generated configuration or start a REF build.
sed '/^#define CONFIG_DEVICE /d' "$root/nemu/include/generated/autoconf.h" > "$out/generated/autoconf.h"
cat > "$out/probe.c" <<'SRC'
#include <isa.h>
#include "local-include/reg.h"
CPU_state cpu;
FILE *log_fp;
bool log_enable(void) { return false; }
void assert_fail_msg(void) { abort(); }
int main(void) {
  cpu.priv = 3; cpu.INTR = true; csr(MIE) = 128; csr(MSTATUS) = MSTATUS_MIE;
  assert(isa_query_intr() == ((1ull << 63) | 7));
  word_t time; assert(riscv_csr_read(TIME, &time) && time == 0);
  assert(!cpu.INTR); return 0;
}
SRC
flags=(-O2 -Werror=implicit-function-declaration -D__GUEST_ISA__=riscv64 -I"$out" -I"$root/nemu/include" -I"$root/nemu/src/isa/riscv64/include" -I"$root/nemu/src/isa/riscv64")
gcc "${flags[@]}" "$out/probe.c" "$root/nemu/src/isa/riscv64/"{reg.c,system/intr.c} -o "$out/probe"
"$out/probe"
gcc "${flags[@]}" -fsyntax-only "$root/nemu/src/isa/riscv64/inst.c" "$root/nemu/src/monitor/monitor.c"
echo 'No-DEVICE RV64 CSR/interrupt link/run + inst/monitor syntax PASS (not full REF validation)'
