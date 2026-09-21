# records/process —— 日志型归档（阶段实施/调试过程/任务提示词）

> **按项目推进顺序组织**：访存体系（阶段1–3）→ RT-Thread/SDRAM/外设（阶段F–K）→ B3 性能优化
> （阶段1–8）→ ONScripter（PA4.5 选做）→ 环境。每组内按「任务入口（PROMPT/TASKS）→ 计划（PLAN）
> → 结果（RECORD）」排列，附件（图/表）列在所属记录行下。
> 经验性文档见 [`../knowledge/README.md`](../knowledge/README.md)；入口总览见
> [`../../docs/PROJECT_OVERVIEW.md`](../../docs/PROJECT_OVERVIEW.md)。
> 重复/取代关系见文末 §7「权威 / 快照 / 被取代」。

**状态图例**：✅ 结案/完成 ｜ ⏸ 用户裁决暂停 ｜ 📦 历史快照（保留过程价值，结论以权威文档为准） ｜ ⚠️ 部分结论过期（见 §7）

## 1. 访存体系（阶段1–3）✅

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `STAGE1_CACHE_REWORK.md` | RECORD | 缓存重构 + SoC 访存接口适配：AX/X 耦合点 C1–C8、dcache 写分配掩码、fence.i/cacheline 写回 bug、验证体系；**§9 为阶段2 设计草稿**（与 STAGE2 重叠，以 STAGE2 为准） | ✅ |
| `STAGE2_MEM_IF.md` | PLAN | 阶段2 访存接口重构设计基线：CPU↔cache 接口、AXI burst/MMIO 生成、slave_crossbar、SoC 地址映射、S0–S5 实施计划 | ✅ |
| `STAGE3_PSRAM_READDBG.md` | RECORD | 阶段3 PSRAM 读回错位调试：flash 数据通路修复、逐级定位、根因=dcache 写分配掩码 | ✅ |

## 2. RT-Thread / SDRAM / 外设（阶段F–K）✅

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `STAGE_F_RTTHREAD_PROMPT.md` | PROMPT | 阶段F 任务入口（bootloader 把 RT-Thread 搬 PSRAM 执行）；最终结论见 `../../docs/DEBUG_WORKFLOW.md` 阶段F | 📦 |
| `STAGE_H_ONWARDS_TASKS.md` | PLAN | 阶段 H–K 任务定义与实现路径（SDRAM 位/字扩展、J1–J5、ChipLink）；各阶段结论已固化到对应 `STAGE_*` 记录 | ✅ |
| `STAGE_J_ONWARDS_PROMPT.md` | PROMPT | 阶段J 任务入口（J4/J5 现状/目标/实现路径；J1–J3 见 H_ONWARDS） | 📦 |
| `STAGE_I_SDRAM_EXT_PROMPT.md` | PROMPT | 阶段I 任务入口（SDRAM 位扩展 2→32bit + 字扩展 4 颗粒） | 📦 |
| `STAGE_I_SDRAM_EXT.md` | RECORD | 阶段I 实施：位扩展(64MB)+字扩展(128MB) 相位推导/改动/坑/验证数据 | ✅ |
| `STAGE_J0_NVBOARD.md` | RECORD | J0 NVBoard 接入 soctest + GPIO 7 段译码；坑与验证 | ✅ |
| `STAGE_J1_GPIO.md` | RECORD | J1 GPIO：控制器 RTL + 寄存器/引脚验证（difftest ON + 波形） | ✅ |
| `STAGE_J2_UART.md` | RECORD | J2 UART：AM_UART_RX + 除数条件化 + RT-Thread 键入 + hello 验证 | ✅ |
| `STAGE_J3_PS2.md` | RECORD | J3 PS/2 键盘：RTL 解码+FIFO + AM 键盘 IOE 翻译表 | ✅ |
| `STAGE_J4_VGA.md` | RECORD | J4 VGA/timer/video：vga_top_apb + AM GPU IOE + mtime | ✅ |
| `STAGE_J5_RTTHREAD_AM.md` | RECORD | J5 rt-am 合并 + am-apps 集成（hello/microbench/snake → msh am_<app>） | ✅ |

