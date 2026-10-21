# CRP 最终验收与收尾准备 — 2026-10-21

<a id="closure-20261021"></a>
## 用户确认与限定收尾提交（2026-10-21）

**技术验收：既有批准范围内通过；用户确认：已确认；本轮CRP修复执行按本次三README收尾提交关闭。** 用户明确确认上一轮最终结果并授权提交/关闭；实际提交身份和三路径blob核验记入本地[提交回执](submit-20261021/receipt.json)，也可由本文件Git历史查询。提交前状态为已授权/尚待执行，只有实际commit成功才记为已提交；不为将hash写入自身再扩大或追加提交。

分类固定为**109修复验收通过、6延期/Partial仍未解决、2能力移交、2无需实施闭合**。原批准依据及承接未缺失：F0029/F0073见[联合延期](../../crp-f0073/README.md)，F0030/F0054见[内存寿命联合延期](../../crp-memory-lifetime-20261021/README.md)，F0040见[Partial延期](../../crp-f0040/README.md#deferral-20261021)，F0043见[音频并发延期](../../crp-audio-lifecycle-20261021/README.md)；F0031/F0071仍在[Linux能力接收入口](../../../../../docs/LINUX_PLAN.md#npc-capability-followup-20261021)未实施；F0017/F0084的非代码闭合依据见各原报告，不计修复通过。延期项未来有实际需求须另获授权/冻结验收，关闭本轮执行不删除这些事项。

本次提交前复核881份上一轮验收文件、15,171个源/配置/正式资产、44符号链接与10嵌套仓HEAD/原差异均保持，见[precheck](submit-20261021/precheck.json)；因此复用已确认回归，不重新执行完整验收。双平台36PASS+1XFAIL保持原判定；NPC完整nanos、完整游戏、实际声音未验收，wrapper/NWM既有限制保持。关闭不意味着119项全修、全部能力实现/场景验证或代码不存在缺陷。

本次Git范围严格为process/README.md、repair-status/README.md、本文件；详细日志、配方、问题台账及.agent等仍按原策略仅本地ignored保存，commit不是全部证据备份。上一轮evidence-manifest保持为验收时快照，本次确认/状态补充产生的文档哈希变化由submit-20261021增量清单解释，不覆盖旧技术证据。

现有业务M2仅规划、M2-P1未Start保持；CRP执行入口关闭，唯一当前动作是**等待新的任务授权**，不自动选择延期项、业务阶段或其他任务。以下“收尾准备/Pending/未提交”正文为上一轮已确认验收的历史截面，当前确认和关闭以本节及实际提交回执为准。

---

**技术验收：Completed（既有批准修复范围内通过）；本次结果用户确认：Pending；本次收尾：未提交，未完全关闭CRP。** 沿用[原修复方案](../../REPAIR_AND_REGRESSION.md)、[119项修复台账](../README.md)和各批次批准边界。本次没有生产代码修改、自动修复、commit/push、安装/下载或业务阶段推进。唯一下一入口为 `.agent/TASK_QUEUE.md#crp-next`：等待用户确认最终验收并授权收尾提交。

本轮授权来自用户“最终验收与收尾准备”完整指令，覆盖状态恢复、全差集复核、隔离回归及文档留档；替代旧“收尾未Start”状态，不重开CCR-P0～P10、不产生新修复编号。Project Resume/Guard核对现行Session→CURRENT_STATE→TASK_QUEUE→各仓状态；旧计划入口与本次授权一致，无未解释的状态冲突。业务M2仅规划、M2-P1未Start保持。

## 基线、差集和归属

| 身份 | 实际状态 |
|---|---|
| 原始CCR审阅基线 | 根 `47b6c78d9b91ae0a55ba248222a7cf306c2e174e`；原P10交付 `0ee3778388c1da0eecc76af4ac82571284a5e665`，历史119项问题事实及P8缺源结论保持 |
| CRP修复开始 | 根 `2f11b081f5fc2ab5c8bebdc8bb6a0ec52c9ca61f`；嵌套基线逐仓见 repositories-before.json / preexisting-differences.json，不能用根HEAD代表嵌套源码 |
| 本次最终源码 | 根boot_linux `7398c88c0d0aa91ca4ecd62d9c204153311c29b2`；开始时根working tree/index干净；本次结束仅文档/证据变化 |
| 完整已提交差集 | 根90提交、全部仓合计101提交；根272路径，其中生产/测试92路径，嵌套22路径，合计114路径逐项复核；包括已经提交的所有批次，非只看working diff |
| 当前本地源码/配置 | 15,171个受保护文件（含必要ignored/untracked源码、配置、正式资产）、44个符号链接按实际内容/模式/目标记录并复核；本轮无源/配置漂移 |
| 批次和审批 | 76份现有批次报告；batch-evidence-audit.json关联报告SHA、根/嵌套提交及保留验证证据；finding-closure.json按119个稳定ID连接原问题、批准方案、代码路径/最终SHA、版本化验证及最终结论 |

[各仓身份](repositories-before.json)、[全部提交及改动路径](commit-audit.json)、[114源/测试差集](production-delta.json)、[原有差异](preexisting-differences.json)、[逐项闭环](finding-closure.json)、[批次证据](batch-evidence-audit.json)。各仓完整patch与working patch保留在本目录，含未提交差异；原源码位置行号是原审阅版本，不伪装成当前行号。

实际变化的嵌套HEAD：am-kernels `22791cfe514a5302b17a9ede62fb27fb77576996`；bird `80f9918b032b83ef1f0e81b0356e7cb2a2dddf6c`；ONS `5e72dbb9739ae39a3a2dc520ed89f20219e92f84`；PAL `a744ceedd5797135d045fcc2e36cfe3fda4740c0`；newlib `8101fad4376b7df0e3ec18db2db8cfa32746ad3a`。未变化的riscv-tests/env、fceux-am、busybox、Spike也单独核对。完整40位值以repositories-before.json为准。

原有无关差异继续保留：嵌套文件模式、riscv-tests/env适配、fceux emufile、bird Video.h、busybox文件、PAL历史删除/符号链接/main.c、ONS字体编码行及am-kernels未跟踪测试等。九个嵌套working diff与修复起点一致；ONS diff上下文随修复改变，但未提交内容仍是原DEFAULT_ENV_FONT编码行（原提交回执排除项），未纳入本次修复/收尾提交。root修复区间内独立批准的宿主性能 `a52ca9e` 和99:1调度 `7e0c97e` 单独识别，不计CCR-F修复数量；流程、存储维护和文档提交同样非生产修复。未发现未经批准的重构或功能扩展。

## 119项闭环结论

| 分类 | 数量 | 结论 |
|---|---:|---|
| 已修复且验收通过 | 109 | 仅各项批准范围；原始问题分类不改，本次用户确认Pending |
| 已修改但尚未满足批准验收 | 0 | 不把下面Partial计入此列或通过数 |
| 批准延期/Partial，仍未解决 | 6 | F0029、F0030、F0040、F0043、F0054、F0073；F0040串行已修但并发/异常/析构不完整，整项不算Fixed |
| 能力移交、未实施 | 2 | F0031、F0071由既有Linux计划接收；不计修复、不推进对应阶段 |
| 无需实施的批准闭合 | 2 | F0017（未选QEMU参考源）、F0084（选定Linux启动目标无需libam heap）；不计已修 |

六延期不是本轮新增豁免，也没有改契约/扩排除范围。原缺源fceux/navy oslab0仍未审，沿用P10已有用户豁免。**本结论不表示119个缺陷均已修复，也不表示平台全部功能正确。** 所有行都保留原证据、方案和历史提交；完整映射见finding-closure.json及FINDINGS追加字段。未发现需要新返工授权的缺陷，当前技术待决策项无。

特别边界：F0086验收为源列表指向现行nanos磁盘源码，完整nanos-lite-guest仍有五个VME符号链接缺口，运行NotRun；F0110为已批准的最小NWM状态/EOF修复，真实host合成链历史通过，标准native仍有getenv/strtol声明构建问题，RV64 NWM不宣称通过。这些是原批准范围，不是本轮免测。F0107/F0108历史修复版ONS实际输入进入制作信息/标题菜单的证据保留；本轮重测字体生命周期，标准盘不代表已替换所有ONS，完整游戏/对白/声音未验收。

## 差集及影响范围复核

按完整patch和最终源码检查调用链、共享结构、条件选源、返回值/位宽/单位与状态转换。未受影响模块引用原审阅，不重做全仓CCR。

| 范围 | 复核重点与结论 |
|---|---|
| NEMU ISA/MMU/内存 | W运算模运算、高PA检查先于窄化、异常PC/rd/内存副作用、访存失败传播、边界INV/FENCE.I；共享riscv32目录按RV64配置审阅。后续inst/mmu提交未撤销前批修改 |
| NEMU宿主/设备 | host读取对齐、disk偏移/长度、SD方向/容量、音频配置失败/重开；FIFO竞争F0043仍明确延期，串行生命周期通过不覆盖并发安全 |
| DiffTest/monitor | NPC REF初始化签名、NEMU DUT regcpy调用差异、分段镜像同步、拒绝错误段、注入异常目标PC、诊断与失败退出；本轮真Spike仅golden角色 |
| AM/klib/启动 | CTE上下文/ABI、VME分配失败、页表权限/地址、GPU尺寸、RTC能力声明、ramdisk boot拷贝及SRAM静态界限；VME/MPE平台能力和内存回收延期不混为同等能力 |
| nanos内核/镜像 | 108项盘几何/字节与RV64 ELF布局，loader正常/坏ELF/分配失败、exec参数边界、brk errno和拒绝副作用、设备读写单位/EOF、调度及boot依赖；补充批次errno变更已反映到最终夹具 |
| RT及am-kernels | CPU结果分类、错误样例XFAIL、时钟及中断返回切换、AM应用集成；生成脚本原为ignored源码，其Git整文件新增不等于166行全部新设计 |
| Navy/newlib | reentrant errno、sbrk、calloc/fwrite/格式化边界；NDL事件/时钟/视频、SDL事件/定时器/RWops/CloseAudio所有权、mixer音频输入与完整配置；跨批文件依赖已用当前实现重测 |
| 应用与资源 | BDF/nterm裁剪、bird Sprite、PAL RIX、ONS字体缓存/RWops生命周期、NWM最小合成链；实际资源与旧盘程序区分，未将旧二进制验证冒充全部新源码通过 |
| 非目标分支 | MIPS/LoongArch仅已有共享INV接口适配，非新增ISA验收；RV32、其他AM/OS平台不重新纳入。RT/宿主工具作为既有支持保留 |

## 本次最终源码回归

以下均为本轮当前输入重建/执行，不拼接不同历史版本为“最终版本全过”。历史批次的专属边界/反例结果继续按原commit引用；本轮重跑受跨批影响的关键定向与组合链路，不宣称所有原始测试逐条重跑。实际argv/cwd/env、退出码、源/配置SHA、工具版本与日志在对应JSON/目录；配置原文保留configurations/，工具见tool-environment.json。

| 路径 | 最终实际结果 | 证据 |
|---|---|---|
| 当前NEMU native + shared REF | 两者新建exit0；native builtin GOOD；现有M1-P9 REF ABI检查PASS；不覆盖默认REF | engine/builds.json、binaries.json、static-smoke.log、ref-abi.log |
| RV64 NEMU CPU | 37例：36PASS + wrong XFAIL，make0 | nemu-cpu-final.json/.log |
| RV64 NPC CPU | 当前RTL新建、DIFF=1使用本轮REF；37例：36PASS + wrong XFAIL，make0 | npc-rt/npc-build2.json、consumers-builds.json、cpu-results.json |
| RT双平台 | 当前AM/BSP update/image均0；NPC DiffTest ON到msh（133.6s），NEMU到msh+2s（2.41s） | npc-rt/rt-current-result.json、rt-nemu/build-results.json、standard-nemu-result.json |
| 标准nanos/Navy组合 | 原入口make update0；运行8观察点，nterm真实qzx输入/提示、slides翻页/返回帧相同、PAL中文标题，hello持续37→168；108连续盘项逐字节吻合，48 RV64 ELF几何合法，4启动程序与本轮构建一致 | standard-path/update-final-result.json、final-run/result.json、geometry.json、visual-qa.json及PNG |
| RTC能力 | 两平台真实软件handler返回has_rtc=false，固定日历和uptime行为保留；原rtc_test三行观察 | rtc/commands.json及运行日志；NPC handler在NEMU guest中重命名调用，不宣称NPC RTL RTC查询已测 |
| NEMU→golden/REF分段装载 | 当前DIFF NEMU新建；fw/kernel/dtb首指令前全部同步、真Spike/本轮REF通过；四个漏段/错段故障正确拒绝；native/builtin正例通过 | golden/tests.json、results.json、new-diff-identity.json、golden-identity.json |
| 定向host回归 | 31次最终成功命令：CPU算术/高PA/INV、AM VME分配失败、RT、disk、ELF/exec/brk、errno/newlib、事件/定时器、NDL/RWops、BDF/nterm、bird/PAL、ONS字体、音频格式和跨层生命周期；含普通/ASan/UBSan/负例，具体组合按各脚本 | replays/final-replay-results.json及各目录结果/日志；不是31项CCR-F或31个单例 |

新NEMU native SHA `14c590b6a774bfb46ee46c0432c6a8e2cf6b517adf9b9cb6cc76227babc322a9`，新REF SHA `5babebde35f21a654a9c2748a5b80fa4a3e7f2f8754df6ccaee352c77511773e`；标准nanos运行另用隔离标准构建native，身份由standard-path输入清单及configurations/identities.json区分，不混作同一个二进制。

可重复性与失败说明：NEMU CPU采用既有`-j1`和`--defsym=_heap_end=_heap_start+0x8000`测试兼容参数，冻结本轮已建native避免guest LDFLAGS污染宿主递归构建；第一次污染导致未执行guest的构建失败保留nemu-cpu.json。RT-NEMU采用既有测试布局补充片段rt-extra-test.ld（通过环境LDFLAGS追加），第一次命令行覆盖链接参数失败保留build-attempt1.json。F0061/F0089/F0090旧夹具因后续有效ELF/errno/CloseAudio接口变化不适用，先保留失败日志，再只调整测试夹具/链接桩，最终结果在final-replay-results.json；未改生产代码、未削弱原错误路径判据。F0089最后独立mm-final运行exit0，旧adapted-retry-results的失败是先前尝试。所有故障注入/原版失败均按预期计，不当作当前生产回归失败。

RT和nanos是达到明确观察点后终止本轮自建进程组：NPC RT和nanos exit=-15，NEMU RT终止处理后exit0；都不是guest自然退出证明。dummy SDL仍经过真实键盘事件路径，截图验证可见内容；不证明实体显示/扬声器/完整游戏。NEMU CPU布局参数与RT-NEMU片段代表测试兼容方式，不宣称未附加参数的默认构建通过。NPC CPU/RT并不意味着完整nanos/虚存/图形平台对等支持；F0031/F0071限制保持。

## 隔离、清理与持久化

执行前检查Make/脚本副作用：复制当前源码及现存资源到本轮隔离目录，禁止网络拉取，使用git_commit=、冻结适当构建目标或`-o compile_git`抑制自动提交；原嵌套源码、正式磁盘/镜像、默认REF/配置只读，未停止无关任务。受保护输入核验见protection-pre-docs.json与protection-final.json。本轮隔离副本/对象/可执行产物及重复BMP已按既有策略清理，完整清单/哈希见cleanup.json；PNG、日志、结果、源码/配置身份与完整差集保留。未清理任何历史批次或原工作区产物。

测试配方和最小fixture源码统一封装在recipes.tar.gz（忽略资产），成员逐字节核验后移除本轮散落副本；recipes-manifest.json列SHA。解压到新隔离输出目录，按保留脚本和身份重建；日志中的旧cwd/argv是真实执行路径，清理后不能直接当成现存产物。依赖现有本地工具、嵌套repo/符号链接目标、资源和指定历史commit；不承诺单独root clone即可复现。

Git待提交仅本轮可归属文档：records/process/README.md、repair-status/README.md、本报告README.md。其余FINDINGS/findings.json、REPAIR_AND_REGRESSION、COVERAGE、CONTRACTS、INTERFACES、BUILD_PATHS、EVIDENCE_INDEX及本轮JSON/log/patch/config/recipes/PNG、.agent状态为现行ignored本地资料，未force-add、未改忽略策略。原嵌套仓未提交差异不纳入收尾。现有本地持久化约定覆盖本次证据；没有新增持久化策略裁决，但普通commit不会备份这些本地资料，冷启动/迁移须另行携带。asset-retention.json及evidence-manifest.json记录实际分类/身份。

## 停点

本次技术结论可供确认，**尚未获用户确认、尚未收尾commit，CRP不宣称完全关闭**；各批既有确认/提交事实保持。六延期/两移交保留各自后续归属，本次没有新返工项。用户下一回复可为：“确认最终验收，授权提交本次收尾文档；保留延期、移交及验证限制，不推进下一任务。” 提交前只核对本批收尾和归属，不重新执行已验收回归。没有自动下一任务。
