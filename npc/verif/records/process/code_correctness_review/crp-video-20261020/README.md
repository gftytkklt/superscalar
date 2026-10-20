# CRP SDL 图形四项与 nanos-lite 运行时性能分析（2026-10-20）

## 整体计划与授权

来源：用户“提交后继续，并进行执行性能分析”；进一步明确“针对音频、视频组修复完成后整体性能分析，仍然面向nanos-lite执行时图片、音频是否卡顿以及性能瓶颈等应用运行时分析”。前置音频八项已确认提交根d4b6c9c691f53f1316b0801ff2dae1dd4935ff40及ONS6326adf488985b9752fab47833a8acd0f9264e15，原验收/收尾复用。本轮仅一个图形修复与分析工作单元，不推进M2；完成后停等确认/提交，不自动提交新组或push。

目标与范围：F0091 NDL canvas/绘图边界、F0097同格式转换、F0098显示mask、F0114缩放矩形范围。保持现有8/32bit、byte mask与合法消费者路径；不扩BMP/PNG解码/窗口协议。性能分析面向修复后真实riscv64-nemu nanos-lite应用的画面推进、音频供给/欠填充、guest执行预算与热点，按实际必要对照定位原因，当前不实施新的调度/时钟/音质/性能策略。

契约：NDL非法canvas不发布新状态，DrawRect非法范围不IO；不新增屏外裁剪能力，合法居中及整行快路径保持，seek/write失败停止。SoftStretch等尺寸沿已有Blit裁剪，缩放分支域外/空矩形不写；按SDL1.2源的拒绝契约。ConvertSurface同mask保持、实际R/B对调才交换；UpdateRect按源mask提取RGB，显示alpha保持现有0xff，源不变。现有边界不需人工选新能力；若发现真实契约冲突/安装/系统变更即停依赖工作，由用户裁决。

步骤（同一阶段内顺序执行，可并行独立代码）：先保存入口身份与原反例，分别修NDL/miniSDL并定向host普通/ASan+UBSan；组合真实RV64像素探针与实际消费者；隔离标准update→run三前台/hello与画面目视；同版实际运行诊断与必要对照；完整diff正反/语句说明、同版源码/对象/库/链接/安装/盘核对、记录索引/状态/完成快照/产物清理。CPU/RT/REF不依赖Navy图形不重跑。NPC/其他ISA/native/NWM/实体声卡听音与长时未测单列。

交付/验收：生产video.c/NDL.c最小修改；逐项原版失败与最终合法像素/边界、同格式/RB双向/alpha、pitch/8bit、缩放采样/域外不写；host与真实RV64实际执行/有效PASS/main0/GOOD判据；PAL/bird/nslider实际受影响消费者；标准update→run与三前台/hello/目视证据；性能统计窗口、实际供给/画面间隔及欠填充、诊断开销/对照局限，不以源码猜测代替瓶颈证据，不把模型/有限观察/自有组SIGTERM写成完整正常退出或实体听感。归档本地最小测试/命令/日志/身份，正文完整diff及逐句说明，删除已完成隔离镜像/ELF/截图/源码副本；正式用户盘/header/kernel、NEMU/配置、ONS原编码/libc850mode保持。

结束节点：本组验收/性能分析/留档清理完成后报告结论、改动、验证、限制与下一入口，等待用户确认提交；真实性能优化或其他修复组另有门槛。无安装计划，无未决新增能力选择。

