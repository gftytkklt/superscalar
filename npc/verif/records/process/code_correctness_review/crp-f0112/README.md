# CRP F0112 — PAL RIX/MKF 有界读取与文件所有权

2026-10-20。用户“继续”授权 TASK_QUEUE#crp-next 一个单元；前批 F0111 已确认提交 root 7e68b85 / bird 80f9918。本组不授权 commit/push，不推进 M2。

## 计划、范围与验收

复用 CCR/CRP 整体计划及 workflow。本组只处理 nested PAL `src/sound/adplug/rix.cpp`、`rix.h` 中单文件及 MKF 的文件大小、offset/index/length、16384 字节容量、完整读取、失败状态和 FILE 独占/释放；不改 OPL 合成、循环音质、音频调度或性能策略，不改 Make 接口。

1. 恢复与原版见证：保存 root/nested HEAD、全部既有 nested 内容/mode、正式资产 SHA；复核实际 mus.mkf 和调用者，执行原16385/坏offset/短文件/析构见证。
2. 最小修复与定向：合法16383/16384，拒绝16385/坏signature/短header/反序越界表、模拟短读/seek失败，重复load/失败后销毁、两个实例独立；host 普通及 sanitizer、实际RV64运行，实际音乐轨道与旧版 OPL 寄存器轨迹比较。
3. 真实消费者与收尾：在隔离副本走 nanos 标准 update→run，三前台/hello及实际PAL；核对最终源码/对象/链接/安装/盘身份，完整diff正反重建、目视记录及产物清理，更新records/状态/唯一下一入口后停止，等待确认/提交。

本组无需安装。新契约取舍按 WORKFLOW_POLICY 停点；日常实现/验证组织直接执行。基线 nested HEAD `32e0a2f`，已有 main.c 跳过开场差异、AUTHORS/README 删除及广泛 mode 差异与原P8一致，原样保留，目标两源与审阅 SHA 一致。入口记录 `local/entry.json`。

实际 mus.mkf 为331284字节，89个offset（88槽），空槽0/29合法，最大非空10108字节。RIX_Init 先load，后由void rewind选择曲目；update false已有停止/重试分支。因此空槽与坏选择应安全停止，合法容器仍可选择后续曲目；不能把空首槽当作整容器无效。具体列表及SHA见local/resource-baseline.json。

参考：[ICS-PA输入输出](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)（2026-10-20读取），仅作为声卡/设备分层背景；不以教学音频范围豁免本问题的文件读取边界。OPL算法依原审阅S01/S02排除，恶意RIX内部命令/乐器索引的完整语义校验不在本项文件读取修复范围。

## 执行结果

F0112 Completed；结果确认及 root 文档 / PAL nested 源码提交 Pending。只改两源90增44删，`rix.cpp` 81增44删、`rix.h` 9增。无运行中构建/guest，无commit/push/安装，M2保持。原FINAL_FINDINGS与P8/P10快照保留历史“未修”文字，现行修复状态由repair-status及本报告维护。

### 实现及失败返回

- 构造器确定初始化fp/subsongs/file_size/length/播放状态，析构器只在fp非NULL时close。load先关闭旧fp并清状态；NULL、打开/seek/tell/读失败均false，统一fail路径close并置NULL，失败后update为false。private拷贝构造/赋值阻止FILE所有权复制；普通播放器仍由RIX_Init在堆上创建。
- 单RIX先用long取得真实文件extent，要求14≤size≤sizeof(rix_buf)。14来自data_initial读取到0x0D的既有头部；checked完整字节读取后才发布length，尾部清零并检查aa55。短名称先检查name_length≥4，避免原filename-4越界；现有大小写无关.mkf识别不变。
- MKF先完整读uint32 table，要求至少两个offset、4字节对齐、表在真实文件内，首资源位置可完整读取原有签名。subsongs=table/4-1，排除末端sentinel。选曲先清length/播放状态，范围合法后才计算long表位置，逐项检查两个offset短读、index≥表尾、index2≥index、index2≤file_size、差≤16384，再seek/read。非空槽需14字节头与签名，完整读取后才发布length；空槽合法但保持停止。
- rewind/rewindReInit公共void接口不变，内部bool helper将加载失败传回load；之后选曲失败则update false，已有RIX_FillBuffer停止/有限重试路径消费此返回。选曲失败保留独占fp供后续合法选曲，load失败/替换则释放；尾部旧字节不被播放。合法reinit=false恢复music_on，保持循环路径；新增timed曲目专门覆盖再次循环。
- 本项不校验RIX内部所有音乐命令/乐器/合成索引，不宣称任意恶意RIX语义安全；原OPL计算/音质算法保持。

