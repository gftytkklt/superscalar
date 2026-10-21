# CRP F0110 — NWM初始状态与控制管道EOF必要分析

## 整体计划（2026-10-21）

来源：用户“继续”；前组F0107/F0108已确认，根9747db89010dd89e30ee76c10c25c21e270dd777、ONS5e72dbb9739ae39a3a2dc520ed89f20219e92f84已提交。沿TASK_QUEUE#crp-next只执行本F0110必要分析单元，M2不变。根树/index干净；ONS既有DEFAULT_ENV_FONT编码行保持，与本组无关。

目标与范围：核对Window构造/首次update/resize/析构、WindowManager窗口/焦点/事件调用链，以及NDL尺寸握手和关闭语义；用原版正常/失败见证确定最小修复边界。保留Robustness/Low原分类，不把当前RV64缺IPC/mmap服务当本批已获授权的新能力。

本单元阶段：原版身份与静态调用链→隔离host原版真实pipe/fork/memfd/mmap及精确NDL握手函数见证→最小方案/策略冲突分析→证据清理、结果/索引/状态与唯一入口。交付本报告、本地最小配方/日志/退出码/源码与正式资产身份/清理回执；不保存再生二进制或生产源码副本。

验收：明确初始化缺口、EAGAIN与真正EOF区别、首次映射正常路径、NDL正常关闭控制管道时子进程是否仍存活；正向/反例不得以编译通过替代。隔离夹具只替换非目标绘制管理环境，完整生产window.cpp及提取的NDL_OpenCanvas注明范围，不冒称完整host GUI或RV64 guest已通过。读取函数/pipe的公开规范作依据，访问失败如实记录。

停点与人工项：若EOF关闭窗口与现行NDL握手后close(4)冲突，先提出最少契约裁决，不擅自更改协议/默认应用流程或决定删除/冻结窗口。软件安装、扩RV64 IPC/mmap、系统改动均需人工，本轮不执行。此单元无安装依赖；没有生产修改、commit/push或下一单元授权。完成后停下等待真实未决项裁决，分析文档未提交不另设实施前置门槛。

## 用户裁决与实施补充（2026-10-21）

原版五个隔离见证已明确初始状态/空映射/EOF问题，也证明NDL正常握手后close(4)时子进程仍存活；“遇EOF删除窗口”会改变现有协议。用户在明确两选项后选择“按最小范围修复（推荐）”：只改初始化、空映射释放、EOF循环，保留现有窗口生命周期。该选择授权同一单元直接实施/验证，无需先提交分析文档；不是授权扩子进程退出检测、pipe重构或RV64能力。

实施范围只含window.cpp：fw/fh/dx/dy确定为0；有实际fb才munmap；nread<=0结束当前读取循环；仅在canvas/fb均有效时复制/刷新。正数尺寸的首次/再次映射、正常NDL握手及持续绘制保持。短消息/坏尺寸、ftruncate/mmap/write失败、pipe端点/fd覆盖/fork失败、窗口/焦点退出回收仍不在本次支持范围，不因本批消除两个根因就宣称全部IPC安全。

验收补充：原版正常/失败对照，新版host普通及ASan/UBSan针对未握手、首次/再次resize、EAGAIN/EOF、正常客户端close(4)及之后绘制；尽可能真实完整native compositor消费，标准native构建失败与临时host直接编译须区别。只修改NWM私有应用，CPU/RT/nanos默认应用不依赖，不重跑无关guest；RV64先有既存IPC/mmap能力断点，不用host代替RV64验收。完整diff与语句说明、旧HEAD重建/正反应用/源码身份、正式资产保持、清理与状态留档后停止，结果确认/commit另计。


## 原版见证与协议核实

基线为根`9747db89010dd89e30ee76c10c25c21e270dd777`；window.cpp SHA256 `a7e1e789956d36e32b894c0329cee7f37c640abb44405dbdd5061281c3131f86`，与原P8定位的a7e1e789…一致。local/probe.py使用完整生产window.cpp/实际BDF源；WindowManager仅提供字体/mark_dirty的最小环境，非完整合成器。Window对象底层存储预填字节，只比较未设置字段的对象表示；真实pipe2/fork/execve/memfd/mmap/read/close未替换。munmap观察wrapper调用真实宿主实现；关闭父进程保留的写端只在夹具中暴露EOF，不改生产pipe生命周期。

| 原版场景 | 结果与边界 |
|---|---|
| 构造/子进程退出后 | fw/fh/dx/dy的16字节仍全为预填0x01；子进程已waitpid确认退出，父进程read仍为EAGAIN=11，证实保留写端掩盖EOF |
| 首次未握手update | 同样预填条件下SIGSEGV/-11；canvas/fb为空，原update仍按未初始化fh进行复制。预填只使已有未初始化缺陷稳定可见，不声称默认堆布局必崩 |
| 首次2×2、再3×2映射/复制/析构 | 正常像素可复制，但首次多一次munmap(NULL,0)；再次resize及析构各有一次有效unmap |
| 真正EOF | 夹具关闭父端保留writer并实际read==0后，原update持续不返回；0.6秒自有进程组SIGTERM/-15，不是应用正常退出 |
| 精确NDL_OpenCanvas客户端 | 从当前NDL.c逐字提取函数，真实写尺寸/读mmap ok/close(4)，函数返回后子进程仍存活；父端暴露EOF，实际read==0。证明尺寸通道EOF不是应用退出信号 |

