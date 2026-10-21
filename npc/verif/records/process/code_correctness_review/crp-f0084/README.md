# CRP F0084 — libam公开heap初始化与所有权分析

> **现行处置（2026-10-21，用户已确认）**：已核实既定Linux启动链不依赖Navy libam公开heap，按用户指令将F0084 **Closed / 当前目标无需实现**。未修改生产代码，不计已修；先前“必须实现”和静态/动态池候选均为被本次范围裁决覆盖的分析历史。闭合与提交收尾见文末#linux-scope-closure-20261021。

2026-10-21；用户“提交后继续”授权F0113提交后执行唯一入口一个分析单元。前批已确认实际5f38770a521e3f0e44d871cbf7a42d5099ceaa54，root/index干净；103已修+14待修+2Linux能力扩展移交，F0084尚未修复，M2不变。

## 本单元计划

目标：复核公开TRM heap空区间、首个访问和链接可达、初始化入口、libc allocator所有权及宿主预算，形成最小方案并找出真实裁决项。本单元只读生产代码，不先确定固定堆大小、不实现wrapper VME/切换/存储、不开新Make选项、不安装或扩展NPC能力。

步骤/交付：保存当前源/正式资产身份；读取trm/libos CRT/sbrk/newlib/AM消费者；以实际trm链接host反例及RV64对象/符号核对空heap，少量定向验证libc分配不改变heap、已有heap消费者失败；形成初始化/不重叠/失败与重复初始化策略建议、验收清单及最少裁决问题。报告/命令/结果/最小测试配方保留在本目录，更新records索引/repair-status和.agent唯一入口。

验收/停点：分析事实有源码/实际命令支撑，候选与实际实施明确分开；如果预算/所有权/失败语义未获明确批准，则分析完成后等待技术裁决，不修改生产。固定身份后清理可再生对象/执行文件与源副本，正式8资产/newlib状态保持。不commit本单元、不push、不串行下组或M阶段。

