# CRP CCR-F0111 — bird资源加载（2026-10-20）

## 整体计划与授权

用户“提交后继续”确认BDF/终端组，已实际提交13d30a9，提交后根working tree/index干净；本轮授权TASK_QUEUE唯一下一入口F0111一个工作单元，新组不自动commit/push，不推进M2。复用CRP总体计划及workflow，既有bird HEAD79e4ea3的21mode与Video.h高度300均与P8 provenance一致，保持原样，src/Sprite.cpp/include/Sprite.h字节与原审阅基线一致。

目标/范围：只修Sprite构造/加载失败状态、描述名称与整数/rect/alpha读取边界、条目及texture所有权与重复实例；保留合法atlas图像/描述、first duplicate wins、Draw/DrawEx现有混合与不旋转行为、公开接口及玩法/音频/Make流程，不改Video.h。现有hsearch_r虽有接口，但实际hdestroy_r节点清理被#if0关闭；本组在CSprite私有512桶内管理owned链节点，保持hash查找与首个同名条目语义，无全局table或新libc改动，不设新的固定记录条数上限。

阶段：本组一个修复阶段。交付bird nested两源最小改动、host原反例/普通sanitizer/实际RV64共用suite、标准update→run及真实bird消费、nested完整diff/说明与正反应用/同版身份、记录索引/状态/产物清理。源码保留nested归属，不把21mode/Video.h或整个库纳入根跟踪。

验收：原缺图析构/长名称/错误rect及失败后Draw、重复构造明确见证；最终NULL/缺图缺描述/截断/超长name/整数溢出/负或超界rect/合法边界与alpha两分支、重复名称/多个同时存在实例/重复load-destroy。host实际SDL代码普通与ASan+UBSan、实际RV64精确PASS/main0/GOOD和判据故障拒绝；真实atlas逐条输出像素保持、标准nanos既有update→run三前台hello与目视/像素、实际bird标题/动画（不扩玩法验收）。实际源码→对象→链接→安装→盘绑定，完整diff正反与清理后停等用户确认/根及nested提交。真实策略/安装未决即停；当前无待裁决项。

必读/恢复：FINAL_FINDINGS F0111、APP_OS_CALLS、MEDIA_RUNTIME、实际Sprite/BirdGame与atlas.png/txt、本地libc hcreate_r实现及P8 provenance；前组crp-bdf-term README#submit-20261020、当前entry。后续唯一TASK_QUEUE#crp-next。

## 实现与失败契约

nested根`navy-apps/apps/bird/repo`中仅`src/Sprite.cpp/include/Sprite.h`，111增61删；原`Video.h`高度300及21mode差异保留，不改玩法/音频/Make/公开函数签名。

构造初始化`m_pTexture=NULL`、两维度0和全部桶NULL；`Clear()`逐节点free name/entry后释放texture，全部指针/尺寸复位，供析构和加载失败共同调用。NULL文件名/缺图/转换失败/描述失败成为可安全析构、Draw/DrawEx无输出的对象；查找前核texture/renderer、Find核NULL tag。名称/条目为实例自身拥有，512桶链按unsigned hash索引，保留首次同名条目，独立实例销毁互不影响；条目数量不绑定512桶容量，600条及碰撞实际通过。`hsearch_r`虽有声明，但当前`hdestroy_r`的节点回收在#if0内，所以本组使用private owned链，未改libc或新增全局共享表。每节点只在全部字段及资源成功后链接，strdup失败释放未链接entry；中途失败Clear清除此前有效条目。

`ReadToken()`通过fgetc按实际文件字节读取、unsigned char送isspace；255字符容量前核限，内嵌NUL拒绝，干净EOF/文件错误分开。保留原描述按空白分隔、可跨行且可无末newline的契约，不强制一行一条。四整数用strtol和完整尾部/ERANGE/0..USHRT_MAX检查后再写入unsigned short字段；width/height须正，先核x/y处于图内，再用`w > textureWidth-x`/`h > textureHeight-y`防加法溢出和越界，合法边缘接受。alpha读取用size_t与实际pitch计算行，所有坐标均已验证；遇首个非255 alpha即可结束扫描，分类与原算法相同。原myBlit/DrawEx不旋转和混合算式保持。

