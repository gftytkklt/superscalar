# records/process —— 日志型归档（阶段实施/调试过程/任务提示词）

> **按项目推进顺序组织**：访存体系（阶段1–3）→ RT-Thread/SDRAM/外设（阶段F–K）→ B3 性能优化
> （阶段1–8）→ ONScripter（PA4.5 选做）→ 环境 → **Linux 双端启动（LINUX_PLAN M0~，进行中）**。
> 每组内按「任务入口（PROMPT/TASKS）→ 计划（PLAN）→ 结果（RECORD）」排列，附件（图/表）列在所属记录行下。
> 经验性文档见 [`../knowledge/README.md`](../knowledge/README.md)；入口总览见
> [`../../docs/PROJECT_OVERVIEW.md`](../../docs/PROJECT_OVERVIEW.md)。
> 重复/取代关系见文末 §7「权威 / 快照 / 被取代」。

**状态图例**：✅ 结案/完成 ｜ 🔶 进行中/待确认 ｜ ⏸ 用户裁决暂停 ｜ 📦 历史快照（保留过程价值，结论以权威文档为准） ｜ ⚠️ 部分结论过期（见 §7）

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

### 3.4 B4 流水线处理器（✅ 已完成，2026-09-22 结档）

> 总计划（活跃区）：`../../docs/B4_PLAN.md`（讲义 36 项 → 现状/待做/分阶段计划）；
> **架构优化台账（活跃区）**：`../../docs/ARCH_OPT_BACKLOG.md` + `../../docs/arch_opt/*`
> （所有优化候选/收益/状态/决策的统一入口，落地前须数据采样）。
> 进度：**Q1 ✅ 量化 / Q2 ✅ 计数器 / Q3 ✅ branchsim / Q4 ✅ fence.i 反例 / Q5 ✅ 流水线形式化（depth 20 PASS，~377s） /
> Q6 ✅（OPT-19、真实 RTL 缺陷×2：JALR LSB / `dnpc_reg_valid` 握手优先级） / Q7 ✅ 完成
> （计划 `../../docs/B4_Q7_PLAN.md`；Q7-A ✅ 写缺失拆分探针（收益集中填充侧 1,317 vs 回写 927）；
> Q7-B OPT-11 功能全绿但 locality 回归 → **否决并回退**（保留 `lduse_fwd.S`）；
> Q7-C OPT-05 **暂缓**（字节掩码元数据实测 +26% 面积，面积/收益比不足）；
> Q7-D 形式化深探 **depth 24 限时 1h 未判定**（判定上限 depth 20 PASS）；Q7-E ✅ 结档）→ **B4 完成**。
>
> **B4 后扩展：riscv-tests 接入**（与 cpu-tests 同模式：nemu/npc 双目标链接 + `ebreak`+a0 结束约定）——
> `RISCV_TESTS_R3.md` 首轮 NPC 63/3/1、NEMU 55/3/8/1；**N-1 修复 NEMU REF**（`NEMU_REF_FIXES.md`：
> `mulh/mulhsu/mulhu` 高 64 位 + div/rem 全 8 条除零/溢出/W 符号扩展）→ NEMU 也 **66 PASS / 0 FAIL /
> 1 SKIP / 0 UNDET**，mul/div 用例可 **DIFF=1** 交叉验证；
> **R-5 修复完成**（`B4_R5_RISCV_FIXES.md`）：`divuw/remuw` ✅（`3ecba24`）+ `jalr rd=rs1` ✅（B4-R5b：
> `npc_e` 握手拍保留"不同的新目标"——修重定向目标丢失→同地址重复请求；不触碰握手/气泡语义）；
> 最新 NPC 全套 **66 PASS / 0 FAIL / 1 SKIP(ma_data)** + 全回归逐位（formal depth 20 PASS）；
> 脚本 `riscv_tests_{build,run}.sh`、`riscv_tests_patch_env.py`。

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `B4_QUANT_EVAL.md` | RECORD | B4-Q1 量化：**fetch/retire 双指针对齐**精确重建动态序列（bubble=380,591、类别与 PERF 逐位一致；澄清 `other`=未跳转分支）+ 四项理想收益：理想流水线 **1.285×**、转发 **1.069×**、控制冒险 **1.021×**、jal/jalr **1.0011×**、icache 流水化 ≈1.00×（上界 1.236×） | ✅ |
| `B4_Q2_COUNTERS.md` | RECORD | B4-Q2 计数器：新增 `lduse_cyc/ev`、`mdu_ev`、分支细分（taken/ntaken/jal/jalr，与 Q1 逐位一致）；**修正 `mul_cyc` 旧口径恒 0（漏计 M/D）→ 87,405 cyc/0.48%T**；div/mul-longlong 定向验证（≈64/32 拍每条）；基线逐位一致 | ✅ |
| `B4_Q3_BRANCHSIM.md` | RECORD | B4-Q3 branchsim：条件 382,591（taken 359,844/not 22,747）+ jal 8,687 + jalr 12,058；**方向预测上限 1.0200×，BTFN 1.0193×（96.6%）、2-bit PHT 1.0197×**；落地须 BTB（IF 生效）→ 留档、不优先落地 | ✅ |
| `B4_Q4_FENCEI.md` | RECORD | B4-Q4 fence.i 反例：新增 `tests/fencei_pipeline.S`（SMC 自修改；有 fence.i PASS 0x11/0x22/0x5A5A@683cyc；**禁用后 10× 超时 FAIL**）；**修复 harness "超时误报 PASS"**（暴露 4 个测试长期死锁）与 tb 写握手（AW/W 可同拍）；RTL 隐患 `axiburst2xxx` 写握手登记台账 OPT-19 | ✅ |
| `B4_Q5_FORMAL.md` | RECORD | B4-Q5 流水线形式化：`formal/pipeline.sby`+`props_pipeline.sv`（REF=受限子集单周期执行器，探针注入避开 yosys 层次引用限制）**BMC depth 20 PASS（~377s，结档见 Q6 记录）**，`make formal` 四件全 PASS；过程修复 4 个 REF/harness 保真度问题（层次引用/复位取指/非法编码放行/SRA 退化） | ✅ |
| `B4_Q6_OPT19_AXIBURST.md` | RECORD | B4-Q6/OPT-19：`axiburst2xxx` 写握手 **AW/W 解耦修复**（与 dcache 双 FSM/`axi64to32` 范式一致）；harness 恢复严格从端后 **11/11 微测试（当时；现 13 例全绿）+ assert 11/11（当时）+ formal 四件 + `make perf` 逐位 + sdram-heap 15,329,912 全绿** | ✅ |
| `B4_Q6_OPT05_STORE.md` | RECORD | B4-Q6/OPT-05 采样：Python dcache 模型与 RTL **逐项一致**（rd 32,894/1,090、wr 18,075/3,307）；**97.1% 写缺失驱逐前写满整行（3,212/3,307）**；免填充上界 **≈4.2M（23%T）→ ≈1.30×**（推荐 write-validate）；含候选 A/B/C 与前置拆分实验 | ✅ 采样 |
| `B4_Q6_JALR_LSB.md` | RECORD | B4-Q6 形式化反例调试**结档**：修复 4 处 harness 假反例（电平 valid/`O_pc=dnpc` 索引/逐拍自由指令/请求地址供给）+ **2 个真实 RTL 缺陷**：① `dnpc_reg` 未清 JALR 目标 bit0；② `dnpc_reg_valid` 握手优先级（跳转目标重复取指→同一指令执行两次，depth≥20 反例根因）；**depth 20 PASS（~377s）**；全回归逐位（微测试/assert 12/12（当时；现 13 例）、formal 四件、`make perf` 18,318,000/1,352,016、sdram-heap 15,329,912），零性能损失 | ✅ |
| `B4_Q6_PROMPT.md` | PROMPT | B4-Q6 续作任务入口（历史，已完成：depth≥20 反例定位与修复） | 📦 |
| `B4_Q7_OPT05_SPLIT.md` | RECORD | B4-Q7/Q7-A 写缺失 episode 拆分采样（纯 verif 打印 1 行）：psram fill_avg=1,317 / wb_avg=927（58.7%/41.3%），**收益集中在填充侧**，write-validate 上界维持 ≈1.30×；`make perf` 逐位一致（18,318,000/1,352,016） | ✅ |
| `B4_Q7_OPT05_DESIGN.md` | RECORD | B4-Q7/Q7-C OPT-05 设计评估：write-validate 必需按字节有效性元数据；面积探针（`sta/probe/probe_validmask.v`）**+31.2Kμm²（+26% 全芯片）**、阵列 f_max 776MHz；A1/A4/A2 方案对比 → **用户裁决暂缓（A3）**，未动 RTL | ⏸ |
| `B4_Q7_OPT11_LDUSE.md` | RECORD | B4-Q7/Q7-B OPT-11：MEM 拍 load 数据前递 + "数据未回才停"（定向测试抓到"直接去 MEM 项"的气泡漏洞）；功能全绿（微/assert 13/13、formal 四件、depth 20 PASS、difftest），裸核 −1 拍/事件；但 `make perf` −0.16%、**locality +2.3~3.5% 回归**（UART 轮询 + APB 时延模型）→ **否决并回退**（测试 `lduse_fwd.S` 保留） | ❌ |
| `B4_Q7_CLOSE.md` | RECORD | B4-Q7 收尾与 **B4 结档**：36 项最终状态（✅19/➖10/❌6/🔶1，无遗留必做）、结档回归证据（13/13、assert 13/13、formal 四件、perf 18,318,000/1,352,016、sdram-heap 15,329,912）、**形式化判定上限 depth 20 PASS / depth 24 限时 1h 未判定**、决策与遗留 | ✅ |
| `B4_Q7_PROMPT.md` | PROMPT | B4-Q7 续作任务入口（历史，已完成）：OPT-05 决策落地 / OPT-11 / 形式化深探 / B4 结档；结果见 Q7 各 RECORD | 📦 |
| `RISCV_TESTS_R3.md` | RECORD | riscv-tests 接入（R-1~R-3，与 cpu-tests 双目标模式一致）：双目标链接（NPC flash/SRAM vs NEMU 0x80000000）、env 适配（ebreak+a0 / CSR 子集 / M 模式 / 数据搬运）、死锁三层防护；**NPC 63 PASS/3 FAIL/1 SKIP**；NEMU REF 自身 mulh/div 缺陷留档 | ✅ 首轮 |
| `B4_R5_RISCV_FIXES.md` | RECORD | R-5 **完成**：**divuw/remuw ✅**（符号扩展 1 行，`3ecba24`）；**jalr rd=rs1 ✅**（B4-R5b：波形证据链修正为"Q6 握手优先在消费旧 pending 的同拍丢掉新跳转目标 → 同地址重复请求 → link 响应被二次消费"；修复 `npc_e` 为 pending 语义规范式 `valid' = load ∨ (valid ∧ ¬accept)`，load 只认"与被接受值不同的新目标"，兼容 Q6、不动握手/气泡语义）；riscv-tests **66 PASS/0 FAIL/1 SKIP**、微/assert 13/13、formal 四件 + depth 20 PASS（442s）、perf 18,318,000/1,352,016、sdram-heap 15,329,912 逐位；含远目标行边界定向控制实验（修前 BAD/修后 GOOD） | ✅ |
| `B4_R5B_PROMPT.md` | PROMPT | R-5b 续作任务入口（历史，已完成：`npc_e` 新目标保留修复 + 全回归；结果见 `B4_R5_RISCV_FIXES.md` §2） | 📦 |
| `NEMU_REF_FIX_PLAN.md` | PLAN | N-1 计划：NEMU REF 语义修复（N-1 mulh 三例 / N-2 div·rem 八例 / N-3 REF 变更后交叉验证 / N-4 留档；Spike 未启用） | 📦 |
| `NEMU_REF_FIXES.md` | RECORD | **NEMU REF 语义修复结档**：根因（64 位乘后才拓宽、宿主除法除零/INT_MIN÷-1 SIGFPE）+ 修复（128 位显式提升 + 8 个除零/溢出 helper）；**NEMU 66/0/1/0**、DIFF=1 定向 11 例 0 mismatch、cpu-tests/sdram-heap 无回归；含 REF `.so` 构建配置要点（SHARE 配置、DEVICE 关闭、`-pie` 冲突） | ✅ |
| `RTL_STD_MODEL_PROMPT.md` | PROMPT | RTL 标准模型化任务入口（**已完成**）：标准范式 P1~P5 + 候选清单 + 阶段/验收/停点；全流程落地见 `../knowledge/CPU_STD_MODELS.md` 与 `RTL_STD_MODELS_FINAL.md` | ✅ |
| `RTL_STD_MODELS_S1.md` | RECORD | **S1 结档：dcache 写通道 B 单一 ack/pend（P3）**——`b_ack/b_pend/wr_issue` 单点化 + 12 处观察点派生；断言走 bind 监视器（非侵入）；等价论证不依赖 `bready≡1`（协议一般性 + 当前配置逐位等价）；全回归绿、perf 18,318,000/1,352,016 与 sdram-heap 15,329,912 逐位、riscv-tests 双端 66/0/1、formal 四件 + depth 20 PASS | ✅ |
| `RTL_STD_MODELS_S2.md` | RECORD | **S2 结档：pc 取指槽 P1 规范式**——`slot_valid/inst_slot` 统一 `valid'=load∨(valid∧¬accept)`、数据与 valid 同条件；槽满覆盖隐患改"保持+断言"，icache 单次交付/`slot⇒IF_valid` 契约断言化（`assert/pc_fetch_check.sv`）；全回归绿、perf/sdram-heap 逐位、riscv-tests 双端 66/0/1、formal 四件 + depth 20 PASS | ✅ |
| `RTL_STD_MODELS_S3.md` | RECORD | **S3 结档（v2）：mul/div 数据+valid 对拍（零时延）**——div 保持"迭代直出"，接收保持由既有 `gpr_alu` 捕获寄存器保证（v1 模块级寄存器与后级冗余，按用户评审回退）；mul 空闲 hold 门控（呈现拍不变）；断言 3 监视器（start-while-busy/done 单拍/捕获==呈现）；**回归口径 v2：去 NEMU 端、常规 formal=depth 12，depth 20 仅疑点/收尾**；全绿、`mul_cyc=87,405` 不变、perf/sdram-heap 逐位、NPC 端 66/0/1 | ✅ |
| `RTL_STD_MODELS_S4.md` | RECORD | **S4 结档：冒险/前递 match 五要素单点化**——stall_unit 增 wen 输入、match=读rsX(≠0)∧rs==rd∧rd≠0∧wen 单点表达式（decoder/forward_unit 零改动，forward &wen 幂等）；等价论证含 perf 探针/formal 探针消费者核查；断言 18 条（x0 不匹配/match⇒valid/完备性/前递优先级，`assert/hazard_forward_check.sv`）；全绿、perf 停顿计数逐位、perf/sdram-heap 逐位、NPC 端 66/0/1 | ✅ |
| `RTL_STD_MODELS_S5.md` | RECORD | **S5 结档（v2.1）：slave_crossbar owner 释放点 ready 门**——v1 改握手点置位致 riscv-tests 14 UNDET；根因（v2.1 更正）=单拍握手（valid 一拍+组合 ready 同窗）对 posedge 采样不可见，**非伙伴违规**（AXI4ToAPB.scala s_wait_rready_bready 保持到 fire，"单拍 rvalid"系 VCD code 复用误读已收回）；v2 回退置位、保留写释放 B 握手 ready 门；断言 7 条；全绿恢复 66/0/1、perf/sdram-heap 逐位 | ✅ |
| `RTL_STD_MODELS_S6.md` | RECORD | **S6 结档：CSR 仲裁/中断提交纪律断言**——csr 三事件（wen/intr_wr/mret_wr）同拍互斥 3 条 + intr 提交次拍 MIE==0（"恰一次消费"的 MIE 门控机制钉死）；mtip 采样口径/无 pending 清除端注释化；RTL 行为零改动；全绿 13/13、formal 四件、NPC 端 66/0/1、perf/sdram-heap 逐位 | ✅ |
| `RTL_STD_MODELS_B1.md` | RECORD | **B1 结档：四级流水寄存器控制模板化（P1 slice）**——新增 pipe_ctrl_slice 模板（valid'=load∨(valid∧¬accept)），四级 out_ready 原样传入、握手位留级内；模板首版丢反压保持项致 6 停顿类用例挂死当场抓获（教训入档）；EX_MEM 复合语义 3 条 SVA（首版误报=气泡陈旧载荷改写 wstatus 良性形态，已限定）；全绿 13/13 ×3、formal 四件、NPC 端 66/0/1、perf/sdram-heap 逐位；STA apples-to-apples：面积 +0.19%、f_max 429.9→452.1MHz 无回归 | ✅ |
| `RTL_STD_MODELS_S7.md` | RECORD | **S7 结档：C 批归档**——C1 随 B1-3 模板收敛；C2 axi_crossbar 4 条仲裁纪律 SVA（grant 互斥/R 路由互斥/事务保持到 last×2）；C3 axiburst2xxx 归档不动；跨拍断言组合信号须同沿延迟采样（第 3 次同构修正）；RTL 零改动，assert/formal/微测试全绿 | ✅ |
| `RTL_STD_MODELS_FINAL.md` | RECORD | **RTL 标准模型化任务总收尾**——S0~S7+B1 全部完成（8 commit）；最终基线：微/assert 13/13（新增 8 监视器 48 条断言，合计 12 文件 57 条）、formal 四件、NPC 端 66/0/1、perf/sdram-heap 逐位、STA 无回归；六条可复用结论（等价性铁律/检查非侵入/范式让位于承载性行为/逐格真值表/跨拍采样纪律/数据-valid 同条件结构保证）+ 五项留档不动清单 | ✅ |
| `OPT08_SAMPLE.md` | RECORD | **OPT-08 采样+试做证伪结档**：W1/W2/M3/M6 结构证据→双口径基线（r=3.5/4.5）→M1/M2 试做被 sdram TB 证伪（W1=桥 2 拍/写间隔拍、W2=采样/DQ 窗口最小对齐，均非位扩展可消除开销）→❌ 否决回退；附带产出 PERF_R45 旋钮（r=4.5 现行口径，EQUATION OK 验证）；SDRAM 控制器已恢复原实现 TB 7/7 | ✅ |
| `RISCV_TESTS_RESULT_npc.md` | RESULT | riscv-tests **NPC 自校验结果表**（runner 自动生成/覆盖）：**66 PASS / 0 FAIL / 1 SKIP(ma_data) / 0 TIMEOUT**（R-5b 后，含逐用例 cycles） | ✅ 最新 |
| `RISCV_TESTS_RESULT_nemu.md` | RESULT | riscv-tests **NEMU 原生结果表**（runner 自动生成）：**66 PASS / 0 FAIL / 1 SKIP / 0 UNDET**（N-1 修复 REF 后）；历史 REF 缺陷见 `NEMU_REF_FIXES.md` | ✅ 最新 |

