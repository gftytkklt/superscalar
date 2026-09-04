# records/knowledge —— 经验性归档（案例复盘 / 方法论 / 性能分析）

> 可复用的"怎么做/为什么"：独立成篇的经验文档 + 指向各过程文档中方法论章节的**经验地图**。
> 过程时间线见 [`../process/README.md`](../process/README.md)；入口总览见 [`../../PROJECT_OVERVIEW.md`](../../PROJECT_OVERVIEW.md)。

## 独立成篇

| 文件 | 主题 | 要点 |
|---|---|---|
| `rtthread-stackoverflow-debug.md` | 案例复盘：RT-Thread 栈溢出（NEMU 平台） | 现象→定位→验证→修复的完整链路；根因是 main 线程栈溢出破坏对象链表，非 NEMU bug——"看似模拟器问题实为软件 bug"的典型样本 |
| `MEM_PIPELINE_OPT.md` | 访存流水线性能分析与优化方向 | 架构分析/瓶颈定位方法/验证策略/优化方向/浪费点清单——**支撑未来目标"NEMU+NPC 双端 Linux + NPC 持续性能优化"的方法底座**（当前阶段 B3 调优在此基础上推进） |

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
| cache 掩码/时序/PSRAM/SRAM wmask 等硬件经验 | `../../DEBUG_WORKFLOW.md` §3 | 活跃文档，硬件坑汇总（现行参考） |
