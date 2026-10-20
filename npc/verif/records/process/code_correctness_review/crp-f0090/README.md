# CRP F0090 — NDL 事件错误与初始化生命周期

## 整体计划及启动（2026-10-20）

用户“继续CRP修复”授权沿唯一队列执行一个单元。Guard：前组F0087已确认并提交根aee3a0bc01ffbd72e3a3dfefb2a9067e88b3437e，根working tree/index干净；本轮不恢复旧连续提交授权，不提交/push/安装，不推进M2。nested libc既有850 mode差异按原约定保留。

目标/范围：F0090，仅NDL初始化、退出和事件返回，以及libam必要的失败传播；miniSDL已有SDL_Init直接返回NDL_Init结果，无需新增接口。正常Make/update→run、设备路径、flags忽略、音频及NWM绘图协议不变。F0091绘图边界/握手失败策略、全POSIX和native设备模拟器生命周期不扩修。

一个独立单元，顺序为原版见证→最小修改与定向验证→实际RV64生命周期及受控缺设备验证→最终Navy update→run三前台/hello→完整diff归档/目视/清理/状态收尾。交付为必要源码补丁、正文完整diff及语句说明、命令/结果/身份/限制和records索引；统一收尾后停止等待结果确认及commit。

失败契约从现有调用推导：NDL_PollEvent被SDL和libam按布尔值消费，只能正read报1，失败/未初始化/退出后报0；NDL_Init与SDL_Init返回int，成功0失败-1；libam ioe_init返回bool，传播false。重复有效Init幂等，Quit关闭有效fd并清零屏幕/画布状态；失败不发布半初始化状态，可在设备恢复后重试。临时dispinfo fd在所有已打开路径关闭；NWM继承事件fd3在成功前不转交给NDL，失败只关闭本次open资源，成功后的Quit延续原close3行为。事件文本留NUL空间供现有字符串消费者使用；不引入新错误码/errno或改SDL队列。

验收：原版负read/失败Init/重复Quit动态见证；host覆盖所有open/read失败点、空/有效事件、缓冲边界、重复init/quit/失败重试与NWM fd分支，sanitizer；实际RV64不stub NDL或libc的受控缺设备、读失败与生命周期消费者，正常及错误判据；最终现有nanos目录update→run，三前台真实输入及后台hello，源码→库→链接/安装/盘身份；完整diff正反应用和实际目视，结束进程再清理可再生副本。CPU/RT不消费Navy NDL，按影响不重跑；NPC/native NWM/实体AV/长时不声称已测。遇真实范围或策略裁决/安装即停。

