#!/usr/bin/env bash
# P-B 部件级频率评估平台：对给定 RTL（输入/输出已包 FF 的探针）跑 nangate45 综合 + STA，
# 提取 面积 / 最差路径延迟 / f_max。
#
# 用法：./probe_run.sh <top模块名> <目标频率MHz> <输出目录根名> <RTL文件...>
#   f_max(MHz) = 1000 / 最差路径延迟(ns)（取 core_clock 的 max 路径，忽略 clock_gating 组）。
#   iEDA 时钟端口名固定 clk（探针顶层端口统一为 clk）。
set -euo pipefail
TOP=$1; FREQ=$2; OUTNAME=$3; shift 3
[ $# -ge 1 ] || { echo "usage: $0 <top> <freqMHz> <outname> <rtl files...>"; exit 1; }
RTL=""
for f in "$@"; do RTL+=" $(readlink -f "$f")"; done

WB=/home/gftyt/ysyx-workbench
OUT=$WB/npc/verif/sta/result-$OUTNAME
LOG=/tmp/probe_${OUTNAME}.log
make -C $WB/yosys-sta syn sta DESIGN=$TOP PDK=nangate45 CLK_FREQ_MHZ=$FREQ \
     CLK_PORT_NAME=clk O=$OUT RTL_FILES="$RTL" > "$LOG" 2>&1

RPT=$(ls $OUT/$TOP-*/$TOP.rpt 2>/dev/null | head -1)
STAT=$(ls $OUT/$TOP-*/synth_stat.txt 2>/dev/null | head -1)
[ -n "$RPT" ] || { echo "STA report not found (see $LOG)"; exit 1; }

AREA=$(grep -o 'Chip area for module.*: [0-9.]*' "$STAT" | grep -o '[0-9.]*$' | head -1)
# 取 core_clock 的 max 路径最大 Path Delay（去掉 r/f 后缀）
DELAY=$(awk -F'|' '$3 ~ /core_clock/ && $4 ~ /max/ {d=$5; gsub(/[rf ]/,"",d); if (d+0>m) m=d+0} END {if (m) printf "%.3f", m}' "$RPT")
FMAX=$(python3 -c "print(f'{1000/float('$DELAY'):.1f}')")
echo "== $TOP @ target ${FREQ}MHz: area=${AREA} um^2, worst_delay=${DELAY}ns, f_max=${FMAX}MHz"
echo "   report: $RPT"
