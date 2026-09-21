# records/knowledge —— 经验性归档（案例复盘 / 方法论 / 性能分析）

> 可复用的"怎么做/为什么"：独立成篇的经验文档 + 指向过程文档中方法论章节的**经验地图（按阶段排序）**。
> 过程时间线见 [`../process/README.md`](../process/README.md)；入口总览见
> [`../../docs/PROJECT_OVERVIEW.md`](../../docs/PROJECT_OVERVIEW.md)。
> **状态图例**：✅ 有效 ｜ ⚠️ 部分结论已被取代（保留工具/方法价值，见对应权威文档）｜ 📦 跨平台旧案

## 1. B3 性能链（按阶段）

| 文件 | 阶段 | 主题 | 要点 | 状态 |
|---|---|---|---|---|
| `B3_STAGE2_PERF_ANALYSIS.md` | 阶段2 | 性能剖析 + Amdahl 瓶颈分析（microbench test） | **计数器手册 + PERF-CHECK 自检**（decode==retire==exu、cat_sum==decode、deliver−decode≈bubble）+ P4 修法（按请求拍计数替代 held-valid 按拍）。可信旧结论：dcache 读缺失 3.21%/写 15.47%、SRAM 端到端≈9cyc | ⚠️ 旧 IPC/延迟数字已被阶段5/7 校准口径取代（`../process/B3_STAGE5_PERF.md`、`B3_STAGE7_RECALIB_PERF.md`） |
| `B3_CACHESIM_ANALYSIS.md` | 阶段3 | cachesim 参数化 DSE（8KB/整颗 SRAM 约束） | 工具 `npc/verif/cachesim/`（C++）、trace 导出（`CACHESIM_TRACE`）、未校准 `RegionCost` 初值；瓶颈在固定 MMIO（UART printf）与单次缺失代价 | ⚠️ 旧结论"几何最优仅 +3.5%、几何非瓶颈"已被 E1 校准推翻（16B 块 −13.2%，见 `../process/B3_STAGE8_PE_CACHESIM_DIFF.md`）；保留工具约束与旧模型记录 |
| `APB_PSRAM_HANDSHAKE_DEBUG.md` | 阶段4 | 控制器 IP 状态机握手调试（E1c/E1d 暴露的重触发 bug） | 从机状态机只在「新请求握手上升沿」触发、不能拿持续电平当事件；两种失效（回 IDLE 重读、组合触发器 mr_rd 洪水）+ 检测法（trigger/done 1:1、写→读一致性小模型）+ 修复范式（prev 构造 new_access 单脉冲 + stb=penable） | ✅ |
| `SDRAM_AXI_BURST_DEBUG.md` | P-D | SDRAM AXI 突发链"伏击双 bug"案例复盘 | ①跨级对账同窗口/同口径/握手沿采样（"写拍 4160 vs 986"为探针窗口假象）；②颗粒模型读输出必须支持背靠背（CAS 流水线，RD_DELAY=2）；③64→32 宽拆 FIXED 必须改 INCR；④脱离 SoC 最小复现 + pin 级打印 + 状态扫描 VCD + 固定回归 TB | ✅（过程数据以 `../process/B3_STAGE8_PD_DEBUG.md` §7 为准） |
| `MEM_PIPELINE_OPT.md` | 阶段I 时点 | 访存流水线性能分析与优化方向 | 架构分析/瓶颈定位/浪费点 W1–W10/优化方向 A1–A5、M1–M6——支撑"NEMU+NPC 双端 Linux + 持续性能优化"的方法底座 | ⚠️ §1 架构现状（SDRAM 在 APB、axiburst 含 SDRAM）已被 P-D 的 AXI4SDRAM+bus 直连更新（见 `B3_STAGE8_PD_DEBUG.md`）；浪费点/方法仍有效 |

## 2. 工具入门（可独立于阶段查阅）

| 文件 | 主题 | 要点 | 状态 |
|---|---|---|---|
| `FORMAL_VERIFICATION_NPC.md` | 形式化验证入门（SymbiYosys+Yosys+SMT/sby+z3/btormc） | assume/assert/cover 三角色、bmc/cover 两模式、depth/mode/solver 参数、REF-vs-DUT 等价思想、完整编译链、五大坑 + div/axiburst/icache 三案例（§10 含选型对比） | ✅ |
| `SYNTHESIS_STA_NPC.md` | 逻辑综合与 STA 入门（yosys+ABC+iEDA/yosys-sta） | 面积/频率来源、gen_synth_rtl.py→make syn sta 全流程逐参数、yosys.tcl 白话、平坦 vs 层级、八大坑（**库不可比**/SRAM 黑盒/端口名等）、面积优化手法总览 | ✅ 数字速查以过程记录为准（`../process/B3_STAGE8_AREA_N45.md`、`B3_STAGE8_PA_A1.md`：A1 后 **118,805.71μm² / 426MHz**） |

## 3. 工程方法

