# CRP F0093 — miniSDL定时器重入与回调状态

## 整体计划与启动（2026-10-20）

用户“提交，继续”确认F0092并授权精确提交后唯一下一单元。根实际7eb176d563d9c537abb849a8e59772cf9ca22655，五路径/mode/blob及验收patch核对一致，52保留身份/既有验收复用，提交后根/index干净；nested libc8101fad内容/index不变/850原mode保持，正式F0074输入保持。仅本轮F0093执行授权，不恢复旧连续提交授权、不push/安装/推进M2。

目标/范围：F0093，优先仅timer.c；CallbackHelper/audio.c保持，除非必要证据证明需调整。让计时callback查询GetTicks/PollEvent/Delay等轮询API时，同次到期timer不重复派发；回调内Remove/Add重用slot时，旧回调返回不写回新timer状态。保留16槽、void* ID ABI、Add/Remove/返回0停止及返回非0改间隔、单线程轮询、Make/update→run和正常音频路径；不引入并发/线程/新timer特性。

已有接口足以确定最小契约：TimerHelper串行派发，嵌套pump不递归进入timer扫描；callback本身仍可查询真实时间。Add每次分配标记该slot的新实例，callback返回仅在原实例仍有效时写回。callback返回后刷新后续扫描使用的NDL时间（无回调时仍只读时钟一次），避免前一个callback新建timer的last大于扫描开始旧now、经无符号减法误判到期。正常同槽删除/重建继续允许，不以运行标志占住已释放slot改变16槽容量。

NULL与interval0分析：现有Add原样接受NULL callback和0间隔，头文件无额外注册失败约定；本轮不擅改注册语义。0间隔保持每个外层pump最多对该slot派发一次、返回0停止；NULL仅作注册后移除的兼容性检查，不执行NULL到期回调，不宣称支持调用空函数。无效/过期ID、非本地跳转/线程并发不扩修，generation为内部实例身份而非新公共ID协议。

一个独立单元：原版受控动态见证→最小实现与确定性host验证→实际RV64真实时钟/回调消费者→最终标准Navy update→run三前台/hello→正文完整diff/语句解释/正反应用/实际目视/清理/状态收尾。交付为最小生产补丁、报告、命令/日志/结果/身份及records索引/唯一下一入口；完成后停止等结果确认/commit，不自动提交新组或下一组。

验收：原生产timer/audio/event在明确时钟模型下复现单due回调3次/深度3、同槽重建被旧返回覆盖，以及callback推进时间并新建后续slot的提前触发；最终GetTicks/PollEvent不重入、自移除/同槽重建返回0与非0、移除其他timer、新建后续timer、改间隔/停用、16槽耗尽/释放/重加、uint32回绕、0间隔、NULL注册后移除。普通GCC/ASan+UBSan；正常audio CallbackHelper路径用真实生产audio加NDL后端模型检查。实际RV64链接真实miniSDL/NDL/libc，时间由真实gettimeofday提供，callback内查询/事件轮询及删除重建/后续slot不提前、停止/改间隔均实际观察。最终原nanos目录update→run三前台/hello、同版源码/对象/库/链接=安装=盘、正式资产保护、完整diff正反与目视后清理。

CPU/RT/REF不依赖Navy miniSDL不重跑；NPC/其他ISA/真实native/NWM/实体声音/长期NotRun，host模型不代替真实消费者。真实策略/范围冲突或安装即停；测试夹具本地忽略，仅必要源码/报告提交。参考本对话已读ICS-PA应用章节及本地sdl-timer.h/CallbackHelper，具体接口以当前实现声明为准，不声称完整SDL兼容。


## 实施结果 — Completed，结果确认/commit Pending

生产仅`navy-apps/libs/libminiSDL/src/timer.c` 12增1删；audio/event/NDL及公开头文件/Make不改。F0093完成，累计72已修/47未修完，前71已确认提交（F0092实际7eb176d），本组确认/根commit Pending。

