# CRP F0030/F0054 — 内存回收与页表所有权必要分析

## 整体计划（2026-10-21）

用户“提交后继续”确认并提交F0118补充91388f4后，执行TASK_QUEUE#crp-next本单元。沿既有CRP整体计划/workflow，不推进M2，不因分析另立业务Phase。

目标/范围：核NEMU AM protect/unprotect/map与pgalloc/pgfree、klib malloc/free与nanos new_page/mm_brk/exec的实际所有权及回收路径；区分AM教学物理arena、Navy newlib用户堆和Linux自身内存管理。结合讲义允许简化、公开AM生命周期规约与现行Linux目标，明确F0030/F0054契约问题及最小选项。生产未修改，不自行补通用free或递归释放共享内核页表。

阶段与交付：冻结必要源码与八正式资产/ONS差异→定向调用/规约核验→真实RV64原版最小见证（真实AM VME/klib与nanos分配入口，测试回调/独立微内核边界明确）→整理范围和最少裁决问题→验证身份/清理临时AM构建及产物、留报告/命令/退出码/SHA、更新records/.agent唯一入口。无需安装。

验收：证明free是否复用、分配失败是否改变游标、malloc/new_page是否共享且不重叠；证明unprotect是否调用回收器、用户私有根/中间表与共享内核分支关系，区分叶数据页/页表所有权。不把短时成功当作长期不耗尽，不把微内核冒称真实nanos进程退出/exec压力回归。生产未改，不重跑无关CPU/RT/音频/完整游戏。

停点：支持回收的范围/所有权/失败语义等真实取舍未冻结时分析留档后停下裁决，既有CQ仍未修；不把课程允许简化自动记为用户批准或Closed/Fixed，不移交Linux或新增其任务。不自动commit本分析/push/下一组/M2；软件安装/系统改动即停。

## 调用、所有权与现行需求

基线：根`91388f4`（完整commit与15源/八正式资产SHA见local/entry.json）。本单元没有生产源码修改，无修复diff；108已修+7CRP未修完+2能力移交+2无需实施闭合不变。F0030/F0054仍原ContractQuestion，不从新探针GOOD TRAP推定已解决。

| 层次 | 实际路径 / 生命周期边界 |
|---|---|
| AM klib物理块 | malloc按max_align_t对齐并推进可变heap.start，越界返回NULL/不推进；free为空。bf/galton等真实demo存在free调用，重复工作负载会持续耗尽arena，不能因free(NULL)安全就认定可复用 |
| nanos物理页/页表 | new_page与klib共用heap.start，页对齐后向前分配；mm_brk预留数据+页表事务只归还本次未用的尾部预算，不是通用free。free_page直接panic；init_mm将该函数交给VME，因此不能直接让unprotect递归调用后宣称nanos可回收 |
| AM地址空间 | protect分配私有根并复制kas根，内核分支的下级页表共享；map对缺失用户分支分配私有中间表。unprotect为空，既不遍历也不调用pgfree_usr/as清理；所有leaf的物理数据页是否归其回收也没有冻结 |
| 实际exec/退出 | context_uload验证镜像后直接protect(&pcb->as)覆盖旧根，再分配用户栈/ELF页；现nanos没有unprotect调用，sys_exit转exec nterm。因此只实现unprotect也不会回收实际exec旧地址空间；要接入须先界定旧页、内核共享分支、当前satp/引用与argv/envp源的寿命，不可加载前盲目释放 |
| Navy用户堆 | navy Make默认LIBS=libc/libos；malloc/free由newlib包装到_malloc_r/_free_r，分配器mallocr.h维护用户块，_sbrk经SYS_brk请求nanos扩映射。用户free可以在自身arena内管理空闲块，不能把klib空free当作所有Navy应用free都为空。这里只核源码/构建入口，没有动态验证任意newlib负载或向系统返还物理页 |
| Linux目标 | LINUX_PLAN目标是OpenSBI→Linux→initramfs shell，Linux自行管理其内存；M3/M4仍有AM VME/nanos虚存消费者验收，但未找到要求本轮为nanos补完整物理回收/任意长时exec的具体条款。这不消除有限物理内存耗尽风险，也不自动授权范围移交或关闭问题 |

