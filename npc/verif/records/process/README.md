# records/process —— 日志型归档（阶段实施/调试过程/任务提示词）

> 按时间顺序的"当时做了什么"：实施记录、调试时间线、任务定义与续作提示词（PROMPT）、修复计划。
> 可复用的经验与方法论见 [`../knowledge/README.md`](../knowledge/README.md)。
> 入口总览/现状目标见 [`../../docs/PROJECT_OVERVIEW.md`](../../docs/PROJECT_OVERVIEW.md)。

## 访存体系（阶段 1–3）

| 文件 | 主题 | 要点 |
|---|---|---|
| `STAGE1_CACHE_REWORK.md` | 缓存重构 + SoC 访存接口适配 | cache AX/X 耦合点 C1–C8、dcache 写分配掩码、fence.i/cacheline 写回 bug、验证体系（末尾含"阶段2"草稿，与 STAGE2 重叠） |
| `STAGE2_MEM_IF.md` | 阶段2 访存接口重构设计基线 | CPU↔cache 接口、AXI burst/MMIO 生成、slave_crossbar、SoC 地址映射、S0–S5 实施计划 |
| `STAGE3_PSRAM_READDBG.md` | 阶段3 PSRAM 读回错位调试 | flash 数据通路修复、PSRAM 读回逐级定位、根因=dcache 写分配掩码 |

## RT-Thread / SDRAM / 外设（阶段 F–K）

| 文件 | 主题 | 要点 |
|---|---|---|
| `STAGE_F_RTTHREAD_PROMPT.md` | 阶段 F 任务提示词 | RT-Thread 在 PSRAM 执行的原始任务说明（结论见 DEBUG_WORKFLOW 阶段 F 记录） |
| `STAGE_H_ONWARDS_TASKS.md` | 阶段 H–K 任务定义与实现路径 | SDRAM/字扩展/外设 J1–J5/ChipLink 的任务分解+完成记录 |
| `STAGE_I_SDRAM_EXT_PROMPT.md` | 阶段 I 任务提示词 | SDRAM 位扩展(2颗粒→32bit)+字扩展(4颗粒)——新对话续作提示词 |
| `STAGE_I_SDRAM_EXT.md` | 阶段 I 实施记录 | 位扩展(64MB)+字扩展(128MB)的相位推导/改动/坑/验证数据 |
| `STAGE_J0_NVBOARD.md` | J0 NVBoard 接入 | NVBoard 接入 soctest + GPIO 7 段译码；坑与验证 |
| `STAGE_J1_GPIO.md` | J1 GPIO | GPIO 控制器 RTL + 寄存器/引脚验证（difftest ON + 波形） |
| `STAGE_J2_UART.md` | J2 UART | AM_UART_RX + 除数随 NVBoard 条件化 + RT-Thread 键入 + am-tests hello 验证 |
| `STAGE_J3_PS2.md` | J3 PS/2 键盘 | RTL 解码+FIFO + AM 键盘 IOE 翻译表 + soctest 防误采 |
| `STAGE_J4_VGA.md` | J4 VGA/timer/video | vga_top_apb + AM GPU IOE + mtime；坑=NVBoard UART 除数、.bss 搬运 |
| `STAGE_J5_RTTHREAD_AM.md` | J5 rt-am 合并 + am-apps 集成 | make update 集成 hello/microbench/snake → msh am_<app>；附录含 RT-Thread 带 NVBoard 的 make 链路 |
| `STAGE_J_ONWARDS_PROMPT.md` | 阶段 J 后续任务提示词 | J1–J5 现状/目标/实现路径——新对话续作提示词 |

## B3 性能优化（阶段 1–5）