## 3. B3 性能优化（阶段1–8）✅（E4 用户裁决暂停）

> 阶段8 按计划顺序 **P-A → P-H** 分组，每组「入口/计划 → 结果 → 附件」；
> `STAGE_B3_CACHE_PERF.md` §1 是讲义 34 项全清单与状态，`B3_PLAN.md` 是整体计划。

### 3.1 阶段1–4：性能计数 / Amdahl / cachesim / APB 校准

> 阶段1–4 无独立过程记录，结果沉淀在 knowledge：
> `../knowledge/B3_STAGE2_PERF_ANALYSIS.md`（阶段2，⚠️旧数字）、`../knowledge/B3_CACHESIM_ANALYSIS.md`
> （阶段3，⚠️旧成本模型）、`../knowledge/APB_PSRAM_HANDSHAKE_DEBUG.md`（阶段4 E1c/E1d 根因与修复范式）；
> 阶段4/5 的校准结论与 IPC 见 `B3_STAGE5_PERF.md`。

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_CTR_TRACE.md` | RECORD | 补充讲义「性能计数器的trace」（选做）：`PERF_CTR_TRACE` 环境变量 → 每 10 万周期 CSV + `verif/perf/ctr_trace_plot.py` 四联图；基线逐位复现（18,318,000/1,352,016）；区间 IPC p50=0.012/p90=0.241/max=0.553（相位时变可视化） | ✅ |

附件：`B3_CTR_TRACE.png`、`B3_CTR_TRACE_summary.md`

### 3.2 阶段5–7（`make perf` / icache 形式化 / 校准后瓶颈与主频取舍）✅

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE5_PERF.md` | RECORD | 阶段5：APB 延迟校准（E1c/E1d，r=3.5）+ `make perf` IPC 对比：无校准 0.196 → 有校准 0.074；含 XIP/PSRAM 状态机重触发根因（与 knowledge APB 篇配套） | ✅ |
| `B3_STAGE6_ICACHE_BMC.md` | RECORD | 阶段6：icache 数据透明性 BMC（btormc PASS @ depth≤35，状态≈1500 位；depth 40 超时=判定上限；cover 证实非空泛） | ✅ |
| `B3_STAGE7_PROMPT.md` | PROMPT | 阶段7 任务入口（校准后重新找瓶颈 + 主频是否值得） | 📦 |
| `B3_STAGE7_RECALIB_PERF.md` | RECORD | 阶段7 结案：r=3.5 IPC=0.0738；**store 写路径 41%T 为 #1（Amdahl 1.69×）**、load 29.5%、UART 轮询 12.4%；提频：p_mem=0.70 天花板 +42%、α=2 已取 90% 但 IPC −36% → 先降 p_mem 再提频 | ✅ |

### 3.3 阶段8（P-A → P-H）✅

**P-A 面积专题（#29，讲义"远超上限马上优化"）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_AREA_N45.md` | RECORD | 面积复测（nangate45）：**120,383.62μm²（4.8× 上限）/ f_max≈411MHz**，关键路径=icache FSM；层级面积表（dcachectrl 36.3K/icachectrl 25.9K/gpr 18.0K=67%）+ 根因（逐行译码写、FF 寄存器堆）；含 #15 dcache 理想收益 3.38×、#31 性价比快答 | ✅ |
| `B3_STAGE8_PA_A1.md` | RECORD | A1 面积优化：**118,805.71μm²（−1.3%）/ f_max≈426MHz（+3.7%）双改善**；"编码冗余"假设被实验否定（V1 已回退）；A2/A3 清单已定义、**暂停**；功能零变化（微测试 16/16 + PERF 逐位） | ✅（A2/A3 ⏸） |

