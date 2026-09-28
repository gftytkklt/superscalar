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

## Agent 状态架构（Schema Version: 2）

`.agent/` 是模型无关的镜像、恢复与导航层。技术事实以项目代码、活跃计划及 `npc/verif/records/` 证据为准；阶段范围和验收沿用 `LINUX_PLAN.md`、`LINUX_M1_PLAN.md`、`ARCH_OPT_BACKLOG.md`。用户最新明确指令优先于旧状态文字；记录其来源，不能从文件存在、测试通过或 context compressed 自行推定阶段获批。

### 状态读取规则

1. 每次冷启动先读 `AGENTS.md`，然后读 `.agent/CURRENT_STATE.md` 的 **Active Execution Context**，定位当前 Milestone、Phase、目标、最后完成动作、工作文件、下一动作和提交门槛。
2. 再读 `PROJECT_CONTEXT.md`（长期边界）、`TASK_QUEUE.md`（Milestone → Phase → Task）、`DECISIONS.md`（有效决策/待决项）、`DOCUMENT_INDEX.md`（证据入口）和 `CHANGELOG_AGENT.md` 中当前 Phase 最新完成快照。首次进入会话须读全六件；接续时按相关段落读取。
3. 只核对恢复所需的工作树、HEAD、产物/记录是否仍在；仅在发现变更、证据缺失或具体疑点时展开源码分析或重跑验证。历史快照不覆盖当前明确指令。
4. `Completed` 表示该阶段约定交付已完成；用户确认与 commit 分别记录。未提交可以保持 Completed，但不能绕过下一 Phase 的门槛。Milestone 的完成须独立核对全部验收条件。
5. 若状态文件冲突，按最新用户明确指令、当前计划/技术证据核对，写出差异和来源；只有影响下一动作的缺失信息才需澄清。文件缺失时经索引/项目入口恢复，无法证明的状态写 Unknown，不能猜测。

### 状态文件职责

| 文件 | 职责 |
|---|---|
| `PROJECT_CONTEXT.md` | 稳定的工程背景、技术边界、事实权威和冷启动路线 |
| `CURRENT_STATE.md` | 唯一当前执行指针、Active Execution Context、工作树状态和未完成事项 |
| `TASK_QUEUE.md` | Milestone / Phase / Task 层级、状态、依赖及下一入口 |
| `DECISIONS.md` | 稳定 ID 的统一决策记录；明确有效、待决与被替代状态 |
| `DOCUMENT_INDEX.md` | 计划、证据、快照与恢复入口导航 |
| `CHANGELOG_AGENT.md` | 追加式 Phase Completion Snapshot、Milestone Handoff 与维护记录 |

### Phase 完成更新规则

1. 对照当前计划核对交付、验证范围与未完成项；运行日志/构建证据保存在既有 `records/`，更新受影响的计划和索引。历史记录通过追加更正保留原事实。
2. 在 `CHANGELOG_AGENT.md` 追加 **Phase Completion Snapshot**：Milestone、Phase、Task、Goal、Completed Changes、Modified Files、Debug Findings、Tests/Evidence、Remaining Risks、用户确认、HEAD/Commit State、Next Entry/Gate、恢复所需资料。
3. 同步 `CURRENT_STATE.md` 六项 Active Execution Context，更新 `TASK_QUEUE.md` 对应行；新增/替代决策使用 `DECISIONS.md` 统一格式，文档入口变化同步 `DOCUMENT_INDEX.md`。
4. 核对“已完成/已确认/已提交/下一阶段未开始”在各处一致。报告阶段结果与下一入口，按既有工作流停点；不因写完快照而自动 commit 或执行下一阶段。

### Milestone 完成 Handoff 规则

1. 所有计划内 Phase 的验收与 Milestone 总体验收都满足后，才标记 Milestone Completed；列出延期/排除项及其用户决策依据。
2. 追加 **Milestone Handoff**：各 Phase 结果、总体验收证据、最终配置/产物路径与哈希、关联决策、剩余问题、分支/HEAD/提交状态、下一 Milestone 入口和放行条件。
3. 同步当前指针、队列、长期上下文中确已变化的稳定事实及导航；保留原有计划和 records 路径，避免历史链接失效。
4. `.agent/` 当前为 git 忽略的本地资料。交接列明本地文档与工作区外构建资产的保存位置；跨机器/新 checkout 接续需携带这些资料或可复现配方，不能把 commit 当成已备份本地档。未经授权不改跟踪规则、不上传资料。

### context compressed 处理规则

- 上下文压缩前，能写入时先更新 Active Execution Context：特别是 Last Completed Action、Current Working Files、Next Action、未完成动作、运行中进程/输出路径、有效授权和停点；不把启动中的操作记为完成。
- 压缩后先恢复 CURRENT_STATE，再核对 TASK_QUEUE、相关决策和最新 Snapshot。保留原目标与用户最新修正，从未完成动作继续；不重新立项、不重做已验收工作，不把 P3 的 Next 状态当成已获执行许可。
- 工具调用可能在压缩前已生效；重试修改、提交或长任务前先检查结果。原有授权持续有效；压缩本身不要求再次确认或开启新会话。
- 若已触发 `WORKFLOW_POLICY.md` §6 的高风险上下文交接条件，则按该条件留档/停点；普通压缩恢复不能替代必要的证据核对。

文档入口链：根 `README.md` → `npc/README.md` → `npc/verif/README.md` → `npc/verif/docs/PROJECT_OVERVIEW.md`。

> 改动最小、可回滚、不引入无关改动。Agent 管理维护不占用或推进业务 Milestone/Phase。
