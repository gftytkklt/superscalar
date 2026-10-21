# CRP F0073 — 用户指针与故障恢复必要分析

## 整体计划（2026-10-21）

来源：用户“提交，继续”；F0110已确认并实际提交111059c012272b6a6b0706833ceb5a9f448502ba，根树/index干净；ONS5e72dbb及既有编码行保留。本次仅执行唯一TASK_QUEUE#crp-next的F0073必要分析，生产未改，107+8+2+2保持，M2不变。

目标/范围：核当前syscall→FS/设备、exec参数/加载、irq→AM trap、VME用户区/页表/MMU的实际路径；复核讲义允许简化、Linux计划需求及F0029权限契约，区分已实现功能错误和用户输入容错/隔离扩展。特别核内核内部sys_execve/context_uload/FS调用、当前satp与MPRV，避免统一范围检查误拒绝合法内核指针。

本单元阶段：冻结必要源码/八正式资产身份→定向静态调用链/参考核验→原版host及必要真实RV64见证→提出最小方案和真实保护/失败策略裁决→证据清理、记录/索引/状态及唯一入口。交付本报告、最小配方/命令/日志/退出码/源码和产物SHA、清理/验证回执；不保留可再生二进制或全生产源副本。

验收：明确哪些指针被直接读/写、正常有效指针是否可用、NULL/未映射指针如何终止、恒等内核映射是否仍可被访问；不把host SIGSEGV冒充guest EVENT_ERROR，不以简单区间检查冒充完整隔离或可恢复EFAULT。若真实RV64使用独立microkernel，标识实际复用的syscall/irq/AM与桩，不冒称完整nanos应用回归。生产未改时不重跑CPU/RT/游戏等既有验收。

停点/人工项：保护边界、失败返回/进程处置、copyin/out与F0029权限策略未冻结前不实施；不自行选“非法指针返回EFAULT”或删除原问题，不以Linux本身安全功能替代nanos契约。安装/下载/系统改动即停，本轮仅用现有源码/工具，不commit/push/下一组/M2。分析文档未提交不增加裁决后同组实施的门槛。


## 实际分析与调用边界

本轮基线为根`111059c012272b6a6b0706833ceb5a9f448502ba`；entry.json冻结13个必要输入与八正式资产，ONS既有编码差异另以diff SHA保持。没有生产源码、配置、Makefile或默认磁盘/镜像修改。

| 路径 | 当前事实与影响 |
|---|---|
| do_syscall→open/read/write/gettimeofday | 由Context直接取用户指针，传给FS/设备或写timeval；没有通用copyin/out/范围及页访问预检。bad fd在FS层可先返回EBADF，不能擅自改变成指针错误优先 |
| FS/设备 | fs_open读取pathname并规范化到256字节局部数组；长度限制不保证源地址有效。普通文件复制、串口/事件/音频/GPU也会消费用户缓冲区。部分零长度设备路径可不访问buf，新增校验时须保留相应语义，不预选NULL+0失败 |
| exec参数 | F0061既有修复限制32KB预算/对齐/字符串长度，不证明指针数组/每个字符串页已映射；count_args与后续复制仍直接读源。当前进程satp在这段复制期间保持，不能把用户VA误当物理PA |
| 内核内部调用 | sys_exit用内核常量/局部argv调用sys_execve；init_proc也用内核字符串/数组调用context_uload；loader用内核scratch/目标物理页调用FS。若在共用FS或context_uload一律要求指针属于用户area，会误拒这些合法内部路径；入口层区分来源与内部复制接口需另定 |
| AM映射与硬件 | USER_SPACE是[0x40000000,0x80000000)；protect复制kas，map对所有leaf追加RWXUAD/V并直接混入prot，未做AM权限位转换。内核PMEM恒等映射也U。NEMU RV64现MMU按MPRV/MPP选择有效数据访问特权并检查PTE权限；AM trap主动置MPRV，让有效用户VA在M态handler中依当前satp工作 |
| 错误传播 | AM CTE未识别cause转EVENT_ERROR，nanos irq默认panic；没有copy fault fixup、EFAULT返回或仅结束当前进程的路径。一个区间判断不能自动补齐这些机制，更不能阻止应用绕过syscall直接访问现有U内核映射 |

