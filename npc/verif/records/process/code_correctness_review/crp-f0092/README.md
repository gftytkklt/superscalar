# CRP F0092 — miniSDL事件入队边界

## 整体计划与启动（2026-10-20）

用户“继续”授权沿TASK_QUEUE#crp-next执行一个单元；Guard核对前F0090根9251511bffb9205403d2e33b8de55a657cd340d7、根working tree/index干净，与当前状态一致；nested libc8101fad/850原mode保持。旧连续提交授权不恢复，不commit/push/安装或推进M2。

目标/范围：仅修libminiSDL/src/event.c的事件入队边界，所有入队路径在修改队列/keystate前验证type及按键sym。键值0(NONE)至82沿用合法范围；键值83/255拒绝，USEREVENT不按键值检查；仅接受sdl-event.h现有声明的KEYDOWN/KEYUP/USEREVENT。PushEvent原成功1/失败0、ADDEVENT逐项计成功数量保持，拒绝项不发布队列或改keystate。既有NULL/full行为、FIFO/peek/get/remove、mask、借用用户data指针及NDL文本输入格式保持；不新增SDL事件能力、定时器/音频或全SDL兼容承诺。

一个独立单元，依次原版动态反例→最小修复/host定向→实际RV64 API消费者→最终标准Navy update→run三前台/hello→正文完整diff正反应用/目视/产物清理与状态收尾。交付为一个生产源补丁、本报告完整diff/逐句说明、真实命令/结果/同版身份、records索引和唯一下一入口。

验收：原生产源码sym255数组越界与type32进入mask移位的UBSan明确反例；修复后普通GCC与ASan/UBSan覆盖sym0/82/83/255及type2/3/31/32/255、Push/ADDEVENT拒绝前无副作用、混合合法/非法批次成功数、满256队列及环绕FIFO、选择peek/get/remove/keystate保持、用户payload借用、正常NDL事件/Wait/Poll；实际RV64链接真实miniSDL/NDL/libc执行相同API用例，按main实际返回/GOOD判定，原内核生产退出语义不改。最终同版标准update→run三前台及后台hello；源码/对象/库/真实链接=安装=盘、正式F0074资产保护；完整diff正反应用，实际目视后再清理。

正常停点：本组全部收尾后停止，等待用户确认及commit，不自动下一组。真实未决契约或安装即停；现有声明和调用足以确定上述失败契约，无新人工策略裁决。CPU/RT/REF不消费Navy miniSDL不重跑；NPC/其他ISA/真实native/NWM/实体AV/长时不宣称已验收。测试夹具/原始证据本地忽略，不批量提交。

