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

原冻结来源为用户前轮明确要求“最后再统一汇总，形成启动下一次任务前必须人工确定或豁免的guard”，不是新增全局审批规则。前轮在两组修复完整收尾后结束连续推进；**任何下一次CRP工作单元Start前，须用户明确决定或豁免本节**。沿用既有延期即可放行独立任务，无需一次解决全部问题；模糊的Next、测试通过、压缩恢复或旧授权不自动解除本冻结门槛。

| 待确认/豁免项 | 当前事实与实际影响 | 建议保留的边界 / 可选裁决 |
|---|---|---|
| F0040 C++ guard/DSO | 用户最新条件授权内已修签名/完成字节/DSO与串行初始化，已提交1603f88；并发初始化仍未实现，整项Partial | 后续明确并发/异常/析构需求再闭合完整项，不能把串行成功当作线程安全 |
| F0029/F0030 VME权限/撤映射/页表回收 | 原五CQ中两项，权限与生命周期教学子集未定；原问题不删除 | 继续留到正式内存管理阶段，或明确权限/撤映射及页表所有权/回收契约 |
| F0031 NPC VME/MPE能力 | dummy能力仍未闭合，不能从当前RT/IOE通过推定多核/虚存可用 | 延续延期；如纳入新能力，转正式计划，当前CRP不自行推进M阶段 |
| F0054 free契约 | free空实现是否允许arena教学子集未决定，仍未修 | 延续延期，或明确可回收分配器/单次arena的需求与验收 |
| F0055 RTC声明 | has_rtc=true与固定日期的能力契约未定；与uptime时基分开 | 延续延期，或明确真实墙钟/不支持声明/占位允许范围 |
| 上轮F0045的NEMU-on-AM音频边界：已澄清 | Kconfig在!TARGET_AM内才可选HAS_AUDIO，audio.c按HAS_AUDIO参与编译；不是受支持配置的可达兼容性回归。删除MUXDEF候选已撤回 | 不再作为人工启动阻塞；若未来开发AM目标音频再正式规划，不要求本轮额外豁免 |
| 2026-10-19 F0003范围与并行优化已批准/实施 | 双端功能修复后按用户批准优化mtvec并行准备；同配方估算420.232MHz，超过原399.074MHz，原355.983MHz回退在本次对照中消除；仍未达500MHz | [补充交付](../crp-f0003/README.md#parallel-mtvec-result-20261019)：本次新结果已获用户确认/提交授权；实际提交回执见报告，不自动启动其他组 |

用户先以条件授权完成兼容性单元，后以“确认WR属性…然后提交并进入下一批修改”确认实际提交1603f88并放行F0010/F0011。本组因PAL启动卡顿反馈Reopen完成定向监测后，用户“我了解了，闭合并提交你做过的相关修改”确认已披露范围并授权重新闭合和提交；本次提交包含F0010/F0011。PAL供给不足与新增退化因果未明保留风险，不宣称性能已修。剩余五CQ、F0040完整并发范围和F0043提交协议仍分别保留具体裁决，不作为独立修复的统一前置；已澄清的不可达AM音频分支不再要求豁免。唯一下一入口仍在TASK_QUEUE，本节不维护第二个队列。

验收限制继续保留：历史RT到msh后SIGTERM；本兼容性单元RT只重新image，未重跑到msh。本轮nanos到观察点后SIGTERM，音频小guest正常GOOD TRAP；未跑四AM应用、实际声音/窗口、全配置及长时调度，CPU按链接闭包未受影响不重跑。两缺源fceux/oslab0仍按原批准暂缓。ignored测试证据/.agent本地保管，commit不代表备份；无新安装或环境阻塞，不要求为未涉及的能力逐一新增豁免。

## 当前逐项状态

全部已有功能修复43（此前42项已确认提交，F0003补充优化已确认，实际提交回执见本组报告末尾及本地记录）；未修完76，其中契约待定5、F0040部分修复1。F0003方案A已明确批准并按共享ecall链路完成双端修复，并行优化已消除本次对照中的原回退，用户已确认本次结果并授权提交，实际回执见报告末尾。总计119；技术事实见对应报告，功能完成不代表性能已接受。

| ID | 原审阅分类 / 级别 | 当前修复状态 | 提交 / 证据 |
|---|---|---|---|
| CCR-F0001 | Confirmed / Medium | 已修 / 已确认提交252eaea | [C UB反例/原NPC数值核验及真实回归](../crp-f0001/README.md) |
| CCR-F0002 | Confirmed / High | 已修 / 已确认提交784e73b | [全地址身份/精确异常/真实消费者](../crp-f0002/README.md) |
| CCR-F0003 | Confirmed / Medium | 已修 / 补充优化Completed；已确认，提交回执见报告 | [共享ecall链路/并行MTVEC/STA对照](../crp-f0003/README.md#parallel-mtvec-result-20261019) |
| CCR-F0004 | Confirmed / Medium | 已修 / 已确认提交1ddaf04 | [非对齐/别名安全与共享真实回归](../crp-f0004-f0005-f0008/README.md) |
| CCR-F0005 | Confirmed / Medium | 已修 / 已确认，代码bc7a110/补验1ddaf04 | [既有bc7a110修复/本组补验](../crp-f0004-f0005-f0008/README.md) |
| CCR-F0006 | Confirmed / Low | 已修 / 已确认提交7e68ca7 | [保留字段/原指令诊断及真实回归](../crp-f0006-f0007/README.md) |
| CCR-F0007 | Confirmed / Low | 已修 / 已确认提交7e68ca7 | [PMEM/Sv39/MMIO边界及真实回归](../crp-f0006-f0007/README.md) |
| CCR-F0008 | Confirmed / Medium | 已修 / 已确认提交1ddaf04 | [整数偏移先于指针及边界验证](../crp-f0004-f0005-f0008/README.md) |
| CCR-F0009 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0009) |
| CCR-F0010 | Confirmed / Medium | 已修 / 已确认提交12afa58 | [初始化/欠载原函数验收](../crp-f0010-f0011/README.md) |
| CCR-F0011 | Confirmed / Medium | 已修 / 已确认提交12afa58 | [初始化/欠载原函数验收](../crp-f0010-f0011/README.md) |
| CCR-F0012 | Confirmed / Medium | 已修 / 已确认提交77a9471 | [边界及真实CLI验收](../crp-f0012-f0013/README.md) |
| CCR-F0013 | Confirmed / Medium | 已修 / 已确认提交77a9471 | [边界及真实CLI验收](../crp-f0012-f0013/README.md) |
| CCR-F0014 | Confirmed / Medium | 已修 / 已确认提交194d2c0 | [整段区间/高位别名及真实REF/NPC验收](../crp-f0014/README.md) |
| CCR-F0015 | Confirmed / Medium | 已修 / 已提交 | f5825fd；[报告](../crp-f0015/README.md) |
| CCR-F0016 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0016) |
| CCR-F0017 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0017) |
| CCR-F0018 | Confirmed / Medium | 已修 / 已确认提交37b3195 | [load失败原子性/真实CLI验收](../crp-f0018/README.md) |
| CCR-F0019 | Confirmed / Low | 已修 / 已确认提交522bed7 | [有界生成/oracle失败传播/真实CLI](../crp-f0019/README.md) |
| CCR-F0020 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0020) |
| CCR-F0021 | Confirmed / Medium | 已修 / 已提交 | 2a96eb3；[ELF边界/真实FTRACE验收](../crp-f0021/README.md) |
| CCR-F0022 | Confirmed / Medium | 已修 / 已提交 | bc7a110；[嵌入镜像/真实AM验收](../crp-f0022/README.md) |
| CCR-F0023 | Confirmed / High | 已修 / 已确认提交c9be898 | [MPP/栈约定与真实NEMU验收](../crp-f0023/README.md) |
| CCR-F0024 | Confirmed / Medium | 已修 / 已确认提交fc7835e | [双页表嵌套切走恢复/真实回归及回执](../crp-f0024/README.md#approval-submit-20261018) |
| CCR-F0025 | Confirmed / Medium | 已修 / 已确认提交f3a5d0c | [NPC启动布局真实验收](../crp-f0025-f0027-f0028/README.md) |
| CCR-F0026 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0026) |
| CCR-F0027 | Confirmed / Medium | 已修 / 已确认提交f3a5d0c | [NPC启动布局真实验收](../crp-f0025-f0027-f0028/README.md) |
| CCR-F0028 | Robustness / Low | 已修 / 已确认提交f3a5d0c | [NPC启动布局真实验收](../crp-f0025-f0027-f0028/README.md) |
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
| CCR-F0040 | Confirmed / Low | 未修完 / 部分修复 | 1603f88；[本轮ABI/串行修正，线程同步未闭合](../crp-compatibility-20261018/README.md) |
| CCR-F0041 | Confirmed / Medium | 已修 / 已提交 | e83df62；[本组报告](../crp-f0041-f0042-f0053/README.md) |
| CCR-F0042 | Confirmed / Medium | 已修 / 已提交 | e83df62；[本组报告](../crp-f0041-f0042-f0053/README.md) |
| CCR-F0043 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0043) |
| CCR-F0044 | Robustness / Low | 已修 / 已提交 | 1603f88；[容量分片及原测试真实验收](../crp-compatibility-20261018/README.md) |
| CCR-F0045 | Robustness / Low | 已修 / 已提交 | f4e3c0c；[本组报告](../crp-f0045/README.md) |
| CCR-F0046 | Confirmed / High | 已修 / 已提交 | e9a71f3；[报告](../crp-f0046-f0048-f0050/README.md) |
| CCR-F0047 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0047) |
| CCR-F0048 | Confirmed / Low | 已修 / 已提交 | e9a71f3；[报告](../crp-f0046-f0048-f0050/README.md) |
| CCR-F0049 | Confirmed / Medium | 已修 / 已提交 | d9a3d42；[报告](../crp-f0049/README.md) |
| CCR-F0050 | Confirmed / Medium | 已修 / 已提交 | e9a71f3；[报告](../crp-f0046-f0048-f0050/README.md) |
| CCR-F0051 | Confirmed / Medium | 已修 / 已提交 | 4ab9f3f；[报告](../crp-f0051/README.md) |
| CCR-F0052 | Confirmed / Medium | 已修 / 终态补充已确认提交22791cf | am-kernels c1ba0bb；[原报告](../crp-f0052/README.md)、[双平台真实补充](../crp-f0052-ref-terminal/README.md) |
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

