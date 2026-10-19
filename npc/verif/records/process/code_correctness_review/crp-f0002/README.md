# CRP F0002 — RV64物理地址身份

2026-10-19 Start。用户“提交并继续CRP修复”确认F0006/F0007并提交7e68ca7后，执行既有唯一入口一个复杂单元；M2不变。

## 计划与验收

复用CCR-P2 high-bare/high-pt反例，核对D21与LINUX_M1_PLAN §3.1 → 最小修复 → 定向/native及REF真实构建与受影响消费者回归 → 留档停止。交付mmu.c、本报告/ignore及索引/状态；测试源码、快照、日志/镜像仅local。

保留paddr_t及成功翻译/访存/REF ABI；以word_t保留Bare地址、Sv39 root/nonleaf地址与叶地址，窄化前显式检查可表示性，之后仍走现有注册内存/MMIO整段检查。不扩容、不改satp WARL或Make接口，不增加MMU能力。D21已要求坏物理地址access fault，此为落实既有契约，无新策略裁决。

验收Bare读/写/取指、MPRV、LR/SC/AMO；高root/nonleaf/leaf、4GiB边界和最高PPN。检查原PC/cause/tval、rd/低RAM/低页表/MMIO无别名副作用，覆盖委托；合法低地址、页表权限与原ABI保持。逐项生产CPU链定向后同版native/REF及双CPU、RT/nanos按共享影响覆盖。不得以假guest替代真实消费者；缺测/历史限制明列，组完成后等待确认/commit。

参考（2026-10-19）：[ICS-PA4.3](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)分页/Sv39范围及官方Sv39规范，结合D21现有三级/大页能力，不将课程简化范围误作回退既有能力的依据。

## 完成结果

**F0002 Completed；本批结果确认/commit Pending。** 生产只改`nemu/src/isa/riscv32/system/mmu.c`（16增5删，riscv64软链接共用），未改`paddr_t`/`FMT_PADDR`、访存/REF导出ABI、satp WARL、内存映射与Make接口，无安装或RTL修改。

Bare直通在赋入paddr_t前拒绝不可表示地址；Sv39的root/nonleaf table及pte_addr使用word_t全宽计算，在调用物理页表读前检查可表示性；叶PA先完整计算并检查，再更新A/D及交付paddr_t。合法可表示地址继续由现有注册区域/MMIO整段检查判定，不将32位容量之外的地址截断为有效低地址。失败沿D21原access fault路径返回原VA，CPU保持原指令PC/cause/tval及既有委托语义，避免rd/低RAM/低页表/MMIO别名副作用。

| 验收 | 本次结果 / local证据 |
|---|---|
| 原P2见证复用 | 未改P2 repro.c，链接本次成套原/新生产CPU链。原LD命中低RAM、store改为abcdef，高root/leaf读取成功；修复后LD cause5/原PC=0x80000000/tval=0x180002000，store返回false/cause7且低RAM保留1122334455667788，高root/leaf返回false/cause5。见p2-results.json及baseline2/final3中p2日志，不把该观察夹具exit0当作guest成功 |
| 组合定向 | baseline2 **86项中45失败**；final3 GCC-O2与ASan/UBSan各 **86/86**。覆盖Bare读/写/取指、4GiB前后/64位末端、MPRV数据及取指忽略MPRV、LR/SC有/无reservation及AMO的W/D、高root/两级nonleaf/leaf、最高44位PPN、2MiB/1GiB叶、原PC/cause/tval与M/S委托；高RAM/低页表快照及受控MMIO回调无副作用，低域/MMIO/A/D/只读与非规范VA/PMEM末端和跨界无部分写控制通过。repro.c链接生产CPU/ISA/MMU/内存；仅时钟/设备为受控输入，不称其为真实设备回归 |
| 真实native/REF | 同版源码隔离构建两配置，native内置guest及原REF 33字PC/GPR/五内存域ABI检查通过。高地址小guest校验10次精确trap（Bare LD/SD/LR/SC/AMO/取指及MPRV高root/两级nonleaf/leaf），两平台GOOD TRAP；同一镜像在前批原native为BAD TRAP/exit1。既有m1_p7_sv39、m1_p7_sfence_priv及m1_p6_atomic在native/REF均GOOD TRAP，共8次真实guest执行，不借新增导出状态接口。见guest-results.json/high-original-native.json |
| CPU真实全集 | 新REF/NPC与新native各 **36 PASS + wrong 1 XFAIL**，make均exit0；65.02/24.68秒，逐例74份主终态/退出状态检查通过，无SIGTERM/预算耗尽替代正常终止。NPC先核现有RTL身份/模型SHA；NEMU沿用既有`--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`测试符号、-j1兼容配置，不声称默认缺符号入口已修 |
| RT真实消费者 | 当前已验收NPC模型 + 本次新REF，163.33秒到msh、difftest ON，无分歧。RT镜像源/生成器未改，复用已验收镜像并记录SHA，不重复update。到观察点后终止自有进程组，SIGTERM/exit-15，非guest正常退出；见rt-result.json |
| nanos真实消费者 | 本次native在隔离现AM/nanos源码、现Navy ramdisk下实际构建运行，51.72秒完成8个截图点：F2到nterm/键入命令、F3 slide 0→1→0、F1返回PAL及Enter后继续，后台hello 1326→6382递增；截图实际目视核对，未宣称PAL性能/实际声音或完整游戏通关。源/生成器未改，不重复Navy update；观察后自有组SIGTERM/exit-15。见nanos/result.json与contact.png |
| 终检 | validation.json **23/23**：含6种虚假PASS判据故障拒绝、成套原版/同版定向/真实构建源码、前组647文件manifest无漂移、默认模型/配置保护、原HEAD/空index/空白检查。必要manifest **285文件**，是源码身份、测试、配置、日志及截图等文件条目，非285用例 |

