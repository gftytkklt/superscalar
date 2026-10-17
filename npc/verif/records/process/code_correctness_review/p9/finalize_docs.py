#!/usr/bin/env python3
"""Persist authorized P9 semantic boundary after pre-gate; does not commit/start P10."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;B=H.parent;R=H.parents[5]
pre=json.loads((H/'pre-gate.json').read_text());assert pre['gate']=='PASS'
ch=R/'.agent/CHANGELOG_AGENT.md';assert 'id="snapshot-ccr-p9-20261017"' not in ch.read_text(),'Reuse existing completion; do not duplicate'
chains=json.loads((H/'chains.json').read_text());summary=json.loads((H/'review-summary.json').read_text())
intro='P9完成L01–L09跨层审阅，9×15=135字段及故障路径均有双方证据；Completed表示审阅义务闭合，包含已确认缺陷/能力断点，不表示九条实现全部正确。'
md='# CCR-P9 跨层闭合审阅与 Final Gate\n\n2026-10-17；**Completed（审阅交付）**。'+intro+'\n\n'
md+='本轮先按用户“同意，先提交再执行，那两个缺源暂不解决”提交P8 Partial：`5f88749ce1a9ed814ae42b76e03b3d324d86a3fe`。该明确指令豁免P8完成作为P9启动前提；fceux/oslab0继续Unavailable/未审，不改成Excluded或Completed。P9结果确认Pending、P9未提交；停止，不开始P10。\n\n'
md+='## Project Resume / State Consistency Guard\n\n已按Session→CURRENT_STATE独立CCR→TASK_QUEUE→Git核对，先读根AGENTS/WORKFLOW_POLICY与总计划§7、P0规划记录、P1–P8报告、各阶段证据索引及coverage/CONTRACTS/既有findings/INTERFACES。P8原247项manifest提交前匹配；本轮实际提交14个可跟踪文件，无生产代码。授权/提交基线在[p9/baseline](p9/baseline.json)，用户豁免与实际提交回执在[P8](P8.md#p8-waiver-20261017)。M2 Active Execution Context原文保持；没有新长期架构裁决，DECISIONS未改。\n\n'
md+='## 跨层结果\n\n| 链路 | 关键审阅结论 | 本次动态边界 |\n|---|---|---|\n'
short=[('加载/argc/env/寄存器/trap/返回配对；ELF/Context旧缺陷保留','受控RV64完整启动、syscall、exec/exit通过；坏ELF/缺盘异常退出'),('固定fd/共享offset、byte→512block、errno/失败传播','低层libos→FS→AM→NEMU真实文件短读/seek/EOF/close'),('82个键值及文本/布局/FG消费配对；短buf缺陷','枚举/布局验证；真实输入/GUI NotRun'),('us/sec/ms、RTC锁存、legacy/mtimer与NPC相对周期区分','target计时返回；libam回绕定向复现'),('pixel/byte/stride/地址、同步先于像素与裁剪缺陷','配置初始化可达；绘制/屏幕NotRun'),('S16/帧/byte/count/生命周期、正常开启顺序与后端失败','AM+NEMU原驱动接点probe；真实声音/并发NotRun'),('exec预检/替换、exit重载、yield/brk、AS/Context归属','成功/失败exec、yield返回、brk与exit重载通过'),('33字/选择拷贝/skip/内存域、native/REF/Spike分离','REF注入函数probe；完整NPC/REF.so/Spike NotRun'),('生成宏/链接/文件表/镜像/实际执行配对，历史产物Unknown保留','隔离直编/执行；108 extents匹配；完整Linux NotRun')]
for c,(a,d) in zip(chains,short):md+=f'| [{c["id"]}](p9/{c["id"]}.md) | {a} | {d} |\n'
md+='\n逐字段主证据：[CROSS_LAYER_P9](CROSS_LAYER_P9.md)、[INTERFACES](INTERFACES.md)、[结构化矩阵](p9/chains.json)、[X03支撑接口](p9/X03_SUPPORT.md)。不从P2–P8两端各自通过推导跨层正确。\n\n'
md+='## 新问题与限定\n\n新增 **CCR-F0116–F0119**：REF中断注入丢PC（Medium/Confirmed）、libam微秒计时继承32位ms回绕（Low/Confirmed）、音频后端打开失败仍接受控制/数据（Medium/Robustness）、NPC调用REF init参数签名不一致（Low/Confirmed）。[详细位置/根因/影响/建议](p9/findings.json)及[FINDINGS](FINDINGS.md#ccr-p9-findings-20261017)。累计119项：86 Confirmed/28 Robustness/5 CQ，High13/Medium79/Low27，均未修。\n\nF0010限定：AM实际先写init=1，再写freq/channels/samples；最后offset8正好触发现有NEMU回调。因此单写init的问题不能推导当前首次打开必败。本轮原函数bridge已观察正常首次触发。旧115问题对象不改写。OS固定PCB/固定fd教学边界沿用P6，不能扩为AM通用unprotect或完整POSIX/SDL豁免；五CQ仍待决。\n\n'
md+='## 本次验证与覆盖\n\n[END_TO_END](p9/END_TO_END.md)完整区分本次target、host seam、编译与历史证据：legacy及mtimer模式受控guest均成功；坏魔数与磁盘不存在均BAD TRAP/rc1，记录不可恢复路径；三个host seam观察各有日志，目标ABI布局编译通过。前四次隔离脚本装配失败原样保留，最终attempt5完整成功，未修生产源码。\n\n40,010稳定coverage行及旧阶段对象保持；P9原2,082责任行（1,843文件/239条件）全部消费，补108接点文件，共2,190条P9增量。1,951文件身份零未解释漂移，其中1,772资产生产/消费边界、165接点、13 Linux支撑实现、1派生pyc；239条件是接口责任导航，不是运行次数。原121个独立端点身份全部保留，扩充必要支撑引用；没有把资源数量当功能覆盖率。两个Unavailable不变。见[逐行增量](p9/cross-layer-coverage.jsonl)、[统计](p9/review-summary.json)、[源身份](p9/source-check.json)。\n\n'
md+='## Final Gate 与停点\n\n预Gate 29项通过后执行Phase Completion；最终[validation](p9/validation.json)核对稳定ID/旧问题/旧阶段字段、135维度、引用、当前源、构建与故障日志、原历史前缀、M2及未提交状态；[manifest](p9/manifest.json)保存交付SHA。这里只完成总计划§7的P9验收，不执行§10整项CCR终验/P10，也不标CCR Milestone Completed。\n\n**Working tree contains uncommitted Phase changes.** P9结果确认/commit Pending。下一入口P10（计划/未Start）是最终范围、差集/漂移、证据汇总与修复/回归建议，须单独授权；两个缺源仍是完整CCR未覆盖项，处理或范围裁决不得由本轮豁免推定。所有缺陷只留证，无生产修复/安装/push。多数技术报告、JSON、日志及.agent受原ignore规则保护，commit不是这些本地资产的备份；不force-add/不改跟踪规则。\n'
(B/'P9.md').write_text(md)
# Summary cross-layer document with exact nine references.
s='# CCR-P9 L01–L09 跨层审阅\n\n'+intro+'\n\n每条链路15项：syscall number、register、argument、width、pointer、structure layout、address、length、unit、ownership、lifetime、error code、return value、state transition、configuration prerequisite。独立行记录实际两端和失败传播；N/A会给理由（例如L08/09无新syscall号），不能以本端结论替代。\n\n| 链路 | 逐字段/失败/限制 |\n|---|---|\n'
for c in chains:s+=f'| {c["id"]} | [{c["title"]}](p9/{c["id"]}.md) |\n'
s+='\n接口事实：[chains.json](p9/chains.json)，coverage增量：[cross-layer-coverage.jsonl](p9/cross-layer-coverage.jsonl)，动态：[END_TO_END](p9/END_TO_END.md)。P8缺源保留、历史产物生成配对Unknown、5 CQ及119未修问题不因本阶段完成消失。见[P9结论](P9.md)。\n'
(B/'CROSS_LAYER_P9.md').write_text(s)
readme='''# CCR-P9 证据索引

[P9报告](../P9.md) / [跨层总览](../CROSS_LAYER_P9.md) / [INTERFACES](../INTERFACES.md)。只执行P9，Final Gate后停；P8 Partial已按用户豁免提交5f88749，两缺源暂缓；P9未commit，P10未Start。

| 证据 | 内容 |
|---|---|
| [baseline.json](baseline.json) / *.before.gz | 授权、HEAD、P8提交前manifest核对、原coverage/interfaces/findings与M2/历史前缀 |
| [chains.json](chains.json) / L01.md–L09.md | 九链×15字段，实际双方、故障传播、旧/新问题、配置与动态限制 |
| [endpoints.json](endpoints.json) / [source-check.json](source-check.json) | 121原独立端点加必要支撑；1951实际身份/链接语义与SHA零漂移 |
| [cross-layer-coverage.jsonl](cross-layer-coverage.jsonl) / [review-summary.json](review-summary.json) | 2082原责任+108补充接点，2190增量；旧40010身份及各阶段事实不改写 |
| [X03_SUPPORT.md](X03_SUPPORT.md) | 14 Linux支撑文件/6冻结条件；代码13+派生pyc1边界 |
| [findings.json](findings.json) | F0116–F0119全部字段，旧115对象保留；F0010实际首次打开顺序限定见L06 |
| [END_TO_END.md](END_TO_END.md) / e2e-attempt1–5/ / faults/ | 四次fixture构建失败、第五次完整target成功、两类实际失败与mtimer成功；命令/版本/源/产物/输入SHA |
| probes/ / probes2/ | 第一次测试桩链接失败保留；第二次原函数REF、uptime、audio三个接点probe，明确不冒充硬件全栈 |
| layout.c / layout-result.json / key-match.json / fsimg-match.json | RV64结构断言、82键序列、108当前fsimg extent比对 |
| [pre-gate.json](pre-gate.json) / [validation.json](validation.json) / [manifest.json](manifest.json) | 审阅Final Gate、保护/状态/导航与交付哈希，不是全部产品正确性认证 |

复现命令/可控替换/动态限制见END_TO_END。生产源只读；临时大产物不承诺长期存在。audit_inputs.py只读检查并写本目录；build_findings.py/build_chains.py/update_coverage.py/finalize_docs.py是本阶段证据生成器，后续阶段不得直接重跑覆盖新记录，finalize有重复完成保护。validate.py可只读重新核对当前阶段（写验证结果）；来源更新后应按Guard补证据，不伪造旧哈希。

多数主报告、JSON、原日志及.agent被既有规则忽略；可跟踪README/测试fixture与脚本不包含全部证据。未force-add、未改变跟踪策略。冷启动需携带本地忽略资料或按源码SHA和配方复现；原P0–P8证据不重写。
'''
(H/'README.md').write_text(readme)
# Establish a link target; final validate replaces this with the full final-state result.
(H/'validation.json').write_text(json.dumps({**pre,'gate':'PendingFinalStateCheck'},ensure_ascii=False,indent=2)+'\n')
(H/'manifest.json').write_text('{}\n')
# Current navigation; older detailed phase sections remain historical.
p=B/'INTERFACES.md';s=p.read_text().replace('# CCR-P1 当前 RV64 跨层接口入口','# CCR 当前 RV64 跨层接口与 P9 结论',1)
s=s.replace('2026-10-17 P4 AM端补充：','P4历史截面（非当前执行状态）：',1)
a=s.index('全部Enumerated/NotRun，');z=s.index('\n\n',a)
s=s[:a]+'P9当前：L01–L09均ReviewedStaticWithFindings，15字段/链及故障路径已核；详细见[CROSS_LAYER_P9](CROSS_LAYER_P9.md)、[逐链证据](p9/README.md)、[动态记录](p9/END_TO_END.md)。实现缺陷/能力断点和5 CQ仍保留，不标九条功能全PASS；P8两个缺源暂缓，P9未提交，P10未Start。原端点身份不变，interfaces_current.json逐链已写本轮事实。'+s[z:]
s+='\n\n## P9 当前闭合补充\n\n[P9](P9.md)为当前状态；上方P4–P8各段是当时本端补充截面，其“P9待闭合”不再是当前审阅状态。9×15字段、端点身份、失败传播和分层动态已完成，已定位断点与NotRun不隐藏。F0010实际首次开启限定、F0116–F0119新问题见p9链路表。\n';p.write_text(s)
p=B/'COVERAGE.md';s=p.read_text();a=s.index('当前阶段：');z=s.index('\n\n',a);s=s[:a]+'当前阶段：[P9](P9.md) Completed（接口审阅）；L01–L09/135字段，P9覆盖增量2190行（原2082责任+108补充接点），1951文件/239条件导航。原40010稳定ID、旧阶段字段和115旧问题对象保持；四项新问题累计119。P8 Partial已提交5f88749、两个缺源保留；P9未提交、P10未Start。详[跨层](CROSS_LAYER_P9.md)、[证据](p9/README.md)。'+s[z:]
s=s.replace('完整静态验收未通过，P8 Partial；P9不是可启动Next。','P8完整静态验收未通过，保持Partial；其后用户明确暂缓缺源、授权先提交并执行P9，豁免前置完成门槛，见P8授权回执。')
s+='\n\n## P9跨层覆盖增量\n\n原2082责任=1843文件+239条件；另补108实际接点文件，共2190条p9_review，不重做逐文件审计。1951文件细分：1772资产生产/消费边界、165接点、13 Linux支撑文本、1派生pyc；条件仅配置/接口导航。主状态只推进20条原X03主责（19 ReviewedStatic/1 BoundaryReviewed），其他行旧主审状态保留。全局状态与[review-summary](p9/review-summary.json)一致；p9_review的ReviewedStatic只限本次接口职责，不代表功能无缺陷。两个Unavailable、2689 Excluded原样保留。\n';p.write_text(s)
p=B/'CONTRACTS.md';s=p.read_text();s+='\n\n## P9跨层契约消费 — 2026-10-17\n\n当前L01–L09已按[CROSS_LAYER_P9](CROSS_LAYER_P9.md)逐字段匹配；上方P5–P8待P9措辞为历史截面。既有D17/D22、P6固定FD/固定PCB教学边界继续沿用；未批准完整POSIX/SDL或AM unprotect/free/RTC简化。F0029–31/F0054–55五CQ仍未决，不新增长期裁决。NPC周期计数直接当相对us与NEMU native 1MHz明确分离；REF/Spike二参和NPC三参regcpy不得互换。F0010首次音频开启顺序限定、F0116–F0119具体新差异有当前源和探针，均未修。P8缺源暂缓不等于上游实现已审或范围排除。\n';p.write_text(s)
# Plan status only; do not change §7 objectives or scope.
p=R/'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md';s=p.read_text();lines=s.splitlines();lines[2]='> 最新执行状态（2026-10-17）：[CCR-P9](../records/process/code_correctness_review/P9.md) L01–L09/135字段跨层审阅Completed；4项新问题累计119未修。P8 Partial已按用户豁免提交5f88749，两缺源暂缓保留；P9未提交/P10未Start。§7范围及M2不变。';lines[4]='版本：v0.3（S06仅RV64+双平台/Spike角色澄清），2026-10-17。整体计划及S01–S06已批准；P0–P7已确认/提交。P8 Partial已提交5f88749；用户明确“同意，先提交再执行，那两个缺源暂不解决”授权提前执行P9，现P9审阅Completed、结果确认/commit Pending。P10未授权。历史提交回执见各阶段记录。';s='\n'.join(lines)+'\n';s=s.replace('- P0–P7已完成/确认/提交；本轮用户授权仅提交P7并执行P8；现P8 Final Gate Partial（2项保留缺源），不可标Completed；P9/P10未开始。','- P0–P7已完成/确认/提交；P8保持Partial、两缺源按用户最新明确指令暂缓，已提交5f88749并获提前进入P9豁免。P9仅跨层审阅Completed，P10未Start；本次不推定完整CCR验收。')
a=s.index('P1基线及P2–P6审阅证据已落盘；');z=s.index('\n\n',a);s=s[:a]+'P1基线及P2–P9现有审阅证据已落盘（P8仍Partial）。当前[P9](../records/process/code_correctness_review/P9.md)、[跨层](../records/process/code_correctness_review/CROSS_LAYER_P9.md)、[证据](../records/process/code_correctness_review/p9/README.md)。P10及FINAL_REPORT仍是未来交付。'+s[z:]
a=s.index('**当前结束节点：');z=s.index('**',a+2)+2;s=s[:a]+'**当前结束节点：CCR-P9跨层审阅Completed；结果确认和commit Pending。Final Gate后停止，不修复生产源码、不进入P10。P8两个缺源仍未审、五CQ保留，完整CCR未Completed。M2/M2-P1不变。**'+s[z:];p.write_text(s)
# Five tracked navigation entries.
for name,prefix in [('README.md','npc/verif/records/process/code_correctness_review/'),('npc/README.md','verif/records/process/code_correctness_review/'),('npc/verif/README.md','records/process/code_correctness_review/'),('npc/verif/records/README.md','process/code_correctness_review/')]:
 p=R/name;s=p.read_text()
 ls=s.splitlines();ls=[f'独立CCR：[P9审阅/Final Gate]({prefix}P9.md) **Completed（跨层审阅）**；L01–L09共135字段，受控RV64启动/文件/计时/exec/exit与故障路径留证；4项新问题，累计119未修。[跨层表]({prefix}CROSS_LAYER_P9.md)、[证据]({prefix}p9/README.md)、[覆盖]({prefix}COVERAGE.md)。P8 Partial已按用户豁免提交`5f88749`，两缺源暂缓；P9未提交，P10未开始；生产源码与M2未改。' if l.startswith('独立CCR：') else l for l in ls];p.write_text('\n'.join(ls)+'\n')
p=R/'npc/verif/records/process/README.md';s=p.read_text().replace('P8未提交，P9未开始 |','P8 Partial已提交5f88749；用户暂缓两缺源并豁免P9前置完成门槛 |');s+='| [code_correctness_review/P9.md](code_correctness_review/P9.md) | PROCESS | CCR-P9 L01–L09逐15字段/故障路径；[跨层](code_correctness_review/CROSS_LAYER_P9.md)、[证据](code_correctness_review/p9/README.md) | ✅ Completed（审阅）；4新问题累计119；受控target与host seam验证分开；P9确认/commit Pending，P10未Start，两缺源仍保留 |\n';p.write_text(s)
# Completion Guard: current explicit authorization and pre-gate state.
p=R/'.agent/CURRENT_STATE.md';s=p.read_text();assert 'CCR / CCR-P9 / Active' in s
start=s.index('## 独立审阅执行上下文 — CCR');end=s.index('## Completed（M0',start)
section='''## 独立审阅执行上下文 — CCR（2026-10-17）

仅管理独立CCR；M2业务Active Execution Context不变，本节为当前权威检查点。

| Field | Value |
|---|---|
| Task / Phase / Status | CCR / CCR-P9 / Completed（跨层审阅，Final Gate后停止） |
| Current Objective | 已完成总计划§7 L01–L09/135字段与故障路径审阅；不表示实现全PASS |
| Last Completed Action | P9预Gate29项通过；交付INTERFACES/逐链/coverage/新问题/target与host证据；完成持久化和最终Guard |
| Current Working Files | P9/CROSS_LAYER_P9、INTERFACES/coverage/CONTRACTS/findings、p9证据/README导航；生产源只读 |
| Next Action | 停止，等待P9结果确认/commit及P10单独授权；P10仅Next，未Start |
| Remaining Work / Risks | P8 fceux/oslab0缺源仍未审；119未修问题含5CQ；真实GUI/音频/NPC/Spike/完整Linux本轮NotRun；历史产物配对Unknown |
| Approval / Commit | 用户“同意，先提交再执行，那两个缺源暂不解决”豁免P8前置完成；P8 Partial已提交5f88749；P9执行授权已履行，结果确认/commit Pending |
| Repository / Processes | boot_linux HEAD5f88749；Working tree contains uncommitted Phase changes；本轮隔离进程均已结束，无P9 commit/push |
| Blocked By | 无P9交付阻塞；P10启动依独立确认/commit/授权，完整CCR仍需处理两缺源或明确范围裁决 |

Completion Guard：Session授权、P9 Active检查点、队列与Git一致；预Gate通过后首次完成，无既有P9快照重复。旧115问题/40010身份/M2段及历史前缀不改；P8仍Partial而非补做Completed。恢复：[P9](../npc/verif/records/process/code_correctness_review/P9.md)、[证据](../npc/verif/records/process/code_correctness_review/p9/README.md)、p9/validation.json/manifest.json。忽略资产需随冷启动材料保留，commit不是备份。

'''
s=s[:start]+section+s[end:];p.write_text(s)
p=R/'.agent/TASK_QUEUE.md';s=p.read_text().replace('用户2026-10-17本轮仅授权提交P7并执行P8','用户2026-10-17本轮明确授权保存P8 Partial并提前执行P9，两个缺源暂缓');s=s.replace('| CCR-P9 | Active（In Progress） | 本轮明确授权；P8先提交且获提前进入豁免 | L01–L09逐字段/故障路径闭合，Final Gate后停 |','| CCR-P9 | Completed（跨层审阅） | 执行授权已履行；结果确认/commit Pending | [P9](../npc/verif/records/process/code_correctness_review/P9.md)；9链/135字段，4新问题累计119；[快照](CHANGELOG_AGENT.md#snapshot-ccr-p9-20261017) |').replace('| CCR-P10 | Pending（Planned，未Start）','| CCR-P10 | Next（Planned，未Start）').replace('P9 Active，P10未开始','P9审阅Completed、未确认/未提交，P10 Next但未开始').replace('P6消费端证据保留、P9待闭合','P6消费端证据保留、P9已按现有契约留证闭合；五CQ未决');p.write_text(s)
ch.write_text(ch.read_text()+'''\n\n<a id="snapshot-ccr-p9-20261017"></a>
## Phase Completion Snapshot — CCR-P9（2026-10-17）

- Milestone / Phase：独立CCR / CCR-P9 Completed（审阅）。CCR整体未Completed，P8仍Partial；M2不推进。
- Goal：总计划§7 L01–L09真实接口15字段/故障路径闭合，Final Gate后停。
- Completed Changes / Modified Files：P9、CROSS_LAYER_P9、INTERFACES、CONTRACTS、coverage/COVERAGE、findings/FINDINGS、p9九链/fixture/日志/校验；计划状态与五README导航；.agent独立CCR状态/队列/导航。生产源码零修改。
- Debug / Technical Findings：新增F0116 REF注入丢PC、F0117 libam uptime回绕、F0118音频打开失败吞掉、F0119 REF init签名；3 Confirmed/1 Robustness、M2/L2。累计119，86 Confirmed/28 Robustness/5CQ、H13/M79/L27，未修。F0010仅单写init，不推导正常AM首次开启失败。
- Tests / Validation：本次attempt5当前源直编与legacy受控target完整链PASS；mtimer模式同fixture成功；坏ELF/缺盘均BAD TRAP/rc1，作为失败路径观测。三host接点probe、RV64布局、82键序列、108 extents通过；先前四次fixture装配失败原样留档。预Gate29项通过；最终门槛/交付SHA见validation/manifest。旧M1/P2–P8测试仅历史，不计本次运行。
- Problems Solved：完成跨层审阅与证据责任；保留原40010 ID及旧阶段事实，消费2082责任+108接点=2190增量；1951文件身份零未解释漂移。没有修复功能缺陷。
- Remaining Risks：P8 fceux/oslab0未审；五CQ保留；历史产物完整生成配对Unknown；NPC能力、真实GUI/声音、完整REF/Spike/Linux本轮未运行。不能宣称全CCR覆盖完成。
- Confirmation Source：用户“同意，先提交再执行，那两个缺源暂不解决”明确P8 Partial保存/提交与P9前置门槛豁免；P9结果确认Pending，执行授权不替代结果批准。
- HEAD / Commit State：boot_linux `5f88749ce1a9ed814ae42b76e03b3d324d86a3fe`，P8已提交/未push；P9 Working tree contains uncommitted Phase changes，无提交授权，不自动commit。多数报告/JSON/log/.agent仍忽略，commit不是备份。
- Next Entry / Gate：P10 Next（Planned，未Start），需P9结果确认+commit+P10明确授权；两个缺源保留供完整CCR范围闭合，不自动豁免。
- Recovery Materials：[P9](../npc/verif/records/process/code_correctness_review/P9.md)、[p9入口](../npc/verif/records/process/code_correctness_review/p9/README.md)、baseline、chains、validation、manifest；/tmp大产物按源SHA/fixture/argv复现。
- Next Step：停止在P9 Final Gate；不执行P10、不修复生产源码、不安装。
''')
p=R/'.agent/DOCUMENT_INDEX.md';s=p.read_text().replace('## CCR-P8当前导航','## CCR-P8历史导航（当时停点）');s+='\n\n## CCR-P9当前导航\n\n[P9/Final Gate](../npc/verif/records/process/code_correctness_review/P9.md)、[L01–L09](../npc/verif/records/process/code_correctness_review/CROSS_LAYER_P9.md)、[证据](../npc/verif/records/process/code_correctness_review/p9/README.md)。9链/135字段审阅Completed，4新问题累计119；受控target与host接点分开。P8 Partial已提交5f88749、两缺源暂缓；P9结果确认/commit Pending，P10未Start。生产代码/M2不变；本地忽略证据须另保留。\n';p.write_text(s)
print('P9 completion persisted; run final validate before reporting')
