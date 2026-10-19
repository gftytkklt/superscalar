# NEMU宿主访存热路径优化与复测（2026-10-19）

## 整体计划

来源：用户“基于你的调研结论，在不改变程序行为和接口的条件下，先对宿主端重负载做可能的优化。完成后再进行一轮性能测试，看看有无提升。”

Guard：当前F0016与性能调研Completed、待确认/commit，HEAD d28c393；已报告未提交改动与Session一致。本轮是用户明确授权的独立性能工作单元，不开始F0018或M2/M3、不推定F0016获确认/提交。现有修改保留并纳入before/after共同基线，无需为执行独立任务越过CRP门槛。

目标/范围：消除宿主访存路径内可证明冗余的查找/检查，以更少宿主工作实现相同guest读写、异常与接口。第一候选为checked物理访存复用已找到的MemRegion；第二候选为单页读/取指合并物理预检与实际checked read。保持原region hooks、trace、MMIO方向/次数/长度、Sv39检查及A/D/跨页失败原子性，不改guest调度/音频/时钟轮询/内存布局/Make选项。无需软件安装或新接口/语义裁决。

本轮一个实现/验证单元：
1. 捕获优化前实际源码/配置/输入及未提交基线；隔离构建before，复用原nanos输入与临时磁盘，建立同轮性能基线。
2. 逐项最小修改、定向检查物理内存/边界/MMIO回调/trace与虚拟访问异常；必要时保留旧慢路径。不引入跨指令缓存，避免改变当前无TLB实现的PTE立即可见性、A/D与状态切换行为。
3. 真实Sv39/原子/权限/高地址/跨页guest、CPU消费端及native/REF/ABI按影响覆盖；nanos三前台和后台hello；NPC模型本身未改，REF变化覆盖其消费契约。before/after使用同编译选项、同输入、相同采集点，交错测量固定指令吞吐与实际PAL进度；无速度收益或行为不等价则调整/撤回该候选，不能降级功能换速度。
4. 留存实际命令/退出码/配置和源/输入身份、必要最小测试与补丁、速度统计/限制；清理生成产物并更新records索引和.agent。结果/用户确认/提交分别记录，本轮完成后停止，不commit/push或开始其他工作单元。

验收：定向与真实guest通过，差异检查覆盖返回值、内存/寄存器/异常、MMIO side effects，失败判据不伪PASS；原trace路径保持。性能使用同轮交错before/after多次测试给出中位数及波动，不拿上一轮独立宿主状态作严格对照。真实输入和默认配置/执行器不变；明确真实时钟下“等价”指ISA/设备语义及接口保持，不要求更快执行后guest读到同一墙钟值或中断落在同一指令。结束节点为本单元完整收尾待确认/commit；若实际需要改变行为/接口/系统权限则停止相关候选。

当前：Completed，结果确认/commit Pending；F0016原确认/提交状态独立保留。

<a id="implementation-result"></a>
## 实现与行为保持

本轮生产修改仅`nemu/src/memory/paddr.c`、`nemu/src/memory/vaddr.c`，合计47增10删；原F0016三文件改动保留，未混作本轮优化。

- checked物理读写找到并验证完整MemRegion后，直接使用**原有**`r->read/write(r->mem,offset,len)`，省去`paddr_read/write`中第二次相同region查找。不是绕过访存钩子或整数/边界检查；malloc初始化后的region指针仍实时读取，没有缓存地址或布局。
- MTRACE开启时仍进入原`paddr_read/write`诊断路径。非普通内存路径保留原`mmio_range_mapped→paddr_read/write→mmio_read/write`，包括现有region/MMIO优先级，不改变回调次数/顺序/宽度。
- 单页读/取指先按原`riscv64_mmu_translate_checked`翻译，再由一次`paddr_try_read`同时检查并读取物理范围；原先同页的`paddr_try_access`预检不再重复。跨页路径保持原预检两页后才读/写；store、SC probe、dirty更新及页表遍历算法未改。

无新增/变更public函数签名、CPU_state或DiffTest ABI，无Make选项/用户步骤变化。无跨指令缓存；每次翻译仍读取当前PTE，所以不用改变satp/sfence失效策略，页表不做sfence更新也仍立即可见。MPRV/SUM/MXR/权限/精确异常/A/D仍走原代码；guest调度、音乐、像素尺寸、时钟源/设备轮询频率均未改。实际时钟/中断落点可能因运行速度提升不同，这是原真实时钟输入语义；不承诺更快执行后输出同一墙钟值或逐条相同的定时中断落点。

