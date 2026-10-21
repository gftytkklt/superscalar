# CRP F0113 — 软件 syscall 与宿主后端派发隔离

2026-10-21，用户“继续CRP修复”授权唯一入口的一个工作单元。F0086已确认提交848299737048b8a3138a1efcd910737b793037bf，根工作树/index干净，无状态冲突；M2不变。

## 本单元计划

范围仅libam软件CTE与libos弱hook协作：未注册handler及handler内部的后端syscall使用原硬件陷入；外层软件syscall进入handler一次，保留参数/原始返回与上下文。采用私有hook“是否处理+返回值输出”协议，handler执行域标记覆盖syscall/yield/native事件，软件syscall使用调用栈上的Context。两个私有调用端同步修改；公开AM/POSIX接口与Make入口不变。NULL handler返回原有0语义保持。真实上下文切换、线程/信号安全、wrapper VME/heap与新存储能力不在范围。

步骤：现源反例与弱符号实际闭包→最小修复→host原函数定向/失败与RV64真实libos/libam/NDL及nanos消费者→完整diff及正反字节验证/身份/清理→同步records索引与.agent后停止。保留旧版递归/未注册错误对照；未测或能力阻塞如实标注。正式盘/内核/配置/用户引擎及newlib既有差异保持entry身份；构建隔离、无安装。真实未决策略按WORKFLOW_POLICY §3停下，当前无安装/策略裁决事项。

验收：无hook/未注册/已注册正常与失败、backend嵌套不重入、参数和64位返回/errno保持、外层Context不被覆盖、返回替代Context/NULL、yield后恢复派发；实际RV64运行与受影响nanos三前台/hello回归。CPU-tests/RT不链接Navy libos/libam，无相关源码变更，不重跑。完整wrapper仍缺VME/provider，不把定向guest作为完整wrapper运行。

交付：两生产源、本文完整diff/解释与结果、local最小配方/命令/日志/身份/patch及清理回执，process/repair-status/REPAIR与.agent。完成后等结果确认/commit，不自动commit/push/下一组或M阶段。