| 文件 | 主题 | 要点 |
|---|---|---|
| `B3_STAGE5_PERF.md` | B3 阶段5：访存延迟校准 + `make perf` IPC 对比 | E1c/E1d 结论：`apb_delayer` r=3.5；IPC 无校准 0.196 → 有校准 0.074；XIP/PSRAM 状态机重触发根因（mr_rd 洪水）+ commit 清单 |
| `B3_STAGE6_ICACHE_BMC.md` | B3 阶段6：icache 数据透明性 BMC（btormc PASS） | 规模数据（状态≈1500 位；depth 20/30/35 PASS、depth 40 超时=可判定上限≈35；`mode cover` 证实 O_cpu_rvalid step10 可达非空泛）；断言加 `!I_rst&&qv` 门控排除初始态伪反例 |
| `B3_STAGE7_PROMPT.md` | B3 阶段7 续作提示词（复制即用） | 新会话任务："校准后重新寻找瓶颈 + 主频优化是否值得"；含工程背景/本阶段目标/可用工具数据/执行方法/交付验收/约束停点/下一步（阶段8） |
| `B3_STAGE7_RECALIB_PERF.md` | B3 阶段7：校准后瓶颈重定位 + 主频优化取舍（**结案**） | r=3.5 校准后 IPC=0.0738；**store 写路径升 #1（41.0% T，=写缺失 3,307×2,244cyc，Amdahl 极限 1.69×）**，load 29.5%、UART 轮询 12.4%、ifu 供给仅 4.4% 非瓶颈；**主频：p_mem=0.70 下提频天花板 +42%、α=2 已拿 90%（+28.5%）而 IPC -36% → 推荐先降 p_mem 再提频**；§2.1 retire 时变归因（UART LSR 轮询差 ×3=指令差，跨配置比 IPC 有效、比指令数无效） |
| `B3_STAGE8_AREA_N45.md` | B3 阶段8（一）：**nangate45 各模块面积报告** + 大面积定位 | **工艺库更正：E1b 的 16.4 万是 icsprout55，与讲义 25000 约束不可比**；nangate45 复测：**面积 120,383.62μm²（4.8× 上限）、f_max≈411MHz（关键路径仍=icache FSM）**；层级面积表（dcachectrl 36.3K/icachectrl 25.9K/gpr 18.0K = 67%）+ 根因（cache 元数据**逐行译码写** generate 模式、FF 寄存器堆 2 读口 mux 树）+ 改法与预估；dcache 理想收益 3.38×/性价比快答（讲义 #15/#31） |
| `B3_STAGE8_PA_A1.md` | B3 阶段8（二）：P-A/A1 面积优化实施（**面积 −1.3%、f_max +3.7% 双改善；"编码冗余"假设被实验否定**） | **V1 索引写反而 +7.2K（memory 推断把全表复位换进数据端、DFF 换贵单元 SDFFCE_PN0P，已回退）**；保留改动=tag 读口共享（way1/fencei 互斥复用）+mmio_flag 前缀化+alloc_lane 复用；最终平坦 **118,805.71μm²（−1,578）/ f_max≈426MHz（−0.348ns，关键路径仍 icache FSM）**；功能零变化（微测试 16/16 + PERF 逐位一致）；教训：带全表复位的阵列勿写变量索引、ABC 已自动共享重复逻辑；后续杠杆=几何降配（归 P-E） |
| `B3_STAGE8_PC_PD_PLAN.md` | B3 阶段8（三）：P-C+P-D 执行计划 | 架构核实：npc bus 直连路径 SDRAM 请求本就 64bit 突发直传（绕过 axiburst2xxx 天然成立）；SoC xbar 全域 64bit 而 `sdram_top_axi` verilog 32bit → AXI4SDRAM Impl 内插 delayer+64→32 burst 保形转换（不改第三方 core）；程序上 SDRAM 复用 `BOOT_MODE=sdram/sdram-heap`；delayer 仿 APB B 方案（握手上升沿/单脉冲坑规避、逐拍等式） |
| `B3_STAGE8_PC_AMAT.md` | B3 阶段8（四）：P-C 数据分析平台 + 基线（**关闭讲义 #17**） | `icache_stats.sv`（缺失代价=rd_miss→rvalid 有边界计时）+ `amat_report.py`（日志→AMAT/TMT）；基线 icache AMAT=3.02（1+0.05%×4285 flash XIP）；**新洞察：icache flash refill 816 次×4,285≈3.49M≈19%T 被阶段7"残差"掩盖（ifu_miss 计数低估），归因更新：store 41%>load 29.5%>icache flash 19%；.text 搬出 XIP 为高价值优化（P-D/P-F 协同）** |
| `B3_STAGE8_PC_AMAT_LAYOUT.md` | B3 阶段8（七）：P-C 平台复跑 —— 三配置 AMAT/TMT + SDRAM 布局/.text 收益量化 | A(xip)/B(sdram-heap)/C(全 SDRAM) 同条件（PERF=1 r=3.5）对比：**堆放 SDRAM 写缺失代价 2244→1422、端到端 18.32M→15.33M（B 最优）**；**.text 进 SDRAM 使 icache AMAT 3.02→1.58、纯 kernel Scored −31%**，但 bootloader 搬 30KB 一次性多耗 ~5.5M cyc → 端到端反 +24.8%（优化加载路径归 P-F）；**§6 追加 r=4.25 复跑：SDRAM 代价超线性（~2×）→ 布局排序翻转为 A<B<C**；含复现命令与口径备注（PERF cycles 含 boot ≠ benchmark 窗口） |
| `B3_STAGE8_PE_CACHESIM_DIFF.md` | B3 阶段8（十一）：P-E/E1 —— cachesim↔RTL 对账 + 成本模型校准 | **E1 通过**：trace F 钩子改取指握手后 F=1,732,607 与 ICACHE 精确一致、R/W 各区一致；替换策略对齐 RTL 后 **结构 0 偏差**（I 815/816、D 4,397=rd1,090/wr3,307 逐区精确）；成本校准（新增 base_w：psram 1676/2244、flash 4285/4529、sdram 1346/1370/1422、MMIO 18/7）→ **缺失 TMT 精确一致**（icache −0.01%、dcache 0%）；**校准后扫描：16B 块成最优（8KB 内 −13.2% TMT）**，推翻旧模型"+3.5%"结论 |
| `B3_STAGE8_PH_PROMPT.md` | B3 阶段8 **P-H 续作提示词（复制即用，新对话入口）** | 现状（阶段8 主体完成 P-A~P-G，仅剩 P-H）+ P-H 三小项（#12 局部性绘图/#13 数组vs链表/#19 压缩 trace）做法与验收 + 工作流约束（先计划/一次一项/停点）+ 关键命令与资产 + 7 条已知坑（pkill -f 自杀、setsid、mainargs 编译期、探针输出插行、基线逐位、布局判据、文档约定） |
| `B3_STAGE8_PG_TRAIN.md` | B3 阶段8（十五）：P-G train 规模性能记录 + .text 搬 SDRAM 收益确认 | 三布局并行（r=3.5/PERF=1，~1.5h）：**A xip 2,458.2M / B sdram-heap 2,134.6M / C sdram 1,916.7M cycles（IPC 0.0271/0.0312/0.0348），全 PASS+等式 OK**；**用户假设确认**：train 下 icache 缺失 99,421 次×（4286→1341）= TMT −290M，一次性搬运 +5.5M → **C 端到端 −10.2%（−217.9M）**；结论：长跑用 `BOOT_MODE=sdram`，短跑仍 sdram-heap（break-even≈50M cyc 实测验证） |
| `B3_STAGE8_PE_E4_SAMPLE.md` | B3 阶段8（十四）：P-E/E4.1+E4.2 —— 参数化 + 目标几何综合采样（**停点：面积模型偏差 >15%**） | E4.1 `dcachectrl` 行宽/几何参数化（`WAY_W/WAY_LANES/LANE_W`+generate 泛化），**默认零回归**（make perf 逐位一致 + mem-test PASS）；E4.2 同流程采样：dcache 4KB/32B/2w→8KB/64B/2w 逻辑面积 **+5,464（+13.9%）**（模型预测 −2.2%，偏差 ≈16pp，**行路径位宽成本未建模**）、f_max +2.4%；修正 A 全芯片面积 ≈+5%（非持平）；**用户裁决：暂停 E4，P-E 结案**（dcachectrl/icachectrl 均已参数化；way 数仍 2 路硬编码；资产保留可复用） |
| `B3_STAGE8_PE_E4_PLAN.md` | B3 阶段8（十三）：P-E/E4 实施计划 —— A 方案（icache 2KB/32B/1w + dcache 8KB/64B/2w）（**待确认**） | 现状硬编码点清单（参数/行路径/8bit cen 拼接/8 颗 SRAM/axiburst 只支持 32B burst）；子阶段 E4.1 参数化（默认零回归硬门槛）→ E4.2 目标几何综合采样校准面积模型 → E4.3 **PSRAM 64B 通路决策**（最大风险：axiburst2xxx 只实现 32B）→ E4.4 落地+全回归+评估；预计 2–3 轮，可回退 |
| `B3_STAGE8_PE_DSE.md` | B3 阶段8（十二）：P-E/E2+E3 —— 16B/32B 块对比 + 面积约束 DSE | 面积模型（逻辑=元数据线性外推+固定控制；SRAM=fakeram45 4.11μm²/B）基线全芯片估算 152.5K；**E2：校准后 16B 块 TMT 最优（−13.2%）但 8KB 内需 5 路 dcache（元数据 +59%）→ 面积不增约束下无 16B 方案**；**E3 Pareto：推荐"icache 2KB/32B/1w + dcache 8KB/64B/2w"（TMT −6.5%、面积持平）；省面积方案（各 2KB/1w）−21% 面积/IPC −9%；激进（D8SR+16B）−14.6%/+20% 面积**；E4 待拍板 |
| `B3_STAGE8_PE_PLAN.md` | B3 阶段8（十）：P-E 阶段计划 —— cachesim 闭环 + 面积约束 DSE（**待确认**） | E1 cachesim↔RTL 对账（校准 RegionCost，命中差≤0.5%/TMT 差≤10%）；E2 16B/32B 块对比成文；E3 面积约束 DSE（面积模型=元数据实测插值+SRAM 宏单列；≥12 点扫描；Pareto；r 双口径）；E4 终选落地+全回归；人工决策点=面积口径/候选范围/终选；风险=SRAM blackbox、模型近似、收益天花板 ≈+3.5% |
| `B3_STAGE8_PF_LOADER.md` | B3 阶段8（九）：P-F 加载路径量化与优化（`BOOT_MODE=sdram` 搬运） | `BOOT_TO_T0` 插桩实测：校准 r=3.5 下搬运 ~30KB = **5.58M cyc（≈186cyc/B，77% 是 ~953 个 flash 行填充×4.5K）**；`boot_sram.c` 拷贝改 **8B 批量**（−0.21M 直通 / −0.15M 校准 / 端到端 −0.14M，sram/psram/sdram 通用）；**break-even ≈ 50M cycles → 默认维持 B(sdram-heap)，全 SDRAM 仅长跑场景**；**§6 尾部收尾（P-F ✅ 结案）**：填充/对齐（align 8/64/128）全负收益（icache 缺失 +4~29%、cycles +0.5~1.2%）→ 默认布局最优；`.rodata` 留 flash 否决（train 下 flash rodata 读缺失 64.5M ≫ 省下搬运 1.8M） |
| `B3_STAGE8_PB_FMAX.md` | B3 阶段8（八）：P-B 部件级 f_max 评估（#6，**结案：决策 C 已落地**） | 探针平台 `verif/sta/probe/probe_run.sh`（nangate45）：**gpr 14,214μm²/0.490ns/2,041MHz；64bit 加减法器 2,111μm²/1.435ns/697MHz**；全芯片 A1 后 426MHz（关键路径仍=icache FSM）→ 数据通路非瓶颈、提频杠杆在 FSM；**§6 用户拍板 C：`PERF_R426=1` 参数化 r（默认 3.5 不变），r=4.25 复跑 EQUATION OK + 三配置数据（SDRAM 代价超线性，布局排序翻转）** |
| `B3_STAGE8_PD_DEBUG.md` | B3 阶段8（五）：P-D SDRAM AXI 突发链（**结案：A/B 双根因+修复+全绿**） | 前序：改动清单（scala 仅学号+AXI 挂载，**突发参数不许改**；npc SDRAM→bus 直连绕过 axiburst2xxx；新 `axi4_delayer/axi64to32`）；**§7 收尾**：先更正"从端 4160 写拍 vs 986"是探针日志窗口口径假象（写通道无重复）；**根因 A = 自制 `sdram.v` 读输出"预取+保持"不支持背靠背读**（突发读偶拍恒 0 → 可缓存 refill/64bit MMIO ld 受害）→ **CAS 流水线 RD_DELAY=2**；**根因 B = `axi64to32` 宽拆保留 FIXED**（`ld/sd` 单拍拆两拍落同地址、高半字覆盖低半字）→ **宽拆强制 INCR**；验证：定向 TB 7 case PASS + 配置 X/Z microbench 全 kernel PASS + mem-test PASS + AXIDLY/APBDLY EQUATION OK + `make perf` 逐位一致 |
| `B3_STAGE8_PD_HANDOFF.md` | B3 阶段8（六）：P-D 调试交接（**A/B 已在 PD_DEBUG §7 收尾，本文留作过程快照**） | 基线逐位一致；`axi64to32` 道感知修复→零 strb 归零、mem-test PASS；AW-without-W 假设被证伪；从端存储自洽+突发形态正确；当时未解 A（"写拍重复"疑点——后证伪为窗口口径）、B（单拍下 15pz 丢指针）；调试设施清单+复现命令 |
| `B3_STAGE8_PD_PROMPT.md` | B3 阶段8 P-D **续作提示词（复制即用）** | 新会话任务：完成 P-D 两个遗留 bug（A/B）直至全绿；含当前状态/证据/约束（不改 TransferSizes/未清 bug 不提交）/执行方法（波形逐周期计数、扩窗日志）/回归链/交付验收/下一步 |

## ONScripter 移植（PA4.5 选做，2026-09-03 ~ 09-04）

| 文件 | 主题 | 要点 |
|---|---|---|
| `ONSCRIPTER_PROMPT_V2.md` | 续作提示词 | 任务目标/已固化事实/工作流约束/建议执行顺序 |
| `ONSCRIPTER_NAVY_NATIVE_DEBUG.md` | navy-native 透明窗口调试（**结案**） | 根因=native.cpp 上屏偏离官方框架；含 §2 劫持误判修正、§8 调试技巧、§9 结案（定位方法/逻辑锁） |
| `ONSCRIPTER_FIX_PLAN.md` | 显示修复整体计划与执行 | 阶段 A–D：误判修正→双侧对照→根因定性→官方化修复 |
| `ONSCRIPTER_RISCV_NEMU_PORT.md` | riscv64(NEMU) 移植（**验证通过**） | navy 编译打通；内核三修复（fs_open/sys_execve·exit/max_brk）；syncconfig 坑；运行命令；NPC 内嵌 ramdisk 休眠机制 |