| 验收 | 本轮实际结果与local入口 |
|---|---|
| 原版动态见证 | 原timer.c+当前真实audio.c/event.c，NDL后端明确时钟模型。单due回调3次/最大深度3；回调自移除并同槽Add后，原返回0停掉新timer、返回7改错新间隔；回调将时间推进10→100再新建后续slot，旧扫描now导致立刻触发。本组四个进程都在对应契约断言exit1，非编译/工具失败。unit/before-*.log及unit-results |
| 最终host | 普通GCC/ASan+UBSan各15场景、111断言通过：GetTicks/PollEvent/Delay重入、自移除、同槽重建返回0/7、满16槽时自移除重建仍能同槽成功、移除其他timer、callback后新建后续slot、改间隔/停止、16槽耗尽/复用、uint32回绕、零间隔、NULL注册后移除。无timer/16个未到期timer的单pump均只读时钟一次，避免新增16次系统调用；正常audio开启/回调内查时间与事件/暂停/一次Query-Play路径通过。NDL时间/音频为模型，非实际声卡；LSan按已知沙箱限制关闭，ASan/UBSan启用 |
| 实际RV64 | 真实SDL_Init/miniSDL/NDL/libc/libos及gettimeofday，52断言通过，main0→诊断SYS_exit→NEMU exit0/GOOD；callback查询时间/轮询事件不重入，同槽重建返回0和7、新建后续slot均在真实120ms后才触发（实际各120ms）；移除其他timer/25ms改间隔/停止、零间隔、满16槽、callback Delay通过，NULL只注册并移除。无stub timer/audio/event/NDL或真实时钟，仅隔离内核末端打印main码并halt。guest.c/prepare-guest/run-guest、guest-results/guest-run.log；六种非零/缺PASS/错断言数/错退出码/重复PASS/混BAD判据变异拒绝 |
| 标准最终消费者 | 隔离原nanos目录`make -j4 ARCH=riscv64-nemu git_commit= update`exit0/27.080秒，再同目录`run`54.652秒；PAL→NTerm qzx not found并回prompt→slide0/1/0→PAL/Return队列输入后继续渲染，10次SDL输入/8帧目视，hello35→148；slide0回归帧SHA精确恢复。Return不单凭帧差声称进入特定菜单。自有组SIGTERM/make-15是有限观察结束，不是guest正常退出。standard-path/update-final-result及nanos/result/observe/guest日志 |
| 同版/归档/保护 | 完整diff正反应用精确；最终源码/编译对象/真实库成员、链接=安装=108个唯一连续extent、诊断独立盘目标、标准新内核/NEMU与正式F0074输入保护核对；实际检查/源码与产物身份、清理和最终状态见local。正式盘/header/kernel/NEMU/配置未变，nested内容/index及850原mode保持 |

## 语句实现及调用链

`timer_dispatching`只属于timer派发器。进入helper时若已在派发即返回，外层正常返回前清除标志；因此callback里的SDL_GetTicks仍返回NDL时间，PollEvent仍可取事件，Delay仍按NDL时间前进，但这些API经实际audio CallbackHelper再次调用TimerHelper时不会递归进入timer扫描。audio_in_callback及正常音频调用链没有改动，不把计时器保护扩大为停用音频。

每次Add使用空slot时递增该slot的`uint64_t generation`，作为内部实例身份，仍返回原slot指针。派发前保存generation，callback返回后只有`used`仍真且generation未变才应用返回值；自移除/重建产生的新实例与旧实例不同，旧返回0或新interval都不再污染新timer。已释放slot仍可立即Add，不用running标志占用它；满16槽中的callback自移除后也可重用自己slot。此generation不改变公共void* ID ABI，不解决外部长期保存旧ID后误操作复用slot的既有边界。

callback可能耗时、Delay或新建后续slot；故返回后更新扫描使用的`now = NDL_GetTicks()`，避免旧now小于新timer的last而以模减误判超时。原实例仍有效且返回非0时，直接用这个更新后的now作为last，保持从callback完成后重新计时；返回0清used停用。外层无callback时仍只取一次时钟，有callback时每次返回取一次，不在16个slot上无条件增加16次gettimeofday。计时差仍使用uint32模减，host验证跨单次回绕，实际guest没有等49.7天。

## 限制与恢复

本项为单线程、callback正常返回的轮询模型，不承诺线程并发、异常/longjmp退出callback或任意恶意ID安全；64位generation不承诺在一个未返回callback中循环同槽重建2^64次后的身份区分。NULL callback到期调用仍不支持/未修，零间隔沿用接口；没有新增注册拒绝/errno策略。F0094 CloseAudio、F0095混音及F0096格式等独立问题保持未修；host正常audio用例在callback内暂停后不再次派发，不拿它声称CloseAudio生命周期已解决。实体声音、真实native/NWM、NPC/其他ISA/长期NotRun，CPU/RT/REF按影响不重跑。

从入口完整commit加repair.patch恢复最终源码；按entry/F0074现有资产配方和工具，unit.py→prepare-runtime.py→standard-path/run-standard.local nanos→prepare-guest.py→run-guest.py→visualize.py→archive.py→check.py，实际目视后cleanup.py/final-check.py。无下载或安装；隔离诊断仅另盘追加f93目标并在SYS_exit末端观测，标准盘无诊断目标/标记。保留最小测试源/命令/日志/结果/身份与patch，产物和生产副本验证后清理；local/.agent不由普通commit备份。

本组收尾后停止，等确认及精确提交；不自动提交新组/push/下一组/M2。唯一后续范围/必读/门槛/验收只在TASK_QUEUE#crp-next。会话建议：本批确认提交后建议开启新对话，因当前已累积多组修复证据，下一项转音频资源生命周期，恢复入口完整；建议不增加确认/执行门槛，不另造启动Prompt。

## 最终收尾

