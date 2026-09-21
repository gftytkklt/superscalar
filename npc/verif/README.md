# npc/verif —— 自研处理器验证环境与文档区

> 本目录包含两大部分：**RTL 微验证环境**（代码，见下表）与**文档区**（`docs/` 活跃 + `records/` 归档）。
> 文档总入口：[`docs/PROJECT_OVERVIEW.md`](./docs/PROJECT_OVERVIEW.md)（项目总览/现状与未来目标/文档索引）。

## 1. 目录结构与文件功能

| 条目 | 功能 |
|---|---|
| `Makefile` | 验证环境构建入口。主要目标：`make run T=xxx`（仿真+自校验）、`make fst T=xxx`（出波形）、`make ptest/pfst T=xxx`（**主存模式** `NPC_PMEM_BOOT`，PC 复位 0x80000000，验证可缓存区 icache/dcache）、`make pboot`（PSRAM memtest 探针）、`make assert` / `make assert-cache`（挂接 `assert/` 断言的仿真）、`make axiburst`（AXI burst 专用 tb）、`make formal`（SymbiYosys 形式化）、`make bins`（汇编用例批量编译） |
| `tb_main.cpp` | Verilator testbench：AXI4 内存模型 + 时钟/复位 harness，断言失败返回非 0（CI 友好） |
| `tb_axiburst.cpp` | AXI burst 行为专用 testbench（配合 `formal/axiburst.sby`） |
| `tests/` | 汇编微测试（10 个）：回归类 `bug2_csr`（CSR 冒险）/`bug3_div`（有符号除零）/`bug4_fencei`；访存类 `cache_data`/`cache_region`/`fencei_cache`/`partial_store`/`pmem_stress`/`psram_burst`；控制流 `residual_mret` |
| `assert/` | 仿真期断言（`bind` 注入的 SystemVerilog 监视器，`$error` 报错）：`cache_bypass_check`（cacheable 访问禁入 MMIO 态，可 CACHE_CHECK_OFF）、`csr_hazard_check`（CSR 写读冒险·MEPC 定向）、`div_zero_check`（除零商必须 -1）、`axi_protocol_check`（AXI 协议合法性） |
| `formal/` | SymbiYosys 形式化：`div.sby`+`props_div.sv`（除零证明 ✅ PASS）、`axiburst.sby`+`props_axiburst.sv`（读通道证明 ✅ PASS）、`props_icache/dcache.sv`（缓存性质属性集；dcache.sby 因大查找表 BMC 不可判定已移除，见 `docs/VERIF_TESTS.md` §4）、`trim_rtl.py`（形式化前裁剪 RTL） |
| `perf/` | `perf_counters.sv`：B3 阶段非侵入式性能计数器（`bind` 注入 `ysyx_22040750_cpu_core`，不改核 RTL，分 `ifu_deliver`/`decode_*`/`retire`/`lsu`/`exu`/类别 + 周期快照）。**接入点**：经 `npc/Makefile` 的 `VSRC += ./verif/perf/perf_counters.sv`（第 25 行）随全系统 SoC 仿真（top=`ysyxSoCFull`）编译，在 ebreak/HIT GOOD TRAP 时 `$display` 输出、并周期 `PERF[snap]` 快照。**不接入**本 `verif/Makefile`（裸核 harness，top=`ysyx_22040750`），故 `make run`/`make ptest` 不会出 PERF。分析脚本：`trace_locality.py`（P-H/#12：CACHESIM_TRACE→工作集/行距/重用间隔 4 图+表，`--cacheable-only` 剔非缓存区）、`trace_compress.py`（P-H/#19：text/bin5/bitpack/dvar/dseg × gzip/bzip2/xz 压缩对比，round-trip 校验）、`amat_report.py`（P-C：日志→AMAT/TMT） |
| `cachesim/` | B3 阶段3 参数化 cache 模拟器（C++）：读 trace（`CACHESIM_TRACE` 由 npc 导出）→ 按 8KB/整颗SRAM 约束扫配置 → 命中率 + extra-stall TMT + 推荐。用法/编译见其 `README.md`；分析见 `records/knowledge/B3_CACHESIM_ANALYSIS.md` |
| `boot/` | 裸机探针启动代码：`boot.S`（微测试公共启动）、`psram_memtest.S`（PSRAM 存储测试） |
| `sdram/` | **SDRAM AXI 控制器定向回归 TB**（P-D 收尾新增）：`tb_sdram_ctrl.sv` + `run.sh`，AXI BFM 直驱 `sdram_top_axi` + 自制颗粒模型，覆盖单/突发读写、读写交替、16 拍长突发、跨 512 列行边界（7 case）；**P-D 双根因**（`sdram.v` 背靠背读、`axi64to32` FIXED 宽拆）的固定防回归测试，见 `records/knowledge/SDRAM_AXI_BURST_DEBUG.md` |
| `build/` | 构建产物（Verilator 模型/编译中间物），不入库 |

## 2. 文档区

| 位置 | 内容 |
|---|---|
| [`docs/`](./docs/) | **活跃文档**：`PROJECT_OVERVIEW.md`（总览/现状与目标/文档索引——先看这个）、`DEBUG_WORKFLOW.md`（调试工作流+编译开关+启动链+阶段执行记录）、`RUN_GUIDE.md`（各测试程序编译运行命令速查）、`VERIF_TESTS.md`（验证体系：微测试/断言/形式化）、`WORKFLOW_POLICY.md`（开发推进工作流政策）；当前阶段文档 `B3_PLAN.md` + `STAGE_B3_CACHE_PERF.md`（性能计数器与缓存调优） |
| [`records/process/`](./records/process/) | **归档·日志型**：各阶段实施/调试过程记录、任务提示词（索引见其 README） |
| [`records/knowledge/`](./records/knowledge/) | **归档·经验性**：案例复盘/方法论/性能分析 + 跨文档经验地图（索引见其 README） |

## 3. 快速命令

```bash
make run  T=dummy            # 跑单个微测试（自校验，失败返回非 0；不带性能计数器）
make fst  T=cache_data       # 同上但生成波形 (build/*.fst；不带性能计数器)
make ptest T=cache_data      # 主存模式(0x80000000 boot)：验证可缓存区 icache/dcache
make assert                  # 断言全量仿真（assert/ 四个监视器）
make formal                  # SymbiYosys 形式化（需 sby/z3）
```

> 性能计数器（`perf/perf_counters.sv`）**不在本验证环境**编译，需走全系统 SoC 仿真路径
> （`npc/Makefile`，见上面 `perf/` 行）：例如
> `cd am-kernels/benchmarks/microbench && make ARCH=riscv64-npc HEAP_SIZE=0x400000 WITH_TRACE=n run mainargs=test`
> 或 `cd am-kernels/tests/cpu-tests && make ALL=dummy ARCH=riscv64-npc run`，仿真结束会打印
> `PERF[ebreak]` / 周期 `PERF[snap]`。

整机（SoC 全系统仿真 / difftest / NVBoard）与 AM 应用的运行方式见仓库级文档：
根 `README.md` → `npc/README.md` → `docs/RUN_GUIDE.md`。

> 注：`docs/` 与 `records/` 下除各级 `README.md` 外的 md 被 `npc/.gitignore` 忽略（工作区本地文档），
> 以各级 README 索引为查阅入口。
