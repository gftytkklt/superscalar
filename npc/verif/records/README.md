# npc/verif/records —— 归档区（历史调试过程与经验记录）

> **归档说明（2026-09-04 重组）**：本目录为纯归档区，按文档性质分两类存放：
>
> | 子目录 | 性质 | 内容 |
> |---|---|---|
> | [`process/`](./process/) | **日志型** | 阶段实施记录、调试过程时间线、任务提示词（续作 PROMPT）、修复计划——按时间顺序叙述"当时做了什么" |
> | [`knowledge/`](./knowledge/) | **经验性** | 案例复盘、方法论沉淀、性能分析——可复用的"怎么做/为什么"，独立于具体时间线 |
>
> **当前活跃文档**（入口/工作流/运行速查/测试体系/当前阶段 B3）在上级目录 `npc/verif/`，
> 总入口见 `../PROJECT_OVERVIEW.md`（含"现状与目标"：NEMU+NPC 双端启动 Linux、NPC 持续性能优化）。
> 新阶段的产出按 `../WORKFLOW_POLICY.md` §4 落档：过程记录入 `process/`，提炼的经验入 `knowledge/`，
> 并同步更新对应 README 索引。

## 索引

- **日志型归档索引**：[`process/README.md`](./process/README.md) —— STAGE1~3 / STAGE_F / STAGE_I / STAGE_J0–J5 /
  STAGE_H_ONWARDS / ONScripter 全系列（含 PROMPT 与计划）
- **经验性归档索引**：[`knowledge/README.md`](./knowledge/README.md) —— RT-Thread 栈溢水案例复盘、
  访存流水线性能分析、跨文档经验地图（指向各过程文档中的方法论章节）

> 历史注记：本目录前身为"分阶段调试过程记录（归档）"，2026-08-31 集中归档于 verif/ 根目录，
> 2026-09-04 拆分为 process/knowledge 两区并将 B3 活跃文档上移至 `npc/verif/` 顶层。
