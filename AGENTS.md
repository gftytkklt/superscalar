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

`.agent/` 是模型无关的镜像、恢复与导航层。技术事实以项目代码、活跃计划及 `npc/verif/records/` 证据为准；阶段范围和验收沿用 `LINUX_PLAN.md`、`LINUX_M1_PLAN.md`、`ARCH_OPT_BACKLOG.md`。用户最新明确指令优先于旧状态文字；记录其来源，不能从文件存在、测试通过或 context compression 自行推定阶段获批。

### Architecture Principle — 状态文件职责

| 文件 | 唯一主要职责 |
|---|---|
| `AGENTS.md` | Stable behavior：稳定行为、生命周期协议、状态管理规则 |
| `.agent/PROJECT_CONTEXT.md` | Project knowledge：长期项目背景、架构与核心知识 |
| `.agent/CURRENT_STATE.md` | Current execution state：当前执行检查点与 Active Execution Context |
| `.agent/TASK_QUEUE.md` | Future work：Milestone → Phase → Task 的未来工作、依赖与入口 |
| `.agent/CHANGELOG_AGENT.md` | Historical completion：已完成 Phase / Milestone 的历史快照 |
| `.agent/DECISIONS.md` | Durable technical rationale：具有长期影响的架构/技术决策及理由 |
| `.agent/DOCUMENT_INDEX.md` | Document navigation：重要文档索引与用途 |

同一信息以职责文件为主，其他文件仅保留必要摘要或链接，避免重复保存同一内容。保留现有文件、稳定 ID 和历史路径；协议升级不要求重写历史或重建快照。

## Agent Lifecycle Protocol

以下协议细化 `WORKFLOW_POLICY.md`：新工作仍须计划先行；已规划任务的恢复、开始与完成使用本节入口，不因生命周期操作重新立项、重规划 Milestone 或全仓扫描。所有生命周期操作前先执行下述 Guard，并遵守完成/批准/提交门槛和持久化规则。

### State Consistency Guard — 状态读取与转换前检查

1. 轻量核对顺序：当前 Session 明确上下文 → `CURRENT_STATE`（优先 Active Execution Context）→ `TASK_QUEUE` → 当前 Git/working tree。其他 `.agent` 文档、相关代码与产物仅在需要时读取；不默认全仓扫描或重跑已验收测试。
2. `Completed`、用户确认和 commit 分开记录；未提交可以 Completed，`Next` 仅是队列入口。Milestone 完成须独立核对总体验收，不能从单个 Phase 或压缩恢复推定。
3. 若用户声明、Session、状态文件或工作区存在无法由当前明确上下文解释的冲突，暂停生命周期转换，输出 **State Consistency Conflict**：用户声明状态、`.agent` 记录状态、当前工作区状态、冲突位置、建议确认事项。不能猜测或自动覆盖任何一方；能由明确上下文解释时，说明依据再继续。
4. 缺失资料按导航入口定向找回；不能证明的验收/批准/提交写 Unknown，说明影响下一动作的缺失信息，不能以扩大探索代替澄清。
5. 重复调用须先核对已有结果。同一 Phase/Milestone 的完成快照已存在且无新事实时，复用记录并简短报告，不重复归档。部分完成只补缺失步骤；新确认、提交或更正用引用原 ID/锚点的补充记录，不重写原快照。

### Project Resume

用于新 Session 接管：先读 `AGENTS.md` → `CURRENT_STATE` → `TASK_QUEUE`，执行 Guard；按当前任务需要读取 `PROJECT_CONTEXT`、`DECISIONS`、`DOCUMENT_INDEX` 与 `CHANGELOG_AGENT` 的相关部分，不强制读全六件。

恢复 Current Milestone、Current Phase、Current Objective、Last Completed Action、Next Action、Known Risks / Blockers；只读取继续任务必需的代码/文档。通常只读，不修改 `.agent`。输出简短 **Project Resume Report**，随后按已有明确授权继续；无待执行授权则等待。

### Phase Start

1. 用 `Mx-Py` 定位 `TASK_QUEUE` 的目标 Phase、Goal、Tasks、依赖和相关计划；队列是摘要时沿链接补齐该 Phase 的验收与停点，不重新规划整个 Milestone。
2. 核对上一 Phase 已完成、获用户确认且已 commit，以及目标 Phase 的执行授权。提前进入或豁免必须有用户明确指令，并记录原因/来源；不能仅凭 Next 放行。
3. 边界和门槛满足后，按需读取知识与代码，更新 `CURRENT_STATE` 的 Milestone、Phase、Current Objective、Last Completed Action、Current Working Files、Next Action、Blocked By，并同步队列活动状态；无阻塞写无。
4. 只执行已规划的本 Phase，按其验收和停点结束。

