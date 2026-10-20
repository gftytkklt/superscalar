# CRP F0061 — exec参数容量与内核栈

## 计划与启动（2026-10-20）

用户“继续CRP修复”授权唯一入口一个单元，同时要求每次提交落档按上下文长度
及任务相关性提醒是否新对话。前63项已确认提交，root27b5bd8/干净、nested8101fad
内容/index干净及850既有mode差异保持，M2不变。复用CRP整体计划/工作流，不新立
业务Phase。会话建议规则在AGENTS稳定行为层固化，WORKFLOW_POLICY/CRP引用；
本次没有提交授权，规则与本组修复完成后统一报告，是否换对话不新增审批门槛。

目标/范围：只修context_uload参数计数/有界测长/32KiB预算及无界VLA。先验证总
字符串、argc/argv/NULL/envp/NULL表和16字节padding预算，再fs preflight/protect/
分配/改PCB；超限返回-E2BIG，经现有sys_execve失败返回链传播且旧进程可继续。
不改CRT/Make/日常update→run流程、ELF可信性或通用用户指针copyin、物理OOM策略。
原队列F0067为音频记录，不是exec失败证据；本轮必读改为实际sys_execve/_execve
和F0060启动布局。空向量和NULL向量按空参数处理，不额外引入ARG_MAX策略。

实现/验收：一个独立单元，移除argv_addr/envp_addr VLA，在新用户栈直接构造固定
布局的指针表，先完整复制参数再loader以保持源参数别名/exec旧映像约定。计数/
测长始终由STACK_SIZE预算限制，size_t域计算，不在int窄化后查错。保持已有F0060
字符串存放顺序、表顺序和16字节对齐。

1. 从27b5bd8复现40000字节参数被接受/越栈，以及大量参数触发VLA的旧失败见证。
   host直接使用生产loader，VME/非VME sanitizer：空/NULL、小参数、多参数和共享
   字符串/向量别名；16种余数、恰容量/越1、长env、未终止但可读长字符串与指针表，
   检查新布局/内容/哨兵及失败无protect/new_page/map/fs副作用、PCB/旧上下文保持；
   编译-Werror=vla及小内核栈压力，不把坏地址可访问性纳入本组。
2. 实际RV64用户exec：大参数/大量参数/env超限-E2BIG返回后旧程序继续读写/打印；
   合法共享字符串/环境、多参数与近容量成功exec后新CRT核对argc/envp及内容。
   最终组合按现有nanos make update→run三前台/hello，核实际新内核/ELF/盘身份。
   CPU/RT/REF不消费本组nanos参数逻辑，按调用闭包不重跑；非VME仅host覆盖。
3. 保存真实命令/退出码/源与产物身份、内嵌完整diff和语句解释并正反应用；8帧
   目视后清理本组隔离大产物，更新records/repair-status、状态和唯一下一入口。
   同轮核对新增会话规则/引用，不改写原审阅或旧完成快照。完成报告后停止，等待
   结果确认/commit，不push/安装/自动下一组/M2；真实策略冲突即停。

