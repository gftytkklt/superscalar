# CRP RWops 与图像加载组（2026-10-20）

## 整体计划与授权

用户“提交后继续”确认前图形组并授权其实际提交后沿TASK_QUEUE#crp-next执行一个工作单元。前组实际根a27a262，6路径/blob核对一致，提交后根/index干净。复用既有CRP总体计划/工作流；本组F0099/F0104/F0106，不推进M2，不自动提交新组或push。

目标与边界：F0099只修内存RWops构造、长度乘积、seek及pos不变量，保留合法既有读写/底层buffer所有权；F0104维持现有24bit未压缩bottom-up BMP子集，核header/offset/尺寸/stride/分配/seek/短读，统一资源清理及成功后发布尺寸，SDL_LoadBMP失败返回NULL并核现有surface的宽度表达式范围；F0106核定MEM公共入口freesrc与位置限制并安全拒绝不支持输入，不扩codec/字体/窗口/新格式或完整FILE流解码能力。IMAGE其他函数仅共享最小必要处理，避免顺带新增功能。

契约与待核：mem seek继续钳位[0,size]，非法whence返回-1且不改状态；零长度返回0，乘积溢出返回0且保pos/buffer，size*nmemb可表示时沿现有尾部partial bytes并返回完整item数；constructor拒负长度/NULL。SDL1.2 mem_read源码与现有消费者支持该合法读取行为，不另改partial-item策略。BMP不扩top-down/8bit等子集。IMG公开入口保留既有MEM/pos0子集；非0位置/FILE/非法输入返回NULL，不引入新流消费契约。freesrc非0成功或失败均close wrapper，base继续由调用者拥有，freesrc0不推进位置。正常ONS FromMem→isPNG→Load_RW(src,0)及失败JPG fallback依赖此行为；公开限制核验只拒绝原不支持输入，不扩新能力。

步骤（单一工作单元）：保存入口与原反例，逐项最小修复并执行host普通/ASan+UBSan；组合真实RV64定向读流/BMP/图像与现有WAV/mixer交互；隔离复制当前已有源码/正式资源，通过标准nanos目录update→run三前台/hello及实际slide像素/目视。CPU/RT/REF不消费Navy库不重跑，音频共享RWops必须定向验证，ONS实际图像路径须核对。之后完整diff/逐句说明与正反应用、同版源码/对象/库/链接/安装/盘核对、记录/状态/索引/完成快照、产物清理。

交付与验收：三项各有原反例/最终合法结果及错误状态/所有权证据；MEM边界/极值/非法whence、BMP格式/尺寸/短读/分配失败/输出保持/fd清理；IMG现有PNG等合法路径及NULL/FILE/位置/freesrc0与非0、错误解码清理。host不能代替实际RV64/真实消费者。运行检查实际exit/有效PASS/main0/GOOD及判据失败变异，标准三前台/hello有限观察不冒作正常guest退出。源码/命令/日志/SHA/patch最小源本地保存；报告正文完整diff及实现说明入库，生成镜像/ELF/截图/副本完成后清理。正式盘/header/kernel、NEMU/配置及ONS编码/libc原mode保持；不安装或下载。

结束节点：本组必要验证及留档清理完成后报告真实完成/未修/未测及唯一下一入口并停止，等待用户结果确认和commit。真实契约冲突/安装/系统变更立即停依赖动作，不自行裁决。