**P-B 部件级最高频率（#6）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PB_FMAX.md` | RECORD | 探针平台 `verif/sta/probe/`：**gpr 2,041MHz / 64bit 加减法器 697MHz**（全芯片 426MHz，关键路径仍 icache FSM）→ 数据通路非提频瓶颈；**用户拍板 C：`PERF_R426=1` 参数化 r**（默认 3.5 不动）；§6 r=4.25 复跑（EQUATION OK，SDRAM 代价超线性、布局排序翻转） | ✅ |

**P-C AMAT/TMT 平台（#17/#27）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PC_PD_PLAN.md` | PLAN | P-C+P-D 执行计划（架构核实：bus 直连 64bit 突发；SoC 侧 delayer + 64→32 保形；D1–D6 步骤） | ✅（已执行） |
| `B3_STAGE8_PC_AMAT.md` | RECORD | P-C 平台：`icache_stats.sv` + `amat_report.py`（日志→AMAT/TMT）；基线 **icache AMAT=3.02**；新洞察 icache flash refill≈19%T；关闭 #17 | ✅ |
| `B3_STAGE8_PC_AMAT_LAYOUT.md` | RECORD | P-C 三配置复跑（A xip/B sdram-heap/C 全 SDRAM）：堆放 SDRAM 写缺失 2244→1422、端到端 18.32M→15.33M；**.text 进 SDRAM icache AMAT 3.02→1.58、纯 kernel −31%**，但 boot 搬运 ~5.5M 吃掉端到端；§6 追加 r=4.25 排序翻转（**写于 P-E/P-F 期间，晚于 P-D**） | ✅ |

**P-D SDRAM AXI 突发链（#23–26）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PD_PROMPT.md` | PROMPT | P-D 任务入口（遗留 bug A/B 直至全绿） | 📦 |
| `B3_STAGE8_PD_DEBUG.md` | RECORD | **P-D 结案（权威）**：§7 双根因=①自制 `sdram.v` 读输出不支持背靠背读→CAS 流水线（RD_DELAY=2）；②`axi64to32` 宽拆保留 FIXED→强制 INCR；验证：定向 TB 7 case + 配置 X/Z microbench 全绿 + mem-test + 等式 OK + `make perf` 逐位一致 | ✅ |
| `B3_STAGE8_PD_HANDOFF.md` | SNAPSHOT | P-D 中途交接快照；其中"写拍重复 4160 vs 986"已被 PD_DEBUG §7.1 证伪（探针窗口口径），A/B 已结案 | 📦 |

**P-E cachesim 闭环 + 面积约束 DSE（#18/#20/#21/#22/#30）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PE_PLAN.md` | PLAN | P-E 阶段计划 E1–E4（计划已执行：E1/E2/E3 结案、E4 暂停） | ✅（计划） |
| `B3_STAGE8_PE_CACHESIM_DIFF.md` | RECORD | E1 对账：trace F 钩子改取指握手后 F 与 ICACHE 精确一致、替换策略对齐后**结构 0 偏差**；**成本模型校准**（`--cal`）后缺失 TMT 精确；**校准后 16B 块成最优（−13.2%），推翻旧 +3.5% 结论** | ✅ |
| `B3_STAGE8_PE_DSE.md` | RECORD | E2/E3：16B 块 TMT 最优但 8KB 内需 5 路（面积 +59%）；**全局 Pareto 推荐 icache 2KB/32B/1w + dcache 8KB/64B/2w（TMT −6.5%、面积持平）**；省面积/激进方案并列 | ✅ |
| `B3_STAGE8_PE_E4_PLAN.md` | PLAN | E4 实施计划（A 方案、E4.1–E4.4、PSRAM 64B 风险）——**未按此执行** | 📦 |
| `B3_STAGE8_PE_E4_SAMPLE.md` | RECORD | E4.1 `dcachectrl` 参数化（默认零回归）+ E4.2 面积采样（实测 +13.9% vs 模型 −2.2%，偏差 >15% 停点）→ **用户裁决暂停 E4，P-E 结案**；资产保留（参数化/采样 wrapper/校准 cachesim） | ⏸ |