## 2026-10-18 条件兼容修复补充

[本轮报告](../crp-compatibility-20261018/README.md)保存逐项影响、用户TARGET_AM追问及撤回候选、原入口真实验收；全部已修21/未修完98，F0040仍Partial且含在98中。原兼容性单元已确认提交1603f88，随后按明确指令执行F0010/F0011，当前结果见本次报告。历史原119项分类不改。

## 2026-10-18 WR确认、实际提交与F0010/F0011

WR为AM写接口、不提供读回契约；前兼容性单元实际提交1603f88（F0044全部、F0040Partial）。用户明确授权进入下一批，独立F0010/F0011已完成，[真实验收](../crp-f0010-f0011/README.md)；全部已修23/未修完96含5CQ及F0040Partial，本组未确认未提交。F0043协议未决不阻塞其他独立修复；唯一下一入口TASK_QUEUE。

2026-10-18 [PAL启动卡顿补查](../crp-f0010-f0011/README.md#performance-review-20261018)：11个真实PulseAudio测量、真实窗口旧/新对照和AM回退均已完成；Open/参数/宿主回调与容量等待无异常，旧/新均大量欠载，PAL填音/轮询供给不足。没有生产新改动或性能问题修复声明，不能以旧功能PASS关闭用户反馈；本组保持Reopened，不推进后组。

2026-10-18 [用户确认重新闭合/提交](../crp-f0010-f0011/README.md#closeout-approval-20261018)：本组Completed，用户已确认并授权本次commit，原性能Reopen停点解除；PAL供给不足/新增退化因果和F0043仍保留风险，不记性能修复。全部23项功能修复纳入提交，96项未修完不变；实际提交身份以包含本附记的Git提交及本地回执为准。下一组只沿TASK_QUEUE，当前未Start。

## 2026-10-18 F0012/F0013完成

用户“继续CRP修复”授权已落档独立单元；依前组确认/提交12afa58及现行Next的非依赖边界继续，旧连续提交授权不在本轮复用。两项Completed，结果确认/commit Pending；[报告](../crp-f0012-f0013/README.md)保存host332检查、真实CLI37检查/内置guest及限制。25已修/94未修完含5CQ及F0040Partial。原冻结表保留相关风险，不推定其获裁决；下一步只沿TASK_QUEUE，当前停等确认提交，未push/M2。

2026-10-18 用户“提交，继续”确认F0012/F0013已报告范围并授权本次提交及随后一个单元。51条manifest与原13项validation复核通过，复用原动态验收；实际提交见本组报告/本地回执。


## 2026-10-18 F0014完成及前组实际提交

用户“提交，继续”确认F0012/F0013，实际提交77a9471，提交后root/index干净。
随后授权的独立F0014已Completed、待结果确认/commit；[报告](../crp-f0014/README.md)
保存整段范围、size_t与64位入口高地址拒绝、原三反例、host3030断言、真实REF77场景/
原ABI执行、CPU全集36PASS+1XFAIL及真实RT到msh/无分歧。RT原ANSI判据误判已保留并
通过日志复核/3负例更正，不重跑guest。17项最终核对通过，默认REF已更新且旧产物保留。
26已修/93未修完含5CQ/F0040Partial，未push/M2；唯一下一入口仍TASK_QUEUE。

2026-10-18 用户“提交，继续”确认F0014已报告结果并授权提交后执行下一单元；146条manifest无漂移，原17项validation通过，复用动态验收。[确认回执](../crp-f0014/README.md#approval-submit-20261018)。


## 2026-10-18 F0018完成及F0014实际提交

用户“提交，继续”确认F0014，实际提交194d2c0，提交后root/index干净。独立F0018
已Completed，待本组结果确认/commit；[报告](../crp-f0018/README.md)保存暂存读取/失败
清理、原3失败见证、修复ASan/UBSan16场景/124断言、真实128MiB CLI10次失败保持/
完整恢复及GOOD TRAP，21项真实判据/14项最终核对通过。LSan环境失败单列，不冒称通过。
27已修/92未修完含5CQ/F0040Partial；额外128MiB临时内存/原raw非全机恢复限制保留。
无新安装/commit/push/M2；当前停等确认提交，下一入口只见TASK_QUEUE。

2026-10-18 用户确认F0018并授权提交及独立大型临时资产清理；45条manifest/原14项validation核对通过，复用原验收。[提交授权回执](../crp-f0018/README.md#approval-submit-20261018)，不Start F0021。


## 2026-10-18 F0018实际提交及用户授权空间清理

F0018已确认实际提交37b3195，原Pending为提交前截面；27已修/92未修完不变。
用户要求直接删除大型临时存档，本轮独立[空间清理](../../workspace-storage-cleanup-20261018/README.md)
完成：29文件释放约3.05GB，工作区约5.08GB；868项保护哈希不变，未推进F0021/M2。
F0037/F0038、F0033/F0056、F0034/F0035/F0036、F0085归档ramdisk及F0018完整raw原字节
已按授权删除，原报告追加说明、原命令/验证/哈希保留；历史manifest缺失需对照删除清单，
不伪称旧产物仍存在或已备份。维护说明/索引尚未提交，当前停点及未来入口只见TASK_QUEUE。


## 2026-10-18 F0021完成与维护实际提交

用户“提交后继续CRP”确认空间维护并授权提交485548c后执行本单元。F0021已Completed，
待结果确认/commit；[报告](../crp-f0021/README.md)保存原3反例、最终ASan/UBSan32场景、
8清理控制、39真实native含实际call/ret/GOOD TRAP及默认关闭对照、16项终检。
仅改monitor.c的ELF解析/失败清理，原GLOBAL/FUNC与名称截断/最后SYMTAB策略保持，
非完整ELF验证器。28已修/91未修完含5CQ/F0040Partial，未推进M2或其他未决能力；
空间清理已删字节事实保持，测试资料约1.5MiB，不自动提交新修复。唯一Next仍TASK_QUEUE。

## 2026-10-18 F0021实际提交与F0022完成

用户“提交，继续”确认F0021，226条manifest无漂移并复用已报告验收，实际提交2a96eb3。
随后按唯一入口完成F0022：[报告](../crp-f0022/README.md)保留28个host sanitizer边界、
6个真实AM-native场景、RISC-V内外两层NEMU和默认native成功执行，以及原2反例。
同时最小修正动态PMEM表初始化的实际C编译阻塞；根配置/REF/NPC保持，未扩AM音频。
29已修/90未修完含5CQ/F0040Partial，本组结果确认/commit Pending；全部错误全局配置的
启动安全不属于本组验收，具体init_isa前置限制见报告，不自动推进M2/下一单元。

2026-10-18 用户明确确认F0022并授权提交，687条manifest无漂移，复用原验收；同时授权只读盘点CRP存档构建资产，未授权启动下一修复单元。实际提交回执以包含本附记的commit及.agent为准。

2026-10-18 F0022实际提交bc7a110，index/工作树在提交检查点干净。其后独立CRP存档盘点完成，未删除资产，维护说明未提交；本次未Start F0023，未来仍沿TASK_QUEUE唯一入口。

2026-10-18 用户“提交修改，并继续CRP修复”确认存档盘点说明，三份维护文档实际提交47063cd；随后按唯一入口完成F0023。生产仅NEMU cte.c，原三模式精确失败、最终三guest GOOD TRAP、M/U改栈/嵌套/真实MTIMER/线程切换、RT测试链接配置下msh及am_hello、nanos稳定8观察点与hello递增、18项终检通过。无效/失败夹具及RT链接限制见报告；30已修/89未修完，本组确认/commit Pending，不从本轮继续推定自动提交/串行下一组。

2026-10-18 用户“提交，然后继续CRP修复”确认F0023，3,958项证据/18项原验收/生产patch无漂移，实际提交c9be898；随后按唯一入口完成F0024。生产仅vme.c删除按旧槽跳过，原零槽真实跨页表恢复失败/非零正常控制、修复后三guest GOOD TRAP（双页表私有VA/嵌套用户与内核现场恢复）、RT测试链接配置msh+am_hello、nanos8点/hello1483→6787及21项终检通过。31已修/88未修完，本组确认/commit Pending，五CQ/权限回收/并发及原性能限制保持，不自动Start下一组。

2026-10-18 用户“提交”确认F0024已报告范围并授权提交；545条文件清单无漂移、21项验收/生产patch保持，复用原验收。实际回执以包含本附记的commit及.agent为准；本轮不Start下一组，不push。3,958为F0023逐文件清单条目（含大量源树输入），不是测试数量，详见本组报告澄清。

2026-10-18 F0025/F0027/F0028修复三项Completed：原3BSS/5rodata真实失败、最终35NPC启动/20heap边界/CPU36PASS+1XFAIL/RT当前模型到msh通过。现有CPU汇总计入REF附加终态会假失败，保留失败并独立重判/重跑；后续F0052补充仅TASK_QUEUE维护。本组三项待确认提交；F0026与五CQ不变。

2026-10-18 前组F0025/F0027/F0028已确认提交f3a5d0c；F0052终态归属补充Completed：原两假失败/一REF-only假通过，最终42/42及真实NPC/NEMU全集各36PASS+1XFAIL、make exit0，补充待确认提交。同一F0052不重复加计，34已修/85未修完保持。

2026-10-18 F0052补充已确认分仓提交22791cf/f3d0252；F0019工具修复Completed待确认提交：原请求3/输出0/exit0精确失败，128独立oracle/真实CLI、10,000 sanitizer生成/3边界树、输入/子进程/IO失败及并发通过，17项终检。35已修/84未修完；仅工具修改，未冒充CPU/RT/nanos重测。

2026-10-19 F0004/F0008新增修复及F0005补验闭合Completed：F0005原代码已随F0022/bc7a110提交，原清单漏镜像，本次按证据补齐不重复修改。宿主181×6检查、实际static/malloc/REF/AM、双CPU全集、RT新REF到msh及nanos8点通过；本组三项待确认，新代码未提交。38已修/81未修完，原历史计数不回写。

2026-10-19 前组宿主内存三项已按用户“提交，继续CRP修复”确认提交1ddaf04；F0006/F0007 Completed待确认提交，40次GCC/sanitizer定向、native/REF自修改/尾非法指令和双CPU全集各36PASS+1XFAIL通过，23终检。其他ISA完整构建仍有原有阻塞，成套源/头逐文件对比确认前后诊断一致；不称其完整通过。40已修/79未修完，详细边界见本组报告，未来仅TASK_QUEUE。

## 2026-10-19 F0003方案A实施

用户“同意建议A，开始修复”并要求NPC共享ecall时序，已解除原M3窄范围裁决，双端功能修复完成。NEMU76例×2/NPC71向量、真实三平台13次trap及两类流水/mtvec前递guest、15微测试/15断言、两CPU全集36PASS+1XFAIL、RT171.45秒msh与nanos8帧/hello1316→5722通过。前后同配置综合STA估算频率399.074→355.983MHz，约-10.80%，面积+1.10%；未擅自接受降级。43已修/76未修完，当前结果/性能接受/commit Pending；等待用户选择接受或继续优化，唯一入口仅TASK_QUEUE#crp-next。旧边界分析和历史计数保留为原截面，M2/M3不推进。

2026-10-19 F0003补充完成：用户“同意你的建议，实施”批准mtvec并行准备，生产仅两处RTL补充。71向量/14预读与前递检查、原串行结构/注入错误值拒绝、真实SoC trap/冒险/mtvec/负例、15微测/15断言、NPC CPU36PASS+1XFAIL和RT169.64秒msh通过；24项核验与原385清单保持。同配方估算420.232MHz，原399.074/串行355.983，面积比原+0.265%；仍未达500MHz。新结果确认/commit Pending，43/76不重复计数，未来只见TASK_QUEUE，M2/M3不推进。

2026-10-19 用户“提交”确认F0003原修复和并行优化已报告结果/限制并授权本批提交；57/385/193项清单、28/11/24/8核验和源/模型身份保持。实际commit/暂存核对见[确认回执](../crp-f0003/README.md#approval-submit-20261019)及本地submit-receipt/.agent；43项功能修复均已获确认，不将提交授权记为未测能力验收。仅本批提交，不push/Start下一组。
