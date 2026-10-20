# CRP BDF/终端组（2026-10-20）

## 整体计划与范围

用户“提交后继续”确认前RWops/图像组，已实际提交70983d4；授权唯一入口F0105/F0109一个单元。复用CRP整体计划/workflow；M2不变，新组不自动commit/push，不安装。

目标：F0105限制BDF token/整行、尺寸、bitmap行/位移和字符索引；缺文件/解析失败对象w=h=0且释放此前glyph；现有STARTCHAR十六进制索引与32bit行/32行子集、现有本地Courier字体输出保持，不扩通用字体格式。NULL/缺glyph surface安全失败，NTerm处理失败。F0109严格按count读取，已有18种序列及旧空参数语义保持，必要跨块状态；数字溢出拒绝且光标算术有界，不扩VT。

阶段/交付：本组一个修复阶段，5生产文件、逐项host原反例和普通/sanitizer验证、实际RV64共享suite及真实消费者、内嵌完整diff/正反应用与源/对象/库/链接/安装/盘同版证据、records索引/修复镜像/状态与清理。

验收：原token/缺newline/33bitmap行/高位char及部分ESC明确失败见证；最终缺文件/失败清理/合法字体逐glyph行与surface像素、截断/长行/数值边界、每个escape分割点及非NUL精确buffer/溢出通过。实际RV64精确PASS+main0+GOOD且判据变异拒绝；标准nanos make ARCH=riscv64-nemu update→run三前台hello及目视/像素。本组完成停止，等待用户确认/commit；真实策略冲突或安装停止。无已知待裁决项。