**P-F 加载路径 / 程序内存布局（#28）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PF_LOADER.md` | RECORD | 加载路径：搬运 ~30KB = **5.58M cyc（77% flash 行填充）**、`boot_sram.c` 拷贝改 8B 批量（端到端 −0.14M）；**break-even≈50M cyc → 默认 sdram-heap、长跑 sdram**；§6 #28 填充/对齐（align 8/64/128）全负收益、`.rodata` 留 flash 否决 | ✅ |

**P-G train 规模性能记录（#8）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PG_TRAIN.md` | RECORD | 三布局并行（~1.5h）：**xip 2,458.2M / sdram-heap 2,134.6M / sdram 1,916.7M cycles**（IPC 0.0271/0.0312/0.0348），全 PASS+等式 OK；`.text` 搬 SDRAM 净收益 −10.2%；**长跑 sdram、短跑 sdram-heap** | ✅ |

**P-H 教学项（#12/#13/#19）**

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B3_STAGE8_PH_PROMPT.md` | PROMPT | P-H 任务入口（#12/#13/#19 做法/验收/坑） | 📦 |
| `B3_STAGE8_PH_PLAN.md` | PLAN | P-H 计划（H1→H2→H3、独立目录、样本与参数；用户已确认） | ✅（计划） |
| `B3_STAGE8_PH.md` | RECORD | P-H 结果：**H1** `trace_locality.py`（F 1.73M 访问仅 286 行/18KB、R 85%=UART LSR 单地址、W 68KB≫4KB dcache；§H1.5 F−retire=bubble+2 对账）；**H2** `trace_compress.py`（dseg 6.41×、**dseg+xz 716.7×**）；**H3** `am-kernels/tests/locality/` 三例（**每元素缺失 0.109/0.484/0.965**、cycles 6.26M/24.73M/57.51M） | ✅ |

附件（P-H）：
- H1：`B3_STAGE8_PH_H1_locality_all.png`、`B3_STAGE8_PH_H1_summary_all.md`、`B3_STAGE8_PH_H1_locality_cacheable.png`、`B3_STAGE8_PH_H1_summary_cacheable.md`
- H2：`B3_STAGE8_PH_H2_compress_summary.md`
- H3：`B3_STAGE8_PH_H3_loc_array-sum.md`、`B3_STAGE8_PH_H3_loc_array-sum.png`、`B3_STAGE8_PH_H3_loc_list-alloc.md`、`B3_STAGE8_PH_H3_loc_list-alloc.png`、`B3_STAGE8_PH_H3_loc_list-chase.md`、`B3_STAGE8_PH_H3_loc_list-chase.png`

## 4. ONScripter 移植（PA4.5 选做）✅

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `ONSCRIPTER_PROMPT_V2.md` | PROMPT | 任务入口（目标/已固化事实/约束/执行顺序） | 📦 |
| `ONSCRIPTER_FIX_PLAN.md` | PLAN | 显示修复整体计划：阶段 A–D（误判修正→双侧对照→根因定性→官方化修复） | ✅ |
| `ONSCRIPTER_NAVY_NATIVE_DEBUG.md` | RECORD | navy-native 透明窗口调试**结案**：根因=native.cpp 上屏偏离官方框架；§8 调试技巧、§9 定位方法/逻辑锁 | ✅ |
| `ONSCRIPTER_RISCV_NEMU_PORT.md` | RECORD | riscv64(NEMU) 移植（验证通过）：navy 编译打通、内核三修复、syncconfig 坑、NPC 内嵌 ramdisk | ✅ |

## 5. 环境与工具

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `YSYXSOC_REGEN_SETUP.md` | RECORD | ysyxSoC Chisel 重生成链：mill 0.11.12/firtool 1.51.0/JDK17、学号 BlackBox 定制点、apb_delayer 固化；重生成后 PERF 与基线逐位一致（P-D 前置） | ✅ |

## 6. 附件清单（数据表/图）

| 附件 | 归属 | 说明 |
|---|---|---|
| `B3_CTR_TRACE.png` / `B3_CTR_TRACE_summary.md` | `B3_CTR_TRACE.md` | 计数器 trace 四联图 / 区间表 |
| `B3_STAGE8_PH_H1_*.png` / `*_summary_*.md`（2+2） | `B3_STAGE8_PH.md` §H1 | 局部性四联图 + 汇总表（全量 / 仅可缓存区） |
| `B3_STAGE8_PH_H2_compress_summary.md` | `B3_STAGE8_PH.md` §H2 | 15 行压缩对比全表 |
| `B3_STAGE8_PH_H3_loc_array-sum.md`、`B3_STAGE8_PH_H3_loc_array-sum.png`、`B3_STAGE8_PH_H3_loc_list-alloc.md`、`B3_STAGE8_PH_H3_loc_list-alloc.png`、`B3_STAGE8_PH_H3_loc_list-chase.md`、`B3_STAGE8_PH_H3_loc_list-chase.png` | `B3_STAGE8_PH.md` §H3 | 三例局部性工具输出与曲线 |

## 7. 权威 / 快照 / 被取代

| 主题 | 权威文档 | 快照/被取代 | 说明 |
|---|---|---|---|
| P-D SDRAM AXI 调试 | `B3_STAGE8_PD_DEBUG.md` | `B3_STAGE8_PD_HANDOFF.md` 📦 | HANDOFF §3-A"写拍重复"已被 §7.1 证伪；调试设施/复现命令仍可参考 |
| P-E 对账与 DSE | `B3_STAGE8_PE_CACHESIM_DIFF.md`、`B3_STAGE8_PE_DSE.md`、`B3_STAGE8_PE_E4_SAMPLE.md` | `B3_STAGE8_PE_PLAN.md`、`B3_STAGE8_PE_E4_PLAN.md`（计划类） | E4 按用户裁决暂停（E4.1 参数化已入库） |
| P-C | `B3_STAGE8_PC_AMAT.md` + `B3_STAGE8_PC_AMAT_LAYOUT.md` | `B3_STAGE8_PC_PD_PLAN.md`（计划） | PC_AMAT_LAYOUT §6 r=4.25 与 `B3_STAGE8_PB_FMAX.md` §6 同源 |
| P-H | `B3_STAGE8_PH.md` | `B3_STAGE8_PH_PROMPT.md`、`B3_STAGE8_PH_PLAN.md` | 计划中样本（mb_pe）与编码方案已被结果（mb_pe2/dseg）取代，结果为准 |
| 任务入口 PROMPT（阶段7/PD/PH、STAGE_F/I/J） | 各自的结果记录 / `DEBUG_WORKFLOW.md` | 对应 PROMPT 📦 | PROMPT 仅供任务背景，状态看结果 |
| 阶段8 面积/频率数据 | `B3_STAGE8_AREA_N45.md` / `B3_STAGE8_PA_A1.md` / `B3_STAGE8_PB_FMAX.md` | `../knowledge/SYNTHESIS_STA_NPC.md`（入门+速查） | 速查数字以过程记录为准（A1 后 118,805.71μm²/426MHz） |
| 阶段2/3 性能结论 | `B3_STAGE7_RECALIB_PERF.md`、`B3_STAGE8_PE_CACHESIM_DIFF.md` | `../knowledge/B3_STAGE2_PERF_ANALYSIS.md` ⚠️、`../knowledge/B3_CACHESIM_ANALYSIS.md` ⚠️ | 旧数字/旧成本模型已被校准口径取代；计数器手册与工具说明仍有效 |
