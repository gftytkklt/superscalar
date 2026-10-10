#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out="$root/npc/verif/build/m1p8-tests"
mkdir -p "$out"
for name in m1_p8_timer m1_p8_time_wfi m1_p8_jalr_high; do
  riscv64-linux-gnu-gcc -nostdlib -nostartfiles -static -fno-pic -mno-relax \
    -march=rv64ima_zicsr_zifencei -mabi=lp64 -Wl,-Ttext=0x80000000 -Wl,--no-relax \
    -Wl,--build-id=none "$root/nemu/tests/$name.S" -o "$out/$name.elf"
  riscv64-linux-gnu-objcopy -O binary "$out/$name.elf" "$out/$name.bin"
  SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy timeout 15s \
    "$root/nemu/build/riscv64-nemu-interpreter" -b --timer-source=mtimer "$out/$name.bin" > "$out/$name.log" 2>&1
  grep -q 'HIT GOOD TRAP' "$out/$name.log"
  echo "$name PASS"
done
