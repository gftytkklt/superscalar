# CRP F0006 / F0007 — FENCE.I与非法指令诊断

2026-10-19 Start，用户“提交，继续CRP修复”授权前组提交1ddaf04后执行唯一队列入口。本组实施与验收中；M2不变。

## 计划与边界

一个阶段：复用P2原反例、核对当前路由→逐项最小修复→定向/真实native与REF构建、受影响消费者回归→证据/索引/状态收尾后停止。交付inst.c、cpu.h、hostcall.c及必要的其他ISA调用签名适配、本报告/局部ignore、本地证据。不安装、不改Make入口、D18 INV失败政策或新增guest异常/缓存能力。

F0006只约束FENCE.I opcode/funct3，忽略imm/rs1/rd并验证GPR不变；riscv64为riscv32软链接，只改真实源一份。F0007传递Decode已取得的32位原指令，诊断不再取当前/下一字；保留原PC和NEMU_ABORT。其他现有固定32位ISA仅适配调用，不扩展其功能。

验收：标准/单字段非零/全1 FENCE.I、rd哨兵/非法funct3控制；PMEM尾、Sv39页尾且下一页未映射或无X、MMIO邻接；检测原PC/指令、NEMU_ABORT和guest CSR不被诊断改写，诊断零附加取指。复用P2生产执行链定向，真实native/REF与受影响CPU消费者选测；其他ISA仅构建兼容性验证，不声称完整guest回归。