## 正确性与真实回归

所有构建在本批local隔离目录，以`make -o compile_git`避免自动提交；不重配/覆盖默认NEMU/NPC执行器或真实磁盘。

| 检查 | 本次实际结果 |
|---|---|
| 原生定向物理/虚拟边界与MMIO | before/after各430项通过：4内存域、1/2/4/8字节、非对齐/区间尾部、无效长度/完整范围拒绝、高地址不截断、异常cause/tval与失败输出保持；20次回调/8次写，单页读/取指/写各准确一次、跨页MMIO和region-only MMIO访问不触发回调。`probe-results.json`、`probe-*.log` |
| MTRACE | before/after各430项；384条内存trace**逐条原字符串完全相同**，非空检查有效。`trace-before.log/trace-after.log` |
| malloc PMEM | before/after配置重新构建，各430项通过，覆盖运行时PMEM指针；默认GARRAY配置保持。`malloc-results.json` |
| 无设备REF内存 | before/after各473项，额外覆盖第五SDRAM内存域/边界。测试仅加local export，不改变生产导出。`probe-before-ref.log/probe-after-ref.log` |
| 真实ISA guest | after native/REF的高地址10陷阱自检、原Sv39（叶子大小/A-D/权限/跨页失败原子性/非相邻物理页）、sfence权限、LR/SC/AMO，8次均GOOD/exit0。`guest-results.json` |
| PTE立即可见性 | before/after均运行将原Sv39 guest的sfence替换为nop的局部版本，GOOD/exit0；所有PTE改变后无缓存可见性保持。原sfence权限guest另独立通过。`*-nofence.log`、`sv39-nofence.S` |
| REF ABI | before/after纯REF均通过既有33字选择复制/canary、五内存域、exec/time检查。`*-ref-abi.log` |
| CPU全集 | 新构建的当前NPC+after REF、NEMU after均**36 PASS+1 XFAIL**；原XFAIL保持，检查37项和真实汇总/退出码。`cpu-results.json`及各CPU日志 |
| RT真实消费者 | 隔离BSP按现生成器update/image成功，新NPC+after REF实际difftest ON，**141.41秒到msh**；观察后自有组SIGTERM/-15，非guest正常退出。`rt-builds.json/rt-result.json` |
| nanos三前台/后台 | 使用原guest与临时磁盘，新native运行约51.75秒：PAL有场景/标题画面；nterm键入qzx出现command not found并新提示符；nslider 0→1→0，返回0的像素SHA与首0相同；F1返回PAL有画面；hello1720→7665。目视图与原SHA已记`nanos/visual-qa.json`，8观察点完成后自有组SIGTERM，实际进程exit0，不冒作guest完成退出。`nanos/result.json` |

NPC RTL和guest源没有变化；为保证REF消费回归身份，使用本版RTL新建隔离NPC（构建约15.29秒），未复用主目录较旧执行器。RT使用现源/生成器隔离重建，不依赖已清理的历史RT镜像；本轮未在msh后再次启动四个AM程序。STA/P&R、其他ISA/全配置、物理窗口/声音、完整Linux和长期稳态未测；不把定向通过扩大成这些能力验收。

测试源/runner只留local最小再生材料，不作为新增用户流程；生产API/runner未改。上述边界均有独立期望/实际退出码，不以超时或只有日志存在判断通过。

<a id="performance-result"></a>
## 同轮性能复测

真实负载仍为原nanos-lite PAL前台+hello后台，原Navy ramdisk临时副本，native `-O2`、trace/watchpoint/diff关闭、legacy timer、800×600 VGA、SDL video/audio dummy，与原调研相同。没有关闭渲染/音频或减少设备检查；没有profiling信号或每指令计数探针。before/after仅在原执行区间结束后各打印一次原`g_timer`与指令计数，临界测量路径一致。

两版均绑定允许列表中的宿主CPU0，以before→after→after→before→before→after交错顺序测量。性能测试期间不并发本批编译/消费者测试；其他宿主负载/热状态/CPU频率未固定，不能消除全部环境波动。各次均执行指定指令数后q正常exit0，无ABORT/BAD，磁盘路径从启动日志检查，源盘/副本最终SHA保持。