### Phase Completion — 正式持久化边界

用户声明 `Mx-Py` 完成或已授权的 Phase 到达完成边界时，先执行 Guard 并检查既有完成记录，按编号定位原计划与验收证据，再依据 Session、实际修改、验证结果与当前状态盘点：

| 文件 | 本次完成需持久化的内容 |
|---|---|
| `CURRENT_STATE` | Current Milestone、Completed Phase / Status=Completed、已完成工作、代码/working tree、Last Completed Action、Remaining Work、Known Risks、Next Phase / Next Action；修改未提交时明确写“Working tree contains uncommitted Phase changes”或等价表达 |
| `TASK_QUEUE` | 当前 Phase 标记完成，清理完成 Task，下一 Phase 设为 Next；保留未完成/延期项及归属。仅保留依赖所需的完成状态/快照链接，完整历史放 CHANGELOG |
| `CHANGELOG_AGENT` | 追加不可变式 Phase Completion Snapshot：Milestone/Phase、Date、Goal、Completed Changes、Modified Files、Debug / Technical Findings、Tests / Validation、Problems Solved、Remaining Risks、Next Step；同时记确认来源、HEAD/Commit State、Next Entry/Gate 与恢复资料。只写事实结果，区分本次测试与历史证据，不堆调试过程 |
| `DECISIONS` | 仅有新的长期架构决策、接口契约、技术策略或重要取舍时更新；沿用统一格式/稳定 ID，不记录普通实现细节、临时方案，不重复已有决策 |
| `DOCUMENT_INDEX` | 仅重要文档新增、删除或职责明显变化时更新；不因完成事件自动重写 |

技术证据仍按既有 `records/` 流程保存，按实际影响更新项目计划/索引；模板见 `.agent/CHANGELOG_AGENT.md`。输出简短 **Phase Completion Report**：Completed Phase、State Updated、Validation Result、Remaining Risks、Next Phase。核对完成/确认/提交/下一阶段状态一致后停下；除非用户明确要求，不 commit、不开始下一 Phase。

### Phase Reopen

用于刚完成 Phase 在 review、验证、讨论或进一步检查中发现范围内问题后的重新打开。

1. 先执行 State Consistency Guard；必须同时满足：目标 Phase 已执行 Phase Completion、下一 Phase 尚未执行 Phase Start、新问题属于该已完成 Phase 的目标/实现/验收范围。不满足或无法确认时，报告状态与未满足条件并等待确认，不自动 Reopen；冲突按 Guard 处理。
2. 将 `CURRENT_STATE` 的 Active Execution Context 恢复到目标 Phase，使用既有状态 `Active（Reopened / In Progress）`；记录 reopen 原因及原完成记录链接，更新 Current Objective、Current Working Files、Next Action 和必要的未完成项，保留真实的 Last Completed Action。
3. `TASK_QUEUE` 同步该 Phase 为 `Active（Reopened / In Progress）`，补入待修复任务；下一 Phase 保持 `Pending（Planned，未开始）`，不得启动。本轮新增修改仍归属于 reopened Phase。
4. 保留原 `CHANGELOG_AGENT` Phase Completion Snapshot，不删除、覆盖或改写。只读取问题相关代码、文档和必要状态，不重新规划 Milestone 或默认全仓扫描；Reopen 本身不产生 Decision，仅实际形成长期决策时更新 `DECISIONS`。
5. 补充修改完成后必须再次执行 Phase Completion，不能用旧快照代替本轮验收：`CURRENT_STATE` 与 `TASK_QUEUE` 恢复该 Phase 为 Completed，下一 Phase 恢复为 Next；在 `CHANGELOG_AGENT` 追加 **Supplemental / Reopened Phase Completion** 记录，引用原完成记录，说明 reopen 原因、补充修改、验证结果及剩余风险，保留第一次 Completion 历史。
6. 重新完成后仍须满足既有用户确认、commit 和下一 Phase 执行授权门槛；原确认/commit 不自动覆盖本轮新增修改。

### Context Recovery — context compressed 处理

context compression 本身不触发恢复、Completion 或 Handoff。若 Milestone、Phase、Current Objective、Next Action 仍清楚，直接遵循原授权与停点继续。

不确定时先读 `CURRENT_STATE`、`TASK_QUEUE`，结合保留的 Session 执行 Guard；必要时才读其他 `.agent` 或任务相关资料，恢复目标与下一动作。信息足够则从该动作继续（已完成 Phase 仍遵循等待门槛）；不足则说明缺失/冲突，不大规模探索。

