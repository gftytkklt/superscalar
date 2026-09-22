#!/usr/bin/env bash
# ============================================================================
# B4 R-2/R-3: riscv-tests runner（与 cpu-tests 双目标执行模式对齐）
#   TARGET=npc  : NPC SoC `npc/build/ysyxSoCFull <bin>`（flash XIP 0x30000000）
#   TARGET=nemu : NEMU 原生解释器 `nemu/build/riscv64-nemu-interpreter -b <bin>`（0x80000000）
#   结束约定：项目统一 `ebreak` + a0（HIT GOOD/BAD TRAP），与 cpu-tests 相同
#   死锁三层防护：仿真看门狗（NPC SIM_END）/ timeout 墙钟 / 单测失败不中断批量
#   四分类：PASS / FAIL / SKIP(原因) / TIMEOUT(未判定)
# 用法：TARGET=npc ./riscv_tests_run.sh；可选 MAXCYC/WALL/OUT/RT_DIR 环境变量
# ============================================================================
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
RT=${RT_DIR:-$ROOT/am-kernels/tests/riscv-tests}
TARGET=${TARGET:-npc}
ISA_DIR="$RT/isa/$TARGET"
SKIP_FILE=${SKIP_FILE:-$HERE/riscv_tests_skip.txt}
# NPC: flash XIP 校准延迟 ~4.3k 拍/行，单测约 0.2~0.5M 拍 → 默认 1M 拍预算
MAXCYC=${MAXCYC:-1000000}
WALL=${WALL:-120}
# NPC 默认 DIFF=0：riscv-tests 自带 PASS/FAIL 自校验；且本仓 NEMU REF 在
# mulh/mulhsu/mulhu（结果错）、div*/rem*（SIGFPE）上不可靠，DIFF=1 仅作可用子集的交叉验证。
DIFF=${DIFF:-0}
OUT=${OUT:-$HERE/records/process/RISCV_TESTS_RESULT_${TARGET}.md}
LOGDIR=${LOGDIR:-$HERE/build/rvtests_logs/$TARGET}
NEMU_BIN=${NEMU_BIN:-$ROOT/nemu/build/riscv64-nemu-interpreter}
REF_SO=${REF_SO:-$ROOT/nemu/build/riscv64-nemu-interpreter-so}
SOC_BIN=${SOC_BIN:-$ROOT/npc/build/ysyxSoCFull}

mkdir -p "$LOGDIR"
case "$TARGET" in
  npc)
    make -C "$ROOT/npc" DIFF=$DIFF build/ysyxSoCFull >/dev/null || { echo "[runner] SoC 构建失败"; exit 1; }
    if [ "$DIFF" = 1 ] && [ ! -f "$REF_SO" ]; then echo "[runner] 缺 REF: $REF_SO"; exit 1; fi;;
  nemu) [ -x "$NEMU_BIN" ] || { echo "[runner] 缺 NEMU 原生解释器: $NEMU_BIN"; exit 1; };;
  *) echo "TARGET=npc|nemu"; exit 1;;
esac
if [ ! -d "$ISA_DIR" ] || ! ls "$ISA_DIR"/rv64ui-p-* >/dev/null 2>&1; then
  "$HERE/riscv_tests_build.sh" "$TARGET" || { echo "[runner] 构建失败"; exit 1; }
fi

declare -A SKIP
if [ -f "$SKIP_FILE" ]; then
  while read -r t reason; do
    case "$t" in ""|\#*) continue;; esac
    SKIP[$t]="$reason"
  done < "$SKIP_FILE"
fi

pass=0; fail=0; skip=0; timeout=0; undet=0
rows=()
for f in "$ISA_DIR"/rv64ui-p-* "$ISA_DIR"/rv64um-p-*; do
  [ -e "$f" ] || continue
  case "$f" in *.bin) continue;; esac
  t=$(basename "$f")
  if [ -n "${SKIP[$t]:-}" ]; then
    rows+=("| $t | SKIP | - | ${SKIP[$t]} |"); skip=$((skip+1)); echo "SKIP $t (${SKIP[$t]})"; continue
  fi
  [ -f "$f.bin" ] || { rows+=("| $t | SKIP | - | 缺 .bin（未编译） |"); skip=$((skip+1)); continue; }
  log="$LOGDIR/$t.log"
  if [ "$TARGET" = npc ]; then
    if [ "$DIFF" = 1 ]; then
      env SIM_END=$((MAXCYC * 2)) timeout "${WALL}s" "$SOC_BIN" "$f.bin" "$REF_SO" > "$log" 2>&1
    else
      env SIM_END=$((MAXCYC * 2)) timeout "${WALL}s" "$SOC_BIN" "$f.bin" > "$log" 2>&1
    fi
  else
    timeout "${WALL}s" "$NEMU_BIN" -b -l "$LOGDIR/$t.nemu.log" "$f.bin" > "$log" 2>&1
  fi
  rc=$?
  cyc=$(grep -oE "t=[0-9]+" "$log" | tail -1 | grep -oE "[0-9]+")
  if grep -q "HIT GOOD TRAP" "$log"; then
    res=PASS; pass=$((pass+1)); reason="-"
  elif grep -q "HIT BAD TRAP" "$log"; then
    res=FAIL; fail=$((fail+1)); reason=$(grep -oE "HIT BAD TRAP.*" "$log" | head -1)
  elif [ "$rc" -eq 124 ] || grep -q "reach SIM_END" "$log"; then
    res=TIMEOUT; timeout=$((timeout+1)); reason="周期/墙钟看门狗超时（未判定）"
  else
    res=UNDET; undet=$((undet+1)); reason="无 TRAP 且非超时 (rc=$rc)"
  fi
  rows+=("| $t | $res | ${cyc:--} | $reason |")
  echo "$res $t"
done

{
  echo "# riscv-tests 结果（B4 R-3，TARGET=$TARGET）"
  echo
  echo "生成: $(date '+%F %T')；MAXCYC=$MAXCYC；WALL=${WALL}s"
  case "$TARGET" in
    npc)  echo "运行: NPC SoC（$SOC_BIN，flash XIP 0x30000000，链接 $RT/isa/npc，DIFF=$DIFF）";;
    nemu) echo "运行: NEMU 原生解释器（$NEMU_BIN，加载 0x80000000，链接 $RT/isa/nemu）";;
  esac
  echo
  echo "**汇总**: PASS=$pass FAIL=$fail SKIP=$skip TIMEOUT=$timeout UNDET=$undet"
  echo
  echo "| 测试 | 结果 | cycles | 备注 |"
  echo "|---|---|---|---|"
  printf '%s\n' "${rows[@]}"
} > "$OUT"
echo "[runner] 汇总: PASS=$pass FAIL=$fail SKIP=$skip TIMEOUT=$timeout UNDET=$undet"
echo "[runner] 结果表: $OUT"