参考：本对话已读取[ICS-PA应用程序章节](https://ysyx.oscc.cc/docs/ics-pa/3.5.html)，NDL支撑miniSDL的层次与本地调用一致；具体事件集合、返回值和键值范围以当前sdl-event.h/event.c为准，不从讲义推定完整SDL特性。


## 实施结果 — Completed，结果确认/commit Pending

仅根仓`navy-apps/libs/libminiSDL/src/event.c`一源5增2删，无声明/Make/定时器/音频修改。F0092完成，累计71已修/48未修完；前70已确认提交，本组结果确认/根commit Pending。

| 验收 | 本轮实际结果/证据 |
|---|---|
| 原版明确反例 | 入口完整commit的生产event.c链接host NDL空输入与CallbackHelper桩，sym255在原24行触发index 255 out of bounds for uint8_t[83]；type32先Push成功，再Peep筛选在原52行触发shift exponent 32。UBSan非恢复模式两次exit1，非编译/工具失败。unit/before-sym/type.log及unit-results |
| 最终host | 普通GCC及ASan/UBSan各1108断言通过；sym0/82合法、83/255的DOWN/UP通过Push/ADDEVENT均拒绝，type3/31/32/255拒绝，已有user事件/keystate保持；混合批次仅3合法项入队，选择GETUSER后保留键事件顺序，出队不回滚keystate。256满队列拒绝且不改状态，出129/再入129验证环绕FIFO及借用payload；NULL、peek/get/Wait/queued Poll保持。额外host真实fetch_ndl解析kd A并仅报告一次；NDL输入源为桩，实际正常输入另由标准guest覆盖。LSan因本沙箱已知ptrace限制关闭，ASan/UBSan启用；本修复不分配堆内存，不据此声称通用泄漏验收 |
| 实际RV64 API | 与host相同api-cases.h链接真实miniSDL/NDL/libc/libos，先真实SDL_Init成功，再完成1108断言，实际main返回0经CRT到SYS_exit，诊断NEMU exit0/GOOD。没有stub目标API；仅隔离内核SYS_exit边界记录main码并halt，不改变生产退出重启语义。guest-builds/guest-results、guest-run.log及guest.c/prepare-guest/run-guest；六种非零/缺PASS/错断言数/错退出码/重复PASS/混BAD判据变异均拒绝 |
| 最终标准入口 | 新源经隔离原nanos目录`make -j4 ARCH=riscv64-nemu git_commit= update`exit0/27.483秒，再同目录`run`54.652秒；PAL→NTerm输入qzx并返回prompt→slide0/1/0→PAL/Return继续，10次真实SDL队列键输入、8帧已目视，hello33→155；slide0返回SHA精确恢复。自有进程组SIGTERM/make-15仅表示有限观察结束，不是guest正常退出。standard-path/update-final-result及nanos/result/observe/guest日志 |
| 同版与归档 | 完整diff正反应用精确；最终源/对象/库、实际链接=安装=108个唯一连续盘extent、正式F0074输入保护及nested身份核对；具体preclean/源码产物身份和清理记录见local。诊断目标仅追加在独立盘，标准盘/header不含f92目标，不混用两种结果 |

## 语句实现、边界与未测

`push_event`是PushEvent、Peep ADDEVENT和NDL解析入队的共同入口。先沿用满队列返回0，再以`ev->type > SDL_USEREVENT`拒绝声明集合外的值；当前枚举连续为0/1/2，type为uint8_t，因此3及以上均在复制/移动游标之前返回。随后仅对KEYDOWN/KEYUP检查`sym >= NR_KEYS`，user payload不按键值解释。两项验证都在`ev_queue[ev_tail] = *ev`、tail/count递增和keystate写入之前，拒绝不会留下半个事件或改变按键状态。

验证通过后沿用原复制和FIFO发布顺序，按键状态直接索引已经证明小于83的sym，删去不能保证边界的`& 0xff`。NONE=0依旧可入队，不擅自变成无效键；USEREVENT的code/data1/data2原样借用，不复制或释放指向对象。所有进入队列的type均小于3，`find_matching`中的EVENTMASK移位不再消费外部非法type；宏自身被外部直接传非法值仍不属本修复保证。

`SDL_PeepEvents(ADDEVENT)`仍逐项调用push_event并累计成功数：混合合法/非法输入允许合法项成功，非法项被跳过，不把整个批次改成原子事务。满队列停止扫描、peek不消费、GET按mask移除且不回滚已记keystate均保持。没有改SDL错误值体系、事件union/API布局或新建事件类型；不存在新增生产Make参数/日常步骤。

CPU/RT/REF不依赖Navy miniSDL，按影响不重跑；NPC/其他ISA/真实native/NWM/实体音视频/长时NotRun，有限SDL dummy观察不代表全游戏或人工显示验收。定时器F0093、音频、F0091绘图及其他独立问题保持未修，不从本组Poll/Wait通过推定它们正确。正式F0074盘/头/内核/NEMU/配置不改；标准run按原规则构建隔离NEMU，身份与正式二进制分别记录。

## 恢复与停点

从旧完整commit加本组repair.patch得到最终源；按entry/F0074配方准备已有资源/工具（不下载/安装），运行unit.py→prepare-runtime.py→standard-path/run-standard.local nanos→prepare-guest.py→run-guest.py→visualize.py→archive.py→check.py，实际目视/完整diff归档后cleanup/final-check。保留必要最小测试源、实际命令/结果/身份与补丁，local/.agent不随普通commit备份；最终可再生盘/ELF/截图/源码副本按用户规则删除，不宣称旧图仍可直接查看。

本组统一收尾后停止，等结果确认和精确commit，不启动下一组/push/M2。未来范围、资料/门槛及验收仅在TASK_QUEUE#crp-next，不另造第二份Next。


## 最终收尾

166项preclean及33项最终收尾检查全部通过，4891份源码/配置及849份构建产物身份保存。实际目视和完整diff正反应用核对后，删除9390项507075380逻辑字节（约483.6MiB）的隔离源码/构建/盘/ELF/host二进制及截图，零tracked删除；路径/大小/SHA及预期缺失见local/cleanup-plan、cleanup-receipt。原身份记录保留，不把已清理截图或诊断盘宣称为仍可直接查看；正式F0074输入全部保持。

记录索引、逐项台账、CURRENT_STATE/TASK_QUEUE及完成快照同步。Working tree contains uncommitted CRP repair/documentation changes；根HEAD仍9251511，双index空，nested8101fad内容不变/850原mode保持。71已修/48未修完，本组结果确认/commit Pending。单元后停止，未来F0093未Start，仍沿TASK_QUEUE唯一入口；没有提交/push/下一组/M2推进。

<a id="repair-diff"></a>
## 最终完整diff与版本身份

根仓，旧完整commit `9251511bffb9205403d2e33b8de55a657cd340d7`，相对路径 `navy-apps/libs/libminiSDL/src/event.c`；旧源SHA256 `6d3965b3d0f3c5252fd1b312dc9ed6378e18af888b378a749a9f3890767beab9`；新源为 `WORKTREE（2026-10-20，未提交）`，SHA256 `67ad1573c6ca7b02804ebe0b9d84833f44a72d95f9f909934f8ae2b32d7fbd58`。逐句/调用链与失败状态说明见上文。临时目录正向应用逐字节等于最终源，反向逐字节恢复旧源；保留完整上下文及原无末尾换行状态。报告的两条尾随空白告警均逐条核对为diff空上下文行的一个前缀空格，按归档要求保持补丁字节；正文/新增代码无此问题，见local/whitespace-review。

```diff
diff --git a/navy-apps/libs/libminiSDL/src/event.c b/navy-apps/libs/libminiSDL/src/event.c
index 9291467535c26d27bbefa9991040d92b77a571dc..998aa8236525371d7233ab4b43e25ced745d9765 100755
--- a/navy-apps/libs/libminiSDL/src/event.c
+++ b/navy-apps/libs/libminiSDL/src/event.c
@@ -18,11 +18,14 @@ static uint8_t keystate[NR_KEYS];
 
 static int push_event(SDL_Event *ev) {
   if (ev_count == MAX_EVENTS) return 0;
+  if (ev->type > SDL_USEREVENT) return 0;
+  if ((ev->type == SDL_KEYDOWN || ev->type == SDL_KEYUP) &&
+      ev->key.keysym.sym >= NR_KEYS) return 0;
   ev_queue[ev_tail] = *ev;
   ev_tail = (ev_tail + 1) % MAX_EVENTS;
   ev_count ++;
-  if (ev->type == SDL_KEYDOWN) keystate[ev->key.keysym.sym & 0xff] = 1;
-  else if (ev->type == SDL_KEYUP) keystate[ev->key.keysym.sym & 0xff] = 0;
+  if (ev->type == SDL_KEYDOWN) keystate[ev->key.keysym.sym] = 1;
+  else if (ev->type == SDL_KEYUP) keystate[ev->key.keysym.sym] = 0;
   return 1;
 }
 
```


<a id="submit-20261020"></a>
## 2026-10-20 用户确认与提交回执入口

用户“提交，继续”确认F0092已报告范围并授权精确提交后执行唯一下一单元。本轮52保留身份、166preclean/33最终检查、单源patch/正式输入/nested状态核对复用，不重跑功能验收、不重复Completion。仅event.c、本组README/.gitignore及process/repair-status五路径纳入，local/.agent继续忽略，不宣称由commit备份。

前文Pending/WORKTREE是完成时截面；实际提交以本附记所处根提交和local/submit-precheck、submit-staged、submit-receipt及CURRENT_STATE为准。实际提交后核对路径/mode/blob/验收patch和根/index干净，再保存完整hash；不虚构自身提交hash或把未测能力改成通过。提交后仅沿用户同句授权执行F0093一个单元，不push或恢复旧连续提交授权。

会话建议：可在当前对话继续；本组恢复材料完整，下一项仍属SDL轮询调用链，当前授权和停点明确，不增加新审批或启动Prompt。
