# CRP F0032 — AM NEMU VME根页初始化与分配失败保护

2026-10-20。用户“提交后继续”授权前F0070提交后执行本单元；前组实际6264781045bfa0381763c6fd8f00e5779420a67e。F0032沿TASK_QUEUE既有计划执行，不推进M2。

**当前结论：方案A已批准并实施，F0032功能修复Completed；结果确认/本组commit Pending。累计99完全已修/20未修完。** 下方必要分析、待决状态及反例为本单元历史，现行结果见“方案A实施验收”。

## 本单元计划与停点

范围：先核riscv/nemu/vme.c根页初始化、vme_init/protect/map分配结果和调用者/讲义契约，用当前源dirty/NULL定向观察区分缺陷与回调前置。没有真实待决时才最小实施并覆盖真实消费者；若失败契约未定，保存证据/可评审方案，停止依赖实施并最少裁决。禁止自行新增可恢复OOM接口、回滚/页回收/权限/NPC能力。

交付：本分析报告、local最小host配方/命令/日志/身份与清理回执、records索引/repair-status/.agent；无生产改动时不伪造修复diff/成功guest验收。分析结束或完成修复为停点，不提交新组/安装/push/下一单元。

## 当前契约与证据入口

- 本地am.h声明vme_init为bool，protect/map为void，回调只声明分配字节数参数；不声明必须返回零页、NULL还是终止、部分失败如何恢复。riscv/nemu/vme.c根分配后立刻map而无清零/NULL检查；protect在memcpy之前就发布ptr/area/pgsize，NULL会先发布无效地址；map中间表NULL只由klib assert拦截，NDEBUG取消检查。
- nanos当前pg_alloc已有清零及OOM诊断终止，不返回NULL；brk容量事务和先预留表页保持。因此正常nanos调用遮蔽本项，不宣称现有nanos启动发生NULL。F0070只消费vme_init已经返回的false，不能拦截AM返回之前的非法访问。
- am-tests VME(simple_pgalloc,simple_pgfree)在main CASE的vm_test之前执行；simple_pgalloc只是按size对齐并前移游标，无memset/容量检查。vm_test内部限制x86/native，但RV64即使最后返回Not supported，VME初始化仍发生；不把RV64现成vm_test当完整用户执行用例。
- 定向查找本项目AM/nanos/am-kernels/rt/Navy源（排除build/.git/第三方repo及tools）仅发现nanos init_mm、am-tests VME宏两个外部注册入口；rt/BSP与libam当前无该注册调用，AM各平台实现是定义不是消费端。本次不穷举外部项目或本地历史夹具。
- [讲义VME与nanos分页](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)（2026-10-20访问）要求nanos pg_alloc清零；它没有冻结AM对任意调用者的零页/分配失败恢复协议。此教学前置不能自动扩大为整个AM失败语义裁决。旧审阅入口：FINAL_FINDINGS F0032、P4 VME节与p4/vme-results（旧仅零页正常allocator观察）。

## 当前源定向观察（分析，不是修复验收）

源版本根仓`6264781045bfa0381763c6fd8f00e5779420a67e`，文件`abstract-machine/am/src/riscv/nemu/vme.c`，SHA256 `b9568db08f09f75c87003b8bd55011421870aed72bc464227c2e3d7c9c7c14db`。仅在host生成副本替换两处satp CSR表达式为mock_satp；本测试把四个内核映射范围缩成一个4KiB叶，保留原生产控制流/分配/复制/发布语句，回调提供对齐零页、脏根或指定次序NULL。无生产改动。

| 场景 | 实际观察（UBSan普通 / UBSan加NDEBUG） |
|---|---|
| 正常零页 | 两者exit0，init true、三张内核页表+protect根共4次分配，protect复制及area正确 |
| 脏根已有valid项 | 两者exit0，init true，但仅分配一次，并改写回调未分配的另一张有效leaf表；这是受控注入的旧问题见证，不是正确行为PASS。若AM清零根，应创建独立表而不修改外部表 |
| 根分配NULL | 两者SIGSEGV/-11，只打印ALLOC NULL at=1，未返回false；本访问未被UBSan先报告，不能将SIGSEGV写成受控panic |
| protect根NULL | 两者exit1，UBSan报告memcpy参数1是NULL；as->ptr/area/pgsize在复制之前发布是静态语句顺序事实，未冒称在UBSan中采到崩溃后状态 |
| map第一级中间页NULL | 普通：assert诊断/halt1，目标root[1]尚未发布；NDEBUG：memset(NULL)触发UBSan/exit1 |
| map第二级中间页NULL | 普通：assert诊断/halt1，但第一级root[1]已发布；NDEBUG：memset(NULL)触发UBSan/exit1。现源不具事务回滚 |