这里只定位已有调用与边界，不把F0073改成硬件MMU缺陷。AM/MMAP声明与教学子集的既有冲突仍归F0029；F0031/F0071是另一组已批准Linux能力移交，本次不将F0073混入该移交或新增Linux实现任务。

## 讲义与现行需求复核

2026-10-21读取[ICS-PA3.3](https://ysyx.oscc.cc/docs/ics-pa/3.3.html)、[4.1](https://ysyx.oscc.cc/docs/ics-pa/4.1.html)、[4.3](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)。3.3要求正常buf/len系统调用输出及正确返回；4.1的初始化参数由内核构造。4.3在map/prot章节明确暂不实现保护、prot暂不用，并把MMU_FAIL描述为PA不会发生的情况；这支持将本项识别为尚未冻结的容错/隔离需求，而非据讲义强加完整POSIX EFAULT机制。网页访问摘要/链接见local/references.json；未把当前2025讲义页面冒充用户历史版本。

本地AM的MMAP_NONE/READ/WRITE公开声明与上述教学简化并不完全一致，原F0029保留ContractQuestion。此前只允许记录CQ，不等于用户已批准实现不保护；本轮因此先展示真实结果再请用户裁决。Linux计划主线使用真实Linux自身的用户访问/异常处理，未发现要求nanos实现完整用户指针隔离的明确验收项；这不证明nanos坏指针已安全，也不授权agent自行关闭问题或移交范围。

## 真实RV64原版见证

本轮最终直接使用真实RV64，替代原计划中较弱的host同构指针观察；没有用host SIGSEGV冒充guest故障。rv-probe.py在local/build复制现有AM并沿现有`make ARCH=riscv64-nemu git_commit= image`构建五个独立微内核，读取当前nanos syscall.c/irq.c/mm.c及真实AM VME/CTE/trap；没有下载/新安装或改AM生产源。既有正式NEMU解释器SHA为entry记录值，不重建默认引擎，运行只读正式磁盘且未发起磁盘写。

探针初始化真实页表、映射用户代码/数据，通过ucontext/mret进入U模式，执行SYS_gettimeofday(19)，随后yield回到最小schedule观察；未用直接M态C调用替代用户ecall。schedule和本次未执行的FS/exec函数由夹具提供桩，无完整loader/文件系统/多应用运行的声明。用户代码没有栈访问；timer源在夹具中清mie关闭，使判据只接收预定ecall，不改生产中断规则。

| case | 原版参数/映射 | 实测结果与判定 |
|---|---|---|
| 0 | 正常已映射0x40001000，READ/WRITE | timeval哨兵被真实uptime覆盖，ret0、np=U(0)、后续yield cause8；GOOD TRAP/exit0。正常路径可用 |
| 1 | NULL | nanos do_event报告Unhandled event ID=4（EVENT_ERROR），BAD TRAP/exit1；未返回用户。未记录精确mcause/mtval，不虚构具体cause编号 |
| 2 | 用户area内未映射0x40002000 | 同样EVENT_ERROR/panic/BAD TRAP/exit1；简单属于area并不足够 |
| 3 | 内核全局timeval地址0x80003000 | 不在用户area，但syscall实际写入内核哨兵并ret0，GOOD TRAP/exit0；证明当前边界无此保护，不把GOOD当安全通过 |
| 4 | map(...,MMAP_READ)的数据页 | 仍可被gettimeofday写入并ret0/GOOD TRAP；权限需求依赖F0029，不能只加非NULL检查就宣称隔离 |

五个case各构建/运行一次，最终10命令日志/镜像身份见rv-commands.json；正常结果移除返回标记、把exit伪造为1，两种假PASS均被拒绝。GOOD/BAD用于确认原版观察符合预期，不能把三GOOD两BAD合写为系统容错通过；没有新增修复功能验收或完整nanos回归。

夹具问题如实保留：初次漏引入USER_MODE定义、第二次缺AM私有include路径，均仅编译失败；修正夹具后运行最初误把U态即刻timer当成测试返回，哨兵/ret判据正确拒绝。仅清mstatus.MPIE不足以阻止U态被更高特权中断抢占，最终在隔离夹具明确清mie后完成预定ecall；attempt日志保留，不把这些失败当生产新问题，也不覆盖正式成功证据。最终两坏指针运行原异常处理器，未加诊断替换EVENT_ERROR返回。

## 方案比较与用户裁决

| 选项 | 所需契约与边界 |
|---|---|
| 本轮建议：延期并保留风险 | 保持正常可信程序的教学子集；F0073/F0029继续未修，不冒充安全/容错通过。需要该能力时联合恢复并冻结验收 |
| syscall入口校验并返回EFAULT | 需明确来源、NULL/零长度、fd错误优先级、字符串/argv逐页上界、读写方向/权限及预检后失败策略；不能在共用内核FS接口一刀切。仍不能替代硬件/页表隔离 |
| 完整权限隔离与故障恢复 | 联动F0029、kernel/user PTE、prot转换、MPRV与内核栈、copyin/out/fault fixup或进程处置；属于更大范围，不能从“继续”推定授权 |

用户已在看到上述真实结果及三选项后明确选择**“延期并保留风险（推荐）”**。因此本轮分析Completed；F0073保持Robustness/Medium/未修/已批准延期，F0029保持ContractQuestion/Medium/未修/已批准延期。此为延期决定，不是ApprovedGap、Closed、Fixed或现实现已符合完整AM/POSIX契约；不将其计入两项无需实施闭合/两项Linux能力移交。后续有具体坏用户指针容错/隔离需求时再联合冻结范围与失败/权限验收，本轮不实现入口guard、EFAULT或页表改动。

## 收尾、持久化和停点

原版13源码/八正式资产及ONS原差异SHA最终保持，根生产无修改，HEAD111059c不变。进程均已结束；删除前逐路径记录local/build的生产副本/对象/ELF/bin/反汇编/隔离AM文件的字节与SHA，再清理整个本组build；实际数量/字节与0 tracked/正式资产删除见cleanup-receipt.json。保留本报告、rv-probe.py/probe.c/user.S最小夹具、命令/原失败及最终日志、entry/内部调用导航/参考摘要、验证与清理manifest；复现旧源按111059c及现有正式引擎身份重建，使用新证据目录，避免覆盖本轮日志。

F0110上一批已确认实际提交111059c，本批分析/延期文档尚未提交，index空；本轮“提交，继续”未额外授权提交新分析文档，不push。119=107已修+8CRP未修完+2能力移交+2无需实施闭合不变。唯一下步仍由TASK_QUEUE#crp-next管理：当前分析/延期结论确认与文档提交后，后续明确继续才处理F0043/F0118音频提交/重开生命周期的必要范围分析一个单元，尚未Start；既有其他延期独立保持，M2不变。

会话建议：建议开启新对话；本对话已累积字体、窗口与用户指针三类证据，当前结论/恢复入口已整理。该建议不额外增加确认/执行门槛，ignored证据/.agent仍需本地保管，Git提交不代表备份。


<a id="submit-20261021"></a>
## 用户确认与文档提交（2026-10-21）

用户“提交后继续”确认本批已报告分析及延期结论，授权提交本批四路径文档后执行TASK_QUEUE#crp-next的F0043/F0118必要分析一个单元。提交前29保留证据、13源、八正式资产与ONS既有编码差异SHA一致，复用既有验收/清理，无新动态测试。只提交报告/.gitignore及process、repair-status索引；最小夹具/原始证据仍本地忽略，不声称随Git备份。实际提交身份与blob核对见local/submit-20261021/receipt.json及.agent回执；不push、不自动提交下一单元。

会话建议：可在当前对话继续；本次已按唯一入口恢复，下一音频分析边界明确，证据可定向读取。
