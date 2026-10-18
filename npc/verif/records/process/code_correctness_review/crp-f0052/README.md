# CCR-F0052：cpu-tests 判据最小修复

2026-10-17。**Completed（隔离 host/fake 局部验收）；结果待用户确认，未 commit。**

## 授权与范围

承接本对话第一阶段准备与既有 [修复计划](../REPAIR_AND_REGRESSION.md)。用户本轮明确
继续实施 F0052，要求最小修改、保留 `make ARCH=xxx ALL=xxx run` 入口和选项，
仅补充必要信息，不建立通用测试协议，不自动提交。本授权允许在 F0015 未提交的
现状下执行本批；不表示 F0015 结果已确认或提交。没有重新开展全量审阅。

Guard：根分支 boot_linux，HEAD `2f11b081f5fc2ab5c8bebdc8bb6a0ec52c9ca61f`；
F0015 一行源码、报告和索引未提交状态与准备轮一致。am-kernels HEAD
`9c433f7cf4b4e05d09543bf7e269b23502d1b2b6`，其既有未跟踪项保持。
riscv-tests/env 的 HEAD、修改、未跟踪状态保持，见 baseline.json、protection.json。
M2/M2-P1 不变，不 Reopen CCR-P10。

## 最小生产 diff

仅修改嵌套仓库 `am-kernels/tests/cpu-tests/Makefile`：**41 行新增、14 行删除**。
该文件不由根仓库跟踪；根仓库 commit 不能代替 am-kernels 的提交。

- 删除 `grep -q | grep -v` 的错误汇总。汇总仅接受 PASS、XFAIL，拒绝零条、
  条数不符、重复或格式错误的记录；发现源文件的 find 失败也产生不可满足的目标。
- `wrong` 是精确名称的既有负例：正常 GOOD TRAP 为 XPASS，整体失败；正例 BAD
  TRAP 为 FAIL。没有按字符串过滤删除 wrong，也没有修改任何测试 C 文件。
- 通过已有 `NEMU_EXEC` 变量保存模拟器原始退出码，使子 Make 的状态只承担其余
  构建/执行周边步骤的错误传播。原始退出码、当前日志、子 Make 状态共同判定，
  不把 Make 的通用错误码当作 guest 返回值。NPC 使用既有 trap 日志和子 Make 状态。
- 正例要求唯一完整 GOOD TRAP；负例要求唯一完整 BAD TRAP；ABORT、SIM_END、
  watchdog 退出、缺失/重复终止信息、工具异常退出均不能通过。支持当前 ANSI 彩色日志。
- 每次调用使用独立 `/tmp/cpu-tests.XXXXXX` 日志目录；不截断或删除旧 `.result`。
  保留每例 `.log`、`.make-status`，NEMU 另有 `.status`，以及 summary。
  入口输出日志路径。`results: N/M` 表示结果记录数/预期数，ERROR 记录不代表有效执行；
  状态与外层退出码仍是成功门槛。
- 非 run 目标直接调用原子 Make，保留交互输出。改用 `$(MAKE)` 正确传递递归选项。

现有观测能力的明确边界：NEMU 的正常 BAD TRAP + 模拟器退出 1 可以证明 guest
以非零值终止；其现有日志不暴露 guest 的具体返回值，因此**不声称验证了 guest
返回值恰为 1**。NPC 已输出返回值，wrong 要求 `ret code=0x1h`（允许前导零）。
这采用现有预期失败语义，未为精确值增加生产日志协议或修改模拟器。
NEMU ABORT 虽同样退出 1，但没有正常 BAD TRAP，且会被 ABORT 检查拒绝。

源码 SHA256：

- before：`f2f159f56bdfd4ccdbf69e8643e8c1ddaaf90136d6c76e1227c37ac445fd3df5`
- after：`26f9eea6f900e06346acbfb0d6dc5e0604f7bba9bf05e13e42beb607764ca057`

## 本轮新验证及日志

[check.py](check.py) 只复制实际 cpu-tests Makefile 到唯一临时目录，提供 fake AM
及后端；执行真实 make/sh/awk，不编译产品或运行 guest。最终 fixture 包含两层递归
Make，验证 NEMU_EXEC 中变量/美元符号穿过真实递归 Make 的行为，并使用彩色终止日志。
每例另放旧 PASS `.result` 与旧产物，验证本轮错误不会从它们获得成功；旧产物字节保留。