两个编译+十二实际执行共14条命令，全部符合各自预期观察；不把故意的非法访问或外部表修改算作功能正确。RLIMIT_CORE=0，未留下core。命令、环境覆盖、退出码见local/results.json，各场景精确日志保存；source-identity记录仅两CSR替换及范围缩小。host不是RV64硬件MMU。本次无生产修复，因此不重跑CPU/RT/nanos/guest，也没有新增真实消费者成功结论。

夹具初编译启用比生产更严格的-Wextra/-Werror触发既有signed/unsigned比较，并触发观测指针保存局部AddrSpace的编译诊断；改用生产相同-Wall/-Werror边界，并把观测AddrSpace设为static，保留initial-compile日志。初runner预期根NULL被UBSan拦截，但实际SIGSEGV；保留initial-null-init原结果，最终明确采用真实-11并单列限制，其他NULL边界仍要求具体UBSan/assert诊断，不凭任意非零当通过。

## 待裁决方案（尚未实施）

建议 **A：AM自清零根页，页表分配失败统一诊断终止**。

1. vme_init：根分配后先panic_on(NULL)，再memset整页零，然后执行既有map循环、最后set_satp/vme_enable；成功仍返回true。分配失败不返回一个看似可继续的状态，不改变bool API，已支持能力与不支持平台false仍保持各自实现。
2. protect：分配后先panic_on(NULL)，先复制内核根，再发布as->ptr/area/pgsize；失败停止时不把NULL根发布给调用者。
3. map：把现有assert(pg != NULL)换为不受NDEBUG影响的panic_on，随后原清零/写中间PTE/写leaf顺序保持。第二级失败前可能已有第一级表，本方案停止系统，不承诺回滚/回收这些已分配的页；不实现新失败返回接口。
4. 根页清零不再依赖外部调用者是否零填充；原nanos清零继续保持，不顺带优化/改变分配回调。回调必须有效、返回的非NULL页大小/对齐/所有权仍沿现行有效输入前提，本单元不扩成任意非法指针验证。

替代 **B：要求可恢复OOM**，则应先冻结protect/map的失败返回/发布/重试/所有权契约和部分页回滚策略；现有void接口与nanos free_page终止、AM unprotect空实现不能自行支持，属于另一项明确设计取舍。不是只让vme_init返回false就能宣称全链恢复。

真实未决项仅是是否采用A的“分配失败终止、无回滚/回收”契约；未询问日常实现细节。依据WORKFLOW_POLICY§3及TASK_QUEUE已定停点，未经裁决不修改生产。用户2026-10-20“提交后继续”授权必要分析，不自动裁决新失败语义。已发出A/B选择，当前等待答复；分析文档是否commit不新增本单元实施门槛，明确选择A后可继续本F0032范围，仍不自动commit/push。

## 留档与清理

33项分析/身份/正式资产检查通过；根HEAD仍6264781、index空，生产源码字节保持entry，五正式资产SHA保持。两次编译/全部子进程结束后，删除3个可再生文件（两执行文件与变换后的生产副本），95577逻辑B/106496分配B，0tracked/正式资产删除。最小probe.c/run.py、日志/结果/源码身份、validation-preclean与cleanup-plan/receipt保留，按当前根commit重建；无安装/下载/运行中动作。

F0032 **必要分析完成、生产修复未开始，等待失败策略裁决**；本报告无实际修复diff，不新增修复计数。前98已确认提交6264781，仍98完全已修/21未修完。Working tree contains uncommitted analysis/documentation changes；local/.agent不由commit备份。唯一Next为TASK_QUEUE#crp-next，不启动其他组/M2。可在当前对话继续：必要证据简洁且下一动作就是本项明确策略后的实施。