参考：[ICS-PA3.5](https://ysyx.oscc.cc/docs/ics-pa/3.5.html)（2026-10-21访问）说明Navy的OS相关运行库与应用层分层；本项具体派发契约依据已批准F0113与本地调用链，不从讲义推定完整CTE能力。

## 实施结果与调用语义

F0113 **Completed，结果确认/本组commit Pending**。生产仅修改根仓两源（28增16删，含cte原缺失EOF换行）；公开AM/POSIX接口、各ISA原陷入指令、syscall编号、nanos内核及Make选项不变。

- libos私有弱hook由“直接返回syscall结果”改为`bool handled`和`intptr_t *ret`输出。弱符号不存在，或hook返回false时，继续执行原硬件asm；返回true时只取输出结果。该协议将“未处理”与合法返回0/负errno明确分开，不借用错误码作为bypass哨兵。两个调用端必须同版链接；既有递归archive/update会按源依赖重建二者，本次实际干净构建验证。未承诺旧/新私有ABI混配兼容。
- libam在未注册handler或`in_handler`为true时立即返回false，不修改Context或输出。未注册时不再把输入a0误当syscall结果，普通libam初始化前的IO也回到真实宿主。
- `__am_irq_handle`在实际调用handler前保存旧标志并置true，返回后恢复；syscall、yield及native信号的callback入口统一经过它。handler内部NDL/newlib/libos调用因此走宿主，后端errno/原始返回仍由既有F0076转换处理。保存/恢复标志保留同步嵌套事件的外层域；没有实现线程/TLS/异步信号安全或不返回handler的恢复。
- 每次软件syscall在栈上复制`current_ctx`为独立现场，填写GPR1～4及Event cause/ref，交给handler；返回替代Context时取其GPRx，NULL仍返回0。不会由backend改写外层现场或yield共享现场；此栈上Context只在同步handler调用期有效，不提供持久Context或真实进程切换能力。

## 本次验证

| 验证 | 结果与实际范围 |
|---|---|
| host旧/新同判据 | 最终host.py/test.c：旧hook普通311检查157失败，san311检查158失败，均exit1；最终普通/sanitizer各105检查零失败、exit0。旧/新无hook各8检查零失败。只把libos硬件asm替换为受控backend、重命名导出符号/低层errno避免宿主冲突；CTE/IOE为真实生产函数，host NDL为最小时钟桥，不冒充完整OS。旧handler深度>2返回-ELOOP以有界观察实际重入/覆盖；不是生产新增递归限额。 |
| 实际RV64旧/新 | Navy真实Make/当前newlib/libos/libam/libndl，真实NEMU+nanos宿主：旧310检查157失败/BAD TRAP/exit1，新104检查零失败/GOOD TRAP/exit0；无hook应用7检查零失败/GOOD TRAP/exit0。实际nm确认before/after存在hook定义、nohook无定义。外层测试handler为最小夹具；后端执行真实宿主nanos syscall，IOE TIMER→NDL_GetTicks64→gettimeofday→libos→ecall真实闭合。 |
| 有区分力的场景 | 无hook、hook存在但未注册及取消注册、连续注册后请求；handler一次派发、type/三参数/Event cause/ref、64位正返回、原始-EBADF与低层errno、backend time/read失败/write成功、外层Context逐字节不变、替代Context/NULL返回、yield内backend与yield后再次软件syscall。host替代硬件/guest实际陷入分开记录；未运行实际上下文切换。 |
| 标准消费者update→run | 隔离nanos `make -j4 ARCH=riscv64-nemu git_commit= update` exit0（27.432s），随后既有run入口54.656s，8帧/10键实际观察：F2终端qzx→command not found→新prompt，F3幻灯片0→1→0且往返图SHA相同，F1返回PAL并Enter后继续绘制；hello从首帧39到末帧160。自有组SIGTERM、make -15，非guest正常退出。108extent逐字节匹配真实安装文件，尾padding全零。 |
| native条件编译 | 原/新CTE用Linux/glibc系统头、`-D__ISA_NATIVE__`各实际编译exit0；未运行native信号/计时或其它ISA。 |
| 归档/保护 | 49项preclean核对通过，含全部命令退出/有效结果、完整diff正反逐字节、最终隔离源与生产源相同、8正式资产/根HEAD/newlib HEAD及既有mode差异保持。native另2条编译命令exit0；不安装、下载或修改系统。 |

RV64测试复用现有隔离runtime配方；外层宿主内核只在测试配置将前台设为单测试应用，测试sys_exit改halt返回判据，生产nanos不改。raw报告/退出ecall确保旧版未注册handler不会吞掉判据。完整wrapper受F0086已记录的VME/provider、F0084 heap及真实switch占位限制，本轮不扩其能力、未运行完整wrapper，也不把本项定向guest当wrapper可用。真实消费者取当前标准配置/源，不改正式用户盘；原生CPU-tests及RT不链接Navy这两库，未重跑无关回归。

验证准备曾缺NDL头路径，补齐夹具include后最终host六组构建均无warning/error；随后增加三参数断言，最终以105/104检查版本为准。native第一次编译因未禁用ccache遇只读缓存错误，原失败日志保留，显式`CCACHE_DISABLE=1`后旧新均编译成功；没有安装或调整系统。原始命令、退出码、测试源、配置、符号表和结果分别保存在local/host-results、real-results、native-compile-results、standard-path与archive-validation。

## 完整生产diff与版本

仓库：根ysyx-workbench，以下均相对根仓路径。旧完整commit `848299737048b8a3138a1efcd910737b793037bf`；新为**WORKTREE（2026-10-21，未提交）**，旧/新SHA256如下。cte mode100644、libos mode100755保持；本批无nested源码修改。

| 文件 | 旧SHA256 | 新SHA256 |
|---|---|---|
| navy-apps/libs/libam/src/cte.c | 925ac61167227ef21be87d5f06108cf62cff8a1dfdbb564d86f4b444e4cd31f0 | 6ce953228fd137391caca48c7d0681fc138cb9bf603e06c7eb78a769b2a7390c |
| navy-apps/libs/libos/src/syscall.c | 0fe52fc62f01bd6cb9c6c92a97ec36439fd54d5eaee90f912025d9c07cc08f32 | a2726fef3077967e17144aa18108c07ed36810f989e127b98a2afa6ba06d5849 |

```diff
diff --git a/navy-apps/libs/libam/src/cte.c b/navy-apps/libs/libam/src/cte.c
index 1b7bca1e6bcd2c6b9ff2321de90ebe6f99adfe81..eb7861089374414677030805b87768cb848a76c6 100644
--- a/navy-apps/libs/libam/src/cte.c
+++ b/navy-apps/libs/libam/src/cte.c
@@ -23,6 +23,7 @@
 
 static Context *(*cte_handler)(Event ev, Context *ctx) = NULL;
 static bool irq_enabled = true;
+static bool in_handler = false;
 
 // 软件自陷下的"当前上下文"（不做真实寄存器保存）
 static Context current_ctx;
@@ -31,7 +32,12 @@ static void __am_switch_to(Context *next);
 
 static Context *__am_irq_handle(Event ev, Context *ctx) {
   Context *next = ctx;
-  if (cte_handler != NULL) next = cte_handler(ev, ctx);
+  if (cte_handler != NULL) {
+    bool saved = in_handler;
+    in_handler = true;
+    next = cte_handler(ev, ctx);
+    in_handler = saved;
+  }
   return next;
 }
 
@@ -39,14 +45,18 @@ static Context *__am_irq_handle(Event ev, Context *ctx) {
 // guest 的 libos _syscall_ 通过弱符号钩子(__am_cte_syscall)转到这里，
 // 以"函数调用"模拟陷入：把系统调用投递给 guest 注册的 CTE handler。
 // 系统调用号/参数通过 GPR1..GPR4 传递，返回值经 GPRx 取回。
-intptr_t __am_cte_syscall(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2) {
-  current_ctx.GPR1 = type;
-  current_ctx.GPR2 = a0;
-  current_ctx.GPR3 = a1;
-  current_ctx.GPR4 = a2;
-  Event ev = { .event = EVENT_SYSCALL, .cause = type, .ref = (uintptr_t)&current_ctx };
-  Context *next = cte_handler != NULL ? cte_handler(ev, &current_ctx) : &current_ctx;
-  return next != NULL ? next->GPRx : 0;
+bool __am_cte_syscall(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2, intptr_t *ret) {
+  if (cte_handler == NULL || in_handler) return false;
+  // 每次软件自陷独占现场，后端请求不改写外层或 yield 的 current_ctx。
+  Context ctx = current_ctx;
+  ctx.GPR1 = type;
+  ctx.GPR2 = a0;
+  ctx.GPR3 = a1;
+  ctx.GPR4 = a2;
+  Event ev = { .event = EVENT_SYSCALL, .cause = type, .ref = (uintptr_t)&ctx };
+  Context *next = __am_irq_handle(ev, &ctx);
+  *ret = next != NULL ? next->GPRx : 0;
+  return true;
 }
 
 void yield(void) {
@@ -140,7 +150,7 @@ static void trap_signal_handler(int sig, siginfo_t *info, void *uc_void) {
 
   Context *next = &ctx;
   if (ev.event != EVENT_NULL && cte_handler != NULL) {
-    next = cte_handler(ev, &ctx);
+    next = __am_irq_handle(ev, &ctx);
     if (next == NULL) next = &ctx;
   }
   ctx_to_uc(next, uc);
@@ -189,4 +199,4 @@ bool cte_init(Context *(*handler)(Event ev, Context *ctx)) {
   return true;
 }
 
-#endif
\ No newline at end of file
+#endif
diff --git a/navy-apps/libs/libos/src/syscall.c b/navy-apps/libs/libos/src/syscall.c
index c1590f1cf930b0855cd6865388e1596aa6b33550..a9d347204c660276f6787f3e522f78d6557db68f 100755
--- a/navy-apps/libs/libos/src/syscall.c
+++ b/navy-apps/libs/libos/src/syscall.c
@@ -5,6 +5,7 @@
 #include <errno.h>
 #include <time.h>
 #include <stdint.h>
+#include <stdbool.h>
 #include "syscall.h"
 
 // newlib's _xxx_r wrappers copy this low-layer slot into the requested _reent.
@@ -62,13 +63,14 @@ static intptr_t syscall_result(intptr_t ret) {
 extern char end;
 void* program_break = &end;
 
-// 若链接了 libam（Navy 上的 AM），系统调用改走软件自陷；
-// 否则该弱符号为 NULL，_syscall_() 保持原有的自陷指令。
-__attribute__((weak)) intptr_t __am_cte_syscall(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2);
+// libam 仅在 guest handler 可接收请求时处理软件自陷；未注册或正在执行
+// handler 时返回 false，使后端 IO 走宿主自陷，避免再次进入同一 handler。
+__attribute__((weak)) bool __am_cte_syscall(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2, intptr_t *ret);
 
 intptr_t _syscall_(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2) {
-  if (__am_cte_syscall) {
-    return __am_cte_syscall(type, a0, a1, a2);
+  intptr_t result;
+  if (__am_cte_syscall && __am_cte_syscall(type, a0, a1, a2, &result)) {
+    return result;
   }
   register intptr_t _gpr1 asm (GPR1) = type;
   register intptr_t _gpr2 asm (GPR2) = a0;
```

全部修复hunk与local/repair.patch一致。隔离临时目录从旧commit还原两源，正向patch生成当前新字节，反向patch逐字节恢复旧源，均exit0；49项核对中包含这6项应用/结果检查。正文空上下文行保留原始统一diff字节，空白告警须逐条核对，不能改写证据。

## 恢复、清理与停点

复现时先使用baseline完整commit及local/repair.patch，运行host.py；prepare-runtime.py只复制本工作区已有源/资产到新standard-path/work，排除Git/build、重映射绝对symlink后按显式NAVY_HOME/AM_HOME/NEMU_HOME执行update。standard-path/run-standard.py执行既有run并采集；real.py顺序构建旧/新/nohook与独立测试内核/盘，完整命令/输出/产物SHA另存。不要直接在正式盘执行失败实验或覆盖已有证据目录。prepare-runtime.py复用了F0076配方及F0085观察helper，必要源已本地保留；未下载依赖。

保留test.c、host/real/prepare/archive/收尾与清理最小配方、observe_sdl.c/run-standard.py、实际命令/退出/配置/日志/符号表、输入与产物身份、完整patch；一次性测试源与脚本无需随生产提交，local由本批.gitignore排除。截图已实际查看，清理后不能再查看原图；源码/模型/对象/盘按Git与配方重建。ignored记录/.agent不是commit备份。

本组完成后停止，等用户确认及精确commit；累计103已修（前102确认提交、本项Pending）+14 CRP待修+2 Linux能力扩展移交，原119行保持。唯一未来入口TASK_QUEUE#crp-next，不在此维护第二个Next。不自动commit/push/下一组或M阶段。

### 清理与持久化回执（2026-10-21）

验证/目视/归档通过并确认自有任务均结束后，按cleanup-plan逐项身份删除9404个可再生隔离文件/链接，507165304逻辑字节、535093248分配字节；零tracked/正式资产删除，全部预期路径已不存在。包括源/资产副本、测试盘、ELF/对象/库/执行器和已观察截图，必要文字/配置/命令/测试配方/身份与patch保留。cleanup-plan/receipt解释预期缺失；不能再直接复用旧镜像或截图。8正式资产及newlib既有状态在最终收尾再次核对。

CURRENT_STATE/TASK_QUEUE/CHANGELOG_AGENT、DOCUMENT_INDEX及process/repair-status/REPAIR已同步本次真实范围、验收、未测及停止门槛。Working tree contains uncommitted F0113 code/documentation changes；根HEAD仍8482997，index无暂存，无本组commit/push/下一组Start。

F0113最终终检：102项PASS；119行=103已修+14 CRP待修+2移交一致，完整生产patch/内嵌diff与已验收源一致，8资产/newlib状态保持，9404预期清理逐项确认缺失。10条空白告警逐一核对只来自内嵌diff的原始空上下文行，正文无其他空白问题；git --no-index --check实际exit3（差异与空白诊断组合），终检脚本按实际语义核对，不把退出3误当生产失败。未新增动态测试/commit，本组Completed、确认/commit Pending；下一F0084未Start，当前停止。

<a id="submit-20261021"></a>
## 用户确认与提交收尾（2026-10-21）

用户“提交后继续”确认F0113已报告范围及完整wrapper/其它ISA等未测边界，授权精确提交本批后执行唯一下一入口F0084必要分析。复用原Completion和动态验收，不重复归档或重跑测试；提交前62份本地证据、完整生产patch、8正式资产、newlib HEAD及既有mode差异均保持。提交仅包含两份生产源、本报告/.gitignore、process索引和repair-status六个根路径；local/.agent/REPAIR等仍为本地忽略资料，commit不等于备份。

实际提交身份由包含本节和完整生产diff的Git commit及local/submit-staged.json、submit-receipt.json定位；生产新源SHA与已验收WORKTREE相同。103已修均获用户确认，本次提交不把定向夹具变成完整wrapper能力验收，不授权push或提交F0084新内容。

会话建议：可在当前对话继续。F0113收尾证据完整，F0084同属libam背景，下一入口与需裁决边界明确。