没有为外部并发、拷贝CSprite实例、伪造SDL对象、通用decoder大图/OOM、恶意hash碰撞性能或任意INT_MIN Draw坐标提供新保证；公开Draw原clip算法未重写，合法现有资源输出和消费场景本轮验收。

## 原反例与host验证

`python3 local/make-fixtures.py`生成4×3有透明/半透明/不透明像素PNG及最小描述；修改前`python3 local/run-host.py before`：预填0xa5对象缺图后析构，普通SIGSEGV、UBSan无效/未对齐surface读；长256名称ASan stack-buffer-overflow、负坐标和部分非法描述ASan heap-buffer-overflow；同时两个对象触发原hcreate assert，普通partial描述未安全拒绝。普通longname/negative/wide中有exit0控制，宽5×1跨行但仍落底层buffer内的例子未触发ASan，保留原日志，不把每个无效rect都说成必然越过总allocation。

最终`python3 local/run-host.py final`用实际Sprite、IMG/STB、miniSDL file/video/general（gc-sections去掉未调用NDL），普通与ASan+UBSan各767断言通过：14类缺描述/长name/负或零/越界rect/溢出/长整数/截断/非数字/尾垃圾/NUL，NULL路径及缺图确定失败、合法和opaque/alpha两路径、最大255名称/多行无末newline/重复名首个优先、两个不同atlas同时存在及任意销毁次序、30次load/destroy、600记录及碰撞、真实71条atlas共548240输出像素逐个与独立R/B转换+原混合公式匹配，hash2203439073。

host仅针对自身编译代码用malloc/calloc/realloc/free/strdup wrappers跟踪分配，decode预热后live4→4；包含节点/name/texture/失败资源，不追踪全部libstdc++或系统内部，不能泛化为通用泄漏证明。ASan/UBSan参数明确detect_leaks=0/abort_on_error=1/halt_on_error=1，沿已知沙箱ptrace限制不称LSan成功。初次本地测试编辑脚本因引号错误未生效，纠正后以最终源重跑，不影响生产契约。

## 实际RV64与标准真实消费者

`python3 local/prepare-runtime.py`复制已有源码/资产并remap symlink，仅隔离目录构建，无下载/安装。标准nanos目录执行`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= update` exit0，28.333秒。`prepare-guest.py`编译实际Sprite.cpp/SDL/IMG/newlib及同套suite，标准盘追加诊断app和22payload；只改诊断初始应用/SYS_exit oracle。实际RV64最终765断言、71条atlas/548240像素/hash2203439073、main0/exit0/GOOD，六非零exit/缺PASS/错计数/错main/重复PASS/BAD判据故障全部拒绝。

初次guest本身765断言/GOOD，但printf不支持测试用%zu，atlas行打印成pixels=zu/hash错位而被严格oracle拒绝；仅把诊断统计改%lu并显式unsigned long，重新host两构建、测试目标/诊断盘/内核及实际guest验证，生产源码及标准盘不变。原错误日志/结果保留initial；不放宽最终oracle。冷启动直接用最终suite和prepare-guest，无须先做中间refresh。

标准`make ... run`54.655秒，PAL→F2 NTerm/qzx command-not-found后prompt→F3 slide0/1/0→F1 PAL/Return持续渲染，hello首帧32→末143。八帧contact已实际目视；两NTerm帧各排除blink cursor一个cell，其余69797 RGB像素与旧Courier模型相等，slide0返回帧SHA恢复。另仅FG slot1 nterm→bird的诊断内核，标准盘/库/真实bird链接未改；23.661秒采三帧标题/按钮/小鸟/地面，动画不同、hello61、Space进真实SDL队列，未证明玩法开始。标准make -15/额外bird host exit0均在自有组SIGTERM请求后结束，不能当guest正常退出。

