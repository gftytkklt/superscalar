#!/usr/bin/env bash
set -euo pipefail
nemu_dir=$(cd "$(dirname "$0")/.." && pwd)
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT
for test_name in m1_p5_priv m1_p5_tvm_tsr; do
  riscv64-linux-gnu-gcc -nostdlib -nostartfiles -static -fno-pic -mno-relax \
    -march=rv64im_zicsr_zifencei -mabi=lp64 \
    -Wl,-Ttext=0x80000000 -Wl,--no-relax -Wl,--build-id=none \
    -o "$work_dir/$test_name.elf" "$nemu_dir/tests/$test_name.S"
  riscv64-linux-gnu-objcopy -O binary "$work_dir/$test_name.elf" "$work_dir/$test_name.bin"
  timeout 15s "$nemu_dir/build/riscv64-nemu-interpreter" -b "$work_dir/$test_name.bin" \
    > "$work_dir/$test_name.log" 2>&1 || { cat "$work_dir/$test_name.log"; exit 1; }
  if ! grep -q 'HIT GOOD TRAP' "$work_dir/$test_name.log"; then
    cat "$work_dir/$test_name.log"
    exit 1
  fi
  printf '%s: PASS\n' "$test_name"
done

# INV is a host-side debug stop: an unmatched opcode must print and abort.
test_name=m1_p5_inv
riscv64-linux-gnu-gcc -nostdlib -nostartfiles -static -fno-pic -mno-relax \
  -march=rv64im_zicsr_zifencei -mabi=lp64 \
  -Wl,-Ttext=0x80000000 -Wl,--no-relax -Wl,--build-id=none \
  -o "$work_dir/$test_name.elf" "$nemu_dir/tests/$test_name.S"
riscv64-linux-gnu-objcopy -O binary "$work_dir/$test_name.elf" "$work_dir/$test_name.bin"
status=0
timeout 15s "$nemu_dir/build/riscv64-nemu-interpreter" -b "$work_dir/$test_name.bin" \
  > "$work_dir/$test_name.log" 2>&1 || status=$?
if [[ $status -ne 1 ]] || ! grep -q 'invalid opcode' "$work_dir/$test_name.log" \
    || ! grep -q 'ABORT' "$work_dir/$test_name.log"; then
  cat "$work_dir/$test_name.log"
  printf 'm1_p5_inv: expected INV abort, exit status %d\n' "$status" >&2
  exit 1
fi
printf '%s: PASS (expected INV abort)\n' "$test_name"