参考：2026-10-20读取[ICS-PA应用程序章节](https://ysyx.oscc.cc/docs/ics-pa/3.5.html)，其将NDL作为miniSDL底层支持；具体失败传播以本地NDL.h/SDL_Init/ioe_init及nanos fs返回契约为准，不把当前2025版讲义当项目历史实现版本。

## 实施结果 — Completed，结果确认/根commit Pending

生产仅根仓`navy-apps/libs/libndl/NDL.c`和`navy-apps/libs/libam/src/ioe.c`，37增18删（含libam原末尾补换行）。F0090完成；累计70已修/49未修完，前69已确认提交，本组确认/commit Pending。没有改变NDL函数签名、Make接口、nanos文件系统或退出语义。

| 验收 | 本轮实际结果及local入口 |
|---|---|
| 原版动态见证 | 从入口完整commit提取原NDL，实际链接SDL_Init包装；负read误报、open失败仍0、第二次Quit重复close，三个进程均在对应契约断言处exit1。unit/before-{negative,fail1,quit}.log及unit-results，不把编译/工具失败当反例 |
| host最终 | 14类场景×普通GCC/ASan+UBSan，各113断言通过；全部3个open失败点、显示read负值/空/格式缺失/零尺寸、负/空/有效事件、未初始化/退出后调用、无效buf/长度/小缓冲、native snprintf长返回、重复init/quit及失败重试，含NWM继承fd3成功/失败所有权分支。libam-host另验证失败false且不调用OpenCanvas，恢复true。LSan在本沙箱ptrace下不能运行，最终detect_leaks=0；fd所有权另以mock live计数验证，非堆泄漏证明 |
| 实际RV64 | 六次真实NDL→libc/libos→ecall→nanos：normal、missing-event/dispinfo/fb、read-dispinfo/event均exit0/GOOD，四Init失败由实际ioe_init传播false，再SDL_Init重试成功。三处缺设备在隔离fs_open单次把目标路径改成实际不存在路径，走原查找失败；两处read在隔离fs边界单次返回-1，不stub NDL/SDL/libc。其余调用真实执行，SDL_Init重复成功、三轮ioe_init/Quit及未初始化/退出后Poll均通过。guest.c、prepare-guest/run-guest、guest-results与六run日志 |
| RV64资源观测 | 每例只读events两次；正常/事件read失败各4次显示read，missing-event/dispinfo亦4次，missing-fb/显示read失败5次。关闭events正常4次、三个已打开event的部分Init失败5次；关闭dispinfo与其成功open次数相同；每例fb恰关闭4次。第二次Init不额外open，第二次Quit/退出后Poll无额外close/read；不把nanos fs_close重置offset当真实POSIX fd分配/回收 |
| 标准最终消费者 | 新源复制入隔离原有nanos目录，现有`make -j4 ARCH=riscv64-nemu git_commit= update`最终exit0/17.557秒（初次完整构建27.133秒；补native长度保护后再标准update）；随后同目录`run`54.652秒，10条真实SDL键输入/8帧目视通过，PAL→NTerm输入qzx并返回prompt→slide0/1/0→PAL/Enter；后台hello34→148。slide0回归帧SHA完全恢复。自有进程组SIGTERM/make-15为观察结束，非guest正常退出。standard-path/update-combined-result及nanos/result/observe/guest日志 |
| 判据/版本/归档 | 六种非零/缺标记/错退出码/重复标记/混BAD/非法read的oracle变异均拒绝；最终two-source SHA、原编译命令、库成员/对象、真实链接=安装=盘extent、108唯一连续extent及正式输入保护核对；正文完整diff正反应用精确。具体终检和清理见下方结果与local记录 |

实际RV64每次成功后取得800×600画布；不是把host模型的400×300硬套到设备配置。诊断只在隔离内核SYS_exit边界将main返回值打印并halt；标准消费者内核不注入fail/log/halt。标准盘中无f90目标，诊断仅在另一个盘尾附加目标及文件表条目，保持标准盘字节不变。

夹具更正如实保留：最初host宏包装被系统FORTIFY重定向到原open/read，关闭本次host编译的FORTIFY后才运行有效夹具；ccache只读通过进程CCACHE_DISABLE=1避开，不安装/更改系统。第一次诊断run遗漏NAVY_HOME，错误读到正式盘并因盘尾越界在加载前被拒绝；第二次使用正确隔离盘但误设画布400×300，实际配置800×600使断言失败。两次失败均非产品通过，原日志/结果/旧测试源在fixture-corrections；修正环境和预期后六例重新执行，再补实际read计数后最终六例重验。正式资产SHA复核保持；没有写入正式盘。

## 实现边界、未测与恢复

`NDL_PollEvent`先拒绝无效buf/长度，再清空首字节；fd无效或缓冲仅一字节时不read，read非正值统一返回0，仅正值报事件。保留一字节NUL，按实际read返回位置终止；native模拟器返回snprintf逻辑长度时，把终止位置限制到len-1。正常短文本格式不改，不替SDL增加新队列/截断协议。

`NDL_Init`用局部event_fd/fbctl/framebuffer_fd收集资源，event/dispinfo/fb任一点失败、显示read非正或超范围、缺少正尺寸都返回-1；fbctl读完立即关闭，失败仅关闭本次open成功的event。成功后才将event/fb及尺寸发布到静态状态；已有效Init直接0，避免重复open泄漏。NWM fd3继承路径在成功前不由失败清理关闭，成功后Quit延续原关闭行为；未执行NWM OpenCanvas握手、未解决其帧缓冲覆盖/错误循环等独立F0091范围。flags继续忽略。

`NDL_Quit`只关闭非负fd，随即将event/fb置-1、四尺寸置0；重复Quit不再操作旧fd。libam `if (NDL_Init(0) != 0) return false`让失败在OpenCanvas之前返回，成功逻辑保持；SDL_Init原来已直接透传结果，不改。直接忽略NDL_Init结果的既有应用不扩改，失败后Poll返回0，不宣称它们都有错误界面或恢复逻辑。

本轮不修绘图参数/F0091、音频fd/SDL音频、任意恶意显示文本整数溢出、NWM握手/IPC或native模拟器资源重开语义。native libos的open返回共享静态伪fd，NDL关闭后并不会由open重新创建底层资源；本轮host覆盖NDL分支，不声称真实native反复退出/重开已验证或已修。CPU/RT/REF不依赖Navy NDL，按影响不重跑；NPC/其他ISA/真实NWM/实体AV/长时NotRun。正式F0074盘/头/内核/NEMU/配置保持；本轮运行使用隔离副本，标准run重新构建其自身NEMU，二者hash分别记录，不混作同一文件。

复现从入口完整commit加本组repair.patch恢复新源码，使用entry保护输入/已存在外部资源和工具，依次unit.py、prepare-runtime.py、update-final.py、standard-path/run-standard.local nanos、prepare-guest.py、run-guest.py、visualize.py、archive.py、check.py，实际目视后cleanup.py/final-check.py。隔离准备不下载；正式镜像/资源仍按F0074配方与入口身份恢复。一次性测试源、命令/日志/JSON和补丁本地保留，不批量提交；local/.agent不由普通commit备份。


## 最终收尾与停点

228项preclean全PASS，4975份源码/配置及913份构建产物身份已保存；libam ioe.o按原Make规则重编字节完全相同，核实诊断六次所用实际对象。完整diff已内嵌并正反应用逐字节核对，8帧实际目视后删除。最终清理9635项510367465逻辑字节（约486.7MiB），零tracked删除，仅本组隔离源码/构建/诊断盘/host二进制/截图，正式F0074资产未动。路径/大小/SHA见local/cleanup-plan及cleanup-receipt，原身份记录保留，缺失为预期清理；已删除的截图/盘不能再直接查看。最小测试源、实际命令/结果/日志/身份和patch保留，工具故障与错误配置不计验收。

CURRENT_STATE/TASK_QUEUE与逐项台账及process索引同步。F0090 Completed但结果确认/commit Pending；Working tree contains uncommitted CRP repair/documentation changes。根HEAD仍aee3a0b，双index空；nested libc8101fad内容不变/850原mode保持。唯一后续入口TASK_QUEUE#crp-next，未来F0092未Start，须先完成本组确认及commit；本轮不自动提交/push/下一组/M2。

<a id="repair-diff"></a>
## 最终代码diff与语句说明

根仓，旧完整commit `aee3a0bc01ffbd72e3a3dfefb2a9067e88b3437e`；新版本 `WORKTREE（2026-10-20，未提交）`，相对路径/新SHA256：

- `navy-apps/libs/libndl/NDL.c`：`ee65b9521e14e2139672dde077f3245031512ef6465fe266f6f7a6dd20af53ec`
- `navy-apps/libs/libam/src/ioe.c`：`e5e13eff1ff24fbbb494cff57b20be29cf1f5e8f2a24b26338589220e4f0b16f`

全部实际修复hunk如下，语句/失败收尾/所有权与调用链说明见上方“实现边界”。旧源取本批修复前的根commit，新源为本轮已验收工作树；隔离目录正向应用逐字节等于新源，反向逐字节恢复旧源。libam原无末尾换行的差异如实保留。新增报告的6条空白检查告警逐条确认均为本diff空上下文行的单个前缀空格，按归档规则保留原字节；正文/新增代码无对应尾随空白，核验见local/whitespace-review。

```diff
diff --git a/navy-apps/libs/libam/src/ioe.c b/navy-apps/libs/libam/src/ioe.c
index fc68fff105e65848a0cfa139fb53c3e6ed15ea0d..4f08f22fa01895e31fbeef02675fbabca9aa5554 100755
--- a/navy-apps/libs/libam/src/ioe.c
+++ b/navy-apps/libs/libam/src/ioe.c
@@ -21,7 +21,7 @@ static int name_to_keycode(const char *name, int len) {
 }
 
 bool ioe_init() {
-  NDL_Init(0);
+  if (NDL_Init(0) != 0) return false;
   NDL_OpenCanvas(&screen_w, &screen_h);
   return true;
 }
@@ -84,4 +84,4 @@ void ioe_write(int reg, void *buf) {
       NDL_DrawRect((uint32_t *)fb->pixels, fb->x, fb->y, fb->w, fb->h);
     }
   }
-}
\ No newline at end of file
+}
diff --git a/navy-apps/libs/libndl/NDL.c b/navy-apps/libs/libndl/NDL.c
index 3a2b1e8c52763f4dc125564e4cfec67c5887f376..7a908f298c1e518b61219fe849a6eefcd3533252 100755
--- a/navy-apps/libs/libndl/NDL.c
+++ b/navy-apps/libs/libndl/NDL.c
@@ -10,7 +10,6 @@
 
 static int evtdev = -1;
 static int fbdev = -1;
-static int fbctl = -1;
 static int screen_w = 0, screen_h = 0;
 static int canvas_w = 0, canvas_h = 0;
 static struct timeval timevar = {};
@@ -21,7 +20,14 @@ uint32_t NDL_GetTicks() {
 }
 
 int NDL_PollEvent(char *buf, int len) {
-  return read(evtdev, buf, len) ? 1 : 0;
+  if (buf == NULL || len <= 0) return 0;
+  buf[0] = '\0';
+  if (evtdev < 0 || len == 1) return 0;
+  int nread = read(evtdev, buf, len - 1);
+  if (nread <= 0) return 0;
+  // The native device shim may return snprintf's untruncated length.
+  buf[nread < len ? nread : len - 1] = '\0';
+  return 1;
 }
 
 void NDL_OpenCanvas(int *w, int *h) {
@@ -96,34 +102,47 @@ int NDL_QueryAudio() {
 }
 
 int NDL_Init(uint32_t flags) {
-  if (getenv("NWM_APP")) {
-    evtdev = 3;
-  }
-  else {
-    evtdev = open("/dev/events", 0, 0);
-  }
-  fbctl = open("/dev/dispinfo", 0, 0);
+  if (evtdev >= 0 && fbdev >= 0) return 0;
+  int nwm = getenv("NWM_APP") != NULL;
+  int event_fd = nwm ? 3 : open("/dev/events", 0, 0);
+  if (event_fd < 0) return -1;
+  int fbctl = open("/dev/dispinfo", 0, 0);
+  if (fbctl < 0) goto fail;
   char buf[128];
   int nread = read(fbctl, buf, sizeof(buf) - 1);
-  buf[nread > 0 ? nread : 0] = '\0';
+  close(fbctl);
+  if (nread <= 0 || nread >= sizeof(buf)) goto fail;
+  buf[nread] = '\0';
+  int width = 0, height = 0;
   // format: "WIDTH : <w>\nHEIGHT:<h>\n", whitespace around ':' is flexible
   // (see navy-apps/README.md)
   const char *p = strstr(buf, "WIDTH");
   if (p != NULL) {
     p = strchr(p, ':');
-    if (p != NULL) { p ++; while (*p == ' ' || *p == '\t') p ++; screen_w = atoi(p); }
+    if (p != NULL) { p ++; while (*p == ' ' || *p == '\t') p ++; width = atoi(p); }
   }
   p = strstr(buf, "HEIGHT");
   if (p != NULL) {
     p = strchr(p, ':');
-    if (p != NULL) { p ++; while (*p == ' ' || *p == '\t') p ++; screen_h = atoi(p); }
+    if (p != NULL) { p ++; while (*p == ' ' || *p == '\t') p ++; height = atoi(p); }
   }
-  close(fbctl);
-  fbdev = open("/dev/fb", 0, 0);
+  if (width <= 0 || height <= 0) goto fail;
+  int framebuffer_fd = open("/dev/fb", 0, 0);
+  if (framebuffer_fd < 0) goto fail;
+  evtdev = event_fd;
+  fbdev = framebuffer_fd;
+  screen_w = width; screen_h = height;
   return 0;
+
+fail:
+  // NWM's inherited event pipe is only adopted after successful initialization.
+  if (!nwm) close(event_fd);
+  return -1;
 }
 
 void NDL_Quit() {
-  close(evtdev);
-  close(fbdev);
+  if (evtdev >= 0) close(evtdev);
+  if (fbdev >= 0) close(fbdev);
+  evtdev = fbdev = -1;
+  screen_w = screen_h = canvas_w = canvas_h = 0;
 }
```


<a id="submit-20261020"></a>
## 2026-10-20 用户确认与提交回执入口

用户“提交”确认F0090已报告范围并授权精确根提交。本轮复核103项保留manifest身份、228项preclean与9672项既有终检（含逐路径清理核对）、两源已验收patch/正式输入及nested状态无漂移；复用原功能验收、完整diff归档和清理，不重复动态测试或Completion。仅两生产源、本组README/.gitignore及process/repair-status六路径纳入提交，local/.agent仍为忽略资料，不宣称由commit备份。

前文Pending及WORKTREE保留为完成时截面；本次用户确认及实际提交以本附记所处修复提交和local/submit-precheck、submit-staged、submit-receipt及CURRENT_STATE为准。提交前不虚构自身完整hash，实际提交后核对六路径/mode/blob及两源diff与已验收patch相同，再保存真实hash和工作树结果；不改变真实native/NWM未测限制。本轮仅提交，完成后停止，不启动F0092、不push。

会话建议：可在当前对话继续；本对话只完成F0090，下一项仍属SDL事件调用链，且唯一入口与恢复资料完整。建议不改变确认/commit或后续执行授权门槛，不另造启动Prompt。