CPU/RT/REF不依赖bird Sprite不重跑；NPC/其他ISA/native/NWM/完整ONS脚本/实体显示听音/长期NotRun。dummy/LD_PRELOAD只在宿主观察/输入，实际guest与NEMU设备路径不替换。未作性能策略或性能测量，F0043/F0118/PAL RIX/字体缓存等保留各自归属。

## 同版身份及完整nested diff

255项身份通过：31份源/配置、28产物、3薄库17唯一对象/65引用，108标准extent/5应用linked=installed=disk、22诊断payload绑定最终执行，7640原标准入口输入无漂移。标准Sprite.o dep包含最终source与repo/include/Sprite.h（header为合法相对路径，首个checker误假定绝对路径后修正），目标suite/Sprite源字节一致，实际执行nm包含Clear/Find/LoadTxt/Draw等且不引用global hsearch/hcreate/hdestroy；额外bird内核仅指定FG slot改动。root/ONS/libc/bird HEAD及index、8正式资产、21bird原mode与Video.h差异、ONS原编码/libc850mode保持。

旧nested完整commit`79e4ea3ee03487395d7a7cfa1a231d42767f8153`，新为2026-10-20未提交工作树；根记录HEAD`13d30a9bc7faacd2cef0d15601acb031500b5c7f`。以下完整diff只含两源功能变动，用core.filemode=false排除历史mode噪声；预期未来nested提交保持Git100644，实际本地755沿旧事实保留。12归档核对证明旧源SHA、正反apply、逐字节与Git mode相符；初次checker错误用POSIX644比较git apply生成664而拒绝，最终按Git是否executable核100644，并未放过mode变动。

| nested相对路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `src/Sprite.cpp` | `57e9c6f859811a9534bf760c5bc0187585c89a1a2f54a5803cb34d1edbb6b03b` | `209dc444a7a8fed0f0d16cf5d397d67975725f73dc130156e707a673b02d6641` |
| `include/Sprite.h` | `41d95e493bdab9ae7cf067cc79c6ba64d81b73ff72a6a2083dac958fe241d436` | `dffdb962f0c81a60cf51c41d9d2c17dd2fbcca3187bc6208d477ef7d15b44b1a` |

