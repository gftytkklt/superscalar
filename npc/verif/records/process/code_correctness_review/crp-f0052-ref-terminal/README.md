# CRP F0052补充 — CPU-tests终态归属

2026-10-18。**本补充单元Completed；结果用户确认/新修改commit Pending。** 用户“提交，继续修改”确认前组并授权实际提交f3a5d0c后执行TASK_QUEUE唯一入口一个单元。F0025/F0027/F0028十三文件已提交；原F0052生产提交c1ba0bb、原Completion/确认历史保留，本单元不自动Reopen旧阶段，不推进M2。

## 计划与实现

目标：NPC DIFF=1时REF附加终态不能算作第二次NPC终态，也不能代替缺失的NPC终态。一个阶段按原版见证→最小修改→定向故障验证→双平台真实CPU全集→记录/索引/状态后停止；只修改嵌套仓库`am-kernels/tests/cpu-tests/Makefile`的现有awk判据，不增加Make选项/目标/运行步骤，不改REF日志、业务RTL或CPU测试源，不建立通用runner框架。无安装/策略裁决事项。

原实现同时识别两种终态格式，不区分ARCH；NPC与REF各打印一次GOOD/BAD后terminal=2，于是正常执行也记ERROR。反过来只有REF打印GOOD、实际NPC缺失终态时，terminal=1且good=1，会被误判PASS。这两种方向均须修复。

生产改动为一个文件11增5删：

- 根据ARCH归属终态：`*-npc`只计以数字时间戳开头的NPC事件，`*-nemu`只计带nemu标签的事件；只由选定后端的完整终态增加good/bad，选定后端的畸形/重复终态仍不能通过。
- 全日志继续检查ABORT、SIM_END、RTL watchdog；记录出现过的GOOD/BAD，拒绝NPC与REF结果矛盾等混合GOOD/BAD情形。正常同类REF附加终态不再增加主终态次数。
- 保留make退出码、NEMU原始退出码、唯一主终态、wrong精确名称/XPASS失败、NPC wrong必须BAD code1、零样例/重复summary/旧结果不得救援等既有规则。NEMU日志不暴露guest精确返回值，仍只确认BAD及工具exit1，不声称确认其guest返回值恰为1。

## 本次验证

| 验收 | 本次结果 |
|---|---|
| 原版真实见证 | 上组local/cpu-npc.log保存37项真实NPC执行后汇总全ERROR/make exit2；本轮未改写该日志。定向before/42中39符合预期，精确复现两个REF附加终态假失败和一个REF-only假PASS |
| 实际make/sh/awk定向 | 复用原F0052 check.py的隔离AM/受控后端，新增本问题输入；final/ **42/42**，脚本exit0。包含普通成功/负例、正负构建失败、工具缺失/错误退出、执行后步骤失败、缺失/重复/畸形终态、ABORT/预算/看门狗、零样例、wrong XPASS/错误code、REF-only、REF+重复主终态、REF结果冲突；每次均使用生产Makefile，未用mock替换判据 |
| 真实NPC完整入口 | 新构建37个CPU镜像，匹配当前源码的NPC执行器及当前REF；`make -j1 ARCH=riscv64-npc ... run` **exit0，36 PASS + wrong 1 XFAIL**，60.27秒，difftest ON，无分歧/预算耗尽。npc-run.log/npc-logs/real-results.json |
| 真实NEMU完整入口 | 同样37个测试、独立riscv64-nemu镜像；`make -j1 ARCH=riscv64-nemu ... run` **exit0，36 PASS + wrong 1 XFAIL**，28.96秒。逐例make-status=0，wrong原始工具status=1，其余status=0；nemu-run.log/nemu-logs/ |
| 最终一致性 | validation.json **12/12**：被测/生产Makefile SHA一致、74次真实原始日志/状态、原上组681文件清单未变、保护二进制/配置未变、嵌套生产只改一个Makefile、root HEAD及空index核对通过 |

真实入口这次由修复后的生产汇总直接返回成功，区别于上组“原命令失败后独立重判”。Npc/NEMU两次结果均为guest实际终止，不是SIGTERM观察点。

## 测试配置、复现与边界

实际argv/env/输入SHA见local/real-inputs.json及real-results.json，配方为local/check.py、real.py、verify.py。已有输出目录禁止覆盖，复现须新目录。每例.log/.make-status、NEMU.status与summary保存在npc-logs/nemu-logs；before/final为临时后端验证，不能当作CPU功能测试数量。manifest.json为必要文件SHA清单，不是测试数量。

NPC模型在执行前核对：沿用前组executor.json来源，已验收模型SHA256 `1ced513005f8e30df4d1b9b7ebcd7f2be9290dcae32304ef3f4cf971a582f208`，相关NPC源码自194d2c0至当前HEAD无差异，复制到本组独立NPC树。明确使用该模型后才以make `-o build/ysyxSoCFull`避免重建；未误用根目录旧MRET模型，未覆盖根二进制。REF/native解释器及配置前后SHA相同，NEMU子make用既有`-o <已核对解释器>`避免无关构建/自动提交。

NEMU沿用此前真实CPU测试兼容配置：`--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`，因为现NEMU linker未定义共享malloc所需_heap_end；本单元不改该链接脚本，**不声称省略此既有配置的默认NEMU命令也通过**。两平台均-j1，自动git_commit钩子置空，现有mem-test等37项完整保留。

本单元只影响cpu-tests汇总，不改变AM/RT/nanos产品执行闭包，因此不重跑RT update/msh或nanos三前台；前组真实RT结果为历史证据，不算本轮重测。未验证其他ARCH、多进程并发共享生成Makefile、任意非标准日志协议、GUI/音频/Linux。未改root旧NPC模型；后续验收继续显式核对模型身份。

生产修改在am-kernels嵌套仓库，当前HEAD6dc302a，修改未提交；根仓库HEADf3a5d0c，新报告/索引镜像未提交。嵌套历史五个未跟踪项原样保留，不纳入本批。临时夹具/源码副本/日志/JSON/ELF/bin仅local，不提交一次性测试代码与生成证据；ignored证据/.agent不随普通commit备份。

原F0052仍计同一问题，累计**34项功能修复/85未修完**不因本补充增加；其中34项原修复已确认提交，本补充待确认提交。F0026、五CQ、F0040Partial、PAL/F0043/两缺源等保持。记录与状态已同步，完成后停止；后续仅沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动commit/push/下一组或推进M2。

<a id="approval-submit-20261018"></a>
## 用户确认及分仓提交（2026-10-18）

用户“提交，然后继续修复”确认本补充已报告范围/测试配置/限制并授权分仓提交后继续F0019一个单元。648条文件清单及生产Makefile无漂移，复用12项核对/42定向和两平台真实全集；未重跑、未重复Completion。am-kernels实际提交`22791cfe514a5302b17a9ede62fb27fb77576996`，仅一个Makefile11增5删，暂存/实际集合一致，历史未跟踪项保留；根记录提交回执见local/submit-receipt.json与.agent。无push，新F0019修改不自动提交。
