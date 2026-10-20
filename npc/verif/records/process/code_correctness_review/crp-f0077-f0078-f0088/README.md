# CRP F0077/F0078/F0088 — Navy syscall ABI 边界

## 本轮计划（2026-10-20）

用户“提交后继续”授权前组提交后一个既有单元。F0079/F0080已确认提交nested
5d9ffdb/root7a8150e，内容/blob及根干净、nested原mode差异保持均已核对；不推进M2。

范围/目标：F0077只在newlib内部编译启用既有_COMPILING_NEWLIB原型；F0078只为
libos底层asm补memory clobber，保持a0输入/输出关系、原ISA寄存器及弱AM hook；
F0088仅按本地flags决定是否读取可选mode，其他默认0，保留当前mode_t整数提升。
不增加Make选项/目标/日常步骤，不改OS errno/文件创建能力或增加CPU fence。

交付与顺序：
1. 复用P7 width/visibility背景；原newlib低层调用按implicit声明为error编译反例，
   host及RV64检查大于INT_MAX/UINT_MAX和-1的返回、参数及独立errno。核新libc实际
   内部宏与低层声明、实际构建，不能用宿主截断推定当前RV64必然截断。
2. asm正常/弱hook/非hook与O2/O3/LTO可用路径，验证read/time输出和write输入，
   保存编译器约束及优化产物证据；旧版不能复现误编译时如实保留Robustness界限。
   open二参只读/只写、三参创建/权限提升、默认mode与返回/errno透传；真实OS忽略
   mode时用最小捕获层区分参数，不把它冒作实际文件创建支持。
3. 实际重建newlib/libos和PAL/NTerm/NSlider/hello，真实用户IO/时间/stdio/分配回归
   与三前台/hello。复用前组可靠隔离runner/输入，新增判据做失败拒绝，不另造框架。
4. 保存命令/退出码/源输入/链接身份及patch，目视后清理本组可再生产物，更新records
   索引/台账/既有计划/.agent及唯一未来入口，整组完成后停止，等结果确认/commit。

验收：三项分别有依据/定向证据及最终组合真实消费端验证，host/stub与真实OS分开；
CPU/RT/REF闭包未受Navy影响不重跑，NPC nanos/其他ISA/全配置/长期/实体音视频未测
单列。无安装；真实策略/接口冲突先裁决，不自动提交新组/push/下一组/M2。