```diff
diff --git a/include/Sprite.h b/include/Sprite.h
index c2cf41c4c9c46eeaf7817929f6f8d098fd674cff..d24864bd2741d38608893b7409784a3d77054f28 100644
--- a/include/Sprite.h
+++ b/include/Sprite.h
@@ -56,6 +56,16 @@ class CSprite
   void                  Load(SDL_Surface *pRenderer, const char *szImageFileName, const char *szTxtFileName);
   bool                  LoadTxt(const char *szTxtFileName);
 
+  struct SpriteEntry {
+    char *name;
+    SpritePart_t part;
+    SpriteEntry *next;
+  };
+  SpriteEntry *m_parts[512];
+  unsigned              Bucket(const char *name) const;
+  SpritePart_t         *Find(const char *name);
+  void                  Clear();
+
   SDL_Surface          *m_pTexture;
   int                   m_iTextureWidth;
   int                   m_iTextureHeight;
diff --git a/src/Sprite.cpp b/src/Sprite.cpp
index f5ad71c90759032ab5b936b8bc380d0586b7fc48..0f67fa3bf82e046755beaf7b0c86c5db6e59e6b5 100644
--- a/src/Sprite.cpp
+++ b/src/Sprite.cpp
@@ -28,24 +28,54 @@
  */
 
 #include "Sprite.h"
-#include <search.h>
+#include <stdlib.h>
+#include <errno.h>
+#include <limits.h>
+#include <ctype.h>
 #include <assert.h>
 #include <string.h>
 
 CSprite::CSprite(SDL_Surface *pRenderer, const char *szImageFileName, const char *szTxtFileName)
+  : m_pTexture(NULL), m_iTextureWidth(0), m_iTextureHeight(0)
 {
-  int ret = hcreate(512);
-  assert(ret);
+  memset(m_parts, 0, sizeof(m_parts));
   Load(pRenderer, szImageFileName, szTxtFileName);
 }
 
-CSprite::~CSprite()
+unsigned CSprite::Bucket(const char *name) const
 {
-  if (m_pTexture != NULL)
-    {
-      SDL_FreeSurface(m_pTexture);
+  unsigned hash = 0;
+  for (const unsigned char *p = (const unsigned char *)name; *p; p ++)
+    hash = hash * 33u + *p;
+  return hash % 512;
+}
+
+SpritePart_t *CSprite::Find(const char *name)
+{
+  if (name == NULL) return NULL;
+  for (SpriteEntry *p = m_parts[Bucket(name)]; p; p = p->next)
+    if (strcmp(p->name, name) == 0) return &p->part;
+  return NULL;
+}
+
+void CSprite::Clear()
+{
+  for (SpriteEntry *&head: m_parts) {
+    while (head) {
+      SpriteEntry *next = head->next;
+      free(head->name);
+      free(head);
+      head = next;
     }
-  hdestroy();
+  }
+  SDL_FreeSurface(m_pTexture);
+  m_pTexture = NULL;
+  m_iTextureWidth = m_iTextureHeight = 0;
+}
+
+CSprite::~CSprite()
+{
+  Clear();
 }
 
 static void myBlit(SDL_Surface *src, SDL_Rect *srcrect, SDL_Surface *dst, SDL_Rect *dstrect, int hasAlpha) {
@@ -118,14 +148,12 @@ static void myBlit(SDL_Surface *src, SDL_Rect *srcrect, SDL_Surface *dst, SDL_Re
 
 void CSprite::Draw(SDL_Surface *pRenderer, const char *szTag, int x, int y)
 {
-  ENTRY item;
-  item.key = (char *)szTag;
-  ENTRY *ret = hsearch(item, FIND);
+  if (m_pTexture == NULL || pRenderer == NULL) return;
+  SpritePart_t *it = Find(szTag);
 
-  if (ret)
+  if (it)
     {
       SDL_Rect srcrect, dstrect;
-      SpritePart_t *it = (SpritePart_t *)ret->data;
 
       srcrect.x = it->X;
       srcrect.y = it->Y;
@@ -143,14 +171,12 @@ void CSprite::Draw(SDL_Surface *pRenderer, const char *szTag, int x, int y)
 
 void CSprite::DrawEx(SDL_Surface *pRenderer, const char *szTag, int x, int y, int angle)
 {
-  ENTRY item;
-  item.key = (char *)szTag;
-  ENTRY *ret = hsearch(item, FIND);
+  if (m_pTexture == NULL || pRenderer == NULL) return;
+  SpritePart_t *it = Find(szTag);
 
-  if (ret)
+  if (it)
     {
       SDL_Rect srcrect, dstrect;
-      SpritePart_t *it = (SpritePart_t *)ret->data;
 
       srcrect.x = it->X;
       srcrect.y = it->Y;
@@ -168,6 +194,7 @@ void CSprite::DrawEx(SDL_Surface *pRenderer, const char *szTag, int x, int y, in
 
 void CSprite::Load(SDL_Surface *pRenderer, const char *szImageFileName, const char *szTxtFileName)
 {
+  if (szImageFileName == NULL || szTxtFileName == NULL) return;
   SDL_Surface *pSurface = IMG_Load(szImageFileName);
 
   if (pSurface == NULL)
@@ -184,64 +211,77 @@ void CSprite::Load(SDL_Surface *pRenderer, const char *szImageFileName, const ch
   to.Rloss = fmt->Bloss; to.Rshift = fmt->Bshift; to.Rmask = fmt->Bmask;
   to.Bloss = fmt->Rloss; to.Bshift = fmt->Rshift; to.Bmask = fmt->Rmask;
   m_pTexture = SDL_ConvertSurface(pSurface, &to, 0);
-  assert(m_pTexture);
   SDL_FreeSurface(pSurface);
+  if (m_pTexture == NULL) { Clear(); return; }
 
   // Load txt file
   if (!LoadTxt(szTxtFileName))
     {
-      SDL_FreeSurface(m_pTexture);
-      m_pTexture = NULL;
+      Clear();
 
       fprintf(stderr, "CSprite::Load(): LoadTxte failed\n");
       return;
     }
 }
 
+// Return 1 for a complete token, 0 for clean EOF, -1 for an invalid token/read.
+static int ReadToken(FILE *fp, char *token)
+{
+  int ch;
+  do { ch = fgetc(fp); } while (ch != EOF && isspace((unsigned char)ch));
+  if (ch == EOF) return ferror(fp) ? -1 : 0;
+  size_t len = 0;
+  do {
+    if (ch == 0 || len == 255) return -1;
+    token[len ++] = (char)ch;
+    ch = fgetc(fp);
+  } while (ch != EOF && !isspace((unsigned char)ch));
+  token[len] = '\0';
+  return ferror(fp) ? -1 : 1;
+}
+
 bool CSprite::LoadTxt(const char *szTxtFileName)
 {
   FILE *fp = fopen(szTxtFileName, "r");
-
-  if (fp == NULL)
-    {
-      return false;
+  if (fp == NULL) return false;
+  bool ok = true;
+  char name[256], token[256];
+  int status;
+  while ((status = ReadToken(fp, name)) == 1) {
+    int values[4];
+    for (int i = 0; i < 4; i ++) {
+      if (ReadToken(fp, token) != 1) { ok = false; break; }
+      char *end;
+      errno = 0;
+      long value = strtol(token, &end, 10);
+      if (end == token || *end || errno == ERANGE || value < 0 || value > USHRT_MAX) {
+        ok = false; break;
+      }
+      values[i] = (int)value;
     }
-
-  while (!feof(fp))
-    {
-      char name[256];
-      int w, h, x, y;
-
-      if (fscanf(fp, "%s %d %d %d %d", name, &w, &h, &x, &y) != 5)
-	{
-	  continue;
-	}
-
-      SpritePart_t *spritePart = new SpritePart_t;
-
-      spritePart->usWidth = w;
-      spritePart->usHeight = h;
-      spritePart->X = x;
-      spritePart->Y = y;
-
-      spritePart->hasAlpha = 0;
-      for (int j = 0; j < h; j ++) {
-        for (int i = 0; i < w; i ++) {
-          int alpha = ((uint8_t *)m_pTexture->pixels)[((y + j) * m_iTextureWidth + x + i) * 4 + 3];
-          if (alpha != 255) {
-            spritePart->hasAlpha = 1;
-            break;
-          }
-        }
+    if (!ok) break;
+    int w = values[0], h = values[1], x = values[2], y = values[3];
+    if (w == 0 || h == 0 || x >= m_iTextureWidth || y >= m_iTextureHeight ||
+        w > m_iTextureWidth - x || h > m_iTextureHeight - y) { ok = false; break; }
+    if (Find(name)) continue; // Preserve the first entry for duplicate names.
+
+    SpriteEntry *entry = (SpriteEntry *)malloc(sizeof(SpriteEntry));
+    if (!entry) { ok = false; break; }
+    entry->name = strdup(name);
+    if (!entry->name) { free(entry); ok = false; break; }
+    entry->part = { (unsigned short)w, (unsigned short)h,
+                    (unsigned short)x, (unsigned short)y, 0 };
+    for (int j = 0; j < h && !entry->part.hasAlpha; j ++) {
+      const uint8_t *row = (const uint8_t *)m_pTexture->pixels + (size_t)(y + j) * m_pTexture->pitch;
+      for (int i = 0; i < w; i ++) {
+        if (row[(size_t)(x + i) * 4 + 3] != 255) { entry->part.hasAlpha = 1; break; }
       }
-
-      ENTRY item;
-      item.key = strdup(name);
-      item.data = spritePart;
-      ENTRY *ret = hsearch(item, ENTER);
-      assert(ret != NULL);
     }
-
-  fclose(fp);
-  return true;
+    unsigned bucket = Bucket(name);
+    entry->next = m_parts[bucket];
+    m_parts[bucket] = entry;
+  }
+  if (status < 0) ok = false;
+  if (fclose(fp) != 0) ok = false;
+  return ok;
 }
```