参考：本地FINAL_FINDINGS F0105/F0109、MEDIA_RUNTIME/APP_OS_CALLS及实际Courier字体/NTerm内置与外部shell调用；2026-10-20查询[X.Org BDF规范](https://www.x.org/releases/X11R7.0/doc/PDF/bdf.pdf)核对BBX/bitmap格式，保持本地原STARTCHAR命名索引实现子集，不新增ENCODING能力。

## 实现与逐项结论

F0105：`fields()`用`strtol`与ERANGE/INT范围验证替代不受约束的整数转换；token复制前核`n < sizeof(cmd)`，整行超255字节拒绝，不再将同一长行拆成多个命令。bitmap按BBX规定的行数和每行补齐到byte的hex位数读取，核32行/32bit容量、合法hex及行终止；允许文件最后ENDFONT无newline，截断bitmap失败。状态要求font bounds→STARTCHAR→BBX→BITMAP→ENDCHAR，ENDFONT闭合；现有元数据仍忽略，STARTCHAR保留本地hex编码索引子集，不实现任意命名字形/ENCODING。`w/h`初始0，NULL/缺文件安全返回，失败销毁此前已创建glyph并重置尺寸；重复编码先delete旧glyph。`create()`用int64计算偏移，行/位移均验证，`UINT32_C(1)`避免signed bit31；固定cell/glyph32×32子集。`BDF_CreateSurface`对NULL/失效尺寸/malloc失败返回NULL，索引用unsigned char；NTerm初始化失败退出1，缺glyph跳过绘制，避免继续把无效对象传入SDL。字体缓存/通用OpenFontRW、通用surface内部OOM断言不扩展。

F0109：已有18种escape pattern与空数字语义保持。`escape[40]/escape_len`保存有界前缀，每读取一个已授权字节后匹配；固定字符与数字均先验`pos < escape_len`。数值在乘10前核INT_MAX，最多3×10位参数的现有最长合法序列落在容量内；无效/溢出/超长序列沿原fallback丢ESC并按普通文本处理其余部分，新ESC可重新启动解析。返回Incomplete时只保存状态，不提前修改光标/颜色/模式；跨write/read块继续。四个相对移动先按剩余行列距离截断，避免INT_MAX参数与当前位置相加溢出；原最终边界钳位保持。`write`仍在count内遇NUL停下，不扩完整VT、超长数字、线程或生命周期以外的状态。

## 原反例与host验证

命令：`CCACHE_DISABLE=1 python3 local/make-tests.py`生成最小BDF，`python3 local/run-host.py before`在修改前编译实际BDF/Terminal与miniSDL video，逐模式执行；token ASan明确stack-buffer-overflow、33行UBSan index32、单字节精确heap ESC ASan read越界、高位char ASan非法索引，普通高位case SIGSEGV。缺末newline的截断bitmap未被原实现拒绝（断言失败），不夸称该特定短输入必然越过256字节数组。最初host编译因ccache目录沙箱只读失败；只对测试进程设置CCACHE_DISABLE=1后重试，无安装/系统配置更改。

最终`python3 local/font-reference.py`根据旧算法与现有7个实际Courier资源独立计算行hash；`python3 local/run-host.py final`普通与ASan+UBSan各248599条断言/零失败。覆盖15类缺文件/空/长token/长行/33行/截断/非法hex/尺寸负值或溢出/无BBX/短多行/无ENDFONT/已分配后失败、合法/无末newline/空行/重复编码、NULL/高位/缺glyph与极限偏移、32×32/bit31与小写hex；7字体各191glyph行hash一致且所有实际surface像素逐一符合位图。20个现有控制序列及空参数变体在所有切分点分为精确大小无NUL的两块，另逐字节输入、save/restore/clear/color/模式语义、INT_MAX移动与溢出拒绝、NUL停止。miniSDL video为实际代码，host仅用gc-sections去掉未调用NDL路径；不把host定向当真实设备回归。

ASan/UBSan环境明确`ASAN_OPTIONS=detect_leaks=0:abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1`，沿已知沙箱LSan/ptrace限制关闭泄漏扫描；不宣称LSan通过或通用OOM/泄漏证明。bitmap/glyph清理由失败对象全NULL和重复编码/析构实际执行覆盖。

## 实际RV64与标准消费者

复用已有隔离配方`python3 local/prepare-runtime.py`，仅复制现有资源和源码、remap绝对symlink，不下载/安装/修改正式输入；在隔离nanos目录执行`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= update`，exit0，28.385秒。`prepare-guest.py`链接实际libbdf/miniSDL/NDL/newlib和字节一致Terminal源，诊断仅添加suite/字体、选择初始应用与SYS_exit oracle；初次实际RV64通过后，将所有split测试改用精确allocation边界，host复验并`refresh-guest.py`重建测试目标/诊断盘/内核、`run-guest.py`最终重跑。生产源码/标准盘不变。最终248599断言/7×191glyph、main0/exit0/GOOD全部通过；六种非零exit/缺PASS/错误计数/错误main/重复PASS/BAD trap变异全部拒绝。首轮日志/结果保留initial；随后补32×32/bit31与小写hex边界，定向suite增加6断言，host/实际RV64再次通过，前次结果另保留before-boundary；生产及标准回归不变，不与最终suite混称。

标准`make ... run`54.058秒，F2→NTerm qzx command-not-found后prompt、F3→slide0/1/0、F1→PAL/Return继续渲染，hello首帧32→末148；八帧实际contact sheet目视正常。NTerm初始及命令后两帧，分别排除正在blink的一个cursor cell，其余各69797个RGB像素与旧Courier-7字形模型全部相等；slide返回0帧SHA完全恢复。屏幕外canvas保留上个前台背景属既有行为；PAL Return只证明输入与持续渲染，不夸称菜单或完整玩法。运行结束为自有组SIGTERM/make -15，不是guest正常退出。dummy SDL经实际NEMU设备路径，不能证明实体显示/听音。

CPU-tests/RT/REF不消费Navy libbdf/NTerm，按影响不重跑；NPC/其他ISA/native/NWM外部pipe/完整ONS脚本/实体AV/长时NotRun。跨块Terminal在host与实际RV64调用suite验证，不称当前RV64不支持的外部pipe端到端已运行。F0043/F0118/PAL RIX/ONS字体缓存与OpenFontRW及其他未修归属保持，不新增性能结论。

## 同版身份与框架完整diff

旧根完整commit `70983d4b2ac7c22e90fda116ec71b6b6119ded96`；新为2026-10-20未提交工作树。下面完整diff覆盖5文件；29项正反应用/字节/mode归档核验通过。235项身份核验通过：47份源/配置、26份产物、2薄库9唯一对象/19引用，108标准extent与5应用linked=installed=disk，23诊断payload绑定最终guest。7640原入口源全部未漂移；标准对象dep含最终BDF/SDL_bdf/term/main与nterm.h，guest Terminal与suite字节一致。8正式资产/root/ONS/libc HEAD/index、ONS原编码差异及libc850原mode保持。

| 根相对路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `navy-apps/libs/libbdf/src/BDF.cpp` | `ce18a79aaceb7eab8e77d997301f3fc094760cfe08ad16c7dc6f2ff7aa25fd1e` | `3f0233d0eaea58e7dfab059db5e725aa7046fcc581fb508f47dbbdf2db00bc10` |
| `navy-apps/libs/libbdf/src/SDL_bdf.cpp` | `da2b08e12b58d2df201c49546404209c08247b80bcb6a84e1ff5275c31d82666` | `60c1e1d45b24dcd345db0924369adc5ab01cb2477caa8a0c4b0782275ce76e11` |
| `navy-apps/apps/nterm/src/term.cpp` | `e9254f0dc858db70fb8ba1e45842ee7cb481dad3b3cfc15bbc2990a8bb364ed1` | `5bdaa1fb5f0791616f50ad4eb00f6ad103049b1bc95cc89f19702f4d696b388b` |
| `navy-apps/apps/nterm/include/nterm.h` | `58b23473e5ad9b946faafaac42f3b5f57826d5f4c5343d393c6fdf6747a7e6fa` | `a279527c936b10698471047be6c2eda4cddbc2c650919c92da64d596998c9073` |
| `navy-apps/apps/nterm/src/main.cpp` | `26fff3975778ccc9619127ee35f2092d3f2fa5f258e3623bce0e70c82467860d` | `e8ea5760bdeab79c8c37f913502112dfffd52a7a6205c8777d24a124016e6f70` |

```diff
diff --git a/navy-apps/apps/nterm/include/nterm.h b/navy-apps/apps/nterm/include/nterm.h
index 9285b671917cbb1534e8ee2688f13f2ce06528e6..462c1202a6602c49e20bd65ab8b72caf56a501eb 100755
--- a/navy-apps/apps/nterm/include/nterm.h
+++ b/navy-apps/apps/nterm/include/nterm.h
@@ -25,7 +25,9 @@ private:
 
   void move_one();
   void backspace();
-  size_t write_escape(const char *str, size_t count);
+  char escape[40];
+  size_t escape_len;
+  int write_escape();
   void scroll_up();
 
 
diff --git a/navy-apps/apps/nterm/src/main.cpp b/navy-apps/apps/nterm/src/main.cpp
index 2d58349b16fe8d85be336d07ff39ffe30ec46767..05abf0dafdf31a7f7bdbc958a4c06f6d44d05dd3 100755
--- a/navy-apps/apps/nterm/src/main.cpp
+++ b/navy-apps/apps/nterm/src/main.cpp
@@ -13,6 +13,7 @@ void extern_app_run(const char *app_path);
 int main(int argc, char *argv[]) {
   SDL_Init(0);
   font = new BDF_Font(font_fname);
+  if (font->w <= 0 || font->h <= 0) { delete font; SDL_Quit(); return 1; }
 
   // setup display
   int win_w = font->w * W;
@@ -30,6 +31,7 @@ int main(int argc, char *argv[]) {
 
 static void draw_ch(int x, int y, char ch, uint32_t fg, uint32_t bg) {
   SDL_Surface *s = BDF_CreateSurface(font, ch, fg, bg);
+  if (!s) return;
   SDL_Rect dstrect = { .x = x, .y = y };
   SDL_BlitSurface(s, NULL, screen, &dstrect);
   SDL_FreeSurface(s);
diff --git a/navy-apps/apps/nterm/src/term.cpp b/navy-apps/apps/nterm/src/term.cpp
index ec0ea7ca1fa323048cf33f59299d468ba714a701..a4d0927c0cd995abc6406fc4b1431094af103c68 100755
--- a/navy-apps/apps/nterm/src/term.cpp
+++ b/navy-apps/apps/nterm/src/term.cpp
@@ -1,4 +1,5 @@
 #include <nterm.h>
+#include <limits.h>
 
 #define EMPTY ' '
 
@@ -58,19 +59,19 @@ void Terminal::esc_movefirst(int *args) {
 }
 
 void Terminal::esc_moveup(int *args) {
-  cursor.y -= args[0];
+  cursor.y -= min(args[0], cursor.y);
 }
 
 void Terminal::esc_movedown(int *args) {
-  cursor.y += args[0];
+  cursor.y += min(args[0], h - 1 - cursor.y);
 }
 
 void Terminal::esc_moveleft(int *args) {
-  cursor.x -= args[0];
+  cursor.x -= min(args[0], cursor.x);
 }
 
 void Terminal::esc_moveright(int *args) {
-  cursor.x += args[0];
+  cursor.x += min(args[0], w - 1 - cursor.x);
 }
 
 void Terminal::esc_save(int *args) {
@@ -145,6 +146,7 @@ Terminal::Terminal(int width, int height) {
   buf = new char[w * h];
   color = new uint8_t[w * h];
   dirty = new bool[w * h];
+  escape_len = 0;
   inp_len = 0;
   col_f = Color::BLACK;
   col_b = Color::WHITE;
@@ -200,43 +202,52 @@ void Terminal::scroll_up() {
   }
 }
 
-size_t Terminal::write_escape(const char *str, size_t count) {
+// 0: incomplete prefix; 1: handled; -1: unsupported or overflowing sequence.
+int Terminal::write_escape() {
+  bool prefix = false;
   for (auto &p: esc_seqs) {
-    bool match = false;
-    int len = 0, args[4], narg = 0;
-
-    for (const char *cur = p.pattern, *s = str; ; cur ++) {
-      if (*cur == '\0') { // found a match.
-        match = true; break;
-      }
-      if (*cur != '#') {
-        if (*s != *cur) break;
-        s ++;
-        len ++;
-      } else {
+    size_t pos = 0;
+    int args[4] = {}, narg = 0;
+    bool match = true;
+    for (const char *cur = p.pattern; *cur; cur ++) {
+      if (pos == escape_len) { prefix = true; match = false; break; }
+      if (*cur == '#') {
         int data = 0;
-        for (; *s >= '0' && *s <= '9' && s - str < count; s ++, len ++) {
-          data = data * 10 + *s - '0';
+        while (pos < escape_len && escape[pos] >= '0' && escape[pos] <= '9') {
+          int digit = escape[pos ++] - '0';
+          if (data > (INT_MAX - digit) / 10) return -1;
+          data = data * 10 + digit;
         }
         args[narg ++] = data;
-      }
+        if (pos == escape_len) { prefix = true; match = false; break; }
+      } else if (escape[pos ++] != *cur) { match = false; break; }
     }
-
-    if (match) {
+    if (match && pos == escape_len) {
       (this->*p.handle)(args);
       cursor.x = max(min(cursor.x, w - 1), 0);
       cursor.y = max(min(cursor.y, h - 1), 0);
-      return len;
+      return 1;
     }
   }
-  return 1;
+  return prefix ? 0 : -1;
 }
 
 void Terminal::write(const char *str, size_t count) {
   for (size_t i = 0; i != count && str[i]; ) {
     char ch = str[i];
-    if (ch == '\033') {
-        i += write_escape(&str[i], count - i);
+    if (escape_len || ch == '\033') {
+      escape[escape_len ++] = ch;
+      i ++;
+      int result = write_escape();
+      if (result == 0 && escape_len < sizeof(escape)) continue;
+      size_t len = escape_len;
+      escape_len = 0;
+      if (result != 1) {
+        // Keep the old fallback: discard ESC, then process the remaining text.
+        char tail[sizeof(escape)];
+        memcpy(tail, escape + 1, len - 1);
+        write(tail, len - 1);
+      }
     } else {
       switch (ch) {
         case '\x07':
diff --git a/navy-apps/libs/libbdf/src/BDF.cpp b/navy-apps/libs/libbdf/src/BDF.cpp
index c5d6d14405ddb269b031327593873ecd36c283ad..f57d9f58d40a54f525c1d4909f86145f4b53285d 100755
--- a/navy-apps/libs/libbdf/src/BDF.cpp
+++ b/navy-apps/libs/libbdf/src/BDF.cpp
@@ -1,84 +1,115 @@
 #include <BDF.h>
 #include <stdio.h>
 #include <string.h>
+#include <stdlib.h>
+#include <errno.h>
+#include <limits.h>
+
+static bool fields(const char *p, int *values, int count, int base = 10) {
+  for (int i = 0; i < count; i ++) {
+    char *end;
+    errno = 0;
+    long value = strtol(p, &end, base);
+    if (end == p || errno == ERANGE || value < INT_MIN || value > INT_MAX) return false;
+    values[i] = (int)value;
+    p = end;
+  }
+  while (*p == ' ' || *p == '\t') p ++;
+  return *p == '\0';
+}
 
 void BDF_Font::create(uint32_t ch, int *bbx, uint32_t *bitmap, int count) {
+  delete [] font[ch];
   font[ch] = new uint32_t[h];
   for (int y = 0; y < h; y ++) {
     uint32_t row = 0;
     for (int x = 0; x < w; x ++) {
-      int x1 = x - bbx[2];
-      int y1 = y - (h - bbx[1] - bbx[3]) - h1;
-      if (x1 >= 0 && y1 >= 0 && y1 < bbx[1]) {
-        uint32_t mask = bitmap[y1];
-        if ( (mask >> (x1)) & 1 ) {
-          row |= (1 << x);
-        }
+      int64_t x1 = (int64_t)x - bbx[2];
+      int64_t y1 = (int64_t)y - ((int64_t)h - bbx[1] - bbx[3]) - h1;
+      if (x1 >= 0 && x1 < 32 && y1 >= 0 && y1 < count) {
+        if ((bitmap[y1] >> x1) & 1u) row |= UINT32_C(1) << x;
       }
     }
     font[ch][y] = row;
   }
 }
 
-BDF_Font::BDF_Font(const char *fname) {
+BDF_Font::BDF_Font(const char *fname) : w1(0), h1(0), name(NULL), w(0), h(0) {
   memset(font, 0, sizeof(font));
+  if (fname == NULL) return;
   FILE *fp = fopen(fname, "r");
   if (!fp) return;
 
   char buf[256], cmd[32];
-  bool valid_file = false, in_bitmap = false;
-  uint32_t bm[32], ch = '\0';
-  int bm_idx, bm_bbx[4];
+  bool started = false, bounds = false, glyph = false, bbx = false;
+  bool in_bitmap = false, ended = false, ok = true;
+  uint32_t bm[32];
+  int ch = 0, bm_idx = 0, bm_bbx[4] = {};
 
-  while (fgets(buf, 256, fp)) {
-    sscanf(buf, "%s ", cmd);
-    if (strcmp(cmd, "STARTFONT") == 0) {
-      valid_file = true;
-    }
-    if (strcmp(cmd, "FONTBOUNDINGBOX") == 0) {
-      sscanf(buf, "%*s %d %d %d %d", &w, &h, &w1, &h1);
-    }
-    if (strcmp(cmd, "STARTCHAR") == 0) {
-      sscanf(buf, "%*s %x", &ch);
-    }
-    if (strcmp(cmd, "BBX") == 0) {
-      sscanf(buf, "%*s %d %d %d %d", &bm_bbx[0], &bm_bbx[1], &bm_bbx[2], &bm_bbx[3]);
-    }
-    if (strcmp(cmd, "ENDCHAR") == 0) {
-      if (ch < 256) {
-        create(ch, bm_bbx, bm, bm_idx);
+  while (fgets(buf, sizeof(buf), fp)) {
+    size_t len = strlen(buf);
+    if (len == sizeof(buf) - 1 && buf[len - 1] != '\n') { ok = false; break; }
+    while (len && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) buf[--len] = '\0';
+    const char *p = buf;
+    while (*p == ' ' || *p == '\t') p ++;
+    size_t n = strcspn(p, " \t");
+    if (n >= sizeof(cmd)) { ok = false; break; }
+    memcpy(cmd, p, n); cmd[n] = '\0'; p += n;
+    while (*p == ' ' || *p == '\t') p ++;
+
+    if (in_bitmap && strcmp(cmd, "ENDCHAR") != 0) {
+      size_t digits = (bm_bbx[0] + 7) / 8 * 2;
+      if (bm_idx >= bm_bbx[1] || bm_idx >= 32 || len != digits) { ok = false; break; }
+      uint32_t row = 0;
+      for (size_t i = 0; i < digits; i ++) {
+        char c = buf[i];
+        int value = c >= '0' && c <= '9' ? c - '0' :
+                    c >= 'A' && c <= 'F' ? c - 'A' + 10 :
+                    c >= 'a' && c <= 'f' ? c - 'a' + 10 : -1;
+        if (value < 0) { ok = false; break; }
+        for (int bit = 0; bit < 4; bit ++)
+          if ((value >> (3 - bit)) & 1) row |= UINT32_C(1) << (i * 4 + bit);
       }
-      in_bitmap = false;
-      ch = '\0';
+      if (!ok) break;
+      bm[bm_idx ++] = row;
+    } else if (strcmp(cmd, "STARTFONT") == 0) {
+      if (started) { ok = false; break; }
+      started = true;
+    } else if (strcmp(cmd, "FONTBOUNDINGBOX") == 0) {
+      int box[4];
+      if (!started || bounds || glyph || !fields(p, box, 4) ||
+          box[0] <= 0 || box[0] > 32 || box[1] <= 0 || box[1] > 32) { ok = false; break; }
+      w = box[0]; h = box[1]; w1 = box[2]; h1 = box[3]; bounds = true;
+    } else if (strcmp(cmd, "STARTCHAR") == 0) {
+      if (!bounds || glyph || !fields(p, &ch, 1, 16) || ch < 0) { ok = false; break; }
+      glyph = true; bbx = false;
+    } else if (strcmp(cmd, "BBX") == 0) {
+      if (!glyph || bbx || !fields(p, bm_bbx, 4) ||
+          bm_bbx[0] < 0 || bm_bbx[0] > 32 || bm_bbx[1] < 0 || bm_bbx[1] > 32) { ok = false; break; }
+      bbx = true;
     } else if (strcmp(cmd, "BITMAP") == 0) {
-      in_bitmap = true;
-      bm_idx = 0;
-    } else if (in_bitmap) {
-      int idx = 0;
-      bm[bm_idx] = 0;
-      for (const char *p = buf; *p != '\n'; p ++) {
-        int val;
-        if (*p >= '0' && *p <= '9') val = *p - '0';
-        else val = *p - 'A' + 10;
-        for (int i = 0; i < 4; i ++) {
-          if ((val >> (3 - i)) & 1) {
-            bm[bm_idx] |= 1 << idx;
-          }
-          idx ++;
-        }
-      }
-      bm_idx ++;
-    }
-    if (strcmp(cmd, "ENDFONT") == 0) {
-      break;
+      if (!glyph || !bbx) { ok = false; break; }
+      in_bitmap = true; bm_idx = 0;
+    } else if (strcmp(cmd, "ENDCHAR") == 0) {
+      if (!glyph || !in_bitmap || bm_idx != bm_bbx[1]) { ok = false; break; }
+      if (ch < 256) create(ch, bm_bbx, bm, bm_idx);
+      in_bitmap = false; glyph = false;
+    } else if (strcmp(cmd, "ENDFONT") == 0) {
+      if (!bounds || glyph) { ok = false; break; }
+      ended = true; break;
     }
   }
 
+  if (ferror(fp)) ok = false;
   fclose(fp);
+  if (!ok || !ended) {
+    for (uint32_t *&pixels: font) { delete [] pixels; pixels = NULL; }
+    w = h = w1 = h1 = 0;
+  }
 }
 
 BDF_Font::~BDF_Font() {
   for (uint32_t *pixels: font) {
-    if (pixels) delete [] pixels;
+    delete [] pixels;
   }
 }
diff --git a/navy-apps/libs/libbdf/src/SDL_bdf.cpp b/navy-apps/libs/libbdf/src/SDL_bdf.cpp
index 15026da0e88c38512efe96ea7d944b0119757a45..e9c89383ba7c1df80d0243fe898cae7b65dc3134 100755
--- a/navy-apps/libs/libbdf/src/SDL_bdf.cpp
+++ b/navy-apps/libs/libbdf/src/SDL_bdf.cpp
@@ -3,11 +3,12 @@
 #include <assert.h>
 
 SDL_Surface* BDF_CreateSurface(BDF_Font *font, char ch, uint32_t fg, uint32_t bg) {
-  uint32_t *bm = font->font[ch];
+  if (!font || font->w <= 0 || font->w > 32 || font->h <= 0 || font->h > 32) return NULL;
+  uint32_t *bm = font->font[(unsigned char)ch];
   if (!bm) return NULL;
   int w = font->w, h = font->h;
   uint32_t *pixels = (uint32_t *)malloc(w * h * sizeof(uint32_t));
-  assert(pixels);
+  if (!pixels) return NULL;
   for (int j = 0; j < h; j ++) {
     for (int i = 0; i < w; i ++) {
       pixels[j * w + i] = ((bm[j] >> i) & 1) ? fg : bg;
```

## 恢复、清理与本组停点

`local/entry.json`固定授权/旧HEAD/8正式资产；`repair-root.patch/archive-validation`与正文完整diff可从旧Git重建，未提交最终源保留patch。`make-tests.py`生成小字体、`font-reference.py`读取已有7字体生成oracle，`run-host.py before/final`保存实际命令/退出/日志；旧源须从70983d4重建后执行before。`prepare-runtime.py`复现标准update，`standard-path/run-standard.local nanos`复现三前台；`prepare-guest.py`直接使用当前最终suite/全部小字体创建诊断盘，`run-guest.py`执行；`refresh-guest.py`只记录本轮测试迭代，冷启动不需重复。实际环境/命令见build/result JSON，无下载/安装步骤。identity/standard-input/source/artifact/member/visual-qa与preclean记录当时证据；截图删除后不能直接打开，须重新运行再生。全部辅助测试/JSON/log仅本地保留不入库。

本次235身份、29归档、93preclean通过；验证进程/构建session均已结束后清理9398路径510228359逻辑字节，零tracked删除。删除隔离源码/构建树/目标/盘/截图/对象/库/pycache；`cleanup-plan/cleanup-receipt`逐路径SHA解释旧manifest预期缺失，保留最小suite/生成器/完整patch/命令结果和身份，正式8资产/用户盘/配置及原nested差异未动。commit不等于ignored证据/.agent或正式资源备份。

F0105/F0109 Completed；5生产文件127增80删。累计89已修/30未修完（含5CQ与F0040 Partial），前87均确认提交；本组结果确认/根commit Pending，Working tree contains uncommitted CRP repair/documentation changes。根HEAD70983d4，根/ONS/libc index均空，无push/安装，不推进M2。未来只沿`.agent/TASK_QUEUE.md#crp-next`，F0111 Next/Planned、未Start；本组确认/commit门槛及另有执行授权满足后再继续。F0112/PAL RIX、F0107/F0108字体缓存/OpenFontRW等保持独立，不以本次修复替代其契约。

可在当前对话继续：本组只有两个相关解析器，证据已归档且恢复入口明确；会话建议不增加审批或启动Prompt门槛。本组完成后停止，等待用户确认/提交。

最终终检补充：476项PASS，101份保留文件manifest，21条原始diff空白逐条核对仅证据字节；实际改动路径/清理缺失解释/本组计数与唯一入口一致，无残余二进制或截图。复用本次Completion，不重复快照；本组仍待结果确认/根commit。
