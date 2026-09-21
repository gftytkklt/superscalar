# npc/verif/records —— 归档区（历史调试过程与经验记录）

> **归档说明（2026-09-04 重组；2026-09-21 结构化重构）**：本目录为纯归档区，按文档性质分两类存放：
>
> | 子目录 | 性质 | 内容 |
> |---|---|---|
> | [`process/`](./process/) | **日志型** | 阶段实施记录、调试过程时间线、任务提示词（续作 PROMPT）、计划——**按项目推进顺序组织**（访存体系→外设→B3 阶段1–8→ONScripter→环境），重复/取代关系见其 §7 |
> | [`knowledge/`](./knowledge/) | **经验性** | 案例复盘、方法论沉淀、性能分析——按「B3 性能链 / 工具入门 / 工程方法 / 跨平台旧案」分组，含按阶段排序的经验地图 |
>
> **当前活跃文档**（入口/工作流/运行速查/测试体系/当前阶段）在上级目录 `npc/verif/`，
> 总入口见 `../docs/PROJECT_OVERVIEW.md`（含"现状与目标"：NEMU+NPC 双端启动 Linux、NPC 持续性能优化）。
> 新阶段的产出按 `../docs/WORKFLOW_POLICY.md` §4 落档：过程记录入 `process/`，提炼的经验入 `knowledge/`，
> 并同步更新对应 README 索引。

## 索引

- **日志型归档索引**：[`process/README.md`](./process/README.md) —— 访存体系（STAGE1–3）/
  RT-Thread·SDRAM·外设（STAGE_F–K、J0–J5）/ **B3 性能优化阶段1–8（含 P-A~P-H 计划→结果→附件）** /
  ONScripter / 环境（含附件清单与权威/快照/被取代表）
- **经验性归档索引**：[`knowledge/README.md`](./knowledge/README.md) —— B3 性能链（含被取代标注）、
  形式化/综合 STA 入门、长仿真进程管理、跨平台旧案 + 按阶段排序的经验地图

> **重构记录（2026-09-21）**：本轮按"项目推进顺序"重排两张索引、补全缺失条目（附件、
> `YSYXSOC_REGEN_SETUP`、`B3_CTR_TRACE`）、标注重复/取代关系；计划与范围见
> [`RECORDS_RESTRUCTURE_PLAN.md`](./RECORDS_RESTRUCTURE_PLAN.md)（含讲义复核结论）。

## 工具链状态（B3/E1 相关，全部就绪）

| 项 | 状态 | 说明 |
|---|---|---|
| **yosys-sta** | ✅ 已安装（2026-09-08） | oss-cad-suite (Yosys 0.68) + iEDA/icsprout55；GCD 样例与 npc 均跑通 |
| **ysyxSoC Chisel 重生成链** | ✅ 已打通（2026-09-09，P-D 前置） | mill 0.11.12/firtool 1.51.0/JDK17；学号定制点=`soc/CPU.scala` BlackBox 类名；apb_delayer 固化；**重生成后 PERF 与基线逐位一致**。详见 `process/YSYXSOC_REGEN_SETUP.md` |
| **oss-cad-suite / btormc** | ✅ 已装（`~/oss-cad-suite`） | sby/boolector 可用（阶段6 解锁；`records/knowledge/FORMAL_VERIFICATION_NPC.md`） |
| **OpenSTA** | — 不需要 | yosys-sta 用 iEDA/iSTA |
| **npc 可综合化适配（E1a）** | ✅ 已完成 | `verif/sta/gen_synth_rtl.py`：去 DPI + blackbox `sram_behav` |
| **E1b：STA 出频率算 `r`** | ✅ 已完成 | icsprout55 f_max≈349.7MHz→`r≈3.5`；nangate45 复测 120,383.62μm²/411MHz（`process/B3_STAGE8_AREA_N45.md`）；A1 后 118,805.71μm²/426MHz |
| **E1c/E1d：APB 延迟校准 + 等式校验** | ✅ 已完成（2026-09-08） | `apb_delayer.v`（B 方案，`PERF_DELAY` 门控）；`(t1−t0)·r == t1'−t0` EQUATION OK；IPC 0.196→0.074（`process/B3_STAGE5_PERF.md`） |
| **B3 阶段1–8 全部任务** | ✅ 完成（E4 用户裁决暂停） | 讲义 34 项清单与状态见 `../docs/STAGE_B3_CACHE_PERF.md` §1；推进历史见 `process/README.md` |

> 下一步回到全局目标：**① NEMU+NPC 双端启动 Linux；② 持续性能优化**
> （依据 `PROJECT_OVERVIEW.md` 未来目标 + `knowledge/MEM_PIPELINE_OPT.md` 的方法底座 +
> `process/B3_STAGE8_PE_DSE.md` 的 Pareto 备选方案，如需重启 E4）。