## 恢复、清理与停点

本地entry保存root13d30a9/bird79e4ea3完整HEAD、两源与21原文件SHA、既有Video.h差异/21mode、8正式资产；完整patch/正文diff与archive-validation可从nested旧Git正反重建。旧行为从bird79e4ea3取Sprite两源，原高度300按entry既有patch保留；不从HEAD一致推定整个nested工作树干净。`make-fixtures.py`再生小PNG/描述，`run-host.py before/final`保存实际命令/编译日志/退出，alloc-track仅本地；`prepare-runtime.py`标准update，`standard-path/run-standard.local nanos`标准run，`prepare-guest.py`直接用最终suite/fixtures生成诊断盘、`run-guest.py`执行；`refresh-guest.py`仅本轮printf诊断迭代，不是日常必经步骤。`prepare-bird.py/run-bird.py`恢复额外真实消费者。没有新下载/安装步骤；外部资源沿已有路径/原SHA与entry配方，不备份正式盘。

255身份/12归档/80preclean通过，所有验证/构建session结束后清理9463路径530286715逻辑字节、零tracked删除。cleanup-plan/receipt逐路径哈希解释旧源/对象/库/ELF/盘/截图/生成小PNG/pycache预期缺失；保留源身份/日志/结果/最小suite/生成配方/完整patch和目视文字，不能直接打开已删截图，须再生。正式8资产、nested原Video/mode/ONS/libc差异均保持。本地local/.agent和忽略正式资产不由commit备份。

