# AGENTS 规则职责整理（2026-10-18）

## 整体计划

- 来源：用户要求结合代码正确性修复流程优化 AGENTS.md，把任务专用语句迁至合适位置，并同步引用及状态入口。
- 目标：全局规则承载稳定行为与生命周期；CRP 专用规则有单一现行入口；移动后恢复、验证、留档和提交门槛均可追溯。
- 范围：AGENTS、WORKFLOW_POLICY、CRP 流程/修复计划、records 索引及受影响的 .agent 导航。仅文档维护，不推进业务 Phase 或功能修复，不改历史验收事实、源码、测试、跟踪规则。
- 阶段：一个维护单元，依次盘点与分类 → 迁移/改链 → 检查/留档；同轮执行至完成，不另立业务 Phase。
- 交付：本计划与结果、CRP 专用流程、精简后的全局规则、更新后的引用和状态。
- 验收：原要求逐条有去向；现行引用无断链；历史记录仅追加迁移说明；CRP 唯一下一入口及各任务确认/提交状态一致；Git 差异仅本批文档，无暂存/提交。
- 结束节点：完成文档检查和记录后停止，等待用户确认/提交；不启动 F0037/F0038 或 M2。
- 人工决策/安装：当前无真实未决策略、无安装或系统改动。需要改变既有契约时另行提出，不从职责迁移推定策略获批。

## Guard 与起始状态

根分支 boot_linux，HEAD `862f4de26c161d91c13d2926e964a904275d051a`，普通工作树/index 干净。
前次测试精简维护已确认/提交；F0037/F0038 为唯一未来修复批次、尚未开始；M2-P1 未 Start。
本轮用户明确授权规则维护，解释与原“继续修复”入口的任务切换，无状态冲突。
`.agent`、WORKFLOW_POLICY、REPAIR_AND_REGRESSION 仍按既有本地忽略约定维护；新流程采用普通可跟踪的 README 路径，不改 ignore。

## 分类结论与迁移映射

| 原位置 / 内容 | 判断与现行落点 |
|---|---|
| AGENTS 全局第6条；WORKFLOW_POLICY §5：Make 接口与日常流程保留 | 代码正确性修复的兼容性约束，迁至 [CRP 构建接口](../workflow/README.md#build-interface)，保留冲突裁决条件 |
| AGENTS“修复测试代码与证据的提交范围”；WORKFLOW_POLICY 同类节 | 修复证据入库策略，迁至 [CRP 测试与证据](../workflow/README.md#test-artifacts)，原3条完整保留 |
| AGENTS“修复批次的组织”；WORKFLOW_POLICY“修复批次” | CCR-F / CQ 与逐项回归专用，迁至 [CRP 合批](../workflow/README.md#batching)，原4条完整保留 |
| AGENTS“继续”第6条；既有模块回归约定 | guest/host、真实消费者和失败判据属于修复验收，集中到 [CRP 验证](../workflow/README.md#validation)，保留来源与适用边界 |
| AGENTS“继续”第1/2/4/5条中的“修复”限定 | 授权续作、独立阻塞、唯一入口属于通用协议，泛化为当前主线/独立任务；不重排全量问题等细则留在 CRP |
| AGENTS 状态架构固定引用 Linux 计划；TASK_QUEUE 顶部及 Rules 的同类限定 | 改为沿任务条目定位权威计划，不让独立 CCR/CRP 的范围误受 Linux 计划限定；Linux 既有业务入口原位保留 |
| 每轮执行与提交收尾、Guard、恢复/完成/重开/Handoff、状态职责和本地持久化 | 跨任务稳定规则，保留在 AGENTS；本轮交互不新增 Phase，用户“提交”授权及确认/提交分离语义不变 |
| AGENTS 中规则归属；WORKFLOW_POLICY 同类入口 | 补通用要求：任务专用约束由队列必读入口指向，迁移必须同步现行引用和状态，不复制细则 |

## 引用与状态闭环

现行路径为 AGENTS → CURRENT_STATE → TASK_QUEUE / `crp-next` 的 Read First → CRP workflow → 修复计划/逐项证据。
修复总计划顶部、process 索引、DOCUMENT_INDEX 均增加直接入口；不新增第二个 Next。
CRP workflow 的状态收尾节指回 records 索引、CURRENT_STATE/TASK_QUEUE 与全局生命周期规则，确保执行后仍更新原状态体系。

历史记录保持原路径和事实：修复计划、前次维护报告、process 索引及 DOCUMENT_INDEX 追加迁移说明，CHANGELOG 仅追加本次维护结果。
F0051/F0085 对 AGENTS“继续”第4条的引用仍有效，该条编号和裁决/提交停点保留。
既有已修4项/剩余115项含5CQ、前批确认/提交与 M2 状态不变。
本轮维护 Completed；结果确认/commit Pending。F0037/F0038 保持 Planned，先完成本轮文档收尾门槛，再由后续授权恢复。

## 验证与限制

文档检查包括迁移条款逐项保留、变更链接的路径/锚点解析、旧章节引用检索、唯一入口及状态门槛检查、Git 差异/空白/暂存区检查。
检查命令与结果保存于本目录本地 `validation.json`，检查脚本为本地 `check.local`；它们是一次性文档检查材料，不纳入提交。
未执行产品构建或 host/guest 回归：只改文档，既有产品验收不重跑、不扩写。

根 HEAD 仍为 `862f4de`，本轮未 commit/push，无安装或系统改动。
新增流程和本报告采用现有可跟踪 README 路径；WORKFLOW_POLICY、修复总计划和 .agent 仍为本地忽略资产，未改 ignore 或强制纳入跟踪。
本轮完成后停止，等待确认/提交，不开始功能修复或业务 Phase。

验收结果：`python npc/verif/records/process/code_correctness_review/agent-policy-maintenance-20261018/check.local`
退出0，15项检查通过，75个本轮相关链接/锚点有效；`git diff --check` 通过，index 空，HEAD 未变化。
初检发现构建条款的一处同义改写影响逐字比对，以及检查脚本被现有 Python 白名单识别为可跟踪；
已恢复条款原文，并将一次性脚本改为本地忽略的 `check.local`，未改任何 ignore 规则。复检全部通过。


### 2026-10-18 确认与提交授权补充

用户“提交当前改动，并且继续CRP修复任务”确认本批已报告的规则维护范围并授权提交，另授权提交后执行唯一入口的 F0037/F0038 一个修复批次。复用上轮15项/75链接文档验收，本轮 `git diff --check` 通过，核对5份可跟踪文档范围，无新增产品测试。实际提交回执保存在本目录本地 `commit-receipt.json` 及 .agent；原完成记录保留，忽略资产不随提交备份。