参考依据（2026-10-20查阅）：[NDL讲义](https://ysyx.oscc.cc/docs/ics-pa/3.4.html)、[SDL_UpdateRect](https://www.libsdl.org/release/SDL-1.2.15/docs/html/sdlupdaterect.html)、[SDL1.2 SoftStretch源码](https://raw.githubusercontent.com/libsdl-org/SDL-1.2/main/src/video/SDL_stretch.c)。技术事实仍以本地当前源码与实际测量为准。

## 逐项实现与功能验收

| ID | 改动与本轮证据 |
|---|---|
| F0091 | `NDL_OpenCanvas`在任何协议IO/状态发布前检查指针、设备与屏幕状态；仅双零解析为全屏，负/单零/超屏拒绝并保留旧canvas及输入参数。NWM沿既有3/4/5握手，额外限制其int framebuffer容量，控制短写失败不发布；实际NWM仍未运行。`NDL_DrawRect`先检查完整rect在canvas内，以减法避免坐标加法溢出，再用uint64计算居中byte offset/长度并核SIZE_MAX/LONG_MAX。每次seek返回必须等于目标；按返回字节推进的完整像素短写继续，零/负/非像素对齐/超请求长度停止，避免错误位置继续写。合法全屏仍单seek与整块write，合法小canvas逐行路径保持。原版5类动态见证：未初始化仍fd=-1 IO、负rect仍IO、非法canvas污染居中offset、seek失败仍写、70000²offset回绕；原版UBSan精确signed overflow退出1。最终真实NDL封装+syscall模型普通/ASan+UBSan各180检查通过；大屏只验证4字节源的宽offset，不声称分配完整超大屏。 |
| F0097 | `SDL_ConvertSurface`保留现有32bit、同G、兼容A及紧密pitch约束；同R/B直接复制全部像素字节，实际R/B交换时才转换。常见低byte/第三byte使用原16像素展开快路径；其他已有byte mask位置仅交换声明的R/B字段，保留其他字节。其他新格式不扩展，保留assert契约。测试含34像素非整16、两个方向、alpha兼容、源不变及高位byte mask独立期望。 |
| F0098 | `SDL_UpdateRect`保留默认RGB mask的OR-alpha快路径；其他已有32bit byte mask按`(p & mask) >> shift`取RGB，组装现有显示opaque alpha及RRGGBB；不改源/行尾padding。8bit palette路径保持。真实SDL→NDL捕获核对默认/反向/高位byte masks、子矩形/pitch与8bit；额外真实NDL/framebuffer末帧2×2 RGB精确对应112233/445566/778899/aabbcc。 |
| F0114 | 等尺寸先交既有Blit裁剪及dstrect尺寸回写，保持合法旧行为。缩放分支在指针/循环前拒绝空矩形、负原点、超surface范围，减法检查完整rect而不新增屏外采样裁剪。`j*sh/i*sw`先转uint64，行地址转size_t。测试精确8bit采样、源/目标偏移/pitch/外哨兵、零/负/超域不写、等尺寸裁剪，以及纵/横乘积超过INT_MAX。原版ASan精确buffer前1byte写，原UBSan精确65535×32769溢出；最终两反例无诊断且正常退出。 |

miniSDL组合：同最终基础用例原版40检查21失败；最终普通及ASan+UBSan各42/42、exit0。源码/命令/每例日志与生产身份见`local/video-validation.json`、`video-*.log`与`video-cases.h`。NDL见`local/ndl-results.json`、`ndl-host.c`、`ndl-run.py`。LSan沿当前沙箱限制关闭，当前不宣称通用泄漏证明。未扩大到构造任意损坏surface/指针背后真实allocation长度、线程或其他ISA。

## 实际RV64与消费者

隔离标准源码完整`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= update` exit0，25.423秒；随后同目录标准`run`54.653秒，10次真实SDL按键、8帧实际目视、PAL→NTerm/qzx command-not-found→slide0/1/0→PAL/Return继续渲染，hello36→158。slide0与切回0的frame SHA精确一致，slide1不同；不从PAL Return画面变化夸称到达某菜单，canvas外保留前一前台背景属既有行为。标准SIGTERM/make-15为自有组有限观察，非guest正常退出。

真实RV64独立探针链接同版miniSDL/NDL/libc/libos：42项实际SDL API检查与6项设备检查，main0/exit0/GOOD。API像素断言使用同一生产video.c的`NDL_DrawRect`观察边界（仅该符号重命名），不是以模型冒作实体显示；另外同源真实UpdateRect和真实NDL→nanos→AM→NEMU framebuffer路径无stub。实际host SDL纹理捕获得到居中32×24矩形与最终全屏底色/左上2×2色块，逐像素核对，源/普通库实际调用分开记录。非零exit、缺PASS、错计数、错main、重复PASS、BAD六种判据变异均拒绝。实际命令/exit/日志/盘extent身份与帧SHA见`local/guest-{fixture,results}.json`、`guest-run.log`、`checker-negatives.json`。

额外bird消费者使用同一标准新盘/ELF/库，诊断内核仅把FG slot1的nterm换为bird，仍PAL/bird/nslider+hello99:1，实际F2/Space输入、23.460秒、hello63；3帧实际目视均为青色标题页、白字/绿地与鸟/地面继续动画，未证明游戏正式开始。`bird-play`/`bird-later`是采集标签而非玩法断言。nslider已在标准三前台实际显示0/1/0，PAL实际8bit缩放显示保持；ONS本组没有源码改动，其图像同格式缺陷由直接SDL反例验证，不声称完整ONS脚本运行。

`SDL_VIDEODRIVER=dummy`/`SDL_AUDIODRIVER=dummy`用于实际NEMU设备运行/采集，不能当作物理听音或实体屏幕体验。CPU/RT/REF不依赖Navy SDL，不无故重跑；NPC/其他ISA/native/NWM/长时NotRun。正式用户盘/header/kernel、根NEMU/config及ONS原编码/libc850mode保留。标准、诊断与额外bird运行日志和修改边界分别保存，不能互相替代。

## 框架代码完整diff及语句说明

旧版本为本组开始前根仓音频提交`d4b6c9c`（完整HEAD见local/entry.json），新版本为2026-10-20本组未提交工作树；实际old/new SHA与mode、隔离正反应用结果见`local/archive-validation.json`。下方保留两个文件全部修复hunks；实现顺序、边界、失败返回和调用影响已逐项对应到上述语句说明。既有音频修复不重复算入本批差异。

```diff
diff --git a/navy-apps/libs/libminiSDL/src/video.c b/navy-apps/libs/libminiSDL/src/video.c
index de4cff0639fc6efbcace7cbf12a8613ac8819e73..3fb8578975e8a824a5ecaef2f6efa28097262788 100755
--- a/navy-apps/libs/libminiSDL/src/video.c
+++ b/navy-apps/libs/libminiSDL/src/video.c
@@ -91,7 +91,18 @@ void SDL_UpdateRect(SDL_Surface *s, int x, int y, int w, int h) {
     }
     for (int i = 0; i < h; i ++) {
       uint32_t *src_row = (uint32_t *)s->pixels + (y + i) * (s->pitch / 4) + x;
-      for (int j = 0; j < w; j ++) buf[i * w + j] = src_row[j] | 0xff000000u;
+      if (s->format->Rmask == DEFAULT_RMASK && s->format->Gmask == DEFAULT_GMASK &&
+          s->format->Bmask == DEFAULT_BMASK) {
+        for (int j = 0; j < w; j ++) buf[i * w + j] = src_row[j] | 0xff000000u;
+      } else {
+        for (int j = 0; j < w; j ++) {
+          uint32_t p = src_row[j];
+          uint32_t r = (p & s->format->Rmask) >> s->format->Rshift;
+          uint32_t g = (p & s->format->Gmask) >> s->format->Gshift;
+          uint32_t b = (p & s->format->Bmask) >> s->format->Bshift;
+          buf[i * w + j] = 0xff000000u | (r << 16) | (g << 8) | b;
+        }
+      }
     }
     NDL_DrawRect(buf, x, y, w, h);
   } else {
@@ -215,12 +226,20 @@ void SDL_SoftStretch(SDL_Surface *src, SDL_Rect *srcrect, SDL_Surface *dst, SDL_
     return;
   }
 
+  // Stretching requires complete rectangles; unlike the equal-size blit above,
+  // it does not define a clipped sampling map.
+  if (sw <= 0 || sh <= 0 || dw <= 0 || dh <= 0 ||
+      sx < 0 || sy < 0 || dx < 0 || dy < 0 ||
+      sx >= src->w || sy >= src->h || dx >= dst->w || dy >= dst->h ||
+      sw > src->w - sx || sh > src->h - sy ||
+      dw > dst->w - dx || dh > dst->h - dy) return;
+
   for (int j = 0; j < dh; j ++) {
-    int sy0 = sy + (j * sh) / dh;
-    uint8_t *sp = src->pixels + sy0 * src->pitch;
-    uint8_t *dp = dst->pixels + (dy + j) * dst->pitch + dx;
+    int sy0 = sy + (uint64_t)j * sh / dh;
+    uint8_t *sp = src->pixels + (size_t)sy0 * src->pitch;
+    uint8_t *dp = dst->pixels + (size_t)(dy + j) * dst->pitch + dx;
     for (int i = 0; i < dw; i ++) {
-      int sx0 = sx + (i * sw) / dw;
+      int sx0 = sx + (uint64_t)i * sw / dw;
       dp[i] = sp[sx0];
     }
   }
@@ -283,7 +302,26 @@ SDL_Surface *SDL_ConvertSurface(SDL_Surface *src, SDL_PixelFormat *fmt, uint32_t
 
   assert(fmt->Gmask == src->format->Gmask);
   assert(fmt->Amask == 0 || src->format->Amask == 0 || (fmt->Amask == src->format->Amask));
-  ConvertPixelsARGB_ABGR(ret->pixels, src->pixels, src->w * src->h);
+  if (fmt->Rmask == src->format->Rmask && fmt->Bmask == src->format->Bmask) {
+    memcpy(ret->pixels, src->pixels, (size_t)src->pitch * src->h);
+  } else {
+    assert(fmt->Rmask == src->format->Bmask && fmt->Bmask == src->format->Rmask);
+    if ((fmt->Rmask | fmt->Bmask) == (DEFAULT_RMASK | DEFAULT_BMASK)) {
+      ConvertPixelsARGB_ABGR(ret->pixels, src->pixels, src->w * src->h);
+    } else {
+      // maskToShift also accepts other byte positions. Only exchange the
+      // declared R/B fields and retain the green/alpha bytes as before.
+      uint32_t *sp = (uint32_t *)src->pixels, *dp = (uint32_t *)ret->pixels;
+      size_t count = (size_t)src->w * src->h;
+      for (size_t i = 0; i < count; i ++) {
+        uint32_t p = sp[i];
+        uint32_t r = (p & src->format->Rmask) >> src->format->Rshift;
+        uint32_t b = (p & src->format->Bmask) >> src->format->Bshift;
+        dp[i] = (p & ~(fmt->Rmask | fmt->Bmask)) |
+          ((r << fmt->Rshift) & fmt->Rmask) | ((b << fmt->Bshift) & fmt->Bmask);
+      }
+    }
+  }
 
   return ret;
 }
diff --git a/navy-apps/libs/libndl/NDL.c b/navy-apps/libs/libndl/NDL.c
index 6bd6fb1d93d342e7aa4c179754a8c05fb95ec960..471125a4fe49d12ffd85f7167d7939e561efc58d 100755
--- a/navy-apps/libs/libndl/NDL.c
+++ b/navy-apps/libs/libndl/NDL.c
@@ -7,6 +7,7 @@
 #include <sys/time.h>
 #include <time.h>
 #include <fcntl.h>
+#include <limits.h>
 
 static int evtdev = -1;
 static int fbdev = -1;
@@ -31,46 +32,69 @@ int NDL_PollEvent(char *buf, int len) {
 }
 
 void NDL_OpenCanvas(int *w, int *h) {
+  if (w == NULL || h == NULL || fbdev < 0 || screen_w <= 0 || screen_h <= 0) return;
+  int width = *w, height = *h;
+  if (width == 0 && height == 0) { width = screen_w; height = screen_h; }
+  if (width <= 0 || height <= 0 || width > screen_w || height > screen_h) return;
   if (getenv("NWM_APP")) {
     int fbctl = 4;
-    fbdev = 5;
-    screen_w = *w; screen_h = *h;
+    // NWM's resize path stores its framebuffer byte count in an int.
+    if ((uint64_t)width * height > INT_MAX / 4) return;
     char buf[64];
-    int len = sprintf(buf, "%d %d", screen_w, screen_h);
+    int len = sprintf(buf, "%d %d", width, height);
     // let NWM resize the window and create the frame buffer
-    write(fbctl, buf, len);
+    if (write(fbctl, buf, len) != len) return;
     while (1) {
       // 3 = evtdev
       int nread = read(3, buf, sizeof(buf) - 1);
       if (nread <= 0) continue;
-      buf[nread] = '\0';
+      buf[nread < sizeof(buf) ? nread : sizeof(buf) - 1] = '\0';
       if (strcmp(buf, "mmap ok") == 0) break;
     }
     close(fbctl);
+    fbdev = 5;
+    screen_w = width; screen_h = height;
+  }
+  canvas_w = width; canvas_h = height;
+  *w = width; *h = height;
+}
+
+static int write_pixels(const uint8_t *pixels, size_t bytes) {
+  while (bytes > 0) {
+    ssize_t done = write(fbdev, pixels, bytes);
+    // Both framebuffer implementations advance by the returned byte count.
+    // Retrying a partial pixel would misalign the next nanos-lite fb_write.
+    if (done <= 0 || (size_t)done > bytes || done % 4 != 0) return 0;
+    pixels += done;
+    bytes -= done;
   }
-  if (*w == 0 && *h == 0) {*w = screen_w; *h = screen_h;}
-  assert(*w <= screen_w && *h <= screen_h);
-  canvas_w = *w; canvas_h = *h;
+  return 1;
 }
 
 void NDL_DrawRect(uint32_t *pixels, int x, int y, int w, int h) {
-  int offset_y = screen_w*((screen_h-canvas_h)/2+y);
-  int offset_x = (screen_w-canvas_w)/2 + x;
-  int offset = offset_y + offset_x;
+  if (fbdev < 0 || pixels == NULL || canvas_w <= 0 || canvas_h <= 0 ||
+      x < 0 || y < 0 || w <= 0 || h <= 0 ||
+      x > canvas_w || y > canvas_h || w > canvas_w - x || h > canvas_h - y) return;
+  uint64_t row_bytes = (uint64_t)w * 4;
+  uint64_t bytes = row_bytes * h;
+  uint64_t offset = ((uint64_t)screen_w * ((screen_h - canvas_h) / 2 + y) +
+                     (screen_w - canvas_w) / 2 + x) * 4;
+  uint64_t end = offset + (uint64_t)(h - 1) * screen_w * 4 + row_bytes;
+  if (bytes > SIZE_MAX || bytes > LONG_MAX || end > LONG_MAX) return;
   // full-width rects are contiguous rows in the framebuffer: one shot
   if (w == screen_w) {
-    lseek(fbdev, offset*4, SEEK_SET);
-    write(fbdev, pixels, w*h*4);
+    if (lseek(fbdev, (off_t)offset, SEEK_SET) != (off_t)offset) return;
+    write_pixels((const uint8_t *)pixels, (size_t)bytes);
     return;
   }
-  uint32_t *current_row = pixels;
+  const uint8_t *current_row = (const uint8_t *)pixels;
   // arbitrary canvas
   // this is correct for native
   for (int i=0;i<h;i++){
-    lseek(fbdev, offset*4, SEEK_SET);
-    write(fbdev, current_row, w*4);
-    current_row += w;
-    offset += screen_w;
+    if (lseek(fbdev, (off_t)offset, SEEK_SET) != (off_t)offset ||
+        !write_pixels(current_row, (size_t)row_bytes)) return;
+    current_row += row_bytes;
+    offset += (uint64_t)screen_w * 4;
   }
 }
 
```

## 修复后 nanos-lite 应用运行性能

结论：在本轮PAL启动画面、99前台/1hello的实际负载下，长绘图占用使同线程补音服务点迟到，仍有明显音频缺供给；四项图形正确性修复不等于卡顿已消除。这里只对该场景作因果判断，NTerm/slide/bird为上述功能观察，不把PAL性能数字推广为所有应用或历史版本对照。

实际配置由新标准盘/内核/四应用ELF绑定；PAL实际11025Hz、双声道S16、1024 samples，每包4096B，需求44100B/s、至少10.7666包/s（每92.8798ms一包）。miniSDL仍由GetTicks/PollEvent/WaitEvent/Delay经CallbackHelper服务音频，没有独立音频线程；yield/定时调度不直接进入该用户回调。音频帧在`AUDIO_FillBuffer`计算完后经真实NDL/AM/NEMU提交，不静音、不替换生成算法。

四次24秒交错`normal1 → skip1 → normal2 → skip2`，同一个诊断引擎、host探针、guest、kernel与盘字节；各次稳定窗口为共同CLOCK_MONOTONIC起点4..20秒，先结束所有构建和其他仿真再串行采样。符号/反汇编从本次PAL与kernel生成，不复用旧硬编码PC；6个入口PC、动态ra返回跟踪，核对PAL入口不落入另三应用可执行段，测量不切前台。skip唯一变化是诊断引擎在已核对的PAL SDL_UpdateRect入口模拟立即ret，画面故意不更新，不能作为生产修复或图形验收。

| 指标（稳定窗口） | normal1 | skip1（仅去绘图） | normal2 | skip2（仅去绘图） |
|---|---:|---:|---:|---:|
| PCM提交频率（由平均间隔取倒数，包/s） | 4.595 | 10.841 | 4.375 | 10.855 |
| PCM平均提交间隔 ms | 217.630 | 92.238 | 228.597 | 92.125 |
| 欠填充host回调数/总数 | 101/174 | 0/174 | 104/173 | 0/173 |
| 需求字节缺供给比例 | 58.05% | 0% | 60.12% | 0% |
| PAL生成回调平均耗时 ms | 55.796 | 58.960 | 59.255 | 56.215 |
| SDL_UpdateRect单次平均 ms | 77.468 | 跳过 | 80.771 | 跳过 |

补音回调在skip中仍实际执行约0.90M条guest指令、56–59ms，因此供给恢复不是去掉音频计算得到。正常例超过92.88ms预算的服务点空档73/69次，平均其中154.94/161.60ms落在绘图内；skip两轮没有超过预算的空档，最长82.90/81.08ms。绘图经常连续两次占用，单次耗时虽接近而未必超过92.88ms，两次之间没有补音服务仍会透支供给预算。这里的poll为非填音重入期间的CallbackHelper入口机会，不能等同每次都生成PCM。

正常例热点（包含式计时，不把嵌套项相加）：每次SDL_UpdateRect约1.51M条guest指令，占稳定窗口内guest指令约74.2–74.5%；PAL填音约22.4–22.6%。每次显示内NDL_DrawRect约24.97/26.51ms，其中200次fb_write共19.47/20.52ms；UpdateRect在DrawRect以外约52.50/54.26ms，包含8bit palette展开、分配/释放及其余本函数工作，未单独证明malloc或某条指令是全部热点。NDL在fb以外约5.49/5.99ms，静态链为小canvas逐行seek/write，kernel逐行FBDRAW并sync；这些是后续优化候选，不能仅凭调用数断言全部时间应归于syscall。调用内指令/墙钟包含期间内核/中断/调度，不是无扰动的逐源码指令剖析。

实际PlayAudio每次请求/返回均4096B，写COUNT增量逐次4096；本轮复制字节=实际消费字节、最后观测count=0，未观察read→write间consume序列改变。NDL音频提交往返仅约1.5ms，当前持续缺供给已有更强的绘图/服务点证据；COUNT原并发语义未改，探针会改变宿主时序，观测闭合不证明F0043无竞态，也不据此修复F0043/F0118或PAL RIX问题。

证据：`local/perf/{fixture,symbols,engine-identities,builds,analysis,validation,recovery}.json`及`probe-addresses.h`、各样本`process/result.json`和`app/device/host/guest.log`；准备/测量/分析脚本见`local/{prepare-perf,measure-perf,analyze-perf}.py`。四种结果判据负例拒绝。初次skip判据错误要求纹理更新，已保留原result/runner日志并改为正常须有刷新、skip须无刷新，在同一原始日志上重新判定；该错误不计生产缺陷，未为更正判据重复采样。

限制与后续方向：每指令PC检查、日志与设备探针有开销，绝对耗时是该诊断环境数值；同引擎对照消除了依赖“探针零开销”的假设。SDL dummy可量化供需和真实像素，不代替物理听感；host纹理刷新不是完整guest帧率，skip完全无绘图也不是可交付的优化。短窗口不证明长时保证、不判disk或99:1策略为根因，也不能据此还原用户未识别的旧流畅版本。后续优先独立评估8bit显示展开、逐行提交开销与长绘图分段服务音频；音画吞吐、缓冲水位/延迟等新策略须另行明确，本轮没有实施性能策略修改。


生产引擎参考：另用同版标准NEMU（无PC/COUNT修改）、同配置/guest/盘，仅host SDL观察24秒，稳定窗口174次callback、369次纹理更新，纹理更新平均43.38ms、p95 102.00ms、max119.00ms；诊断正常两轮平均44.37/44.92ms。host音频回调耗时参考约0.00488ms、诊断约0.02090/0.02045ms，直接表明观察会影响执行；不能据此校准生产欠填充比例。实际回调是否缺供给仍以受限的诊断对照讨论，不把约23次/s纹理刷新称为完整guest帧率或主观流畅证明。

性能18项最终检查/4种负例均通过，14个注入/替换点精确计数，三份诊断源码完整差异及冷恢复配方保留于perf。所有5组进程已结束。旧原始错误oracle与日志保留，未覆盖历史样本。未实施调度/音频时钟/容量/音质或显示吞吐策略修改。


## 最终收尾与恢复

归档14/14、同版身份235/235、额外功能/收尾91/91、性能18/18全部通过；61份相关源/配置及29份关键产物身份、标准输入7640项身份另存。两薄归档8个唯一成员/17条引用均对应实际对象，108标准盘extent/5应用链接=安装=盘字节、40条隔离symlink均核对。根/ONS/libc HEAD与index保持，正式8份资产无漂移。完成运行与实际目视后清理9749项542589427逻辑字节（约517.5MiB），零tracked删除，无本组运行进程。

清理仅本组local隔离源码/构建/盘、ELF/对象/库、截图和两份可由Git恢复的生产源码副本；未触及正式用户产物。原图已删，目视文字/数值像素/原SHA保留，不能再宣称图片可直接打开。路径/字节/SHA与预期缺失见cleanup-plan/receipt；日志/最小验证源/配置/完整diff/实际命令及结果仍在。local/.agent不由普通commit备份。

本组F0091/F0097/F0098/F0114 Completed，用户结果确认与本组commit Pending；音频前组根d4b6c9c691f53f1316b0801ff2dae1dd4935ff40/ONS6326adf488985b9752fab47833a8acd0f9264e15已确认提交，未push。本组只改NDL.c/video.c生产源，2文件86增24删，无性能策略源码修改。累计84已修/35未修完，前80已确认提交。唯一后续入口TASK_QUEUE#crp-next，下一RWops/图像加载组未Start，M2不变。

冷恢复：从local/entry.json所记根HEAD恢复旧源，应用正文完整patch；最小host验证按ndl-run.py及video-validation.json的build/run命令，真实消费者prepare-runtime.py后standard-path/run-standard.local；真实guest先prepare-guest.py再refresh-guest.py→run-guest.py，bird使用prepare-bird.py→run-bird.py。性能prepare-perf.py须绑定该轮标准guest的ELF符号/盘，四个同版对照及host-only参考的准确命令/环境见perf/recovery.json，按analyze-perf.py重新汇总；不复用旧PC或未保留的ELF。先恢复F0074正式资源/现有工具链，不安装/下载，副本路径不写正式目录；完整再生顺序及判据均在保留脚本/JSON。

建议开启新对话：本轮已有跨仓提交、四项图形修复和多组运行时证据，下一组转RWops/图像加载，唯一入口与恢复资料完整；此建议不增加审批或启动Prompt。当前单元完成后停止，等待确认/提交，不自动下一组或M2。