依据（2026-10-19读取）：[ICS-PA2.2取指/译码](https://ysyx.oscc.cc/docs/ics-pa/2.2.html)、[官方Zifencei 2.0](https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf)规定忽略保留的funct12/rs1/rd字段；原P2/FINAL_FINDINGS F0006/F0007及D18。临时测试/原始证据留local，不提交。

## 完成结果与验证

**本组两项Completed，结果确认/新commit Pending。** 生产改动5文件15增20删；保持原Make入口、REF导出ABI、访存/异常政策，无安装和业务RTL改动。

| 项目 | 改动与结论 |
|---|---|
| F0006 | FENCE.I仅匹配opcode/funct3，其他字段全部通配，执行仍为no-op/PC+4，不写rd。riscv32/64同源，仅修改riscv32/inst.c一份 |
| F0007 | INV显式携带已取得的32位指令字；hostcall不再读取guest内存，只打印原PC/4字节/指令字并进入原NEMU_ABORT。两处原子指令早期拒绝也适配，MIPS/LoongArch的INV调用机械适配同一签名。诊断缩为当前一条指令，不再预读下一条 |

| 验收 | 本次结果 / local入口 |
|---|---|
| 原版反例 | baseline2保留FENCE.I rd/rs1/imm非零错误ABORT，旧诊断在PMEM尾和Sv39下一页未映射/无X时先SIGABRT；邻接受控MMIO实际多读一次。baseline-nodevice用原生产DEVICE=n分支复现尾外out_of_bound/SIGABRT，未到NEMU_ABORT。原P2历史证据保持 |
| 定向组合 | final2 **28/28**（GCC-O2与ASan/UBSan各14）：标准编码、单字段非零/全1与所有保留字段全1，全部GPR哨兵不变；funct3=2/7保留INV。PMEM尾、Sv39下一页未映射/无X、邻接受控MMIO均报告原PC/指令并NEMU_ABORT，cause/epc/tval哨兵不变。链接包装仅计数，CPU/ISA/MMU/内存仍生产源码；checked取指恰1次、legacy取指0次、MMIO读0次 |
| INV早期调用与边界补充 | extra **12/12**：LR的rs2非零及未分配AMO op两条显式INV，另四个边界，GCC-O2与ASan/UBSan各6；同样无诊断附加取指或CSR/GPR改变。与final2共40次定向执行，不将断言/文件数量作为用例数量 |
| 真实native/REF | 当前默认native和原riscv64-ref配置分别隔离构建，内置guest/原ABI五域检查通过；标准/非零保留位FENCE.I、rd哨兵与写指令→FENCE.I→跳转执行的自修改小guest，两平台均GOOD TRAP。PMEM尾非法指令小guest两平台正确ABORT/原PC=0x87fffffc/原字ffffffff；native正常失败exit1，REF导出API调用进程exit0且输出ABORT，不把它称作guest成功 |
| CPU真实全集 | 新native和新REF/NPC各 **36 PASS + wrong 1 XFAIL**，make均exit0；NPC 64.12秒、NEMU 28.20秒，74份原始主终态/退出状态核验通过，无SIGTERM或预算耗尽代替成功。NPC执行器先核对现有RTL源身份和SHA；NEMU沿用`--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`测试符号兼容配置、-j1，依赖原因仍为mem-test.c |
| 其他ISA兼容边界 | MIPS/LoongArch修改的inst.c及共同hostcall.c前后均可编译；RV32 hostcall同样通过。三种完整构建均有原有阻塞：RV32的RV64专用类型/格式与初始化，其他两种的cpu-exec RISC-V专用csr/priv初始化。compat-check-final对修改源及cpu-exec逐文件使用原/新成套源码头文件，所有错误诊断前后完全相同，不宣称RV32/MIPS/LoongArch完整构建或guest通过，不扩大本组修复 |
| 终检 | validation.json **23/23**：包括6个判据故障正确拒绝、同版生产源码/构建输入、默认模型/配置保护、原前组311文件manifest无漂移、空白/index检查；identity/patch/manifest保存必要证据647文件，文件条目不等于用例数量 |

## 复现与限制

主要命令按序为`python3 local/directed.py baseline2`、`baseline-nodevice`、`final2`、`extra`；`python3 local/build.py`、`guest.py`、`prepare-cpu.py`、`cpu.py`；`python3 local/compat.py`、`compat-check-final.py`和`verify.py`。目录/日志默认新建，已存在的输出不要覆盖，复现需换新路径；命令/配置/结果见各JSON。构建禁用compile_git，AM/CPU传git_commit=，没有自动提交或安装。ASan使用进程局部`ASAN_OPTIONS=detect_leaks=0`，未关闭地址或UB检查；不声称泄漏扫描通过。

当前验证为x86小端宿主/RV64；真实REF保留现有静态PMEM初始化政策，未新增导出状态接口。host诊断路径已由相同生产CPU链覆盖；受影响正常执行用双CPU全集和native/REF定向guest验证。RT/Navy生成器、AM/设备/调度协议未改，本组未重复RT update/run及nanos交互，不用历史msh/窗口结果冒充本轮测试；未运行Linux、所有配置/完整其他ISA、长时或实际声音。

失败尝试单独保留且不计PASS：初版baseline的MMIO stub对未映射访问也返回数据，故不作为尾外panic证据，最终baseline2与baseline-nodevice替代；首轮ASan断言通过但LeakSanitizer在受限环境退出1，final2/extra以仅关闭泄漏扫描重测；guest-attempt1误读未导出的nemu_state，最终改用既有regcpy/PC、日志及定向状态断言，不改REF ABI。compat-before首轮误混新头旧源，不作基线；compat-check初次被宿主ccache只读缓存阻断，最终用/usr/bin/gcc及成套头/源对比。全部无效尝试保留，不把夹具错误列为生产修复。

临时C/脚本、源码快照、日志/JSON/镜像/截图均仅local，不提交；本报告/局部ignore和导航随未来本批提交。manifest含必要源码before/after、配置、日志与实际二进制身份；普通commit不备份ignored证据/.agent，跨会话/异机需另带本地证据和隔离构建配方。

累计**40项修复Completed / 79项未修完**（含5CQ及F0040Partial）。前组F0004/F0005/F0008已确认提交1ddaf04，F0005原代码bc7a110；本组新结果/新修改待确认提交。F0026栈预算、PAL性能因果、F0043、五CQ与两缺源等原限制保持。当前root HEAD1ddaf04，Working tree contains uncommitted CRP code/documentation changes，index空，无运行中任务、无push。本组留档后停止；后续范围与门槛只见[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动提交新组或推进M2。

## 2026-10-19 提交确认补充

用户“提交并继续CRP修复”确认本组已报告范围与限制，授权提交后执行既有F0002入口一个单元。提交前647文件manifest、23项既有验收及生产/默认模型/配置身份均无漂移；复用动态验收，不重复测试或Completion。仅提交5生产文件、本报告/局部ignore、process索引与repair-status；一次性测试/原始证据继续local保留。实际提交回执见local/submit-receipt.json及.agent对应补充，未push；普通commit不备份ignored资料。