### 原版见证与最终定向

`python3 local/make-fixtures.py`生成边界文件；`python3 local/run-host.py before`从nested旧版本取两源，普通与ASan+UBSan分别运行：16385文件原返回true；额外raw-overflow见证覆写virtual rewind以在OPL初始化前观察邻接字段，末字节107确实落入f_buffer（旧accepted1/length16385/neighbor107，新accepted0/length0/neighbor0，local/raw-overflow-results.json）。主suite的neighbor87是OPL初始化之后的值，不将该值当作原始越界字节；反序index得到4294967288；坏签名之后析构普通glibc double-free abort，ASan明确double-free。溢出位于同一C++对象内部，ASan未拦截这个写，不能把它写成ASan溢出报告；after写越界由容量拒绝消除。原始日志保留。

最终`python3 local/run-host.py final`普通和ASan+UBSan各562检查、0失败，136成功fopen/136 fclose配平；实际RV64同样562/0及136/136，main返回0、host exit0、GOOD TRAP，6种退出码/缺PASS/计数/错误main/重复PASS/BAD标记判据故障均拒绝。包含单RIX及MKF16383/16384/16385、短header/表/签名、反序/越界/高位/表内offset、负及sentinel选曲、空槽0/29、短名称/NULL/缺文件、单RIX短读、MKF表/签名/index/payload逐次短读、逐次seek失败及tell失败、失败后重新加载/选择、30次成功失败往返与两个独立实例；private copy/assignment额外编译负例已实际拒绝。开关只用于夹具I/O故障注入，真实消费者不带包装。

实际mus.mkf的86个非空音乐槽均以原decoder运行至100tick或首次结束；真实命令驱动Copl寄存器记录，两host构建及实际RV64一致。单独golden在每个非空槽前重置记录器，旧/新均86槽、31136 writes、86次init、聚合hash4218567204；不把空槽原无效update当作合法合成基线，也不据此宣称真实PCM/听感等价。suite全程轨迹hash545576888另行核对。

夹具迭代如实保留：初次RV64测试在main栈上放两个约17KiB播放器，栈帧35584字节超过既有32KiB用户栈，触发EVENT_ERROR/BAD TRAP（guest-*-initial）。只把测试播放器改为与RIX_Init一致的堆分配，host/实际guest重跑通过，未改生产或扩大OS栈。host sanitizer的FORTIFY将部分fread改为__fread_chk，最初两构建注入覆盖不同；夹具补__fread_chk转发后两构建相同，最终均严格断言每次注入生效。单RIX短读补例后最终562；较早519/555日志不是最终验收。copy编译负例首尝试被只读ccache拒绝，CCACHE_DISABLE=1重试得到正确private访问拒绝，无安装/系统改动。

### 标准消费者及同版身份

隔离复制现有源码/资源，绝对workspace链接remap入隔离副本，没有下载/安装。标准nanos目录执行`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= update`，exit0、25.681秒；继而同目录标准`make ... run`54.049秒。PAL初始标题→F2 NTerm及qzx失败后新prompt→F3 slide0/1/0→F1 PAL/Return继续渲染，hello首帧39→末168。八帧contact已实际目视；两帧NTerm各69797像素排除blink cursor后与旧字体模型完全一致，slide返回0与初始0 hash相同。PAL标题持续变亮，不宣称已经进入菜单或完整游戏；自有组SIGTERM结束、make=-15不是guest正常退出。

`identity-validation.json` 1644项PASS：7640原始输入无漂移；26源/684产物身份；3薄库667唯一成员/677引用逐字节；PAL的rix.o及header依赖、CrixPlayer/CPlayer和fread/seek/tell/close符号、真实PAL与四其他应用链接=安装=108标准盘extent；诊断两源逐字节等于生产、测试suite精确、39诊断payload及执行盘身份；8正式资产、PAL旧main/删除/mode及root/nested HEAD/index保持。诊断仅额外app/payload和初始app/SYS_exit oracle，不替换NEMU设备或真实文件系统。标准盘不含诊断app。

