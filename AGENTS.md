# AGENTS.md — 全局工作规则

本工作区（ysyx-workbench）内的开发/验证/文档任务**一律遵守** `npc/verif/docs/WORKFLOW_POLICY.md`：

1. **先产出整体计划文档并对齐**：从任务/讲义/需求清单出发必须先写《整体计划文档》（目标、范围、
   阶段划分、每阶段交付物、验收标准、结束节点、含人工决策/安装的阶段标识），**用户确认后**才分阶段执行。
2. **一次只做一个阶段，每阶段停下来**：阶段完成后向用户报告"本阶段结论/改动/验证 + 下一阶段内容"，
   **用户确认无误并 commit 后**才开始下一阶段。
3. **人工确认 / 软件安装即停**：凡涉及 `sudo`/`apt`/`pip` 等软件安装或系统级改动、以及任何需要
   人工决策/知情的取舍，**立即停下由用户操作/拍板**，用户完成后再继续。
4. **不擅自 commit、不擅自安装**；默认由用户 commit。
5. **每阶段留档**：结果写入 `npc/verif/records/` 并更新记录索引。

## Agent 上下文与文档入口

- 开始任何任务前，先读取 `.agent/` 下的 `PROJECT_CONTEXT.md`、`CURRENT_STATE.md`、
  `TASK_QUEUE.md`、`DECISIONS.md`，并按需经 `.agent/DOCUMENT_INDEX.md` 查找其他文档。
- `.agent/` 是模型无关的**镜像与导航层，不是事实权威**：技术事实以
  `npc/verif/docs/PROJECT_OVERVIEW.md` 及各活跃计划 / `records/` 记录为准；任务状态以
  PROJECT_OVERVIEW §3、`LINUX_PLAN.md`、`ARCH_OPT_BACKLOG.md` 为准，不自行推定完成。
- 完成重要修改后同步 `.agent/CURRENT_STATE.md`；产生新决策时更新 `.agent/DECISIONS.md`；
  文档增删移动时更新 `.agent/DOCUMENT_INDEX.md`；长期任务进展同步 `.agent/TASK_QUEUE.md`。
- 文档入口链：根 `README.md` → `npc/README.md` → `npc/verif/README.md` →
  `npc/verif/docs/PROJECT_OVERVIEW.md`。

> 遵循项目既有约定与文档（见 `npc/verif/` 下入口文档）。改动最小、可回滚、不引入无关改动。
