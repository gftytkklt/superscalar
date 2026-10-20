# CRP — CCR-F0034 / CCR-F0035 / CCR-F0036：klib 整数格式化修复（2026-10-18）

## 计划、授权与停点

复用[既有修复计划](../REPAIR_AND_REGRESSION.md)、[CRP规则](../workflow/README.md)与
[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。用户本轮“继续”授权执行本批；
前批F0033/F0056已确认提交5b7a045，开始时root/index干净。M2保持，不安装、不commit/push。

| 问题 | 修改范围 / 契约 | 逐项验收 |
|---|---|---|
| F0034 / Medium Confirmed | decode_fmt使用当前转换字符决定属性 | d/i/u/o/x/X及已有l修饰后跟u/X/普通字符，独立期望文本/计数，复现P5 %X/%du反例 |
| F0035 / Medium Confirmed | 已有整数转换按int/unsigned int/long/unsigned long/void*取参，无符号域求负数幅值，符号/前缀先于零填充 | INT/LONG MIN/MAX、UINT/ULONG最高位及MAX、负数/0、宽度和混合变参，host sanitizer与真实RV64；指针保留既有非零0x前缀/零为0的约定 |
| F0036 / Medium Confirmed | num2str及vformat内部数字缓冲覆盖最大位数/前缀/NUL | ULONG_MAX现有8/10/16与内部helper radix2，size0/1/2/完整sink、返回计数/哨兵及ASan/UBSan；不新增公开格式 |

执行顺序：原版反例→最小修复→同版host/RV64定向→共享真实回归→统一留档停止。
共享klib stdio被CPU-tests/RT/nanos消费，选真实CPU全集、RT update/run至msh、nanos update/run三前台+hello；
沿用既有CPU测试专用_heap_end符号/-j1配置，冻结原NEMU/REF/NPC运行器。输出sink、公共API、格式支持集合及Make流程不扩展。
原始源码/夹具/日志/镜像本地保留，仅最小生产修复/报告/索引/局部忽略拟入库。
当前无必须用户裁决项；若发现真实范围/接口/失败语义冲突，按实际依赖停下裁决。完成后等确认/commit，不执行下一批。

## 逐项修复与定向验收（Completed）

原版stdio.c SHA与P5一致：`ed347e71529fe14c396bb629b737fda5b2a411f22791311a197b463d89d46654`。
本轮逐例隔离执行原源码，共43例13通过/30失败，其中16例被sanitizer终止；
`check.local before`的退出0仅表示采集结束，各失败子命令实际退出1，不是原代码PASS。

| 问题 | 原版本次结果 / 反例 | 最小修复 / 本次独立验收 |
|---|---|---|
| F0034 | 12例1通过/11失败（2例san中止）；%X 0xab→ab、%xX→ABX、%du -7→18446744073709551609u | 保存当前conversion再推进指针，以该字符决定signed/upper；host及真实RV64均12/12 |
| F0035 | 25例10通过/15失败（10例san中止）；负数-7写越内部21字节数组、高位uint被符号扩展、零填充在符号/前缀前 | 按实际类型va_arg，负数在unsigned long域求幅值，先发符号/指针前缀再零填充；host及真实RV64均25/25 |
| F0036 | 6例2通过/4失败（4例san中止）；%lo ULONG_MAX即使size2仍越内部栈缓冲 | 数字数组按sizeof(unsigned long)*CHAR_BIT+3定容（LP64为67字节，含radix2最大位数/前缀/NUL）；host及真实RV64均6/6 |

部分反例穿过同一转换链，san中止可由相邻问题共同触发，不把分组失败数当独立根因数；三项修复后分别验收。
43例包含：带后继字符/已有l修饰、INT/LONG MIN/MAX、UINT/ULONG最高位与MAX、0、正负和宽度、
void*及混合变参、零长/截断/完整sink和包装入口。除包装检查外，每例均检查size0/1/2/5/256的独立期望字符串、
返回完整长度、NUL及目的区前后未写入字节；size0使用NULL输出。sprintf/snprintf/printf及va_list路径共用的输出核已验证，
host捕获putch文本/计数，RV64实测输出`stream:-00007/AB`及计数。

额外`extra.local`原样重现P5的`snprintf(out,100,"%d",-7)`及`snprintf(out,2,"%lo",ULONG_MAX)`，
原版均ASan退出1，修复版为`-7`/2与`1`/22，exit0。
白盒夹具只include真实stdio.c并调用私有num2str，ULONG_MAX在radix2/8/10/16的四项输出/终止/哨兵均正确，
原版也通过这四项，说明容量反例在vformat的原21字节调用端；不新增公开%b等能力。

命令（本记录目录下）：`python3 local/check.local before`、`python3 local/check.local after`、
`python3 local/extra.local`、`python3 local/run.local direct`。
host GCC13.3.0，`-std=gnu11 -O2 -Wall -Werror -fno-builtin`及ASan/UBSan、不可恢复，
使用真实AM/klib头、仅重命名stdio导出符号以免劫持宿主libc；真实生产源码参与编译。
修复后host **43/43**、RV64 **43/43 + GOOD TRAP/exit0**；逐case集合/退出/日志独立核对。
指针保留原非零`0x`前缀、零指针`0`，未套用宿主libc的实现定义文本；未扩展格式集合或修改sink。

## 共享真实回归

| 消费端 | 本轮结果 / 证据 |
|---|---|
| CPU-tests RV64 NEMU全集 | 36 PASS + wrong 1 XFAIL，37/37，exit0，28.63秒；local/cpu-compat-serial-result.json、日志及cpu-final-evidence逐例status/log/summary |
| RT四应用update | 真实生成/集成成功，exit0，1.52秒；local/rt-update-result.json及日志 |
| RT真实NPC run | 165.58秒至Hello RISC-V! / msh />，difftest ON，无比较分歧/坏trap；local/rt-run-result.json及日志，不声称四应用实际运行 |
| nanos update/run | 完整navy update exit0，23.32秒；108个ramdisk extent与当前fsimg逐字节一致；真实NEMU运行51.75秒，F2 nterm输入qzx后返回prompt，F3 slides0→1→0，F1 pal切回/输入后继续刷新 |
| 输入/显示与后台 | 原SDL队列→MMIO→guest事件/显示链；contact.png及原BMP已视觉核对；hello八观察点1257→1974→2617→3344→3860→4377→5096→5809，持续递增 |

CPU沿用前批已记录测试配置：`-j1`及仅命令层
`--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`，没有删减全集分母或改生产linker/Make。
默认mem-test缺_heap_end、并行共享AM重建问题仍独立存在，本次不重跑已知失败默认配置，不声称默认命令已通过。
RT/nanos均由监督器向自有进程组SIGTERM收停，make退出-15不是guest正常退出。
未测人工GUI、音频、长时游戏、Linux、完整NPC CPU全集或RT四应用运行；host不替代共享消费者guest。
完整命令、cwd、环境、退出、时间均在对应result.json。

## 身份、证据与完成状态

- F0034、F0035、F0036均**Completed**；结果确认Pending、commit Pending。生产唯一修改stdio.c，31增12删、mode100755保持；
  新SHA `d1e16b1b0ab885033c7a5781427e5e71b258e8936ca669380b7de417c3f80739`。decode_fmt/取参/私有num2str与缓冲/补零为改动范围，API/Make/NEMU/NPC/RTL/M2保持。
- 测试副本`/tmp/crp-stdio-11ytsbgr`；local/prepare.local复制现有源码、排除Git/build并重定位symlink/files.mk，
  复制冻结NEMU/REF/NPC且禁止自动Git钩子；CCACHE_DISABLE=1。无下载/安装/无关运行器重建。
- local/source-manifest.json、tested-identity.json、tools.json绑定原/修复源码、两平台实际对象、运行器及工具；
  root与副本源码SHA一致，原NEMU/REF/NPC二进制SHA不变。
  原/修复源码、repair.patch、before/after/extra/direct结果、CPU/RT/nanos日志/帧、ELF/BIN/ramdisk/对象副本均在local/及artifacts/。
- local/validation.json的**19项证据核对全部通过**；local/manifest.json为证据清单。
  一次性host/guest/白盒/SDL采集夹具未加入常规测试入口，按CRP规则**不提交测试代码**；只拟提交最小生产修复/报告/索引/局部.gitignore。
- root boot_linux HEAD `5b7a0454f38c3f69ddd1591bb072ee06cc9960ca`，index空；**Working tree contains uncommitted CRP repair/documentation changes**，未commit/push。
  .agent、计划和原始证据本地忽略，commit不等于备份；旧CCR最终台账/manifest/完成快照保留历史。
- 累计已修11项，剩余108项含5CQ。当前批次统一留档后停止，未来范围/门槛只见[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本轮不执行下一批或推进M2。

回滚仅反向应用local/repair.patch并核对原SHA；目标如已有后续变化先核对差异，不整文件覆盖/reset/clean或回退嵌套仓库。



<a id="f0034-f0035-f0036-submit-20261018"></a>
## 2026-10-18 用户确认与提交收尾

用户“提交”确认已报告的F0034/F0035/F0036范围并授权提交。复用既有技术验收与完成快照，
本轮核对239份本地证据、7份收尾文档、生产SHA及精确patch均无漂移；未重跑产品测试，不重复Completion。
提交范围仅stdio.c、本报告/局部.gitignore及process索引；一次性夹具/原始日志/镜像/.agent继续本地忽略。
实际commit、暂存范围及提交后状态见`local/submit-20261018/receipt.json`和.agent确认/提交回执。
前文Pending/HEAD5b7a045为本批完成时截面，不扩写CPU兼容配置、受控收停或未测能力。
提交后停止，不push、不启动F0046或推进M2；普通commit不等于忽略资产已备份。


2026-10-18 空间清理附记：用户明确授权删除工作区大型临时存档。本目录的大型归档
ramdisk或一次性完整raw测试快照已按[清理记录](../../workspace-storage-cleanup-20261018/README.md)
精确删除，原路径/尺寸/SHA见该记录local/deletion-manifest.json；原文本验收/命令/
结果与哈希保留，历史manifest缺失项须结合该授权清单解释，不视为源码漂移或验收
事实变更。旧产物字节不再本地保留，需复核时按原版本/配置重建或重新运行测试。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0034/F0035/F0036 — 根仓库

格式解析、数值转换与输出缓冲三项共用一个文件，保留原 helper 与公开入口验收区别。

- 差异路径相对于仓库 `.`；旧版本：`5b7a0454f38c3f69ddd1591bb072ee06cc9960ca`；新版本：`71c6cf84f0b58fd44df005494b06629daefae40a`。

#### `abstract-machine/klib/src/stdio.c`

F0034：保存 `conversion = *tmp++` 再判断 u/X，避免读取转换符后一个字符来判有符号和大写。F0035：取参按指针/有符号/无符号及 long 分类；负数幅值通过 `0UL - (unsigned long)val` 形成，num2str 接收 unsigned long 幅值及独立 negative，不再把负值直接当巨大无符号数打印，也不对 LONG_MIN 做有符号取负。补零时先 emit 符号或非零指针前缀，再输出 padding 与剩余数字，避免出现 00-123/000x...。F0036：数字缓冲扩大为 `sizeof(unsigned long)*CHAR_BIT+3`，容纳最坏逐位数位、符号/0x 和 NUL。保留原零指针表示和已支持格式集合，未扩展完整 printf。

```diff
diff --git a/abstract-machine/klib/src/stdio.c b/abstract-machine/klib/src/stdio.c
index 4f7d2eaa76d698eb40543663ac6fa4acab972b4e..8ad3d0c130d021639cde879edaaba0901a724fd3 100755
--- a/abstract-machine/klib/src/stdio.c
+++ b/abstract-machine/klib/src/stdio.c
@@ -2,6 +2,8 @@
 #include <klib.h>
 #include <klib-macros.h>
 #include <stdarg.h>
+#include <stdint.h>
+#include <limits.h>
 
 #if !defined(__ISA_NATIVE__) || defined(__NATIVE_USE_KLIB__)
 enum {INVALID_TYPE, STR, NUMBER, CHAR, };
@@ -40,7 +42,8 @@ static int decode_fmt(const char* fmt, formatinfo* info){
   if(*tmp == 'l') {info->islong = true; tmp++;}
   // as behavior of invalid fmt as %lp/%ls is UB, deal them with valid info is OK
   // info in struct formatinfo is invalid when meet inv fmt above
-  switch (*tmp++) {
+  char conversion = *tmp++;
+  switch (conversion) {
     case 'c':
       info->argtype = CHAR;
       break;
@@ -56,7 +59,7 @@ static int decode_fmt(const char* fmt, formatinfo* info){
     case 'd': case 'i': case 'u':
       info->argtype = NUMBER;
       info->radix = 10;
-      info->issigned = (*tmp == 'u') ? false : true;
+      info->issigned = (conversion != 'u');
       break;
     case 'o':
       info->argtype = NUMBER;
@@ -65,7 +68,7 @@ static int decode_fmt(const char* fmt, formatinfo* info){
     case 'x': case 'X':
       info->argtype = NUMBER;
       info->radix = 16;
-      info->isupperdigit = (*tmp == 'X') ? true : false;
+      info->isupperdigit = (conversion == 'X');
       break;
     default:
       info->argtype = INVALID_TYPE;// as a result, invalid fmt will be ignored
@@ -75,18 +78,18 @@ static int decode_fmt(const char* fmt, formatinfo* info){
 }
 // get str of number
 // e.g, -123456 -> "-123456"
-static void num2str(char* dst, long val, bool issigned, bool isupper, bool ispointer, int radix){
+static void num2str(char* dst, unsigned long val, bool negative, bool isupper, bool ispointer, int radix){
   assert(radix != 0);
   const char* lowerstr = "0123456789abcdef";
   const char* upperstr = "0123456789ABCDEF";
   const char* usestr = isupper ? upperstr : lowerstr;
   char *tmp = dst;
   if (val == 0){*tmp++ = '0';*tmp = '\0';return;}
-  else if(issigned && (val < 0)){*tmp++ = '-';}
+  else if(negative){*tmp++ = '-';}
   else if(ispointer){*tmp++ = '0';*tmp++ = 'x';}
   // tmp points to lsb digit, p points to wr pos
   char *p = tmp;
-  unsigned long val_abs = (unsigned long) val;
+  unsigned long val_abs = val;
   while(val_abs != 0){
     *p++ = usestr[val_abs % radix];
     val_abs /= radix;
@@ -138,14 +141,30 @@ static void vformat(emit_f emit, void *arg, const char *fmt, va_list ap) {
         break;
       }
       case NUMBER:{
-        long val_num = info.islong ? va_arg(ap, long) : (long) va_arg(ap, int);
-        char numstr[21] = {0};
+        unsigned long val_num;
+        bool negative = false;
+        if (info.ispointer) {
+          val_num = (uintptr_t)va_arg(ap, void *);
+        } else if (info.issigned) {
+          long val = info.islong ? va_arg(ap, long) : (long)va_arg(ap, int);
+          negative = val < 0;
+          val_num = negative ? 0UL - (unsigned long)val : (unsigned long)val;
+        } else {
+          val_num = info.islong ? va_arg(ap, unsigned long) : (unsigned long)va_arg(ap, unsigned int);
+        }
+        // One character per bit, a sign or pointer prefix, and the terminator.
+        char numstr[sizeof(unsigned long) * CHAR_BIT + 3];
         char padding = info.zeropad ? '0' : ' ';
-        num2str(numstr, val_num, info.issigned, info.isupperdigit, info.ispointer, info.radix);
-        for(int i=strlen(numstr);i<info.width;i++){
+        num2str(numstr, val_num, negative, info.isupperdigit, info.ispointer, info.radix);
+        int len = strlen(numstr);
+        char *p = numstr;
+        if (info.zeropad) {
+          int prefix = negative ? 1 : (info.ispointer && val_num != 0 ? 2 : 0);
+          while (prefix-- > 0) emit(arg, *p++);
+        }
+        for(int i=len;i<info.width;i++){
           emit(arg, padding);
         }
-        char *p = numstr;
         while(*p){
           emit(arg, *p++);
         }
@@ -216,4 +235,4 @@ int snprintf(char *out, size_t n, const char *fmt, ...) {
   return ret;
 }
 
-#endif
\ No newline at end of file
+#endif
```
