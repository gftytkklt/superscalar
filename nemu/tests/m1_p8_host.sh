#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
out="$root/npc/verif/build/m1p8-tests"
mkdir -p "$out"
cd "$root/nemu"
flags=(-std=gnu11 -O2 -Wall -Wextra -Wno-unused-parameter -D__GUEST_ISA__=riscv64 -Iinclude -Isrc/isa/riscv64/include)
gcc "${flags[@]}" tests/m1_p8_intr.c src/isa/riscv64/reg.c src/isa/riscv64/system/intr.c -o "$out/intr"
"$out/intr"
gcc "${flags[@]}" tests/m1_p8_devices.c src/device/mtimer.c src/device/serial.c src/device/io/map.c src/device/io/mmio.c -o "$out/devices"
printf abc > "$out/input"
"$out/devices" "$out/input"
fifo_dir=$(mktemp -d "$out/fifo.XXXXXX")
trap 'rm -rf "$fifo_dir"' EXIT
mkfifo "$fifo_dir/input"
"$out/devices" "$fifo_dir/input" fifo
amflags=(-O2 -ffunction-sections -fdata-sections -Wno-unused-parameter '-DARCH_H="arch/riscv.h"' -I"$root/abstract-machine/am/include" -I"$root/abstract-machine/klib/include" -I"$root/nanos-lite/include" -Wl,--gc-sections)
gcc "${amflags[@]}" tests/m1_p8_fg.c "$root/nanos-lite/src/"{proc,device,irq}.c -o "$out/fg"
"$out/fg"
gcc "${amflags[@]}" tests/m1_p8_ticks.c "$root/nanos-lite/src/syscall.c" "$root/navy-apps/libs/libndl/NDL.c" -o "$out/ticks"
"$out/ticks"
