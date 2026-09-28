#!/usr/bin/env bash
set -euo pipefail

nemu_dir=$(cd "$(dirname "$0")/.." && pwd)
root=$(cd "$nemu_dir/.." && pwd)
rt="$root/am-kernels/tests/riscv-tests"
out_dir="${OUT_DIR:-$root/npc/verif/build/m1p6-atomic}"
cc="${CC:-riscv64-unknown-elf-gcc}"
objcopy="${OBJCOPY:-riscv64-unknown-elf-objcopy}"
nemu_bin="${NEMU_BIN:-$nemu_dir/build/riscv64-nemu-interpreter}"
mkdir -p "$out_dir"

if ! grep -q RVTEST_ADAPTED "$rt/env/p/riscv_test.h"; then
  echo "riscv-tests env/p requires the existing riscv_tests_patch_env.py adaptation" >&2
  exit 1
fi

run_one() {
  local name="$1" source="$2"
  local log="$out_dir/$name.log" elf="$out_dir/$name.elf" bin="$out_dir/$name.bin"
  "$cc" -march=rv64ima_zicsr_zifencei -mabi=lp64 -static -mcmodel=medany \
    -fvisibility=hidden -nostdlib -nostartfiles -mno-relax -DRVTEST_ADAPTED \
    -I"$rt/env/p" -I"$rt/isa/macros/scalar" -T"$rt/env/p/link.ld" \
    "$source" -o "$elf"
  "$objcopy" -O binary "$elf" "$bin"
  if ! timeout 15s "$nemu_bin" -b "$bin" >"$log" 2>&1 ||
     ! grep -q 'HIT GOOD TRAP' "$log"; then
    tail -n 35 "$log" >&2
    echo "FAIL $name" >&2
    return 1
  fi
  echo "PASS $name"
}

run_one m1_p6_atomic "$nemu_dir/tests/m1_p6_atomic.S"
count=0
for source in "$rt/isa/rv64ua/"*.S; do
  name=$(basename "$source" .S)
  case "$name" in
    amocas_*) continue ;; # Zacas is outside the standard A extension.
  esac
  run_one "rv64ua-$name" "$source"
  count=$((count + 1))
done
echo "rv64ua standard A: $count PASS"