CPU/RT/REF没有PAL加载器依赖，按影响不重跑；NPC/其他ISA/native/NWM/实体显示听音/长时与完整游戏流程NotRun，F0043 count竞态/F0118后端开启失败及性能策略保持独立。LSan按已知sandbox限制关闭；136次FILE配平是本suite覆盖内所有权证据，非任意OOM/线程/通用泄漏证明。

## 完整修复diff与版本

仓库`navy-apps/apps/pal/repo`，相对路径见diff；旧完整commit `32e0a2f5c47aff04270cdb7ef5e5e5c150ce6234`，目标两源旧SHA与原审阅一致。新版本为2026-10-20未提交工作树，Git mode保持100644，实际755旧权限差异保留，不纳入本项功能修复。

| 路径 | 旧SHA256 | 新工作树SHA256 |
|---|---|---|
| `src/sound/adplug/rix.cpp` | `ffcdc95f825ee13d745e5c66704381bb75e9157633a7f2e4123198ea170c25ff` | `59c33ae7fbcde1b785dd4bcfacbbaf5626e9bbb0ce64f4eb9af2d153e64176e4` |
| `src/sound/adplug/rix.h` | `87681a32a5c609a2496da19d0cf6826ff1399e6b4d4cc3275b4b0ae71ce4f168` | `7806b4493a7d2d15d3f1947d12daa069f29de60a742891ecb1d49257661f788f` |

以下从上述旧Git版本生成完整unified diff；`archive.py`正向/反向应用及两源逐字节/Git mode共12项PASS，恢复旧源无需永久保留生产快照。

