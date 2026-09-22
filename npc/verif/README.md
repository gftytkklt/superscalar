# npc/verif —— 自研处理器验证环境与文档区

> 本目录包含：**验证/性能/形式化/综合资产**（代码，§1）与**文档区**（`docs/` 活跃 + `records/` 归档，§5）。
> 入口链：根 `README.md` → `npc/README.md` → 本文件 → [`docs/PROJECT_OVERVIEW.md`](./docs/PROJECT_OVERVIEW.md)。
> **想用某个工具/流程时先查 §3「调试技术目录」**：每项给出用途、精确用法、产物与详见文档；
> 常用输出行见 §4，使用约定（gitignore/生成物/超时）见 §6。

## 1. 目录结构与文件功能

| 条目 | 功能 |
|---|---|
| `Makefile` | 裸核微验证构建入口。主要目标：`make [all]`（跑全部 `tests/*.S`）、`make run T=xxx`、`make fst T=xxx`（FST 波形）、`make ptest/pfst T=xxx`（**主存模式** `NPC_PMEM_BOOT`，复位 `0x7ffffffc`→首取 `0x80000000`，验证可缓存区 I/D cache）、`make pboot`（PSRAM memtest 探针，`PB_N=<字节数>`）、`make assert`/`assert-cache`、`make axiburst`（AXI burst 专用 tb）、`make formal`（SymbiYosys）、`make bins`、`make clean`。源文件/断言变更由 `.deps_*` 指纹自动触发重建，**不需要手删 `build/`** |
| `tb_main.cpp` | Verilator testbench：AXI4 从端内存模型 + 时钟/复位 harness；按 `a0` 打印 `HIT GOOD/BAD TRAP`，断言失败返回非 0（CI 友好）；`VTB_MAXT` 周期看门狗（默认 400000，出波形时 30000） |
| `tb_axiburst.cpp` | AXI burst 行为专用 testbench（配合 `formal/axiburst.sby` 与 `make axiburst`） |
| `tests/` | **汇编微测试 13 例**（`make all`）：`bug2_csr`（CSR 冒险）、`bug3_div`（有符号除零）、`bug4_fencei`、`cache_data`、`cache_region`、`fencei_cache`、`fencei_pipeline`（SMC+fence.i 反例）、`lduse_fwd`（load→use 前递）、`partial_store`（WR merge 字节保留）、`pmem_stress`（>4KB 伪随机写读）、`psram_burst`（32B/边界）、`residual_mret`、`shift_fwd`（移位结果下一条消费） |
| `assert/` | 仿真期断言 4 个（`bind` 注入，`$error` 报错）：`cache_bypass_check`（cacheable 访问禁入 MMIO，可 `CACHE_CHECK_OFF`）、`csr_hazard_check`（MEPC 写读冒险）、`div_zero_check`（除零商 -1）、`axi_protocol_check`（ARVALID/arlen 协议） |
| `formal/` | 形式化 **4 件**：`div.sby`（depth 100, z3）、`axiburst.sby`（35, z3）、`icache.sby`（20, boolector）、`pipeline.sby`（12, boolector；深探 `depth 20`）；`trim_rtl.py` 裁剪 RTL 并注入 46 个 `PROBE_*` 探针；`props_dcache.sv` 为无 sby 的历史残留 |
| `perf/` | 性能探针 10 个（`perf_counters.sv` + `dcache_stats/icache_stats/apbdly_check/axidly_check/axiwatch/sdramprobe/sdramcore_probe/pmem_probe/dcache_axi_probe.sv`，经 `npc/Makefile` 的 `VSRC` 注入全系统 SoC 仿真）与分析脚本 7 个（`amat_report.py`/`ctr_trace_plot.py`/`trace_locality.py`/`trace_compress.py`/`branchsim.py`/`b4_quant_eval.py`/`store_path_analysis.py`）。**不接入本 Makefile**（裸核仿真不出 `PERF`） |
| `cachesim/` | 参数化 cache 模拟器（C++，读 `CACHESIM_TRACE` 导出的 trace 扫配置）；用法见其 `README.md` |
| `sdram/` | SDRAM AXI 控制器定向回归 TB：`./run.sh` → `[TB] ALL PASS`（7 case：单/突发读写、读写交替、16 拍长突发、跨行边界）；详见其 `README.md` |
| `sta/` | 综合/STA 与部件频率探针：`gen_synth_rtl.py`（去 DPI/blackbox SRAM）、`patch_apbdelayer.py`、`probe/probe_run.sh`；结果 `result*/` |
| `boot/` | 裸机探针启动代码：`boot.S`（FSBL 搬运）、`psram_memtest.S`（PSRAM 存储测试，配 `make pboot`） |
| `riscv_tests_{build,run}.sh`、`riscv_tests_patch_env.py`、`riscv_tests_skip.txt` | riscv-tests 双目标套件资产（见 §3-⑤）；`riscv_tests_link_npc.ld` 由 build 脚本**当场生成**（不入库） |
| `build/` | 构建产物（Verilator 模型/镜像/波形/日志），不入库 |

