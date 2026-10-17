# CCR-F0051：失败传播与发布边界分析

> 最新状态：A修复与本批验收Completed；用户2026-10-18已确认报告范围并明确授权提交，
> 见[提交收尾回执](#f0051-submit-20261018)。下文原分析/裁决/未提交截面保留。

2026-10-17；**本分析单元 Completed，生产修复未开始，发布策略待用户裁决。**
授权来自本轮“继续”及 [CRP 唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。
前置F0015/F0052及上批文档已确认/提交，根HEAD为
`9402822f1d3705467151ea81504dd0b6d8550111`，开始时根working tree/index干净。
M2保持规划状态，本分析不Reopen已闭合的CCR审阅阶段。

## 1. 源码与消费链

| 顺序 / 位置 | 当前行为 | 失败后的影响 |
|---|---|---|
| 生成脚本32–34 | 先以`w`打开`build/ARCH/am-apps.mk`和共享`build/am-apps.c` | 尚未检查工具就截断旧文本；单独调用时ARCH父目录不存在也可能失败。Make update只预建该目录 |
| 43–50 | 库不存在时调用make；随后nm读符号 | make及nm状态均忽略；nm失败/空stdout会向符号集加入空字符串，后续继续 |
| 52–58 | 应用make后`copytree(..., dirs_exist_ok=True)`，遍历目标目录所有`.o` | 失败make可以复制旧build；合并复制不移除旧目标目录独有对象，会重复变换旧对象 |
| 59–74 | 工作目录共享`redefine_sym.txt`，逐对象原地调用三次objcopy后写SRCS | 三次状态均忽略；失败后仍继续变换和登记对象，不保证对象内容完整 |
| 75–末尾 | 逐应用输出C包装函数，最后关闭mk/C | 中途Python文件异常会非零退出，但此前文本/对象已改变；非零退出本身不能恢复旧集合 |
| BSP Makefile 23–25 | `-include files.mk`、`-include build/ARCH/am-apps.mk`，再include AM Makefile | mk缺失可静默省略集成。删除mk不等于阻止后续构建；残缺但语法有效的mk可被消费 |
| AM Makefile 49–64、108–134 | `.o`条目映射到`build/ARCH`后直接链接；C条目用工作目录相对路径编译 | mk是对象/C的清单。仅原子替换两份文本、但原地改对象，仍可能混用新旧内容 |
| BSP Makefile 44–50 | 显式update调用Python；无忽略错误前缀 | Python非零会使该update失败；后续另一次run不依赖update成功状态 |

依据：[原问题](../FINAL_FINDINGS.md#ccr-f0051)、[P5](../P5.md)、
[消费链历史](../BUILD_PATHS.md)、[契约](../CONTRACTS.md)C-A13/C-A14/C-X04与S03。
脚本SHA256仍为`3775d2d5d0109f0bb0a9953b9e6dcf9509fb5d82ebb834496a1c7ef3d6e72166`，
与原审阅一致。当前`build/am-apps.c`跨ARCH共享；隔离mk而继续覆盖共享C不能形成集合边界。

既有入口是**先单独update，再新开一次make run**。同次`make update run`会先解析旧mk，
目标间也无生成后重解析契约；不把它当作新集合验收方式。同目录并发update/run、掉电持久性、
外部手改产物及上游make成功却保留过期输入对象的全面来源认证不在本修复候选内。

## 2. 本轮补证：仅隔离host/fake

保留P5原`generator-failed-make.log`（0字节）、`generator-failed-make-output.mk`、
`final-probe-results.json`及`run_final_probes.py`；未运行旧runner或覆盖旧证据。
本轮 [probe.py](probe.py) 将**未修改的生成脚本**复制到独立临时目录，
make/nm/objcopy全部为受控工具；源对象仅为带标记文本。消费者探针使用原BSP Makefile副本，
仅AM include由无副作用stub替代，运行inspect；不解析生产AM Makefile，不执行update/run。

| 场景 | 脚本 / make退出码 | 观察 |
|---|---|---|
| 工具均成功 | 0 | 四个输入对象之外，旧目标`previous.o`也进入mk（共5条对象行） |
| 四个应用make均exit7 | 0 | 继续复制预置旧输入并发布5条对象行 |
| 两次nm均exit9 | 0 | 继续发布mk/C，错误不传播 |
| 每次objcopy先写部分内容再exit11 | 0 | 继续登记对象；旧目标也被再变换，旧集合哈希已变 |
| 最后snake的输入目录缺失 | 1 | 前三个应用已写入；含旧目标共4条对象行，旧mk/C被改写 |
| 消费端mk存在 | 0 | SRCS含stub内核、AM对象及C |
| 消费端mk删除 | 0 | SRCS只剩stub内核；没有因缺少集成而拒绝 |

这些是**原缺陷的观察结果**，不是修复后7/7 PASS，也不是RT真实构建或guest验证。
命令、cwd、退出码及前后hash见[analysis-results.json](analysis-results.json)，
每场景stdout/stderr/mk/c/tools.jsonl独立保存在本目录。
临时副本位于`/tmp/crp-f0051-analysis-h72mlvs9`；恢复不依赖该目录长期存在。
原生成脚本、BSP/AM Makefile另存`inputs/*.original.txt`，复制后hash与运行前baseline一致。
probe.py本轮读取工作区中匹配该baseline的输入；修复后重现原缺陷时，应在新隔离夹具中
使用上述快照，不能直接对已修源码重跑并覆盖本轮结果。probe已有同名结果拒绝覆盖保护。

## 3. 唯一待裁决：失败后旧集合是否仍可消费

两方案共同要求：所有make/nm/三步objcopy使用argv数组并检查退出码，文件异常非零；
打印失败步骤/应用/工具状态，失败make不得再复制该应用旧build；只在本批私有位置处理
符号表/新对象，阻止目标目录残留对象被混入；四个应用均有对象才允许成功发布。
不改应用集合、ARCH/CROSS_COMPILE入口、AM API或RT运行时。

| 选择 | 明确语义与最小实现 | 生产文件边界 / 代价 |
|---|---|---|
| **A 保留上次集合（推荐，尚未批准）** | 同一ARCH的新C/对象存入独立生成目录；mk全部引用该目录。完成所有构建/变换及关闭文件后，最后用同文件系统原子replace切换**一个mk入口**。失败清理本轮临时集合，旧mk及其C/对象逐字节不变；首次失败无新mk，仍沿用默认未集成行为 | 预计仅`rt/bsp/abstract-machine/integrate-am-apps.py`。需要独立输出路径与旧目录保留/清理；不在失败路径删除旧入口引用目录。已有历史旧集合仅保持原字节，来源Unknown不因此被认证为有效 |
| **B 失败后禁止构建/运行** | update在任何正式输出改动前设置失效标记；成功完整发布后最后清除。Makefile在读取无效mk和包含AM规则前拒绝消费，失败后必须成功单独update才能run；更新重试和clean仍须可用，首次从未update仍维持默认不集成。生成C需按ARCH隔离，避免失败污染别的平台 | 至少脚本+BSP `Makefile`。需覆盖默认image、run/gdb和其他消费目标；防止残缺mk在重试前解析失败；不能仅删除mk。增加持久失效状态和恢复门禁 |

A符合现有mk消费方式，不增加Make消费端状态机，因此推荐A；这只是建议，不记入DECISIONS。
“先replace C，再replace mk”不是集合原子发布；复制进旧对象目录后仅推迟写mk也不足。
A的单入口方式只覆盖本地顺序update→run及所声明的失败，不承诺通用事务框架、并发发布或掉电恢复。
具体无引用目录清理可作常规实现细节，但不得为了清理损坏仍被旧入口引用的目录。
B是更强的失败后停用契约，需用户明确接受；不能从“工具失败非零”推定已获批准。

## 4. 策略确认后的一个修复单元

范围：按已选方案只修改上表生产文件，另增本问题定向验证/证据及现有索引/状态。
若消费端验证表明必须改变更多生产文件、链接布局或既有稳定配置，先报告具体原因。
不顺带修F0049、F0054/F0055、F0085等问题，不修改共享AM/NEMU/CPU实现。

后续验收采用少量有区分力的情形，不另建通用runner：

1. 正常四应用及一次重复update：无旧目标孤儿对象混入，mk/C/对象同次发布；缺对象非成功。
2. 库不存在时make失败、应用make失败且旧输入存在、nm失败；必须非零，后续依赖步骤不运行。
3. 三个objcopy步骤分别失败（分布到首/中/末应用）；另测一次末应用复制异常。
   A逐字节核对旧mk及其全部C/对象不变；B核对消费端拒绝并允许update重试恢复。
4. 首次失败及已有集合后的失败各一次；成功重试后新make解析新清单。
   验证PATH中工具不存在也非零，清理不掩盖原始失败。
5. **真实RT功能验收**：使用受控副本及现有已稳定RV64平台/配置，真实update成功，
   新make run实际到达msh。记录源码/config/工具/镜像hash、命令、日志及退出/到达判据；
   按已有契约规避自动Git构建钩子，不用fake替代guest。若缺环境/安装/必须改变配置则按规则停下。

选择RT真实回归的依据是本次修改其生成与链接输入；未修改共享AM/NEMU，CPU-tests全集与
nanos三前台回归无需为本项额外执行。本轮上述修复后验收均**NotRun**，没有任何真实guest新结果。

## 5. 本轮交付与停点

本轮新增分析报告、probe及证据，追加REPAIR_AND_REGRESSION与记录索引；更新CURRENT_STATE、
TASK_QUEUE、CHANGELOG_AGENT及DOCUMENT_INDEX导航。生产脚本、Makefile、原build及历史
P5/P10证据未修改，保护核对见protection.json；证据hash见manifest.json。
Working tree contains uncommitted analysis/documentation changes；本批结果确认Pending，
commit Pending，无commit/push授权。ignored资产沿用本地持久化，未改变跟踪规则。

下一入口只保存在[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)：
等待用户选A/B、确认本轮结果及完成提交门槛，再授权实施。未选策略时再次“继续”不默认选A。

按根[AGENTS.md](../../../../../../AGENTS.md)“继续”第4条及
[WORKFLOW_POLICY.md §3](../../../../docs/WORKFLOW_POLICY.md#3-人工确认--软件安装-停点触发即停)，
“改变功能/失败语义等真实契约取舍”须交用户拍板。上述发布失败后的可用性正属该取舍，
因此分析完成后在此停止；F0051生产问题仍未修复，其余117项口径不变。

<a id="f0051-a-approval-20261017"></a>
## 2026-10-17 A策略确认与update语义澄清

用户明确“同意A”，并规定正确性修复原则上不新增或删除Makefile选项、执行流程，
除非与功能正确性冲突。**A发布策略Approved**；采用新C/对象集合全成功后切换单一mk入口，
失败保留旧集合。预计仅修改生成脚本内部，不修改BSP Makefile，不引入新的开关/目标、
失效门禁或日常运行必经步骤。该约束已同步根AGENTS和WORKFLOW_POLICY。

两个项目的同名目标语义不同：

- `nanos-lite/Makefile:40`已有update，调用navy的ramdisk构建并更新镜像/头文件链接。
- `rt/bsp/abstract-machine/Makefile:47`也已有update，调用本问题的AM集成脚本，
  与ramdisk无关；Makefile:24读取已有集成mk，普通run无需先调用update。

前文“先单独update，再新开make run”只适用于**主动重新生成AM集成产物后的验证**，
不应被读为RT每次启动的必经流程；不因本次修复把默认run改成自动生成或强制要求update。
后续本问题的生成器验收仍需实际触发已存在的集成路径，并验证既有run到msh；
这是验证所改路径，不能据此增加用户日常命令步骤，也不能以nanos更新ramdisk代替RT集成验证。

“集成失败”指构建/读符号/对象变换/复制任一步没有正确完成。本问题是这些失败可能被
脚本吞掉或留下部分输出，不是已经证明AM应用在真实RT里都不能运行：有旧对象时可能
继续链接并运行旧版本，残缺/不兼容对象可能导致后续链接失败；首次未集成时RT本身也
可能启动但没有相应AM命令。当前仅有隔离host/fake反例，真实RT编译/运行故障尚未证明。

本轮只读核对上述两份Makefile及生成脚本；未重新运行探针或guest，生产文件未改。
只记录明确的A策略批准，不从“同意A”推定全部分析证据已获确认或已commit；
本批分析确认/提交门槛仍见[唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，
本次没有生产实施或commit/push指令。原manifest中README的hash随本附记改变，
旧manifest和完成快照不重写，原动态证据保持。

<a id="f0051-implementation-20261017"></a>
## 2026-10-17 A方案实施与本批验收

**CCR-F0051修复 Completed；修复结果用户确认Pending、commit Pending，未push。**
用户在已知分析/裁决文档未提交后明确“执行修改”，据此授权按A继续本批实施；
这是本批执行顺序授权，不推定已commit、允许commit/push或全部历史证据获确认。
根HEAD仍`9402822f1d3705467151ea81504dd0b6d8550111`；已有未提交文档可由前两轮解释，Guard无冲突。

### 生产改动

仅修改`rt/bsp/abstract-machine/integrate-am-apps.py`：

- make/nm/三步objcopy均改为argv数组及受检返回码；缺库时用已有archive目标生成所需库。
  文件/工具异常非零退出并报告，失败后不继续复制/发布；空对象目录也拒绝成功。
- 每次在`build/ARCH/am-apps/gen-*`私有目录生成C、复制并变换对象；mk仅引用本次集合。
  全部成功并关闭文件后，最后原子替换`build/ARCH/am-apps.mk`这一个入口；失败清理本轮目录，
  旧mk、旧C和旧对象保持原字节。旧成功集合保留到原有clean清理，不增加清理选项或用户步骤。
- 不修改BSP/AM/NPC Makefile、默认run行为、应用集合或运行时C模板；未增加/删除Make目标、
  选项或日常运行流程。生成文件内部路径变化由mk承接。

最终脚本SHA256：`32fcba79da06ca97ed5091599097c81f17caa61446b6b4a0df1191eadea08b10`。
补丁/回滚入口为`implementation/repair.patch`；原版快照仍在inputs，最终源码另存
`implementation/generator.after.txt`。反向patch dry-run通过，执行回滚前须先核对工作树。
该生产脚本当前受Git忽略；本轮未force-add或改变跟踪规则，提交不会自动备份全部本地证据。

### 定向验证：原版见证与最终结果

[check.py](implementation/check.py)只用隔离host/fake对象验证失败传播与发布契约，
不代替guest。13个场景涵盖正常/重复发布、库make失败、应用make失败且旧输入存在、nm失败、
三步objcopy分别在首/中/末应用写入后失败、末应用复制缺失、零对象、缺工具、首次失败及失败后成功恢复。
对失败场景比较整个旧输出树hash，检查无部分文件发布；对成功场景核对4个输入对象、
无旧目标孤儿对象混入、C/对象引用同一集合、重复成功保留旧集合。

- 原版同组检查 **0/13满足修复契约**（整体退出1），记录在`implementation/before-02/`。
- 最终版本 **13/13通过**（整体退出0），记录在`implementation/final-03/`。
- 首轮验证发现Python 3.12的mkdtemp返回绝对路径，导致正常路径relative_to失败；
  已将生成目录规范为工作目录相对路径并完整复验，初轮10/13和中间结果保留于after/final。
  最终版发布入口替换后没有额外可能报错的输出步骤。

### 真实RT回归

在`/tmp/crp-f0051-guest-s3rb4wic`复制RT、AM和四个AM应用源码，排除原build/Git；
只将files.mk中的绝对RT路径重定位到副本。真实交叉工具链完整生成四应用，
mk引用**16个对象+1份本次C**，四个应用入口和msh导出符号均进入RT ELF。
最终脚本真实update退出0；此前一次成功生成也保留，旧/新集合互相独立。

随后通过已有`make ARCH=riscv64-npc run`调用链运行真实NPC guest，
仅在测试命令中复用原仿真器/REF并禁用自动Git钩子，未改生产接口：

```text
make --no-print-directory -j4 -o build/ysyxSoCFull ARCH=riscv64-npc \
  DIFF=1 WAVE=0 WITH_TRACE=0 WITH_SDL=0 PERF=1 PERF_R45=1 git_commit= \
  'MAKE=/usr/bin/make -o build/ysyxSoCFull' run
```

仿真输出RT 5.0.1启动信息、`Hello RISC-V!`、`msh />`提示符，help列出四个am_*命令，
difftest ON，至停点无比较分歧或BAD TRAP。**真实RT生成/链接及run到msh验收通过。**
连续运行guest在180秒由本次监督进程对自有进程组发SIGTERM停止；make状态-15是受控终止，
不声称guest正常退出或GOOD TRAP。预置序列尚未执行到am_hello，本批不声称四应用运行通过。

初次运行夹具的父make `-o`未传递至NPC子make，导致副本中不必要的仿真器重建失败；
调整测试用MAKE变量直接把该选项传到子make后，复用原仿真器启动，原生产文件不受影响。
原采集器又因只匹配`msh >`漏掉带路径的`msh />`，raw结果保留false；
已用原始串口日志修正里程碑判据并保存补充验证，未重写原结果或重跑guest冒充新证据。
最终以`implementation/guest-milestone-validation.json`及guest-run.log为准。

ELF 258,016 B；BIN 245,016 B，BIN SHA256
`ac8f1c5e448b0464e5cf7601f74969d67922dca7824ea1bfc2bdba570bcb872b`。
工具版本、1604个副本源码身份、生成清单/hash、ELF/BIN、仿真器/REF hash、所有命令与原日志
均在implementation的guest-*证据中；最终本地产物另存guest-artifacts。

### 范围、保护与停点

未修改共享AM/NEMU或nanos，故本批不额外执行CPU-tests全集、nanos前台切换；
没有以host/fake代替受改RT路径的真实guest回归。原RT build的531个文件、BSP/AM/NPC
Makefile、UART预置命令及原模拟器/config保持，HEAD未变、index无暂存。
保护与反向补丁检查见`implementation/protection.json`；本轮hash清单见implementation/manifest.json。
原分析manifest及历史P5/P10证据不改写，README后续附记差异有明确来源。

Working tree contains uncommitted CRP repair/documentation changes；修复结果确认和提交门槛待用户完成。
F0051不再计入待修复问题，其余116项含5CQ保留。仅本批Completed，不推进M2或自动开始其他项。
唯一下一动作/门槛仍在[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本批结束后停止。

<a id="f0051-submit-20261018"></a>
## 2026-10-18 用户确认 / 提交收尾回执

用户明确“提交本轮改动”，确认本批已报告范围并授权提交归属明确的修复及验证资料；
四应用实际运行仍未测，不因提交授权扩大验收。上一轮已完成本批收尾，本次复用完成快照，
只补批准/提交事实、流程规则与唯一下一入口，不重复归档或重跑已有13项/真实guest。
提交前复核最终源码SHA与已验收版本一致，implementation manifest的363项hash零差异，
原报告hash也匹配；原Makefiles和RT build保持，无新产品改动或动态测试。

本次按用户授权精确加入原受忽略的生产脚本，并提交本批报告、三个分析/验证脚本、
原分析产生的可跟踪C/mk见证与记录索引。未修改ignore规则；原始日志/JSON/镜像、
WORKFLOW_POLICY及.agent继续本地持久化，不force-add或宣称已随commit备份。
实际提交hash和终检回执记入本地REPAIR_AND_REGRESSION及.agent，避免为回填自身hash重复提交。

流程规则另行提交：无真实未决项时同轮执行修改/验证后总结；收到“提交”时补齐或复用收尾。
本次提交后停止，不push、不执行F0085或推进M2。原完成快照和历史manifest保留。
