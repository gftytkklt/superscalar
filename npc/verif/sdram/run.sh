#!/usr/bin/env bash
# SDRAM AXI 控制器定向回归（P-D 根因回归测试）
#   cd npc/verif/sdram && ./run.sh
# 期望输出：各 case 无 MISMATCH，最后一行 "[TB] ALL PASS"。
set -e
cd "$(dirname "$0")"
SYNC="$(cd ../.. && pwd)/ysyxSoC/perip/sdram"

rm -rf obj_dir
verilator --binary -j 4 -Wno-fatal -O2 --top-module tb \
  "$SYNC/sdram_top_axi.v" \
  "$SYNC/core_sdram_axi4/sdram_axi.v" \
  "$SYNC/core_sdram_axi4/sdram_axi_core.v" \
  "$SYNC/core_sdram_axi4/sdram_axi_pmem.v" \
  "$SYNC/sdram.v" \
  tb_sdram_ctrl.sv -o tb_sdram_ctrl >/dev/null
./obj_dir/tb_sdram_ctrl
