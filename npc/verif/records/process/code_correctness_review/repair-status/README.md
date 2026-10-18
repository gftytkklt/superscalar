# CRP 修复状态与人工启动 guard

## 职责与维护方法

本表只镜像每个CCR-F的当前修复状态，技术事实仍以源码、对应批次验收及提交回执为准；原始119项审阅分类以[FINAL_FINDINGS](../FINAL_FINDINGS.md)及历史findings.json为准，不回写旧快照。未来执行顺序只在[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本表不是第二份任务调度队列。

2026-10-18从119项原清单与16项已有完成/提交报告逐项对齐初始化；不从文件存在或单个测试通过推定修复。每批完成后更新对应行的修复/未修、报告及真实commit；分开记录Completed、用户确认或预授权、提交与未测范围，计数从本表逐行计算。未修行的“准入待核”不表示已授权实现所有能力。

下一组选择：先满足已授权存量修复范围、明确契约和依赖门槛，再按共享模块/调用链/反例及验证环境形成自适应组，优先修复会污染其他验收判据的依赖；严重度帮助排序，不按编号或固定数量凑组。复杂项单独处理。未决或延期项仍计入剩余，且只阻塞依赖它的工作。

## 本轮连续授权（2026-10-18，已执行收尾）

用户明确授权：“完成后提交并继续……在上下文长度在不影响任务质量的前提下连续进行多批任务的提交和新任务开启……未决项除非直接影响下一批任务，否则……最后再统一汇总，形成启动下一次任务前必须人工确定或豁免的guard”。本授权替代当前CRP各组必须另等确认的停点，仍逐项验证、逐组完成留档再提交；不授权push、安装、其他业务主线或未决实现。代理验收与提交预授权不等于用户逐项review。

本轮已完成提交：既有F0039 b2229ef；新组三项F0041/F0042/F0053 root e83df62、am-kernels 6dc302a；新组F0045 root f4e3c0c。两组独立验收/留档后连续提交。现停在完整收尾边界；以下guard冻结Pending，旧连续授权不能自行绕过新的人工启动门槛。未push，M2未Start。

<a id="manual-start-guard"></a>
## 下次启动前人工 guard（2026-10-18冻结，Pending）

来源为用户本轮明确要求“最后再统一汇总，形成启动下一次任务前必须人工确定或豁免的guard”，不是新增全局审批规则。本轮在两组修复完整收尾后结束连续推进；**任何下一次CRP工作单元Start前，须用户明确决定或豁免本节**。沿用既有延期即可放行独立任务，无需一次解决全部问题；模糊的Next、测试通过、压缩恢复或旧授权不自动解除本冻结门槛。

| 待确认/豁免项 | 当前事实与实际影响 | 建议保留的边界 / 可选裁决 |
|---|---|---|
| F0040 C++ guard/DSO | 用户已决定本轮只分析，待正式需求；仍未修，并发/异常/析构不具备完整运行时。本轮未改cpp.c | 确认继续沿用延期；若要修，先冻结C++初始化/并发/异常/析构要求。仅阻塞依赖该能力的工作 |
| F0029/F0030 VME权限/撤映射/页表回收 | 原五CQ中两项，权限与生命周期教学子集未定；原问题不删除 | 继续留到正式内存管理阶段，或明确权限/撤映射及页表所有权/回收契约 |
| F0031 NPC VME/MPE能力 | dummy能力仍未闭合，不能从当前RT/IOE通过推定多核/虚存可用 | 延续延期；如纳入新能力，转正式计划，当前CRP不自行推进M阶段 |
| F0054 free契约 | free空实现是否允许arena教学子集未决定，仍未修 | 延续延期，或明确可回收分配器/单次arena的需求与验收 |
| F0055 RTC声明 | has_rtc=true与固定日期的能力契约未定；与uptime时基分开 | 延续延期，或明确真实墙钟/不支持声明/占位允许范围 |
| F0045配置兼容性边界，关联下一组音频 | 本组真实验证native NEMU及NPC；未启用的CONFIG_TARGET_AM音频分支有3处读WR的旧调用，严格方向检查会拒绝该用法，未修/未测该消费者 | 确认暂不纳入NEMU-on-AM，或把该消费者加到下一组必要分析/回归；不能宣称全配置兼容。该限制不回写为新CCR-F已修 |

建议下次先确认“沿用F0040及五CQ延期，NEMU-on-AM暂不纳入（或明确纳入），允许下一组音频必要分析”。这仅放行分析，不预先批准修改音频寄存器协议、超长请求拒绝/分片策略或增加设备；真正影响实现的取舍形成具体提案后裁决。唯一任务范围与执行入口仍在TASK_QUEUE，本节不维护第二个队列。

既有验收限制继续保留：RT/nanos到观察点后SIGTERM、未声称guest正常退出；本轮未跑四AM应用、实际声音/窗口、全配置及长时调度，CPU未受影响不重跑。两缺源fceux/oslab0仍按原批准暂缓。ignored测试证据/.agent本地保管，commit不代表备份；无新安装或环境阻塞，不要求为未涉及的能力逐一新增豁免。

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
| CCR-F0045 | Robustness / Low | 已修 / 已提交 | f4e3c0c；[本组报告](../crp-f0045/README.md) |
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
