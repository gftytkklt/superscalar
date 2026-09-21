# records/knowledge —— 经验性归档（案例复盘 / 方法论 / 性能分析）

> 可复用的"怎么做/为什么"：独立成篇的经验文档 + 指向各过程文档中方法论章节的**经验地图**。
> 过程时间线见 [`../process/README.md`](../process/README.md)；入口总览见 [`../../docs/PROJECT_OVERVIEW.md`](../../docs/PROJECT_OVERVIEW.md)。

## 独立成篇

| 文件 | 主题 | 要点 |
|---|---|---|
| `rtthread-stackoverflow-debug.md` | 案例复盘：RT-Thread 栈溢出（NEMU 平台） | 现象→定位→验证→修复的完整链路；根因是 main 线程栈溢出破坏对象链表，非 NEMU bug——"看似模拟器问题实为软件 bug"的典型样本 |
| `MEM_PIPELINE_OPT.md` | 访存流水线性能分析与优化方向 | 架构分析/瓶颈定位方法/验证策略/优化方向/浪费点清单——**支撑未来目标"NEMU+NPC 双端 Linux + NPC 持续性能优化"的方法底座**（当前阶段 B3 调优在此基础上推进） |
| `B3_STAGE2_PERF_ANALYSIS.md` | B3 阶段2 性能剖析 + Amdahl 瓶颈分析（microbench test） | IPC≈0.197。**复核更正：旧 latency/占比数字因 `O_cpu_rvalid` held-valid 被放大、不可信**；改用"请求拍 + FSM 有边界计时"（附录 D=P4）。可信结论：① dcache 读缺失 3.21% / 写缺失 15.47%；读缺失代价 avg≈748cyc、写缺失 avg≈657cyc（未校准）；**② SRAM 端到端访问≈9cyc（非 1cyc，AXI/APB 桥往返）**→ 缓存 SRAM 有收益（命中≈2cyc），但需与用户确认 SRAM 本征延迟/桥开销取舍；③ **PERF-CHECK 自检**（decode==retire==exu、cat_sum==decode、deliver−decode≈bubble）实证 OK；含计数器含义/用法说明 + P4 修法 |
| `B3_CACHESIM_ANALYSIS.md` | B3 阶段3：cachesim 参数化设计空间探索（8KB/整颗SRAM约束） | 工具 `npc/verif/cachesim/`（C++），trace 由 npc 仿真 DPI 导出（`CACHESIM_TRACE`）。microbench test：icache 命中 99.95%、dcache 91.26%、extra-stall≈6.58M；**8KB 内几何重分配最优仅 ~+3.5%（Amdahl 限制）→ cache 几何非瓶颈**；瓶颈在**固定 MMIO（UART printf 456K 次 + SRAM 栈/全局 43K 次×8cyc）**与**单次缺失代价（flash 1309 / dcache 写缺失含脏回写）**；改 `RegionCost()` 初值/配置接口可校正成本模型 |
| `APB_PSRAM_HANDSHAKE_DEBUG.md` | **控制器 IP 状态机握手调试**（E1c/E1d 延迟校准暴露的重触发 bug） | 核心原则：从机状态机只在「新请求握手」（access 上升沿）触发，不能拿持续电平（psel/wb_valid 常高）当事件；两种失效（回 IDLE 重读、组合触发器 mr_rd 洪水）+ 检测法（计数 trigger/done 1:1、写→读一致性小模型）+ 修复范式（prev 信号构造 new_access 单脉冲 + stb=penable） |
| `SDRAM_AXI_BURST_DEBUG.md` | **案例复盘：SDRAM AXI 突发链"伏击双 bug"（P-D）** | ①跨级对账必须同窗口/同口径/握手沿采样（"写拍 4160 vs 986"是探针窗口假象）；②**颗粒模型读输出必须支持背靠背（CAS 流水线）**——旧"预取+保持"被下一拍命令清掉→突发读隔拍恒 0，TB 标定 RD_DELAY=2；③**64→32 宽拆 FIXED 必须改 INCR**（否则 `ld/sd` 单拍拆两拍落同地址、高半字覆盖低半字）；④通用方法：脱离 SoC 最小复现 + pin 级逐命令打印 + 状态扫描 VCD 重放 + 固定回归 TB |
| `FORMAL_VERIFICATION_NPC.md` | **形式化验证入门**（SymbiYosys+Yosys+SMT/sby+z3/btormc，新手友好） | assume/assert/cover 三角色、bmc/cover 两模式、depth/mode/solver 关键参数含义、REF-vs-DUT 等价思想、完整编译链（trim_rtl.py→vsrc_fm.v→sby→yosys-smtbmc→z3/btormc）、文件清单、五大坑（BMC 任意初态/空泛 PASS/规模先测/宽位用 boolector/REF 别带真实存储）+ 新手起步路径；**§10 含 div/axiburst/icache 三案例分析**（各讲验证目标→假定条件→判定方法→结论/坑，附选型对比表） |
| `SYNTHESIS_STA_NPC.md` | **逻辑综合与 STA 入门**（yosys+ABC+iEDA/yosys-sta，新手友好） | 面积/频率两指标从哪来（liberty/标准单元/关键路径/slack）、工具链分工、gen_synth_rtl.py 预处理→make syn sta 全流程逐参数讲（PDK/CLK_FREQ_MHZ/**CLK_PORT_NAME 坑**）、yosys.tcl 逐段白话（flatten/share/dfflibmap/abc DELAY-4/upsize-dnsize=面积↔频率交换机制）、平坦 vs 层级两种口径、八大坑（**库不可比**/SRAM 黑盒/端口名/产物 gitignore `sta/result*/` 通配）、面积优化手法总览（逐行译码写陷阱/宏化/降宽/FSM 编码）+ 当前基线速查（nangate45 120,384μm²/411MHz） |