复现：`python3 npc/verif/records/process/code_correctness_review/crp-f0032/local/run.py`。清理后会重建host-build；重跑历史观察前须确认当前源身份等于上表，不使用未来新源冒充本次现源见证。local/close-analysis.py为当次清理配方，删除前先核对保留日志/状态；本地证据不自动纳入Git。

最终一致性终检：27项PASS、28份保留证据身份；生产源码/正式资产未改、3项清理缺失符合回执、119行98/21与唯一裁决入口一致。F0032仍待A/B，未实施/未提交，当前停止。

## 方案A批准与实施入口（2026-10-20）

用户对已发问题明确选择“采用最小诊断终止方案（推荐）”，批准上述A：AM根页自清零、三处页表分配失败诊断终止含NDEBUG、保护描述符复制后发布，保留API、无回滚/页回收。解除本项失败契约门槛，直接续作当前F0032实施/host与真实RV64定向/标准nanos回归/完整diff正反/身份清理，完成留档后停等结果确认与commit。分析文档未提交不构成新门槛；无commit/push/其他组/M2授权。前述待决/未改是批准前历史。

## F0032方案A实际修复diff

所属根仓ysyx-workbench，路径相对根。旧完整commit `6264781045bfa0381763c6fd8f00e5779420a67e`；新为2026-10-20未提交工作树。旧SHA256 `b9568db08f09f75c87003b8bd55011421870aed72bc464227c2e3d7c9c7c14db`；新SHA256 `e17021b71acc43f4d5fb1f0bd1b9fee71e39e068f8613b6196b788bbaef6a1f6`，mode100755保持。

```diff
diff --git a/abstract-machine/am/src/riscv/nemu/vme.c b/abstract-machine/am/src/riscv/nemu/vme.c
index ba9f8661163723cb08225b4683328524e6252670..bcf8b68265a1a40dba899d346b952716cdf9f798 100755
--- a/abstract-machine/am/src/riscv/nemu/vme.c
+++ b/abstract-machine/am/src/riscv/nemu/vme.c
@@ -29,6 +29,8 @@ bool vme_init(void* (*pgalloc_f)(int), void (*pgfree_f)(void*)) {
   pgfree_usr = pgfree_f;
 
   kas.ptr = pgalloc_f(PGSIZE);
+  panic_on(kas.ptr == NULL, "Failed to allocate kernel page table");
+  memset(kas.ptr, 0, PGSIZE);
 
   int i;
   for (i = 0; i < LENGTH(segments); i ++) {
@@ -46,11 +48,12 @@ bool vme_init(void* (*pgalloc_f)(int), void (*pgfree_f)(void*)) {
 
 void protect(AddrSpace *as) {
   PTE *updir = (PTE*)(pgalloc_usr(PGSIZE));
+  panic_on(updir == NULL, "Failed to allocate user page table");
+  // Copy the kernel mappings before publishing the new address space.
+  memcpy(updir, kas.ptr, PGSIZE);
   as->ptr = updir;
   as->area = USER_SPACE;
   as->pgsize = PGSIZE;
-  // map kernel space
-  memcpy(updir, kas.ptr, PGSIZE);
 }
 
 void unprotect(AddrSpace *as) {
@@ -125,7 +128,7 @@ void map(AddrSpace *as, void *va, void *pa, int prot) {
   for (int i = 1; i < 3; i ++) {
     if (!(pt[i - 1][vpn[i - 1]] & PTE_V)) {
       PTE *pg = (PTE *)pgalloc_usr(PGSIZE);
-      assert(pg != NULL);
+      panic_on(pg == NULL, "Failed to allocate intermediate page table");
       memset(pg, 0, PGSIZE);
       // store the next-level page table's physical page number in Sv39 PPN (bits 53:10)
       pt[i - 1][vpn[i - 1]] = (((uintptr_t)pg >> 12) << 10) | PTE_V;
```

