# CRP — CCR-F0033 / CCR-F0056：klib string 修复（2026-10-18）

## 计划、范围与停点

复用[既有修复计划](../REPAIR_AND_REGRESSION.md)、[CRP规则](../workflow/README.md)及
[TASK_QUEUE 唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。用户本轮“继续CRP修复任务”授权执行本批；
前批已确认提交0aa1dca，开始时root working tree/index干净。M2保持，不安装、不commit/push。

| 问题 | 目标 / 修改范围 | 验收 |
|---|---|---|
| CCR-F0033 / Medium Confirmed | string.c: strncpy先检查n，再读源；短串零填满n字节，保持返回dst | P5原反例；非NUL n字节源、n0/1/短串/恰边界、padding、源/目的哨兵；ASan原越读 |
| CCR-F0056 / Low Robustness | string.c: memmove去VLA，按地址方向复制，O(1)栈，保留重叠/零长/返回值 | P5原反例；n0/同址/不重叠/双向重叠/大块、哨兵；编译栈预算及真实64KiB小栈运行 |

执行顺序：原版定向反例 → 最小修复 → 同版host sanitizer/RV64 guest定向验收 → 共享真实回归 → 统一留档停止。
消费端已有nanos device.c的strncpy、AM demo ant的memmove；共享klib还进入RT及CPU-tests，选择CPU-tests全集、
RT update/run到msh及nanos update/run三前台切换+后台hello。原始默认CPU链接缺口与并行构建缺口已知，沿用前批测试配置。
不改变公共API、Make接口/用户流程、其他string函数、NEMU/NPC/RTL或堆布局。当前无真实未决裁决/安装事项；如出现则按实际依赖停下。
交付为最小生产修复、本报告/索引及本地证据；一次性夹具不入库。完成后等待结果确认/commit，不进入下一批。

## 逐项定向验收（Completed）

原始 `local/string.before.c` SHA与P5审阅身份一致：
`f475cc8c6cd0a583dc6fca5595e559beef2bd21afa4239a769dfe9bf7edfec12`。
本次实际重现P5的strncpy-bound/pad、memory/move-zero等输入，不重跑无关格式化/helper旧验收。

| 问题 | 原版本次见证 | 修复及本次结果 |
|---|---|---|
| F0033 | padding原反例为61 00 5a 5a 5a；13项copy检查有3项padding失败；非NUL的1字节源/n=1触发ASan越读；n=0/one-past源也触发ASan | 先判断i<n再访问src[i]，首NUL后补满剩余n字节；13/13通过，原padding/bound/n0反例均通过；返回dst、源/目的哨兵保持 |
| F0056 | 原两向重叠正常，GNU11无san的n0运行成功；UBSan单独报告VLA bound0；1MiB双向移动在64KiB host栈限制下SIGSEGV（-11） | 提前返回n0/同址，以uintptr_t地址顺序在本项目平坦地址空间选择前/后向逐字节复制；1092/1092 host矩阵通过，额外分离数组双向/哨兵通过；1MiB双向在64KiB host栈下通过 |

host命令：`python3 local/check.local before`、`python3 local/check.local after`；GCC13.3.0、
`-std=gnu11 -O2 -Wall -Werror -fno-builtin`，san版本加ASan/UBSan且不可恢复；
编译真实生产string.c，只重命名公开符号以免劫持宿主libc，使用真实AM/klib头。
最终host普通及san矩阵均为copies=13/moves=1092/failures=0。
`local/extra-result.json`记录P5原padding、零长不读源和分离数组的精确编译/运行命令及退出码。
1092含8×8×17个小块offset/长度组合、2个分离区间与2个1MiB大块；独立期望字节由固定原始模式产生。
源码/目的周边均检查，既有二进制调用未被宿主builtin替代。
guest的4KiB栈夹具补齐后，host按最终夹具重新核验同样结果；初次日志/产物保留`local/initial-host/`。

RV64命令：`python3 local/run.local direct`经原AM→NEMU make run入口构建执行，
**13项copy + 1093项move/stack检查、0失败，HIT GOOD TRAP，exit0**。
其中1MiB双向重叠搬运经`small-stack.S`仅对目标调用切换至对齐4KiB静态栈，返回后上下32字节哨兵完整；
额外第1093项为栈哨兵检查。这是实际RV64小栈运行，与host进程栈限制/UBSan诊断分开记录。
独立`-fstack-usage -O2`报告：原host为32字节+dynamic、原RV64为16字节+dynamic；
修复host为8字节static、RV64为0字节static，长度不再增加栈。
命令/退出/诊断/反汇编见`local/{before,after}-result.json`、`rv64-stack-result.json`、`*.su`、`rv64-*.disasm`及`direct.log`。

## 共享真实消费者回归

| 验收 | 本轮实际结果 / 证据 |
|---|---|
| CPU-tests RV64 NEMU全集 | **36 PASS + wrong 1 XFAIL，37/37，exit0，27.64秒**；`local/cpu-compat-serial-result.json`、日志及`cpu-final-evidence/`逐例status/log/summary |
| RT AM集成update | 原四应用真实生成成功，exit0，1.37秒；`local/rt-update-result.json`及日志 |
| RT真实NPC run | **158.08秒到Hello RISC-V!及msh />，difftest ON，无比较分歧/坏trap**；`local/rt-run-result.json`及日志，不声称四应用实际运行 |
| nanos真实update/run | 完整navy update exit0，21.81秒；108个ramdisk extent与当前fsimg逐字节相同；真实NEMU run 51.72秒，F2 nterm输入qzx返回prompt、F3 slides0→1→0、F1 pal切回/输入后继续刷新 |
| 真实输入与显示 | SDL队列注入按键并经过原guest MMIO/事件/显示；原BMP/contact.png已视觉核对；hello八阶段1310→2062→2741→3498→4040→4581→5334→6086，均继续执行 |

CPU沿用前批已明确的测试配置：`-j1`，并仅在测试make命令中加入
`--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`。
存量mem-test引用_heap_end而NEMU linker未导出、-j4共享AM重建竞态仍未修；本批不重跑已知失败默认配置，
不改生产linker/Make/测试源，也不声称默认命令已通过。完整命令/cwd/环境/退出在各result.json。
RT与nanos均由监督器向自有进程组SIGTERM收停，make退出-15不是guest正常退出。
未测人工GUI、音频、长时游戏、Linux、完整NPC CPU全集或RT四应用运行；这些能力不属于本批验收。
AM demo ant的具体四方向动画未单独运行，方向/大块搬运已由真实RV64定向覆盖，RT update包含demo真实构建；
不把编译或msh到达写成该动画已跑。

## 身份、持久化与完成状态

- **F0033 Completed；F0056 Completed；本批结果确认Pending、commit Pending。** 两问题分别有原反例和修复验收，不由共享回归推定。
- 生产唯一修改`abstract-machine/klib/src/string.c`，16增14删，mode100755保持。新SHA
  `3a8321ac99fc67bc50e81964d5e375c8c45a7af38895e1f600c07ee2277a2322`；其他string函数/API/Make入口保持。
- 测试副本`/tmp/crp-string-yu5nwih1`；`local/prepare.local`保存现有源码复制、排除Git/build、symlink/files.mk重定位及冻结运行器复制配方。
  只在副本构建，`CCACHE_DISABLE=1`，禁用构建Git钩子，不下载/安装/重建无关模拟器。
- 当前生产、两ISA消费端实际源码/编译对象及冻结NEMU/REF/NPC hash见`local/tested-identity.json`。
  运行器与原生产同SHA；GCC/cross13.3.0、Make4.3；完整副本初始身份见`source-manifest.json`。
- ELF/BIN/ramdisk/对象副本在`local/artifacts/`；原/修复源码、repair.patch、host/RV64/CPU/RT/nanos原始日志、帧、精确命令、退出和验证清单均在local。
  `local/validation.json`的13项一致性检查全部通过，`local/manifest.json`绑定本批证据；旧CCR审阅manifest/完成快照未改。
- 本批夹具为一次性host/guest/观察采集，未加入现有常规测试入口；按CRP规则**不提交测试代码**，保留本地复现。
  仅最小生产修复、本报告/局部.gitignore及process索引纳入拟提交范围，不改全仓跟踪规则。
- 根boot_linux HEAD `0aa1dca5a49716461a1b09bf02f14fe26faa9dc9`，index空；
  **Working tree contains uncommitted CRP repair/documentation changes**，未commit/push。
  .agent、本地原始证据及计划仍被忽略，普通commit不等于备份。
- 累计已修8项（F0015/F0052/F0051/F0085/F0037/F0038/F0033/F0056），剩余111项含5CQ。
  业务M2保持；统一留档后停止。未来批次/门槛只见[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本轮不执行。

回滚仅反向应用`local/repair.patch`并核对原SHA；如目标已有后续修改，先核对差异，不整文件覆盖/reset/clean或回退嵌套仓库。



<a id="f0033-f0056-submit-20261018"></a>
## 2026-10-18 用户确认与提交收尾

用户“提交”确认本批已报告的F0033/F0056范围并授权提交。复用已有技术验收与完成快照，
本轮核对252份本地证据、7份收尾文档、生产源码SHA及精确patch均无漂移；未重跑产品测试，不重复Completion。
提交范围仅string.c、本报告/局部.gitignore及process索引；一次性夹具、原始日志/镜像/.agent保持本地忽略。
实际commit、暂存范围及提交后状态见`local/submit-20261018/receipt.json`及.agent确认/提交回执。
前文Pending/HEAD0aa1dca为本批完成时截面，不扩写CPU测试适配、受控收停或未测能力。
提交后停止，不push，不启动下一批或推进M2；本地忽略资产仍不等于已备份。


2026-10-18 空间清理附记：用户明确授权删除工作区大型临时存档。本目录的大型归档
ramdisk或一次性完整raw测试快照已按[清理记录](../../workspace-storage-cleanup-20261018/README.md)
精确删除，原路径/尺寸/SHA见该记录local/deletion-manifest.json；原文本验收/命令/
结果与哈希保留，历史manifest缺失项须结合该授权清单解释，不视为源码漂移或验收
事实变更。旧产物字节不再本地保留，需复核时按原版本/配置重建或重新运行测试。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0033/F0056 — 根仓库

两项分别保证有界读/零填充与重叠移动的常量栈空间。

- 差异路径相对于仓库 `.`；旧版本：`0aa1dca5a49716461a1b09bf02f14fe26faa9dc9`；新版本：`5b7a0454f38c3f69ddd1591bb072ee06cc9960ca`。

#### `abstract-machine/klib/src/string.c`

F0033：strncpy 把 `i < n` 放在读 src[i] 前，n=0 不读源；遇到 NUL 后循环把剩余 n 字节全部填零，替代仅写一个终止符。F0056：memmove 删除 `char tmp[n]`，n=0/同址直接返回；目标地址低于源时前向复制，否则从末端向前复制，避免覆盖仍需读取的重叠字节。使用固定局部变量，栈占用不再随 n 增长。

```diff
diff --git a/abstract-machine/klib/src/string.c b/abstract-machine/klib/src/string.c
index 2667b0ee713239e17a2d82ec2e599e270868fe5b..e757be7f12069a0027a4dd09efe77c6e6d91ee0f 100755
--- a/abstract-machine/klib/src/string.c
+++ b/abstract-machine/klib/src/string.c
@@ -25,15 +25,15 @@ char *strcpy(char *dst, const char *src) {
 }
 
 char *strncpy(char *dst, const char *src, size_t n) {
-  //panic("Not implemented");
   size_t i = 0;
-  while((src[i] != '\0') && (i<n)){
+  while ((i < n) && (src[i] != '\0')) {
     dst[i] = src[i];
     i++;
   }
-  if(i<n){dst[i] = '\0';}
+  while (i < n) {
+    dst[i++] = '\0';
+  }
   return dst;
-  
 }
 
 char *strcat(char *dst, const char *src) {
@@ -84,16 +84,18 @@ void *memset(void *s, int c, size_t n) {
 }
 
 void *memmove(void *dst, const void *src, size_t n) {
-  //panic("Not implemented");
-  char tmp[n];
-  char *pdst = dst;
-  const char *psrc = src;
-  size_t i;
-  for(i=0;i<n;i++){
-    tmp[i]=psrc[i];
-  }
-  for(i=0;i<n;i++){
-    pdst[i]=tmp[i];
+  if (n == 0 || dst == src) return dst;
+  unsigned char *pdst = dst;
+  const unsigned char *psrc = src;
+  if ((uintptr_t)pdst < (uintptr_t)psrc) {
+    for (size_t i = 0; i < n; i++) {
+      pdst[i] = psrc[i];
+    }
+  } else {
+    while (n > 0) {
+      n--;
+      pdst[n] = psrc[n];
+    }
   }
   return dst;
 }
```
