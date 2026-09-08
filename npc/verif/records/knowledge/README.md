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
| `FORMAL_VERIFICATION_NPC.md` | **形式化验证入门**（SymbiYosys+Yosys+SMT/sby+z3/btormc，新手友好） | assume/assert/cover 三角色、bmc/cover 两模式、depth/mode/solver 关键参数含义、REF-vs-DUT 等价思想、完整编译链（trim_rtl.py→vsrc_fm.v→sby→yosys-smtbmc→z3/btormc）、文件清单、五大坑（BMC 任意初态/空泛 PASS/规模先测/宽位用 boolector/REF 别带真实存储）+ 新手起步路径；**§10 含 div/axiburst/icache 三案例分析**（各讲验证目标→假定条件→判定方法→结论/坑，附选型对比表） |

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
| cache 掩码/时序/PSRAM/SRAM wmask 等硬件经验 | `../../docs/DEBUG_WORKFLOW.md` §3 | 活跃文档，硬件坑汇总（现行参考） |
