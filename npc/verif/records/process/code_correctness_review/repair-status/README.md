# CRP 修复状态与人工启动 guard

## 职责与维护方法

本表只镜像每个CCR-F的当前修复状态，技术事实仍以源码、对应批次验收及提交回执为准；原始119项审阅分类以[FINAL_FINDINGS](../FINAL_FINDINGS.md)及历史findings.json为准，不回写旧快照。未来执行顺序只在[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本表不是第二份任务调度队列。

2026-10-18从119项原清单与16项已有完成/提交报告逐项对齐初始化；不从文件存在或单个测试通过推定修复。每批完成后更新对应行的修复/未修、报告及真实commit；分开记录Completed、用户确认或预授权、提交与未测范围，计数从本表逐行计算。未修行的“准入待核”不表示已授权实现所有能力。

下一组选择：先满足已授权存量修复范围、明确契约和依赖门槛，再按共享模块/调用链/反例及验证环境形成自适应组，优先修复会污染其他验收判据的依赖；严重度帮助排序，不按编号或固定数量凑组。复杂项单独处理。未决或延期项仍计入剩余，且只阻塞依赖它的工作。

## 本轮连续授权（2026-10-18，已执行收尾）

用户明确授权：“完成后提交并继续……在上下文长度在不影响任务质量的前提下连续进行多批任务的提交和新任务开启……未决项除非直接影响下一批任务，否则……最后再统一汇总，形成启动下一次任务前必须人工确定或豁免的guard”。本授权替代当前CRP各组必须另等确认的停点，仍逐项验证、逐组完成留档再提交；不授权push、安装、其他业务主线或未决实现。代理验收与提交预授权不等于用户逐项review。

当轮已完成提交：既有F0039 b2229ef；新组三项F0041/F0042/F0053 root e83df62、am-kernels 6dc302a；新组F0045 root f4e3c0c。两组独立验收/留档后连续提交。当时停在完整收尾边界并冻结guard Pending，后续独立任务放行见下节；旧连续授权不能自行越过用户停点。未push，M2未Start。

<a id="manual-start-guard"></a>
## 启动 guard（2026-10-18历史冻结；后续独立任务已放行）

本节冻结文字是历史截面；后续用户已放行独立修复（见下方回执），2026-10-20又明确授权维护后继续实际未修任务。五CQ/F0040/F0043具体未决保持，不恢复为独立任务统一阻塞。

历史冻结要求（后续放行见本节首段及下方回执）：原冻结来源为用户前轮明确要求“最后再统一汇总，形成启动下一次任务前必须人工确定或豁免的guard”，不是新增全局审批规则。前轮在两组修复完整收尾后结束连续推进；**任何下一次CRP工作单元Start前，须用户明确决定或豁免本节**。沿用既有延期即可放行独立任务，无需一次解决全部问题；模糊的Next、测试通过、压缩恢复或旧授权不自动解除本冻结门槛。

| 待确认/豁免项 | 当前事实与实际影响 | 建议保留的边界 / 可选裁决 |
|---|---|---|
| F0040 C++ guard/DSO | 用户最新条件授权内已修签名/完成字节/DSO与串行初始化，已提交1603f88；并发初始化仍未实现，整项Partial | 后续明确并发/异常/析构需求再闭合完整项，不能把串行成功当作线程安全 |
| F0029/F0030 VME权限/撤映射/页表回收 | 原五CQ中两项，权限与生命周期教学子集未定；原问题不删除 | 继续留到正式内存管理阶段，或明确权限/撤映射及页表所有权/回收契约 |
| F0031 NPC VME/MPE能力 | dummy能力仍未闭合，不能从当前RT/IOE通过推定多核/虚存可用 | 延续延期；如纳入新能力，转正式计划，当前CRP不自行推进M阶段 |
| F0054 free契约 | free空实现是否允许arena教学子集未决定，仍未修 | 延续延期，或明确可回收分配器/单次arena的需求与验收 |
| F0055 RTC声明 | has_rtc=true与固定日期的能力契约未定；与uptime时基分开 | 延续延期，或明确真实墙钟/不支持声明/占位允许范围 |
| 上轮F0045的NEMU-on-AM音频边界：已澄清 | Kconfig在!TARGET_AM内才可选HAS_AUDIO，audio.c按HAS_AUDIO参与编译；不是受支持配置的可达兼容性回归。删除MUXDEF候选已撤回 | 不再作为人工启动阻塞；若未来开发AM目标音频再正式规划，不要求本轮额外豁免 |
| 2026-10-19 F0009方案A已批准并实施 | 用户同意A，失败诊断终止及尾块/零块规则已完成最终源码验收；未增加可恢复错误协议 | [本组交付](../crp-f0009/README.md#implementation-result-20261019)：失败契约裁决解除，本组已获用户确认与提交授权，实际回执见报告，不再作为后续独立任务的新策略阻塞 |
| 2026-10-19 F0003范围与并行优化已批准/实施 | 双端功能修复后按用户批准优化mtvec并行准备；同配方估算420.232MHz，超过原399.074MHz，原355.983MHz回退在本次对照中消除；仍未达500MHz | [补充交付](../crp-f0003/README.md#parallel-mtvec-result-20261019)：本次新结果已获用户确认/提交授权；实际提交回执见报告，不自动启动其他组 |

用户先以条件授权完成兼容性单元，后以“确认WR属性…然后提交并进入下一批修改”确认实际提交1603f88并放行F0010/F0011。本组因PAL启动卡顿反馈Reopen完成定向监测后，用户“我了解了，闭合并提交你做过的相关修改”确认已披露范围并授权重新闭合和提交；本次提交包含F0010/F0011。PAL供给不足与新增退化因果未明保留风险，不宣称性能已修。剩余五CQ、F0040完整并发范围和F0043提交协议仍分别保留具体裁决，不作为独立修复的统一前置；已澄清的不可达AM音频分支不再要求豁免。唯一下一入口仍在TASK_QUEUE，本节不维护第二个队列。

验收限制继续保留：历史RT到msh后SIGTERM；本兼容性单元RT只重新image，未重跑到msh。本轮nanos到观察点后SIGTERM，音频小guest正常GOOD TRAP；未跑四AM应用、实际声音/窗口、全配置及长时调度，CPU按链接闭包未受影响不重跑。两缺源fceux/oslab0仍按原批准暂缓。ignored测试证据/.agent本地保管，commit不代表备份；无新安装或环境阻塞，不要求为未涉及的能力逐一新增豁免。

## 当前逐项状态

全部已有功能修复95（前94已确认提交；F0020已确认/本批授权提交）；未修完24，含5CQ及F0040/F0118 Partial。F0118静音子范围已确认提交be8a4c0。唯一未来入口TASK_QUEUE#crp-next，M2不变。

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
| CCR-F0009 | Confirmed / High | 已修 / 已确认提交d28c393 | [最终源码验收及清理回执](../crp-f0009/README.md#implementation-result-20261019) |
| CCR-F0010 | Confirmed / Medium | 已修 / 已确认提交12afa58 | [初始化/欠载原函数验收](../crp-f0010-f0011/README.md) |
| CCR-F0011 | Confirmed / Medium | 已修 / 已确认提交12afa58 | [初始化/欠载原函数验收](../crp-f0010-f0011/README.md) |
| CCR-F0012 | Confirmed / Medium | 已修 / 已确认提交77a9471 | [边界及真实CLI验收](../crp-f0012-f0013/README.md) |
| CCR-F0013 | Confirmed / Medium | 已修 / 已确认提交77a9471 | [边界及真实CLI验收](../crp-f0012-f0013/README.md) |
| CCR-F0014 | Confirmed / Medium | 已修 / 已确认提交194d2c0 | [整段区间/高位别名及真实REF/NPC验收](../crp-f0014/README.md) |
| CCR-F0015 | Confirmed / Medium | 已修 / 已提交 | f5825fd；[报告](../crp-f0015/README.md) |
| CCR-F0016 | Confirmed / Medium | 已修 / 已确认提交de7e3be | [三段启动同步/真实golden及性能诊断](../crp-f0016/README.md) |
| CCR-F0017 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0017) |
| CCR-F0018 | Confirmed / Medium | 已修 / 已确认提交37b3195 | [load失败原子性/真实CLI验收](../crp-f0018/README.md) |
| CCR-F0019 | Confirmed / Low | 已修 / 已确认提交522bed7 | [有界生成/oracle失败传播/真实CLI](../crp-f0019/README.md) |
| CCR-F0020 | Confirmed / Medium | 已修 / 已确认，本批授权提交 | [SD方向/I/O/按需容量验收](../crp-f0020/README.md#f0020-final-20261020) |
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
| CCR-F0057 | Confirmed / High | 已修 / 已确认提交a92ccf9 | [ELF组提交回执](../crp-f0057-f0058-f0059/README.md#submit-20261020) |
| CCR-F0058 | Confirmed / High | 已修 / 已确认提交a92ccf9 | [ELF组提交回执](../crp-f0057-f0058-f0059/README.md#submit-20261020) |
| CCR-F0059 | Confirmed / Medium | 已修 / 已确认提交a92ccf9 | [ELF组提交回执](../crp-f0057-f0058-f0059/README.md#submit-20261020) |
| CCR-F0060 | Confirmed / Medium | 已修 / 已确认提交7b83685 | [本组报告](../crp-f0060/README.md) |
| CCR-F0061 | Robustness / Medium | 已修 / 已确认提交0ddd35c | [参数预算/提交回执](../crp-f0061/README.md#submit-20261020) |
| CCR-F0062 | Confirmed / High | 已修 / Completed，已确认，实际提交见报告回执 | [堆/页表容量事务合组](../crp-f0089/README.md) |
| CCR-F0063 | Confirmed / High | 已修 / Completed，已确认，实际提交见报告回执 | [堆/页表容量事务合组](../crp-f0089/README.md) |
| CCR-F0064 | Robustness / Medium | 已修 / 已确认提交5941586 | [本组报告](../crp-f0064-f0065/README.md) |
| CCR-F0065 | Confirmed / Medium | 已修 / 已确认提交5941586 | [本组报告](../crp-f0064-f0065/README.md) |
| CCR-F0066 | Confirmed / Medium | 已修 / Completed，已确认；本次提交见报告回执 | [本组报告](../crp-f0066-f0067/README.md#submit-20261020) |
| CCR-F0067 | Robustness / Medium | 已修 / Completed，已确认；本次提交见报告回执 | [本组报告](../crp-f0066-f0067/README.md#submit-20261020) |
| CCR-F0068 | Confirmed / Medium | 已修 / 已确认提交9fb8831 | [FB边界/真实ecall与三前台/清理](../crp-f0068/README.md) |
| CCR-F0069 | Confirmed / Medium | 已修 / 已确认提交e58bbd0 | [本组计划及勘误](../crp-f0069/README.md) |
| CCR-F0070 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0070) |
| CCR-F0071 | Confirmed / High | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0071) |
| CCR-F0072 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0072) |
| CCR-F0073 | Robustness / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0073) |
| CCR-F0074 | Confirmed / High | 已修 / 已确认提交b260359，正式产物已更新 | [提交/资产回执](../crp-f0074/README.md#submit-20261020) |
| CCR-F0075 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0075) |
| CCR-F0076 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0076) |
| CCR-F0077 | Confirmed / Low | 已修 / 已确认，nested71fac82；root回执见报告 | [Navy syscall ABI/真实优化及三前台](../crp-f0077-f0078-f0088/README.md) |
| CCR-F0078 | Robustness / Low | 已修 / 已确认，nested71fac82；root回执见报告 | [Navy syscall ABI/真实优化及三前台](../crp-f0077-f0078-f0088/README.md) |
| CCR-F0079 | Confirmed / Medium | 已修 / 已确认提交nested5d9ffdb，根记录见报告 | [newlib边界/实际新库用户与三前台](../crp-f0079-f0080/README.md) |
| CCR-F0080 | Confirmed / Medium | 已修 / 已确认提交nested5d9ffdb，根记录见报告 | [newlib边界/实际新库用户与三前台](../crp-f0079-f0080/README.md) |
| CCR-F0081 | Confirmed / Medium | 已修 / 已确认提交nestedd923fa4，根回执见报告 | [exec输入边界/真实新库/标准update-run](../crp-f0081-f0082/README.md) |
| CCR-F0082 | Confirmed / Medium | 已修 / 已确认提交nestedd923fa4，根回执见报告 | [exec输入边界/真实新库/标准update-run](../crp-f0081-f0082/README.md) |
| CCR-F0083 | Confirmed / Medium | 已修 / Completed，用户确认、nested 8101fad；root文档1dbf841 | [setenv失败保持/所有权/实际新库](../crp-f0083/README.md) |
| CCR-F0084 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0084) |
| CCR-F0085 | Confirmed / Medium | 已修 / 已提交 | b739176；[报告](../crp-f0085/README.md) |
| CCR-F0086 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0086) |
| CCR-F0087 | Robustness / Low | 已修 / Completed，用户已确认，实际提交见报告回执 | [exec示例确认/提交](../crp-f0087/README.md#submit-20261020) |
| CCR-F0088 | Confirmed / Low | 已修 / 已确认，nested71fac82；root回执见报告 | [Navy syscall ABI/真实优化及三前台](../crp-f0077-f0078-f0088/README.md) |
| CCR-F0089 | Robustness / Low | 已修 / Completed，已确认，实际提交见报告回执 | [堆/页表容量事务合组](../crp-f0089/README.md) |
| CCR-F0090 | Robustness / Low | 已修 / 已确认，提交见回执 | [NDL失败与生命周期、真实RV64及标准回归](../crp-f0090/README.md) |
| CCR-F0091 | Robustness / Medium | 已修 / 已确认提交a27a262 | [SDL图形合组/实际RV64/消费者/运行时性能](../crp-video-20261020/README.md) |
| CCR-F0092 | Robustness / Medium | 已修 / 已确认，提交见回执 | [事件入队边界/真实RV64及标准回归](../crp-f0092/README.md) |
| CCR-F0093 | Confirmed / Medium | 已修 / 已确认，提交见回执 | [定时器重入/slot生命周期及实际RV64](../crp-f0093/README.md) |
| CCR-F0094 | Confirmed / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0095 | Robustness / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0096 | Confirmed / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0097 | Confirmed / Medium | 已修 / 已确认提交a27a262 | [SDL图形合组/实际RV64/消费者/运行时性能](../crp-video-20261020/README.md) |
| CCR-F0098 | Confirmed / Medium | 已修 / 已确认提交a27a262 | [SDL图形合组/实际RV64/消费者/运行时性能](../crp-video-20261020/README.md) |
| CCR-F0099 | Robustness / Medium | 已修 / 已确认提交70983d4 | [RWops/图像合组/真实RV64/标准消费者](../crp-rw-image-20261020/README.md) |
| CCR-F0100 | Confirmed / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0101 | Robustness / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0102 | Confirmed / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0103 | Confirmed / Low | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0104 | Robustness / Medium | 已修 / 已确认提交70983d4 | [RWops/图像合组/真实RV64/标准消费者](../crp-rw-image-20261020/README.md) |
| CCR-F0105 | Robustness / Medium | 已修 / 已确认提交13d30a9 | [BDF/终端边界/实际RV64/标准消费者](../crp-bdf-term-20261020/README.md) |
| CCR-F0106 | Robustness / Medium | 已修 / 已确认提交70983d4 | [RWops/图像合组/真实RV64/标准消费者](../crp-rw-image-20261020/README.md) |
| CCR-F0107 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0107) |
| CCR-F0108 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0108) |
| CCR-F0109 | Robustness / Medium | 已修 / 已确认提交13d30a9 | [BDF/终端边界/实际RV64/标准消费者](../crp-bdf-term-20261020/README.md) |
| CCR-F0110 | Robustness / Low | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0110) |
| CCR-F0111 | Robustness / Medium | 已修 / 已确认，bird80f9918/根提交见回执 | [Sprite资源边界/所有权/实际RV64与真实消费者](../crp-f0111/README.md) |
| CCR-F0112 | Robustness / Medium | 已修 / 已确认，PAL a744cee/根文档提交见回执 | [RIX/MKF边界/所有权/实际RV64与标准消费者](../crp-f0112/README.md) |
| CCR-F0113 | Confirmed / Medium | 未修 / 准入待核 | [原问题](../FINAL_FINDINGS.md#ccr-f0113) |
| CCR-F0114 | Robustness / Medium | 已修 / 已确认提交a27a262 | [SDL图形合组/实际RV64/消费者/运行时性能](../crp-video-20261020/README.md) |
| CCR-F0115 | Confirmed / Medium | 已修 / 已确认，根/ONS提交回执见报告 | [SDL音频合组/真实RV64/标准回归](../crp-audio-20261020/README.md) |
| CCR-F0116 | Confirmed / Medium | 已修 / 已确认，实际提交见回执 | [REF显式注入PC/host及真实RV64执行/ABI/清理](../crp-f0116/README.md) |
| CCR-F0117 | Confirmed / Low | 已修 / 已确认提交b3b3b88 | [NDL64批准/最终实现与验收](../crp-f0117/README.md#final-ndl64) |
| CCR-F0118 | Robustness / Medium | 未修完 / Partial；失败静音子范围已确认提交be8a4c0 | [用户最小策略/无写入与真实验收](../crp-f0118/README.md#mute-final-20261020) |
| CCR-F0119 | Confirmed / Low | 已修 / 已确认提交7912c42 | [NPC init(int)/参数哨兵/真实CPU/ABI与清理](../crp-f0119/README.md) |

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

2026-10-19 F0009本轮必要分析：用户“继续CRP修复”授权原入口一个单元；12个原行为观察完成，失败语义无法沿现契约确定，触发原有裁决停点。F0009仍未修，43/76不变；本次没有新功能完成/提交，不以分析文档或复现成功推定修复获批。唯一下一动作见TASK_QUEUE#crp-next。

2026-10-19 F0009实施/清理补充取代上方分析截面：用户明确批准A，最终源464定向/6初始化/真实MMIO与storage/nanos及native-REF通过；已修44/未修完75，本组结果确认/commit Pending。已授权删除18660个可再生产物、14大日志无损gzip；统一规则/所有历史manifest的清理指向见workflow与本组报告，不再默认保留全部旧镜像和源码构建树。

2026-10-19 用户手工验证/提交确认：用户明确PAL绘图正常、此前观察不完整是程序运行慢，并要求“提交修改”。PAL绘图功能不再列为当前未决，原短时观察保留；没有本批性能优化声明。F0009结果已确认、提交已授权，实际提交回执见报告末尾；复用既有验收，不重造清理产物/不开始下一单元。

2026-10-19 F0016及nanos性能诊断补充：用户本轮授权继续既有唯一入口，F0009 d28c393门槛满足。F0016三段实际装载范围完整送入golden，旧版实际Spike对拍失败/新版通过、REF全字节读回、四同步负例、单镜像/内置/loader/native/REF ABI通过。性能诊断约16–18M guest/s，后台hello约45.46%、guest DBOPL27.14%、guest绘图15.14%，host翻译/访存相关self样本约61%；未实施性能优化。45已修/74未修完，前44已确认提交，本组待新结果确认/commit，统一停点；恢复只沿TASK_QUEUE#crp-next。

2026-10-19 提交授权补充：用户要求调度99:1补充验证后提交当前改动；F0016与宿主优化复用既有验收，只补确认和实际提交回执，不重复Completion。新调度不增加F项计数，45/74保持；F0016实际提交结果见本组报告及local回执，未push/下一CRP Start。


## 2026-10-20 入口勘误及实际未修任务启动

F0018在本表一直为已修/已确认提交37b3195；TASK_QUEUE及相关2026-10-19快照误列为未来候选，本轮按用户明确要求勘误，不重复计数/验收。45已修/74未修完经119稳定ID逐行计算；F0069实际尚未修，当前Active，计划/验收见报告，唯一调度入口仍TASK_QUEUE。


## 2026-10-20 F0069 完成（未提交）

非FG保留stage按实际PCB选择、无可用目标时保持current/frame一致；原四NULL反例拒绝，最终五配置各50000调用/sanitizer、10个实际内核构建及10次真实有限NEMU运行、默认三前台/hello37→160通过。当前46已修/73未修完，F0069结果确认/commit Pending；其他45项已确认提交。旧F0018重复候选不计新修复；证据/未测/清理见[本组报告](../crp-f0069/README.md)。下一入口只在TASK_QUEUE，本轮不提交/下一组Start。


## 2026-10-20 F0069实际提交及F0060启动

用户“同意你提交以后进入下一项”确认前组范围并授权提交后执行唯一F0060。实际e58bbd0，12文件173增17删，暂存/实际blob一致、提交后root/index干净；复用75manifest/21文档身份/15终检及既有动态验收/清理，未push。本组F0060尚Active，46已修/73未修完不变，计划/边界见本组报告，不自动提交新组。


## 2026-10-20 F0060完成（未提交）

loader仅5行参数表padding；原PAL/NTERM四host失败、VME/非VME各99例、真实旧C入口不对齐/新四应用及非VME-NTERM对齐、六次各1亿指令/纯生产与默认三前台/hello37→167通过。47已修/72未修完，前46均确认提交，本项结果确认/commit Pending。684临时产物169182570字节已清理，保留文字/身份/patch；完整证据与未测见[本组报告](../crp-f0060/README.md)。未来唯一TASK_QUEUE，不自动提交或下一组Start。


## 2026-10-20 F0060提交及F0064/F0065完成

用户“提交后继续”确认前组并授权7b83685提交后本组，5文件/范围/blob/干净状态核对通过，58manifest/18终检和原动态验收/清理复用。F0064四入口fd验证、F0065signed定位先验后发布已修，原3host反例、30fd/28seek/129断言、真实旧FD故障入口/旧seek偏移失败及新syscall PASS/写盘差异、默认三前台/hello38→165通过。49已修/70未修完，前47已确认提交，本组2项待确认/commit；389临时产物315283627字节已清理，证据/夹具修正/未测见[报告](../crp-f0064-f0065/README.md)。未来仅TASK_QUEUE，不自动提交/下一组Start。


## 2026-10-20 F0064/F0065提交及F0066/F0067完成

用户“提交，继续”确认前组并授权5941586提交后本组；6文件/blob/干净状态核对，72manifest/19终检和原验收/清理复用。事件有界前缀/可选NUL/键码验证及len0不轮询、音频限长memcpy/未对齐安全已修。原4host失败、两分支各135场景、真实旧len0失败/新SDL注入与音频read/PCM PASS、默认三前台/hello38→169通过。51已修/68未修完，前49已确认提交，本组2项待确认/commit；390产物315392054字节已清理，完整证据与未测见[报告](../crp-f0066-f0067/README.md)，未来仅TASK_QUEUE。


2026-10-20 F0066/F0067音频补查补充完成：[当前99:1证据及方法问答](../crp-f0066-f0067/README.md#audio-review-20261020)。用户收敛验收为证明高负载降低填音频率；同引擎仅跳过绘图对照4.98→10.87包/s、欠填充117/217→0/217，达到该标准，执行预算型卡顿按用户要求不修。没有补查生产改动，不增加修复计数，51/68及本组待确认commit保持；F0043/其他SDL缺陷不宣称已修。原快照保留，Supplemental Completion及819文件清理已落档，下一入口仅TASK_QUEUE。


2026-10-20 用户“提交”确认F0066/F0067及99:1音频补查的已报告范围/限制，授权本批5文件提交；原19/补充15终检及技术验收复用，9项提交前核对通过、原60与补充64 manifest项/48源输入/patch保持，不重跑或重复归档。实际commit/暂存与最终blob核对见[提交回执](../crp-f0066-f0067/README.md#submit-20261020)及local/submit-receipt.json，未来仅TASK_QUEUE；本轮提交后停止，不开始F0068，不push。51/68不变，ignored/.agent不由commit备份。


2026-10-20 F0068：用户“继续CRP修复”授权单元，前51项确认提交07bba74；FB实际容量限写/安全初始化、原反例/两分支host/真实旧新ecall/三前台与hello通过，[报告](../crp-f0068/README.md)记录RGBA观察夹具更正/未测/清理。52/67，本组确认/commit Pending，无push/M2推进；未来仅TASK_QUEUE。


2026-10-20 F0079/F0080：前F0068已确认提交9fb8831，本组授权来自“提交后继续”。两嵌套newlib源/原反例/58host/真实libc与重建三前台验证完成，54/65，结果确认/commit Pending；原850执行位差异保持、内容仅两源变化，根不force-add库。证据/清理/限制见本组报告，未来仅TASK_QUEUE。


2026-10-20 F0077/F0078/F0088：前组确认提交nested5d9ffdb/root7a8150e，“提交后继续”授权本组。三项最小修复/逐项证据和实际重建新库/优化/弱hook/三前台完成，57/62，结果确认/commit Pending；原memory当前未误编译/其他warnings/未测/清理见本组报告。未来仅TASK_QUEUE，不自动提交/push/M2。

2026-10-20 本组用户条件提交/接续指令确认已报告范围；nested实际71fac82，root本次提交回执见[本组记录](../crp-f0077-f0078-f0088/README.md#submit-20261020)。165原manifest保持、复用33终检及既有验收；上下文较长，提交后提示新对话继续唯一入口，不开始F0081/F0082、无push/新测试。


### 2026-10-20 F0081/F0082完成（本组待确认提交）

两项wrapper容量保护完成，43场景/169断言在host sanitizer与实际RV64新库均通过，三次真实exec参数/环境链及标准update→run三前台/hello34→149通过。145终检/身份/目视及9398产物清理见[本组报告](../crp-f0081-f0082/README.md)。59已修/60未修完，前57确认提交，新2项未确认提交；两HEAD/index保持，nested四源60增36删/原850mode噪声保留。未测/夹具更正/再生限制见报告，未来仅TASK_QUEUE，无commit/push/M2。

2026-10-20 用户“提交后继续”确认F0081/F0082并授权提交后一个单元；nested实际d923fa4，root回执见本组local/submit-receipt.json；59已修均确认提交，复用验收/清理，无push，随后仅F0083。


### 2026-10-20 F0083完成（待确认提交）

用户“提交后继续”授权前组nested d923fa4/root5423bd7提交后本单元，并在本轮明确继续处理。nested单源37增37删，环境字符串/向量先成功后发布、当前向量所有权及失败保留修复；四原host见证、新8场景259host/273RV64断言/七真实exec与标准update→run三前台hello34→153通过。146preclean/4890源/850链接身份，9396产物约483.3MiB清理。累计60已修/59未修完，前59确认提交，新1待确认commit；夹具leaf更正/未测/恢复见[报告](../crp-f0083/README.md)。未来仅TASK_QUEUE，无push/M2。


### 2026-10-20 框架/OS 修复 diff 文档补充

[盘点与核验](../framework-diffs-20261020/README.md)：25 份原验收文档内嵌 48 份逐文件 diff，覆盖 41 个相关 ID（含 F0040 已实施部分），附仓库/版本及语句级实现说明；正反应用与历史补丁一致，生产代码不变。用户授权补充完后提交文档；F0083 报告及内嵌 diff 纳入根文档提交，生产结果确认/嵌套源码提交仍 Pending，不将根提交等同于代码提交。累计 60/59 不变，后续只沿 TASK_QUEUE 唯一入口，未开始 F0089/M2。

2026-10-20 用户“提交后继续”确认F0083并授权提交后一个单元；nested实际8101fad，root报告原1dbf841，本次回执见[F0083提交附记](../crp-f0083/README.md#submit-20261020)。60已修均确认提交，复用原验收/清理，无push；随后仅F0089。

### 2026-10-20 F0062/F0063/F0089同链合组完成

用户“提交后继续”授权接续F0089，后明确扩大同组范围至F0062/F0063和页表分配失败事务。
[本组交付](../crp-f0089/README.md)：checked new_page、loader受控OOM、ELF堆下界/栈底上界、
Sv39只读表页预算+数据/表预留事务及_sbrk无符号预检。原五见证，host84及默认/NDEBUG各137，
真实RV64容量拒绝/8192B堆/exec重建，最终标准update→run三前台/hello34→152，165preclean通过。
63已修/56未修完，新3项确认/commit Pending。原队列“F0063完成记录”为错误引用，现已更正；
原审阅未修截面保留，不伪造旧验收。未来只沿TASK_QUEUE唯一入口；无push/安装/M2推进。

2026-10-20 用户“提交”确认F0062/F0063/F0089已报告范围并授权本组精确根提交；100项manifest及生产patch无漂移，复用原验证/清理，不重复Completion。63已修均已确认，实际路径/blob/提交回执见[本组附记](../crp-f0089/README.md#submit-20261020)及local/submit-receipt.json；本轮提交后停止，无push/下一组/M2推进。

### 2026-10-20 F0061参数容量及会话建议规则

用户“继续CRP修复”授权本单元，并要求每次提交落档按上下文长度/任务相关性提醒
新对话；AGENTS稳定规则与WORKFLOW_POLICY/CRP引用已补齐。[本组报告](../crp-f0061/README.md)：
loader33增33删，参数预算先于fs/protect/分配、超限-E2BIG及去VLA。原四host精确失败、
两模式各112、实际RV64七拒绝/24KiB CRT参数/空argv/恰容量汇编exec、标准三前台/hello34→149、
167preclean与清理完成；64已修/55未修完，本组结果确认/commit Pending。未来只沿TASK_QUEUE，
不自动commit/push/下一组/M2。建议本组确认提交后新对话接续，建议本身不新增门槛。


### 2026-10-20 F0061提交与ELF组合修复完成

用户“提交修改后继续CRP修复”确认F0061和会话规则，根实际0ddd35c已核对；继而完成F0057/F0058/F0059一个单元。五源199增83删，ELF全预检先于替换/固定尺寸读/同页复用；137host、真实27坏映像加设备保持/同页执行、标准三前台及hello36→159、263preclean和清理通过。累计67已修/52未修完；本组三项待确认/commit，正式旧盘F0074未自动记修。完整diff/身份/限制/清理见[报告](../crp-f0057-f0058-f0059/README.md)，未来仅TASK_QUEUE#crp-next；无自动新组/push/M2。


### 2026-10-20 ELF组提交与F0074正式产物修复

用户“提交，继续”确认ELF组三项并授权实际根提交a92ccf9及后续一个单元。F0074正式旧盘错配/受控拒绝已固定，标准无clean update→run完成正式更新；108extent/48ELF/四启动新链接匹配，三前台/hello33→144、8帧目视及218检查通过，无生产源码改动。68已修/51未修完，本组产物已生效、结果确认/文档commit Pending；10项local截图/观察库已清理，正式资产保留且不由commit备份。报告与前后SHA见[本组](../crp-f0074/README.md)，未来只沿TASK_QUEUE#crp-next，无自动新组/push/M2。


### 2026-10-20 F0074提交与F0087示例状态修复

用户“提交后继续”确认F0074记录并授权根实际b260359提交后一个单元；F0087三示例4增3删，原exec失败return0动态复现，修复后EXIT_FAILURE及缺失提示。三host/27断言、六真实RV64失败1/成功0与目标验证、标准三前台/hello35→157、186检查/完整diff正反/8目视/清理通过。69已修/50未修完，本组待确认commit；正式F0074资产保持。未来仅TASK_QUEUE#crp-next，建议本组确认提交后新对话接续，无自动新组/push/M2。


2026-10-20 用户“提交”确认F0087已报告范围并授权精确根提交；88保留身份/369既有终检/3源patch无漂移，复用原验收和清理，仅补[确认/实际回执](../crp-f0087/README.md#submit-20261020)。本轮提交后停止，F0090未Start，无push/M2推进；正式忽略产物不由commit备份。


2026-10-20 用户“继续CRP修复”授权F0090一个单元，现已[完成](../crp-f0090/README.md)。70已修/49未修完，本组结果确认/commit Pending；最终228preclean、六真实RV64/标准三前台及清理结果以报告为准。唯一后续TASK_QUEUE#crp-next，F0092未Start，无push/M2推进。


2026-10-20 用户“提交”确认F0090已报告范围并授权精确根提交；103保留身份/两源patch与既有验收/清理复核，复用原结果，补[确认及实际回执入口](../crp-f0090/README.md#submit-20261020)。提交后停止，F0092未Start，无push/M2推进。


2026-10-20 用户“继续”授权F0092一个单元，已[完成](../crp-f0092/README.md)。71已修/48未修完，本组结果确认/commit Pending；原2UB见证/host与实际RV64各1108/标准三前台/166preclean/归档和清理完成。未来仅TASK_QUEUE#crp-next，F0093未Start，无push/M2推进。


2026-10-20 用户“提交，继续”确认F0092报告范围并授权精确提交后唯一下一单元；52保留身份/原验收/patch及清理复核，[实际回执入口](../crp-f0092/README.md#submit-20261020)。无push/M2推进。


2026-10-20 用户“提交，继续”授权F0092实际7eb176d提交后一个单元，已[完成F0093](../crp-f0093/README.md)。72已修/47未修完，本组确认/commit Pending，host15类两构建/实际RV64/标准回归、207preclean/归档/清理完成。未来只沿TASK_QUEUE#crp-next，F0094未Start，无push/M2推进。

2026-10-20 F0093确认及精确提交授权、用户update/run资产保留说明见[本组回执](../crp-f0093/README.md#submit-20261020)。后续只沿唯一入口执行F0094一个单元，旧连续提交授权不恢复。

2026-10-20 用户音频合组及格式限制授权，F0093实际e42b6b3后八项Completed，80已修/39未修完；本组根/ONS源码尚未提交、结果确认Pending。[逐项与共享证据](../crp-audio-20261020/README.md)。原ONS编码差异和用户update/run资产保留，下一入口只在TASK_QUEUE#crp-next；不恢复连续提交授权或推进M2。

2026-10-20 用户确认SDL音频八项并授权提交后继续；ONS实际6326adf，根实际回执见[本组提交收尾](../crp-audio-20261020/README.md#submit-20261020)，复用87身份/118终检及原技术验收，不重复Completion。原字体编码/libc850mode与正式资产保持；后续按唯一入口图形组及用户明确的nanos-lite应用画面/音频性能分析，不恢复连续提交授权。

2026-10-20 音频已确认提交根d4b6c9c/ONS6326adf后，按用户继续及应用卡顿分析授权完成图形F0091/F0097/F0098/F0114；84已修/35未修完。本组未提交，正常绘图约4.4–4.6PCM包/s、同版仅跳过绘图约10.85包/s且两轮无欠填充，结论/局限见[本组报告](../crp-video-20261020/README.md)。无性能策略修改；唯一下步及门槛在TASK_QUEUE#crp-next，不自动commit/下一组/M2。

2026-10-20 用户“提交后继续”确认图形/性能分析，根a27a262已精确提交；本组F0099/F0104/F0106 Completed待结果确认/根commit。host RW60/BMP47+83/IMG46均两构建、最终实际RV64 RW60/BMP83/IMG46/root130/main0/GOOD，标准三前台hello34→152/8目视/slide逐像素通过，338身份/24归档/141preclean及9447路径512652139B清理完成。87已修/32未修完，已确认前84；IMG保留MEM pos0子集，FILE/非0位置安全拒绝，通用decoder尺寸/构造器OOM仍有限制，详见[报告](../crp-rw-image-20261020/README.md)。唯一未来TASK_QUEUE#crp-next，未push/M2。


2026-10-20 用户“提交后继续”确认RWops图像三项，实际根70983d4；随后F0105/F0109 Completed，host两构建及实际RV64各248599/7×191glyph、6判据负例/main0/GOOD，标准三前台hello32→148/8目视及NTerm像素匹配通过；完整diff/235身份/29归档/93preclean与9398路径清理完成。89已修/30未修完，本组待结果确认/commit；详见[报告](../crp-bdf-term-20261020/README.md)。唯一Next仅TASK_QUEUE#crp-next，未push/M2，不恢复旧连续提交授权。


2026-10-20 用户“提交后继续”确认BDF/终端，实际根13d30a9；F0111 Completed待结果确认/根及bird nested提交，90已修/29未修完。host两构建767/live4→4、实际RV64765/main0/GOOD/6判据负例、71atlas548240像素及标准三前台hello32→143/额外bird标题动画/hello61通过；255身份/12diff正反/80preclean及9463路径清理见[报告](../crp-f0111/README.md)。既有Video.h/21mode/ONS编码/libc850mode保留；唯一Next仍TASK_QUEUE#crp-next，无push/M2，不恢复连续提交授权。


2026-10-20 用户“提交，给我一条能自己运行bird进行测试的终端语句”确认F0111并授权精确分仓提交；bird实际80f9918，两源111增61删、Git mode100644及已验收patch/blob相符，21原mode/Video.h保留。根报告随本次提交，完整[确认/回执](../crp-f0111/README.md#submit-20261020)与local/submit-*为准；90已修均已确认，29未修完，F0112未Start，不push/M2。复用484终检及原验收，不重跑产品。


## F0112完成（2026-10-20）

用户“继续”及后续游戏应用修复说明授权同一单元；[报告](../crp-f0112/README.md)保存两源90增44删、562定向/实际RV64/136FILE配平与86真实音乐槽旧新寄存器轨迹、三前台hello39→168/8目视、完整diff正反及9441路径清理。91已修/28未修完，前90确认提交；本项结果确认/根与PAL源码分仓提交Pending，原nested差异保留，M2不变。下一入口只沿TASK_QUEUE，不自动commit/push。


2026-10-20 用户“提交后继续”确认F0112，PAL实际a744cee；763终检/79身份/23原diff空白及两源patch一致，原nested差异保留。根文档随本次提交，[确认/回执](../crp-f0112/README.md#submit-20261020)。91已修均确认，28未修完；提交后授权F0116一个单元，未push/M2。


## F0116完成（2026-10-20）

用户“提交后继续”确认F0112并授权分仓提交后本单元；F0112实际root12be663/PALa744cee。F0116只ref.c一行写回trap PC，host普通/ASan+UBSan各36、真实RV64 REF 37/首条handler及CSR/原33字ABI通过，旧库负例拒绝；19preclean、97输入及完整diff正反、4产物235576字节清理。[报告](../crp-f0116/README.md)为证据；92已修/27未修完，前91已确认提交，本项确认/commit Pending。默认产物未替换，NPC无注入调用、CPU/RT/nanos无依赖不重跑，无push/M2；未来只TASK_QUEUE唯一入口。


2026-10-20 用户再次“提交后继续”确认F0116并授权提交后F0119一个单元；79保留身份及生产patch一致，122终检复用。[提交回执](../crp-f0116/README.md#submit-20261020)，92已修均确认，27未修完；不push/M2。


## F0119完成（2026-10-20）

用户再次“提交后继续”授权F0116提交后本单元；F0116实际f5b9973。F0119 NPC两行init(int)/显式0及末尾换行，旧类型编译/函数sanitizer拒绝、最终host动态DSO/step/skip通过；新同版完整NPC/REF及ABI、真实CPU全集36 PASS+1 XFAIL/37次init0、PC/GPR故障两例拒绝；693身份/归档检查、258消费者/97REF输入、565路径137996332B清理。[报告](../crp-f0119/README.md)。93已修/26未修完，前92确认提交，本项确认/commit Pending；默认产物未替换，未push/M2，未来只TASK_QUEUE唯一入口。

2026-10-20 F0119已确认实际提交7912c42。F0117直接gettimeofday候选按用户NDL层次要求撤回，仍未修；候选通过观察不等于最终验收，范围裁决见本组报告/唯一TASK_QUEUE入口。93已修/26未修完不变。

## F0117 NDL64完成（2026-10-20）

用户要求libam只经NDL，已撤回直接系统函数候选；用户后续批准新增NDL64并保持旧行为。NDL_GetTicks64毫秒64/原32位低位保持、libam只适配1000，3源9增3删；原动态回绕反例、host两构建各90断言、原新32接口1000样本/故障序列逐字节相同、实际RV64同libam/NDL88/main0/GOOD及真实2ms进展、标准update→run三前台hello38→168、166preclean/6002身份/完整diff正反/8目视，清理9400路径507473688B零tracked删除。[报告](../crp-f0117/README.md#final-ndl64)。94已修/25未修完，前93确认提交，本组结果确认/commit Pending；唯一TASK_QUEUE入口，F0118未Start/M2保持。

## F0117提交与F0118必要分析（2026-10-20）

F0117已由用户“提交后继续”确认，实际根b3b3b88，七路径/blob/55保留身份及三源patch精确、两原diff空白核对，复用原验收和清理，不重跑。F0118已完成必要现源分析：原F0010已处理检查返回/错误打印/失败不Pause；当前五层实际函数host同步桥接普通/sanitizer五例各24断言，共10运行/48断言、43身份/现象核对，后端失败上层仍ret0并接受PCM、普通重开寄存器22050实际44100、显式失败旧已关/队列仍在可再写均复现；非真实OS/线程/声卡验收。仅分析，生产未改；清理12探针/对象911184B，等用户A保留接口故障终止仿真或B可恢复错误扩展（含重开清队列语义）裁决，见[报告](../crp-f0118/README.md)。94已修均确认提交/25未修完，F0118仍未修，当前单元Active，无自动提交/下一组/M2。

## F0118最小静音子范围完成（2026-10-20）

用户明确后端失败报错、不播放从不写入开始；本轮选择保留公开接口/继续仿真，替代旧A/B。NEMU失败INIT0/COUNT0并推进消费游标到已提交末端；AM写ring前/等待期间检查0返回，2源16增3删。旧三反例精确拒绝，host两构建各52/真实RV64三故障各3×65537B提交ring65536B未变/COUNT0及正常65537B PCM、两个显式成功fresh512/线程/欠载静音、标准三前台hello40→179、193preclean/5978身份/完整diff正反通过。用户已确认两默认产物由其原工程构建并保留，Guard解除；清理9370路径360267188B零tracked/默认删除。[报告](../crp-f0118/README.md#mute-final-20261020)。F0118仍Partial（普通改配置重开未修），94完全已修/25未修完不变，本子范围结果确认/commit Pending；未来仅TASK_QUEUE，不自动commit/push/M2。

## F0020完成（2026-10-20）

前F0118最小静音子范围实际be8a4c0。用户要求16 GiB不预占，并明确失败终止/未写区读零按需增长；F0020方向/命令重放/I/O边界修复完成，host普通/san各529正常+132空盘断言/10失败，真实RV64新NEMU GOOD及三失败，512MiB上限/16GiB逻辑8KiB实际占用验证。完整diff/16项保护/正反归档及1996文件清理通过，见[本组报告](../crp-f0020/README.md)。95已修/24未修完，本组结果确认/commit Pending；F0118整项仍Partial。唯一后续入口TASK_QUEUE#crp-next，当前停止，无本组commit/push/M2。
