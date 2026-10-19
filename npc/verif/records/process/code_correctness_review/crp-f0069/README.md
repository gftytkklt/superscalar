# CRP F0069 与过期入口勘误（2026-10-20）

## 整体计划与授权

来源：用户“修正过期入口以及所有相关过期文档，然后继续未修复的任务”。
上轮 Guard 发现 TASK_QUEUE 将已完成的 F0018 再列为下一项；本轮明确授权解除该
状态冲突，定向维护导航后执行一个实际未修复单元。不提交、不安装、不推进 M2/M3。
开始时 HEAD `7e0c97e66977bc8d2326dc153856ef09064c3de7`，root/index 干净。

1. 核对逐项台账、Git、F0018 原报告及当前实现；修正现行入口、README 链和相关
   当前状态，历史快照保留并追加可导航勘误。交付本报告、文档核对结果和唯一入口。
2. 执行 F0069：只修 proc.c 的非 FG 调度选择及无有效目标时 current/frame 一致性；
   单进程选择 pcb[0]，两进程模式轮转 pcb[0]/pcb[1]，FG 保持每百次 99fg/1hello。
   不新增模式/Make 选项、不改变装载内容/打印/时钟；未知新策略须停下裁决。
3. 实际生产函数的原版反例和 sanitizer 定向；四种保留模式的首次/后续调度、
   空目标 fallback、prev 保存、FG 动态切换与滑动百次窗口；隔离构建实际内核，
   真实 NEMU 检查四模式启动与持续进度，FG 复用现有三前台/hello观察入口。
   CPU/RT/NPC 未使用这些 nanos 模式，按闭包解释未测，不以 host 代替真实 guest。
4. 保存命令/退出码、源码/配置/输入身份、必要 patch 和文字观察；完成后删除
   可再生镜像/构建/截图/生产源码副本，更新 records 索引、逐项台账和 .agent。

结束节点：本单元验证及留档后停止，等待用户确认/提交；完成不等于确认或提交。
无安装/系统改动；不重跑已验收 F0018，不重写历史完成快照或原审阅问题分类。

## 状态勘误（维护结论）