参考：[ICS-PA2.3](https://ysyx.oscc.cc/docs/ics-pa/2.3.html)（2026-10-21访问）说明AM模块按应用需求分层；本地README已声明libam支持TRM/IOE，公开heap缺陷不据此扩大成完整内核能力。讲义不为本实现确定堆预算。

## 分析结论（生产修复未开始）

**必要分析单元Completed，F0084仍未修复；静态arena容量待用户裁决。** 本轮不增加已修计数。当前原119项仍103已修均确认提交+14 CRP待修+2 Linux能力扩展移交。

1. `libam/src/trm.cpp:5`只有`Area heap;`。本轮实际将完整未改trm.cpp链接到host probe，最早用户constructor及main均观察到NULL..NULL；先后四次glibc malloc/free成功也不改变heap。正常/sanitizer各15项零失败证明旧缺陷仍存在，不表示heap已修。host probe引用heap触发该对象的真实链接，不把“只声明了符号”当不可达。
2. 同版trm.cpp真实RV64交叉编译exit0，readelf显示全局`heap`为16字节OBJECT，属于4号`.bss`（NOBITS，16字节），对象没有`.init_array`/`.preinit_array`初始化器。只做对象/符号检查，**未运行RV64/完整wrapper**。probe另按原样提取当前nanos `new_page`函数与klib `malloc`函数（只重命名避免覆盖glibc、PGSIZE使用现有4096）：当前空heap下new_page(0)/new_page(1)/klib malloc(0)/malloc(32)均NULL；不是把这些klib函数作为Navy实际libc malloc。
3. Navy的_start→call_main先设environ，后调用newlib `__libc_init_array`再main。newlib启用HAVE_INITFINI_ARRAY，按preinit再init数组顺序执行。这提供constructor初始化入口，但默认constructor之间的先后不能自动保证“任意用户constructor第一次读heap时已就绪”；静态地址初始化则在动态构造前已经就绪，且不需要新增用户步骤或公开初始化API。
4. non-native Navy malloc采用newlib mallocr.h的MORECORE→`_sbrk_r`→libos `_sbrk`，program_break从链接`end`起，只有SYS_brk成功后才前移；这些函数没有heap赋值。nanos mm_brk还受进程地址空间/栈保留/数据页与页表物理余量限制。当前NEMU配置的128MiB是整机物理内存，**不是每个Navy进程或libam独占额度**；不能用heap=[end,128MiB上界)或另起游标直接占用同一动态区。
5. AM native独立实现由platform constructor用mmap创建128MiB区域再发布heap，NEMU bare-metal则用PMEM_END；这是各自平台所有权，不能复制到运行在nanos用户态的libam。Navy ISA=native使用glibc/LD_PRELOAD后端；它与AM native是两个入口。
6. Navy已列举的coremark默认MEM_STATIC，dhrystone使用自带memory/myalloc，typing-game两源没有heap/动态allocator调用。此次定向范围未发现它们直接依赖公开heap，不把既有三应用运行成功当作F0084不存在。实际AM tests devscan/vm及nanos new_page会读heap；VM用例和完整嵌套wrapper仍依赖未支持能力，不能为修heap顺带提供VME/switch/磁盘。

实际14条构建/运行/符号命令均exit0，源码与产物身份在local/entry、commands、build-identities。host runtime使用Linux/glibc；newlib链结论为当前源静态事实，未伪称本轮运行了newlib分配压力或真实Navy进程。源码基线根`5f38770a521e3f0e44d871cbf7a42d5099ceaa54`，nested newlib身份与原mode差异由entry保留。

## 最小方案与待裁决项

建议采用**进程内静态独占arena**：在trm.cpp内声明`alignas(4096)`的静态字节数组，`heap`直接以数组首尾进行静态地址初始化，终止地址采用半开区间。不调用malloc/_sbrk，不另设动态游标与libc竞争；该数组属于ELF数据/BSS，位于链接end之前，libos动态堆从end开始，所有权按链接布局隔开。此为**尚未实现、尚未验证的候选设计**，需容量裁决后再证明ELF布局及实际RV64不重叠。

- 建议起始额度**1MiB（256个4KiB页）**，是保守资源预算建议，不是讲义/已有代码规定，也不表示足够运行完整嵌套nanos。可选择4MiB或明确其它数值。实际链接保留arena的进程会增加对应装载内存，页表/对齐另计；BSS不等于等量磁盘文件payload。不能从128MiB整机空间推定所有并存进程都可成功装载。
- 静态初始化无运行时分配失败，也没有可重复调用的初始化函数重置已消费heap；进程首次装载发布原始区间，exec新镜像遵循现有loader。不新增全局reset；消费者耗尽按已有allocator返回NULL。装载失败沿用既有loader错误路径，不承诺新的回收策略。
- 备选malloc-backed同容量arena也能由libc维护不重叠所有权，但需要额外页对齐空间、constructor先后和失败处置/寿命约定；本项没有现成“分配失败时终止还是保留空能力”的裁决，故不推荐增加这些入口。直接共享end以上裸区会与newlib分配碰撞，不能采用。

**唯一需要用户确定的执行参数：是否采用静态独占方案，以及arena容量（推荐1MiB；也可4MiB或暂缓）。** 原队列要求与WORKFLOW_POLICY §3均要求真实预算/所有权取舍先裁决；本轮不擅自分配该额度或承诺新增完整内核能力。其它日常实现细节由agent处理。

## 获批后的实施与验收范围（未执行）

生产预计只改trm.cpp，不改Make/CRT/libos/newlib。验收须覆盖：任意用户constructor/main前非空且页对齐/半开合法；ELF arena结束不高于end、与libc先后交错分配不重叠且双方内容哨兵保持；首次/连续访问不重置游标、边界/耗尽返回；host sanitizer与真实RV64新源链接/装载/实际读写（对象编译不能代替）。按受影响libam TRM消费者选真实回归并沿用必要update→run；完整wrapper缺失能力继续NotRun，不把扩VME/堆预算以外能力列作验收。实际修复后须正文内嵌完整diff、版本/哈希/正反应用与同版证据/清理；本分析无生产diff。

本分析结束后等用户技术裁决，不要求先commit本分析文档，原“提交后继续”仅授权F0113提交，不授权本单元commit/push。未来只沿TASK_QUEUE#crp-next，不转去下一组或M阶段。

## 收尾、清理与当前状态

39项preclean核对通过：14个实际命令退出、host两次15检查/NULL范围、RV64 BSS符号与无初始化段、同版构建身份、10个生产输入及8正式资产/newlib状态/根HEAD/index/无生产diff。验证结束后按计划删除10个可再生对象/执行文件和所提取函数副本，共132198逻辑字节，零tracked/正式资产删除；build-identities/cleanup-plan/receipt保留预期缺失与再生依据。保留最小probe.c/probe.py、命令/日志/身份及静态结论，不保留生产源码副本，不从host成功推定真实guest能力。

本单元只新增分析报告/.gitignore、process/repair-status和本地状态导航，生产工作树无改动、index空，HEAD仍5f38770。分析Completed不等于F0084已修/用户已确认或本组已commit；本分析结果确认及预算裁决Pending。唯一下一动作等待用户选择静态arena容量，再在同一F0084实施及验收，不要求先commit分析资料；未批准前保持不实施、不commit本组/push/其他组/M阶段。

F0084分析终检：62项PASS，39项preclean及10项预期清理、8正式资产/生产输入/newlib状态保持，119行103已修+14待修+2移交及唯一入口一致。本组只读分析已完成、生产未修/容量待用户裁决，文档未commit；未新增动态测试或开始其它单元。

<a id="requirements-recheck-20261021"></a>
## 需求来源与消费者复核 — 补充分析计划（2026-10-21）

用户最新明确“进一步明确libam提供固定内存池的需求来源，以及用到公共heap的来源，再确定问题是不需要修复，还是需要实现”。本次在同一F0084分析范围内重新打开必要分析，不新建Milestone/业务Phase；原39/62及空heap证据保留，不把符号为空直接当作当前产品必须新增资源池的充分依据。

范围/验收：追溯AM TRM规约、本地导入历史与ICS-PA Navy教学目标；定向扫描Navy与AM消费者并逐项辨别实际provider、构建入口、公共Area heap与libc动态堆、同名算法heap。形成来源/消费者矩阵及当前处置结论，明确缺源/未承诺能力和未来实施触发条件。只读生产代码，复用既有基线验证；必要证据/链接/哈希、本批记录索引/唯一入口收尾后停止，结果待用户确认，不commit/push/进入其他组。无安装、无新增内存预算或生产实现授权。


### 来源核对：要求实现什么，不要求采用什么方式

| 来源 | 实际要求/证据 | 能推出的结论与边界 |
|---|---|---|
| [AM TRM规约](https://jyywiki.cn/AbstractMachine/AM_Spec.md) §2/§2.2 | heap是main前可用的连续可读写资源范围，大小/位置由实现确定 | 通用TRM包含heap接口；没有规定1MiB/4MiB、页对齐或BSS静态数组。固定范围描述不等于必须静态存储，也不等于普通malloc每次请求都要经过这个Area |
| 本地`navy-apps/README.md:122,137` | libam提供TRM/IOE；AM应用支持列出coremark/dhrystone/typing-game | 这是现有文档承诺，不宜由agent因为某些应用没读heap就自动收窄成“只需输出和计时” |
| [ICS-PA 2023 §3.5](https://nju-projectn.github.io/ics-pa-gitbook/ics2023/3.5.html) am-kernels部分 | 要求实现Navy上的TRM/IOE，给出上述三个直接运行目标 | 为TRM实现提供课程来源；没有给公开heap的容量、资源预算或存储策略，也没有逐项豁免heap |
| 同章microbench题及[用户指定站点对应章节](https://ysyx.oscc.cc/docs/ics-pa/3.5.html) | 另要求分析microbench在Navy运行出错；嵌套Nanos-lite也另作能力讨论 | 这些不是“完整microbench/内核必须运行”的现有验收。不能把扩展支持等同于本轮修复，也不能把预期运行错误直接解释成对heap缺失的正式豁免 |
| 本地初始导入`a20045fdcaaaf39b5717813b076ca0af2a9a480a` | trm.cpp已有`Area heap;`，putch/halt当时同样是空函数；之后c2021d5/5193335只补输出/结束链 | 空heap来自框架未填充部分，非最近修复引入；骨架保留空定义本身既不证明它已实现，也不证明它被允许永久缺失 |
| [上游master骨架](https://raw.githubusercontent.com/NJU-ProjectN/navy-apps/master/libs/libam/src/trm.cpp)与[README](https://raw.githubusercontent.com/NJU-ProjectN/navy-apps/master/README.md) | 当前读取内容与上述框架形态/描述相符 | 仅补充来源；不能把上游教学骨架当成功能已实现或验收豁免的证据。复现基线以本地完整commit为准 |

现代AM规约对heap边界不变及main参数的要求，与本项目已确认的heap.start共享游标和Navy POSIX main入口并不完全同构。本次用它核对“heap是TRM资源接口”的来源，不将现代规约全部行为或容量策略直接迁入本地，更不重开已确认游标修复。

### 公共heap实际来源与provider矩阵

本轮使用`rg --no-ignore`定向扫描Navy、am-kernels、nanos及klib的C/C++源码，排除build与独立newlib实现，核对115个heap标识符命中；其中15条为Area定义/heap.start/end使用或注释。其余主要为BusyBox压缩算法的堆数组、microbench的优先队列、普通文字注释，不能当作公共AM heap消费者。完整命令/结果与8组矩阵见local/requirements-commands、requirements-heap-scan、requirements-matrix。

| 来源/消费者 | 是否使用公共Area heap | 实际链接域与支持范围 |
|---|---|---|
| Navy coremark | 否，当前MEM_STATIC与static_memblk承担测试数据 | 确实链接libam并使用IOE计时；“使用libam”不代表“使用公共heap” |
| Navy dhrystone | 否，私有memory[1024]/myalloc | libc运行时若分配内存仍通过newlib/libos，不通过AM heap |
| Navy typing-game | 两个应用源无heap或malloc/calloc/realloc/free调用 | IOE游戏；不以底层库可能使用libc分配推定其消费公共Area |
| Navy普通malloc/newlib | 不使用公共Area | 现有malloc→MORECORE/_sbrk_r→libos_sbrk→SYS_brk，已支持按需获取进程动态内存；F0084不是“普通malloc不能分配” |
| microbench `bench.c:47,55,161,165` | 是，直接取范围并用bench_alloc管理 | 本地Navy wrapper只列三个目标，不含microbench；课程把它作为运行失败分析题。另有main(const char*)对Navy main(argc,argv,envp)的ABI差异，可能早于heap消费；本轮未运行，不能把全部失败归因heap |
| AM tests devscan/vm | 是，分别打印区间/提供页分配 | 普通AM测试目标不自动等于Navy libam已支持目标；vm还需要VME/CTE |
| AM klib malloc、普通nanos new_page/mm_brk | 是 | 常规内核/裸机路径由真正AM provider提供heap；Navy只复用klib声明，常规链接newlib/glibc，不链接这份klib malloc。不能拿内核heap需求要求Navy每个应用复制一份整机池 |
| nanos-lite-guest wrapper | 是，复用的内核mm会直接读heap | 这是明确存在的潜在libam heap消费者，但当前VME/provider/真实切换等不闭合；本项给heap也不会自动使它可运行，不扩展既有能力范围 |
| FCEUX/oslab0 | Unknown | 入口确实声明LIBS=libam，实际应用源码仍缺失；沿用用户已批准的缺源限制，不从本轮扫描断言它们不需要heap，也不下载补源 |

上表是源码/构建闭包判断，未用历史未配对ELF证明当前源码已执行。既有host空heap、真实RV64对象BSS观察继续有效；本轮无新增产品运行或动态功能验收。

### 处置结论：保留契约缺口，撤回静态池前提

**按当前README仍宣称支持TRM/IOE的契约，F0084不能直接判作“不需要修复”：公开heap仍是未补齐的TRM接口能力。需要处理的是这一接口承诺，不是为coremark或普通malloc新增静态池。** 本轮维持原问题ID/空区间事实和未实现状态，不计已修、不声称完整TRM已验收。

三个可见支持目标没有直接消费者，只证明当前这些应用不因空heap失败；不足以把公开接口从TRM中自动删除。另一方面，目前没有明确的产品需求要求新增固定容量arena、1MiB/4MiB或支持所有AM内核。**撤回原“建议静态1MiB、只需选择容量”的预设及旧提问**，不把容量当成唯一待决项。

后续有两条不同的契约处理路径：保持现有TRM承诺，则需设计有效的heap资源来源、所有权、容量/失败语义和初始化时机，再实施/验证；如果项目只要求现有有限应用兼容，可明确文档化TRM子集并声明公共heap暂不可用，此时才有“不新增生产heap实现”的范围依据。后者是收窄既有声明，必须明确确认，agent不以“当前未用到”自行代替该范围决定。本轮并未修改生产README或选择其中一条实施路径。

因此本轮完成的是需求复核与处置结论：**F0084保留待处理；固定静态池无既定需求，不实施。** 后续首先确认采用的TRM支持契约，不再发起1MiB/4MiB二选一；真正实施有效heap或明确范围后，再由实际消费者和内存预算确定方案。若将来要求microbench/完整AM heap客户端或嵌套内核支持，必须分别验证main ABI/额外AM能力与资源需求，不能把这些能力算入本次分析。

### 本轮验证与持久化边界

只执行只读源码/历史/构建入口核对与官方资料阅读，无生产代码、Make接口或正式README修改，无安装、动态回归或编译产物产生；原39/62分析及10项清理历史保持。补充证据与原证据分开保存于requirements-*，不改写原manifest/完成快照。本次重新完成后记录Supplemental/Reopened Analysis Completion，唯一TASK_QUEUE入口变为确认TRM需求结论/后续支持契约；不以旧容量提示作为阻塞。结果确认/本分析commit仍Pending，不自动提交/其他组/push/M阶段。

F0084需求补充终检：64项PASS；需求/消费者矩阵、旧静态容量入口撤回、历史分类/原快照和103+14+2/唯一入口一致，19份复核输入与8正式资产/newlib/HEAD保持；无新增生产修改、动态测试或编译产物。原39/62及清理/manifest不改写，本次requirements-*独立身份留档。补充复核Completed、结果/后续支持契约确认与本组commit Pending，本轮停止。

<a id="minimal-repair-proposal-20261021"></a>
### F0084最小修复意见与严格边界（2026-10-21；候选未实施）

用户要求提出修复意见，并明确不在本项解决范围外问题。建议仅在libam trm.cpp局部复用既有libc分配路径，在AM应用main前准备一次独占可读写区，完成必要对齐/容量检查后发布heap首尾；该块内存由libc登记为已分配，后续普通malloc不能重复分配它。保留原始分配地址/所有权，应用运行期间由AM侧管理区内分配；沿用现有CRT初始化数组，不增加用户初始化步骤、公开分配API或系统调用。当前入口已调用__libc_init_array，非native使用newlib/libos、native使用glibc；这只是源码可行性分析，初始化顺序/真实链接尚须实施时验证。

该候选将资源来源交给现有宿主分配机制，不采用大BSS数组，也不把整个end以上地址区间直接暴露给AM。它仍是一次性的AM资源准备，需要明确容量及失败语义，不能表述为“按每次heap使用自动增长”。建议失败时heap不发布半成品，固定诊断后终止当前应用；具体额度与此失败契约均未获实施批准，本轮不擅自选择。容量须由公开heap的有限资源约定确定，不根据未承诺的microbench/嵌套内核运行倒推预算。

直接验收只验证heap在规定时机有效/对齐/可写、分配失败行为、与同时发生的libc分配不重叠及内容保持，以及受影响的实际libam消费者；旧版空区间为反例。使用最小AM heap客户端，不为测试先修microbench的main ABI。修改预计限定trm.cpp及必要文档；若无法在这一边界内成立，先说明依赖，不扩改CRT/newlib/内核。

明确排除：microbench main参数适配、支持所有AM应用、VME/CTE/真实进程切换、嵌套nanos完整运行、内核页回收/exec资源泄漏、通用可增长堆/新allocator或mmap、NPC存储/硬件能力。发现它们影响验证时只记录限制，不混入F0084实现或声称本项已解决。F0113已修派发契约沿用。本轮仅提出方案、读取现有入口，生产diff空，无新动态验收、commit或新Completion事件。


<a id="linux-scope-closure-20261021"></a>
## 用户裁决：Linux目标不依赖，闭合而不实施（2026-10-21）

**F0084 Closed / 当前范围无需实现，用户已确认并授权提交本批分析。** 来源为用户最新明确指令：“这一问题暂不修复，如果启动linux不需要此功能就直接将其闭合，提交当前分析结果留档”。本次已核实其条件成立，直接执行闭合与归档提交，不再要求容量、分配策略或TRM支持范围二次裁决。

### Linux依赖核对

- [既定Linux计划](../../../../docs/LINUX_PLAN.md)的启动验收是OpenSBI→Linux→BusyBox/initramfs shell；计划中的NPC M5采用FSBL→OpenSBI FW_JUMP→Linux/initramfs，不依赖Navy libam。当前架构/计划核对不表示启动任何Linux阶段或新验收未来NPC启动。
- [实际boot Makefile](../../../../linux/boot/Makefile)分别调用外部Linux源码构建Image和OpenSBI构建固件，再打包Linux initramfs/DTB；没有将Navy/libam加入这些产物。
- [initramfs Makefile](../../../../linux/initramfs/Makefile)默认使用`$HOME/linux-m0/busybox-1.36.1/busybox`，boot profile记录其为静态musl/lp64版本；它与`navy-apps/apps/busybox`及Navy的newlib/libos/libam不是同一运行栈。
- 当前NEMU配置为native RV64，TARGET_AM关闭，NEMU本身使用native构建规则。[run.py](../../../../linux/boot/run.py)直接装入固件、Linux Image与DTB。Linux及Linux用户态有自身的内存管理路径，不消费Navy的`Area heap`对象。
- boot README中另外列出的AM/nanos旧软件回归不是Linux固件/内核/initramfs依赖；普通nanos使用真正的AM provider，也不能将它的heap与Navy libam混为一谈。

本轮Linux链44项只读核对全部通过，包含构建入口/输入与provider、当前配置及原19份输入/8正式资产/newlib/HEAD状态保持；证据为local/linux-closure.py与linux-closure-validation.json，相关源码身份均固定。复用既有M1完成记录作为历史背景，**没有重新启动Linux、重跑旧测试或扩写新的Linux/NPC验收结果**。

### 当前有效范围与保留限制

本次闭合依据是用户以Linux启动目标作出的范围裁决，**不等于修好了公开heap，也不等于宣称完整TRM heap已经可用**。`Area heap;`仍保持原样，普通Navy malloc仍走原newlib/libos/SYS_brk；无新增静态池、malloc-backed池、初始化器、系统调用或Make步骤。

原始Confirmed空区间事实、AM接口差异、microbench与wrapper能力限制及两缺源Unknown全部保留。当前不把完整AM heap兼容能力列为Linux启动需求或CRP待修；若以后明确新增直接使用公开heap的目标，再按其需求重新打开或另行规划，不自动恢复旧候选/容量建议，不为本项顺带解决VME/切换、main ABI、页回收、exec泄漏或NPC能力。

原119项现行对账为 **103已修 + 13项CRP待修 + 2项NPC能力扩展移交Linux + 1项无需实施而闭合（F0084）**。不删除原ID、不增加已修数、不回写旧快照/计数。records索引、逐项表、原问题补充与.agent的当前状态/唯一未来入口已同步；本次没有把F0084移交为新的Linux待办。

### 提交与持久化

用户同时授权提交当前分析结果。提交范围仅本报告/.gitignore、process索引与repair-status四个根路径；一次性测试/日志/JSON、需求证据、原问题清单/修复计划及.agent仍为本地忽略资料，沿既有约定保留，Git提交不等于备份它们。正文已保存旧空heap观察、需求来源/消费者矩阵、撤回候选、Linux不依赖的具体入口和本次闭合依据，不能仅依赖local证据才能理解结论。

本次复用原39/62/64及10项清理，不重复Completion或重跑无关功能；只补Linux依赖/范围闭合/提交核对与真实回执。实际commit由包含本节的Git提交及local/closure-submit-*定位。提交后停止，不push、不开始下一CRP单元或M阶段。

会话建议：建议开启新对话。本轮已累积多次需求辨析与方案撤回，当前处置和唯一恢复入口已完整落档，下一项切换到独立QEMU适配器背景更适合新会话。
