# CCR-P10 最终证据审计

> 最新用户处理方向与提交补充见[closeout-20261017](closeout-20261017/README.md)；下方是原P10交付截面。

2026-10-17。入口：[P10](../P10.md)、[FINAL_REPORT](../FINAL_REPORT.md)。仅核对现有身份、证据、覆盖与记录；不运行生产代码、项目make或旧阶段validator。用户两缺源验收豁免见[acceptance-waiver.json](acceptance-waiver.json)。结构检查PASS不能证明代码不存在缺陷。

| 文件 | 用途 |
|---|---|
| baseline.json、*.before.gz | P9提交后、P10开始前13份共享输入快照；原hash可验证，不能由后续报告反推历史 |
| audit.py / audit.log | P1同范围重枚举、hash/mode/链接目标、嵌套repo、历史manifest、119问题位置与证据存在性 |
| identity-audit.json | 15,240身份、14,971保护输入、10嵌套repo检查与已知deleted/missing差异 |
| manifest-audit.json | 10份历史manifest / 1,202引用；共享文档演进不等于生产漂移 |
| findings-audit.json | 119条原对象hash、所有位置有效性/源码SHA/证据hash |
| coverage-audit.json | P10补充前原总状态语义；原文件/条件状态计数和5个X01缺阶段字段 |
| RECONCILIATION.md | 数量更正、X01/P2/P8责任映射、历史差异与根因归并依据 |
| reconcile.py | 从冻结baseline附加最终字段和生成最终表；只组装记录，不能代替人工审阅；未来不得直接覆盖新阶段成果 |
| final-coverage.jsonl / coverage-summary.json | 40,010稳定行最终裁定与52模块统计；保留2 Unavailable |
| repair-priority.json | 119项修复建议分组/回归入口；未实施，不是新授权任务 |
| validate.py / validation.json / validation.log | 最终一致性、范围豁免、证据/状态/文件保护检查；代码动态验证NotRun |
| validation-initial.json / validation-initial.log | 首轮56项通过、仅2个指向尚未生成validation.json的自引用报错；校验器修正输出自引用顺序后终检，非产品缺陷 |
| manifest.json | P10交付、当前共享资料与引用证据hash；不包含自身hash以避免递归 |

本轮执行（工作目录为仓库根）：

```text
python3 npc/verif/records/process/code_correctness_review/p10/audit.py > npc/verif/records/process/code_correctness_review/p10/audit.log
python3 npc/verif/records/process/code_correctness_review/p10/reconcile.py
python3 npc/verif/records/process/code_correctness_review/p10/validate.py > npc/verif/records/process/code_correctness_review/p10/validation.log
git diff --check
```

reconcile曾先于最终audit执行；两脚本不运行产品。后续复验必须先保存新检查点并使用新输出目录，不能盲目重写本次静态快照。阶段P3无单独manifest，按原静态记录/源证据核对；历史manifest允许的共享资料与P1升级/P4及P8回执变化见RECONCILIATION。

Final Gate：按用户两处缺源验收豁免闭合CCR；原无豁免全范围标准未满足。119问题未修、5CQ未决；不进入修复/M2，不自动提交P10。多数MD/JSON/日志/.agent被忽略；可跟踪README和审计脚本提交不包含全部证据。

<a id="p10-followup-policy-20261017"></a>
## 最终用户意见 / 提交补充

用户要求未决项按正式Linux M阶段需求再落档，当前优先修复已完成工作的明确问题，并授权最后更新和提交。实际执行边界见[统一处理原则](../LIMITATIONS_AND_DECISIONS.md#p10-followup-policy-20261017)，批准/提交见[P10](../P10.md#p10-final-approval-20261017)。原audit/validate/reconcile及manifest/closure不重生成；本次增量见[补充证据](closeout-20261017/README.md)。