| 每次2亿guest指令，3次/版 | 优化前 | 优化后 |
|---|---:|---:|
| 吞吐min–max（M guest inst/s） | 17.001–17.319 | 19.364–19.903 |
| **吞吐中位数** | **17.190** | **19.740** |
| 执行区间中位耗时（秒） | 11.635 | 10.132 |

**中位吞吐提升14.84%（1.148×），固定指令执行时间缩短12.92%。** 原始wall/user/sys、指令数/原时间计数、执行器SHA、固定CPU及启动路径见`perf/runs.json`，统计见`perf/summary.json`。总进程wall包含初始化，吞吐分母取原执行区间；不把二者混用。

延长到每版5亿guest指令的单对复测：before **15.980 M/s / 31.290秒执行时间**，after **18.233 M/s / 27.423秒**，吞吐提升**14.10%**、执行时间缩短**12.36%**；总wall分别31.665/27.800秒。不是额外三次中位数，原始条目index6/7。两个长度窗口的绝对吞吐因阶段负载及宿主状态不同，均支持约14–15%的本轮提升。

这是解释吞吐提升，不是完整游戏FPS或音频实时性的承诺；真实时钟下两次运行的guest音频供给/调度落点可能变化，不能只按hello打印数评判速度。真实三前台回归用于观察功能和进度，未作为严格FPS基准。原分析中的后台忙循环和guest FM合成仍在，约15%的宿主提速不会消除所有卡顿。

## 再生、身份与停点

本轮before从**开始时实际worktree**隔离复制，包含尚未提交的F0016；after在该基线上仅修改paddr/vaddr。HEAD d28c393，`entry-working.patch`记录进入时tracked差异，`optimization.patch`记录本轮生产优化；不可只检出d28c393而遗漏F0016后冒称同一baseline。源/配置/执行器身份见`before/after-identity.json`、`final-build-identity.json`；默认资产保护见`entry-identity.json`。

在本记录树**新建空local子目录**复制必要脚本，准备对应baseline生产源后运行`build.py before before-ref`，应用optimization.patch后`build.py after after-ref`；两版使用相同`instrument-measurement.py before after`；`benchmark.py`准备临时盘并完成交错测试。`probe.c/probe.py`、`malloc.py`、`guest.py`、`extra.py`、`sv39-nofence.S`、`prepare-consumers.py/build-soc.py/cpu.py/rt.py`及`nanos-run.local/observe_sdl.c`保留必要配方与独立期望。原输入镜像来自主工程/外部RT现源，按身份/配方获取，不纳入Git备份。

本轮优化不增加CCR已修数量：仍45已修/74未修完；F0016和本轮新结果的用户确认/commit分别Pending。完成留档后停止；不commit/push、不开始F0018/M2/M3。没有新增长期架构Decision，只有本轮保持语义的实现选择。

按既有CRP产物规则清理完成：`local/cleanup-receipt.json`删除4511文件、332649877逻辑字节（约317.2MiB），无tracked删除/日志压缩；定向postscan为0，不跟随symlink、不改主工程/外部资源。29项清理前组合核验通过；清理后终检见`validation-final.json`，保留文字manifest。源/执行器身份中的旧路径需结合本回执解释预期缺失，不能直接复用已删除二进制；截图已先目视并写文字QA，哈希不代表删除后仍可查看。ignored/.agent和外部输入不因普通commit获备份。

<a id="approval-submit-20261019"></a>
## 用户提交授权补充（2026-10-19）

用户要求补充hello调度比例并“测试无误后提交修改”，随后明确为每100次调度99fg/1hello；该纠正只修改新增调度目标，不撤回提交授权。此前本组已报告结果/限制得到提交确认，技术证据与原完成快照复用；不重做Completion、不重建已清理产物。新增调度作为独立单元验收与提交；本组复用原技术结果。本节随对应代码提交，完整实际SHA及暂存/实际集合另存local/submit-receipt.json及.agent；不push/不开始下一单元。

原manifest为交付完成时文字身份；README增加本提交授权补充是预期新增事实，其余原条目按哈希核验保持。当前状态以本补充及实际提交回执为准，旧Pending为完成时历史截面；ignored/local/.agent不等于获得Git备份。
