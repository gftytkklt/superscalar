# CRP F0024 — trap现场确定性保存地址空间

2026-10-18。用户“提交，然后继续CRP修复”确认F0023并授权实际提交c9be898后执行本单元。既有整体计划/CRP流程及TASK_QUEUE唯一入口承接，M2保持。

## 本单元计划

目标：新trap frame的pdir槽不能作为线程身份依据；每次CTE入口确定性保存当时有效的地址空间，VME关闭时确定为NULL。仅修改NEMU VME现场捕获；保留Context/CTE/Make接口、kcontext新建NULL标记与__am_switch()对c->pdir==NULL不切页表的既有行为，不扩展权限、撤映射、页表回收等五CQ。

阶段：原版真实零槽/非零槽对照 → 最小修复 → 同版双地址空间U syscall内M yield切走恢复、satp/私有VA/活栈检查、新kcontext首次借用及后续捕获、VME关闭 → 共享RT/nanos回归 → 证据与状态收尾后停止。交付生产最小修改、本报告/局部ignore、local原始测试证据与索引/状态；无安装，出现真实地址空间契约取舍先停。新修复不自动commit/push。

参考：2026-10-18读取[PA4.3](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)“在分页机制上运行用户进程/支持虚存管理的多道程序”和[PA4.1](https://ysyx.oscc.cc/docs/ics-pa/4.1.html)。讲义要求CTE入口保存当前地址空间、返回时落实所选现场页表；kcontext初始NULL可借用当前页表。捕获后保存执行时借用的实际页表，与未初始化槽推断无关；本次不新增永久私有地址空间或修改初始借用接口。

## 结果

**Completed；用户结果确认/修复commit Pending。** 生产仅修改`abstract-machine/am/src/riscv/nemu/vme.c`的`__am_get_cur_as()`：删除`if (c->pdir == NULL) return;`并更正三行注释，每次写入当前根页表，VME未启用时写NULL。trap.S不保存x0槽，该槽被Context的pdir复用，新frame的旧内容不具备线程类型含义。

`kcontext()`初建pdir仍为NULL，`__am_switch()`遇到`c->pdir==NULL`仍不改当前页表。内核线程一旦实际执行并发生trap，现场保存它当时借用的根页表；此后恢复该现场会恢复这个根。没有新增线程私有映射、权限/页表回收或新的Make步骤。CTE/Context布局、入口汇编和F0023生产代码不变。

生产SHA256：`d2f23a7bf1de29f8a4170c799b9091ec37e0131fd708de43d7b15b0b806067a2`，与隔离AM/after副本相同。

| 验收 | 本轮结果与原始入口 |
|---|---|
| 原版零槽真实反例 | `before/run-0.log`：A syscall内的M态yield明确将新frame槽0预填0；保存pdir=0，A根为0x80054000，切B后返回A内核现场仍为B根0x8005a000。根页表断言失败/exit1/BAD TRAP，实际验证了切走再返回，不只是host mock |
| 原版非零控制 | 同一guest仅将槽预填0xdeadbeef，两种嵌套恢复及私有VA内容均通过/exit0/GOOD TRAP；VME未启用对照同样通过，形成一个精确失败与两个正常控制 |
| 修复后三模式 | `final/`零槽、非零槽、VME关闭三guest全部exit0/GOOD TRAP。每个VME模式5次真实U syscall、2次跨B恢复A根（用户syscall内核yield，以及新内核线程yield），M/U来源、scratch=0、活栈哨兵、用户sp变化及私有数据保持全部通过 |
| 真实MMU数据区分 | A/B将相同VA0x40000000映射到不同物理页，值分别0xaaa1/0xbbb2；用户代码在0x40001000，用户栈在0x40002000。所有用户指令/数据/栈经真实Sv39，返回后重新读取相同VA核对各自值；未依赖高位内核恒等映射执行用户测试代码 |
| kcontext既有首次借用 | 新kcontext.pdir=NULL，先在A根下恢复，实际内核线程入口确认仍为A根；其零/非零新trap切到B用户后再恢复时重新得到A根。没有把新建NULL对象当作待捕获的新frame |
| RT共享CTE/VME路径 | 当前源四应用`make -j1 ARCH=riscv64-nemu git_commit= update`及image成功；复用F0023的隔离补充链接配置，真实NEMU到msh、预置命令及am_hello/后续msh通过。观察后实际向自有组发SIGTERM，NEMU exit0；非guest正常退出/GOOD TRAP，不声称difftest ON |
| nanos真实VME消费者 | 既有make run，约51.72秒完成F2终端输入、F3翻页/返回页hash一致、F1回PAL/Enter前后帧变化等8点；hello1483→6787，8点严格递增；最终自有组SIGTERM/make=-15，非guest正常退出。截图可复核，不宣称PAL已流畅或进入某个游戏阶段 |
| 判据/组合终检 | 5个判据负例（错误exit、缺PASS、缺GOOD TRAP、BAD TRAP、assertion）拒绝；`validation.json`21/21；F0023原3,958条manifest全同，未覆盖上一组证据 |

本次runner复用F0023的定向/RT/nanos执行方式；只新增双页表测试源，并给本组RT runner补充终止信号记录及完整日志失败检查。所有构建和观察库复制均在guest启动前完成；运行中不改写这些资产。本轮没有新增失败尝试，唯一预期失败是原版零槽反例。

## 命令、复现与边界

- `python3 local/directed.py before`使用原版vme.c，`... final`使用修复版；实际make/解释器argv、三个mainargs和构建/运行exit在各目录results.json与日志。两个源码版本间采用更新mtime的copyfile，日志可确认重新编译vme.c。
- `python3 local/consumers.py`准备本组独立build并顺序update/image；`python3 local/rt-run.py`与`python3 local/nanos-run.local nanos-final`运行实际消费者，`python3 local/verify.py`做21项核对。上述脚本有证据目录不覆盖约束，重跑须使用新目录；不能把复现命令原样再次运行理解为允许覆盖旧证据。
- RT测试配置沿用F0023的`rt-extra-test.ld`，补入NPC现有应用段及8字节表对齐，环境`LDFLAGS="-T <local>/rt-extra-test.ld"`；默认无该片段的RT/NEMU链接问题保持，不宣称原始命令通过。生产Make/链接脚本不修改。
- Navy/生成器未改，nanos复用现有完整ramdisk/header并记录SHA，未重新update Navy；CPU-tests不调用CTE，NPC有独立VME/CTE，未机械重跑CPU/NPC或Linux。默认NEMU解释器、REF、配置保持，无安装。
- 只覆盖RV64 NEMU现有Sv39/ASID=0和M/U CTE；不扩展ASID、TLB、权限、撤映射、页表回收、S态CTE、RV32/RVE。真实音频、长时调度、全部AM应用未测。PAL性能/F0043/五CQ/F0040Partial/两缺源保持。

一次性guest/runner/源码快照/ELF/bin/日志/截图/patch/身份/manifest只在`local/`保留，不提交测试代码或生成资产。复用方式为新build树：RT公共源目录符号链接指向当前工作区，只复制小BSP及四个AM应用必需源码；未克隆/构建新大型依赖、未写入原RT目录或F0023存档。外部引用不是本地字节备份；冷恢复须携带原RT、Navy镜像、解释器和对应源码/配置。普通commit不代表ignored证据/.agent已备份。

累计31项修复Completed（30已确认提交、本组待确认提交）/88未修完含5CQ/F0040Partial。本组报告/台账/索引/.agent已承接，历史F0024原P4证据不回写。停止等待本组确认/commit；未来只沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动Start/commit/push或推进M2。

<a id="approval-submit-20261018"></a>
## 用户确认及提交授权（2026-10-18）

用户“提交”确认已报告F0024范围与限制并授权提交；545项文件清单无漂移、原21项验收/生产patch保持，复用既有动态验收，不重复测试/Completion。仅六份归属文件入库；实际提交回执见local/submit-receipt及.agent，未push，不启动下一组。

文件计数澄清：F0023所述“3,958项证据”实际为隔离目录的3,958条逐文件SHA清单，包含AM-kernels源树输入1,944份、RT源树输入1,434份，其余580份为AM/nanos输入、构建产物、日志/截图、脚本、快照/元数据等；不是3,958个测试用例或独立结论，F0023最终检查为18项。早期复制了较完整的源码树，清单粒度偏粗。F0024只复制小BSP/四应用必需源，公共RT源引用原树，本组545份归档文件/21项检查分别统计；外部引用不等同本地字节备份。此次只解释计数，不删除或重写历史存档。
