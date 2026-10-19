# CRP F0009 — 磁盘 DMA 边界与失败契约

> 当前：方案 A 修复、最终源码验证及 CCR 产物清理已完成；用户已确认结果并授权提交，实际提交见[确认/提交补充](#approval-submit-20261019)。用户手工确认 PAL 绘图正常，此前不完整观察是运行过慢所致；原短时观察保留历史事实。

2026-10-19 Start。用户“继续CRP修复”授权沿 TASK_QUEUE#crp-next 执行本单元；F0003 已确认提交 c920dbe，技巧文档已提交 f960df0，开始时 working tree/index 干净。五 CQ/F0040 等既有延期不阻塞独立 F0009；M2/M3 不推进，不 commit/push。

## 复用计划与本轮步骤

目标、范围及验收沿既有 [CRP workflow](../workflow/README.md)、[原问题](../FINAL_FINDINGS.md#ccr-f0009) 与 [TASK_QUEUE 唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不重新立项。

1. 核对原 P3/D21、生产 disk→guest_to_host 和 MMIO→AM→nanos 调用链，用临时磁盘复现高地址别名、整段越界、盘块越界及 seek/短 I/O，保存独立期望、实际退出码/源码身份；不操作真实 ramdisk。
2. 契约明确则在 64 位域检查完整地址/长度、块和文件边界，映射后才传输并检查实际 I/O。若错误呈现/ready 不能由现接口确定，形成具体方案后停下裁决，不擅自新建寄存器、AM 字段或改变用户流程。
3. 获准修复后覆盖各注册内存域（native 四域，DEVICE 关闭时另有 SDRAM）、首尾/跨端/高位/零与极大块数、正常读写/文件边界/seek/短 I/O，独立内存/磁盘哨兵与真实 MMIO guest；native/REF 重建及消费者回归按调用闭包选择。仅分析时不冒称修复后验收通过。

交付本报告/局部 ignore、本地复现及必要记录索引/修复镜像/状态；逐项结果与限制分别记录。结束节点为真实契约裁决或本单元完成，统一留档后停止；安装/系统改动立即停。测试夹具/镜像/日志仅 local 保留，无新增日常步骤。

<a id="boundary-review-20261019"></a>
## 本轮结果：原问题已复现，失败契约待裁决

**F0009 仍未修复；生产代码未改。** 当前 `AM_DISK_STATUS` 只有 `bool ready`，NEMU 每次读 ready 都返回 1；`AM_DISK_BLKIO` 是 void 写接口。nanos 的 `disk_read/write` 不读状态，提交后直接复制缓冲区并返回完整长度；am-tests storage 同样提交后直接展示数据。因此“拒绝后返回”会被消费者当成功，“失败时 ready=0”也不能让这些消费者察觉，还会让其他轮询者永远等待。native AM 的 `assert(ret==1)` 是建议 fail-fast 的现有先例，但不是 NEMU 已批准的失败契约。P3 原报告也明确把 disk 错误状态留给接口持有人裁决，D21 只规定 CPU 访存异常，不能将 DMA 错误套成 CPU access fault。

本地复现命令：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0009/local/run.py
```

夹具原样复制本次生产 `disk.c/paddr.c/map.c/mmio.c`，走 `mmio_write → map_write → disk_io_handler → guest_to_host → libc I/O`。使用当前 RV64/paddr32/DEVICE 配置，但把各内存区缩至 4 KiB 以检查边界；诊断/CPU 状态为链接桩，未执行 guest CPU。每个用例独立进程，只打开其 local 子目录的临时 `build/ramdisk.img`；正常/越界盘写均未触及真实 ramdisk。

| 场景 | 原生产路径的实际观察 |
|---|---|
| 正常读 / 写（2 项） | 临时盘 512 字节读入正确；写入首块正确、后块不变，ready=1 |
| 高 32 位读地址 | `0x180000000` 被截为 `0x80000000`，实际覆盖低 PMEM 首块，进程 exit0/ready=1 |
| 跨 PMEM 末尾读 / 写（2 项） | 从末尾前 256 字节传 512 字节；ASan 分别报告无效 WRITE / READ，栈含原 disk/map/mmio；两进程均 SIGABRT/-6 |
| 盘块末端外读 | 2 块盘请求 blkno=2/count=1；缓冲区保留 0xa5，仍 exit0/ready=1 |
| 盘块末端外写 | 2 块盘同请求将文件从 1024 扩为 1536 字节，公布容量仍 2 块，exit0/ready=1 |
| 文件尾不足整块 | 768 字节盘公布 2 块；读末块仅前 256 字节更新，后 256 字节保留 0xa5，exit0/ready=1 |
| seek 失败 | 注入 cookie stream 的 seek 返回 -1/ESPIPE，仍调用 read 填满缓冲区，exit0/ready=1 |
| 短写 / flush 失败（2 项） | 注入 libc stream 回调，分别短返回或返回 -1/EIO；均 ferror=1，但命令仍 exit0/ready=1 |
| 零块数 | 缓冲区/临时盘不变，exit0/ready=1；此为原行为观察，不据此擅自冻结新契约 |

共 **12 个原行为观察**，不是 12 项产品 PASS。前两次夹具运行对“必须出现 ASan global-buffer-overflow”的判据过窄：首次被宿主 FORTIFY 提前中止，局部关闭 FORTIFY 后 ASan 实际报告 SEGV/WRITE；最终判据检查实际非零退出、sanitizer、访问方向及原 disk 调用栈，保留前两次日志 `attempt1-fortify/attempt2-asan-segv/`，不将它们解释成不同生产缺陷。最终交叉读/写均由 ASan 拦截；正常与非越界逻辑失败都退出 0，更能说明不能只查进程退出码。

原始命令/退出码/观测见 `local/results.json`，每例日志和磁盘分目录保存；`local/source/identity.json` 绑定生产源、配置及消费者，最终 `local/validation.json/manifest.json` 另存。当前真实 ramdisk 大小 148376064 字节、按 512 对齐，只作文件属性核对；本轮没有用其运行 guest，也没有写入它。

## 建议 A：保留接口，明确采用失败即终止

此方案需要用户批准其**失败语义与尾块策略**；批准后在同一 F0009 单元直接实施，不要求先 commit 分析文档。

1. 所有请求参数/主机可表达性先用 `uint64_t` 检查，再窄化和映射。检查 paddr 高位、单一注册内存区的完整 DMA 范围、块号/块数与公布容量、`SIZE_MAX`/文件偏移表示范围；复用 `addr_to_soc_range`。native 四域可用，DEVICE 关闭构建额外覆盖 SDRAM；不把 MMIO 当 DMA RAM，不改 paddr/REF ABI 或内存介质权限策略。32 位块数乘 512 在 uint64 内不会溢出，但 size_t/long 可表达性仍要显式核验。
2. 非零无效请求在任何映射/传输前输出具体参数并 `panic` 终止 NEMU；seek、意外短 I/O、写回 flush 失败同样诊断并终止。既有 ready 继续表示同步处理已完成，成功/零块命令返回后为 1；失败不返回 guest，不新增“永久 busy”或伪成功路径。磁盘 absent 的 present=false/无传输行为保留。零块请求明确为无传输 no-op，不映射缓冲区。
3. 保留现有 `ceil(image_bytes/512)` 公布容量，避免截掉末尾文件数据。**最后不完整块的读按已知镜像长度读取并补零；在公布容量内写该块允许文件扩到该块末端，禁止越过公布容量扩盘。** 初始化检查文件大小/seek/容量表达性并保存实际字节数；正常写成功后更新已知长度。仅已知的尾部不足补零，意外短读（如镜像被截短）仍终止，不把所有短读都伪装成正常尾块。
4. 输入校验拒绝须验证 guest/磁盘哨兵未改。真正 I/O 失败可能已经发生部分读写，**不承诺回滚/事务原子性或断电持久性**；以终止阻止 guest 使用失败结果。保留现有路径环境变量和 Make/AM/用户流程，不新增安装或日常必经步骤。
5. 修改预计仅 NEMU disk.c；实际范围随代码核对。按上方既有验收完成边界/注入故障与真实 MMIO guest、native/REF 构建；NEMU 磁盘消费者（am-tests storage、nanos 三前台/后台 hello，临时镜像）须覆盖。CPU/RT 和 NPC 是否重跑按最终依赖闭包说明；不预写其已通过。

## 选项 B：增加可恢复的来宾错误协议

若需要 guest 收到错误后继续执行，应明确新增独立错误状态（ready 仍只表示完成），并让 AM 与 nanos 的读写/loader/FS 调用链传播和消费失败，另行冻结短 I/O/部分完成契约及相应验收。只加设备错误寄存器而消费者不检查无法闭合。该方案扩大现 MMIO/AM/消费者接口与范围，本轮未擅自实施；不建议把 ready 改成错误码或默默复用为成功标志。

## 停点、限制与恢复

停点来自 [TASK_QUEUE#crp-next](../../../../../../.agent/TASK_QUEUE.md#crp-next) 原 F0009 条款“失败状态/ready语义若不能沿现契约确定，停下提具体取舍”，以及 [WORKFLOW_POLICY §3](../../../../docs/WORKFLOW_POLICY.md#3-人工确认--软件安装-停点触发即停) 的改变失败语义须裁决要求；不是额外新增审批。当前等待选 A，或明确要求设计 B。阻塞仅限依赖此契约的 F0009 实施，不扩大为五 CQ 或其他主线前置。

本轮只完成必要分析/原行为复现；五域完整矩阵、极大块数、真实 guest、修复后的 native/REF/CPU/RT/nanos 均 NotRun，因生产修复未开始。现有模型/历史 F0003 测试未冒充本轮证据，无安装/系统改动/运行中动作。累计保持 **43 项已修且已确认提交 / 76 项未修完**，F0009 不标 Completed，不新增技术 Decision 或修复完成快照。root HEAD f960df0；分析文档/索引尚未提交，index 空。一次性脚本与磁盘仅 local，`.agent`/部分文档被忽略，普通 commit 不等于备份。

参考：2026-10-19 读取 [ICS-PA 输入输出](https://ysyx.oscc.cc/docs/ics-pa/2.5.html) 的 MMIO/设备寄存器与 IOE 分层背景；该章没有替本项目规定磁盘 DMA 失败协议，裁决依据仍为本地接口与调用链。原 [P3 审阅](../P3.md) 与历史 FINAL_FINDINGS 保留不改写。

收尾核验：`python3 .../crp-f0009/local/check.py` 的 16 项分析一致性检查通过，55 文件 SHA manifest 已保存；检查源码/配置/消费者身份、原样四源快照、实际退出码、临时盘路径、无生产 diff/空 index、报告链接与状态/镜像一致性。`git diff --check` 通过。以上只证明分析交付一致，不代表修复验收。初次收尾脚本漏列本批合法的 repair-status 文档 diff，已修正预期清单再通过；不涉及生产变更或重复动态测试。

<a id="approval-A-implementation-20261019"></a>
## 方案 A 批准与追加清理要求

用户明确“同意先按方案A修改”，失败/尾块契约已获批准；当前单元直接实施、验证及留档，不另设准备阶段。用户同时要求完成验证后直接删除 `code_correctness_review` 中的大镜像、截图等编译文件，旧实现通过 Git 对应版本重新编译复现；将此动作固化到 CRP 工作流，在修改/提交收尾时执行。

执行顺序：先完成 disk.c 的 A 修复及定向/真实消费者验收，再盘点清理整个 CCR 记录树中已完成验证的镜像、截图、可执行文件、对象/预编译头、波形和隔离构建目录等可再生产物；保留报告、命令、实际结果、配置/身份摘要、补丁和必要最小测试源。较大的原始矩阵等权威文字证据不当作编译垃圾删除；重复综合日志可压缩保留。记录清理前路径/字节/哈希及删除结果，历史 manifest 保留原事实并追加清理指向，不能再宣称所有旧产物仍在。本次删除权限已明确，不再逐文件索取批准；范围仅此记录树，不动主工程真实镜像或系统资产，不借此修改跟踪规则或改写 Git 历史。修改完成后按既有停点总结，未单独获得 commit/push 授权。

<a id="implementation-result-20261019"></a>
## 方案 A 最终交付

**F0009 Completed，结果确认/commit Pending；累计 44 项已修 / 75 项未修完。** 用户同意 A 是本轮实施授权；不将其写成对最终结果的人工复核。用户中途补充“继续，这是一个教学任务，不是真实改动”，随后明确其为给安全检测的说明、要求继续原始任务；本次按原范围完成实际教学项目修改与已授权清理，未因此撤回已完成修改或获得提交授权。

生产只有 `nemu/src/device/disk.c`（42 增 / 14 删）：

- 在 64 位域计算块号/块数/字节与文件偏移，校验 paddr 可表达性、SIZE_MAX/LONG_MAX 及完整盘块范围，再用 `addr_to_soc_range` 验证并映射同一注册内存区的整段 DMA。高位别名、跨区、MMIO 和盘外请求在传输前拒绝，正常可用介质策略沿用现内存表。
- seek、短读/短写与 flush 失败诊断后终止，guest 不会继续使用未报告错误的结果；成功/零块 ready=1，零块及磁盘 absent 不传输，不改 MMIO 寄存器、AM/REF ABI、Make 或日常流程。
- 保存已知实际文件长度，保留向上取整容量；只对已知尾块缺口补零，意外 EOF 仍报错；容量内尾块写可扩至其块尾、成功 flush 后更新已知长度。初始化检查 seek/ftell/rewind；容量必须能由 `AM_DISK_CONFIG.blkcnt` 的 `int` 表达，故限制 INT_MAX，不再窄化出负数。真正 I/O 失败不承诺部分写回滚、并发修改一致性或断电持久性。

| 最终源码验证 | 结果与证据 |
|---|---|
| 定向边界 | GCC-O2 与 ASan+UBSan，两种构建分别覆盖 native 四域、无 DEVICE 五域、malloc PMEM、paddr64 共 **464/464**。首/尾/非对齐缓冲区读写、跨端/域外/高位/UINT64_MAX、零/极大块数、盘末端及整段越界、尾块补零/扩尾后重读、意外短读、seek/短写/flush 注入错误；非法参数检查内存与临时盘哨兵保持。这里的错误终止由诊断链接桩捕获以检查哨兵，真实进程终止另由下行证明。`directed-results.json` |
| 初始化 | **6/6**：seek-end/ftell/rewind 失败、超过 INT_MAX 块的稀疏盘、磁盘 absent、空盘；极大稀疏盘用完即删。`init-results.json` |
| 旧实现反例与判据 | 从 **Git f960df0** 读取原 disk.c 重编译，高地址拒绝期望失败（exit2）；修复实现通过同判据，不复用遗留旧二进制。`oracle-negative.json` |
| native/REF | 最终 disk 源码同步到隔离构建，native/REF 构建均 exit0，native 内置真实 guest GOOD，REF 33字 ABI PASS。REF 无 DEVICE，不编译 disk；重建/ABI 用于确认配置与接口保持。`final-builds.json`、两个 final 日志 |
| 真实 MMIO/AM guest | 正常读写/尾块补零、扩尾重读与零块命令自检 **GOOD/exit0**；高位、PMEM 跨端、盘外三例均打印预执行标记后诊断终止 **SIGABRT/-6**，返回后标记未出现、临时盘不变。`guest-results.json` |
| 原 am-tests storage | 原 devscan/main/AM 源不改，实际输出 512 字节与临时 Navy 盘首块逐字节相同。原 devscan 在 Test End 后无限循环，观察后终止自有进程组；本次进程 exit0，不冒称 guest GOOD/自然退出。`storage-result.json` |
| NEMU nanos 消费者 | 最终 native 运行 **51.73秒**；八帧实际观察 nterm `qzx: command not found` 后新提示符、幻灯 **0→1→同0**、前台切换，hello **1494→7215**。PAL 初帧黑屏、返回/Enter 仅部分蓝框，保留旧供给/绘制风险，未宣称 PAL 完整画面或性能修复。观察后自有组 SIGTERM/-15，非 guest 正常退出。`nanos/result.json`、`visual-qa.json` |
| 身份/组合状态 | 最终源码、配置、binary SHA 与 nanos 实际执行身份一致，主工程 ramdisk SHA 保持 `815fca56e386ad16df98941d1a7cace235cc6e92cc166cd781d7ded9d913e7d4`；**15 项清理前核验通过**。`identity.json`、`validation-preclean.json`、`repair.patch`；清理后另存终检，不用已删除二进制重跑旧验收 |

本轮只改 NEMU 磁盘设备；CPU 指令/AM/生成器/调度/RTL均未改。CPU-tests、RT（NPC 路径无该磁盘设备）与 NPC 全 SoC/STA 不在受影响闭包，不重复执行；nanos/Navy 原源和生成器未改，沿已验收的 Navy 输入临时复制运行，不重 update、不写真实 ramdisk。无新配置选项、安装、Linux/全配置/长时/并发/物理声音显示测试；paddr64 仅小内存域定向配置，不等于完整 PMEM64 集成。

夹具修正也如实保留：第一次截盘短读观察受 libc 缓冲影响，夹具改为保留初始化元数据后重新打开被截短临时盘，验证真正意外 EOF；无 DEVICE 时 a0000300 属 SDRAM，移除“必须为 MMIO”这一错误预期并由 SDRAM 域用例覆盖。guest 首轮缺私有 ISA include、第二轮把串口 stderr 错当 stdout、storage 首轮误等自然退出（其本来无限循环），均修正运行配方/判据后重验。最后因容量增加 AM int 表达性限制，重新构建最终源码并重跑本表关联验证；不将旧 binary 冒作最终源码。

<a id="artifact-cleanup-20261019"></a>
## 验证后清理与旧 manifest 迁移说明

已按用户明确授权清理整个 CCR 树，先保存实际结果/目视观察、Git/源码/配置/产物身份及必要补丁，再删除可再生文件。两次应用回执位于 `workflow/local/cleanup-20261019-applied.json`、`cleanup-20261019-source-applied.json`，逐文件含路径、原字节/分配字节、SHA、类别及实际结果；第二次补清各历史命名的源码/头文件副本。最终 `cleanup-20261019-postscan.json` 为零候选。

- 共删除 **18,660 个文件**，包括旧/新镜像、截图、ELF/共享库/可执行文件、对象/预编译头、波形、生成网表、隔离构建目录及生产源码副本；没有已跟踪文件删除，不跟随目录 symlink，不触及主工程/外部资产。
- **14 份大原始日志无损 gzip**，压缩前 2,354,965,083 字节、压缩后 47,735,754 字节，逐份解压 SHA 校验后才删除原件；新入口为原路径加 `.gz`。
- 合计逻辑占用减少 **4,608,951,502 字节（约4.29GiB）**。保留主要空间为 `coverage.jsonl` 等权威文字矩阵，不作为编译垃圾删除；此数字是文件逻辑字节，不能等同稀疏文件/共享块场景下的物理释放量。

**本说明适用于本树所有历史报告/manifest**：旧清单仍记录当时实际存在及身份，不能再从历史“本地保留”推定文件现存。清理回执明确解释预期缺失；不得把删后的旧镜像/截图/源码副本当可直接恢复的输入。旧数据结论不改写，截图的当时 SHA 不等于仍可查看原图。必要脚本/报告/日志/JSON/配置/补丁与最终文字结果保留；F0003 时序原始大日志现在为 `.gz`，STA 结果摘要/命令/身份仍在。

### 再生方式

旧 F0009 问题的权威生产源是 `git show f960df0:nemu/src/device/disk.c`（blob `9233fe5`，完整身份见 `local/implementation/identity.json`），不是被删的 `before-disk.c`。其他历史实现沿各批记录的 Git commit/父版本重建；不要重新保存所有版本的完整构建树。当前尚未提交的新实现可由本工作树或 `local/implementation/repair.patch` 恢复。

重新验证时在新临时目录准备对应 Git 版本的源和必要最小夹具，使用已安装工具：本轮配方是 `local/implementation/build.py`（native/REF 隔离构建）、`directed.py/.c`（定向）、`init.py/.c`、`prepare-consumers.py`、`guest.py`及`guest/main.c/Makefile`、`storage.py`、`nanos-run.local/observe_sdl.c`。先重建、再执行，不直接重复已删除产物路径；这些脚本的输出目录应为空。原分析 `local/run.py` 已改为从 Git f960df0 读取旧生产源；原 `local/check.py` 是清理前分析检查，不作为清理后恢复入口。

正常/尾块盘由夹具生成 1024/768 字节重复 0x3c；初始化容量用稀疏盘生成后立即删除；真实 nanos 从工作区现有、哈希如上所列 Navy 输入临时复制，路径经 fixture.json 绑定。没有把真实 Navy 输入存入本记录树或 Git；输入缺失时按 Navy 既有配方在对应版本重建，不宣称只凭当前 commit 就备份了它。新临时验证完成后按[CRP 清理规则](../workflow/README.md#artifact-cleanup)再次删除生成文件。

收尾停止于本单元 Completed，结果确认/commit Pending，无push/下一批Start/安装/运行中动作。新持久契约记入 D-CRP-F0009-DMA-20261019；唯一下一入口仍为 TASK_QUEUE#crp-next。本地文字资料和 `.agent` 继续沿原持久化规则，不从 commit 推定已获备份。

清理后终检 **21/21 通过**，保存 `local/implementation/validation-final.json` 与 **568 份文字证据**的 `manifest-final.json`；核对所有删除路径确实不存在、gzip身份、源码/真实ramdisk未变、零残留产物、119项计数与44/75状态、唯一下一入口/完成快照、链接、空index及`git diff --check`。清理前历史manifest保留原样；本终检合并清理回执，不要求已删除二进制仍存在。下一候选F0016仅Planned，尚未Start。

<a id="approval-submit-20261019"></a>
## 用户手工验证与确认/提交补充

用户明确：“我手动执行过了，pal绘图是正常的，是因为程序跑得太慢了。提交修改”。该指令确认本批已报告范围并授权提交；PAL 绘图正常的结论来源是用户手工执行，不冒作 agent 新测试。原短窗口黑屏/部分蓝框观察保留，但不再作为当前绘图功能未闭合的风险；运行慢并未通过本次修改优化，不新增性能修复声明。

提交前复用既有464定向/6初始化、真实guest/storage/nanos及21项收尾验收，核对最终文字manifest、生产源码身份、清理回执与零新增产物；不重造已删除构建/截图，不重复完成快照。仅提交本批8个归属明确的生产/报告/CRP流程文件，一次性测试脚本/结果和清理逐文件回执仍按本地忽略约定保留。实际提交以包含此补充的 Git commit 为准，完整 SHA/暂存范围/结果见 `local/implementation/submit-receipt.json` 及 CURRENT_STATE 对应回执；本次不push、不开始F0016，44已修/75未修完不变。