根分配后先panic_on(NULL)再memset 4096B，map不再读回调遗留的valid项；失败不触及satp/vme_enable。protect先检查updir，再复制整根，最后才按原值发布ptr/area/pgsize，失败时调用者旧描述符保持。map原assert替换为panic_on，清零和中间表/leaf发布顺序不改，NDEBUG不能移除检查。页表仍可能在后级失败前已发布前级表；按批准A诊断终止，无回滚/页回收承诺。现有权限/页型/接口/地址域/回调/正常返回值不变。完整patch正向逐字节得到最终源、反向逐字节恢复旧commit，mode亦保持；local/implementation/archive-validation保存。

## 方案A实施验收（2026-10-20）

A已按用户明确选择实施，生产仅根仓AM `riscv/nemu/vme.c` 6增3删，接口/mode保持；本节为当前有效结论，前述待决/未改/未修是批准前历史。功能修复Completed，结果确认/本组commit Pending。累计99完全已修/20未修完，前98已确认提交6264781；不推进M2。

| 验证 | 本次结果与范围 |
|---|---|
| host最终源码 | 普通、ASan+UBSan、NDEBUG加san三配置，各zero/dirty/root/init两级/protect/map两级8场景，24运行全PASS、27编译/运行命令exit0。只替换两CSR表达式，host映射段缩小为一页；脏回调同时让中间页返回非零字节，原map清零仍正常。旧分析12观察保持，不覆盖旧日志。 |
| 失败状态 | 根/初始化两级失败精确诊断、vme_enable和satp均未启用；protect NULL时整个旧AddrSpace逐字节保持；用户map第一级失败未发布、第二级失败允许已发布第一级，并诊断停止。每例检查code1/指定诊断/准确第几次分配/状态，不以任意失败当通过；NDEBUG同判据。 |
| 真实RV64目标 | 实际完整AM vme.c逐字节包含到目标编译单元，无CSR/映射范围替换；完整NEMU内核映射和实际satp访问。旧源正常zero GOOD、dirty按新安全判据精确BAD；最终及NDEBUG各8场景GOOD（16），共37实际引擎构建/目标build/run命令符合预期。zero/dirty验证外表未改、根闲置slot零、protect复制、实际页表lookup与ucontext字段。正常用户态装载/陷入另由标准nanos证明。 |
| 真实负例判据 | 测试用linker --wrap=halt/putch收集真实panic字符，确认code1/诊断/分配计数/状态后才将该预期终止映射为测试GOOD；生产halt行为没改。若诊断或状态不符为BAD；不冒称真实生产故障后继续执行。旧dirty同一安全断言FAIL/BAD被拒绝。 |
| 现有AM调用者 | 未改的am-tests mainargs=p实际build/run exit0/GOOD，完成CTE与VME(simple_pgalloc)初始化后，按原vm_test架构限制输出Not supported architecture；仅证明初始化调用者兼容，不声称RV64执行该x86测试代码。实际am归档vme.o与其构建对象逐字节相同。 |
| 标准nanos消费者 | 隔离现有update exit0（26.032s）→run（53.449s后自有组SIGTERM，make -15非guest正常退出）。三前台8帧实际查看，PAL初始/返回/Enter标题持续变化，nterm输入qzx后command not found并返回prompt，slides0→1→0且回0 SHA相同；十个SDL键事件，hello38→173逐阶段递增。108extent/安装字节、四应用链接ELF及padding核对通过。 |
| 最终身份与归档 | 194preclean全部通过，9348份输入/产物身份保存；实际target/标准相同本轮源码构建引擎SHA256 `27026bca185a8700b232587680bdb95e5034a163678d38a08fb46483dd3894df`，最终target/NDEBUG/标准AM源同SHA。完整正文diff正反逐字节及Git executable mode100755通过，五正式配置/引擎/盘/header/内核bin保持entry SHA，根HEAD6264781/index空。 |

夹具修正仅在local：初编译把get_satp整数返回与指针比较触发-Werror，改用0/uintptr_t比较后所有host/guest再验；原编译失败日志保留initial-type。归档初验把临时FS权限精确等于755当门槛，git apply生成的临时文件权限为775（字节正确），改核Git实际只表达的executable mode100755，再完成正反字节/执行位核验；未改Git配置或生产权限。标准运行后现有AM消费者重建了不同mainargs的trm.o，但未改VME源/成员；archive-member-identity只明确核VME对象，不冒称整个am归档在各次mainargs后完全相同。