修复前：保存原 Makefile 后先运行 `before/`，28 项中仅 6 项符合正确契约，22 项
错误地返回 0。普通 FAIL、负例构建失败、工具无法启动、零样例均错误通过；负例构建
失败时 `started=[]`。测试外层自身退出 1，证明它检测到了原判据缺口。

修复后：`final/results.json` **28/28 符合契约，check.py 退出 0**。以下每种情形在
NEMU/NPC 两个 fake 平台各执行一次；表中退出码是被测外层 make 的状态。

| 情形 | 修复后状态 / make 退出码 |
|---|---|
| 正常正例、正例与有效负例混合 | PASS / PASS+XFAIL，0 |
| wrong 实际预期失败 | XFAIL，0 |
| 普通测试 BAD TRAP | FAIL，2 |
| wrong 意外成功 | XPASS，2 |
| 正例构建失败、负例构建失败 | ERROR，2；无启动记录 |
| 工具不存在、BAD TRAP 后工具退出 7 | ERROR，2 |
| 正常负例运行后必要步骤失败 | ERROR，2；不被负例抵消 |
| 无终止输出、重复终止事件、GOOD 后 ABORT | ERROR，2 |
| 零选中用例 | 明确 `ERROR: no test results`，2 |

共 14 种故障/对照情形，而非 28 个 CPU 功能测试。没有用 fake 替换被测判定器。
原错误管道已在原 Makefile 的完整 fake 入口中触发，修复路径没有新的判定管道。

关键原始证据：

- `before/results.json`、`before/riscv64-nemu-ordinary-fail/{stdout,stderr}.log`
- `before/riscv64-nemu-negative-build/`、`before/riscv64-nemu-zero/`
- `final/results.json`、`final/riscv64-nemu-expected-negative/logs/wrong.status`
- `final/riscv64-npc-ordinary-fail/`、`final/riscv64-nemu-negative-build/`
- `final/riscv64-nemu-tool-after-trap/`、`final/riscv64-nemu-post-run-failure/`
- `final/riscv64-nemu-zero/`；各目录均有 stdout/stderr，非零日志未删除。

`after/` 是首次修复检查，`after-color/` 加入实际颜色处理，`after-recursive/` 核对递归
变量传递；均保留，不替代终版证据。最终 check.py 可在全新输出目录复验原/现版本：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0052/check.py \
  npc/verif/records/process/code_correctness_review/crp-f0052/before.Makefile \
  /tmp/ccr-f0052-before-NEW
python3 npc/verif/records/process/code_correctness_review/crp-f0052/check.py \
  am-kernels/tests/cpu-tests/Makefile /tmp/ccr-f0052-after-NEW
