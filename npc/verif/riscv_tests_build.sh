#!/usr/bin/env bash
# ============================================================================
# B4 R-2: riscv-tests 双目标编译（与 cpu-tests 的 ARCH=riscv64-{nemu,npc} 约定对齐）
#   TARGET=nemu : env/p/link.ld（0x80000000 连续加载；NEMU 原生解释器/difftest REF 基址）
#   TARGET=npc  : flash XIP 0x30000000 + SRAM(.data/.bss/stack)，-DRVTEST_NPC
#                （.data 由 env 适配的 RVTEST_NPC_INIT 从 flash 拷到 SRAM）
# 用法：./riscv_tests_build.sh [nemu|npc] [测试名...]
#       默认 npc；不带测试名时编译全部 rv64ui/rv64um 的 -p 变体
# 产物：$RT/isa/<target>/<ext>-p-<name>{,.bin}
# ============================================================================
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
RT=${RT_DIR:-$ROOT/am-kernels/tests/riscv-tests}
TARGET=${1:-npc}
shift || true
CC=${CC:-riscv64-unknown-elf-gcc}
OBJCOPY=${OBJCOPY:-riscv64-unknown-elf-objcopy}
CFLAGS_COMMON="-march=rv64g -mabi=lp64d -static -mcmodel=medany -fvisibility=hidden -nostdlib -nostartfiles -DRVTEST_ADAPTED"

[ -d "$RT/env/p" ] || { echo "[build] 找不到 riscv-tests: $RT（先 clone + submodule update）"; exit 1; }
python3 "$HERE/riscv_tests_patch_env.py" "$RT" >/dev/null

# NPC 链接脚本（对齐 AM linker-soc 布局；本地生成，避免改 env submodule 里的文件）
LD_NPC="$HERE/riscv_tests_link_npc.ld"
case "$TARGET" in
  nemu) LD="$RT/env/p/link.ld"; EXTRA="";;
  npc)
    LD="$LD_NPC"; EXTRA="-DRVTEST_NPC"
    cat > "$LD_NPC" <<'EOF'
OUTPUT_ARCH("riscv")
ENTRY(_start)
MEMORY {
  sram  (rw) : ORIGIN = 0x0f000000, LENGTH = 0x2000
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 0x1000000
}
SECTIONS {
  . = ORIGIN(flash);
  .text : { *(.text.init) *(.text*) } > flash
  .rodata : ALIGN(8) { *(.rodata*) *(.srodata*) } > flash
  .tohost : ALIGN(64) { *(.tohost) } > sram AT> flash
  .data : ALIGN(8) {
    _sdata = .;
    *(.data*) *(.sdata*)
    _edata = .;
  } > sram AT> flash
  .bss (NOLOAD) : {
    _bss_start = ALIGN(8);
    *(.bss*) *(.sbss*) *(.scommon)
    _bss_end = .;
  } > sram
  _sidata = LOADADDR(.data);
  _stack_pointer = ORIGIN(sram) + LENGTH(sram) - 8;
  _end = .;
}
EOF
    ;;
  *) echo "usage: $0 [nemu|npc] [tests...]"; exit 1;;
esac

OUT="$RT/isa/$TARGET"
mkdir -p "$OUT"
list=()
if [ $# -gt 0 ]; then
  for n in "$@"; do
    for d in rv64ui rv64um; do
      [ -f "$RT/isa/$d/$n.S" ] && list+=("$d/$n.S")
    done
  done
else
  for d in rv64ui rv64um; do
    for s in "$RT/isa/$d"/*.S; do list+=("$d/$(basename "$s")"); done
  done
fi
[ ${#list[@]} -gt 0 ] || { echo "[build] 无测试可编"; exit 1; }

for rel in "${list[@]}"; do
  d=$(dirname "$rel"); n=$(basename "$rel" .S)
  out="$OUT/$d-p-$n"
  # shellcheck disable=SC2086
  $CC $CFLAGS_COMMON $EXTRA -I"$RT/env/p" -I"$RT/isa/macros/scalar" -T"$LD" "$RT/isa/$rel" -o "$out"
  $OBJCOPY -O binary "$out" "$out.bin"
done
echo "[build] TARGET=$TARGET 共 ${#list[@]} 个测试 -> $OUT"
