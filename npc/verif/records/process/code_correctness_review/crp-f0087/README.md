# CRP F0087 — exec示例失败状态

## 整体计划与启动（2026-10-20）

用户“提交后继续”确认F0074并授权实际提交后一个单元。根实际b260359，5文档85增5删，路径/mode/blob核对及root/index干净；39保留身份/390既有检查、正式资产身份复用。nested8101fad内容/index干净与850原mode保持。旧连续提交授权不恢复，不push/安装/M2推进。

目标/范围：仅修Navy tests/exec-test、execvp-test、busybox-test三个main在exec返回后仍return0的假成功；统一非零失败，execl示例补明确失败提示。成功exec仍不返回，不改libc/libos/OS退出重启/Make接口。原n+1输入溢出等非本问题范围不扩修。

一个独立单元：先原版动态反例与最小修改，再定向/共享验收和统一收尾，不另建业务Phase。交付为3源最小补丁、正文完整diff/语句解释、逐例真实状态与消费者身份、记录索引和唯一下一入口。

验收：host捕获三个main与实际参数/返回状态，exec失败时原版0的见证、修复后EXIT_FAILURE，成功调用不继续旧main的host控制路径。实际RV64跑三个失败输入（自exec缺文件、PATH无cat、busybox缺条目），经真实新main→CRT→SYS_exit捕获返回1；三条成功真实exec到目标，以专用目标标记/参数或实际cat数据和退出0确认旧main未继续。隔离诊断只在SYS_exit边界记录预期码，不把宿主make退出值或nanos重启当main状态；BusyBox诊断可仅追加constructor标记，原applet代码保持。runner故障判据少量验证。

最终新Navy沿原nanos update→run，三前台/hello及同版测试ELF/安装/盘身份，完整diff正反应用/实际目视/清理。CPU/RT/REF不消费这3个Navy示例不重跑；正式F0074产物保持，不直接改正式盘。完成后停止等待结果确认/commit，任何真实协议取舍/安装即停，不自动提交/下一组/M2。

## 实施结果 — Completed，结果确认/根commit Pending

仅3份根仓Navy示例源码4增3删：exec返回后EXIT_FAILURE，execl示例补失败提示。累计69已修/50未修完，前68已确认提交b260359；本组待结果确认/精确根提交。没有改CRT/内核退出/Make流程，正式F0074产物/配置保持原身份。