参考：2026-10-20读取[SDL1.2 RWops源码](https://raw.githubusercontent.com/libsdl-org/SDL-1.2/main/src/file/SDL_rwops.c)、[IMG_Load_RW文档](https://www.libsdl.org/projects/old/SDL_image/docs/SDL_image_12.html)及[讲义文件系统](https://ysyx.oscc.cc/docs/ics-pa/3.4.html)，结合本地SERVICE_RUNTIME/MEDIA_RUNTIME及三条FINAL_FINDINGS，不承诺完整上游能力。

## 执行结果

F0099/F0104/F0106 Completed；结果确认与本组根commit Pending。前84项已确认提交，本组三项不自动提交。


## 逐项实现与验收

| ID | 具体实现、反例与结果 |
|---|---|
| F0099 | `mem_seek`先选非负base，再比较`offset < -base`或`offset > size-base`后钳位，只有落在范围内才相加，避免先溢出后钳位；非法whence返回-1且不写pos。`mem_read/write`先判零与`size > SIZE_MAX/nmemb`，再以size_t求need/avail/min，避免signed need变负和乘积wrap；可表示的大请求只复制真实剩余容量。FromMem拒NULL/负size，非NULL空buffer仍支持；MEM close只free wrapper。原普通60检查17失败；原UBSan `1+INT64_MAX`溢出、ASan SIZE_MAX后base-1读取、read/write wrap四独立反例均见日志。最终host普通/ASan+UBSan各60/60，四独立反例两构建均exit0；FILE部分字节保持，partial bytes消费不改。 |
| F0104 | `BMP_Load`短header不再assert；type/planes、DIB>=40及`offset>=14+DIB`、24bit/compression0、正宽高在转int前核定。size_t除法检查分配及stride，uint64检查完整含padding尾<=LONG_MAX，真实file_size须覆盖；malloc后每行seek/read必须成功才作原BGR到uint32的反向扩展，row索引用size_t。失败统一free/fclose，成功fclose后才发布width/height，close失败也释放像素。扩展DIB108保持；metadata中非解码所需filesize/sizeimg不新增真实性要求。`SDL_LoadBMP`失败返回NULL，额外以`UINT16_MAX/sizeof(uint32_t)`拒绝现有surface pitch不能表达的宽，避免16384截断assert，合法16383保持；成功移除PREALLOC使surface接管像素。构造器若返回NULL则free pixels，但其通用malloc assert未在此改写。原不支持bitcount/compression各exit1资源见证、短header实际SIGABRT -6、短像素错误成功exit1均保留；最终47 host案×两构建通过，精确fd6→6/owner闭合；另真实BMP+SDL/video构造器83断言×两构建通过（含16383/16384实际文件），大尺寸交接stub单列为模型。 |
| F0106 | `IMG_Load_RW`先置surface=NULL，只有非NULL、MEM、seek有效、base有效、0<size<=INT_MAX且tell==0才解码。保留整个MEM/pos0子集；非0位置/FILE/未知type明确NULL，不再从base静默错误解码或assert。统一尾部按`freesrc!=0`关闭有效wrapper，无论成功/识别失败/IDAT解码失败/拒绝输入；borrowed base仍由调用者释放。freesrc0保持pos0不推进，兼容ONS正常isPNG→Load_RW及JPG fallback。原offset错误成功、freesrc1/type断言、NULL崩溃各见证；最终普通/ASan+UBSan各46组exit0，PNG2×1含alpha、PNM像素、freesrc0/1/-7、位置/类型/长度/截断错误及owner均通过。STB现有131072B静态bitreverse LUT预热后新增保留分配0、cache保持；不宣称通用泄漏/任意恶意编码安全。 |

RW最终共享头改用带guard的SDL.h供组合guest include，原host头重复定义风险消除；新host最终普通/san60项重跑结果在`local/rw-integrated-header-results.json`，原`rw-results.json`保持当时历史。首次-Werror因SDL.h原有未用参数失败日志保留，最终命令只加-Wno-unused-parameter；没有生产接口变更。

BMP与IMG初次LeakSanitizer受ptrace沙箱限制失败，原日志保留；最终ASan+UBSan明确`detect_leaks=0`。BMP以精确malloc/free/fd、IMG以owner close及预热后allocation余额补充有限资源证据，不冒充LSan成功。STB浮点/数学适配沿已有fixedpt实现，host日志及实际编译参数为准。

## 同版真实RV64及标准消费者

隔离当前已有源码/资源，不修改正式盘/header/kernel、NEMU/config或ONS/libc历史差异。标准nanos目录执行`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= update`首轮28.183秒exit0；SDL_bmp.c有符号比较cast最终化后复制并增量执行同命令，最终刷新17.759秒exit0，结果见`local/standard-path/update-final-refresh-result.json`，实际run使用最终版本。共享源码/资源均来自现有工作区，无下载/安装。

实际RV64目标通过实际libminiSDL/libbmp/libSDL_image/libSDL_mixer/libndl/newlib，不stub FILE/RWops/decoder/surface：RW60、BMP83（两合法逐像素/扩展DIB、12非法BMP、NULL、真实16383/16384 pitch、24次失败清理）、IMG46组；主线另130断言核3×2 BMP精确像素、SDL失败返回、100次失败后真实fd可复用、IMG_Load文件PNG及SDL文件WAV/mixer带3byte前缀MEM WAV共享读流，溢出请求不污染后续WAV加载。三套子suite及主线各有精确唯一PASS，main0/exit0/GOOD；六种非零exit/缺PASS/错计数/错main/重复PASS/BAD判据变异全部拒绝。旧43组IMG的首轮实际guest结果保留`*-initial`，新增IDAT cleanup三组后只重建最终header/目标/诊断盘与内核，再实际运行46组通过；生产源码未变，标准回归不重复。

标准`make ... run`54.656秒，自有组SIGTERM（make -15），非guest正常退出。10次真实SDL输入；PAL→NTerm/qzx command-not-found→slide0/1/0→PAL/Return继续渲染，hello首次帧34→末帧152，8帧实际目视已记录。三张slide帧400×300的全部RGB像素与实际安装BMP输入逐字节相等；slide0/返回0帧SHA相等、slide1不同。canvas外保留前一前台背景属既有行为；PAL Return不夸称某菜单。`SDL_VIDEODRIVER/AUDIODRIVER=dummy`是实际NEMU设备路径，不能证明物理屏幕/听音体验。

真实ONS消费链为FromMem→isPNG保存恢复→Load_RW(src,0)→必要JPG fallback→close，公共suite同样核其位置/所有权序列；snow的freesrc1入口现安全关闭wrapper，builtin layer未启用，不声称真实游戏脚本已执行。CPU/RT/REF不消费Navy这些库不重跑；NPC/其他ISA/native/NWM/实体AV/长时NotRun。没有性能策略修改或性能新增结论，前组长绘图推迟补音结论不被本组功能验收替代。

## 框架代码完整diff及语句说明

旧根完整commit `a27a262b94255e36d4f26afe10f5d7893b75590f`，新为2026-10-20本组未提交工作树；实际4生产文件及SHA如下，video.c未改（计划初期曾作wrapper候选位置，实际wrapper在libbmp/SDL_bmp.c）。正文保留全部修复hunks，具体分支/计算/拷贝/返回/资源发布语句及失败契约已逐项解释。`local/archive-validation.json`证明24项正反应用/字节/mode检查全部通过。

| 根仓相对路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `navy-apps/libs/libminiSDL/src/file.c` | `da9daa083ef4bb1c692c4babfbea0174e2a6921a42bfb04e271bded6a5ce5678` | `17e652880d0be76123cce2746e5b07e224ebff3c0f2eda8cf83470ccd7f79d24` |
| `navy-apps/libs/libbmp/src/BMP.c` | `31b62fb6d3590fd5925d39b57815ef2aec15cfecc8923eef7e5b491533ec005b` | `8b6b34e093eccb10a517d7c35f527c03863b1c9f919308ae82125abac4628a2d` |
| `navy-apps/libs/libbmp/src/SDL_bmp.c` | `26bbfedfae608475b18bd6a5ac6d8ab95ee1b8e752b36ebc36a0fb9092fb68f3` | `33a0b55d4a8e1ae3e67ee8aa8acf6f81210feff90644bf5d0c8fbf83a2292e77` |
| `navy-apps/libs/libSDL_image/src/image.c` | `e8a6132804d841d9fb2968bed5bc0b461e47c67d78dbec5effe690caf7f760f5` | `5cbb3c1ee201928209d86241fd9737fbc72a2de50b66179dc5f6301ffa4c5272` |

```diff
diff --git a/navy-apps/libs/libSDL_image/src/image.c b/navy-apps/libs/libSDL_image/src/image.c
index fe68f1fea2065c3b224e6511441e5f01da14f496..50a27dc5b5dfc725dbba1e33908e85651188db28 100755
--- a/navy-apps/libs/libSDL_image/src/image.c
+++ b/navy-apps/libs/libSDL_image/src/image.c
@@ -6,14 +6,22 @@
 #include <stdlib.h>
 #include <string.h>
 #include <assert.h>
+#include <limits.h>
 
 #define SDL_STBIMAGE_IMPLEMENTATION
 #include "SDL_stbimage.h"
 
 SDL_Surface* IMG_Load_RW(SDL_RWops *src, int freesrc) {
-  assert(src->type == RW_TYPE_MEM);
-  assert(freesrc == 0);
-  return STBIMG_LoadFromMemory(src->mem.base, src->mem.size);
+  SDL_Surface *surface = NULL;
+  /* The memory decoder supports a complete buffer at position zero only. */
+  if (src != NULL && src->type == RW_TYPE_MEM && src->seek != NULL &&
+      src->mem.base != NULL && src->mem.size > 0 && src->mem.size <= INT_MAX &&
+      SDL_RWtell(src) == 0) {
+    surface = STBIMG_LoadFromMemory(src->mem.base, (int)src->mem.size);
+  }
+  /* Closing a memory RWops releases its wrapper, not the borrowed buffer. */
+  if (src != NULL && freesrc && src->close != NULL) SDL_RWclose(src);
+  return surface;
 }
 
 SDL_Surface* IMG_Load(const char *filename) {
diff --git a/navy-apps/libs/libbmp/src/BMP.c b/navy-apps/libs/libbmp/src/BMP.c
index 9d6a306ab7686a1daa9d3269e1cfa2d17d31dd25..d1a306afe9d87b4092bdbb6fe1fe7515b6831a8f 100755
--- a/navy-apps/libs/libbmp/src/BMP.c
+++ b/navy-apps/libs/libbmp/src/BMP.c
@@ -2,6 +2,7 @@
 #include <stdint.h> 
 #include <stdlib.h>
 #include <assert.h>
+#include <limits.h>
 
 struct BitmapHeader {
   uint16_t type;
@@ -20,33 +21,57 @@ struct BitmapHeader {
 } __attribute__((packed));
 
 void* BMP_Load(const char *filename, int *width, int *height) {
-  FILE *fp = fopen(filename, "r");
+  if (!filename) return NULL;
+  FILE *fp = fopen(filename, "rb");
   if (!fp) return NULL;
 
   struct BitmapHeader hdr;
+  uint32_t *pixels = NULL;
   assert(sizeof(hdr) == 54);
-  assert(1 == fread(&hdr, sizeof(struct BitmapHeader), 1, fp));
+  if (fread(&hdr, sizeof(hdr), 1, fp) != 1) goto fail;
 
-  if (hdr.bitcount != 24) return NULL;
-  if (hdr.compression != 0) return NULL;
+  if (hdr.type != 0x4d42 || hdr.planes != 1 || hdr.ih_size < 40 ||
+      hdr.ih_size > UINT32_MAX - 14 || hdr.offset < 14 + hdr.ih_size ||
+      hdr.bitcount != 24 || hdr.compression != 0 ||
+      hdr.width == 0 || hdr.width > INT_MAX ||
+      hdr.height == 0 || hdr.height > INT_MAX) goto fail;
   int w = hdr.width;
   int h = hdr.height;
-  uint32_t *pixels = malloc(w * h * sizeof(uint32_t));
+  if ((size_t)w > SIZE_MAX / sizeof(uint32_t) / (size_t)h ||
+      (size_t)w > (SIZE_MAX - 3) / 3) goto fail;
+  size_t line_off = ((size_t)w * 3 + 3) & ~(size_t)3;
+  uint64_t offset = hdr.offset;
+  if (offset > LONG_MAX ||
+      (uint64_t)h > ((uint64_t)LONG_MAX - offset) / line_off) goto fail;
+  long data_end = offset + (uint64_t)h * line_off;
+  if (fseek(fp, 0, SEEK_END) != 0) goto fail;
+  long file_size = ftell(fp);
+  if (file_size < data_end) goto fail;
+  pixels = malloc((size_t)w * h * sizeof(uint32_t));
+  if (!pixels) goto fail;
 
-  int line_off = (w * 3 + 3) & ~0x3;
   for (int i = 0; i < h; i ++) {
-    fseek(fp, hdr.offset + (h - 1 - i) * line_off, SEEK_SET);
-    int nread = fread(&pixels[w * i], 3, w, fp);
+    long row_off = offset + (uint64_t)(h - 1 - i) * line_off;
+    uint32_t *row = pixels + (size_t)w * i;
+    if (fseek(fp, row_off, SEEK_SET) != 0 ||
+        fread(row, 3, w, fp) != (size_t)w) goto fail;
     for (int j = w - 1; j >= 0; j --) {
-      uint8_t b = *(((uint8_t*)&pixels[w * i]) + 3 * j);
-      uint8_t g = *(((uint8_t*)&pixels[w * i]) + 3 * j + 1);
-      uint8_t r = *(((uint8_t*)&pixels[w * i]) + 3 * j + 2);
-      pixels[w * i + j] = (r << 16) | (g << 8) | b;
+      uint8_t *src = (uint8_t *)row + (size_t)3 * j;
+      uint8_t b = src[0], g = src[1], r = src[2];
+      row[j] = (r << 16) | (g << 8) | b;
     }
   }
 
-  fclose(fp);
+  if (fclose(fp) != 0) {
+    free(pixels);
+    return NULL;
+  }
   if (width) *width = w;
   if (height) *height = h;
   return pixels;
+
+fail:
+  free(pixels);
+  fclose(fp);
+  return NULL;
 }
diff --git a/navy-apps/libs/libbmp/src/SDL_bmp.c b/navy-apps/libs/libbmp/src/SDL_bmp.c
index eb6af1a5ba2de9c32cb4342b15400cc155d1bb48..f071e8ea042a1c1dd1a95793efe119a3b289c57d 100755
--- a/navy-apps/libs/libbmp/src/SDL_bmp.c
+++ b/navy-apps/libs/libbmp/src/SDL_bmp.c
@@ -1,13 +1,17 @@
 #include <SDL_bmp.h>
 #include <BMP.h>
-#include <assert.h>
+#include <stdlib.h>
+#include <stdint.h>
 
 SDL_Surface* SDL_LoadBMP(const char *filename) {
   int w, h;
   void *pixels = BMP_Load(filename, &w, &h);
-  assert(pixels);
+  if (pixels == NULL) return NULL;
+  // SDL stores pitch in uint16_t; reject widths the surface cannot represent.
+  if (w <= 0 || h <= 0 || w > (int)(UINT16_MAX / sizeof(uint32_t))) { free(pixels); return NULL; }
   SDL_Surface *s = SDL_CreateRGBSurfaceFrom(pixels, w, h, 32, w * sizeof(uint32_t),
       DEFAULT_RMASK, DEFAULT_GMASK, DEFAULT_BMASK, DEFAULT_AMASK);
+  if (s == NULL) { free(pixels); return NULL; }
   s->flags &= ~SDL_PREALLOC;
   return s;
 }
diff --git a/navy-apps/libs/libminiSDL/src/file.c b/navy-apps/libs/libminiSDL/src/file.c
index e413e25a0e630cdac11878d87d09736513e0041b..cb18ba4e1221898a8491d70935252fb5ab0a78d5 100755
--- a/navy-apps/libs/libminiSDL/src/file.c
+++ b/navy-apps/libs/libminiSDL/src/file.c
@@ -45,33 +45,38 @@ static int64_t mem_size(SDL_RWops *f) {
 }
 
 static int64_t mem_seek(SDL_RWops *f, int64_t offset, int whence) {
-  ssize_t pos = ((MemRW *)f)->pos;
+  int64_t base;
   switch (whence) {
-    case RW_SEEK_SET: pos = offset; break;
-    case RW_SEEK_CUR: pos += offset; break;
-    case RW_SEEK_END: pos = f->mem.size + offset; break;
+    case RW_SEEK_SET: base = 0; break;
+    case RW_SEEK_CUR: base = ((MemRW *)f)->pos; break;
+    case RW_SEEK_END: base = f->mem.size; break;
+    default: return -1;
   }
-  if (pos < 0) pos = 0;
-  if (pos > f->mem.size) pos = f->mem.size;
+  int64_t pos;
+  if (offset < -base) pos = 0;
+  else if (offset > f->mem.size - base) pos = f->mem.size;
+  else pos = base + offset;
   ((MemRW *)f)->pos = pos;
   return pos;
 }
 
 static size_t mem_read(SDL_RWops *f, void *buf, size_t size, size_t nmemb) {
+  if (size == 0 || nmemb == 0 || size > SIZE_MAX / nmemb) return 0;
   ssize_t pos = ((MemRW *)f)->pos;
-  ssize_t avail = (pos < f->mem.size) ? (f->mem.size - pos) : 0;
-  ssize_t need = size * nmemb;
-  ssize_t n = (need < avail) ? need : avail;
+  size_t avail = f->mem.size - pos;
+  size_t need = size * nmemb;
+  size_t n = (need < avail) ? need : avail;
   if (n > 0) memcpy(buf, (char *)f->mem.base + pos, n);
   ((MemRW *)f)->pos = pos + n;
   return (size > 0) ? (n / size) : 0;
 }
 
 static size_t mem_write(SDL_RWops *f, const void *buf, size_t size, size_t nmemb) {
+  if (size == 0 || nmemb == 0 || size > SIZE_MAX / nmemb) return 0;
   ssize_t pos = ((MemRW *)f)->pos;
-  ssize_t avail = (pos < f->mem.size) ? (f->mem.size - pos) : 0;
-  ssize_t need = size * nmemb;
-  ssize_t n = (need < avail) ? need : avail;
+  size_t avail = f->mem.size - pos;
+  size_t need = size * nmemb;
+  size_t n = (need < avail) ? need : avail;
   if (n > 0) memcpy((char *)f->mem.base + pos, buf, n);
   ((MemRW *)f)->pos = pos + n;
   return (size > 0) ? (n / size) : 0;
@@ -98,6 +103,7 @@ SDL_RWops* SDL_RWFromFile(const char *filename, const char *mode) {
 }
 
 SDL_RWops* SDL_RWFromMem(void *mem, int size) {
+  if (mem == NULL || size < 0) return NULL;
   MemRW *m = malloc(sizeof(MemRW));
   if (m == NULL) return NULL;
   m->pos = 0;
@@ -108,4 +114,4 @@ SDL_RWops* SDL_RWFromMem(void *mem, int size) {
     .mem = { .base = mem, .size = size },
   };
   return &m->rw;
-}
\ No newline at end of file
+}
```

## 恢复与证据入口

本地`entry.json`保存授权/原HEAD/源身份/8正式资产，`repair-root.patch/archive-validation`保存可从Git旧基线重建的差异；`rw-*`、`bmp-results/commands/result/cleanup`、`bmp-host.c/bmp-guest.c/bmp-fixtures.py`、`img-reproduce.py/img-tracked-*`为host配方/原反例/最终结果。冷恢复先从旧HEAD重建4源并应用完整patch（或使用已验收最终源），保留实际原工具链/外部资源身份，不安装。运行`prepare-runtime.py`按标准update生成隔离环境；`standard-path/run-standard.local nanos`运行标准三前台。运行`prepare-guest.py`装目标/最小资源到诊断盘，再`run-guest.py`执行最终组合；`refresh-guest.py`记录本轮最后3组IDAT增量，仅恢复本轮初始中间状态时使用，冷启动最终源直接prepare即可。实际命令/返回/身份见JSON和日志。截图及镜像清理后须再生，不能声称可直接打开。


## 最终身份、清理与停点

最终338项身份核对通过：79份源/配置、35份关键产物、4薄库28个唯一对象/173条引用；108标准盘extent及5应用linked=installed=disk，25诊断payload绑定最后RW60/BMP83/IMG46/root130运行。7640份隔离入口输入仅已记SDL_bmp cast刷新变化，其余无漂移；完整diff24项、最终141项preclean、8实际目视及3帧全像素匹配均通过。见`local/identity-validation.json`、`standard-input-validation.json`及各身份JSON。首轮preclean只有RW日志名匹配写错而拒绝，修正为实际文件后141项全过，不是产品失败或放宽oracle。

确认所有验证/构建进程结束后，先前BMP子验证清理24路径766313B（`local/bmp-results/cleanup.json`），随后统一清理9423路径511885826B（`local/cleanup-plan.json`/`cleanup-receipt.json`）；合计9447路径512652139逻辑字节，零tracked删除。包含隔离源码/构建树、旧Git源码副本、ELF/镜像/对象/库/截图/生成BMP/PNG及pycache。旧manifest/命令中的相关路径预期缺失，按两份回执解释；截图的实际目视与RGB/原SHA保留文字，不能再宣称原图可直接打开。正式8资产/用户盘/配置、ONS原编码/libc850mode保持；保留日志/命令/最小源/生成配方/完整diff/结果和身份，不把commit当本地资产备份。

F0099/F0104/F0106三项Completed；4生产源74增31删，新结果确认与根commit Pending，未push。累计87已修/32未修完（含5CQ、F0040 Partial等），前84均确认提交。唯一后续入口 `.agent/TASK_QUEUE.md#crp-next`，未来BDF/终端组F0105/F0109 Next/Planned、未Start；本组确认/提交及执行授权满足后再开始，不自动进入下一组/M2。未实施性能策略，F0043/F0118/PAL RIX及字体缓存只读/完整OpenFontRW仍独立。通用surface构造器OOM及IMG大尺寸编码触发既有assert、伪造指针/对象后方allocation大小、readonly/线程/实体AV/其他ISA/长期均未作完整保证，不将最小子集修复泛化为完整SDL。

建议开启新对话：本轮已完成前组提交及三项新修复、host/真实guest/标准消费者证据，下一组转BDF/终端解析，当前唯一入口与恢复材料完备；此建议不增加批准或启动Prompt门槛。本组完成后停止，等待用户结果确认/提交。