## 2. 快速命令

```bash
make run T=cache_data        # 裸核单例（自校验，失败非 0）
make                         # 裸核全部 13 例
make fst T=cache_data        # 裸核 + FST 波形
make ptest T=cache_data      # 主存模式（0x80000000 boot）
make assert                  # 断言回归（4 监视器；assert-cache 含 bug1 检查）
make formal                  # 形式化四件
TARGET=npc DIFF=0 ./riscv_tests_run.sh      # riscv-tests 67 例（NPC 自校验）
make -C ../ perf             # SoC 性能：microbench test（基线 18,318,000/1,352,016）
cd sdram && ./run.sh         # SDRAM AXI 定向回归
```

## 3. 调试技术目录（用途 / 用法 / 产物 / 详见）

1. **裸核微验证（flash 模式）** —— 不编译 SoC/NEMU，最快定位核内功能缺陷。
   用法：`make run T=<name>`（单例）/ `make`（13 例）/ `VTB_MAXT=<cyc>` 改超时。
   产物：`RESULT: PASS/FAIL` + SRAM dump + AXI 事务日志；模型 `build/obj_dir/Vnpc`。
   详见：`docs/VERIF_TESTS.md` §1。

2. **主存模式（pmem boot）** —— 复位 `0x7ffffffc`→首取 `0x80000000`，验证可缓存区（PSRAM）I/D cache 路径。
   用法：`make ptest T=<name>` / `make pfst T=<name>`（波形）。
   产物：同 ① + `build/<T>.fst`。详见：`docs/VERIF_TESTS.md` §1。

3. **仿真期断言回归** —— 4 个 `bind` 监视器在仿真中主动报错（cache 旁路 / CSR 冒险 / 除零 / AXI 协议）。
   用法：`make assert`（关 cache 旁路检查，聚焦 bug2/3）/ `make assert-cache`（全开）。
   产物：逐例 PASS/FAIL + `build/assert_*.log`（`%Error`）。详见：`docs/VERIF_TESTS.md` §3、`assert/*.sv`。

4. **形式化（SymbiYosys BMC）** —— 除零、AXI burst、icache 透明性、五级流水等价（REF 对拍）的有界证明。
   用法：`make formal`（四件；`pipeline` depth 12 ≈2s）；深探：
   `sed 's/^depth 12/depth 20/' formal/pipeline.sby > /tmp/p20.sby && cd formal && timeout 3600 sby -f /tmp/p20.sby`
   （depth 20 约 6–8 分钟；depth 24 限时 1h 未判定）。
   产物：`formal/<design>/`（status/logfile/model/trace）。详见：`docs/VERIF_TESTS.md` §4、`records/knowledge/FORMAL_VERIFICATION_NPC.md`。