附件：`B4_QUANT_RAW.md`、`B4_Q3_RAW.md`、`B4_Q6_OPT05_store_analysis.md`

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
| riscv-tests 状态 | `B4_R5_RISCV_FIXES.md`（R-5 结论）+ `RISCV_TESTS_RESULT_npc.md`（最新结果表） | `RISCV_TESTS_R3.md`（首轮 63/3/1 快照）、`RISCV_TESTS_RESULT_nemu.md`（首轮含 REF 缺陷） | 结果表由 `riscv_tests_run.sh` 自动覆盖；首轮记录留档 |
| NEMU REF 语义（mul/div） | `NEMU_REF_FIXES.md`（修复后，DIFF=1 可用） | `RISCV_TESTS_RESULT_nemu.md` 首轮（55/3/8/1） | 其余 REF 限制（6 CSR、无 `fence`、`ma_data`）仍有效 |

## 8. Linux 双端启动（LINUX_PLAN M0~）🔧

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| `LINUX_M0_SPEC.md` | SPEC | **M0 规格冻结 v1.0（2026-09-27 结档）**：特性矩阵（RV64IMA+zicsr/zifencei，排除 F/D/C 三重机制）、版本选型、DTB 草案（UART 字节步长/CLINT mtime 每拍+1 实测核对）、flash 布局与**实测回填**（kernel Image 1.7MB + OpenSBI 265KB + busybox 314KB ≈ 2.3MB≪16MB）；§8 七项拍板全按推荐 + §8.1 扩展性说明（键盘两路线）；D-M0-3 实测切 musl（lp64d/lp64 ABI 互斥）；§11 构建配方固化（含 4 个已踩平坑）；产物在 `~/linux-m0/`；M1-P4 新 Image 容量以 §13 附记回填，不改 M0 基线 | ✅ v1.0 冻结，附 P4 回填 |
| `LINUX_M1_NEMU.md` | PROCESS | M1-P1～P9：NEMU native/REF平台边界、DTS/initramfs/kernel、CSR/特权/A/Sv39、中断/MTIMER/UART、Linux交互首启、REF隔离构建与旧PC-GPR对拍；含阶段提交回执及M1 Handoff | ✅ M1 Completed（2026-10-10）：P8已提交7efb232；P9已获用户确认并提交14179a3，UI/UM对拍66 PASS/1既有SKIP、cpu-tests7及两注入负例通过；独立总体验收及资产哈希核对通过。ma_data留OPT-17/M3，priv/CSR对拍留M6；M1交接时M2未开始，当前M2规划见下行。复现/回滚见 `linux/boot/README.md` |
| [`LINUX_M2_AMO.md`](LINUX_M2_AMO.md) | PROCESS | M2 NPC A扩展：规划审查、后续人工RTL/验证与AI设计审查证据；范围见LINUX_M2_PLAN | 🔶 2026-10-11计划v0.1已落盘自审待用户确认，P1未Start；无RTL修改或本轮仿真结果 |

