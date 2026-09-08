# npc/verif/records —— 归档区（历史调试过程与经验记录）

> **归档说明（2026-09-04 重组）**：本目录为纯归档区，按文档性质分两类存放：
>
> | 子目录 | 性质 | 内容 |
> |---|---|---|
> | [`process/`](./process/) | **日志型** | 阶段实施记录、调试过程时间线、任务提示词（续作 PROMPT）、修复计划——按时间顺序叙述"当时做了什么" |
> | [`knowledge/`](./knowledge/) | **经验性** | 案例复盘、方法论沉淀、性能分析——可复用的"怎么做/为什么"，独立于具体时间线 |
>
> **当前活跃文档**（入口/工作流/运行速查/测试体系/当前阶段 B3）在上级目录 `npc/verif/`，
> 总入口见 `../docs/PROJECT_OVERVIEW.md`（含"现状与目标"：NEMU+NPC 双端启动 Linux、NPC 持续性能优化）。
> 新阶段的产出按 `../docs/WORKFLOW_POLICY.md` §4 落档：过程记录入 `process/`，提炼的经验入 `knowledge/`，
> 并同步更新对应 README 索引。

## 索引

- **日志型归档索引**：[`process/README.md`](./process/README.md) —— STAGE1~3 / STAGE_F / STAGE_I / STAGE_J0–J5 /
  STAGE_H_ONWARDS / ONScripter 全系列（含 PROMPT 与计划）
- **经验性归档索引**：[`knowledge/README.md`](./knowledge/README.md) —— RT-Thread 栈溢水案例复盘、
  访存流水线性能分析、跨文档经验地图（指向各过程文档中的方法论章节）

> 历史注记：本目录前身为"分阶段调试过程记录（归档）"，2026-08-31 集中归档于 verif/ 根目录，
> 2026-09-04 拆分为 process/knowledge 两区并将 B3 活跃文档上移至 `npc/verif/` 顶层。

## 待办 —— 未安装工具（阻塞 E1 / 时序分析）
> 记录未安装/待补的工具依赖，避免遗漏。相关 B3 分析见 `knowledge/B3_CACHESIM_ANALYSIS.md`、`B3_STAGE2_PERF_ANALYSIS.md`。

| 项 | 状态 | 说明 |
|---|---|---|
| ~~yosos‑sta（`ysyx-workbench/yosys-sta/`）~~ | ✅ **已安装（2026-09-08）** | oss-cad-suite (Yosys 0.68) + `make init` 拉的 iEDA/icsprout55 均就绪，GCD 样例与 npc 均跑通 |
| ~~oss‑cad‑suite / 新版 Yosys~~ | ✅ 已装（`~/oss-cad-suite`，Yosys 0.68） | btormc/sby/boolector 同步可用（Stage6 解锁） |
| ~~OpenSTA~~ | — 不需要 | yosys‑sta 用 iEDA/iSTA |
| **npc 可综合化适配** | ✅ **已完成（E1a）** | `npc/verif/sta/gen_synth_rtl.py`：去 17 处 DPI + blackbox `sram_behav`；`ysyx_22040750_synth.v` 可综合 |
| **E1b：STA 出频率算 `r`** | ✅ **已完成** | 500MHz 目标/DELAY-4：**f_max≈349.7MHz**（worst path=icache FSM 2.832ns；次=PC dnpc），面积 163689.68（SRAM blackbox→频率偏乐观）。**`r ≈ 3.5`**。产物在 `npc/verif/sta/result/ysyx_22040750-500MHz/` |
| **E1c：APB 延迟校准模块** | ✅ **已完成（2026-09-08）** | `apb_delayer.v`（B 方案：请求直通+响应整拍延迟 `t1'=t0+floor(r·k)`），`` `PERF_DELAY` `` 宏门控（默认直通，`make perf` 才启）；并修复 SPI XIP / PSRAM 控制器"持续电平重触发"缺陷（见 `knowledge/APB_PSRAM_HANDSHAKE_DEBUG.md`） |
| **E1d：延迟等式校验 + 校准后 IPC** | ✅ **已完成（2026-09-08）** | `verif/perf/apbdly_check.sv` 校验 `(t1-t0)*r == t1'-t0`（PERF_DELAY 下 EQUATION OK，microbench test 全过）；IPC：无校准 0.196 → 有校准 0.074（`process/B3_STAGE5_PERF.md`） |

> E1c/E1d 已完成。下一步回到全局目标：**① NEMU+NPC 双端启动 Linux；② 持续性能优化**（依据
> `PROJECT_OVERVIEW.md` 未来目标 + `knowledge/MEM_PIPELINE_OPT.md`/`B3_CACHESIM_ANALYSIS.md` 的瓶颈结论）。
