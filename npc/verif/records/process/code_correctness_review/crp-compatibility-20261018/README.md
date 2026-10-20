# CRP — 原入口影响核对与兼容修复（2026-10-18）

## 授权、整体计划及边界

用户最新指令：“先确定这些错误是否影响原有入口和测试函数，如果不影响就修复”。该指令在[冻结guard](../repair-status/README.md#manual-start-guard)之上明确授权本轮定向评估及保持原有受支持入口/正常测试用法的修复，不代表五CQ契约已裁决，也不据旧连续授权自动commit/push。前批root f9adcc7、nested6dc302a，初始root/index干净。复用[CRP总计划](../REPAIR_AND_REGRESSION.md)、[现行流程](../workflow/README.md)及TASK_QUEUE唯一入口；不推进M2。

本轮为一个条件修复工作单元：阶段内先核对调用/配置/最终链接闭包，再对可独立保持兼容的部分做原反例→最小修复→真实定向/消费者验证，最后统一逐项留档。涉及原有语义或新增运行时能力的部分只留下具体影响，不以未调用推断任意新实现安全。

评估范围：F0040、F0029/F0030/F0031/F0054/F0055及上轮NEMU-on-AM音频边界；并核对下一候选F0043/F0044。入口为AM Make image/run、am-tests原测试函数、RT update/run、nanos/navy现有应用及NEMU配置文件。交付源码最小改动、逐项影响矩阵、修复前后与真实guest证据、records索引及本地状态。

当前已确定的可实施边界：

- F0040：只纠正ABI签名、guard完成字节及DSO对象，验证当前非并发初始化；并发/异常/析构不新增，完整问题仍保留未闭合状态。源码/符号确认既有消费端不链接到klib的这些实现，再构建确认；不把单线程成功宣称线程安全。
- F0044：在原AUDIO_PLAY入口内按既有缓冲容量分片，单次合法容量内请求保持同一数据/顺序/提交方式；原AM audio_test的4096分片/配置/状态接口不变。反向Area或非空零容量显式拒绝，零长度不访问设备；与F0043异步计数竞争分开验收。
- NEMU音频三处读WR：核对Kconfig、filelist及AM目标语义，只更正问题归因；不删除MUXDEF分支。最初删除候选已按用户追问撤回，最终该文件与HEAD字节相同。

暂不实施：F0029会影响nanos及vm测试对RW映射可执行的依赖；F0030调用的nanos free_page会panic且页表共享所有权待定；F0054与共享heap.start/new_page所有权耦合；F0031补dummy能力会改变初始化false契约；F0055修改has_rtc改变公开查询语义。F0043若要在读和写之间允许SDL消费，不能只给绝对值写加锁，需要明确协调提交协议，当前不改旧MMIO含义。

验收：保留F0040真实重复初始化见证，修复RV64编译器实际guard调用及DSO OBJECT、保留高guard字节，旧atexit仍失败；F0044容量−1/容量/容量+1、多次wrap、零长、非法Area及数据/提交顺序、原AM audio_test实际函数运行；GCC/Clang sanitizer及真实NEMU guest。对cpp修复按最终链接闭包判断CPU/RT/nanos运行是否受影响；隔离NEMU已实际重新构建，最终音频helper恢复原源；回归nanos三前台/hello，不能用host替代。F0043并发未闭合必须单列，真实音频观察不等于竞态已修。结束核对源码/产物/证据及状态后停止，本轮不自动提交。

## 逐项影响与处置结果

本条件单元 Completed，修复/记录尚未commit，结果确认Pending；不自动恢复上轮已结束的连续提交授权。生产最终仅两文件变化，原Make目标/选项、原AM audio_test及PCM文件均未修改。累计全部已修21（20已提交、F0044本轮未提交），未修完98（含5CQ及F0040部分修复）。

| 项目 | 对现有入口/测试的核对 | 本轮处置 |
|---|---|---|
| F0040 | AM klib消费者RT/nanos与37 CPU ELF不保留这些辅助符号；Navy部分ELF有同名符号，但来自Navy自己的libc，链接不含AM klib | 修正acquire/release签名、完成首字节及DSO对象，atexit签名正确但继续原assert失败。串行初始化修复、并发未实现；整项仍Partial，不计入全部已修 |
| F0044 | 原audio_test按4096分片调用，设备容量65536；合法容量内单次请求仍一次按原顺序提交，接口不变 | 在原入口内按容量分片；容量+1由永久等待变为可完成。零长不操作，反向Area/非空零容量assert；完整修复本项容量等待及长度窄化问题，与F0043独立 |
| F0043 | 旧AM读count后写count+len，SDL异步消费可在两者间发生；只给最终绝对赋值加锁仍会覆盖消费进度 | 不改旧MMIO提交含义，本项未修。需协同提交协议/原客户端兼容策略后再实施，不把本次真实音频成功当作竞态已修 |
| F0029 | nanos loader给代码页映射READ|WRITE后执行；AM vm测试也把RW页作为代码；内核map使用prot=0。当前公开MMAP还未有EXEC位 | 直接严格转换权限或将0视为无效会改变原入口语义；保留CQ，需同时明确执行权限及迁移调用者 |
| F0030 | unprotect为空；nanos传入的free_page会直接panic，且用户页表复制/共享内核页表 | 不能只补递归free；须先确定页表所有权/可用回收器，保留CQ |
| F0054 | klib malloc与nanos new_page共用heap.start，既有demo实际调用free | 新回收器需分清页分配/普通块所有权和复用契约，不能凭free为空推定任意补法兼容；保留CQ |
| F0031 | NPC选dummy，初始化false，VME/MPE后续能力没有成功初始化保证 | 补实际能力会改变原失败契约，属于能力实现范围，保留CQ |
| F0055 | 两平台TIMER_CONFIG声明has_rtc；原rtc_test直接读固定RTC字段，完整动态历法未实现 | 改能力声明/提供新墙钟均为公开语义变化；保留CQ，不从当前shell通过推定日历支持 |
| 上轮NEMU-on-AM边界 | TARGET_AM表示把NEMU构建为AM应用，而非一般“运行AM guest”。当前Kconfig在!TARGET_AM内才提供HAS_AUDIO，filelist按HAS_AUDIO选audio.c | 先前把3处read-WR直接记作实际配置兼容性风险不准确；本轮撤回删除分支候选。最终nemu/src/device/audio.c与HEAD一致，此项从人工启动阻塞移除；不声称已实现AM目标音频 |

## F0040局部修正与边界

原cpp.c acquire/release为空、DSO为函数。GCC/Clang host原版实际输出first=0/second=0/count=0，不能完成一次初始化契约；旧报告已有真实RV64 first=1/second=2/count=2见证。本轮真实RV64默认C++17 flags（仍未禁用threadsafe-statics）修复后first=1/second=1/count=1，直接guard调用保留其余7字节，DSO为8字节OBJECT且指向自身；atexit真实探针继续assert/BAD TRAP，未增加析构能力。

**本轮只修现有非并发行为与签名，不提供跨构造函数的线程同步，也没有新增异常/guard-abort/析构运行时。F0040完整线程安全要求尚未闭合，保留在98项未修完内。** 此前用户“只分析”延期由本轮“若不影响原入口就修复”在这些明确子范围内更新；不是默示批准单线程作为完整C++标准实现。

65 ELF闭包核对：2个本轮重新链接的RT/nanos、37个历史源码/构建契约未变CPU ELF、26个Navy ELF。39个AM klib消费者不保留修改符号；6个Navy ELF的同名符号由navy-apps/libs/libc/src/platform/cpp.cpp及其atexit实现提供，未改且不链接AM klib。因此RT仅重新image确认、未重跑msh，CPU全集不重跑；Navy未改，不重打包fsimg。明确区分新构建与历史ELF观察，不冒充65个全新构建。

## F0044定向与真实原测试验收

GCC/Clang各10例，共20例：原版仅8项通过；修复20/20，ASan/UBSan通过（LSan沿既知沙箱限制关闭）。覆盖0/1/容量−1/容量/容量+1、多容量请求及重复wrap、反向Area、零容量；host独立核对每字节顺序/环回地址及每次提交不超过容量。size_t/uintptr_t消除32位长度窄化，超过4GiB的真实缓冲未运行。

真实riscv64-nemu+SDL dummy：

- 原版65537B请求在容量65536时到PRE后3秒仍不完成，自有组结束；保存约6500万guest指令的等待见证。终止后host exit0不是guest正常返回，raw中没有GOOD/BAD TRAP或完成标志。
- 修复65537B请求约4.63秒GOOD TRAP/exit0；真实SDL回调33次、线程与guest执行线程不同，观察到65537B完整连续payload，捕获总流67584B。
- **原audio_test()函数及原little-star.pcm逐字节未改**，约4.02秒GOOD TRAP/exit0；真实SDL回调28次，56844B原PCM完整连续出现在57344B流中。没有用mock回调替换设备消费，也未修改回调输出；宿主观察库只包住实际callback并保存输出。
- nanos真实八状态（pal、nterm/命令、slides0/1/0、pal返回/输入）通过，后台hello1470→6781严格递增，回页帧一致；51.73秒自有组SIGTERM/make=-15，不是guest退出。

不声称F0043并发正确、真实声音/硬件、欠载填充全部正确、所有ISA或完整C++通过。既有NEMU音频回调未修改；真实录音字节仅证明本次原函数/超容量调用完成及样本传递。

## 用户追问后的配置纠正与测试夹具修正

用户追问删除MUXDEF的依据及CONFIG_TARGET_AM场景后，已核对nemu/Kconfig的“Application on Abstract-Machine”、Makefile引入AM构建、main的am_init_monitor与嵌入bin_start/bin_end镜像加载，及VGA转接AM示例。**原理由只看read/WR文本，不足以支持删除整个平台分支；候选3处已全部撤回**。TARGET_AM音频不在当前Kconfig可选范围，不能称为现有原入口回归。恢复候选前后native NEMU二进制SHA完全相同，说明这些删除对本次native编译没有作用；最终源码恢复原字节，不把无收益清理算作修复。

保留的夹具问题：host首次链接漏halt（补宿主stub，并重命名atexit避免替换宿主退出运行时）；隔离NEMU首次缺fixdep（复用本地现有工具，未安装）；切换before/after时copy2保留旧mtime使after复用旧AM archive，真实超容量例35秒未完成正确失败，原audio_test正常结果属于旧archive，未计修复后验收。随后明确更新时间戳强制重编，反汇编绑定修复实现，再重跑两受影响例通过。原始目录带initial-stale-archive保留，未覆盖。原版等待采集器误要求SIGTERM后必须-15，host实际0；保留初始false并按明确的自有超时/PRE/无终态补判，不把exit0单独当PASS。

## 收尾与恢复

最终28项源码/结果/符号/消费者/数据及状态核对通过；6种正常guest判据故障均拒绝（缺完成、缺trap、BAD TRAP、DIFF ABORT、SIM_END、工具失败）。实际native NEMU SHA256：911476b02b5f686ea007dec5dac3a0fc23fa05d1b9d3acd87e7cc7c24f8c2ae5，根旧build未改；REF和SoC模型未改。

local保留before源、host前后/夹具、guest源码及5镜像/原反例、SDL观察源码/原始流/回调线程日志、配置/入口影响证据、65 ELF闭包及Navy符号来源、NEMU build及恢复候选身份、真实RT/nanos image及nanos交互、失败与补验、verify/validation/patch/artifacts/manifest。隔离副本沿用/tmp/crp-ioe-t400f090；旧组三份manifest与原P5证据不改写。一次性测试与生成证据不入库，ignored资产不随commit备份。

本单元到此停止，等待用户确认/提交；没有新commit/push/安装/M2推进。后续唯一入口在TASK_QUEUE，F0043协议与F0040并发边界及五CQ仍需具体裁决，不要求为已纠正的不可达AM音频分支再作豁免。

<a id="wr-submit-20261018"></a>
## WR语义确认及本批提交授权（2026-10-18）

用户最新“确认WR属性是允许读写还是只允许写，然后提交并进入下一批修改”确认已报告本批范围并授权提交及开启下一单元。AM amdev.h的WR表示写接口（ioe_write/io_write），不是RW或允许读回；AM_AUDIO_CTRL写入freq/channels/samples配置设备，CONFIG/STATUS为查询入口。依据[官方PA输入输出/声卡](https://nju-projectn.github.io/ics-pa-gitbook/ics2024/2.5.html#声卡)及本地amdev.h、原audio_test用法。该属性限定AM抽象操作，不直接决定底层硬件/MMIO寄存器能否读取。

本地native/ioe.c和上游native实现确实把read/write分派到同一handler，AM_DEVREG也丢弃perm；这是未执行方向校验，不能当作WR支持读回的契约。WR handler通常消费输入参数，io_read传入的未初始化结构不提供可靠读回。NEMU设备中的TARGET_AM分支仍按此前配置可达性结论保持原源码，未因WR核对再次删除。

本轮复用28项验收，提交前199份local manifest/生产源码与patch核对无漂移，不无故重跑原guest。F0044已修，F0040仍Partial；仅归属明确的两份生产源码及本批报告/索引/状态/必要历史更正入库，一次性证据本地保存；实际提交回执补记本地状态，未push。

## 实际提交回执（2026-10-18）

WR核对完成后按用户指令实际提交1603f888371578d987925aa296bb26c801a2d163（8文件136增28删），提交后root/index干净，199份既有证据/生产patch无漂移；不重复测试或Completion，未push。随后按同条明确指令开始独立F0010/F0011；F0040仍Partial。local/submit-20261018保存实际回执。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0040（部分）/F0044 — 根仓库

仅展示确实落地的两文件修复；撤回的 F0043 尝试没有进入本 diff。

- 差异路径相对于仓库 `.`；旧版本：`f9adcc7bddd1e3db00273cfeb73a74c1ea6c3b3b`；新版本：`1603f888371578d987925aa296bb26c801a2d163`。

#### `abstract-machine/am/src/platform/nemu/ioe/audio.c`

F0044：用 uintptr_t 起止求 remaining，反向区间断言；零长度返回，非空且 bufsize=0 断言。外层每次取 `min(remaining, bufsize)`，等待该片可写后逐字节写环形区，发布 count，再推进源指针/remaining。原请求大于总容量时会永远等待足够空间，新版可分片提交；保留既有 count 读改写协议，F0043 异步竞争没有因此修复。

```diff
diff --git a/abstract-machine/am/src/platform/nemu/ioe/audio.c b/abstract-machine/am/src/platform/nemu/ioe/audio.c
index 41f25f69577335bf2aca5728ac42565ad8d6f641..597d3e3555a5ea91af35573245bcb3dd543baffb 100755
--- a/abstract-machine/am/src/platform/nemu/ioe/audio.c
+++ b/abstract-machine/am/src/platform/nemu/ioe/audio.c
@@ -1,5 +1,6 @@
 #include <am.h>
 #include <nemu.h>
+#include <klib.h>
 
 #define AUDIO_FREQ_ADDR      (AUDIO_ADDR + 0x00)
 #define AUDIO_CHANNELS_ADDR  (AUDIO_ADDR + 0x04)
@@ -32,20 +33,25 @@ void __am_audio_status(AM_AUDIO_STATUS_T *stat) {
 }
 
 void __am_audio_play(AM_AUDIO_PLAY_T *ctl) {
-  uint32_t len = ctl->buf.end-ctl->buf.start;
-  char *play_buf = (char *)ctl->buf.start;
-  // wait until enough buf len for write
-  //printf("2\n");
-  while(bufsize - inl(AUDIO_COUNT_ADDR) < len);
-  // write audio to buf
-  //printf("3\n");
-  for (uint32_t i=0;i<len;i++) {
-    if (wr_index >= bufsize) {wr_index = wr_index - bufsize;}
-    outb(AUDIO_SBUF_ADDR+wr_index,play_buf[i]);
-    wr_index ++;
+  uintptr_t start = (uintptr_t)ctl->buf.start;
+  uintptr_t end = (uintptr_t)ctl->buf.end;
+  assert(end >= start);
+  size_t remaining = end - start;
+  if (remaining == 0) return;
+  assert(bufsize != 0);
+  const uint8_t *play_buf = ctl->buf.start;
+  while (remaining != 0) {
+    uint32_t len = remaining < bufsize ? remaining : bufsize;
+    while (bufsize - inl(AUDIO_COUNT_ADDR) < len);
+    for (uint32_t i = 0; i < len; i++) {
+      if (wr_index >= bufsize) wr_index -= bufsize;
+      outb(AUDIO_SBUF_ADDR + wr_index, play_buf[i]);
+      wr_index++;
+    }
+    // Preserve the existing count interface; its asynchronous update race is
+    // tracked separately as F0043.
+    outl(AUDIO_COUNT_ADDR, inl(AUDIO_COUNT_ADDR) + len);
+    play_buf += len;
+    remaining -= len;
   }
-  //printf("4\n");
-  // update count
-  outl(AUDIO_COUNT_ADDR,inl(AUDIO_COUNT_ADDR)+len);
-
 }
```

#### `abstract-machine/klib/src/cpp.c`

F0040 已实施部分：把函数形式的 `__dso_handle` 改为有存储的自引用对象；`__cxa_guard_acquire(uint64_t*)` 返回完成字节是否为零，release 写 1，实现串行静态初始化一次。`__cxa_atexit` 补齐参数/返回类型但仍 assert(0)，不声称支持析构注册。并发初始化同步与 guard abort 未补齐，F0040 仍 Partial，不能把这份 diff 当成全部修复。

```diff
diff --git a/abstract-machine/klib/src/cpp.c b/abstract-machine/klib/src/cpp.c
index 9c57751862f54accd8d0cc9ed0b5b4189251e748..db624d53fdbeefd86f130cf8a4b0a258f7cf4ace 100755
--- a/abstract-machine/klib/src/cpp.c
+++ b/abstract-machine/klib/src/cpp.c
@@ -3,17 +3,21 @@
 
 #ifndef __ISA_NATIVE__
 
-void __dso_handle() {
-}
+void *__dso_handle = &__dso_handle;
 
-void __cxa_guard_acquire() {
+// Completion-byte protocol for non-concurrent initialization. Synchronization
+// across concurrent constructors is not supplied by this minimal runtime.
+int __cxa_guard_acquire(uint64_t *guard) {
+  return *(unsigned char *)guard == 0;
 }
 
-void __cxa_guard_release() {
+void __cxa_guard_release(uint64_t *guard) {
+  *(unsigned char *)guard = 1;
 }
 
-void __cxa_atexit() {
+int __cxa_atexit(void (*destructor)(void *), void *arg, void *dso) {
   assert(0);
+  return -1;
 }
 
 #endif
```
