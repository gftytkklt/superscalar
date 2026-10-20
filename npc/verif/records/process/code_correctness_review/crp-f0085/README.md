# CCR-F0085：递归失败传播与 fsimg 发布边界

> 最新：用户2026-10-18明确“同意执行A”；两行修复、10项同版定向验证、完整navy更新和真实nanos三前台/hello回归已完成。
> 本批Completed；用户最新“提交”已确认已报告范围并授权提交，实际回执见[提交收尾](#f0085-submit-20261018)。下方原分析/实施截面保留。

2026-10-18；**必要分析单元 Completed，生产修复未开始，发布策略待用户裁决。**
授权来自本轮“继续”和[既有唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。
F0051修复4ab9f3f及流程8f48825均已确认/提交；本轮开始根工作树/index干净，
HEAD `8f48825b2748031c693294c4c1c59d4428ce536e`。M2保持规划状态。
沿用既有CCR/CRP计划，本轮范围为消费链、隔离反例、最小候选及必要裁决，不另立业务Phase。

## 1. 实际消费链

| 位置 | 源码行为 | 失败影响 |
|---|---|---|
| navy Makefile:119–120 | `libs` 在一个shell中循环递归archive，无显式失败退出 | 首/中项失败而最后一项成功时，循环exit0；最后一项失败才向上传播 |
| :123–130 | app、archive均依赖`libs`，之后才运行LD/ar | 修复循环失败传播即可阻断本次依赖链接/归档；已有archive/build文件不因此回滚 |
| :151–155 | 单应用install先app，再直接cp到`fsimg/bin/NAME` | 早先成功的安装已写入共享目录；后项失败不能撤回这些文件，cp本身失败还可能改变目标文件 |
| :172–173 | `fsimg`循环逐项install，整行前缀`-`忽略错误 | 即使最后一项失败，外层仍继续；首/中项失败也被后项成功掩盖 |
| :177–183 | `build/ramdisk.img`依赖phony fsimg；随后cat整个fsimg，生成镜像及header | 当前会把残留旧文件与本轮成功文件一起打包；成功递归也不清理集合外旧资源 |
| nanos Makefile:43–47 | update先递归navy ramdisk，下一recipe才链接img/header/syscall.h | 递归非零时Make阻断后续三条ln；现有img/header链接通常直指navy build，不能仅以“未重建链接”证明旧数据未变 |
| nanos src/fs.c:51、src/resources.S:13、src/disk.c | files.h提供extent，NPC嵌入镜像；其他磁盘路径读设备 | 必须把header和镜像作为配对消费材料。旧配对若逐字节未变，可供原构建流程继续消费，但来源/配置没有因此被认证 |

navy Makefile SHA256仍为原P7/F0085的
`4833a5e118b786cf85145aeafd3ce4ffbaf1bba1e8eaf28bbcf6e2f5ca77e026`。
原问题、P7证据及P10台账不改写；F0074旧VME镜像错配与F0086包装源缺失仍独立。

## 2. 隔离验证结果

[probe.py](probe.py)复制完整navy/nanos Makefile，使用真实GNU Make 4.3递归和原ramdisk
cat/truncate/wc流水线；仅ISA/AM include、子应用/库构建及LD替换为可控夹具。
三个命名应用替代完整应用清单，以首/中/末准确定位失败；全部操作位于独立临时目录，
不解析生产AM Makefile，不运行产品构建、自动Git钩子、clone或guest。

每个版本10种观察：libs首/中/末失败及正常，nanos update首/中/末失败及正常，
无旧应用/镜像时的中项失败，递归make工具缺失。原版和两行候选共20种观察断言成立，
**这是失败语义的分析证据，不是20项生产修复PASS或真实guest验收。**

| 场景 | 原版观察 | 隔离候选观察 |
|---|---|---|
| libs首/中项archive失败 | 外层0，后续项继续，LD被调用 | 外层2，失败即停，LD不调用 |
| libs末项失败 | 外层2，LD不调用 | 外层2，LD不调用 |
| 三个libs正常 | 外层0，LD调用 | 外层0，LD调用 |
| update首/中/末安装失败，存在旧集合 | 外层0，后续安装继续，ramdisk被重新生成，nanos三条ln执行 | 外层2，后续项停止，旧img/header逐字节不变，nanos后续ln不执行 |
| update中项失败，无旧应用/镜像 | 外层0，缺失中项仍生成镜像/header | 外层2，无新img/header，first已安装，middle/last不存在 |
| update全部成功 | 外层0，完整三项打包，ln执行 | 同左 |
| libs递归make不存在 | 外层2，不调用LD；原循环尝试三次 | 外层2，不调用LD；候选首次即停 |

候选中项失败后的`fsimg/bin`为NEW:first、OLD:middle、OLD:last；末项失败为
NEW:first、NEW:middle、OLD:last。已存在ramdisk仍是原字节，未重新发布混合集合。
无旧集合时失败无新ramdisk，不能宣称首次失败后仍可运行。
旧fsimg中的无关用户资源在全部场景保留，未盲删旧产物。

结果、命令argv/cwd/退出码、工具轨迹、镜像/header及hash见
[analysis-02/results.json](analysis-02/results.json)与各场景子目录。
[protection.json](analysis-02/protection.json)确认188个生产/历史证据条目的mode、文件hash、
链接目标及存在性在本轮探针前后无漂移；包括navy fsimg/build、nanos src/build及原P7/P10入口。
恢复由inputs快照和probe完成，不依赖临时目录`/tmp/crp-f0085-analysis-z89u7me6`长期存在。
analysis-01保留最初夹具误将原版libs末项失败也预期成exit0而中止的输出；修正分析断言后
新建analysis-02完整运行，没有修改或覆盖原P7/P10结果。

## 3. 唯一待裁决：是否允许失败后留下部分 fsimg

两种方案都要求递归失败非零、阻断依赖消费，不将失败构建报告成成功，保留已有用户资源。
F0051批准的RT策略不作为本项navy发布批准。

| 选择 | 具体语义 | 最小改动与代价 |
|---|---|---|
| **A：失败即停，允许保留部分fsimg（推荐，未批准）** | 首个失败立即结束libs/fsimg；失败前已写的库/应用保留，失败应用自身可能留下被部分改写的目标；不执行本次后续链接/ramdisk/nanos ln。旧img/header原字节保留；首次失败不产生可用新镜像。成功重试再正常打包；不新增日常必经步骤 | 仅navy-apps/Makefile两行，完整未应用补丁见[candidate.patch](candidate.patch)。libs/fsimg循环加`|| exit $$?`，移除fsimg忽略错误前缀。既有目标、选项、应用集合及update/run入口均不变 |
| **B：整批成功后发布fsimg** | 当前fsimg在整批成功前不改；失败丢弃本批临时安装集合。用户旧资源须保留，不能清空后重装 | 至少修改安装目的地和fsimg打包/发布规则，增加临时目录及切换/恢复逻辑；若镜像/header也要求生成异常时成对回滚，须进一步明确单一发布入口。超出两行传播修复，需裁决后定向形成最小实现；不预引入通用事务框架 |

推荐A的依据：nanos实际消费img/header，失败传播已能在子构建失败时阻止它们被改写；
接受fsimg作为可重试的中间安装目录即可满足这一较小契约。A不声称fsimg本身事务性、
不认证历史旧镜像来源，也不处理打包工具自身失败、并发make/发布、掉电、VME配置切换或集合外旧文件认证。
上述排除不把现有打包工具错误传播问题宣称已修；B若被选中须先明确其实际发布单位。

本报告已给出A的具体补丁和消费链反例，生产文件未应用候选。未选策略时不能从“继续”推定A。
停点来自[根AGENTS.md](../../../../../../AGENTS.md)“继续”第4条和
[WORKFLOW_POLICY.md §3](../../../../docs/WORKFLOW_POLICY.md#3-人工确认--软件安装-停点触发即停)：
“改变功能/失败语义等真实契约取舍”须用户拍板；既有REPAIR_AND_REGRESSION第4项也明确要求
区分部分fsimg与整批发布。此处对失败后中间产物的处理正属该已列明裁决。

## 4. 策略冻结后的修复单元与验收

- A范围为应用候选两行补丁、定向失败/正常/旧产物验证及真实受影响nanos回归，另补记录/索引。
  若选B，按明确发布单位补足方案，不自动增加Make入口/选项或日常步骤。
- 定向验收检查首/中/末失败、原始递归非零及外层Make非零、无后续链接/打包、正常成功、
  旧img/header保护和首次失败。保留原版见证，修复结果必须与生产同版源码匹配。
- 实施后按影响范围执行真实navy ramdisk更新和nanos运行：pal/nterm/nslider前台切换及后台hello进展，
  记录工具/源码/配置/镜像hash、命令和实际交互证据。host夹具不能替代guest；缺环境或策略冲突时据实停下。
- 仅navy构建规则变化，不改变共享AM、NEMU/NPC、RT或cpu-tests构建，CPU-tests全集/RT不因此要求重测。
  若实际改动扩大为共享模块，按新增依赖影响重新选择回归，不直接沿用此排除。
- 完成留档后停止等结果确认/提交，不擅自commit/push、不串行修相邻问题或推进M2。

本轮生产修复、真实navy编译、nanos update/run与guest回归均**NotRun**。
F0085仍未修，其余116项含5CQ保留。Working tree contains uncommitted analysis/documentation changes；
本轮结果确认和commit Pending，无commit/push授权。日志/JSON/历史资产/.agent仍沿既定本地持久化；
可见于Git不等于完整证据已备份，未改ignore规则。
唯一下一入口仍为[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)。

<a id="f0085-implementation-20261018"></a>
## 5. 2026-10-18 A裁决与实施完成（未提交）

用户明确“同意执行A”，批准允许失败前部分fsimg/库安装残留的最小失败传播语义，
并在已知分析文档未提交时授权本轮实施；该顺序授权不等于commit/push。
决策登记D-CRP-F0085-PUBLISH-20261018；旧分析完成快照及未批准文字均保留历史含义。

**本批Completed，修复结果确认和commit Pending。** 生产文件仅
`navy-apps/Makefile`两行：libs递归archive加`|| exit $$?`；fsimg去掉忽略错误前缀，
递归install也加失败即停。既有Make目标、选项、应用/测试清单、update/run流程不变。
失败不回滚已经写入的中间安装文件；子构建失败时不继续本次链接/归档、ramdisk或nanos后续ln。
不扩写为所有打包工具异常都可回滚的事务保证。

### 5.1 同版定向验证

原分析20种观察不重写。[probe.py](probe.py)新增仅本问题的`--implementation`模式：
读取analysis-02冻结原版，断言生产文件精确等于已批准两行补丁，再只运行10种修复后场景。
完整生产Makefile副本、原nanos Makefile、真实Make递归及打包流水线均沿用；子构建/LD/AM/ISA仍受控。

本轮[implementation/local-01/results.json](implementation/local-01/results.json) **10/10通过**：
libs首/中/末失败均阻止LD，正常路径成功；update首/中/末失败均非零并保留旧img/header字节，
不执行后续ln；无旧集合时失败无新镜像；缺递归工具非零。失败前部分fsimg按A保留，
无关旧用户资源不删除。这些局部结果与下方真实guest证据分别记录，不互相替代。

生产修复SHA256 `2fcad491acc5536f54b8c52039bb6300898a1b70f3b308fc086f75064b3fd6ab`；
完整[repair.patch](implementation/repair.patch)、before/after快照及baseline均在implementation。
`git apply --reverse --check candidate.patch`通过；实际回滚仅反向本批两行且需先确认没有后续改动，
不整文件覆盖或reset/clean历史工作树。

### 5.2 真实navy更新与nanos回归

[guest_prepare.py](implementation/guest_prepare.py)从现有本机源码生成独立副本
`/tmp/crp-f0085-guest-mhmvbiki`，复制navy/AM/nanos/NEMU，排除`.git`和build；
重映射原工作区绝对软链接到副本，不让安装/磁盘写入触及原产物。已有第三方源码存在性
预检通过，不clone/下载/安装；应用/库build从空目录构建，不复用旧薄archive的绝对成员路径。
NEMU使用原有RV64解释器的逐字节副本，SHA256
`455a618de1da2d0c8b69562750640dbc977668b3acfab03f8000eb111929eb35`，不声称本轮重新编译NEMU。
配置沿用HAS_VME、FG_PROCESS及riscv64-nemu；交叉GCC 13.3.0，无项目配置修改。

| 本轮实际操作 | 结果 / 证据 |
|---|---|
| 首次`make -j4 ARCH=riscv64-nemu git_commit= update` | ccache试写只读缓存而失败；外层exit2，失败在libs→fsimg→nanos正确传播。日志guest-update.log保留，不记成功 |
| 相同update，进程环境加`CCACHE_DISABLE=1`及私有`CCACHE_DIR` | exit0，约24.58秒；完整原APPS/TESTS清单执行，没有缩小应用集合。guest-update-02.log/result保存argv/cwd/env/退出码 |
| 原ramdisk生成结果 | 108个extent的大小/offset及全部文件字节与新镜像一致；img 148,378,112 B，SHA256 `87228c1987bd3ee7c10ac4ea019c4108320b9dadd7ccd2688a0dc90aa1377703` |
| `make -j4 ARCH=riscv64-nemu git_commit= image` | exit0，真实AM/nanos编译链接；新pal/nterm/nslider/hello entry分别40046a58/400104d8/4000a72c/40005394，见guest-startup-elfs.json，非历史旧nterm |
| 新开`make ... ARCH=riscv64-nemu git_commit= run` | 使用`MAKE=/usr/bin/make -o <副本NEMU绝对路径>`冻结既有模拟器，跳过其重编译且关闭自动Git钩子；原AM→NEMU run递归真实执行。guest-01/guest.log及process.json保存命令/运行进程 |

真实guest经[guest_run.py](implementation/guest_run.py)运行，SDL使用dummy视频/音频后端；
[observe_sdl.c](implementation/observe_sdl.c)仅在宿主侧向SDL原事件队列PushEvent，并复制
原SDL_UpdateTexture像素观察。不改guest/NEMU源码、不调用内部PCB切换函数、不伪造设备读值。
事件走原NEMU SDL→键盘MMIO→AM输入→nanos events_read→set_fg_pcb→真实调度路径。
LD_PRELOAD观察库编译argv为`gcc -shared -fPIC -O2 -Wall -Werror observe_sdl.c -o observe_sdl.so $(pkg-config --cflags --libs sdl2) -ldl`。

| 时点 / 输入 | 实际显示与进展 | 该时点hello累计 |
|---|---|---|
| 初始pal | 动画画面已刷新；真实进程初始化/四个entry见日志 | 1533 |
| F2切nterm | 看到Built-in Shell与`sh>` | 2395 |
| 在nterm输入qzx并Return | 看到`qzx: command not found`及返回的`sh>`，证明切换后输入/执行继续 | 3150 |
| F3切nslider | 显示蓝色第0页 | 3988 |
| Down | 显示绿色第1页 | 4583 |
| Up | 返回第0页，整帧与原第0页逐字节相同 | 5181 |
| F1返回pal | pal继续刷新画面 | 6015 |
| Return后继续观察 | pal区域帧再次变化，持续渲染；不宣称已完成游戏流程 | 6850 |

原始8张BMP、PNG无损转存、[帧总览](implementation/guest-01/frames.png)、observe.log和guest.log保存于guest-01。
agent已目视检查nterm提示/响应、slide数字及pal画面；未将agent观察写成用户确认。
verify.py还验证两张slide的中心显示区与源BMP资源像素相同、0→1→0往返帧一致、
nterm输入前后及pal返回后的像素变化，全部阶段hello严格递增。
本次持续运行52.32秒后由监督器对自有进程组SIGTERM，make退出-15；这是受控停止，
**不是guest正常返回0**。未见BAD TRAP/ABORT/断言失败，未声称长期游戏/音频/ONS功能通过。

真实回归选择NEMU是已有HAS_VME/FG_PROCESS已稳定路径；NPC当前能力及布局限制仍按原计划保留，
不改变其配置或将本次结果泛化为NPC三前台通过。仅修改navy构建规则，未修改共享AM/NEMU/NPC或RT，
所以CPU-tests全集/RT不受本项影响，按既有模块回归契约不另测。

### 5.3 保护、完成边界与恢复

[verify.py](implementation/verify.py)及[validation.json](implementation/validation.json)记录：
7,640个原源码/资源/既有模拟器输入hash均与副本创建时一致；188条原fsimg/build/src及P7/P10
证据的mode/hash/链接/存在性也未漂移；副本及生产修复SHA一致，反向patch dry check和diff空白检查通过。
runtime ELF/BIN（原run会再次链接）另存`guest-artifacts/runtime-*`，运行前镜像/header和原image
ELF/BIN也保存，区分各次产物；guest运行可能写入的盘是副本盘。
implementation/manifest.json登记本次证据及当前测试脚本；原分析顶层manifest保留原时间截面，
README追加及probe增加实施模式会使其旧hash不同，不回写历史manifest掩盖正常变更。

F0085按已批准A完成本批验收，剩余115项含5CQ保留；F0074配置/产物认证及F0086包装源问题
不因这次副本成功update而自动关闭。没有Reopen CCR-P10或推进M2。
Working tree contains uncommitted CRP repair/documentation changes；根HEAD仍8f48825，
本批结果确认/commit Pending，未commit/push。真实产物、原始日志及.agent仍依既定本地ignored约定保存，
普通commit不能备份它们，不改变跟踪规则。

本轮完成后停止；唯一后续动作/门槛集中在[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)。
示意提交时复用本轮技术收尾，只补确认/实际提交回执，不无故重跑本轮验收或重复完成快照。

<a id="f0085-submit-20261018"></a>
## 6. 2026-10-18 用户确认与提交收尾

用户明确“提交”，确认本批已报告的修复/验证范围并授权提交；同时要求修复相关测试代码只提交必要部分，
也可不提交。复用上轮技术收尾，107项implementation manifest与生产SHA核对无漂移，本轮未重跑10项或真实guest，
不重复完成快照，不扩写未测能力。

本次修复提交范围为navy-apps/Makefile、本文README、records/process/README及本目录`.gitignore`；
本项两行修复已有具体报告和原版/修复后证据，不新增入库测试代码。一次性probe、guest准备/采集/验证脚本、
生成ramdisk.h、源码/补丁快照、日志/JSON/截图/镜像全部保留本地；本目录忽略规则仅放行README和规则自身，
防止按后缀误加大量重复产物。没有删除本地证据或清理已跟踪的历史测试；全仓ignore不变。

用户新增流程落根AGENTS.md及本地WORKFLOW_POLICY：必要验证照常执行，入库测试须具有长期回归价值且最小可维护，
否则可以不提交；报告/记录/当前状态/唯一下一入口仍需维护。F0085修复与流程规则按修改原因分别提交，
实际提交信息保存在implementation/closeout-20261018及.agent确认/提交回执。本次不push、不开始下一项或M2。

修复进度的使用入口：本批技术结果以本文及实施证据为准；records/process/README提供可跟踪导航；
`.agent/CURRENT_STATE.md`保存当前完成/确认/提交状态，`.agent/CHANGELOG_AGENT.md`保存完成快照及新增提交回执。
后续任务只从[现有CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)恢复，具体问题/契约依据仍为
原FINAL_FINDINGS和REPAIR_AND_REGRESSION，不回填原审阅台账的历史“未修复”截面。
原始证据及.agent仍本地保存，提交报告不等于备份全部资产。

实际F0085修复提交：`b7391768dd6c3060f455a4b1ab9470ead37b2134`，4文件236增2删，仅上述四份文件，无测试代码/生成证据入库。
全局流程规则另行提交；实际回执见本地closeout-20261018。原10/10、真实nanos与保护证据本轮复用，
只补当前确认和提交事实；F0085 Completed/用户已确认/修复已提交，未push。


2026-10-18 空间清理附记：用户明确授权删除工作区大型临时存档。本目录的大型归档
ramdisk或一次性完整raw测试快照已按[清理记录](../../workspace-storage-cleanup-20261018/README.md)
精确删除，原路径/尺寸/SHA见该记录local/deletion-manifest.json；原文本验收/命令/
结果与哈希保留，历史manifest缺失项须结合该授权清单解释，不视为源码漂移或验收
事实变更。旧产物字节不再本地保留，需复核时按原版本/配置重建或重新运行测试。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0085 — 根仓库

Navy 的 Makefile 已由根仓库跟踪；本处仍直接给出两行修复差异。

- 差异路径相对于仓库 `.`；旧版本：`8f48825b2748031c693294c4c1c59d4428ce536e`；新版本：`b7391768dd6c3060f455a4b1ab9470ead37b2134`。

#### `navy-apps/Makefile`

F0085：库构建和 fsimg 安装循环的每次递归 make 后增加 `|| exit $$?`，第一处失败立即以原非零码退出 shell，避免后续成功覆盖前面的失败。fsimg recipe 将忽略错误前缀 `-` 改为静默前缀 `@`，使该失败真正传到上层 make/update。正常目标与命令接口保持；此前已安装的文件允许留存，未提供 fsimg 全事务回滚。

```diff
diff --git a/navy-apps/Makefile b/navy-apps/Makefile
index d5fc27d911ac7c3db47fd0bb51ab2125a6e98ee5..0bef147470486e0235bdce7349466bebad6e3338 100755
--- a/navy-apps/Makefile
+++ b/navy-apps/Makefile
@@ -117,7 +117,7 @@ $(DST_DIR)/%.o: %.S
 
 ### Rule (recursive make): build dependent libraries (libc, libos, ...)
 libs:
-	@for t in $(LIBS); do $(MAKE) -s -C $(NAVY_HOME)/libs/$$t archive; done
+	@for t in $(LIBS); do $(MAKE) -s -C $(NAVY_HOME)/libs/$$t archive || exit $$?; done
 
 ### Rule (link): objects (`*.o`) and libraries (`*.a`) -> `$(APP)`, the final ELF binary to be packed into application (ld)
 $(APP): $(OBJS) libs
@@ -170,7 +170,7 @@ APPS = nslider menu nterm bird pal nplayer busybox
 TESTS = hello bmp-test file-test timer-test event-test audiotest cpp-test exec-test busybox-test execvp-test
 
 fsimg: $(addprefix apps/, $(APPS)) $(addprefix tests/, $(TESTS))
-	-for t in $^; do $(MAKE) -s -C $(NAVY_HOME)/$$t install; done
+	@for t in $^; do $(MAKE) -s -C $(NAVY_HOME)/$$t install || exit $$?; done
 
 RAMDISK = build/ramdisk.img
 RAMDISK_H = build/ramdisk.h
```