```

输出目录已存在即拒绝。原版外层检查应退出 1；修复版应退出 0。
baseline 中的启动状态、生产源码哈希及关联依赖终检见 protection.json；
嵌套 Makefile diff 空白检查和反向补丁 dry check 均退出 0。

## 回滚与未验证范围

[repair.patch](repair.patch) 仅含本批 Makefile 差异。先核当前 after 哈希和用户后续修改；
匹配后可在 am-kernels 仓库执行 `git apply --reverse --check <repair.patch绝对路径>`，
再由获准操作者反向应用并核对 before 哈希。若已变化则停下核对，不整文件覆盖、
不 reset/clean，不回滚 F0015 或其他嵌套仓库；证据保留。本轮仅做 dry check。

真实 NEMU/NPC 构建和 guest/CPU 全量回归 **NotRun**；其他 ARCH 未验证。
模拟器启动/终止行为由受控工具模拟，不能据此声称真实 CPU、difftest 或 ISA 正确。
没有为所有无关格式/平台建立通用协议。原生产入口中的自动 Git/波形清理钩子未改、
未执行；恢复真实回归前须按既有规则审查隔离环境与副作用。
同一源码目录的多个独立 make 进程仍共享生成的 Makefile.<case>，并发启动隔离不在
本批承诺内；单次 `make -j2` 和显式 ALL 子集已在定向检查使用。

本批结果待确认、修复未提交。F0015 未提交修改保持；不自动处理其他 CCR-F，不推进
业务 Milestone/Phase。ignored JSON/log/补丁/原版快照需本地保管，commit 不等于备份。


<a id="product-regression-contract-20261017"></a>
## 2026-10-17 用户确认：后续功能修复的真实回归要求

> 适用范围以文末[按模块影响范围选择回归的澄清](#regression-impact-scope-20261017)为准：以下是各类受影响模块的回归要求，不是每批必须全部执行的清单。

用户要求后续nemu/AM/nanos/navy/RT等自研代码的功能修复仍以真实程序回归验收，
并澄清nanos为**现有三个前台加后台hello**，不新增第四个可切换前台。

1. **CPU-tests 全集**：使用实际受测平台、同版源码/配置/工具构建执行
   `make ARCH=<受测平台> run`，正例全部PASS，既有wrong为XFAIL，数量与本轮完整清单一致。
   定向 `ALL=...` 可用于调试，不能代替全集验收；不删除失败项或临时缩小分母。
2. **RT真实guest**：在 `rt/bsp/abstract-machine/` 按已确认平台和配置执行
   `make ARCH=... update`，再 `make ARCH=... run`，保留生成/构建/运行日志与产物来源；
   guest正常初始化并到达可交互msh，不把宿主退出0、超时或单独打印字符串当作启动通过。
3. **nanos真实guest**：在 `nanos-lite/` 按已确认平台和配置执行
   `make ARCH=... update`，再 `make ARCH=... run`；FG_PROCESS实际加载pal、nterm、nslider
   及后台hello。验证F1/F2/F3可切换到对应前台、切换后目标继续正常执行，后台hello保持进展。
   注释残留的bird不替代当前实际加载的nterm；本次不改这些程序或配置。
4. **无GUI不是免测**：可以使用受控无头显示/输入和日志观察，但必须运行真实guest及其
   应用，通过真实输入/事件路径观察切换和继续执行。host harness、fake工具、仅编译、
   内部函数单测都不能替代上述产品回归。无法观察的画面/交互部分明确NotRun并保留人工
   验证停点，不能把宿主超时或结束测试进程当成guest成功。
5. 每批功能修复在实施前核定实际受影响平台、配置、资源和安全构建方式，并保存同版
   输入/产物/日志/退出码或持续运行观察证据；原入口的自动Git、清理、update失败传播及
   旧产物风险须先处理或隔离。现存F0051/F0085等问题不因F0052闭合而消失，不能仅凭
   update退出0认可生成物。发现阻塞如实记录，不通过放宽判据制造通过。

F0052仅修CPU-tests判据，不把其GOOD/BAD TRAP终止规则套到长期运行的msh或前台应用。
当前实现与上述流程兼容，可以闭合本项；后续产品功能修复仍须完成真实回归。
本次收尾**没有执行**CPU-tests真实全集、RT或nanos真实guest，已有28项结果仍仅是
判据的隔离host/fake验证，不新增任何产品回归PASS结论。

## 2026-10-17 本批闭合与分仓提交

用户明确：满足上述用途即闭合提交，其他改动按阶段提交；后续澄清仅清根仓库和本轮
修改，历史嵌套差异保留。当前判据满足本批用途，结果已确认、授权提交。

- F0015根仓库提交：`f5825fdf7ca582f2a1882e28c611acbbc935568d`。
- F0052生产修复在am-kernels提交：`c1ba0bb884eaefc75925401759c9fbdfa6f86124`。
- 本README、check.py与记录索引在根仓库以F0052收尾独立提交；其提交号见本地
  REPAIR_AND_REGRESSION收尾回执/.agent（避免在提交自身中嵌入自身hash）。

提交前复核原F0015/F0052证据manifest均零差异；本次README附记属于新增批准及后续
回归要求，不重写原manifest。增量核对与收尾回执保存在closeout-20261017/。
本轮不push、不运行自动Git构建钩子、不处理其他CCR-F、不推进业务M2/M2-P1。


<a id="regression-impact-scope-20261017"></a>
## 2026-10-17 补充澄清：按模块影响范围选择回归

用户明确：“对应模块的功能修复完成后，必须执行涉及对应模块的验证。完全没有修改的
部分可以不验证，例如修改nanos-lite无需验证rt，因为nanos-lite的代码不影响rt的运行。”
据此澄清前述回归要求及其索引/状态摘要：**按实际修改和依赖影响选择回归，不要求每批
同时执行CPU-tests、RT和nanos全部项目。**

- 仅修改nanos-lite且不影响RT：执行nanos相关真实guest回归，无需执行RT回归。
- 仅修改RT且不影响nanos：执行RT相关真实guest回归，无需执行nanos回归。
- 修改NEMU、AM或共享库：沿调用和构建依赖确定影响范围，执行实际受影响程序的回归；
  消费端即使没有直接改代码，只要受到共享修改影响，也不能按“未修改”免测。
- CPU-tests全集、RT update/run到msh、nanos前台切换及后台hello，分别作为涉及相应
  功能时的回归要求；完全未受影响的部分可不验证，不扩大本批功能范围。
- 每批简要记录修改模块、依赖影响、选测项目及未测理由。对选定的受影响功能，
  无GUI不免除真实guest验证，host/fake不能替代；无法完成时明确NotRun与恢复条件。

本附记只澄清后续回归适用范围，不改历史验证结果、不重新打开F0015/F0052，
不启动新修复或业务阶段。

<a id="handoff-closeout-20261017"></a>
## 2026-10-17 收尾复核与续作承接

- **完成 / 确认 / 提交分开核对**：F0052生产修复及本批host/fake验收已完成，用户已有条件确认和提交授权已履行。生产提交为am-kernels `c1ba0bb884eaefc75925401759c9fbdfa6f86124`，根报告/验证脚本提交为`7d99a8daa14ff2b14705bba1cf238118e6a7bd96`；F0015独立提交`f5825fd`，不夹带本轮文档。
- **本轮只读复核**：当前Makefile与check.py哈希仍匹配final/results.json；生产diff仍为单文件41增14删。历史28/28定向结果、原版22个错误成功及closeout-20261017/receipt.json可追溯。本轮未重跑测试；原manifest的641个文件中仅README因后续批准/澄清附记变化，实际测试证据保持，未重写历史manifest。
- **未验证范围不变**：真实CPU-tests全集、NEMU/NPC/RT/nanos guest等仍NotRun。F0052只闭合测试判据的局部验收；后续功能修复按上文实际模块及依赖影响选测，无GUI及host/fake均不替代受影响功能的真实guest验证。
- **工作流承接**：根AGENTS.md新增“继续”规则，WORKFLOW_POLICY同步最小执行/决策边界；CURRENT_STATE明确当前交互为独立CRP，业务M2保持。唯一下一任务、范围、必读资料、门槛和停点统一在[现有TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)，其他导航仅引用，不另建启动Prompt。
- **新增文档门槛**：上一轮回归范围澄清与本轮工作流/收尾附记尚未获结果确认、尚未commit；原提交授权已履行，本次“落档”不增加commit/push授权。tracked增量仅AGENTS.md、本README及records/process/README.md；WORKFLOW_POLICY、修复计划和.agent为ignored本地资产，沿用本地持久化，不force-add，不声称Git已备份。后续启动先核对确认及提交/明确持久化豁免。

本轮未修改生产源码或Makefile、未开始下一修复、未清理历史嵌套差异、未推进业务阶段。

<a id="handoff-approval-20261017"></a>
## 2026-10-17 用户确认及本批文档提交授权

用户明确：“确认本批已报告通过的范围。按既定规则落档并提交本批归属明确的改动，
准备下一入口后停止，不启动下一批，不 push。”据此确认上述收尾复核、按影响范围回归
及最小工作流承接；授权本批AGENTS.md、records/process/README.md及本README独立提交。
前文文档确认/提交Pending是此次授权前的历史截面，实际提交回执记入本地修复计划及.agent。
WORKFLOW_POLICY、修复计划和.agent沿用既有本地持久化，不force-add，不视为已获Git备份。

本次仅核对文档差异、链接及提交范围，不新增CPU/guest或host/fake测试结果。
唯一下一入口保持[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)，
F0051发布策略仍待下一单元分析裁决；本次确认不代替该裁决，不启动该单元，不推进M2。

## 2026-10-18 测试跟踪范围维护（不重开修复）

用户明确要求直接处理既往同类冗余测试提交。保留check.py的28项可重复判据回归源；fake工具/临时结果/日志继续本地保留，未改变测试源或原验收。
分类、原字节/索引核对和范围见[维护报告](../repair-maintenance-20261018/README.md)。本次不重跑产品回归、不改写历史完成/提交快照；本轮维护尚未提交，旧修复的确认/提交保持。

## 2026-10-18 终态归属补充

原修复/确认及c1ba0bb提交保留。后续真实NPC DIFF=1发现REF附加终态导致假ERROR、REF-only又可假PASS；独立[补充单元](../crp-f0052-ref-terminal/README.md)已完成按ARCH计数及42项定向、NPC/NEMU真实全集各36PASS+1XFAIL/两次make exit0。本补充结果确认/新commit Pending，不覆盖原历史截面；唯一后续入口在TASK_QUEUE。