| 文件 | 主题 | 要点 | 状态 |
|---|---|---|---|
| `LONG_SIM_PROC_MGMT.md` | 长仿真进程管理与安全终止（P-G/P-E 长跑经验） | `pkill -f <pattern>` 会自杀（匹配 shell 自身）→ 用 `pgrep/pkill -x` 或 `pkill -f '[y]syx...'`；长跑 `setsid` 脱离进程组；前置保险：`SIM_END`、总线看门狗、探针 cap、**启动前查镜像大小**（linker 错→GB 级镜像空转） | ✅ |

## 4. 跨平台旧案

| 文件 | 主题 | 要点 | 状态 |
|---|---|---|---|
| `rtthread-stackoverflow-debug.md` | RT-Thread 栈溢出（NEMU 平台，2026-08-19） | 现象→定位→验证→修复完整链路；根因=main 线程栈溢出破坏对象链表（klib printf 2048 缓冲），非 NEMU bug | 📦 与 `../process/STAGE_F_RTTHREAD_PROMPT.md` 起的 NPC/PSRAM 线无关 |

## 5. 经验地图（指向过程文档中的方法论章节，按阶段排序）

> 过程文档以时间线为主，其方法/教训章节可直接按下表定位查阅，无需通读全文。

| 主题 | 出处 | 一句话要点 |
|---|---|---|
| cache 掩码/时序/PSRAM/SRAM wmask 等硬件经验 | `../../docs/DEBUG_WORKFLOW.md` §3 | 活跃文档，硬件坑汇总（现行参考） |
| 计数器正确性：held-valid 按拍污染 vs 按请求拍 | `B3_STAGE2_PERF_ANALYSIS.md` 附录 A/D + §1 | `O_cpu_rvalid` 可保持多拍 → 按拍计数被放大 ~9×；改为"请求拍 + FSM 有边界计时"；PERF-CHECK 是运行时判据 |
| 动态指令数不是跨配置不变量（时变轮询归因法） | `../process/B3_STAGE7_RECALIB_PERF.md` §2.1 | 外设轮询（UART LSR）次数随 CPU/外设相对速度变化：retire 差=每轮询迭代指令数×轮询次数差；跨配置只比 IPC/cycles |
| 提频收益 vs 访存等待的 Amdahl 饱和模型 | `../process/B3_STAGE7_RECALIB_PERF.md` §4 | r=f_CPU/f_APB 下 T(α)=U/α+M·α，吞吐天花板 1/(1−p_mem)；p_mem>0.5 时先降访存占比再提频 |
| 跨配置比较必须声明时间口径（PERF 总周期 ≠ 程序窗口） | `../process/B3_STAGE8_PC_AMAT_LAYOUT.md` §1/§5 | `PERF[final] cycles` 含 boot；`.text` 搬 SDRAM 场景纯 kernel −31% 但端到端 +24.8% → 结论必须两口径并列 |
| 「逐行译码写」generate 模式的面积陷阱 | `../process/B3_STAGE8_AREA_N45.md` §4.1 | `generate for(i) assign hit[i]=(i==idx)` 让工具复制 N 份比较器；应改直接索引写/共享译码器；同族：FF 寄存器堆索引读 mux 树 |
| 全链路逐环验证 / 哨兵法 / 双实现对照归因 | `../process/ONSCRIPTER_NAVY_NATIVE_DEBUG.md` §8 | 各环一次性采样打印快速二分；写后回读区分"写失败"与"写后被覆盖"；参考实现 vs 目标实现对照是最可靠归因手段 |
| fb 转储分界判据 / "透明窗口"逻辑锁 | `../process/ONSCRIPTER_NAVY_NATIVE_DEBUG.md` §9.2 | `cp /proc/<pid>/fd/<memfd:fb>` 做像素统计是"游戏→fb"与"fb→屏"的分界判据；不透明帧缓冲与"透出桌面"逻辑不相容 |
| 静态符号表 ≠ 动态导出 | `../process/ONSCRIPTER_NAVY_NATIVE_DEBUG.md` §9.5 | `nm`（.symtab）的 GLOBAL 符号对动态链接器不可见；劫持类结论必须 `nm -D`/`LD_DEBUG=bindings` 实证 |
| 双侧对照打印验证自研层语义 | `../process/ONSCRIPTER_FIX_PLAN.md` 阶段 B | 自研库是否"语义合规"：与参考实现同打印点跑同样本对齐调用序列 |
| 差分调试锁定"被替换层" | `../process/ONSCRIPTER_FIX_PLAN.md`（用户裁决） | 两世界唯一差异层=被替换层，应优先锁定；复用层测出问题既不可修也解释不了参考侧正常 |
| NEMU MMU 断言的定位法 | `../process/ONSCRIPTER_RISCV_NEMU_PORT.md` §2 | 断言前打印 pc/ra/vaddr/satp → addr2line 落到源码行 → 反推调用链 |
| Kconfig 修改静默失效 | `../process/ONSCRIPTER_RISCV_NEMU_PORT.md` §3 | 直接 sed `.config` 不触发 `autoconf.h` 重生成，须 `conf --syncconfig Kconfig` |