影响/未测：仅RISC-V NEMU VME实现改动；CPU-tests/RT不调用本次修改的vme_init/protect/map路径，CTE使用的地址空间辅助语句未改，不重复其全量运行。Navy源码/打包逻辑未改，仍按标准入口更新/运行覆盖实际nanos消费者。未扩AM权限/回收、NPC VME、32位/其他平台/完整Linux/长期/实体音视频能力；无重复初始化/并发/任意非法回调指针或不对齐页容错。第二级失败可已发布中间表，按批准A终止，无恢复或回滚承诺。额外根清零不增加页数，nanos分配/预算与brk预留算法没改，不重复F0089容量矩阵。

## 方案A复现入口

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0032/local/implementation/host.py
python3 npc/verif/records/process/code_correctness_review/crp-f0032/local/implementation/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0032/local/implementation/real.py
python3 npc/verif/records/process/code_correctness_review/crp-f0032/local/implementation/standard-path/run-standard.py nanos
python3 npc/verif/records/process/code_correctness_review/crp-f0032/local/implementation/am-consumer.py
```

上述依本机现有源码/资源，无下载/安装；旧源由6264781045bfa0381763c6fd8f00e5779420a67e读取，新源应固定为本报告SHA/patch。prepare拒绝覆盖work；恢复先核现状，不从头覆写进行中夹具。清理后模型/截图需重建，其hash只标记当时身份。实际命令/退出/结果见implementation/host-results、real-results、am-consumer-results及standard-path JSON/log；archive/check为当次归档核验配方，不能在以后源码上无辨别覆写历史。

本组一次性夹具不入库，必要生产源码、报告/局部ignore与records索引随未来授权提交；local/.agent本地保管，commit不等于备份。当前无commit/push/下一单元/M2授权；完成统一清理与状态收尾后停等结果确认/commit。

## 方案A最终清理与停点

194preclean/9348身份、完整diff正反及八帧目视完成后，所有测试子进程已结束；删除9401文件/链接，361741235逻辑B/389398528分配B，0tracked/正式资产删除。范围仅local/implementation隔离构建/源副本/镜像/对象/截图，保留最小测试配方/命令/实际日志/配置/身份/patch与cleanup-plan/receipt。原分析3文件清理回执独立保留，不改写；旧模型/图片现在须重建，hash仅作当时身份，不声称仍可直接复用。

F0032 Completed，结果确认/commit Pending；Working tree contains uncommitted F0032 code/documentation changes，根HEAD6264781/index空，无push/安装/运行中任务。99已修20未修完；唯一后续TASK_QUEUE#crp-next，未来F0047未Start。本轮停止，不自动提交/其他组/M2。可在当前对话继续：本组证据和授权清楚，恢复入口已保存；下一项将转RT时钟接线，可沿现有入口接续。

方案A最终终检补充：59项PASS、102份实施保留证据身份，原分析28身份逐一保持；完整生产patch/五正式资产/9401预期清理/119行99与20及唯一下一入口一致。无新增动态测试或commit，F0032 Completed、结果确认/commit Pending，当前停止。

## 用户确认与提交收尾（2026-10-20）

用户“提交后继续”确认本组已报告范围与限制，授权精确提交后执行TASK_QUEUE唯一入口F0047一个单元。提交前102份实施/28份原分析证据身份、完整patch/正式资产与59项终检复核一致；复用动态验收，不重复Completion。实际commit/路径/blob核验见local/implementation/submit-receipt及.agent；无push。可在当前对话继续：入口完整，下一单元范围与停点清楚。

实际提交回执补充（2026-10-20）：根`30bbde81dea31297365b3e5fa8cccba0c1e9004f`，六路径/blob与完整patch精确，102实施/28分析身份及59终检复用；提交后root/index干净。用户“提交后继续”确认此前报告范围并授权F0047一个单元，原Pending为历史。local/implementation/submit-staged与submit-receipt保留；ignored资产未备份，无push。