恢复本身不写 CHANGELOG、不制造 Decision、不修改历史。压缩不要求再次确认或开启新会话。`WORKFLOW_POLICY.md` §6 只在上下文确实影响任务质量时触发其风险交接/停点；这种续作交接也不等于 Phase Completion 或 Milestone Handoff。

### Task Resume

用于 usage limit、Agent interruption、IDE restart、temporary failure 或用户暂停后的续作。执行 Guard，核对已完成操作、已改文件、已跑测试、未完成步骤与 Next Action；Session 足够时直接从中断处继续，否则结合 `CURRENT_STATE`、`TASK_QUEUE` 与 working tree 定向恢复。

原授权在其范围内持续有效，停点仍有效。重试写入、commit 或长任务前先检查是否已生效、进程是否仍在运行；部分完成只补缺失部分，不从头执行原 Prompt。Task Resume 本身不生成完成快照。

### Milestone Handoff — 最高级持久化边界

1. 用 `Mx` 定位既有计划和队列，核对所有必要 Phase、独立的 Milestone 总体验收及获准延期/排除项，执行 Guard。证据不全不能标记 Completed。
2. `CURRENT_STATE` 标记 Milestone Completed，记录最终状态、最后执行结果及下一 Milestone 入口/启动条件；`TASK_QUEUE` 清理该 Milestone 完成任务，保留必要摘要/快照链接、延期项及归属，将下一 Milestone 设为未来入口。
3. `CHANGELOG_AGENT` 追加 **Milestone Completion Snapshot**（沿用 Milestone Handoff 模板/锚点）：Goal、Completed Phases、Major Changes、Validation / Tests、Important Findings、Remaining Risks、Next Milestone Entry；包含最终配置/产物路径与哈希、关联决策、分支/HEAD/提交状态、恢复材料。
4. 确认长期决策已录入 `DECISIONS`，不重复记录；`PROJECT_CONTEXT` 只同步确已变化的稳定事实；`DOCUMENT_INDEX` 仅实际文档结构/职责变化时更新。保留历史路径。
5. 输出 **Milestone Handoff Report** 后停下，除非用户明确要求，不 commit、不自动开始下一 Milestone。

### State Persistence Policy

- 优先在语义边界持久化：Phase Completion、Milestone Handoff、长期架构决策、必须跨 Session 保存的重要问题解决结果；写入对应职责文件，不为每类边界都创建完成快照。
- 不在每次代码编辑/测试后更新 `.agent`；短暂尝试、失败命令和临时推理留在 Session。压缩本身不触发完整 Handoff。
- 中断前确有未完成动作需要保存时，可更新 Active Execution Context 的最后完成动作、工作文件、Next Action、进程/输出路径、授权与停点；只写检查点，不把启动中的操作记为完成。
- `.agent/` 为 git 忽略的本地资料。长期冷启动/交接须携带本地记录、工作区外资产或可复现配方；commit 不等于备份这些资料。未经授权不改跟踪规则、不上传。
- Agent 管理维护不占用或推进业务 Milestone/Phase；协议迁移不回填或重复已完成事件。

### Minimal Lifecycle Commands

| 操作 | 用户短指令 |
|---|---|
| Project Resume | `接管当前项目。执行 Project Resume。` |
| Phase Start | `开始 Mx-Py。执行 Phase Start。` |
| Phase Completion（未提交） | `Mx-Py 已完成，修改尚未 commit。执行 Phase Completion。` |
| Phase Completion（已提交） | `Mx-Py 已完成并已 commit。执行 Phase Completion。` |
| Phase Reopen | `重新打开 Mx-Py。执行 Phase Reopen。` |
| Phase Completion（重新完成） | `Mx-Py 补充修改已完成。执行 Phase Completion。` |
| Context Recovery | `执行 Context Recovery，然后继续当前 Phase。` |
| Task Resume | `执行 Task Resume，从最近有效状态继续。` |
| Milestone Handoff | `Mx 已完成。执行 Milestone Handoff。不要开始下一 Milestone。` |

这些指令只触发协议事件，所需范围/验收从当前状态与已有计划定位，不要求用户重述规则；不能跳过 Guard、提交门槛或用户停点。

文档入口链：根 `README.md` → `npc/README.md` → `npc/verif/README.md` → `npc/verif/docs/PROJECT_OVERVIEW.md`。

> 改动最小、可回滚、不引入无关改动。