参考：[GNU Extended Asm](https://gcc.gnu.org/onlinedocs/gcc/Extended-Asm.html)
（2026-10-20读取）说明memory描述非显式操作数内存访问/编译器屏障，不是硬件fence；
newlib原型/可选mode以本地include及实际RV64 ABI为准，Navy分层沿用既有讲义阅读。

## 实施结果 — 三项Completed，结果确认/commit Pending

生产仅root的libos/src/syscall.c（1增1删）、nested newlib的Makefile/sysopen.c
（16增7删）。F0077内部编译启用_COMPILING_NEWLIB，使用本地既有_read/_write/
_lseek声明，并使既有对象依赖本地Makefile，保证宏变化自动重编译；F0078仅增加asm memory clobber，未动寄存器/返回/弱hook；F0088只有
O_CREAT或头文件已定义的完整O_TMPFILE组合才读mode，否则0。当前RV64 mode_t是
uint32_t，按该类型提取；普通正数int权限字面量在两类型可表示范围内符合va_arg
规则，高位mode_t也保留原32位模式，经现有int _open_r接口透传。未增加创建能力。

累计57已修/62未修完，前54项均已确认提交，本组三项结果确认/commit Pending。

| 项目 | 结果 / local证据 |
|---|---|
| F0077原反例 | 原Makefile无内部宏，readr/writer/lseekr在host与RV64各3个生产源按implicit声明为error编译均失败，最终日志确为对应_read/_write/_lseek缺失声明。host原LP64在期望2147483651时三路返回-2147483645，非工具失败见证；unit-results及before日志 |
| F0077修复 | 相同6条严格编译通过；host6值×read/write/lseek=18次，覆盖0、INT_MAX以上、UINT_MAX以上、40位、LONG_MAX、-1，size_t大count/负64位offset和独立reent错误保持通过。实际RV64 newlib低层wrap入口同18宽返回/参数检查通过，普通真实IO另测；大返回是受控低层注入，不冒作巨量OS IO。最终从空build重建的新libc无这三类原型告警，其他既有库告警仍保留 |
| F0078编译证据 | 原/新-O2/-O3共4次生产源编译，GIMPLE中每版分别12/13个内联ecall站点；旧无memory，新全部有memory。最小IR行保存在asm-results，完整可再生汇编/tree输出已清理。站点不是25个独立测试；仅编译器约束变化，不引入硬件fence |
| F0078真实路径 | 旧版含原libos的O3/LTO/no-hook memory payload正常通过，仍未复现旧误编译/当前RV64截断。新版常规O2独立libos、同TU O3/LTO、同TU O3/LTO+强弱hook三payload均PASS/GOOD；实际read更新8字节、write消费即时输入，gettimeofday更新哨兵内结构，3轮正常IO/时间与hook调度通过。hook只在诊断guest中转发真实ecall，生产弱hook契约不改 |
| F0088 host | genuine二参调用的assembly尾调用先污染缺省mode寄存器，原-O0/-O2都错误转发0x55667788、exit2；新版两优化级别各6次正常open调用，含二参/不需mode的多余实参/目录flags、O_CREAT普通int权限与mode_t高位、失败透传；可选O_TMPFILE组合的host合成宏分支各7次。新共26次mode调用通过UBSan。合成分支不代表CYGWIN/临时文件实际支持 |
| F0088真实路径 | 同RV64用户payload经实际open connector→_open_r捕获层→原内核。旧首个二参open成功却传脏mode，在step2精确失败/BAD/exit1；新缺省0、创建flags的0644/高位模式、非创建多余参数忽略及缺文件返回均通过。内核仍忽略flags/mode，不宣称新建文件测试；观察层只检查接口实参 |
| 最终实际组合 | 5诊断ELF（旧open/旧memory/新O2/新inline/新hook）+PAL/NTerm/NSlider/hello四个新重建ELF，9项均与实际盘extent逐字节一致。最终16个构建/6个NEMU run期望均满足，含旧open失败/旧memory成功/三新guest成功/FG1亿指令后q成功。正式盘、原应用/默认kernel/native/config和NDL/SDL等身份保持 |
| 三前台/hello | 52.87秒8观察点，PAL标题/飞鸟、nterm qzx command not found后prompt、slider0→1→0且帧SHA恢复，F1返回PAL/Enter继续动画，hello35→154，实际10条SDL队列输入顺序正确。按RGB目视全部帧，原返回PAL蓝边保持；自有组SIGTERM/exit0非guest正常完成或长期/实体音视频声明 |
| 身份/判据 | 42项preclean通过，2162份消费者源/头/Makefile/链接脚本、1497对象/库/镜像身份保留。真实用户3轮IO后夹具16B为CDEFGHIJ89abcdef，除此16B外整盘SHA保持；8类缺标记/非零/错盘/混BAD/旧版无关早期失败均拒绝。preclean/checker-negatives/身份清单 |

本组不宣称全newlib无warning。当前仍有非本项的sched/execvpe、stat64、长双精度/
终端等声明或格式warning，见warning-scope及实际构建日志；仅目标正常_read/_write/
_lseek缺失声明闭合。也不从这些测试推定完整POSIX、所有低层接口/errno/F0076已修。

夹具更正：首次严格编译被ccache只读缓存拦住，不能作原问题见证；仅对夹具进程
设CCACHE_DISABLE=1后重跑，最终原始6日志均定位精确声明错误。初始LTO用Navy
直接ld仅附plugin，触发lto_wrapper_argv断言；诊断LTO目标改用已安装GCC driver
提供wrapper参数，未安装软件/更改系统或生产Make入口。原版full-library日志在
增量重试时覆盖，不能从该增量日志推断原型告警有无；原缺陷证据取独立严格编译。
初期检查器错误要求增量旧日志含告警，已改按真实证据核对。所有未通过夹具尝试
与限制在fixture-corrections/initial JSON和日志保留，没有计入最终PASS。

## 仓库归属、限制与恢复

root基线`7a8150e51105eae3ebc3f04f992ec48d336c3370`；
nested基线`5d9ffdb869f36282452a8f48a4655f53fb1745d5`。root本组libos单行及根报告/索引/工作流路径说明未提交；nested
本组仅Makefile/sysopen.c未提交，原850执行位差异保持，两个index未动，无push。
未来提交应分别归属精确内容，nested继续排除mode噪声；根不force-add整个libc。
本组没有新的架构取舍，不改Make选项/目标/日常必经步骤、用户创建/errno协议。

CPU-tests/RT/REF不消费Navy newlib/libos，按闭包未重跑；未测NPC nanos、其他ISA/
所有libc配置、真实CYGWIN O_TMPFILE、全部应用、长期/实体音视频。旧F0078在本次
优化器下运行正确不代表约束可省，修复以GCC memory契约、编译IR与实际正常路径
为依据；旧原型的host截断不外推成当前RV64已截断。

再生使用root与nested上述Git版本加local/root-repair.patch、nested-repair.patch，
正式Navy盘/header来源与SHA见entry-identity。prepare隔离两套Navy库，旧宏/connector/
libos从两个基线Git还原，新库及四正常消费者从空build重编译；GCC driver仅供LTO
诊断程序。正常应用仍走原Navy Make。输入/源码/工具/构建/产物身份和命令/退出码
保存于entry、tools、unit/asm/builds/fixtures/appended-files/runs/nanos结果。

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/asm.py
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/prepare.py
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/run.py
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/nanos-run.local nanos
```

从新清理目录再生，观察输出目录须为空或换名。visualize生成RGB接触图；目视/身份
核对后才清理。已清理16789文件561597430逻辑字节（约535.6MiB）隔离源码/构建/镜像/截图，零tracked删除；四份cleanup计划/回执说明旧身份路径缺失。保留最小IR、补丁、夹具、配置/命令/日志/结果。
local/.agent继续忽略，commit不等于
其备份。整组到此停止，待结果确认/commit；未来只沿TASK_QUEUE#crp-next，不自动
提交新组/push/下一组/M2。


## 用户标准路径补验（2026-10-20，已完成）

用户在本组执行中明确：修改Navy后按`make ARCH=XXX update`，再`make ARCH=XXX run`
更新/运行。本组补充按既有入口的隔离全链验收；不改日常命令，不把定向追加ELF
夹具等同于这个打包入口。另已确认update仍依赖原Make增量判断，因此libc Makefile
增加`$(OBJS): Makefile`保证宏变化自动重编译旧对象；不增加公共选项/目标或clean
步骤。独立验证宏变更单独不足以失效旧对象、补依赖后3旧对象重编译/659对象归档
通过，7项补充核对与660链接身份/841源身份保存。C/头不变，前述功能验收复用。


在完整隔离副本执行既有`nanos-lite`目录`make -j4 ARCH=riscv64-nemu git_commit= update`
exit0/27.732秒，再执行同参数`run`，没有冻结NEMU目标或自定义打包。update实际
生成108条文件/148505088字节盘，108 extent逐字节等于fsimg，四个新链接应用等于
安装文件及盘对应extent；231项标准路径核对通过，7639份更新前输入、4869份最终
源/头/Makefile及1091链接产物身份保留。最终实际盘大小以production-artifact-identity
为准。54.05秒8帧，SDL队列10按键/三前台正常，hello35→159、slide0→1→0 SHA恢复，
RGB全部目视。自有进程组SIGTERM使make -15，属于观察结束，不是guest正常退出。
NEMU按原disk.c和隔离NAVY_HOME读取盘，guest报告512字节块/290049块；该配置关闭
NEMU日志，不能要求stdout/空nemu-log里出现盘路径。核对器据实际source/env/块数及
kernel路径验收，不伪造路径日志。正式应用/默认kernel/盘与配置身份保持（本组
有意修改Makefile的最终SHA单列final-source-delta）。

补验夹具首次排除build目录时漏掉既有fixdep工具，make run构建阶段exit2、无guest；
只将本机已有fixdep按SHA复制入隔离副本再重试，未安装或修改系统。初始失败日志
保留在standard-path/nanos，成功在nanos-retry；不把首次失败列作产品回归或PASS。
补充检查器先错误要求stdout含盘路径，实际日志关闭；已按上述真实证据更正，
无额外guest/生产修改。7项增量核对、231标准路径核对不冒作独立功能场景数量。

补验再生（在本组最终源上，输出目录须全新；主机现有资源/工具，不下载/安装）：
```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/incremental.py
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/standard-path/run-standard.local nanos-retry
python3 npc/verif/records/process/code_correctness_review/crp-f0077-f0078-f0088/local/check-runtime.py
```
prepare-runtime记录源码/已有fixdep身份、执行update并编译最小SDL观察库；run走真实
make run。最后目视/核对后cleanup-standard。工作流README保留这一既有更新/运行入口。

最终收尾33项核对PASS，165项最终manifest绑定报告/源/流程/状态及保留证据。核对119稳定ID、57已修、双HEAD/空index、精确root/nested内容范围、850既有执行位差异、正式资产保护、四份清理回执与唯一未来入口。检查器初按Completed文字统计漏掉早期“已提交”行，已按台账状态列“已修 /”计算，不更改历史行。


<a id="submit-20261020"></a>
## 用户确认、提交与新对话接续（2026-10-20）

用户最新“如果上下文长度过长，提交后提示我开启新对话继续，否则直接继续”确认
本组已报告范围并授权提交。当前对话已有多轮修复及大量构建/运行证据，选择完成
本组提交和接续落档后停在干净边界，由新对话沿TASK_QUEUE唯一入口继续；不启动
F0081/F0082，不push。复用33项最终核对及所有产品验收，不无故重跑；提交前165项
manifest身份全量无漂移。原Completion/manifest保持历史，不重复完成快照。

nested实际`71fac82b295316c80acf5bd3dc825ff2ff202a46`，仅Makefile/sysopen.c两文件16增7删，暂存/实际blob及原100644
模式一致，内容/index干净、既有850执行位差异保持。root本次只提交libos单行、
本组最小README/.gitignore、records索引/台账和既有update→run流程说明；根实际SHA、
最终路径/blob及干净检查写local/submit-receipt.json，不把根提交当嵌套源码提交。
一次性测试/原始证据/.agent继续本地忽略，提交不代表这些资料已有备份。

57项结果已确认，剩余62未修完；未测/原warning/旧memory未复现误编译等限制保持。
新对话可输入“继续CRP修复”，按CURRENT_STATE→TASK_QUEUE#crp-next恢复，读取该入口
范围/资料/验收，执行一个单元；不要重跑已验收的本组、不要切换M2。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0077/F0088 — navy-apps/libs/libc

此块属于独立 libc 仓库；同组 libos 修改在下一块列出。

- 差异路径相对于仓库 `navy-apps/libs/libc`；旧版本：`5d9ffdb869f36282452a8f48a4655f53fb1745d5`；新版本：`71fac82b295316c80acf5bd3dc825ff2ff202a46`。

#### `Makefile`

F0077：`-D_COMPILING_NEWLIB` 使库自身编译时能看到 newlib 内部低层接口原型，避免 `_read/_write/_lseek` 被当作隐式 int 返回。`$(OBJS): Makefile` 把宏所在 Makefile 加入对象依赖，选项改动后沿原 update 流程重编旧对象，不需要新增 clean 步骤。只保证原报告涉及的原型告警闭合，并不宣称整个 newlib 无 warning。

```diff
diff --git a/Makefile b/Makefile
index 5b9ca05093a55b8d491976834b1f3731875b9261..0acf0d25e187762b1292c677caa18a7f77d55746 100644
--- a/Makefile
+++ b/Makefile
@@ -1,5 +1,7 @@
 NAME = libc
-CFLAGS = -DNO_FLOATING_POINT -DHAVE_INITFINI_ARRAY
+CFLAGS = -DNO_FLOATING_POINT -DHAVE_INITFINI_ARRAY -D_COMPILING_NEWLIB
 CFLAGS += -U_FORTIFY_SOURCE  # fix compile error on ubuntu
 SRCS = $(shell find src/ -name "*.c" -o -name "*.S" -o -name "*.cpp")
 include $(NAVY_HOME)/Makefile
+
+$(OBJS): Makefile
```

#### `src/syscalls/sysopen.c`

F0088：`mode` 默认置零；只有 `O_CREAT` 或已定义且完整匹配的 `O_TMPFILE` 标志才执行 `va_start/va_arg(ap, mode_t)/va_end`。普通二参 open 不再读取并不存在的第三实参；完整位匹配避免把仅有 O_DIRECTORY 的 flags 当作 O_TMPFILE。最后统一 `_open_r(..., mode)` 透传返回值。测试观察 mode 传递，nanos 仍不实现文件创建，不能从此推定内核支持这些 flags。

```diff
diff --git a/src/syscalls/sysopen.c b/src/syscalls/sysopen.c
index bc8d9d59f866eb9e4765d6cd669a2f3e08060c30..ecdeda83264afcd60cf530ecbd25ad08ec38a9cc 100644
--- a/src/syscalls/sysopen.c
+++ b/src/syscalls/sysopen.c
@@ -12,12 +12,19 @@ int
 open (const char *file,
         int flags, ...)
 {
-  va_list ap;
-  int ret;
+  int mode = 0;
 
-  va_start (ap, flags);
-  ret = _open_r (_REENT, file, flags, va_arg (ap, int));
-  va_end (ap);
-  return ret;
+  if ((flags & O_CREAT)
+#ifdef O_TMPFILE
+      || (flags & O_TMPFILE) == O_TMPFILE
+#endif
+      )
+    {
+      va_list ap;
+      va_start (ap, flags);
+      mode = va_arg (ap, mode_t);
+      va_end (ap);
+    }
+  return _open_r (_REENT, file, flags, mode);
 }
 
```


### F0078 — 根仓库

libos 此文件实际由根仓库跟踪；不把所有框架文件一概记为未跟踪。

- 差异路径相对于仓库 `.`；旧版本：`7a8150e51105eae3ebc3f04f992ec48d336c3370`；新版本：`23b031327d97e9cd3cecf2fa6eee4a6fc23ef736`。

#### `navy-apps/libs/libos/src/syscall.c`

F0078：在 `asm volatile (SYSCALL ... : "memory")` 中加入 memory clobber，向编译器声明系统调用可能读写寄存器参数指向的内存，使输入缓冲写入与输出缓冲读取不能沿用错误的跨调用假设。`volatile` 只保证该汇编不能被随意删除，不能独自表达这类内存副作用。寄存器约束、返回值与弱 hook 不变；它不是 CPU 硬件 fence。本组旧优化用例未复现误编译，不能声称本轮新增了旧版失败见证。

```diff
diff --git a/navy-apps/libs/libos/src/syscall.c b/navy-apps/libs/libos/src/syscall.c
index 666c1d46545f93ff6d74e09c664002078b4790d6..f8e32bb23ad9b13030557c635d4b18dc45d1ade2 100755
--- a/navy-apps/libs/libos/src/syscall.c
+++ b/navy-apps/libs/libos/src/syscall.c
@@ -62,7 +62,7 @@ intptr_t _syscall_(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2) {
   register intptr_t _gpr3 asm (GPR3) = a1;
   register intptr_t _gpr4 asm (GPR4) = a2;
   register intptr_t ret asm (GPRx);
-  asm volatile (SYSCALL : "=r" (ret) : "r"(_gpr1), "r"(_gpr2), "r"(_gpr3), "r"(_gpr4));
+  asm volatile (SYSCALL : "=r" (ret) : "r"(_gpr1), "r"(_gpr2), "r"(_gpr3), "r"(_gpr4) : "memory");
   return ret;
 }
 
```
