# CRP F0004 / F0005 / F0008 — 宿主内存实现

2026-10-18启动，2026-10-19收尾。**本组三项Completed；本组结果确认/新修改commit Pending。** 用户“提交，继续”确认并授权F0019实际提交522bed7后执行TASK_QUEUE唯一入口一个组；Start前root/index干净，M2保持。F0004/F0008新增修复，F0005是对F0022既有代码的补验/清单闭合，二者分开记录，不重复代码或历史Completion。

## 计划与修改

一个阶段：原版非对齐UBSan/旧malloc静态初始化/指针表达式证据→逐项最小修改/定向验证→static/malloc、MEM_RANDOM、native/REF真实构建与guest、CPU全集/RT/nanos/AM按共享影响回归→留档/索引/状态后停止。交付host.h/paddr.c、本报告/局部ignore与本地证据；保持Make选项/默认配置/REF ABI/地址映射/EEI及业务RTL。无安装或新策略裁决。

参考：2026-10-18读取[ICS-PA2.2](https://ysyx.oscc.cc/docs/ics-pa/2.2.html)的取指→vaddr→paddr调用链；结合原P2、F0014 REF边界与F0022 AM前置。C未定义行为的根因与修复以源码结构为依据，不把sanitizer未报等同于无UB。

| 项目 | 实际结果 |
|---|---|
| F0004 非对齐/有效类型 | `host_read/write`的1/2/4/8字节改成局部对应宽度整数与RAM之间的定长memcpy，保留读取零扩展、写入低位截断。MEM_RANDOM也通过host_write填充，去掉对uint8_t数组的uint32_t指针解引用；原随机种子/调用次数/现有小端宿主字节保持。不改变RAM允许非对齐访问的既有EEI，也不新增大端宿主支持 |
| F0005 动态PMEM编译 | 既有bc7a110的F0022修复已将malloc模式mem_regions初值设NULL，init_mem分配成功后绑定；本组**没有再次修改该表达式**。旧台账未镜像本问题，现凭原编译错误、当前malloc真实构建/初始化/失败断言及AM路径验证闭合，不把其源码修复日期改成今天 |
| F0008 中间越界指针 | `pmem + paddr - CONFIG_MBASE`改为`pmem + (paddr - CONFIG_MBASE)`，先做整数减法，再一次形成数组内指针。合法首/尾/one-past转换保持；不扩展guest_to_host对非法调用的验证契约。F0002高位截断与F0009 DMA整段检查仍独立未修 |

生产仅两文件共12增13删。原F0008在合法base处的首次加法就尝试偏移0x80000000、数组仅0x08000000，随后减回不撤销UB；修复后整数偏移为0。该静态证明独立于当前优化器是否把旧表达式折叠成正确机器地址。

## 本次验证

| 验收 | 本次结果 / local入口 |
|---|---|
| 原版精确反例 | baseline/原host_read(bytes+1,8)和host_write(bytes+1,4)均被UBSan以misaligned诊断拒绝。F0005取bc7a110父版本的原paddr.c，malloc头配置下GCC C报initializer element is not constant；同配置当前源码编译成功。原P2/旧日志不改写 |
| 宿主定向 | 真实host.h/paddr.c，static与malloc各ASan/UBSan和GCC-O2共**4×181=724检查**；Clang-O2另**2×181=362检查**。宽度1/2/4/8、偏移0..7、两侧字节哨兵/小端独立oracle/写截断、PMEM首末/one-past与checked尾拒绝、随机填充逐字节一致均通过；malloc失败沿既有assert拒绝。测试小内存仅用于边界，未替换生产内存实现 |
| 全量配置构建/初始化 | 当前native static与malloc两种128MiB配置（MEM_RANDOM开启）分别真实构建、内置guest GOOD TRAP；新REF按原riscv64-ref配置构建，原M1-P9 ABI检查通过（33字GPR/PC选择复制、哨兵、五内存域、真实执行/time=0）。不重新配置或覆盖根默认解释器/REF |
| 真实非对齐/跨页guest | 两native模式实际执行非对齐SD/LD/字节检查均GOOD TRAP；补充裸地址跨4KiB页边界8字节读写，static/malloc/共享REF三者均通过。共享REF真实guest检查a0/数据寄存器与终态；跨页是bare模式，不冒充单独Sv39故障恢复测试 |
| CPU全集 | 新static native与新REF/NPC各实际`make ... run`，**各36 PASS + wrong 1 XFAIL，两个make exit0**；逐例原始主终态、make/工具退出及无分歧/预算耗尽核对通过。NPC硬件执行器运行前核对既有当前源码身份，不使用根旧模型；cpu-results.json与两套37份日志 |
| RT真实消费者 | 当前既有PSRAM/SSBL RT镜像+本组新REF+已核对NPC执行器，**163.32秒到msh，difftest ON，无分歧**。观察后SIGTERM自有组/exit-15，非guest正常退出。RT/AM生产源码/生成器未变，沿用前组已验收image，未重新update，不把本轮写成重建RT镜像 |
| nanos真实消费者 | 新native解释器、当前AM/nanos独立build、既有Navy镜像，**51.74秒8个观察点**：F2终端输入后画面变化、F3翻页/返回页hash一致、F1回PAL及Enter前后变化；后台hello 1267→5894，8点严格递增。观察后自有组SIGTERM/make exit-15，非guest正常退出，不宣称PAL流畅度或游戏阶段 |
| TARGET_AM实际消费者 | 同版TARGET_AM强制malloc/32MiB，分别真实AM-native及riscv64-nemu构建/执行20B guest；AM-native成功退出，RISC-V外层/内层两次Welcome、两次GOOD TRAP。覆盖本组头文件在AM/klib链接闭包，不仅native libc测试 |
| 判据与终检 | 6个终态判据故障控制拒绝；validation.json **23/23**。各构建使用同版最终源码，根native/REF/NPC及配置SHA未变，原F0019 101文件清单无漂移。identity.json、源码before/after、patch、配置及必要日志清单可恢复 |

本轮全共享影响分别选择真实消费者。CPU按-j1；NEMU CPU-tests沿用`--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`测试兼容配置，所需符号来自既有mem-test.c声明，不是malloc自身要求；不声称无该符号的默认NEMU全集命令通过。先前F0052补充报告将其原因写成共享malloc依赖，现追加勘误。RT/Navy生成器未改，故未重新update这两类资源；nanos镜像在新AM树构建，实际ramdisk/头文件来自原Navy产物。

## 证据、失败尝试及限制

- 主要配方为local/baseline.py、directed.py、build.py、prepare-consumers.py、cpu.py、rt.py、nanos-run.local、am.py、cross-page.py及cross-page-final/ref.py、verify.py。已有输出目录禁止覆盖；复现用新路径，逐命令日志/argv/exit及输入配置见各JSON。NEMU编译禁用自动compile_git，AM及guest make传git_commit=，无自动提交/安装。
- 原版/当前malloc语法检查首次漏了生产构建的__GUEST_ISA__宏，baseline-attempt1无效、保留不计PASS；补齐宏后的baseline明确区分旧初始化失败和当前成功。首次分配失败对整个libc拦截malloc，无法可靠定位目标，directed/保留；最终directed-final只控制paddr分配调用，assert定位pmem。跨页REF首个夹具误用regcpy方向，cross-page/ref.log失败保留；只更正夹具、以原ABI方向重跑REF通过，静态/malloc已通过日志不覆盖。以上不影响最终生产源码或已验收镜像。
- guest_to_host仍以既有有效PMEM/one-past转换前置使用；非法地址的checked访问用addr_to_soc_range/paddr_try接口验证，不能据此声称raw helper或disk DMA已经安全。没有改变one-past、对齐异常/地址宽度/内存映射政策。
- 仅当前x86小端宿主、RV64配置实际验证；未声称大端/RV32/RVE、所有配置/完整Linux/全部AM应用、真实声音/长时负载已通过。默认REF仍为静态PMEM且不调用init_mem；本组没有新增REF-malloc初始化能力，不将native/AM malloc成功推广为任意REF配置可运行。MEM_RANDOM先按原32位rand值填充的字节oracle验证，不声称跨宿主rand序列相同。
- 只复制一套共用NEMU源码供隔离配置构建，consumer/工具各有独立生成目录；RT镜像及Navy公共资源为外部引用，冷恢复需携带或按既有配方重建。临时夹具/源码/日志/截图/二进制均仅local，本批不提交一次性测试代码/生成资产；manifest的311个文件条目不等于测试数量。普通commit不备份ignored证据/.agent或外部资源。

累计**38项修复Completed/81未修完**，含5CQ/F0040Partial；本组三项结果待确认，其中F0005代码早已提交bc7a110，新增F0004/F0008代码本轮未提交。F0019已确认提交522bed7；F0026栈预算、PAL/F0043/两缺源等保持，不重写旧119项审阅截面。root HEAD522bed7，Working tree contains uncommitted CRP code/documentation changes，index空、无运行中动作、未push。记录与索引/状态已同步，本组留档后停止；未来仅沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动commit/push/下一组/M2。

## 用户确认及提交（2026-10-19）

用户“提交，继续CRP修复”确认本组已报告范围/限制并授权提交后执行队列下一组F0006/F0007。提交前核对311文件manifest、两份生产源码SHA及23项既有验收均无漂移，复用动态结果，未重跑已验收测试。仅提交生产代码、报告/局部ignore和索引/事实附记；一次性local证据与.agent继续本地忽略，不视为已备份。实际提交回执见local/submit-receipt.json及.agent追加记录；本次不push，新组修改不自动提交。
