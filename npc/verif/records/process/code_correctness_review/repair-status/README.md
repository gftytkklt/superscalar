# CRP 修复状态与人工启动 guard

## 职责与维护方法

本表只镜像每个CCR-F的当前修复状态，技术事实仍以源码、对应批次验收及提交回执为准；原始119项审阅分类以[FINAL_FINDINGS](../FINAL_FINDINGS.md)及历史findings.json为准，不回写旧快照。未来执行顺序只在[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本表不是第二份任务调度队列。

2026-10-18从119项原清单与16项已有完成/提交报告逐项对齐初始化；不从文件存在或单个测试通过推定修复。每批完成后更新对应行的修复/未修、报告及真实commit；分开记录Completed、用户确认或预授权、提交与未测范围，计数从本表逐行计算。未修行的“准入待核”不表示已授权实现所有能力。

下一组选择：先满足已授权存量修复范围、明确契约和依赖门槛，再按共享模块/调用链/反例及验证环境形成自适应组，优先修复会污染其他验收判据的依赖；严重度帮助排序，不按编号或固定数量凑组。复杂项单独处理。未决或延期项仍计入剩余，且只阻塞依赖它的工作。

## 本轮连续授权（2026-10-18，Active）

用户明确授权：“完成后提交并继续……在上下文长度在不影响任务质量的前提下连续进行多批任务的提交和新任务开启……未决项除非直接影响下一批任务，否则……最后再统一汇总，形成启动下一次任务前必须人工确定或豁免的guard”。本授权替代当前CRP各组必须另等确认的停点，仍逐项验证、逐组完成留档再提交；不授权push、安装、其他业务主线或未决实现。代理验收与提交预授权不等于用户逐项review。

本轮已确认提交：F0039 b2229ef；后续逐组补真实回执。用户已明确F0040本轮只分析、待正式需求裁决；五CQ保持原状。当前连续授权Active，未决不阻塞独立已明确组。

<a id="manual-start-guard"></a>
## 下次启动前人工 guard（本轮结束时冻结）

当前为Active收集状态，尚未到本次连续执行结束边界。结束时列出实际未决、受影响范围、建议处理与豁免边界，并标Pending；**下一次任务启动前须用户明确决定或豁免该冻结guard**，不能由“已有Next”、压缩恢复或旧测试通过推定放行。已获明确延期的事项保留来源，不伪造为新裁决；可由用户确认继续沿用其延期范围。

## 当前逐项状态

已修20；未修99，其中契约待定5、用户延期1。总计119。以下“已修/已提交”均有对应报告，历史审阅“未修”不覆盖本表当前镜像。

| ID | 原审阅分类 / 级别 | 当前修复状态 | 提交 / 证据 |
|---|---|---|---|
| CCR-F0001 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0001) |
| CCR-F0002 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0002) |
| CCR-F0003 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0003) |
| CCR-F0004 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0004) |
| CCR-F0005 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0005) |
| CCR-F0006 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0006) |
| CCR-F0007 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0007) |
| CCR-F0008 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0008) |
| CCR-F0009 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0009) |
| CCR-F0010 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0010) |
| CCR-F0011 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0011) |
| CCR-F0012 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0012) |
| CCR-F0013 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0013) |
| CCR-F0014 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0014) |
| CCR-F0015 | Confirmed / Medium | 已修 / 已提交 | f5825fd；[报告](../crp-f0015/README.md) |
| CCR-F0016 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0016) |
| CCR-F0017 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0017) |
| CCR-F0018 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0018) |
| CCR-F0019 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0019) |
| CCR-F0020 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0020) |
| CCR-F0021 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0021) |
| CCR-F0022 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0022) |
| CCR-F0023 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0023) |
| CCR-F0024 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0024) |
| CCR-F0025 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0025) |
| CCR-F0026 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0026) |
| CCR-F0027 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0027) |
| CCR-F0028 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0028) |
| CCR-F0029 | ContractQuestion / Medium | 未修 / 契约待定 | [原问题](../FINAL_FINDINGS.md#ccr-f0029) |
| CCR-F0030 | ContractQuestion / Low | 未修 / 契约待定 | [原问题](../FINAL_FINDINGS.md#ccr-f0030) |
| CCR-F0031 | ContractQuestion / Medium | 未修 / 契约待定 | [原问题](../FINAL_FINDINGS.md#ccr-f0031) |
| CCR-F0032 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0032) |
| CCR-F0033 | Confirmed / Medium | 已修 / 已提交 | 5b7a045；[报告](../crp-f0033-f0056/README.md) |
| CCR-F0034 | Confirmed / Medium | 已修 / 已提交 | 71c6cf8；[报告](../crp-f0034-f0035-f0036/README.md) |
| CCR-F0035 | Confirmed / Medium | 已修 / 已提交 | 71c6cf8；[报告](../crp-f0034-f0035-f0036/README.md) |
| CCR-F0036 | Confirmed / Medium | 已修 / 已提交 | 71c6cf8；[报告](../crp-f0034-f0035-f0036/README.md) |
| CCR-F0037 | Confirmed / High | 已修 / 已提交 | 0aa1dca；[报告](../crp-f0037-f0038/README.md) |
| CCR-F0038 | Confirmed / Low | 已修 / 已提交 | 0aa1dca；[报告](../crp-f0037-f0038/README.md) |
| CCR-F0039 | Confirmed / Low | 已修 / 已提交 | b2229ef；[报告](../crp-f0039-f0040/README.md) |
| CCR-F0040 | Confirmed / Low | 未修 / 用户延期 | [分析及用户决定](../crp-f0039-f0040/README.md#f0040-analysis) |
| CCR-F0041 | Confirmed / Medium | 已修 / 已提交 | e83df62；[本组报告](../crp-f0041-f0042-f0053/README.md) |
| CCR-F0042 | Confirmed / Medium | 已修 / 已提交 | e83df62；[本组报告](../crp-f0041-f0042-f0053/README.md) |
| CCR-F0043 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0043) |
| CCR-F0044 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0044) |
| CCR-F0045 | Robustness / Low | 已修 / 提交中 | [本组报告](../crp-f0045/README.md) |
| CCR-F0046 | Confirmed / High | 已修 / 已提交 | e9a71f3；[报告](../crp-f0046-f0048-f0050/README.md) |
| CCR-F0047 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0047) |
| CCR-F0048 | Confirmed / Low | 已修 / 已提交 | e9a71f3；[报告](../crp-f0046-f0048-f0050/README.md) |
| CCR-F0049 | Confirmed / Medium | 已修 / 已提交 | d9a3d42；[报告](../crp-f0049/README.md) |
| CCR-F0050 | Confirmed / Medium | 已修 / 已提交 | e9a71f3；[报告](../crp-f0046-f0048-f0050/README.md) |
| CCR-F0051 | Confirmed / Medium | 已修 / 已提交 | 4ab9f3f；[报告](../crp-f0051/README.md) |
| CCR-F0052 | Confirmed / Medium | 已修 / 已提交 | am-kernels c1ba0bb / root 7d99a8d；[报告](../crp-f0052/README.md) |
| CCR-F0053 | Confirmed / Low | 已修 / 已提交 | am-kernels 6dc302a / root e83df62；[本组报告](../crp-f0041-f0042-f0053/README.md) |
| CCR-F0054 | ContractQuestion / Low | 未修 / 契约待定 | [原问题](../FINAL_FINDINGS.md#ccr-f0054) |
| CCR-F0055 | ContractQuestion / Low | 未修 / 契约待定 | [原问题](../FINAL_FINDINGS.md#ccr-f0055) |
| CCR-F0056 | Robustness / Low | 已修 / 已提交 | 5b7a045；[报告](../crp-f0033-f0056/README.md) |
| CCR-F0057 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0057) |
| CCR-F0058 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0058) |
| CCR-F0059 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0059) |
| CCR-F0060 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0060) |
| CCR-F0061 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0061) |
| CCR-F0062 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0062) |
| CCR-F0063 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0063) |
| CCR-F0064 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0064) |
| CCR-F0065 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0065) |
| CCR-F0066 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0066) |
| CCR-F0067 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0067) |
| CCR-F0068 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0068) |
| CCR-F0069 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0069) |
| CCR-F0070 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0070) |
| CCR-F0071 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0071) |
| CCR-F0072 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0072) |
| CCR-F0073 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0073) |
| CCR-F0074 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0074) |
| CCR-F0075 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0075) |
| CCR-F0076 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0076) |
| CCR-F0077 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0077) |
| CCR-F0078 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0078) |
| CCR-F0079 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0079) |
| CCR-F0080 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0080) |
| CCR-F0081 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0081) |
| CCR-F0082 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0082) |
| CCR-F0083 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0083) |
| CCR-F0084 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0084) |
| CCR-F0085 | Confirmed / Medium | 已修 / 已提交 | b739176；[报告](../crp-f0085/README.md) |
| CCR-F0086 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0086) |
| CCR-F0087 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0087) |
| CCR-F0088 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0088) |
| CCR-F0089 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0089) |
| CCR-F0090 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0090) |
| CCR-F0091 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0091) |
| CCR-F0092 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0092) |
| CCR-F0093 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0093) |
| CCR-F0094 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0094) |
| CCR-F0095 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0095) |
| CCR-F0096 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0096) |
| CCR-F0097 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0097) |
| CCR-F0098 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0098) |
| CCR-F0099 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0099) |
| CCR-F0100 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0100) |
| CCR-F0101 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0101) |
| CCR-F0102 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0102) |
| CCR-F0103 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0103) |
| CCR-F0104 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0104) |
| CCR-F0105 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0105) |
| CCR-F0106 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0106) |
| CCR-F0107 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0107) |
| CCR-F0108 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0108) |
| CCR-F0109 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0109) |
| CCR-F0110 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0110) |
| CCR-F0111 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0111) |
| CCR-F0112 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0112) |
| CCR-F0113 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0113) |
| CCR-F0114 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0114) |
| CCR-F0115 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0115) |
| CCR-F0116 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0116) |
| CCR-F0117 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0117) |
| CCR-F0118 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0118) |
| CCR-F0119 | Confirmed / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0119) |
