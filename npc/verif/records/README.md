# npc/verif/records —— 分阶段调试过程记录（归档）

> 历史调试过程/交接文档。**主工作流与各阶段结论以 `../DEBUG_WORKFLOW.md` 为准**（§4 阶段执行记录、
> §5 启动流程）。此处保留各阶段更原始/更详细的排查过程，便于回查，不再单独维护。
> 集中归档于 2026-08-31（原在 verif/ 根目录）。

| 文件 | 阶段/主题 | 要点 |
|---|---|---|
| `STAGE1_CACHE_REWORK.md` | 缓存重构 + SoC 访存接口适配 | cache AX/X 耦合点 C1–C8、dcache 写分配掩码、fence.i/cacheline 写回 bug、验证体系（注：末尾含一段"阶段2"草稿，与 STAGE2 重叠） |
| `STAGE2_MEM_IF.md` | 阶段2 访存接口重构设计基线 | CPU↔cache 接口、AXI burst/MMIO 生成、slave_crossbar、SoC 地址映射、重构实施计划 S0–S5 |
| `STAGE3_PSRAM_READDBG.md` | 阶段3 PSRAM 读回错位调试 | flash 数据通路修复、PSRAM 读回逐级定位、根因=dcache 写分配掩码 |
| `STAGE_F_RTTHREAD_PROMPT.md` | 阶段 F 任务提示词 | RT-Thread 在 PSRAM 执行的原始任务说明（结论见 DEBUG_WORKFLOW 阶段 F 记录 + §5） |
| `rtthread-stackoverflow-debug.md` | RT-Thread 栈溢出调试（NEMU 平台） | 现象→定位→验证→修复：根因是 main 线程栈溢出破坏对象链表，非 NEMU bug |

> 阶段 D/E/F/G 的最终结论、坑与修复已固化进 `../DEBUG_WORKFLOW.md` §4（阶段 A–G 记录）与
> §5（启动流程）；`VERIF_TESTS.md`（测试体系）仍在 verif/ 根目录，作为现行参考。