## 独立任务：系统栈代码正确性审阅（CCR）

2026-10-17后续方案已确定：[执行差异与首批范围](code_correctness_review/REPAIR_AND_REGRESSION.md#repair-readiness-20261017)、[用户确认回执](code_correctness_review/REPAIR_AND_REGRESSION.md#repair-plan-approval-20261017)。首批仅CCR-F0015，范围/host局部验收已确认；用户最新“提交后继续实施”授权提交现有准备文档后实施该单项修复。本文档提交时修复尚未开始；本批结束即停，不改变CCR收尾或M2状态。

CRP历史：[首批CCR-F0015修复与局部回归](code_correctness_review/crp-f0015/README.md)。准备文档已提交2f11b08；首批Completed；用户已确认本次收尾并授权按F0015独立提交。生产一行PC比较；原版43例36通过/7预期失败，修复后43/43通过，4项判据故障正确拒绝。仅host局部闭环，完整Spike/NPC/guest未运行；其他118项仍未解决，本批结束停下，不推进M2。


CRP最新：[CCR-F0052最小判据修复](code_correctness_review/crp-f0052/README.md)已确认闭合：am-kernels生产提交c1ba0bb；F0015根提交f5825fd。两批隔离局部证据保持，未宣称真实CPU/guest回归通过。[后续功能修复回归要求](code_correctness_review/crp-f0052/README.md#product-regression-contract-20261017)：按修改模块及依赖影响选择对应回归（CPU-tests全集、RT到msh、nanos三前台切换及hello），不是每批全部执行；无GUI不豁免受影响功能的真实程序回归。用户确认保留历史嵌套差异，仅清根及本轮修改。

| 文档 | 类型 | 主题/要点 | 状态 |
|---|---|---|---|
| [CODE_CORRECTNESS_REVIEW_PLANNING.md](CODE_CORRECTNESS_REVIEW_PLANNING.md) | PROCESS | CCR-P0最小摸底、计划/范围S01–S05与批准/提交回执 | ✅ P0历史完成；47b6c78已提交；当前阶段见P10行 |
| [code_correctness_review/P1.md](code_correctness_review/P1.md) | PROCESS | CCR-P1身份/配置/契约/覆盖冻结；[COVERAGE](code_correctness_review/COVERAGE.md)、[CONTRACTS](code_correctness_review/CONTRACTS.md)、[CONFIGURATIONS](code_correctness_review/CONFIGURATIONS.md)、[INTERFACES](code_correctness_review/INTERFACES.md)、[AVAILABILITY](code_correctness_review/AVAILABILITY.md)、[GENERATORS](code_correctness_review/GENERATORS.md)及JSON/复现证据 | ✅ P1历史基线已确认/提交0d65d72；当前审阅状态见P10行 |
| [code_correctness_review/SCOPE_RV64.md](code_correctness_review/SCOPE_RV64.md) | PROCESS | CCR S06：用户批准仅RV64；非RV64实现获准排除，共享/宿主支撑保留，原P1证据留存 | ✅ S06已批准；P1已确认/提交，当前状态见P10行 |
| [code_correctness_review/P1_FINAL_GATE.md](code_correctness_review/P1_FINAL_GATE.md) | PROCESS | P1一致性检查及双平台澄清后的复验；FG-01/02已闭合，原NotPassed记录保留 | ✅ P1历史Final Gate通过，已确认/提交0d65d72；当前阶段见P7 |
| [code_correctness_review/BUILD_PATHS.md](code_correctness_review/BUILD_PATHS.md) | PROCESS | RV64 NEMU/NPC双平台run/update/编译/链接/ramdisk及NEMU→Spike/NPC→NEMU角色；build_profiles.json含6场景/31来源hash | ✅ P1入口冻结，动态NotRun；不是代码正确性结论 |
| [code_correctness_review/P2.md](code_correctness_review/P2.md) | PROCESS | CCR-P2 RV64 CPU/类型、ISA/异常/CSR/Sv39逐路径审阅与Final Gate；[证据](code_correctness_review/p2/README.md) | ✅ Completed、用户确认并提交`9918989`；29入口，8项Confirmed（H1/M5/L2） |
| [code_correctness_review/P3.md](code_correctness_review/P3.md) | PROCESS | CCR-P3 RV64运行支撑、设备/monitor/REF/Spike golden/工具静态审阅与Final Gate；[覆盖](code_correctness_review/COVERAGE.md)、[问题](code_correctness_review/FINDINGS.md)、[证据](code_correctness_review/p3/README.md) | ✅ Completed并已确认/提交；新增14项Confirmed（H1/M12/L1）；后续P4见下行 |
| [code_correctness_review/P4.md](code_correctness_review/P4.md) | PROCESS | CCR-P4 RV64双平台启动/链接/Context/VME/MPE审阅；[证据](code_correctness_review/p4/README.md)、[Final Gate](code_correctness_review/p4/validation.json) | ✅ Completed；120文件/78条件；新增5 Confirmed/2 Robustness/3 ContractQuestion；结果已确认/提交a419cea；P5交付见下行 |
| [code_correctness_review/P5.md](code_correctness_review/P5.md) | PROCESS | CCR-P5双平台IOE/klib/辅助运行时/AM BSP；[AM_RUNTIME](code_correctness_review/AM_RUNTIME.md)、[证据](code_correctness_review/p5/README.md)、[Final Gate](code_correctness_review/p5/validation.json) | ✅ Completed；2,537文件/1,213条件；新增19 Confirmed/3 Robustness/2 CQ，累计56项；结果已确认/提交632b843；P6交付见下行 |
| [code_correctness_review/P6.md](code_correctness_review/P6.md) | PROCESS | CCR-P6 OS/loader/syscall/fs/调度/VME；[两链](code_correctness_review/CROSS_LAYER_P6.md)、[OS矩阵](code_correctness_review/OS_RUNTIME.md)、[证据](code_correctness_review/p6/README.md) | ✅ Completed；70文件/91条件，19新问题；累计75；已确认/提交bdc02a3；历史P6证据 |
| [code_correctness_review/P7.md](code_correctness_review/P7.md) | PROCESS | CCR-P7 RV64启动/libos/libc/ABI/构建；[运行时](code_correctness_review/USER_RUNTIME.md)、[ABI](code_correctness_review/SYSCALL_ABI.md)、[第三方](code_correctness_review/THIRD_PARTY_P7.md)、[证据](code_correctness_review/p7/README.md) | ✅ Completed；2624保留文件/8322条件导航，65项S06排除，14新问题，累计89；P7已确认/提交679cc16；当前见P8行 |
| [code_correctness_review/P8.md](code_correctness_review/P8.md) | PROCESS | CCR-P8 [NDL/SDL](code_correctness_review/SERVICE_RUNTIME.md)、[媒体](code_correctness_review/MEDIA_RUNTIME.md)、[应用调用](code_correctness_review/APP_OS_CALLS.md)、[逐文件边界](code_correctness_review/BOUNDARIES_P8.md)、[证据](code_correctness_review/p8/README.md) | ⏸ Partial / Final Gate未通过；2项保留缺源；26新问题累计115；P8 Partial已提交5f88749；用户暂缓两缺源并豁免P9前置完成门槛 |
| [code_correctness_review/P9.md](code_correctness_review/P9.md) | PROCESS | CCR-P9 L01–L09逐15字段/故障路径；[跨层](code_correctness_review/CROSS_LAYER_P9.md)、[证据](code_correctness_review/p9/README.md) | ✅ Completed（审阅）；4新问题累计119；受控target与host seam验证分开；P9已确认/提交4c25408；最终交付见P10，两缺源仍保留 |
| [code_correctness_review/P10.md](code_correctness_review/P10.md) | PROCESS | CCR-P10 [FINAL_REPORT](code_correctness_review/FINAL_REPORT.md)、[最终问题](code_correctness_review/FINAL_FINDINGS.md)、[覆盖](code_correctness_review/COVERAGE.md)、[接口](code_correctness_review/INTERFACES.md)、[证据](code_correctness_review/EVIDENCE_INDEX.md)、[限制/决策](code_correctness_review/LIMITATIONS_AND_DECISIONS.md)、[修复/回归](code_correctness_review/REPAIR_AND_REGRESSION.md)、[本轮审计](code_correctness_review/p10/README.md) | ✅ Completed，按用户两缺源验收豁免闭合；12663/12665，未解释差集0，119问题未修；已获收尾/提交授权，回执见P10；当前后续优先存量问题修复，未决项按正式Linux M阶段需求落档，停 |

CRP本轮承接：[F0052收尾复核](code_correctness_review/crp-f0052/README.md#handoff-closeout-20261017)；唯一下一任务及门槛见[现有TASK_QUEUE / CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)。根AGENTS.md固化“继续”执行规则，本轮只更新文档，未启动下一项、未commit/push。

CRP本批确认：[用户确认及文档提交授权](code_correctness_review/crp-f0052/README.md#handoff-approval-20261017)已落档；本批三份tracked文档独立提交，实际提交回执见本地REPAIR_AND_REGRESSION及.agent。唯一下一入口仍为上方TASK_QUEUE链接；不启动下一批、不push，ignored资料沿用本地持久化。

2026-10-17 CRP当前：[CCR-F0051失败传播与发布边界分析](code_correctness_review/crp-f0051/README.md)
已按本轮“继续”完成，仅分析/隔离补证，生产修复未开始。make/nm/objcopy失败仍exit0、
复制异常部分发布及缺mk静默省略集成均有原版观察；不是修复或真实guest PASS。
本轮结果确认、发布策略和commit Pending；F0015/F0052与9402822既有提交保持。
唯一后续动作/门槛见[现有CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)，未决时不默认实施，M2不变。

F0051补充：[用户已选A及update语义澄清](code_correctness_review/crp-f0051/README.md#f0051-a-approval-20261017)。
正确性修复保留既有Make入口/流程；RT已有集成update与nanos的ramdisk update各自独立，
不将update增加为RT日常run的必经步骤。未新增动态结果，生产修复和提交仍未开始。

CRP最新：[F0051 A修复及验收](code_correctness_review/crp-f0051/README.md#f0051-implementation-20261017)
Completed，结果确认/commit Pending。仅生产集成脚本修改，Make接口/流程不变；最终13/13定向通过，
真实四应用生成/链接、NPC difftest ON到msh通过，help列出四集成命令；180秒受控停止，
未宣称四应用运行通过。生产脚本仍受Git忽略，原build保持，未commit/push。
后续仅沿[现有CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)，本批结束停止，M2不变。

2026-10-18：[F0051用户确认与提交收尾](code_correctness_review/crp-f0051/README.md#f0051-submit-20261018)。
用户已确认本批报告范围并授权提交；上一轮已完成技术收尾，本次复用，未重跑13项/真实RT。
生产脚本按授权精确纳入跟踪，原始本地证据及.agent沿用既有持久化；实际提交回执见本地记录。

F0051修复及验证资料实际提交`4ab9f3f04c12f6e09adf2dab2d873626db51a511`；
流程优化见根[AGENTS.md / 每轮执行与提交收尾](../../../../AGENTS.md#每轮执行与提交收尾)：
无真实未决项则直接完成本轮修改/验证后总结；用户示意提交时补齐或复用已有收尾，
避免重复确认、归档和无故重测。当前不push、不启动下一项，实际工作流提交回执见本地记录。


2026-10-18 CRP最新：[CCR-F0085递归失败传播与fsimg发布边界分析](code_correctness_review/crp-f0085/README.md)
Completed，生产修复未开始。20种隔离观察证明两行候选可阻断link/ramdisk并保留旧镜像/header，
失败前部分fsimg仍保留；需裁决允许部分安装残留或整批发布。结果确认/commit Pending，
没有真实nanos guest新结果，未commit/push。后续范围/门槛仅见[唯一CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)，M2不变。


CRP最新：[F0085 A修复及真实nanos回归](code_correctness_review/crp-f0085/README.md#f0085-implementation-20261018)
Completed，修复结果确认/commit Pending。navy Makefile两行；10/10同版定向，完整update/image、108 extent
字节匹配，真实riscv64-nemu的nterm输入响应/nslider翻页/pal继续渲染及后台hello递增通过。
52.32秒后受控SIGTERM非guest正常退出；未commit/push，未测能力不扩写。[唯一入口/门槛](../../../../.agent/TASK_QUEUE.md#crp-next)，M2不变。

F0085用户已明确“提交”，确认已报告范围并授权提交；[收尾范围](code_correctness_review/crp-f0085/README.md#f0085-submit-20261018)
复用现有验收。生产修复/报告/本批忽略规则入库，一次性测试代码与生成证据留本地；新增“测试代码只提交必要部分或不提交”规则落AGENTS，验证要求不减少。实际提交回执随后补充；不push、不启动下一项。

F0085修复实际提交`b7391768dd6c3060f455a4b1ab9470ead37b2134`，已获用户确认；一次性测试代码/生成证据未入库，保留本地。
当前进度见[CURRENT_STATE](../../../../.agent/CURRENT_STATE.md)，完成历史见[CHANGELOG_AGENT](../../../../.agent/CHANGELOG_AGENT.md)，
后续只沿上方唯一CRP Next；原FINAL_FINDINGS保留审阅时截面，不用其历史“未修复”行判断当前修复进度。

2026-10-18 [CRP既往测试精简与批次组织维护](code_correctness_review/repair-maintenance-20261018/README.md)：
用户明确授权定向处理既往冗余测试；16份中保留4份可重复回归源，12份共434行移出索引且本地原字节保留。
四项生产修复及验收保持；合批规则已明确，逐问题验收/共享回归，未来范围只沿[唯一CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)。
本轮维护Completed待确认/commit，无新功能修复或产品测试，未commit/push。

本轮维护已获用户“提交”确认和提交授权，技术收尾复用；[维护报告附记](code_correctness_review/repair-maintenance-20261018/README.md)
及本地closeout/.agent记录实际提交。12份移出材料全部本地保留，4份必要测试继续跟踪；后续仍只沿唯一CRP Next，本次不启动功能修复或push。


<a id="crp-policy-migration-20261018"></a>
2026-10-18 [AGENTS 规则职责维护计划/结果](code_correctness_review/agent-policy-maintenance-20261018/README.md)：
CRP 专用接口、合批、真实回归和测试证据提交规则已迁至[修复执行流程](code_correctness_review/workflow/README.md)，作为现行必读入口；
前文“规则落 AGENTS”的表述保留为历史事实，全局生命周期仍在 AGENTS。
维护 Completed、结果确认/commit Pending；本轮仅文档，无新产品验证或业务阶段推进。
当前检查点见[CURRENT_STATE](../../../../.agent/CURRENT_STATE.md#agent-policy-maintenance-20261018)，后续仍只沿[唯一 CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)。

2026-10-18 本轮规则维护已获用户“提交当前改动，并且继续CRP修复任务”确认及提交授权；技术收尾复用。实际回执见维护目录本地 commit-receipt.json/.agent；另行授权提交后执行唯一 CRP Next 的一个批次，无 push 授权。


<a id="crp-f0037-f0038-20261018"></a>
2026-10-18 [CRP F0037/F0038 klib stdlib修复](code_correctness_review/crp-f0037-f0038/README.md)：
malloc对齐/容量/溢出与失败游标、atoi六类空白/单一符号/INT_MIN已修；原版21/41失败，修复后host sanitizer及RV64 guest均41/41通过。
CPU-tests在记录的32KiB测试兼容符号/-j1配置下36 PASS+1 XFAIL（原始NEMU缺_heap_end链接缺口保留）；RT真实NPC到msh/difftest ON；
nanos真实三前台继续执行+后台hello通过。Completed、结果确认/commit Pending，HEADbc2d2d0；测试代码/原始证据仅本地保留，M2不变。
未来批次只沿[唯一CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)。

2026-10-18 F0037/F0038已获用户“提交”确认及提交授权；复用既有技术收尾，188份证据/生产SHA/patch无漂移。
[提交附记](code_correctness_review/crp-f0037-f0038/README.md#f0037-f0038-submit-20261018)及本地submit-20261018/.agent保存实际回执；不提交一次性测试/生成证据，不启动下一批或push。


<a id="crp-f0033-f0056-20261018"></a>
2026-10-18 [CRP F0033/F0056 klib string修复](code_correctness_review/crp-f0033-f0056/README.md)：
strncpy边界/完整零填充、memmove去VLA且O(1)栈已修；原P5越读/padding/VLA与真实小栈反例重现，
修复后host 13copy+1092move、RV64 13copy+1093move/4KiB栈哨兵及额外边界全部通过。
CPU全集36 PASS+1 XFAIL（已记录测试兼容配置），RT真实NPC到msh/difftest ON，nanos真实三前台+hello及108extent一致通过。
Completed，结果确认Pending、commit Pending；生产仅string.c，测试源/原始证据本地保留；累计已修8/剩余111含5CQ，M2保持。
本批停止，未来范围/门槛只见[唯一CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)。


2026-10-18 F0033/F0056已获用户“提交”确认及提交授权；复用既有技术收尾，252份本地证据/7份文档、生产SHA/patch无漂移。
[提交附记](code_correctness_review/crp-f0033-f0056/README.md#f0033-f0056-submit-20261018)及本地submit-20261018/.agent保存实际回执。
仅最小修复/报告/索引/局部忽略，未提交一次性测试/生成证据，未重跑产品测试；提交后停止，不push或启动下一批。


<a id="crp-f0034-f0035-f0036-20261018"></a>
2026-10-18 [CRP F0034/F0035/F0036 klib整数格式化修复](code_correctness_review/crp-f0034-f0035-f0036/README.md)：
转换属性/变参类型及无符号幅值/内部数字buffer与符号前缀补零已修；原43例30失败，修复后host sanitizer与真实RV64各43/43。
私有helper四radix与P5原反例通过；CPU全集36 PASS+1 XFAIL（既有测试兼容配置）、RT真实NPC msh/difftest ON、nanos三前台+hello及108extent一致通过。
Completed，结果确认Pending、commit Pending；仅stdio.c生产修复，测试源/原始证据本地保留，累计已修11/剩余108含5CQ，M2保持。
本批停止，未来范围/门槛只见[唯一CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)。


2026-10-18 F0034/F0035/F0036已获用户“提交”确认及提交授权；复用既有收尾，239份本地证据/7份文档及生产SHA/patch无漂移。
[提交附记](code_correctness_review/crp-f0034-f0035-f0036/README.md#f0034-f0035-f0036-submit-20261018)及本地submit-20261018/.agent保存实际回执。
仅最小修复/报告/索引/局部忽略；一次性测试/生成证据未入库，未重跑产品测试；提交后停止，不push或启动F0046。


<a id="crp-f0046-f0048-f0050-20261018"></a>
2026-10-18 [CRP自适应修复组F0046/F0048/F0050](code_correctness_review/crp-f0046-f0048-f0050/README.md)：
[流程](code_correctness_review/workflow/README.md#batching)已按本轮授权改为逐项验证/组末确认/同对话续作；[原维护附记](code_correctness_review/agent-policy-maintenance-20261018/README.md#adaptive-groups-20261018)保留规则检查结果。
本组Partial：F0048堆实际长度与F0050 UART错误/能力检查Completed，最终host8/8、NEMU/NPC UART真实guest、RT NPC到msh/difftest ON及实际2MiB分配范围通过。
F0046候选host/NEMU通过，但RT/NPC读mstatus遇MPP差异DIFF ABORT；候选已撤回，保留失败镜像/日志，未修复。不得写整组PASS。
规则/两项修复结果确认Pending、commit Pending；累计已修13/剩余106含5CQ。仅两份生产源码及文档，测试与生成证据本地保存；后续仅见[唯一CRP Next](../../../../.agent/TASK_QUEUE.md#crp-next)，M2保持。

2026-10-18 [F0046阻塞定位补充](code_correctness_review/crp-f0046-f0048-f0050/README.md#mret-diagnosis-20261018)：相同初值及显式共同写入后，mret导致REF清MPP、DUT保留MPP；原运行器14指令精确复现。仅分析，F0046仍撤回阻塞，本批确认/commit门槛不变。

2026-10-18 [F0046 DUT依赖修复与恢复补充](code_correctness_review/crp-f0046-f0048-f0050/README.md#dut-repair-20261018)：按用户明确授权修复MRET/trap MPP状态更新，恢复中断保存/恢复接口；未找到另一个同根因NPC编号。CSR24组合、SoC原反例/8次trap、裸核14/14、CPU36 PASS+1 XFAIL、双平台MIE及最终RT/NPC difftest到msh/精确2MiB堆通过，29项证据核对通过。本组三项均Completed、确认/commit Pending；累计已修14/剩余105含5CQ。原Partial/失败证据保留，不推定完整特权或Linux完成；下一入口仅见TASK_QUEUE。

2026-10-18 用户“提交现有改动后继续CRP修复任务”确认本组及规则维护并授权提交后续作；
[收尾回执](code_correctness_review/crp-f0046-f0048-f0050/README.md#submit-20261018)记录346条证据及7个身份无漂移，复用原验收；实际提交见本地回执/.agent。未push；下一单元仅沿TASK_QUEUE。


<a id="crp-f0049-20261018"></a>
2026-10-18 [CRP F0049 AM应用线程启动数据生命周期](code_correctness_review/crp-f0049/README.md)：前组三项/DUT依赖/规则已按用户指令确认提交e9a71f3后，执行唯一入口本单元。
生成模板改用RT自有启动记录/参数副本和idle cleanup；分配/create/startup失败及正常返回/主动exit/入口前后delete清理通过。
host ASan/UBSan 8/8；真实NPC RT update/run、11生命周期场景、实际生成am_hello参数输出、75分配/75释放live0、difftest ON及msh通过。
本项Completed，确认/commit Pending；累计已修15/剩余104含5CQ。一次性测试/证据本地保存，F0051发布逻辑未变；CPU/nanos不受影响未重跑。未来只沿TASK_QUEUE，M2保持。

2026-10-18 F0049已获用户“提交后继续”确认及提交授权；[收尾回执](code_correctness_review/crp-f0049/README.md#submit-20261018)记录101份证据/源码无漂移并复用既有验收，实际提交见本地回执/.agent。后续按唯一入口执行一个单元，未push。


<a id="crp-f0039-f0040-20261018"></a>
2026-10-18 [CRP F0039 int64修复与F0040契约核对](code_correctness_review/crp-f0039-f0040/README.md)：F0049已按用户“提交后继续”确认提交d9a3d42后执行本单元。
F0039仅三个signed helper无符号幅值/符号/余数恢复；GCC/Clang UBSan与实际RV64各2427 signed+2428 unsigned向量通过，CPU36 PASS+wrong XFAIL；21项最终核对通过。
RT update/image、完整navy update/nanos image成功；65个消费者ELF无修改helper，故不重跑不受影响的RT/nanos运行。
F0040真实RV64重复初始化与FUNC DSO证据已确认，用户选择本轮只分析、待正式需求裁决，生产未修。F0039 Completed，结果确认/commit Pending；累计已修16/剩余103含5CQ。未来只沿TASK_QUEUE，不推进M2。

2026-10-18 用户确认并授权F0039提交及后续连续批次；[回执](code_correctness_review/crp-f0039-f0040/README.md#submit-20261018)保存114份证据/源码无漂移、复用验收及授权边界。实际提交见本地回执/.agent，未push。

2026-10-18 [CRP逐项修复镜像与人工启动guard](code_correctness_review/repair-status/README.md)以原119项和16项已提交报告逐一对齐，计数按行维护；未来顺序仍只沿TASK_QUEUE。用户已授权当前CRP连续验证/留档/提交及开新组，非依赖未决集中汇总，结束冻结人工启动guard；见[授权规则](code_correctness_review/workflow/README.md#continuous-authorization-20261018)。不授权push或其他业务阶段。

2026-10-18 [CRP F0041/F0042/F0053](code_correctness_review/crp-f0041-f0042-f0053/README.md)：GPU写后sync、NPC缺设备CONFIG/UART TX及devscan能力检查；host8/8、双平台实际子测试、RT约161秒msh及nanos八状态通过，17项核对/6种判据负例通过。F0053独立am-kernels提交6dc302a，根提交按连续授权执行；原组合测试宏错误及分项补验证留档，累计已修19/剩余100含5CQ。未来只沿唯一CRP Next。

2026-10-18 [CRP F0045双平台IOE校验](code_correctness_review/crp-f0045/README.md)：124/124 host、双平台各6例真实合法/非法输入、RT约150秒msh及nanos八状态通过，20项核对、14种判据故障拒绝；严格方向兼容性对未启用NEMU-on-AM音频分支的影响留档。Completed，按连续预授权提交，累计20已修/99剩余含5CQ；本轮最后统一冻结人工启动guard。

2026-10-18 CRP连续授权本轮收尾：F0039 b2229ef、新组三项root e83df62/nested6dc302a、F0045 root f4e3c0c均已提交；20已修/99剩余含5CQ。原始证据与.agent本地保存，未push。下次启动先人工决定/豁免[冻结guard](code_correctness_review/repair-status/README.md#manual-start-guard)，具体下一入口仅见TASK_QUEUE。

2026-10-18 [CRP原入口影响核对与兼容修复](code_correctness_review/crp-compatibility-20261018/README.md)：F0044容量分片已修，F0040 ABI/串行/DSO部分修正；host20/20、真实原audio_test/65537B完整SDL数据/串行CPP、RT/nanos image及nanos八状态、28项核对通过。用户追问后撤回NEMU音频MUXDEF删除候选，Kconfig排除AM音频，不再列作实际回归。全部已修21/未修完98含5CQ及F0040Partial；Completed待确认/提交，唯一下一入口见TASK_QUEUE。

2026-10-18 用户确认WR语义后授权兼容性单元提交及下一批。WR为AM写接口而非RW，native共用handler不等于读回受支持；依据/本批收尾见[回执](code_correctness_review/crp-compatibility-20261018/README.md#wr-submit-20261018)，复用199份证据/28项验收，无生产重测。

2026-10-18 [CRP F0010/F0011声卡初始化与欠载填零](code_correctness_review/crp-f0010-f0011/README.md)：前兼容性组已确认提交1603f88；本组host28/28、真实配置→init/legacy原audio_test/超容量/重init/静音及原版哨兵见证、nanos八状态，26项核对/8判据负例通过。只改NEMU音频设备，TARGET_AM分支/AM/COUNT/Make保持；全部已修23/未修完96含5CQ/F0040Partial，本组待确认提交。

2026-10-18 用户指定[一生一芯 ICS-PA 讲义](https://ysyx.oscc.cc/docs/ics-pa/)为实现参考；目录及抽查的 PA1～PA4 子章节正文/代码可读取，引用与课程范围判定规则已记入[CRP 参考资料](code_correctness_review/workflow/README.md#reference-materials)。本次仅登记参考来源，不推进修复批次或改变待决/提交状态。

2026-10-18 [F0010/F0011 PAL启动卡顿补查](code_correctness_review/crp-f0010-f0011/README.md#performance-review-20261018)：按用户要求Reopen，覆盖全音频链、共享修改与真实音频/窗口、AM回退。11有效测量显示旧新均供给不足，未见重开/变频/容量忙等；用户新增退化未闭合，生产无新修改，原组保持Reopened、未提交，不开始下一组。

2026-10-18 [F0010/F0011用户确认闭合及提交](code_correctness_review/crp-f0010-f0011/README.md#closeout-approval-20261018)：用户确认已报告范围和限制，本组重新Completed，F0010/F0011修复及相关记录纳入本次commit；旧199+199项及补查113项证据无漂移，复用已验收测试。PAL供给不足/性能因果与F0043保留风险；提交后停止，F0012/F0013只设Next未Start。

2026-10-18 [CRP F0012/F0013 monitor输入与watchpoint边界](code_correctness_review/crp-f0012-f0013/README.md)：token有界拷贝/空输入、文本长度/完整保存及池耗尽恢复已修；原版6失败/1对照通过，修复host ASan/UBSan 332检查，真实native默认/监视点CLI及真实PC触发37/37、三次内置guest GOOD TRAP，最终13项核对通过。25已修/94未修完含5CQ/F0040Partial，本组Completed待确认/提交；下一入口仅TASK_QUEUE，未推进M2。

2026-10-18 用户“提交，继续”确认F0012/F0013并授权本次提交及下一单元；[确认回执](code_correctness_review/crp-f0012-f0013/README.md#approval-submit-20261018)复用原332/37验收，51条manifest无漂移。


2026-10-18 [CRP F0014 REF整段内存复制边界](code_correctness_review/crp-f0014/README.md)：F0012/F0013已确认实际提交77a9471；本组范围检查/size_t循环/64位入口防高位别名已修。原3反例失败，修复ASan/UBSan3030断言、真实REF77/77、原ABI执行、CPU全集36PASS+1XFAIL、真实RT141.57秒到msh/对拍ON通过；RT ANSI判据误判保留并以日志复核及3负例校正，17项最终核对通过。默认REF已替换、旧产物本地备份；26已修/93未修完含5CQ/F0040Partial，本组Completed待确认/提交，未推进M2。

2026-10-18 用户“提交，继续”确认F0014并授权提交及后续一个单元；[回执](code_correctness_review/crp-f0014/README.md#approval-submit-20261018)复用原验收，146条manifest无漂移。


2026-10-18 [CRP F0018 load失败保留CPU/PMEM](code_correctness_review/crp-f0018/README.md)：前组F0014已确认提交194d2c0；本组暂存读取/IO检查/失败清理已修。原3反例失败，修复ASan/UBSan16场景/124断言、真实128MiB CLI10次失败状态保持/完整恢复及GOOD TRAP，21项判据与14项最终核对通过；LSan环境不支持单列。27已修/92未修完含5CQ/F0040Partial，本组Completed待确认/提交，原raw格式/非全机恢复及额外128MiB临时内存限制保留，未推进M2。

2026-10-18 用户确认F0018并授权提交及独立空间清理；[确认回执](code_correctness_review/crp-f0018/README.md#approval-submit-20261018)复用已报告验收，45条manifest无漂移，不开始后续修复单元。


2026-10-18 [工作区大型临时资产清理](workspace-storage-cleanup-20261018/README.md)：F0018已确认提交37b3195；用户明确要求直接删除大型临时存档，精确删除29份未跟踪文件（Yosys详细日志、.gch缓存、4份归档ramdisk、3份完整raw快照及2份resources.o）。工作区8.12GB→5.08GB，净减少3.05GB；868份受保护文件哈希不变，保留源码/PDK/当前运行产物/核心审查及STA报告。原SHA/删除清单/持久化影响已记录；维护Completed未提交，不Start F0021/M2。

2026-10-18 用户“提交后继续CRP”确认空间维护结果并授权提交说明/索引后恢复F0021；[确认回执](workspace-storage-cleanup-20261018/README.md#approval-submit-20261018)复用原验证，未重复删除。


2026-10-18 [CRP F0021 FTRACE ELF输入边界](code_correctness_review/crp-f0021/README.md)：维护已确认提交485548c；本组修复header/section/symbol/string尺寸与索引/区间检查、关联字符串表及错误清理。原3反例失败，最终ASan/UBSan32场景、8资源控制、真实native39场景及实际call/ret/GOOD TRAP、16项终检通过；仅改monitor.c既有解析路径，约1.5MiB测试资料。28已修/91未修完含5CQ/F0040Partial，本组Completed待确认/提交，不推进M2或扩展ELF能力。

2026-10-18 用户“提交，继续”确认F0021并授权提交及下一单元；[回执](code_correctness_review/crp-f0021/README.md#approval-submit-20261018)复用原32/8/39验收，226条manifest无漂移。

2026-10-18 [CRP F0022 TARGET_AM嵌入镜像边界](code_correctness_review/crp-f0022/README.md)：F0021已确认提交2a96eb3；本组符号/长度/RESET/剩余容量检查及AM动态PMEM静态初始化编译阻塞修正。原2反例失败，ASan/UBSan28/28、真实AM-native6场景、RISC-V内外两层NEMU双GOOD TRAP、默认native构建/guest与判据控制通过。29已修/90未修完含5CQ/F0040Partial，本组Completed待确认提交，不推进M2。

2026-10-18 用户确认F0022并授权提交，同时要求检查所有CRP存档目录的独立构建资产；[提交回执](code_correctness_review/crp-f0022/README.md#approval-submit-20261018)复用原验收，687条manifest无漂移，不开始F0023。

2026-10-18 [CRP存档构建资产逐目录盘点](workspace-storage-cleanup-20261018/README.md#crp-build-audit-20261018)：F0022已确认提交bc7a110；19个任务共206.99MiB，产物约38.21MiB、截图117.75MiB。7个有NEMU/REF副本，只有F0022有隔离NEMU/AM必要源码与build树；18个有编译产物或镜像，F0052无。逐目录内容/路径清单已留档，本次未删除资产，不Start F0023/M2；维护说明未提交。

2026-10-18 [CRP F0023 NEMU trap来源及mscratch栈约定](code_correctness_review/crp-f0023/README.md)：维护说明已确认提交47063cd；生产仅cte.c按保存MPP分类/入口与内核返回清scratch/用户返回按Context推栈顶/初始化。原3模式失败，最终3guest GOOD TRAP（16M yield/9嵌套/真实MTIMER/2U trap/线程切换）、RT隔离链接配置到msh及am_hello、nanos8观察点与hello1440→6648、18项终检通过。失效夹具与RT链接条件明列，不宣称默认RT/NEMU链接或F0024已修；30已修/89未修完，本组Completed待确认提交，M2保持。

2026-10-18 [CRP F0024 trap地址空间确定性保存](code_correctness_review/crp-f0024/README.md)：F0023已确认提交c9be898；生产仅vme.c删除读未初始化槽的条件跳过，保留kcontext初始NULL/借用接口。原零槽真实A→B→A页表恢复失败、非零正常；修复零/非零/VME-off三guest GOOD TRAP，双私有VA/用户syscall嵌套及内核线程恢复、RT补充测试链接配置msh+am_hello、nanos8点/hello1483→6787、21终检通过。前组3,958证据保持；31已修/88未修完，本组Completed待确认提交，M2不变。

2026-10-18 用户确认并授权F0024提交：545条文件清单/原21项验收及生产patch保持；[提交及计数澄清](code_correctness_review/crp-f0024/README.md#approval-submit-20261018)说明F0023的3,958条是源树/产物/日志等文件SHA条目，非测试用例数量。本轮仅提交已完成批次，不启动后组。

2026-10-18 [CRP F0025/F0027/F0028 NPC启动布局](code_correctness_review/crp-f0025-f0027-f0028/README.md)：七脚本BSS实际对齐/完整边界、五搬运模式text与rodata逐节LMA/VMA/end、四可调heap容量/回绕拒绝。原8真实反例及13控制、最终35NPC启动/20heap边界、当前模型CPU36PASS+1XFAIL及RT四应用update/image/msh通过；旧执行器MRET分歧/现有CPU汇总假失败保留，最终重跑使用已核对当前源码模型。34已修/85未修完，本组三项Completed待确认提交，F0026/五CQ/M2保持。

2026-10-18 [CRP F0052终态归属补充](code_correctness_review/crp-f0052-ref-terminal/README.md)：前组13文件已确认提交f3a5d0c；仅改嵌套cpu-tests Makefile，按ARCH区分主终态，修复REF附加终态假ERROR与REF-only假PASS。定向42/42、真实NPC DIFF=1/NEMU全集各36PASS+1XFAIL且make exit0，当前模型先核身份；NEMU沿用_heap_end兼容配置。Completed待确认提交，不新增问题计数，M2保持。

2026-10-18 [CRP F0019表达式生成工具](code_correctness_review/crp-f0019/README.md)：前组F0052补充已确认分仓提交22791cf/f3d0252；仅gen-expr.c实现有界有效四则生成、独立C oracle/失败传播/私有临时目录。原空输出exit0见证，128条三方结果/真实CLI、10,000 sanitizer/3边界树、8输入/9oracle/3IO故障及并发通过，17项终检。明确非负INT_MAX域/29-token上限及未测边界；35已修/84未修完，本组Completed待确认提交，M2不变。

2026-10-19 [CRP F0004/F0005/F0008宿主内存组](code_correctness_review/crp-f0004-f0005-f0008/README.md)：F0019已确认提交522bed7；新增定长memcpy消除RAM对齐/别名UB、MEM_RANDOM安全写入及guest_to_host整数先减基址，F0005既有bc7a110修复补验闭合。GCC/Clang+sanitizer各181断言、static/malloc/REF实际构建/非对齐跨页/ABI、双CPU36PASS+1XFAIL、RT163.32秒msh/difftest ON、nanos8点/hello1267→5894与AM-native/RV双层启动通过，23终检。38已修/81未修完，本组待确认提交；保留raw helper前置/未测/无效夹具边界，M2保持。

2026-10-19 [CRP F0006/F0007解码与INV诊断](code_correctness_review/crp-f0006-f0007/README.md)：前宿主内存组已确认提交1ddaf04；FENCE.I忽略保留字段，INV仅用已取得原字、不再重复取指/预读。40次GCC/san定向、native/REF自修改及PMEM尾失败、双CPU全集各36PASS+1XFAIL/make0，23终检。其他ISA仅改动单元兼容通过、完整构建既有阻塞前后相同；40已修/79未修完，本组待确认提交，M2保持。

2026-10-19 F0006/F0007后续确认提交：用户“提交并继续CRP修复”确认前组报告范围/限制，实际提交7e68ca7（9文件74增26删）；647文件证据/23项验收无漂移，复用动态结果，未push。

2026-10-19 [CRP F0002 RV64物理地址身份](code_correctness_review/crp-f0002/README.md)：保留D21/窄paddr与REF ABI，仅mmu.c在Bare/页表遍历/叶PA窄化前拒绝高位别名。原86项45失败，修复GCC/sanitizer各86/86、P2原见证、8次真实native/REF高地址及既有Sv39/原子guest、双CPU各36PASS+1XFAIL、RT163.33秒msh/difftest ON、nanos8截图/hello1326→6382与23终检通过。41已修/78未修完，本组待确认提交；PMEM64/其他配置、DMA、五CQ及已列限制保留，M2保持。

2026-10-19 F0002后续确认提交：用户“提交后继续”确认前组报告范围/限制，实际784e73b（五文件72增9删）；285manifest/23既有验收保持，复用动态测试，无push。

2026-10-19 [CRP F0001算术宿主语义与双端核验](code_correctness_review/crp-f0001/README.md)：用户要求解释具体计算反例及双端必要修复。原NEMU GCC/Clang O2的7反例/64项数值全部正确，两种UBSan各7例中止；确认C UB，未观察普通O2数值错误。仅inst.c8增7删改7处无符号运算/低位符号扩展。原NPC RTL以独立期望64项配原/新REF均通过，无对应缺陷，保留原RTL；改错期望时双端真实BAD可检出。修复后4配置各64/64、native/REF构建/ABI、双CPU各36PASS+1XFAIL、RT168.44秒msh、nanos8截图/hello1262→5850、24终检通过。42已修/77未修完，本组待确认提交；326文件为证据SHA条目，非用例数，M2保持。

2026-10-19 F0001后续确认提交：用户“提交后继续”确认原报告范围/限制，实际252eaea（五文件77增10删），326manifest/24验收/身份保持，复用动态结果，无push。

2026-10-19 [CRP F0003双端指令对齐边界分析](code_correctness_review/crp-f0003/README.md)：原3例NEMU均跳到80000002，JAL/JALR污染rd；NPC原decoder/next-PC模块5控制观察及CSR写读确认无错位trap/mtval能力。这里只核模块控制，不冒称完整SoC结果。最小双端方案A（提前补M态cause0/mtval/精确提交）与延期B已具体列出，触发既有M3/WORKFLOW_POLICY §3范围裁决；生产修复未开始，不标F0003 Completed，不重跑无改动消费者。10项分析检查/57文件证据，42已修已提交/77未修完，M2/M3不推进。

## 2026-10-19 CRP F0003方案A实施结果

用户明确同意A，NPC cause0已复用ecall控制时序/三流水/有效WB链路，双端功能完成。[本组报告](code_correctness_review/crp-f0003/README.md#implementation-20261019)保存NEMU76×2、NPC71向量、真实三平台13trap/流水与mtvec前递、15微测试/15断言、双CPU各36PASS+1XFAIL、RT171.45秒msh及nanos8帧/hello1316→5722、28项功能终检。STA同配方前后估算频率399.074→355.983MHz（-10.80%），面积+1.10%，两版均未达500MHz；性能接受待用户决定。43功能已修/76未修完，本组结果确认/commit Pending；停等接受回退或继续优化的决定，Next仅TASK_QUEUE维护，不自动推进M2/M3/其他单元。

2026-10-19 [F0003并行mtvec补充交付](code_correctness_review/crp-f0003/README.md#parallel-mtvec-result-20261019)：用户批准后同单元Reopen，提前按指令类别读/前递mtvec、错位只控制最终选择，保留ecall流水/WB。71+14定向、实际SoC trap/冒险/mtvec与负例、15微测/15断言、NPC CPU36PASS+1XFAIL、RT169.64秒msh和24项核验通过；原385证据保持，NEMU/nanos未受影响复用验收。同配方估算420.232MHz，原399.074/串行355.983，面积相对原+0.265%，仍未达500MHz。原回退停点经获准优化解除，新结果确认/commit Pending，43已修/76未修完保持，未启动F0009/M2/M3。

2026-10-19 F0003确认/提交：用户“提交”确认双端修复及并行MTVEC补充的已报告范围/限制；57/385/193清单和28/11/24/8核验保持，复用验收。本批11文件提交，实际回执见[记录末尾](code_correctness_review/crp-f0003/README.md#approval-submit-20261019)及local/parallel-mtvec/submit-receipt.json/.agent；不push、不开始下一组，ignored资产仍仅本地保管。

2026-10-19 [F0003时序优化技巧/前后依赖图](code_correctness_review/crp-f0003/README.md#timing-technique-20261019)：补充串行CSR准备→按指令类别提前并行准备/晚到条件最终选择、判断公式/两处配套修改、icache终点解释及适用/验收方法；knowledge经验地图已登记。仅文档，复用已提交c920dbe的验证/STA，不改代码或启动后组；用户授权总结完成后直接提交。


## 2026-10-19 CRP F0009磁盘DMA与失败契约

[原行为复现及具体方案A/B](code_correctness_review/crp-f0009/README.md)：12个观察覆盖正常读写、高位别名、跨端、盘外、尾块、seek/短写/flush与零块；原MMIO/map/disk/paddr调用链，临时盘写入，生产未修。AM/nanos没有可消费错误状态，触发原入口的失败语义裁决停点；建议保留接口并失败终止/明确尾块，或增加可恢复错误协议。43已修/76未修完不变，等待本单元裁决，无修复Completion/提交，M2/M3保持。


2026-10-19 [F0009 A修复/最终验收与CCR清理](code_correctness_review/crp-f0009/README.md#implementation-result-20261019)：仅disk.c64位整段DMA/盘块边界及失败终止，零块/已知尾块规则，464定向/6初始化/原版负例、最终native-REF/真实MMIO与storage/nanos通过；PAL旧绘制风险保留。44已修/75未修完，本组待结果确认/commit。按用户要求删除18660可再生产物/旧源码副本、14大日志无损gzip，约4.29GiB逻辑减少；[CRP清理规则/agent工具](code_correctness_review/workflow/README.md#artifact-cleanup)已固化，历史manifest需合并清理回执，旧实现按Git版本重建，不依赖保留的旧二进制。

2026-10-19 F0009用户确认补充：用户手工执行确认PAL绘图正常，原短时不完整观察由运行慢导致；已确认本批结果并授权提交。复用既有验收与清理回执，不记性能修复；实际提交见[F0009回执](code_correctness_review/crp-f0009/README.md#approval-submit-20261019)，本轮不push/不启动F0016。


## 2026-10-19 CRP F0016与NEMU/nanos性能诊断

[F0016修复与性能实测](code_correctness_review/crp-f0016/README.md)：实际装载三段完整同步golden，旧版真实差异/新版Spike与REF全字节读回、四负例、单镜像/内置/loader/native/REF验收通过。真实nanos约16–18M guest/s，hello后台45.46%、OPL合成27.14%、guest绘图15.14%；host翻译/访存占self样本约61%，关闭host绘制未见提速。性能未优化；45已修/74未修完，本组待确认提交，未来唯一入口TASK_QUEUE#crp-next，M2保持。


## 2026-10-19 NEMU宿主访存热路径优化

[宿主优化与同轮复测](code_correctness_review/host-perf-20261019/README.md)：复用checked MemRegion、省去单页读/取指重复预检，保持原hooks/trace/MMIO/Sv39/接口；2亿指令3次交错中位17.190→19.740M/s（+14.84%），5亿单对15.980→18.233M/s（+14.10%）。430/473边界、384条trace完全相同、malloc/高地址/Sv39/原子与REF ABI、双CPU36PASS+1XFAIL、新NPC+REF的RT到msh、nanos三前台/hello通过。独立用户授权优化，F0016待确认/提交改动保留，45/74计数不变；本轮待确认/commit，无push/下一CRP Start。


## 2026-10-19 nanos前台/hello调度99:1与提交收尾

[调度比例与验证/提交回执](code_correctness_review/hello-scheduling-20261019/README.md)：用户明确100次调度仅一次hello，非打印降频。FG_PROCESS每百次99fg/1hello，50000调用/滑动窗口及真实31窗口累计3069fg/31hello/31真实切入通过；纯生产内核3亿指令与三前台/后台进度通过，打印阈值/Navy盘不变。用户条件授权测试后提交F0016/宿主优化/调度三个归属单元，复用旧验收及清理记录，实际SHA见回执；45/74保持，无push/下一任务Start。