F0111 Completed，90已修/29未修完（含5CQ及F0040 Partial），前89均已确认提交；本项结果确认/根文档及bird nested源码commit Pending。Working tree contains uncommitted CRP documentation and nested source changes。root13d30a9/bird79e4ea3/ONS6326adf/libc8101fad及所有index保持，未push/安装，无本组运行中动作，M2不变。唯一后续入口TASK_QUEUE#crp-next，未来F0112 Next/Planned未Start，须本组确认/精确分仓提交及另有执行授权。新组不自动commit或串行下一组。

建议开启新对话：已累积前批提交、nested资源所有权修复及host/实际guest/两类真实消费者证据，下一组转PAL RIX读取链；当前唯一入口与恢复材料完整，不新增审批或启动Prompt。

最终终检补充：484项PASS、120份保留manifest，16条原始diff空白逐条核对仅证据字节；根3份已跟踪文档/新报告与ignore、bird两源实际修复及历史差异、计数与唯一入口相符，无残余二进制/截图。复用本次Completion，本项结果确认/根及bird提交Pending，F0112未Start。


<a id="submit-20261020"></a>
## 用户确认与分仓提交（2026-10-20）

用户“提交，给我一条能自己运行bird进行测试的终端语句”确认本项已报告范围并授权分仓提交，未授权push或F0112。实际bird `80f9918b032b83ef1f0e81b0356e7cb2a2dddf6c`，两源111增61删，暂存mode100644/每文件blob及补丁精确等于验收；提交后nested index空，21原mode和Video.h高度300保留，去mode后仅Video.h原内容差异。120保留manifest/8资产/2源与完整patch无漂移，复用原484终检/技术验收/清理，不重跑产品或重复Completion。根文档提交包含本附记，实际根hash及提交后状态保存在`local/submit-receipt.json`与.agent回执；根文档状态不代替上述nested源码身份。90已修均获确认，29未修完；ignored证据/.agent仍本地保管，不由commit备份。

自行运行沿既有流程，在nanos-lite目录执行`make ARCH=riscv64-nemu update`后`make ARCH=riscv64-nemu run`；窗口按F2进入NTerm，输入`bird`回车（PATH=/bin、实际资源/share/games/bird）。不必改proc.c或生成新的诊断盘。此为当前标准入口与消费者代码核对；本次提交没有新增GUI动态验收。

建议开启新对话：当前跨仓与多类证据已完整落档，下一单元转PAL RIX，唯一TASK_QUEUE入口可恢复；本轮提交后停止，不增加审批或启动Prompt。