```diff
diff --git a/src/sound/adplug/rix.cpp b/src/sound/adplug/rix.cpp
index 472e338524386ff58b1f1203d680d2a615de7122..8a23fdcdab1b763a9ecfde3c8b0f3fc03439a2a6 100644
--- a/src/sound/adplug/rix.cpp
+++ b/src/sound/adplug/rix.cpp
@@ -65,52 +65,72 @@ CPlayer *CrixPlayer::factory(Copl *newopl)
 }
 
 CrixPlayer::CrixPlayer(Copl *newopl)
-  : CPlayer(newopl), flag_mkf(0), fp(NULL)
+  : CPlayer(newopl), flag_mkf(0), fp(NULL), subsongs(0), file_size(0),
+    pos(0), length(0), music_on(0), play_end(1)
 {
 }
 
 CrixPlayer::~CrixPlayer()
 {
-  fclose(fp);
+  if (fp) fclose(fp);
 }
 
 
 bool CrixPlayer::load(const char * &filename)
 {
-  fp = fopen(filename,"rb"); if(!fp) return false;
+  if (fp) fclose(fp);
+  fp = NULL;
+  flag_mkf = subsongs = 0;
+  file_size = 0;
+  pos = length = 0;
+  music_on = 0;
+  play_end = 1;
+  if (!filename || !(fp = fopen(filename, "rb"))) return false;
+
+  size_t name_length = strlen(filename);
+  uint32_t table;
+  uint16_t signature;
+  if (fseek(fp, 0, SEEK_END) != 0 || (file_size = ftell(fp)) < 0 ||
+      fseek(fp, 0, SEEK_SET) != 0) goto fail;
 
-  if(SDL_strcasecmp(filename+strlen(filename)-4,".mkf")==0)
+  flag_mkf = name_length >= 4 &&
+    SDL_strcasecmp(filename + name_length - 4, ".mkf") == 0;
+  if (flag_mkf)
   {
-	  flag_mkf=1;
-	  fseek(fp,0,SEEK_SET);
-      int offset;
-      fread(&offset,4,1,fp);
-	  fseek(fp,RIX_SWAP32(offset),SEEK_SET);
+    if (fread(&table, sizeof(table), 1, fp) != 1) goto fail;
+    table = RIX_SWAP32(table);
+    if (table < 8 || table % 4 || (unsigned long)table > (unsigned long)file_size ||
+        (unsigned long)file_size - table < 2 ||
+        fseek(fp, table, SEEK_SET) != 0 ||
+        fread(&signature, sizeof(signature), 1, fp) != 1 ||
+        RIX_SWAP16(signature) != 0x55aa) goto fail;
+    subsongs = table / 4 - 1; // The final offset is the end sentinel.
   }
-  uint16_t signature;
-  fread(&signature,2,1,fp);
-  if(RIX_SWAP16(signature)!=0x55aa){ fclose(fp);return false; }
-    if(!flag_mkf)
-    {
-        fseek(fp,0,SEEK_END);
-        length = (uint32_t)ftell(fp);
-        fseek(fp,0,SEEK_SET);
-        fread(rix_buf,length,1,fp);
-        subsongs = 1;
-    }
-    else
-    {
-        fseek(fp,0,SEEK_SET);
-        fread(&subsongs,4,1,fp);
-        subsongs = RIX_SWAP32(subsongs);
-        subsongs/=4;
-    }
-  rewind(0);
-  return true;
+  else
+  {
+    if (file_size < 14 || (unsigned long)file_size > sizeof(rix_buf) ||
+        fread(rix_buf, 1, file_size, fp) != (size_t)file_size) goto fail;
+    length = file_size;
+    memset(rix_buf + length, 0, sizeof(rix_buf) - length);
+    if (rix_buf[0] != 0xaa || rix_buf[1] != 0x55) goto fail;
+    subsongs = 1;
+  }
+  if (rewind_subsong(0, true)) return true;
+
+fail:
+  fclose(fp);
+  fp = NULL;
+  flag_mkf = subsongs = 0;
+  file_size = 0;
+  pos = length = 0;
+  music_on = 0;
+  play_end = 1;
+  return false;
 }
 
 bool CrixPlayer::update()
 {
+	if (!length || play_end) return false;
 	int_08h_entry();
 	return !play_end;
 }
@@ -120,8 +140,38 @@ void CrixPlayer::rewind(int subsong)
 }
 void CrixPlayer::rewindReInit(int subsong, bool reinit)
 {
-	play_end = 0;
+	rewind_subsong(subsong, reinit);
+}
+
+bool CrixPlayer::rewind_subsong(int subsong, bool reinit)
+{
+	play_end = 1;
 	pos = 0;
+	music_on = 0;
+	if (!fp) return false;
+	if (flag_mkf)
+	{
+        uint32_t index, index2;
+        length = 0;
+        if (subsong < 0 || subsong >= subsongs ||
+            fseek(fp, (long)subsong * 4, SEEK_SET) != 0 ||
+            fread(&index, sizeof(index), 1, fp) != 1 ||
+            fread(&index2, sizeof(index2), 1, fp) != 1) return false;
+        index = RIX_SWAP32(index);
+        index2 = RIX_SWAP32(index2);
+        if (index < (uint32_t)(subsongs + 1) * 4 || index2 < index ||
+            (unsigned long)index2 > (unsigned long)file_size ||
+            index2 - index > sizeof(rix_buf)) return false;
+        if (index2 == index) return true; // Empty MKF slots are legal.
+        if (index2 - index < 14 || fseek(fp, index, SEEK_SET) != 0 ||
+            fread(rix_buf, 1, index2 - index, fp) != index2 - index ||
+            rix_buf[0] != 0xaa || rix_buf[1] != 0x55) return false;
+        length = index2 - index;
+        memset(rix_buf + length, 0, sizeof(rix_buf) - length);
+	}
+	if (!length) return false;
+	play_end = 0;
+	music_on = 1;
 
 	if (reinit)
 	{
@@ -149,20 +199,6 @@ void CrixPlayer::rewindReInit(int subsong, bool reinit)
 		memset(for40reg, 0x7F, sizeof(for40reg));
 	}
 
-	if (flag_mkf)
-	{
-        int index,index2;
-        fseek(fp,subsong*4,SEEK_SET);
-        fread(&index,4,1,fp);
-        fread(&index2,4,1,fp);
-        index = RIX_SWAP32(index);
-        index2 = RIX_SWAP32(index2);
-        length = index2 - index;
-        fseek(fp,index,SEEK_SET);
-        memset(rix_buf, 0, sizeof(rix_buf));
-        fread(rix_buf,length,1,fp);
-	}
-
 	if (reinit)
 	{
 		opl->init();
@@ -170,6 +206,7 @@ void CrixPlayer::rewindReInit(int subsong, bool reinit)
 		set_new_int();
 		data_initial();
 	}
+	return true;
 }
 
 /*------------------Implemention----------------------------*/
diff --git a/src/sound/adplug/rix.h b/src/sound/adplug/rix.h
index 66e784db99737ad33832c29daaa17e971fff0f68..5e2eb13fbb40a717fbc36e57f59c409d7fdcbbf8 100644
--- a/src/sound/adplug/rix.h
+++ b/src/sound/adplug/rix.h
@@ -45,6 +45,7 @@ class CrixPlayer: public CPlayer
   int flag_mkf;
   FILE *fp;
   int subsongs;
+  long file_size;
   uint8_t rix_buf[16384];  /* rix files' f_buffer */
   uint16_t f_buffer[300];//9C0h-C18h
   uint16_t a0b0_data2[11];
@@ -76,6 +77,14 @@ class CrixPlayer: public CPlayer
   int sustain;
   int play_end;
 
+  bool rewind_subsong(int subsong, bool reinit);
+
+ private:
+  CrixPlayer(const CrixPlayer &);
+  CrixPlayer &operator=(const CrixPlayer &);
+
+ protected:
+
 #define ad_08_reg() ad_bop(8,0)    /**/
   void ad_20_reg(uint16_t);              /**/
   void ad_40_reg(uint16_t);              /**/
```