5. **riscv-tests 双目标套件** —— 官方 rv64ui+rv64um 67 例 ISA 回归（NPC 自校验；NEMU 对照）。
   用法：`./riscv_tests_build.sh npc`（或 `nemu`）→ `TARGET=npc DIFF=0 ./riscv_tests_run.sh`
   （env：`MAXCYC=1000000`、`WALL=120`、`SKIP_FILE`、`OUT`）；单例 `npc/build/ysyxSoCFull <bin>`。
   产物：四分类结果表 `records/process/RISCV_TESTS_RESULT_npc.md`；判据 `ebreak`+a0 → `HIT GOOD/BAD TRAP`；
   当前 **66 PASS / 0 FAIL / 1 SKIP（ma_data，对齐异常未实现）**。详见：`docs/RISCV_TESTS_PLAN.md`。

6. **波形调试（VCD/FST）** —— 定位时序/握手/重定向问题的首选证据（本项目多起缺陷靠窄窗口波形闭合）。
   用法：SoC：`make WAVE=1`（编译支持）→ `make sim WAVE_ON=1 WAVE_FILE=<path> WAVE_START=<t0> WAVE_END=<t1> WAVE_DIV=<N> SIM_END=<t>`；
   裸核：`make fst T=<name>`；`vcd2fst in.vcd out.fst` 转 FST 供 GTKWave/Surfer 或 wave-mcp 会话查询。
   产物：`npc/build/soc.vcd`（未 `WAVE_ON=1` 时自动删除）、`verif/build/<T>.fst`、wave-mcp 会话目录（含 `session.json`+`.fst`）。
   详见：`docs/DEBUG_WORKFLOW.md` §2.5/§6。

7. **性能计数器与统计输出** —— 讲义性能计数器闭环 + 停顿/分支/缓存/总线延迟归因。
   用法：全系统 SoC 仿真路径（探针经 `npc/Makefile` 注入）：`make -C npc perf`（microbench test，基线
   **18,318,000 / 1,352,016**；sdram-heap **15,329,912**）或 `cd am-kernels/... && make ARCH=riscv64-npc ... run`；
   `PERF=1` 开 APB/AXI 真实延迟、`PERF_R426=1` 切 r=4.25 口径、`WITH_TRACE=0` 提速。
   产物：`PERF[snap]/[ebreak]/[final]`、`PERF-CHECK`、`ICACHE_STAT`、`DCACHE_*`、`APBDLY_CHECK`、`AXIDLY_CHECK`
   （行义见 §4）。注意：裸核 `make run` 不出 `PERF`。详见：§4、`docs/STAGE_B3_CACHE_PERF.md`。

8. **总线看门狗与延迟等式自检** —— 挂死时定位最早卡点（APB/AXI AR/R/B/W、SDRAM 各级）。
   用法：随全系统仿真默认开启（探针自带 `HANG_LIMIT`，命中打印现场并 `$finish`）；调死锁时开
   `DEBUG_APBDLY=1` / `DEBUG_AXIDLY=1` 出逐事务诊断。
   产物：`APBDLY HANG` / `AXIDLY HANG` / `AXIWATCH HANG` / `SDRAMPROBE W|R-STUCK` / `SDRAMCORE STUCK` /
   `PMEM STUCK` 行。详见：§4、`records/knowledge/SDRAM_AXI_BURST_DEBUG.md`。

9. **trace 导出 + cachesim** —— 导出访存/性能序列，离线扫 cache 配置找最优。
   用法：运行期 `CACHESIM_TRACE=<path>`（`F/R/W` 行）或 `PERF_CTR_TRACE=<path>`（CSV）；
   `cd cachesim && g++ -O2 -std=c++17 -o cachesim main.cpp cachesim.cpp && ./cachesim <trace> --cal|--i|--d`。
   产物：命中率 / extra-stall TMT / 推荐配置。详见：`cachesim/README.md`。

10. **性能分析脚本（`perf/*.py`）** —— AMAT/TMT 对账、计数器曲线、程序局部性、trace 压缩、分支方向、
    量化重建、store 路径拆分。
    用法：`python3 perf/amat_report.py <perf.log>`、`python3 perf/trace_locality.py <trace> [--cacheable-only]`、
    `python3 perf/ctr_trace_plot.py <csv>`、`python3 perf/trace_compress.py <trace>`、
    `branchsim.py / b4_quant_eval.py / store_path_analysis.py --trace …`。
    产物：表/图/CSV。详见：`records/process/B4_QUANT*.md`、`records/knowledge/`。