## 经验地图（指向过程文档中的方法论章节）

> 过程文档以时间线为主，但其方法/教训章节可直接按下表定位查阅，无需通读全文。

| 主题 | 出处 | 一句话要点 |
|---|---|---|
| 全链路逐环验证 / 哨兵法 / 双实现对照归因 | `../process/ONSCRIPTER_NAVY_NATIVE_DEBUG.md` §8 | 在解码/blit/上屏各环注入一次性采样打印快速二分；写后回读区分"写失败"与"写后被覆盖"；参考实现 vs 目标实现对照是最可靠归因手段 |
| fb 转储分界判据 / "透明窗口"逻辑锁 | 同上 §9.2 | `cp /proc/<pid>/fd/<memfd:fb>` 做像素统计（RGB 占比+alpha 分布）是"游戏→fb"与"fb→屏"的分界判据；不透明帧缓冲与"透出桌面"现象在逻辑上不相容，可用于排除整段链路 |
| 静态符号表 ≠ 动态导出 | 同上 §9.5 | `nm`（.symtab）看到的 GLOBAL 符号对动态链接器不可见；劫持类结论必须 `nm -D`/`LD_DEBUG=bindings` 实证 |
| 双侧对照打印验证自研层语义 | `../process/ONSCRIPTER_FIX_PLAN.md` 阶段 B | 自研库（miniSDL/NDL）是否"语义合规"最可靠的判据：与参考实现（真 SDL1.2）同打印点跑同样本对齐调用序列 |
| NEMU MMU 断言的定位法 | `../process/ONSCRIPTER_RISCV_NEMU_PORT.md` §2 | 断言前打印 pc/ra/vaddr/satp → addr2line 对内核 ELF 落到源码行 → 反推调用链；"看似页表 bug"往往 是内核逻辑（NULL pcb / stale max_brk） |
| Kconfig 修改静默失效 | 同上 §3 | 直接 sed `.config` 不触发 `autoconf.h` 重生成，须 `tools/kconfig/build/conf --syncconfig Kconfig` |
| 差分调试锁定"被替换层" | `../process/ONSCRIPTER_FIX_PLAN.md`（用户裁决） | 两世界唯一差异层=被替换层（miniSDL/NDL），应优先锁定；复用层测出问题既不可修也解释不了参考侧正常 |
| 动态指令数不是跨配置不变量（时变轮询归因法） | `../process/B3_STAGE7_RECALIB_PERF.md` §2.1 | 外设轮询（UART LSR）次数随 CPU/外设相对速度变化：retire 差 = 每轮询迭代指令数 × 轮询次数差（×3 精确吻合）；跨配置只比 IPC/cycles，不比指令数；"固定 MMIO 成本"要按频率比修正 |
| 跨配置比较必须声明时间口径（PERF 总周期 ≠ 程序窗口） | `../process/B3_STAGE8_PC_AMAT_LAYOUT.md` §1/§5 | `PERF[final] cycles` 含 boot/启动（受 bootloader 搬运影响）；microbench `Total/Scored time` 由程序自身计时、不含 boot。.text 搬 SDRAM 场景：纯 kernel −31% 而端到端 +24.8%（一次性搬运 ~5.5M cyc）——结论必须两口径并列，优化目标决定看哪个 |
| 提频收益 vs 访存等待的 Amdahl 饱和模型 | `../process/B3_STAGE7_RECALIB_PERF.md` §4 | r=f_CPU/f_APB 下访存等待 ∝r：T(α)=U/α+M·α，吞吐天花板=1/(1−p_mem)；判据是吞吐 f×IPC 而非 IPC；p_mem>0.5 时先降访存占比再提频（α*=sqrt((1−p)/p)） |
| 「逐行译码写」generate 模式的面积陷阱 | `../process/B3_STAGE8_AREA_N45.md` §4.1 | `generate for(i=0;i<N;i++) assign hit[i]=(i==idx)` 让工具复制 N 份比较器且无法共享（dcache 4×128 份）——应改直接索引写或共享 7→128 译码器；同族：FF 寄存器堆索引读=两棵 32:1×64b mux 树（18Kμm²），SRAM 宏化可省但不计面积 |
| cache 掩码/时序/PSRAM/SRAM wmask 等硬件经验 | `../../docs/DEBUG_WORKFLOW.md` §3 | 活跃文档，硬件坑汇总（现行参考） |