207项preclean及34项最终收尾检查全部通过，4890份源码/配置及849份构建产物身份保存。实际目视和完整diff正反应用后，清理9389项507101571逻辑字节（约483.6MiB），零tracked删除；仅本组隔离源码/构建/诊断盘/host二进制/截图等可再生产物，不动正式F0074输入。路径/字节/SHA及预期缺失见local/cleanup-plan、cleanup-receipt，原身份记录保留；已删除截图/盘不再宣称可直接查看。必要最小测试源/命令/日志/结果/身份/patch保留，local/.agent不由普通commit备份。

记录索引、逐项台账、CURRENT_STATE/TASK_QUEUE及完成快照同步。Working tree contains uncommitted CRP repair/documentation changes；根HEAD7eb176d，双index空，nested8101fad内容不变/850原mode保持。72已修/47未修完，本组确认/commit Pending；整组后停，未来F0094未Start，只沿TASK_QUEUE唯一入口，不自动提交新组/push/M2。

<a id="repair-diff"></a>
## 完整diff与版本身份

根仓，旧完整commit `7eb176d563d9c537abb849a8e59772cf9ca22655`；相对路径 `navy-apps/libs/libminiSDL/src/timer.c`，旧SHA256 `9e3e018d9e252c205b1f6572d59adc7ae6ee3cc31f233471b6af74844659a684`；新版本 `WORKTREE（2026-10-20，未提交）`，SHA256 `ef8f263bacc0cbdf9ed412a489710b0d1c4bdfb0ac959906b2c72fe87546ce5d`。逐句说明见上文；临时目录正向精确得到新源，反向精确恢复旧源。保留完整hunk/上下文与无末尾换行标记。新增报告的3条尾随空白告警逐条确认为diff空上下文行的单个前缀空格，按归档规则保留原字节；正文/新增代码无此问题，见local/whitespace-review。

```diff
diff --git a/navy-apps/libs/libminiSDL/src/timer.c b/navy-apps/libs/libminiSDL/src/timer.c
index 30603ee4182f9f5071cc0b46eb8e014dbcbca9cd..63755b02ec3a9c36ca5137b8c80e638ce2780913 100755
--- a/navy-apps/libs/libminiSDL/src/timer.c
+++ b/navy-apps/libs/libminiSDL/src/timer.c
@@ -10,6 +10,7 @@ void CallbackHelper();
 
 typedef struct {
   bool used;
+  uint64_t generation;
   uint32_t interval;
   SDL_NewTimerCallback callback;
   void *param;
@@ -17,10 +18,12 @@ typedef struct {
 } SDL_Timer;
 
 static SDL_Timer timers[MAX_TIMERS];
+static bool timer_dispatching;
 
 SDL_TimerID SDL_AddTimer(uint32_t interval, SDL_NewTimerCallback callback, void *param) {
   for (int i = 0; i < MAX_TIMERS; i ++) {
     if (!timers[i].used) {
+      timers[i].generation ++;
       timers[i].used = true;
       timers[i].interval = interval;
       timers[i].callback = callback;
@@ -55,16 +58,24 @@ void SDL_Delay(uint32_t ms) {
 // SDL APIs (SDL_GetTicks / SDL_PollEvent / SDL_Delay), mirroring the way the
 // audio callback is fed.
 void SDL_TimerHelper() {
+  if (timer_dispatching) return;
+  timer_dispatching = true;
   uint32_t now = NDL_GetTicks();
   for (int i = 0; i < MAX_TIMERS; i ++) {
     if (timers[i].used && now - timers[i].last >= timers[i].interval) {
+      uint64_t generation = timers[i].generation;
       uint32_t next = timers[i].callback(timers[i].interval, timers[i].param);
+      // Callbacks may advance time or create timers in later slots.
+      now = NDL_GetTicks();
+      // A callback may remove this timer and reuse its slot.
+      if (!timers[i].used || timers[i].generation != generation) continue;
       if (next == 0) {
         timers[i].used = false;
       } else {
         timers[i].interval = next;
-        timers[i].last = NDL_GetTicks();
+        timers[i].last = now;
       }
     }
   }
+  timer_dispatching = false;
 }
\ No newline at end of file
```


<a id="submit-20261020"></a>
## 2026-10-20 确认与提交

用户“提交后继续”确认F0093已报告范围并授权精确提交后F0094一个单元；提交前发现正式ramdisk.img、ramdisk.h和nanos内核在原收尾后更新，用户明确“是的，保留后继续执行”确认来自其update/run，保留当前字节，不回滚、不纳入源码提交，不覆盖原验收身份。原34最终检查及保留证据身份/源码patch复用，本轮不重跑已验收功能或重复Completion。实际提交及路径/blob/工作树核对见local/submit-receipt.json；local/.agent不由普通commit备份。下一单元仅沿TASK_QUEUE#crp-next，无push/M2推进。可在当前对话继续：本对话恢复材料完整，尚未累积长调试，下一项与当前SDL轮询链相连。
