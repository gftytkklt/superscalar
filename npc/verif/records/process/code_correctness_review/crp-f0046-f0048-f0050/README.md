# CRP — CCR-F0046 / F0048 / F0050：RT BSP 局部修复（2026-10-18）

> **最新状态：本组三项均Completed，用户已确认并授权提交。** DUT依赖已修复、F0046已恢复并通过最终组合回归，见[补充验收](#dut-repair-20261018)。下方原Partial/撤回段落为历史证据。

## 范围、验收与停点

复用[修复计划](../REPAIR_AND_REGRESSION.md)、[现行流程](../workflow/README.md#batching)及[唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。用户本轮授权最小调整批次/对话规则并在原门槛满足后执行下一组；前批已确认提交71c6cf8，初始root/index干净。本次规则维护与修复同轮执行，不另设维护提交前置门槛。

| 编号 | 修改边界 | 验收 |
|---|---|---|
| F0046 | interrupt.c遵守rthw.h返回旧level、按level恢复 | 真实声明编译；原MIE0/1、多层嵌套/交错恢复；host及真实RV64读取MIE |
| F0048 | init.c成功即退出缩减循环，耗尽沿用已有初始化assert | 首次/回退/最小成功的Area等于请求，耗尽不公布NULL区 |
| F0050 | uart.c按present读RX、返回注册错误；init.c检查错误 | 注册成功/失败、预置命令耗尽、present false/true和无输入/字符；真实AM及RT运行 |

执行：复用P5反例/隔离环境→逐项最小修改与定向验证→最终组合与真实RT update/run→逐CCR-F证据及统一收尾。组末停止等确认/commit；不自动提交/push，不推进M2。共享修改仅RT BSP，CPU-tests/nanos不依赖它们，不重跑。
F0047涉及时钟/调度接入，F0049涉及线程资源生命周期，单独处理；没有将其算作本组通过。无安装/新能力开发或未决CQ裁决。

## 逐项结果与阻塞隔离

| 编号 | 原反例 / 本次定向结果 | 当前落地状态 |
|---|---|---|
| F0046 | 原真实rthw声明编译冲突、旧嵌套恢复失败；候选声明编译及host 32组八层恢复通过，NEMU guest直接读MIE的32组通过 | **Blocked，候选已撤回，未修复**。RT/NPC/difftest在ienabled读取mstatus时中止，详见下节 |
| F0048 | 原首次32MiB公布16MiB，回退/最小分配同样减半，耗尽继续；修复首次32MiB、回退8MiB、上限3取2字节、1字节、完全耗尽均通过 | 成功即break保留实际size；耗尽沿用同文件已有初始化断言。无NULL Area发布 |
| F0050 | 原注册失败仍返回0，无UART的预置命令耗尽后仍读RX；修复host注册错误-7精确传播，board在错误后停止且未分配；无设备不读RX，有设备0xff/字符Q/NUL按既有约定返回 | uart.c返回注册结果、按CONFIG.present选择RX；init.c检查注册错误 |

最终独立host组合8/8（F0048五场景、F0050 board注册失败及UART两个进程），真实RT声明参与编译。
F0046的host/NEMU通过仅是候选局部证据，**不属于最终生产状态通过**。原`candidate-combined-host.json`的9/9包含候选，最终`combined-host.json`只保留独立8项。
逐项命令：`python3 local/check.local before|after 46|48|50`；原版运行退出1/声明编译1是预期反例，不把采集脚本退出0当代码PASS。F0048中间验证尚未修F0050的board错误用例失败，保留`after-48-before-F0050`；最终同一init.c重验该例通过。
首次部分编译被ccache只读目录拒绝，已设置CCACHE_DISABLE=1重跑，保留原日志。最终guest拆除F0046时遗留的未用测试helper被-Werror拒绝，删去该测试helper后重跑成功，没有放宽编译选项。

## F0046真实阻塞与撤回

候选RT/NPC在149.07秒触发difftest：PC `0x80020188`（`ienabled: csrr a0,mstatus`），REF `0xa00000088`、DUT `0xa00001888`，相差MPP位`0x1800`；双方MIE相同，但逐指令GPR比较仍失败。反汇编确认`rt_hw_interrupt_disable`直接调用该读CSR路径。
父make返回0，监督器依据进程结束/缺shell/失败日志返回1，本次正确拒绝。没有关闭difftest、跳过CSR比较或改RTL/NEMU。

这证明候选触达现存平台CSR差异；**尚未定位或修复差异根因，也不据此认定属于某个已有CCR-F**。其处理涉及当前用户排除的平台能力/其他Phase边界，相关实施停止。
已将候选`interrupt.c`补丁及同版RT ELF/BIN/反汇编/完整日志保存在`local/f0046-blocked/`；工作树和最终测试副本的interrupt.c均恢复本轮起始字节。F0048/F0050不依赖中断接口修复，移除测试观测中的MIE读取后重跑独立组合；不将原失败标成整组通过。
F0046后续恢复须先明确平台CSR差异处理范围，并重新跑受影响RT/NPC验收；局部候选不能直接记完成。

## 规则调整

[现行流程](../workflow/README.md#batching)取消过窄小批解释，明确自适应分组、逐项验证/组末确认、独立阻塞隔离、复用环境/判据、最终组合检查以及同对话续作。
[原维护记录附记](../agent-policy-maintenance-20261018/README.md#adaptive-groups-20261018)保存检查依据与授权来源；未改其他Milestone/Phase规则，未另立调度框架。4～8仅参考，本组按RT BSP背景选3项，未把复杂F0047/F0049凑入。

## 最终独立组合回归与收尾

| 执行 | 本次有效结果 |
|---|---|
| 最终host组合 | F0048/F0050八个进程全部exit0，均有准确PASS结果；真实RT头/配置参与编译 |
| RV64 NEMU UART guest | 预置命令逐字节检查，耗尽后32次无输入，实际CONFIG.present=0；GOOD TRAP、exit0，0.67秒 |
| RV64 NPC UART guest | 同一UART生产源码、真实CONFIG.present=1及MMIO RX；预置耗尽后32次无输入；GOOD TRAP、exit0、difftest ON，2.87秒 |
| RT四应用update | 既有生成器及make update，exit0，1.47秒；生成器未改，F0051发布契约保持 |
| 最终RT/NPC | 150.07秒到Hello RISC-V!/msh，difftest ON，无分歧；测试观测`heap_bytes=2097152 exact_allocation=1`，实际成功分配与公布长度一致 |
| 判据故障验证 | 工具退出7、exit0空结果、仅prompt、标记伴坏trap四种均拒绝；完整标记受控收停正对照接受。5/5 |
| 证据一致性 | `python3 local/verify.local` exit0，26项通过：最终源码/候选撤回、原反例、最终结果、失败保留、运行器身份、HEAD/index/空白等；不代表F0046完成 |

最终RT由监督器对自有进程组SIGTERM收停，make退出-15；不是guest正常退出。测试观测仅位于隔离副本，使用链接`--wrap=rt_malloc`记录真实分配，再由INIT_APP_EXPORT断言公布范围；没有修改生产Make或日常流程。NPC UART定向单独复制AM构建目录，避免与RT不同启动布局混用；执行器均冻结且SHA与根工作区相同。
完整命令/cwd/env/退出码见`local/{direct-final,npc-direct,rt-update,rt-run}-result.json`。原F0046候选的NEMU局部结果见`direct-result.json`，不能混作最终组合。测试副本`/tmp/crp-rt-bsp-sqe6h8pr`；`prepare.local`保留复制配方，原/新源码、精确patch、源清单、测试脚本/日志/ELF/BIN/反汇编、身份及manifest在local/。

**本组结果：Partial；F0048/F0050 Completed，F0046 Blocked且撤回。** 规则维护完成；本批结果确认Pending、commit Pending。生产最终仅init.c与uart.c（11增4删），interrupt.c与本轮基线相同。累计已修13/剩余106含5CQ；不改原审阅台账或历史完成快照。
root HEAD71c6cf8、index空；Working tree contains uncommitted CRP repair/documentation changes。无commit/push/安装，M2未推进。只拟纳入最小生产修改、现行流程/维护附记、本报告/索引及局部.gitignore；一次性测试代码和原始证据本地保留，不随普通commit备份。

CPU-tests/nanos不依赖本组RT BSP，未重跑；未测长时调度/时钟/抢占、四应用实际运行、人工UART键入、Linux或其他平台能力。F0046原接口缺陷仍在；不声称RT所有临界区正确，也不把历史shell通过代替它的验收。
本组按实际结果统一收尾后停止等用户确认/提交；阻塞项不扩大为独立后续修复的门槛。唯一后续范围/门槛仍见[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)，默认同一对话继续，不要求指定编号。

文档终检：`python3 local/doc-check.local`退出0，6项检查与36个本轮相关链接/锚点通过；唯一Next、Partial状态、F0046撤回、index为空及`git diff --check`一致。


<a id="mret-diagnosis-20261018"></a>
## 2026-10-18 F0046阻塞原因补充：mret后的MPP演化差异

用户追问差异来自REF初值设置还是执行过程；本轮仅定位，不修生产源码/重开业务Phase。以下新证据补充前文“未定位根因”的当时截面，不覆盖原失败和组末Partial状态。

- 初始化：`nemu/src/cpu/cpu-exec.c:35`静态设置mstatus=0xa00001800、priv=3；DUT `npc/vsrc/ysyx_22040750.v:1512`复位mstatus同值。NPC difftest初始化确实仅拷贝GPR/PC（difftest.cpp、ref.c），没有CSR同步，但这次不是初值不同。
- 执行：RV64 REF的`riscv_mret`（inst.c:252）按MPP确定返回权限后清MPP，同时更新MIE/MPIE；DUT RTL:1541仅改MIE/MPIE，保留mstatus[63:8]，其中包括MPP。因此共同写入0xa00001880后，执行mret将得到REF 0xa00000088与DUT 0xa00001888。
- 本次实测：复用原NPC/REF二进制（SHA与上轮一致），运行56字节、14条指令的独立镜像。初始`csrr mstatus`通过；显式写0xa00001880后的`csrr`通过；`mret`之后第一条读CSR在PC3000002c精确复现t2差异0xa00000088/0xa00001888及DIFF ABORT。先显式统一状态仍分叉，排除“只需补一次REF寄存器初始化”的解释。
- 这次短程序不经过RT或F0046候选，说明候选暴露了既有执行语义差异；原RT日志的ienabled只是将CSR差异带入GPR后被对拍发现的位置，不是差异产生的位置。尚未采集原完整RT运行的首个CSR分歧时刻，不把短程序冒充原RT逐周期追踪。
- 证据：local/mret-diagnosis含probe.S/ELF/BIN、反汇编、命令/日志、6项核对通过及独立manifest。make仍exit0，按预期DIFF ABORT判断成功复现，绝非产品PASS。首版夹具因la生成GOT而未触达目标，保留local/mret-initial-got，仅最终`.option nopic`版本有效。

本轮只追加分析记录及恢复状态；F0046继续Blocked/withdrawn，F0048/F0050完成待确认/commit不变。后续应明确DUT/REF的mret/特权模型一致性处理范围，不能用重设REF初值或屏蔽MPP比较充当本项修复；本轮未实施相关改动。


<a id="dut-repair-20261018"></a>
## 2026-10-18 用户授权DUT依赖修复与F0046恢复（Completed）

用户最新“执行此项修改。如果此DUT修改属于另一项NPC查找到的bug，请同步更新对应编号的修改情况”授权本次DUT局部修改及F0046恢复；这是同组补充实施，覆盖先前本项“不改RTL”的边界，不推进M2/M3，不要求前批先提交。既有F0048/F0050及规则文档未提交修改保留；无commit/push/安装授权。

沿用本组计划的一次补充单元：DUT mret清MPP、按旧MPP处理MPRV并保持MIE/MPIE更新；当前仅M态执行路径trap保存MPP=M，恢复F0046保存/恢复接口。范围仅CSR状态更新、F0046及必要回归/记录，不实现S/U运行权限、SRET、委托、MMU或完整Linux能力。
验收：CSR模块旧/新反例与有效提交/位保持、MRET短程序及重复trap/return真实SoC difftest；F0046 host/双平台MIE、RT新模型实际运行到msh；既有NPC微测试及CPU回归按受影响路径选择。runner/模型变化核验源码/构建/执行链与失败判据，最终三项组合验证。结束节点为补充组末报告后停止等确认/commit。
编号核对：FINAL_FINDINGS/原CCR计划S04不包含NPC RTL；npc/README §3.2 bug2_csr为CSR前递，residual_mret为MEPC前递，RTL_STD_MODELS S6为仲裁/提交断言，均非本次MPP语义差异。未发现可合并的独立既有问题编号；以F0046的DUT依赖修复记录，不虚构新的CCR-F，不将OPT-17/M3整体标完成。


补充实施结果：`ysyx_22040750_csr`在有效WB提交时，MRET清MPP、MIE←MPIE、MPIE←1，旧MPP非M时清MPRV；当前只执行M态的trap保存MPP=M、MPIE←MIE、MIE←0。后者保证先前MRET清MPP后，下一次trap仍正确保存M。其余CSR位和原提交门控保持。`interrupt.c`恢复候选：引用真实rthw.h声明，disable返回旧MIE，enable按level恢复；未改REF初值/实现或屏蔽比较。

| 本次重新执行 | 有效结果 / 证据（local/dut-repair） |
|---|---|
| CSR模块原/新源码 | 原版trap精确失败；新版24种MPP/MIE/MPIE/MPRV组合、无效WB不写与其他位保持通过；module-results.json |
| 原MRET反例 / 连续trap | 原14指令反例在新SoC通过；新增mret_status含8次交替MIE的ecall/return，SoC difftest通过；soc-check-results.json |
| 既有裸核入口 | 全部14例逐例exit0且RESULT: PASS，含原CSR/MEPC前递用例；micro-results.json |
| CPU全集 / 新SoC difftest | 36 PASS + wrong预期XFAIL；所有37例实际执行、检查NPC终态和DIFF失败，cpu-results.json |
| 最终host三项组合 | F0046真实声明编译、32组八层嵌套；F0048/F0050八进程均通过，共9个有效运行结果；after-46/48/50 |
| 双平台真实guest | NEMU及新NPC各通过32组八层MIE恢复，UART预置耗尽/无输入通过，present分别0/1；均GOOD TRAP exit0，NPC difftest ON |
| RT update / 新NPC组合 | update exit0；160.57秒到msh且difftest ON，`CRP_BSP_ACCEPT heap_bytes=2097152 exact_allocation=1 nested_MIE=1`；rt-run-result.json |
| 判据 / 身份保护 | 新模型坏trap与超时均拒绝；CPU判据5个负例拒绝/1正例接受；原RT监督器字节不变，复用先前5项故障验证。verify.local exit0，29项核对通过 |

新隔离副本`/tmp/crp-mret-repair-0kksxu4a`从源码构建SoC（DIFF=1/WAVE=0/WITH_TRACE=0/WITH_SDL=0/PERF=1/PERF_R45=1）；根目录旧模型保持，REF二进制SHA与前轮完全相同。源码、命令、退出码、测试/日志、模型和RT镜像在local/dut-repair，tested-identity.json与manifest.json绑定最终源码/执行器。既有一次性夹具复用；只新增有长期回归价值的`npc/verif/tests/mret_status.S`至现有入口，不增加生产Make目标或日常步骤。

CPU首次显式`all`被AM子make拒绝（exit2，未执行用例），保留cpu-initial-all日志，改用现有默认目标后构建成功。此次直接逐一运行37个既有镜像：DIFF=1终态同时含NPC和REF GOOD TRAP，按NPC专有行判定，未声称默认CPU聚合runner已通过或修复。裸核构建仅在隔离副本限制Verilator为2个job。RT使用原监督器，在观察到msh及断言标记后对自有进程组SIGTERM，make=-15、监督器exit0；不是guest正常退出。

**F0046/F0048/F0050全部Completed，结果确认Pending、commit Pending。** 原Partial快照/撤回候选/失败镜像及其manifest原位保留，由本补充结论解除F0046阻塞。累计已修14/剩余105含5CQ。HEAD仍71c6cf8，index空，未commit/push；工作树含本组未提交修复/规则/文档。编号归属同步于FINAL_FINDINGS的F0046进展及npc/README §3.5；没有另一个既有NPC编号可标完成。

边界：MPP=0/1及MPRV清位仅CSR模块字段测试，不证明低特权执行、地址转换或权限检查。Linux、完整M/S/U、M3/OPT-17、长时调度/时钟、RT四应用实际运行、人工UART、完整断言/形式化本次NotRun。NEMU/nanos共享实现未改变，NPC nanos的VME/特权能力不在本次范围，未运行nanos。默认同对话；本组停等确认/commit，未来只沿TASK_QUEUE唯一入口，不启动F0049。


<a id="submit-20261018"></a>
## 2026-10-18 确认与提交收尾

用户“提交现有改动后继续CRP修复任务”确认本组已报告范围（含DUT依赖及规则维护），授权提交后执行唯一下一入口F0049。复用既有完成/补充验收，不重复归档或重跑产品测试。提交前复核三份manifest共346条及7个源码/REF身份均无漂移，git diff --check通过；回执见local/submit-20261018及.agent。

提交仅含四份生产源码、现有入口的mret_status.S、报告/局部忽略和受影响导航/规则文档；一次性夹具、生成C/h/mk、日志/JSON/镜像仍本地保存。实际提交hash记本地回执，避免为回填自身hash重复提交；未push，未测能力仍沿原限制。