11. **SDRAM AXI 定向回归** —— AXI BFM 直驱控制器 + 颗粒模型，防止 P-D 双根因回归。
    用法：`cd sdram && ./run.sh`。产物：`[TB] ALL PASS`（7 case）。详见：`sdram/README.md`、`docs/VERIF_TESTS.md` §5。

12. **综合/STA 与部件频率探针** —— 面积/时序评估（P-A 基线 118,805.71μm²、f_max 426MHz），性能改动前必采样。
    用法：`python3 sta/gen_synth_rtl.py` 生成可综合 RTL → `make -C <yosys-sta 目录> syn sta DESIGN=… PDK=nangate45
    CLK_FREQ_MHZ=… CLK_PORT_NAME=… O=<out> RTL_FILES=…`；部件探针 `sta/probe/probe_run.sh <top> <MHz> <outname> <rtl...>`。
    产物：`sta/result*/` 报告。详见：`records/knowledge/SYNTHESIS_STA_NPC.md`。

13. **difftest（NEMU 参考模型）** —— AM 程序/cpu-tests 的逐指令权威对拍（PC + 32 GPR）。
    用法：`make DIFF=1 sim`（或 AM 侧 `DIFF=1`）；REF = `nemu/build/riscv64-nemu-interpreter-so`。
    MMIO 访问自动 `difftest_skip_ref`（NEMU 未建模外设）；flash/SRAM/PSRAM/SDRAM 必真对拍。
    **REF 已知限制**：仅 6 个 CSR、无 `fence`；`mulh*`/`div*` 语义缺陷已于 **N-1** 修复
    （`records/process/NEMU_REF_FIXES.md`，含 REF `.so` 构建要点）→ mul/div 用例现可 DIFF=1；
    riscv-tests 默认仍 `DIFF=0` 自校验。详见：`docs/VERIF_TESTS.md` §2、`docs/RISCV_TESTS_PLAN.md` §1。

14. **看门狗与结束机制** —— 判定 PASS/超时/挂死，长跑防失控。层次：
    ① RTL `ebreak` retire → DPI `sim_end`；② harness 按 `a0` 打印 `HIT GOOD/BAD TRAP`；
    ③ SoC `SIM_END=<半周期>` 强制退出（riscv runner 用 `MAXCYC×2`）；④ 裸核 `VTB_MAXT`（默认 400000；
    带波形 30000）超时 FAIL；⑤ 探针 HANG 看门狗（§4）；⑥ runner 墙钟 `timeout WALL`。
    长跑：`setsid` 脱离 + `SIM_END` + 查镜像大小 + 结束后清理进程（详见 `records/knowledge/LONG_SIM_PROC_MGMT.md`）。

15. **开关速查与定向用例索引** —— 常用编译/运行开关与历史调试用例。
    开关：`DIFF / WAVE(+WAVE_ON/WAVE_FILE/WAVE_START/END/DIV) / WITH_TRACE / WITH_SDL / PERF / PERF_R426 /
    DEBUG_APBDLY / DEBUG_AXIDLY`、AM 侧 `BOOT_MODE / HEAP_SIZE / LDS / BOOT_S`；构建开关与源文件变化由
    `npc/build/.build_cfg` 与 `.deps_*` 指纹自动重建（无需手删 `build/`）。
    定向用例：正式 13 例见 §1（其中 `fencei_pipeline`=SMC 反例、`lduse_fwd`=load-use 前递、`shift_fwd`=移位自依赖）；
    历史 `tmp/*.S`（`divuw_dbg.S`、`jalr_raw.S`、`jalr_seq.S`）与 records 内嵌反例（如 R-5b 远目标行边界用例）。
    详见：`docs/RUN_GUIDE.md`、`docs/DEBUG_WORKFLOW.md` §2。

## 4. 常用输出行速查