F0018 已于 2026-10-18 完成并获确认，提交
`37b3195b0ac0f4504165964d2f1b49aa71f09c82` 在当前 HEAD 历史中；当前 cmd_load
与该修复一致，原 16 场景/124 断言和真实 CLI 21 项为历史验收，**本轮未重跑**。
2026-10-19 相关记录中的“未来 F0018 / Planned / 未Start”是误选，不是重新打开或
撤销修复；未来只沿 [TASK_QUEUE](../../../../../../.agent/TASK_QUEUE.md#crp-next)。
累计 45 已修/74 未修完已包含 F0018，纠正入口不增加已修数。

计划落档时为维护及 F0069 实施中；现已 Completed，确认/commit Pending，结果与清理见下文。

## F0069 实施及本轮验收

**Completed；本轮结果确认/commit Pending。** 生产仅 `nanos-lite/src/proc.c`
11增6删：先计算 `next`，按已有 stage 选择 pcb[0] 或 pcb[0]/pcb[1]；检查目标及
context 有效后才更新 `current`。无有效目标时保留原 PCB 及刚保存的 prev，返回
context 与 current 一致。FG 仍采用原百次计数及当时 fg_pcb，未改初始化、装载、
打印、时钟、Make 或用户操作入口。

| 验证 | 本轮结果与证据 |
|---|---|
| 原版失败见证 | 从 Git 7e0c97e 取 proc.c；四种非FG配置首次调度均被 UBSan 的 NULL PCB 成员访问诊断拒绝，exit1；原FG对照50000调用通过。`local/unit-results.json`、各 `*-before.log` |
| 最终组合定向 | 实际生产 proc.c 直接 include，五配置各50000调用，共250000；初始化装载数、boot首次进入、prev保存、返回context/PCB一致性、空目标回退均通过。FG50000调用中500次hello，动态切前台且每个连续100调用窗口严格99:1。ASan/UBSan开启，LSan按现环境关闭，不声称LSan通过；host头/装载器是小型stub，不代替实际ABI/guest。`unit.py`、`unit-results.json` |
| 实际构建 | 五模式各构建纯生产与只加SCHED输出的诊断内核，共10个成功；现有AM入口 `make -j4 ARCH=riscv64-nemu git_commit= image`，均使用当前生产调度。主工程common.h/默认内核产物未改；NEMU复用前组已验收执行器，SHA与其final-identity及本轮开始时一致。`builds.json`、`entry-identity.json`、`consumer-source-identity.json` |
| 真实非FG与FG进度 | 每模式诊断/纯生产各一次，TEST_KLOAD每次2000万、其余每次1亿指令后输入q，10次均exit0、无BAD/ABORT。诊断记录首8次及每100次选择：NTERM始终pcb0，KLOAD/MULTIPROGRAM/TIME_SHARING首8次0/1轮转，FG首8次0且第100/200次3；这里只是抽样，不冒称所有真实调度窗口均已计数。KLOAD两种arg均持续打印（诊断2520/生产2532条）；MULTIPROGRAM内核hello与PAL运行（4354/4372条）；TIME_SHARING用户hello746/749条；FG用户hello各10条；NTERM的恢复PC随执行变化，未用不存在的hello当判据。`runs.json`及十份run.log |
| 默认三前台/后台 | 真实SDL输入路径，约52.87秒、8观察点：PAL标题/场景，nterm输入qzx显示command not found及新提示符，nslider 0→1→0（返回0的像素SHA相同），回PAL并Enter有画面；后台hello37→160。contact图已目视，PAL返回时保留上一窗口蓝色边框这一观察如实保留，不声称全屏重绘/物理音视频验收。自有组SIGTERM后实际exit0，非guest正常完成声明。`nanos/result.json`、`nanos/visual-qa.json` |
| 身份及收尾核对 | 155项预清理核对通过（含AM源文件哈希，不是155个guest用例）；生产source/配置/源盘/hello/NEMU执行器均无漂移，临时盘与源盘同SHA，十次运行镜像均匹配对应构建。`validation-preclean.json` |

[讲义多道程序](https://ysyx.oscc.cc/docs/ics-pa/4.1.html)及
[分时多任务](https://ysyx.oscc.cc/docs/ics-pa/4.4.html)于2026-10-20读取，作为
current/上下文与双执行流调度背景；模式选择以本项目common.h和init_proc已保留入口为准。

调用影响限于 nanos 调度：真实NEMU已覆盖五模式与默认三前台。CPU-tests、RT、REF
接口、NPC RTL不消费此内核stage选择，未重复回归；未测NPC nanos、所有无VME组合、
物理显示/声音、长时压力、exec全场景，不把短时进度当整体OS正确。F0074已有nterm
镜像地址问题仍未修，本轮未改镜像/地址契约。五CQ/F0040并发/F0043协议及两缺源保留。

## 文档更正范围及恢复方法

现行更正覆盖README→npc/README→verif/README→PROJECT_OVERVIEW入口链、CCR总计划、
原/最终问题和最终报告/证据索引、REPAIR_AND_REGRESSION、CRP workflow/逐项台账、
process索引以及.agent的CURRENT_STATE/TASK_QUEUE/DOCUMENT_INDEX。原F0016、宿主优化、
调度三报告只追加勘误；CHANGELOG_AGENT只追加引用原快照的更正及本次完成记录。
P10的119项未修及各批Pending/未开始明确标为历史；不把它们重写为新验收结果。
F0003并行优化已确认提交c920dbe，现行overview也同步纠正；原测量不变。
完整范围/链接和身份见 `local/documentation-audit.json`、`documentation.patch`。

local一次性夹具/观察脚本不随修复提交；保留 `unit.py`/`prepare.py`/`run.py`、
`nanos-run.local`/`observe_sdl.c`、各配置、精确patch、构建/运行argv/exit和身份。
复现应在新的空local目录从Git 7e0c97e重建源并应用repair.patch；先运行unit.py，
再prepare.py、run.py及`python3 nanos-run.local nanos`。prepare.py依赖当前原Navy
输入与对应ramdisk.h（身份见entry-identity），复制到临时盘；不重建/写回真实盘，
不下载/安装。NEMU源/配置/执行器同原提交及已验收SHA；需重建时用既有
`make -o compile_git -j4 app NEMU_HOME=...`，不触发自动commit。

验证后只清理本组local内可再生副本/镜像/执行器/截图，先留清单与哈希，保留文字
结果和最小源；实际数量见后续清理回执。原manifest里的当时身份合并清理回执解释
预期缺失，不能继续使用旧产物路径。ignored资料/.agent不等于获得Git备份。

累计 **46已修/73未修完**（前45项已确认提交，本项待用户确认/提交），不重复计算
F0018。未来候选F0060原用户栈参数对齐，当前源码仍直接在字符串后压表且未对齐；
其范围/必读/验收/门槛只在TASK_QUEUE#crp-next维护。本轮停止，无commit/push、
安装或下一单元Start，不推进M2/M3。

## 清理及最终状态

验证/目视记录完成、所有本组子进程返回后，定向删除459个本组local可再生产物，
合计170022094逻辑字节（约162.1MiB），含临时Navy盘、隔离AM/nanos源码/构建、
十组bin/ELF、host执行器与截图；无tracked删除，清单逐项复核后剩余产物0。
`local/cleanup-plan.json`及`cleanup-receipt.json`保留路径/类别/哈希和实际删除结果。
未删除主工程构建、原Navy盘或文字证据。documentation.patch只保存Git可跟踪文档
的差异；ignored文档与.agent仍按原本地持久化约定保管，文档身份见audit。


## 用户确认与提交授权（2026-10-20）

用户“同意你提交以后进入下一项”确认本组已报告范围/验证/限制并授权提交，随后执行唯一下一F0060。提交前75条本组manifest及21份文档身份保持，15项最终核对全部通过；复用已完成动态验收及清理，不重跑/重建。仅提交本组可归属代码/文档；本节随实际提交落盘，SHA及文件集合见local/submit-receipt.json与.agent，不push。本组此前Pending为完成时历史截面；ignored文档/.agent仍不由commit备份。