参考：2026-10-20读取[ICS-PA用户进程参数](https://ysyx.oscc.cc/docs/ics-pa/4.1.html#用户进程的参数)，
其简化argc/argv/envp布局允许字符串与指针表之间padding；容量与失败语义以本地
STACK_SIZE、已修16字节ABI和sys_execve/_execve实际链为准。

## 实施结果 — Completed，结果确认/commit Pending

生产仅loader.c，33增33删；全局会话提醒另改AGENTS/CRP workflow及本地忽略的
WORKFLOW_POLICY引用。累计64已修/55未修完，前63均确认提交，本组新结果未确认
未提交。原审阅P6/FINAL_FINDINGS及旧完成快照不改写，队列误指F0067已更正为
实际exec失败代码链和F0060/F0089相关证据。

| 验收 | 结果 / local证据 |
|---|---|
| 原版动态失败 | root27b5bd8实际loader，VME/非VME各40000字节参数和5000参数两个独立进程，原版仍返回成功/产生栈底以下布局，在预期拒绝断言处ARGS FAIL/exit1；四例无ASan/UBSan工具失败，不把编译失败当动态见证。unit/before-{vme,bare}-{large,many}.log |
| VLA编译契约 | 原版两模式-Werror=vla明确指出argv_addr/envp_addr变长数组；修复后独立完整生产loader用相同-Werror=vla和-Werror=frame-larger-than=1024均编译成功。host -O2 .su：context_uload VME192B、非VME144B静态帧，count_args8B；不是完整内核调用链/目标机器栈上界证明。frame-usage-vme/bare |
| host最终组合 | ASan/UBSan，VME/非VME各112场景（10751/9087断言），包含原F0060的PAL/NTERM/空向量与6计数组合×16长度余数、NULL向量、相同向量/字符串及子串别名；恰32768B布局、越一字节、长env、未终止但有可读预算的字符串/指针表、5000项、64KiB pthread栈内3638个空字符串。拒绝时无fs/protect/new_page/map调用、整个stub PCB/上下文及存储哨兵不变；成功初始sp/表/NUL/字符串原顺序与地址保持。LSan关闭，ASan/UBSan保持；FS零段头/AM类型为最小stub，不能代替实际ELF/guest |
| 实际RV64拒绝 | public execve经实际libos→SYS_execve→context_uload，7次：长argv、长env、多argv、多env、可读未终止字符串/向量、预算越1字节；均errno=E2BIG/-1，旧程序继续局部读写及打印。隔离诊断仅wrap context_uload：其返回前PCB字段、当前trap上下文、heap.start、原用户根/中间/叶表指纹保持（正常系统调用返回值随后仍由分派设置）。7条ARGS KERNEL KEEP PASS；kernel-args.c/guest-run |
| 实际RV64成功 | 三次真实exec：24KiB字符串/共享参数与环境进入新CRT（argc4/envp==environ、24575个v及共享值保持），NULL argv以argc0进入新CRT，再携单字符串32736B含NUL+32B表恰填32KiB进入极小汇编目标。后者不下压sp，验证sp=0x7fff8000、指针表/NUL及32735个k后输出ARGS EXACT PASS，GOOD/exit0。该满容量验收针对初始布局，不假称标准CRT/任意C函数可在零剩余调用栈运行。最终9,156,580指令，guest-result/两个实际ELF/反汇编 |
| 标准消费者 | 现有nanos make -j4 ARCH=riscv64-nemu git_commit= update exit0/28.182秒，再同参数run；108extent连续且逐字节匹配当前安装文件，PAL/NTerm/NSlider/hello新链接等于安装与盘。三前台54.054秒8帧已目视：PAL标题/飞鸟、NTerm qzx not found后prompt、幻灯片0→1→0 SHA恢复、返回PAL/Enter继续；10 SDL输入正确、hello34→149。自有组SIGTERM/make-15为观察结束，不是guest正常退出/实体音视频/长期验收 |
| 身份/归档/判据 | 167项preclean全PASS，4893最终源/配置与853构建产物身份；生产单文件diff正反应用精确，8种缺失/重复/非零/混BAD等判据故障正确拒绝。root27b5bd8/nested8101fad及两index保持，nested内容干净/原850mode不变；正式盘/header/kernel/config/NEMU/proc.c保持 |

初始host帧限制误作用到夹具main的局部数组，后改为独立生产loader编译；独立
编译初次ccache只读错误通过既有CCACHE_DISABLE=1解决，没有安装/系统修改。
收尾器初误写16条host命令，按实际明确标签核为14条；失败尝试不计验收，最终
完整判据通过。首次实际guest全过后，又增加24KiB新CRT实测并重跑最终诊断，
中间版本留intermediate，最终新源/盘身份独立固定；生产代码未在该补测改动。

## 每次提交落档的会话建议规则

用户本轮要求已固化到[AGENTS稳定规则](../../../../../../AGENTS.md)、
[WORKFLOW_POLICY引用](../../../../docs/WORKFLOW_POLICY.md)和
[CRP工作流](../workflow/README.md#batching)：每次提交落档都明确提醒可当前对话
继续或建议新对话，并依据对话累积、恢复可靠性和下一任务相关性说明；不虚构
精确上下文占比，不把建议增加为审批门槛。质量实际受影响时沿原§6保存入口并停。
该维护不推进业务Phase、不产生独立Completion，不自动授权提交。

本次会话评估：当前已完成本单元、资料可可靠恢复；下一ELF组仍相关，但本对话
已累积多组修复/证据，建议本组确认和提交落档后以新对话接续。唯一入口已落
TASK_QUEUE#crp-next，新对话可直接输入“继续CRP修复”，不要求另写启动Prompt。

## 影响、限制与再生

本组检查针对可读取的argv/envp和字符串，预算使计数/扫描有限，但不把任意坏
用户指针、未映射输入、并发修改/多核或全copyin能力作为已实现。后续重读长度
依赖当前串行内核中源参数在loader前保持有效；保留复制完成后再覆盖旧映像。
不改ELF格式/段可信性、物理OOM受控停止、回收/撤映射或F0076特殊_reent errno
策略；满容量只保证参数初始布局，不额外引入运行时栈保留/ARG_MAX策略。
CPU/RT/REF不消费本组nanos参数逻辑而未重跑；非VME仅host、未测NPC nanos/
其他ISA/长期/物理音视频，不宣称全ABI或内核输入安全问题全部解决。

本组root基线27b5bd8ff68d471caab0806d87b9d728ec34950c，nested保持
8101fad4376b7df0e3ec18db2db8cfa32746ad3a；Working tree contains uncommitted
CRP source/document changes，两index为空，无push/安装/下一组/M2 Start。
最终生产源码完整diff见下文；会话规则tracked差异另存local/workflow.patch，
WORKFLOW_POLICY为既有本地忽略文档，身份见workflow-policy-identity，不声称Git备份。

完成验证/目视/归档后清理9475文件656204844逻辑字节（约625.8MiB），零tracked
删除；范围仅本组隔离生产源码/构建/盘、全部中间与最终诊断树、可执行夹具及
截图/观察库，未触及正式资产。cleanup-plan/receipt保存删除前路径/字节/SHA和
删除后缺失解释；保留最小脚本/测试源/配置/命令/结果/身份/patch，不能再直接
查看旧截图或复用旧盘。ignored资料/.agent不由commit备份。

从根基线+repair.patch恢复本组生产实现，在全新输出目录用现有工具/资源身份
重建（无下载）。顺序如下；旧原版也从entry.root_head获取，不依赖未来HEAD：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/prepare-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/run-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/standard-path/run-standard.local nanos
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/visualize.py
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/archive.py
python3 npc/verif/records/process/code_correctness_review/crp-f0061/local/check.py
# 实际目视后cleanup.py，最后final-check.py核对保留资料/状态。
```

整组完成后停止等待结果确认/commit。后续唯一TASK_QUEUE#crp-next，不自动
开始未来ELF组/提交/push/M2；下次提交落档必须包含上述会话建议。

<a id="repair-diff"></a>
## 最终框架代码diff与实现说明

仓库：根ysyx-workbench；相对路径`nanos-lite/src/loader.c`。旧完整版本：
`27b5bd8ff68d471caab0806d87b9d728ec34950c`；新版本：`WORKTREE（2026-10-20，尚未提交）`。
新源SHA256：`fd44871302b04e88b8dc402c3233a6028411ef596ff318d929d423785f130578`。该diff为本批实际修复差异，
临时目录正向应用逐字节等于新源，反向应用精确恢复旧源；local/archive-validation。

`count_args`从argc及两个NULL共3个字开始计费，每个非NULL条目先预留一个指针，
再最多扫描当前余量内的字符；找不到NUL即-E2BIG，含NUL后才增加used与count。
used始终不超过STACK_SIZE，计数也由每条至少一个指针加一个NUL的费用限制；
全程size_t计算，避免先有符号溢出、int窄化或无界strlen再查错。NULL向量计为0项。
两组均通过后才fs_open/protect/分配和改PCB，因此超限失败不触及旧进程资源。

`initial_sp=ROUNDDOWN(ustack-used,16)`使用已验证预算；现有页对齐栈顶和
STACK_SIZE均为16倍数，padding后仍在栈内。table/argv_addr/envp_addr直接指向
新栈，去掉两份随参数个数增长的内核VLA。后续size_t长度仅重读已验证、在当前
串行调用中保持有效的字符串，按原顺序向栈顶下方复制并填写虚拟指针和NULL；
先全部复制，再调用loader覆盖旧映像，保留别名/原进程参数来源和F0060布局。
最终GPRx使用initial_sp；CRT与系统调用接口不变。通用坏用户地址/并发修改
检查仍未实现；满容量只保证初始布局，不额外承诺给任意C程序预留运行时调用栈。

```diff
diff --git a/nanos-lite/src/loader.c b/nanos-lite/src/loader.c
index ac82d334963e97c8bd7d04f120c901ed1b12b935..b86091d31d628421ce584fccd926933d02827e46 100755
--- a/nanos-lite/src/loader.c
+++ b/nanos-lite/src/loader.c
@@ -103,7 +103,28 @@ void naive_uload(PCB *pcb, const char *filename) {
   ((void(*)())entry) ();
 }
 
+// Charge every pointer and terminating string byte before changing the process.
+static int count_args(char *const vec[], size_t *count, size_t *used) {
+  *count = 0;
+  while (vec != NULL && vec[*count] != NULL) {
+    if (*used > STACK_SIZE - sizeof(uintptr_t)) return -E2BIG;
+    size_t available = STACK_SIZE - *used - sizeof(uintptr_t);
+    size_t len = 0;
+    while (len < available && vec[*count][len] != '\0') len++;
+    if (len == available) return -E2BIG;
+    *used += sizeof(uintptr_t) + len + 1;
+    (*count)++;
+  }
+  return 0;
+}
+
 int context_uload(PCB *pcb, const char *filename, char *const argv[], char *const envp[]) {
+  size_t argc, envc;
+  size_t used = 3 * sizeof(uintptr_t);  // argc and the two NULL pointers
+  if (count_args(argv, &argc, &used) < 0 ||
+      count_args(envp, &envc, &used) < 0) return -E2BIG;
+  // The page-aligned stack top and STACK_SIZE are multiples of 16.
+  // Rounding a validated used <= STACK_SIZE up to 16 still fits the stack.
   // Reject a missing executable before replacing the caller's address space
   // or context. fs_open() uses a fixed file table; the loader opens it again.
   int fd = fs_open(filename, 0, 0);
@@ -143,54 +164,33 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
 # define USTACK_TO_PA(v) ((void *)(v))
 #endif
 
-  // count argc/envc (read argv/envp BEFORE loader)
-  int argc = 0;
-  while (argv[argc] != NULL) argc ++;
-  int envc = 0;
-  while (envp[envc] != NULL) envc ++;
-
   // layout on user stack (grows downward from ustack), low -> high:
   //   argc, argv[], envp[], string area
+  uintptr_t initial_sp = ROUNDDOWN(ustack - used, 16);
+  uintptr_t *table = USTACK_TO_PA(initial_sp);
+  uintptr_t *argv_addr = table + 1;
+  uintptr_t *envp_addr = argv_addr + argc + 1;
+  table[0] = argc;
   uintptr_t sp = ustack;
 
-  // 1. string area: push argv strings then envp strings, RECORDING each
-  //    string's address as it is placed (stack grows down, so later pushes
-  //    land at lower addresses).
-  uintptr_t argv_addr[argc + 1];
-  for (int i = 0; i < argc; i ++) {
-    int len = strlen(argv[i]) + 1;
+  // Copy into the new user stack and fill its pointer tables directly.
+  // All source strings were bounded above and remain live until loader().
+  for (size_t i = 0; i < argc; i ++) {
+    size_t len = strlen(argv[i]) + 1;
     sp -= len;
     memcpy(USTACK_TO_PA(sp), argv[i], len);
     argv_addr[i] = sp;
   }
   argv_addr[argc] = 0;
 
-  uintptr_t envp_addr[envc + 1];
-  for (int e = 0; e < envc; e ++) {
-    int len = strlen(envp[e]) + 1;
+  for (size_t e = 0; e < envc; e ++) {
+    size_t len = strlen(envp[e]) + 1;
     sp -= len;
     memcpy(USTACK_TO_PA(sp), envp[e], len);
     envp_addr[e] = sp;
   }
   envp_addr[envc] = 0;
 
-  // Leave padding above the pointer tables so argc (and the initial sp)
-  // is 16-byte aligned without moving any of the strings.
-  size_t args_size = ((size_t)argc + (size_t)envc + 3) * sizeof(uintptr_t);
-  sp = ROUNDDOWN(sp - args_size, 16) + args_size;
-
-  // 2. envp[] pointer array (with NULL)
-  sp -= (envc + 1) * sizeof(uintptr_t);
-  memcpy(USTACK_TO_PA(sp), envp_addr, (envc + 1) * sizeof(uintptr_t));
-
-  // 3. argv[] pointer array (with NULL)
-  sp -= (argc + 1) * sizeof(uintptr_t);
-  memcpy(USTACK_TO_PA(sp), argv_addr, (argc + 1) * sizeof(uintptr_t));
-
-  // 4. argc
-  sp -= sizeof(uintptr_t);
-  *(uintptr_t *)USTACK_TO_PA(sp) = (uintptr_t)argc;
-
   // load the new program (may overwrite the calling process's static data)
   uintptr_t entry = loader(pcb, filename);
   assert(entry != (uintptr_t)-1); // preflight found this file in the fixed table
@@ -200,7 +200,7 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
   pcb->cp = cp;
 
   // GPRx points to argc; Navy _start sets sp from GPRx and passes it to call_main
-  cp->GPRx = sp;
+  cp->GPRx = initial_sp;
 
 #undef USTACK_TO_PA
   return 0;
```