参考补充（2026-10-19读取）：[官方特权规范](https://docs.riscv.org/reference/isa/_attachments/riscv-privileged.pdf)当前返回20260120版本，核对翻译过程的satp.ppn×页大小、非叶PTE物理地址与原访问类型access fault；仅作既有D21/项目Sv39契约的补充，不因此新增规范扩展或改项目既有版本边界。

## 复现、限制与交付

主要命令：`python3 local/directed.py baseline2`与`final3`；`python3 local/build.py`、`guest.py`、`prepare-consumers.py`；`python3 local/cpu.py`、`rt.py`和`python3 local/nanos-run.local nanos`；最后`python3 local/verify.py`。p2见证链接命令见local/p2-replay.py。隔离目录和日志使用新建语义，重现应换输出路径，不覆盖现有证据；命令、配置、退出码与实际产物身份见JSON/manifest。Make禁用compile_git，AM传git_commit=，没有隐式commit。ASan仅局部设置detect_leaks=0，不声称泄漏检查通过。

首轮86项前的78项夹具中，Sv39 MMIO场景漏了0x100页内偏移，未真正命中预期低MMIO；最终baseline2/final3已纠正，新增4GiB/大页边界。本地baseline/final/final2保留尝试历史，不用其较窄覆盖替代最终86项，不列作生产缺陷。

本次针对当前x86小端/RV64、paddr32、默认native/静态PMEM REF；未跑PMEM64完整配置、RV32/RVE/其他ISA、Linux、全配置/长时/实际声音或完整四AM应用运行。未改变legacy vaddr_*失败政策；其RV64分页适配仍调用checked翻译，CPU实际取指/数据/原子使用既有显式checked链。F0009 DMA等直接物理API调用者的非法窄化另属独立问题，本修复不冒称其闭合；F0001算术、F0003对齐、F0026栈预算、F0040Partial、PAL性能因果、F0043、五CQ与两缺源保留。

测试C/脚本/汇编、源码快照、JSON/日志/镜像/截图均仅local，不随未来修复提交；本批提交候选仅生产mmu.c、本报告/局部ignore及必要索引/修复镜像。当前root HEAD7e68ca7，Working tree contains uncommitted CRP code/documentation changes，index空，无push/安装/运行中动作。普通commit不备份ignored证据/.agent；跨会话/异机需另带本地资料与配方，外部RT/Navy源和镜像引用亦不算已备份。

累计 **41项Completed / 78项未修完**；前40项已确认提交，本批F0002待确认/commit。留档后停止，下一候选F0001算术单元未Start；唯一范围/验收/门槛仍见[TASK_QUEUE](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动提交新修复或推进M2。

## 2026-10-19 确认/提交补充

用户“提交后继续”确认本批已报告范围与限制并授权提交。285文件manifest、23项既有验收及生产/默认模型配置身份保持，复用动态结果；仅暂存生产mmu.c、本报告/局部ignore、process索引与repair-status共五文件，一次性测试/证据继续local保留。实际提交回执见local/submit-receipt.json及.agent补充，未push；ignored资料不由commit备份。用户同时要求下一算术单元说明具体反例、复核NPC对应实现，确认双端问题时一并修复；不由NEMU的C未定义行为直接推定RTL结果错误。