| 输出行 | 来源探针 | 关键字段含义 |
|---|---|---|
| `PERF[snap @N]` | `perf_counters` | 每 5,000,000 周期的进度快照（长跑用） |
| `PERF[ebreak]` / `PERF[final]` | `perf_counters` | `cycles/retire/ifu_deliver/lsu/exu`；consistency；classes（mem/csr/branch/compute/other/bubble）；`ifu_miss/mul`；stalls（lduse/mdu）；branches（taken/ntaken/jal/jalr）；rd/st_region |
| `PERF-CHECK OK/FAIL` | `perf_counters` | `decode==retire==exu`；`cat_sum==decode`；`deliver−decode≈bubble` |
| `ICACHE_STAT` / `ICACHE_MISS_PENALTY` | `icache_stats` | hit/miss/hit_lat/tmt_sum；分区域缺失 avg/n/peak |
| `DCACHE_STAT` / `DCACHE_*_MISS_PENALTY` / `DCACHE_WR_MISS_SPLIT` / `DCACHE_MMIO_LAT` | `dcache_stats` | hit/miss/wb；读/写缺失分区域代价；写缺失 fill/wb 拆分；MMIO 时延 |
| `APBDLY_CHECK … EQUATION OK/eqv` | `apbdly_check` | `n_txn/eq_viol/avg_k/avg_exp/avg_t1′/max_k`；延迟等式 `(t1−t0)·r == t1′−t0` |
| `AXIDLY_CHECK … EQUATION OK` | `axidly_check` | `n_rbeats/eq_viol_r/burst_mismatch/n_b/eq_viol_b` |
| `PMEM COUNT` / `AXIWATCH HANG` / `SDRAMPROBE …` / `SDRAMCORE STUCK` / `PMEM STUCK` | 各 watchdog | 卡点现场（HANG 即 `$finish`） |

## 5. 文档区

| 位置 | 内容 |
|---|---|
| [`docs/`](./docs/) | **活跃文档**：`PROJECT_OVERVIEW.md`（总览/现状与目标/文档索引——先看这个）、`DEBUG_WORKFLOW.md`（开关/启动链/硬件经验/阶段记录）、`RUN_GUIDE.md`（各测试程序编译运行权威速查）、`VERIF_TESTS.md`（验证体系：微测试/断言/形式化/SDRAM TB）、`WORKFLOW_POLICY.md`（推进工作流政策）、`RISCV_TESTS_PLAN.md`（套件引入计划与 R-1~R-5 状态）、`ARCH_OPT_BACKLOG.md` + `arch_opt/`（优化台账与子文档）、`B3_PLAN.md`/`STAGE_B3_CACHE_PERF.md`/`B4_PLAN.md`/`B4_Q7_PLAN.md`（历史阶段计划与任务说明） |
| [`records/process/`](./records/process/) | **归档·日志型**：各阶段实施/调试过程记录、任务提示词、riscv-tests 结果表（索引见其 README） |
| [`records/knowledge/`](./records/knowledge/) | **归档·经验性**：案例复盘/方法论/性能分析 + 跨文档经验地图（索引见其 README） |

整机（SoC 全系统仿真 / difftest / NVBoard）与 AM 应用的运行方式见仓库级文档：根 `README.md` → `npc/README.md` → `docs/RUN_GUIDE.md`。

## 6. 使用约定

- **文档入库范围**：`npc/.gitignore` 只放行各级 `README.md` 与代码/脚本白名单；`docs/`、`records/` 下其余
  md 与生成物（如 `riscv_tests_link_npc.ld`）为工作区本地文档，以各级 README 索引为查阅入口。
  注意白名单不含 `*.sh/*.txt/*.ld`：新增脚本/链接脚本需加 `!` 白名单或 `git add -f`，否则会被静默忽略。
- **依赖未入库文件**：裸核微测试链接依赖 `npc/scripts/linker-soc.ld`（与 `linker-sram.ld`）——不在版本控制内，
  clean clone 需先具备对应脚本；riscv-tests 链接脚本由 `riscv_tests_build.sh` 当场生成，不受影响。
- **超时口径**：裸核 `VTB_MAXT`（默认 400000；波形 30000）；SoC `SIM_END`（半周期计数）；riscv runner
  `MAXCYC×2` + `WALL=120s` 双看门狗。超时一律当"未判定"，不算 PASS。
