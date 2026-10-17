# CRP 维护：既往测试入库精简与修复批次规则

> 最新：用户2026-10-18“提交”已确认本轮维护结果并授权提交；实际提交回执保存在本地closeout-20261018及.agent。下方原执行/未提交截面保留。

2026-10-18。授权来源：用户要求“如果前面执行的修复也有同样的冗余代码提交问题，也直接在此解决”，并明确批次可包含相近的一组问题。本轮属于既有CRP管理维护，不占用/推进业务Milestone，不重开已验收修复；HEAD14ca16c，开始根工作树/index干净，无状态冲突。

## 本轮计划与边界

- 目标：定向检查F0015/F0052/F0051已跟踪的修复测试，保留必要回归源，将一次性/生成材料移出索引并保留原路径字节；同步批次组织规则及唯一下一入口。
- 范围：三个修复记录目录的测试跟踪/局部.gitignore和报告附记，AGENTS/WORKFLOW_POLICY、REPAIR_AND_REGRESSION、records索引及.agent；四项生产修复实现和既有嵌套差异保持。
- 顺序：盘点与分类→精确移出冗余跟踪/本地保留→更新合批规则与队列→核对原字节/生产hash/索引差异/链接并留档；均为本轮一个维护单元，不另立业务Phase。
- 验收：16份测试源逐项归属明确；12份冗余移出索引、4份必要源保留；原测试字节及四项生产实现SHA不变；仅预期索引删除，链接可恢复；未来批次按逐问题验收，不跨未决策略/原Phase门槛。
- 停点：完成维护报告后停止，用户确认/提交Pending。本轮无新commit/push授权，不开始F0037/F0038功能修复，不安装/下载，不改全仓ignore或改写历史commit。无需新增策略裁决。

本地baseline.json保存原跟踪清单、精确保留/移出集合及全部源/生产SHA；本目录仅README和.gitignore入库，原始JSON留本地。

## 本轮结果：维护Completed，确认/提交Pending

四项生产修复均保持原字节；已修4项、剩余115项含5CQ不变。未开始新功能修复，无commit/push。
本次用户明确授权是对上轮“默认不追溯”规则的例外；不改写历史commit，不清理CCR原始审阅测试。

| 批次 | 保留跟踪的必要回归源 | 本轮处理与依据 |
|---|---|---|
| F0015 | harness.c、run.py | 43项固定比较/调用链/skip恢复回归，可独立重复、覆盖真实比较函数和错误传播，保留最小两份源；原输出/源码副本本地忽略 |
| F0052 | check.py | 28项真实递归Make下的PASS/XFAIL/工具失败/零结果判据回归，有防假PASS价值；fake后端由脚本在临时目录生成，无需重复入库 |
| F0051 | implementation/check.py | 13项生成器工具失败/发布保护回归，可对指定生成器重复执行；原版探针、一次guest采集和生成C/mk属于阶段证据，不作为长期测试源 |
| F0085 | 无新增测试代码 | 上轮已仅保留README/局部忽略规则，本轮无需重复清理 |

本次16份既有测试源中保留4份，以下12份从待提交索引移除，合计434行；全部原路径本地保留：

- `implementation/guest_run.py`
- `last-copy-missing.c`
- `last-copy-missing.mk`
- `make-fails.c`
- `make-fails.mk`
- `nm-fails.c`
- `nm-fails.mk`
- `objcopy-fails.c`
- `objcopy-fails.mk`
- `probe.py`
- `success.c`
- `success.mk`

三个批次新增局部.gitignore，F0051另在implementation内限定放行check.py及规则自身；README仍保留。
所有保留/移出文件原SHA记录在baseline.json。报告内原技术证据链接不变，本地仍可使用；
干净checkout不带这些本地证据，历史提交4ab9f3f仍可恢复F0051原跟踪材料；没有重写或清除Git历史。

## 合批规则与下一入口

原总计划已有R0–RQ技术分组及按调用链处理的思路；最近实际队列连续按单问题安排，
未显式把“同一工作单元可含多问题”及合批边界写清。本轮已在AGENTS/WORKFLOW_POLICY补齐：
同模块/调用链或共同根因、契约明确、依赖兼容、改动与验证可控时由agent组织小批次，
逐问题列范围/失败语义/验收，共享受影响真实回归，批次统一收尾；不跨原Phase门槛、不代裁CQ。

具体未来集合、选择依据、必读资料、门槛和逐项/共享验收只在
[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)维护，其他索引引用即可。
这次未来入口选取同一klib stdlib.c的malloc与atoi两项：前者内存安全优先，后者词法修复增量小，
可共享klib构建/真实消费者回归，且不依赖free回收CQ；两项分别验证，不互相替代。
其他helper ABI、C++运行时及能力项不因同属klib就进入本批。当前仅计划，尚未实施。

## 验证、工作树与停点

- 16份原测试文件逐字节SHA全部不变，12份移出者仍存在本地且命中局部ignore，4份保留源仍在索引且不被ignore。
- 四项原生产修复实现SHA不变；暂存区精确为12份预期删除，无额外文件，unstaged为规则/报告/索引维护。
- diff及cached diff空白检查通过。新增/附记链接与当前队列入口定向核对；无产品功能变化，复用历史验收，不重跑guest或host功能测试。
- baseline.json、validation.json和manifest.json保留本地；报告及局部.gitignore可入库，完整文件/状态清单可据此恢复。

HEAD14ca16c，Working tree contains uncommitted maintenance changes；12份索引删除仅为本轮有意准备，
不表示已经提交。结果确认/commit Pending；后续收到提交指令时仅提交本轮可归属维护改动，
复用本次收尾，不重复阶段完成/归档。没有安装、系统改动、commit/push或M2推进。

## 2026-10-18 确认与提交收尾

用户最新“提交”确认已报告的12份冗余移出跟踪、保留4份必要测试及多问题合批规则，授权提交本轮可归属维护改动。
本次复用原维护结果，核对原manifest和16份测试/四项生产SHA无漂移；只补确认/实际回执，不重跑产品验证、
不重复维护完成事件。提交包含12份索引删除及规则/局部忽略/报告/索引；所有移出者本地原字节保留，
历史commit不重写。实际提交/工作树核对记录在closeout-20261018，.agent保存确认和门槛解除状态。
本次提交不授权push或执行下一功能批次，提交后停止；原始JSON/本地移出材料/.agent不因此获额外备份。


### 2026-10-18 规则现行入口补充

本记录中的 AGENTS/WORKFLOW_POLICY 为当时规则落点，历史结果与提交不改写。
现行合批和测试证据提交条款已迁至 [CRP 执行流程](../workflow/README.md#batching)及其[证据范围](../workflow/README.md#test-artifacts)；
迁移与引用检查见[规则职责维护](../agent-policy-maintenance-20261018/README.md)。后续仍按原唯一队列入口恢复。