| 验收 | 最终事实与local证据 |
|---|---|
| 原版动态见证 | 从本组旧commit取三个实际main，以host链接捕获真实execl/execvp/execve参数并返回-1/ENOENT，均打印F87 MAIN RETURN=0 calls=1，在预期非零断言处exit1；非编译失败/工具失败。unit/*-before.log |
| host最终 | 三个实际main各9断言（共27），ASan/UBSan无报错。核对调用目标/argv/envp及PATH保持，失败各返回EXIT_FAILURE=1；host受控longjmp模拟exec成功不返回，旧main失败路径不继续。只是host控制模型，真实进程替换另见guest。18条实际compile/link/run命令记录unit-results |
| 实际RV64失败 | 自exec argv0指向缺文件、execvp继承缺cat的PATH、busybox-test的诊断文件表移除busybox条目；真实新main→libc exec→libos→kernel ENOENT后返回、打印原失败提示→CRT exit→SYS_exit均带码1。没有用stub替换被修main、exec实现或失败返回链；仅隔离内核SYS_exit末端记录实际码并与预期比较后halt，生产仍重启nterm |
| 实际RV64成功 | 自exec以有效argv0启动诊断目标，验证argc2/argv1=2并打印F87 SELF TARGET PASS；另外两例实际exec到BusyBox cat，原applet代码只追加diagnostic constructor专用标记，真实cat完整输出/share/files/num，最后实际退出0。均没有旧main失败提示/返回路径；标准盘中的BusyBox未插标记，诊断另用追加盘与条目。target.c/busybox-marker.c/prepare-guest.py/guest-results |
| 标准消费者 | 隔离原有nanos目录make -j4 ARCH=riscv64-nemu git_commit= update exit0/27.730s→run 54.682s；3个新示例真实链接=安装=108extent盘内字节，四启动ELF同版。三前台10条真实SDL键输入、8帧已目视：PAL标题/飞鸟、NTerm qzx not found后prompt、slide0→1→0 SHA恢复、回PAL/Enter继续；hello35→157。自有组SIGTERM/make-15是观察结束，不是guest正常退出/实体音视频/长期验收 |
| 身份/归档/判据 | 186preclean全PASS；4975源/配置与909构建身份，三源内嵌完整diff正反应用精确；7种非零/缺失/错误码/重复/混BAD等oracle变异均拒绝。正式盘/header/kernel/NEMU及OS代码/配置保持入口身份，双HEAD/index保持，nested内容干净/850原mode保持 |

六条真实诊断结果如下。“NEMU退出0”是隔离诊断对**预期main状态**匹配后的测试结果；它不表示失败main返回了0，也不把生产nanos sys_exit重启的宿主状态当用户状态。

| 实际输入 | CRT交到SYS_exit的码 | 诊断结果 |
|---|---|---|
| exec-test-failure | 1 | exit0 / GOOD，预期码核对通过 |
| exec-test-success | 0 | exit0 / GOOD，预期码核对通过 |
| execvp-test-failure | 1 | exit0 / GOOD，预期码核对通过 |
| execvp-test-success | 0 | exit0 / GOOD，预期码核对通过 |
| busybox-test-failure | 1 | exit0 / GOOD，预期码核对通过 |
| busybox-test-success | 0 | exit0 / GOOD，预期码核对通过 |

夹具更正：首次BusyBox marker显式lp64与Navy实际默认ABI不一致，链接明确拒绝；改用与实际Navy相同的编译默认ABI，未安装或改变生产ABI。符号首次查了已strip的BusyBox，改从同次busybox_unstripped核对constructor及init_array，并由实际运行的目标marker再次证明；符号检查未通过时的一次run-guest缺fixture调用没有运行任何case，不计验收。最终六case全部实际执行后才接纳，日志/命令和ABI失败记录保留在fixture-corrections，未把编译或准备失败写成产品PASS。

## 限制、清理与恢复

此修复只保证合法输入下exec示例返回路径的可观测失败，不修exec-test n+1极端整数溢出或通用坏指针。未改变nanos重启nterm、不承诺宿主退出码自动等于用户main值；诊断内核的halt/BusyBox constructor只存在隔离环境。host不替代真实guest。CPU/RT/REF不消费这3个Navy示例而不重跑；NPC/其他ISA/人工GUI/实体AV/长期NotRun。

验证/目视/完整diff归档后清理9643项510446459逻辑字节（约486.8MiB），零tracked删除，仅本组隔离源码/构建/盘/六诊断内核、host二进制及截图/observer；不跟随目录symlink，不删除正式F0074资产。cleanup-plan/receipt记录原路径/字节/SHA及预期缺失，旧截图和诊断盘不可再直接查看。保留最小host/目标/marker源、配置/命令/结果/身份/patch；local/.agent不随普通commit备份。

恢复以旧完整commit `b2603592510d20b8cd4467128e8d936e498d143a` 加repair.patch取得本组源码、使用entry中已有正式资源/工具身份，在新隔离目录按local/unit.py→prepare-runtime.py→prepare-guest.py→run-guest.py及standard-path/run-standard.local nanos，之后visualize/archive/check、实际目视后cleanup/final-check。prepare-guest的诊断源/链接注入不属于标准消费者盘；无下载。不能从未来HEAD或已清理盘推定旧字节仍存在。

本组完整收尾后停止，等待结果确认/commit，不自动提交或下一组/push/M2。建议本组确认提交后开启新对话：当前会话已积累多个修复/诊断单元，唯一TASK_QUEUE#crp-next和恢复资料已完备；建议不增加确认/执行门槛，不另造启动Prompt。

<a id="repair-diff"></a>
## 最终代码diff与语句说明

根仓，旧完整commit `b2603592510d20b8cd4467128e8d936e498d143a`；新版本 `WORKTREE（2026-10-20，未提交）`，相对路径/新SHA256：

- `navy-apps/tests/exec-test/main.c`：`0042ead574d6efa892b1b53680f2f42ec0df6c839c6b296c87aaecb9da63f68f`
- `navy-apps/tests/execvp-test/main.c`：`ba20d0599a99f5466005a1322381177475fb966b4b52d8f2f985f40678b415c3`
- `navy-apps/tests/busybox-test/main.c`：`8711b9a15ed2e6d93edc899f8765f315bb0db113724e5f14f92439dd12bf7664`

三个`exec*()`成功时均不返回，因此紧随调用的路径只可能是未成功替换原进程。将此处`return 0`改为`return EXIT_FAILURE`，使标准C main→exit链携带非零失败状态；exec-test原先无错误提示，再补`printf("exec-test: execl failed\n")`，另外两例已有失败提示保持。没有依赖尚待修复的特殊_reent errno，也不把失败提示本身当作成功。

成功路径的调用目标、argv/envp/PATH设置与execl的自增示例保持。nanos现行`sys_exit`会重启nterm，不改变它来伪造宿主失败码；本组诊断仅在隔离内核SYS_exit边界核对实际来自新main/CRT的码，再按预期判定测试结果。返回后任意值均以失败报告，未改变成功exec不返回的契约。源码共4增3删，三个文件完整实际diff如下；临时目录正向等于新源、反向精确恢复旧commit（含原有无末尾换行标记），local/archive-validation。

```diff
diff --git a/navy-apps/tests/busybox-test/main.c b/navy-apps/tests/busybox-test/main.c
index 2128b95405735c8ffd8827f95dfa6fb143c18ff8..bec8cef714187f003d983d7ef929868d23a49d08 100644
--- a/navy-apps/tests/busybox-test/main.c
+++ b/navy-apps/tests/busybox-test/main.c
@@ -8,5 +8,5 @@ int main() {
   char *const envp[] = {NULL};
   execve("/bin/busybox", argv1, envp);
   printf("exec busybox failed\n");
-  return 0;
+  return EXIT_FAILURE;
 }
\ No newline at end of file
diff --git a/navy-apps/tests/exec-test/main.c b/navy-apps/tests/exec-test/main.c
index f7b1b25ef5c898b92b626f10fb06304642bf2b43..6671b7b2a2d6472f13c3414d8d6d6dcf068b7458 100755
--- a/navy-apps/tests/exec-test/main.c
+++ b/navy-apps/tests/exec-test/main.c
@@ -10,5 +10,6 @@ int main(int argc, char *argv[]) {
   char buf[16];
   sprintf(buf, "%d", n + 1);
   execl(argv[0], argv[0], buf, NULL);
-  return 0;
+  printf("exec-test: execl failed\n");
+  return EXIT_FAILURE;
 }
diff --git a/navy-apps/tests/execvp-test/main.c b/navy-apps/tests/execvp-test/main.c
index b980eba92e9cd0797bc5fcc02b10657ec98e9048..ef954d0796bb7f2a9313d0cc61e6d61e76460ee7 100644
--- a/navy-apps/tests/execvp-test/main.c
+++ b/navy-apps/tests/execvp-test/main.c
@@ -9,5 +9,5 @@ int main() {
   char *argv[] = {"cat", "/share/files/num", NULL};
   execvp("cat", argv);
   printf("[execvp-test] execvp failed\n");
-  return 0;
+  return EXIT_FAILURE;
 }
\ No newline at end of file
```


<a id="submit-20261020"></a>
## 2026-10-20 用户确认与提交回执入口

用户本轮“提交”确认已报告的F0087范围并授权精确根提交。88项保留manifest身份、369项既有终检及3源已验收patch无漂移，复用原功能验证、归档与清理，不重跑测试或重复Completion。仅3个示例源及本批必要报告/索引、F0074已完成提交附记纳入；local/.agent和正式忽略资产不随普通commit备份。

前文Pending与WORKTREE是完成时截面；本轮确认与实际提交状态以本附记对应的修复提交和local/submit-precheck、submit-staged、submit-receipt及CURRENT_STATE为准。提交前不虚构自身完整hash，实际提交后核对路径/mode/blob、验收源码diff与根/index干净并保存真实hash；新事实只补回执，不覆盖原完成快照。用户仅授权提交，本轮停止，不开始F0090、不push。

会话建议：建议开启新对话，因本会话已累积多个修复/诊断单元；CURRENT_STATE/TASK_QUEUE唯一入口和证据可恢复，新对话直接“继续CRP修复”即可，不另造启动Prompt。建议不改变既有授权、确认/commit或执行门槛。