五次运行及两次编译原命令/退出码在commands.json，各log保留。没有给原代码注入EOF返回桩或改它的解析/绘制函数。NDL客户端只提取OpenCanvas并设定已有设备状态，不覆盖完整NDL_Init。

阅读[ICS-PA4.3](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)与[4.4](https://ysyx.oscc.cc/docs/ics-pa/4.4.html)（2026-10-21）未发现NWM生命周期的明确约定，不据此宣称课程必须回收窗口。Open Group两个版本read/pipe页面均403；补查[Linux man-pages项目pipe(7)源](https://kernel.googlesource.com/pub/scm/docs/man-pages/man-pages/+/master/man/man7/pipe.7)：管道没有消息边界，全部writer关闭才read==0、有writer而空管道的非阻塞read为EAGAIN。项目现行NDL.c的close(4)才是本次保留窗口的直接依据；规范不替项目决定窗口何时删除。

## 最小修复与代码语句

用户已明确选择最小范围，F0110两项缺陷在该契约内修复，窗口退出回收并非本次交付。改动只有window.cpp，9增8删：

- 构造的连赋值增加fw/fh/dx/dy，第一次读取前尺寸/偏移为0；canvas和fb仍明确为nullptr。
- resize与析构只在fb存在时munmap，首个resize和未握手销毁不传入空映射；正常重映射仍用旧fw/fh长度释放旧映射，fd按原路径关闭。
- `nread <= 0`结束本次do/while：EOF不再被当空串无限解析，原负返回同样退出。没有把EOF解释为应用退出，也不关闭窗口/改焦点。
- canvas和fb均存在时才逐行memcpy/draw；尚未握手/EAGAIN没有无效复制，已有帧在EOF后仍可复制显示。没有改变尺寸消息、ack内容或客户端流程。

旧完整commit如上，新源为2026-10-21未提交工作树，SHA256 `d5b1d6e133e36587e69b47b9d990ead7c6317d5c078e3169bfb556438c9135a5`；实际完整diff如下，local/repair.patch字节一致。archive-validation.json从旧Git blob正向应用逐字节得到新源，再反向恢复原blob；复现旧源从Git重建，未保留整份生产源码快照。

```diff
diff --git a/navy-apps/apps/nwm/src/window.cpp b/navy-apps/apps/nwm/src/window.cpp
index 8a6e85d..4a6dec2 100755
--- a/navy-apps/apps/nwm/src/window.cpp
+++ b/navy-apps/apps/nwm/src/window.cpp
@@ -52,7 +52,7 @@ void Window::draw() {
 
 Window::Window(WindowManager *wm, const char *cmd, const char * const *argv, const char **envp) {
   this->wm = wm;
-  x = y = w = h = 0;
+  x = y = w = h = fw = fh = dx = dy = 0;
   canvas = nullptr;
   fb = nullptr;
 
@@ -124,7 +124,7 @@ void Window::resize(int width, int height) {
     canvas = nullptr;
   }
 
-  if (fbdev_fd != -1) munmap(fb, fw * fh * sizeof(uint32_t));
+  if (fbdev_fd != -1 && fb) munmap(fb, fw * fh * sizeof(uint32_t));
 
   if (has_titlebar) {
     this->w = width + border_px * 2;
@@ -184,7 +184,7 @@ Window::~Window() {
     canvas = nullptr;
   }
   if (fbdev_fd != -1) {
-    munmap(fb, fw * fh * sizeof(uint32_t));
+    if (fb) munmap(fb, fw * fh * sizeof(uint32_t));
     fb = nullptr;
     close(fbdev_fd);
     fbdev_fd = -1;
@@ -203,16 +203,17 @@ void Window::update() {
     do {
       char buf[64];
       int nread = read(read_fd, buf, sizeof(buf) - 1); // this a non-blocking read
-      if (nread == -1) break;
+      if (nread <= 0) break;
       buf[nread] = '\0';
       int w, h;
       int ret = sscanf(buf, "%d %d", &w, &h);
       if (ret == 2) resize(w, h);
     } while (1);
-    int y;
-    for (y = 0; y < fh; y ++) {
-      memcpy(&canvas[(dy + y) * w + dx], &fb[y * fw], fw * sizeof(uint32_t));
+    if (canvas && fb) {
+      for (int y = 0; y < fh; y ++) {
+        memcpy(&canvas[(dy + y) * w + dx], &fb[y * fw], fw * sizeof(uint32_t));
+      }
+      draw();
     }
-    draw();
   }
 }
```

## 最终定向验证与真实消费链

final.py复用原版夹具布局并对新契约断言。普通O2和ASan/UBSan O1各运行五场景，10/10 exit0：

1. 相同预填0x01后四字段字节全0，EAGAIN前后update安全；子进程退出但父保留writer的原行为保持。
2. 未握手首次update安全返回，不发生旧版SIGSEGV，随后析构不unmap空指针。
3. 首次2×2、再次3×2映射及实际像素复制保持；空unmap从1次变0，有效重映射与析构各一次。
4. 真EOF update返回，未握手窗口可析构，不再需要超时终止。
5. 精确OpenCanvas正常close(4)后子进程仍活，连续1000次EOF update返回，帧像素仍从共享映射复制到canvas；没有误删窗口。

ASan/UBSan日志无诊断；ASAN_OPTIONS显式detect_leaks=0，未把它当LSan通过，初始化对象表示见证也不冒充MemorySanitizer。目标释放路径由munmap计数/析构场景证明，不宣称全应用无泄漏。

额外隔离复制现有NWM/依赖，执行原`make -j4 ISA=native app env`，原版exit2：wm.cpp的getenv与BDF.cpp的strtol在当前freestanding C++头路径未声明，完整标准native产品构建未通过。该问题在修复前已发生；未修改Makefile或安装软件。失败保留在native-build-result/log；不把后续host成功混称标准构建通过。

为覆盖生产合成调用链，native-consumer.py用当前完整window/wm/events/main及真实NDL/BDF直接host编译，使用原native.cpp生成的实际libos共享后端；只有诊断编译不带项目freestanding设置，不新增日常步骤。SDL dummy下真实Return事件→原事件分发/WindowManager::spawn→fork/execve→精确OpenCanvas客户端→真实memfd/ftruncate/mmap→Window::update→原合成器→NDL_DrawRect→原native共享屏幕，最终观察到全部768/768个测试像素。客户端写32×24像素后退出；生命周期仍按原行为，未把退出当作新窗口回收支持。

宿主observer只沿SDL入队并在SDL_UpperBlitScaled读取原屏幕surface，不改窗口内存或判据结果；没有截图/肉眼显示或真实音频声明。3.421秒运行最后通过原SDL_QUIT事件正常exit0；helper是精确OpenCanvas+实际pwrite，不是完整nterm/NDL_Init应用。完整native GUI/标准run及RV64 NWM仍未验收。consumer-run/log/result保存标记，移除768像素标记或伪造退出-15两种假PASS均被拒绝。首次诊断NDL编译被ccache只读目录拦截，保留attempt1日志，禁用该次编译缓存后成功，未改系统设置。

## 范围、清理与恢复

CPU-tests/RT不链接NWM，nanos默认APPS不含NWM；本批没有共享库改动，不重跑无关guest。RV64已有pipe2/memfd/mmap/ftruncate接口/系统头断点，本轮没有扩能力或冒充目标guest PASS。坏/负/巨大尺寸、消息分片/合并、fork/exec失败、fd覆盖、端点泄漏、SIGPIPE/子进程跟踪/窗口回收、长期GUI/真实音频均未闭合，不能把原建议“EOF关闭窗口并释放资源”继续当未披露已实现功能。

所有probe/消费者进程已结束；local/cleanup-plan/receipt在删除前记录每个本组build文件SHA/字节并删除整个隔离build树，含二进制、对象/库、两个字体副本与生产源副本。原始命令/日志、最小夹具与提取的OpenCanvas、patch、源码/8正式资产身份及归档/验证保留，未删除tracked/正式资产。最终数量/字节见cleanup-receipt.json；不保留新截图或生产镜像。probe/native构建配方须复制到新证据目录运行，避免覆盖本轮日志；旧版window从上述Git HEAD重建，最终版本用repair.patch。

本组Completed，结果确认与commit Pending，生产一文件未提交，根HEAD仍9747db8；ONS5e72dbb及既有编码行差异保持。119=107已修+8CRP未修完+2能力移交+2无需实施闭合。原P8/最终审阅历史结论不重写；下一动作唯一TASK_QUEUE#crp-next，本轮停止，无commit/push/下一组/M2推进。下一候选F0073用户指针/故障恢复必要分析仅Planned，不能默认为已批准完整地址空间隔离。Ignored证据/.agent仍需本地保管，Git提交不等于备份。


<a id="submit-20261021"></a>
## 用户确认与提交（2026-10-21）

用户“提交，继续”确认本批已报告最小范围及限制，授权本批精确提交后沿TASK_QUEUE#crp-next执行F0073必要分析一个单元；不授权push/新保护策略。复用既有完成/验收/清理，50保留证据与源码patch/八正式资产/其余输入及ONS既有编码差异SHA保持；无新构建/guest或重复Completion。提交仅根window.cpp、本报告/.gitignore、process及repair-status索引五路径，实际完整commit/mode/blob/最终回执在local/submit-20261021；最小夹具/日志/JSON/.agent仍本地忽略资产，不改跟踪政策、不宣称Git备份。

原标准native构建失败、RV64 NWM未验收等限制继续保留。会话建议：建议开启新对话；本组host与协议证据已整理，后续转用户指针保护；本次明确“继续”仍授权本轮执行唯一F0073必要分析，不因会话建议增加门槛。
