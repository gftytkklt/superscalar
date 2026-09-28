#!/usr/bin/env bash
set -euo pipefail
nemu_dir=$(cd "$(dirname "$0")/.." && pwd)
root=$(cd "$nemu_dir/.." && pwd)
out_dir="$root/npc/verif/build/m1p7-sv39"
mkdir -p "$out_dir"
for name in m1_p7_sv39 m1_p7_sfence_priv; do
  riscv64-linux-gnu-gcc -nostdlib -nostartfiles -static -fno-pic -mno-relax \
    -march=rv64ima_zicsr_zifencei -mabi=lp64 \
    -Wl,-Ttext=0x80000000 -Wl,--no-relax -Wl,--build-id=none \
    -o "$out_dir/$name.elf" "$nemu_dir/tests/$name.S"
  riscv64-linux-gnu-objcopy -O binary "$out_dir/$name.elf" "$out_dir/$name.bin"
  if ! timeout 15s "$nemu_dir/build/riscv64-nemu-interpreter" -b \
      "$out_dir/$name.bin" >"$out_dir/$name.log" 2>&1 ||
     ! grep -q 'HIT GOOD TRAP' "$out_dir/$name.log"; then
    tail -n 50 "$out_dir/$name.log" >&2
    exit 1
  fi
  echo "$name: PASS"
done