## 清理、复现与停点

736项预核PASS后清理本组local的9441路径、509387561逻辑字节（0 tracked删除）；相关构建/guest均已结束。cleanup-plan/receipt保留每路径SHA/类别/字节并解释source/artifact原manifest预期缺失。正式源码、真实资源和盘保持，截图已实际观察并留文字结论后删除；旧图不能再直接打开。

恢复：local/entry与resource-baseline、repair-pal.patch、正文完整diff、archive-validation、suite/overflow-witness/make-fixtures/run-host、prepare-runtime/prepare-guest/refresh-guest/run-guest、check-identities/check-visual/preclean与日志/JSON结果均保留。旧两源从nested `32e0a2f5c47aff04270cdb7ef5e5e5c150ce6234`重建，应用patch得最终版；保留entry的原main.c、删除及mode差异，不将Git HEAD相同误作原workspace干净。inputs由make-fixtures再生；prepare-runtime标准update后run-standard.local nanos，prepare-guest直接使用最终suite生成诊断盘，再run-guest。refresh仅是本轮夹具栈/短读补例迭代配方，不是日常必经步骤。raw-overflow日志及测试源保留，其16385字节文件配方是aa55开头、末字节107、其余零；原始源/ELF/盘/截图已删，按上述版本重编译。

最终源码/消费者身份、完整diff正反、记录及清理已闭合。91已修/28未修完，前90已确认提交；本项结果确认/根与PAL精确分仓commit Pending。Working tree contains uncommitted CRP documentation and nested source changes。唯一下一入口[TASK_QUEUE#crp-next](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本轮停止；不自动commit/push/下一组/M2。本地ignored证据和.agent不由普通commit备份。


<a id="submit-20261020"></a>
## 用户确认与分仓提交（2026-10-20）

用户“提交后继续”确认F0112已报告范围，授权精确分仓提交后执行F0116一个单元。PAL实际提交 `a744ceedd5797135d045fcc2e36cfe3fda4740c0`，两源90增44删、Git mode100644与已验收完整patch逐字节一致；原main.c/两删除/全部mode差异保留，index空。提交前复用并核对763项终检、79份保留身份及23条精确diff空白；未重跑已验收产品测试。根报告及两个索引随本次根提交，实际root回执保留local/submit-root-receipt.json及.agent补充记录；旧manifest的报告哈希因本附记变化，原技术证据不改写。91已修均已确认，28未修完；未push，本地ignored证据/.agent不由commit备份。

会话建议：可在当前对话继续；本轮已恢复唯一入口，下一项REF单行修复边界与证据入口明确。此次“继续”授权F0116一个单元，完成后停等确认/提交，不恢复旧连续提交预授权，不推进M2。