将任意free实现为回退heap.start会覆盖随后分配的普通块/页/页表；将共享内核分支当用户私有表递归释放则会破坏其他地址空间。单独增加malloc空闲链表也不能自动回收由new_page分配的对象。若需要回收，至少须冻结：普通块与整页管理的所有权/元数据，user/kernel表区分，用户leaf是否归AM还是OS，活动地址空间/引用和exec替换的释放时点，耗尽/失败原子性及旧接口兼容。此为尚未获批能力边界，不将其作为普通实现细节偷偷引入。

## 讲义与AM规约对照

2026-10-21重新读取[ICS-PA4.3](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)：物理页MM可顺序分配且不要求回收。这支持当前nanos教学页分配范围，并不直接批准klib满足通用C free语义。[PA2.3](https://ysyx.oscc.cc/docs/ics-pa/2.3.html)把malloc/free列为klib职责，但本次未在该页找到明确准许free永远为空的条款；不把页分配简化扩写成所有分配器豁免。[PA3.3](https://ysyx.oscc.cc/docs/ics-pa/3.3.html)明确用户堆由libc管理、经_sbrk/brk调整，支撑上述层次区分。

[公开AM规约](https://jyywiki.cn/AbstractMachine/AM_Spec.html)将unprotect描述为销毁地址空间，并将pgalloc/pgfree作为可用页面分配/回收接口；该规约还把heap描述为不变区域，而当前klib/nanos共同推进heap.start。后者为既有教学分配实现约定，本轮不擅自迁移到不可变heap+私有游标或计入新修复。公开AM规约面向另一课程及平台基准，不能无条件替代本项目已沿用的PA子集。课程简化与公开生命周期契约的差异保留为CQ，用户尚未批准本项目完整回收契约。

页面访问时版本/内容作为本轮参考，不冒充用户当年讲义；local/references.json保存访问日期、链接和结论。没有下载软件、改环境或运行网页中的安装命令。

## 真实RV64原版必要见证

local/run.py在隔离build复制现有AM（不复制Git/旧build），以既有`make ARCH=riscv64-nemu git_commit= image`构建三种mainargs；probe额外链接**当前nanos mm.c原文件**，malloc/free/VME为真实AM/klib实现，不重写生产算法。使用现有正式NEMU解释器，未重建/覆盖默认引擎、磁盘或Navy程序。六条构建/运行均同步完成：三构建exit0；arena/VME运行GOOD TRAP exit0；free_page为明确预期的panic/BAD TRAP exit1。

| 模式 | 实测 / 证明范围 |
|---|---|
| a：共享物理arena | 在独立guest将heap.end收紧为起点+16KiB，以有限输入观察耗尽。malloc32得到0x8000a000；free后游标不变，下一malloc32为0x8000a020；真实new_page(1)页对齐返回0x8000b000，后续malloc16为0x8000c000，无重叠。超限malloc/new_page均NULL且不推进；再255次malloc32/free后返回NULL。7断言/11698指令；不修改生产heap配置，不是完整系统长时压力 |
| v：VME表生命周期 | 测试pgalloc回调调用真实new_page(1)并清零；pgfree计数桩用于观察AM是否调用。真实vme_init后四轮protect/map/unprotect，每轮私有根+两级表=3页，共12页；回收0，根保持非空。四根0x8004f000/0x80053000/0x80057000/0x8005b000，共享内核根项均0x20002c01；用户分支与其分离。28断言/4740707指令。数据页另由new_page供给，不混计私有页表；未实现回收也未测通用leaf所有权 |
| p：真实nanos回收入口 | 直接调用实际free_page，输出not implement yet，BAD TRAP/exit1；没有拿host SIGSEGV代替guest失败。此用例是缺实现见证，不是“回收测试通过” |

上述为M态独立微内核：没有运行用户进程、切换到新用户页表、实际exec/退出或完整nanos调度；设置satp/建立页表不等于已验收U态地址转换或完整OS生命周期。没有新增修复能力，不重跑CPU全集/RT/音频/游戏；既有消费者证据仍属历史。本次无构建夹具失败。完成标记删除、伪造非零退出两类假PASS由同一判据拒绝，不把无执行/无有效结果写成功。

## 方案与停点

| 选项 | 契约 / 后果 |
|---|---|
| 建议：联合延期并保留风险 | 当前可信/有限工作负载继续教学单调arena与页分配；F0030/F0054仍CQ未修，不称Fixed/Closed/ApprovedGap。重复分配/free、长期exec会累积消耗，实际需求明确再联合恢复 |
| 需要回收，先冻结完整方案 | 明确普通块/页分配器与所有权、用户私有表/共享内核表、leaf数据页/活动引用、exec释放顺序及失败/耗尽验收；先形成同一单元实施方案供裁决，不凭“继续”直接改heap游标或递归free |

已向用户提交上述最少选择；在答复前不自行选推荐项、不改生产。分析技术部分Completed，回收范围裁决Pending；分析文档未提交不人为增加裁决后同组续作门槛。新风险选择以最新Session及下方回执为准。

## 身份、清理与复现

15必要源码/八正式资产/ONS既有编码diff保持；根HEAD91388f4/index空，生产无diff。六同步进程已结束，删除前对隔离AM生产副本/对象/库/ELF/BIN/反汇编等188文件记录字节/SHA，共638743逻辑字节；0 tracked/正式资产删除。local/cleanup-plan和cleanup-receipt保存实际回执。保留最小probe.c/run.py、命令/退出码/日志/linked符号、身份/配置与验证manifest，不保留全源副本或可再生二进制。

旧源按local/entry.json完整根commit与源码SHA，沿现有正式NEMU身份重建；将最小配方放到records下新证据目录后执行`python3 "$H/run.py"`，避免覆盖原日志。没有修复patch。一次性夹具/原始证据/.agent仍本地忽略，Git提交不等于备份。

唯一后续入口TASK_QUEUE#crp-next；本轮停在真实回收范围裁决，不自动commit分析/push/下一组/M2。会话建议：可在当前对话继续；本单元证据规模有限，回收边界与原始行为已明确落档。


<a id="deferral-20261021"></a>
## 用户联合延期裁决与最终停点

用户在上述真实结果/所有权分析及二选项展示后明确选择**“联合延期并保留风险（推荐）”**。F0030/F0054因此均为原ContractQuestion/Low/未修/用户批准联合延期，不是Fixed、Closed、ApprovedGap或Linux能力移交。保留单调物理arena、unprotect不回收和free_page尚未实现；有限内存及重复exec的累积耗尽风险不因本次确认消失。将来有实际释放/重复生命周期需求时，联合恢复并冻结普通块/页、私有/共享页表、leaf与exec寿命、失败验收，不直接回退heap.start或递归free共享分支。

技术分析及延期决定留档Completed；108+7+2+2保持，生产未改，结果/延期已获本次明确确认，分析文档commit Pending。前F0118已确认实际91388f4；本轮“提交后继续”不额外授权提交新分析文档。唯一下一入口TASK_QUEUE#crp-next：本组文档提交后另有继续，才F0055 RTC能力声明/实际调用必要分析一个单元（Planned未Start），不自动改has_rtc、补墙钟、push或推进M2。建议可在当前对话继续，当前证据及延期恢复条件清楚；ignored证据/.agent仍需本地保管。

最终终检16项通过，17份保留证据manifest固定；原版行为不是修复验收。身份/八正式资产/原差异、119行/108已修、空暂存、预期清理与报告导航/唯一门槛一致；无新commit/push/下一组启动。


<a id="submit-20261021"></a>
## 分析文档确认与提交（2026-10-21）

用户“提交后继续”确认已报告分析/联合延期及限制，授权本批报告/.gitignore/process/repair-status四路径精确提交后执行F0055必要分析一个单元。提交前17保留证据、15源、八正式资产与ONS原差异均保持，复用既有测试/清理，不重跑、不重复完成快照；实际commit与mode/blob/树核对见local/submit-20261021及.agent回执。一次性夹具/原始证据/.agent保持本地忽略，commit不等于备份；无push。会话建议：可在当前对话继续；本组证据和下个能力分析范围明确。
