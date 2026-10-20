# CRP — F0039 int64 修复与 F0040 C++ guard 契约核对（2026-10-18）

> **本单元Completed：F0039修复完成，用户已确认并授权提交；F0040仅分析完成、按用户决定暂缓修复。** 前批F0049已确认提交d9a3d42。

## 范围与单元计划

用户“提交后继续”确认前批并授权本单元；F0049已提交d9a3d42、初始root/index干净。复用[修复总计划](../REPAIR_AND_REGRESSION.md)、[现行CRP流程](../workflow/README.md)及[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不推进M2、不重排总计划。

本组候选F0039/F0040同属klib编译器辅助契约。先复用P5 int64-min与cpp-guard反例并核真实代码/ABI：F0039只修改int64.c有符号除余辅助函数，在无符号域形成幅值并恢复符号，保留接口及unsigned除法核心；F0040核真实C++17调用、guard首字节及DSO符号，涉及新并发/异常/析构能力或未决契约时仅留分析，不作未经批准的实现。两项独立，真实未决不阻塞F0039。

验收：F0039原版UB见证，修复后MIN/1、MIN%1、分母MIN、正负边界/独立参考向量及RV64 guest；C未定义的除0/MIN除-1单列，不当作新增功能要求。F0040用真实交叉编译/反汇编和必要受控反例证明根因及策略边界，不能以单线程字节置位宣称完整并发安全。共享klib按实际调用/链接影响选择CPU全集、RT update/run到msh、nanos三前台/hello；复用已有可靠runner与隔离环境，仅执行链变化补负例。所有命令/源码/结果及限制留local，必要最小测试才入库。

执行顺序：准入/原反例→逐项最小修改/定向验证→最终组合与受影响真实回归→逐项结论、索引/状态/唯一入口。正常组末停等确认/commit，不自动提交/push；安装或真实策略需人工裁决时停止相关部分。

<a id="f0040-analysis"></a>
## F0040 本轮分析与用户范围决定（生产未修）

本轮真实默认AM C++17 flags仍为`-ffreestanding -fno-rtti -fno-exceptions`，未使用`-fno-threadsafe-statics`。交叉编译/反汇编确认生成guard读取、acquire/release调用；原cpp.c这些函数只有ret，`__dso_handle`的ELF类型为FUNC。真实RV64 NEMU探针输出`first=1 second=2 count=2`并正常终止，证明同一局部static反复初始化；该GOOD TRAP仅说明反例采集程序正常退出，不表示F0040修复。

[Itanium C++ ABI一次初始化接口](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#once-ctor)规定acquire返回是否需要初始化，release设置完成字节；完整线程安全实现还需跨初始化期间的同步。[DSO析构接口](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#dso-dtor)定义了DSO身份及析构注册/执行关系。当前cpp.c的atexit仍为assert，不能用签名及一个guard字节宣称完整C++运行时。

简单首字节方案能修复单线程反例，但不能建立并发初始化保证。本地AM dummy MPE不提供可用atomic_xchg；NPC A扩展仍未实现，不能擅自依赖LR/SC或把跨构造函数关中断当作通用RT线程同步。新增平台锁/调度接入或改变编译选项及并发范围均超出本单元明确边界。这里是修复范围的未决，不改原Confirmed分类或新增CQ编号。

用户本轮明确选择：**“本轮只分析 F0040，待正式需求明确后裁决”**。据此F0040分析Completed、生产修复Deferred；cpp.c保持原字节，未实现单线程候选、并发、异常或析构能力。此延期只影响F0040，不阻塞独立F0039，也不要求其他CRP批次等待该裁决。证据：local/f0040-baseline.cc、cpp-before.log/result、guard-call.log、cpp-abi.log。

## F0039 修复与定向结果

仅修改int64.c三个函数：`__divdi3`/`__moddi3`的sign mask、MIN幅值和返回符号恢复全部使用du_int模运算；`__divmoddi4`的余数重建亦使用无符号乘减，避免有符号中间运算溢出。unsigned除余核心和其他helper保持字节不变；不改公开符号、平台宏或Make接口。

依据现有源文件的二补码/算术右移前提，与[LLVM除法实现](https://raw.githubusercontent.com/llvm/llvm-project/main/compiler-rt/lib/builtins/int_div_impl.inc)采用的无符号幅值思路一致；[GCC整数辅助函数接口](https://gcc.gnu.org/onlinedocs/gccint/Integer-library-routines.html)给出商/余数接口。最终unsigned→signed转换仍遵循本项目GCC/Clang二补码目标的既有约定，未增加跨任意C实现的保证。

host对helper对象重命名，防止参考表达式/UBSan运行时回调解析进被测函数；GCC与Clang各自UBSan原版MIN/1、MIN%1及divmod反例均报signed overflow。修复后两编译器分别通过2427个合法signed向量和2428个unsigned向量，另独立MIN边界检查通过；真实RV64 NEMU使用同一测试C通过相同向量，反汇编确认参考为硬件DIV/REM，被测为三个软件helper的实际调用。MIN/-1直接helper的模结果仅作为附加观察（本版返回MIN、余0），不把C语言未定义表达式设为新契约；除0不在合法C域，本次NotRun且不改变unsigned核心。

初次host夹具缺halt实现、初次RV64夹具因一行缩进触发-Werror，均在测试夹具补齐后重验；失败日志保留，未计产品PASS。host最终10个运行结果全通过（两编译器各完整向量及4个边界入口），local/host-before、host-after、direct.log/result和direct-disasm.log保存证据。

## 消费者影响与回归选择

- CPU-tests真实NEMU全集：36 PASS + wrong预期XFAIL；逐一检查37个实际执行块、终态及汇总，五个缺执行/缺终态/错误终态/额外失败/工具失败判据负例均拒绝。复用已知`_heap_end`测试兼容符号和-j1配置，不声称默认命令已修复。
- RT真实update及image构建成功，nanos完整navy update后image构建成功；首次nanos构建早于update完成，因缺ramdisk失败，保留initial-before-update日志。最终以update成功后重新构建为准，未使用中间产物。
- 对新构建RT、nanos、37个CPU镜像及Navy安装的26个ELF共65项检查，既无原名也无包含这些helper名的编译器派生/应用前缀符号。9个无符号条目均为BusyBox链接，已核对同次unstripped ELF无相关helper，且去ELF封装后的装载字节与安装文件完全一致；未以“nm无符号”当作缺函数证明。
- 这三个被改函数不在上述生产镜像保留的执行闭包，RT/Navy生成器及消费端未改；本轮因此不重复真实RT到msh、nanos三前台/hello，非因GUI或耗时免测。直接RV64 helper guest与真实CPU全集为本轮新运行；前批F0049长测试不复跑。native/其他ISA/除0/完整C++/并发新能力NotRun。

测试只在隔离副本进行。主要命令入口为local/host.local、prepare.local、run.local（direct/cpp-before/cpu/rt-update/navy-update/nanos-image）、build-consumers.local的RT image构建、cpu-verify.local与impact.local；每步依赖其前置成功，不将初次构建失败与最终成功混用。一次性C/C++/执行脚本、源码/ELF/BIN、JSON/日志均local保留不入库；必要报告/索引及最小生产补丁单独提交。


## 本单元完成结论与停点

| 项目 | 真实状态 |
|---|---|
| F0039 | 修复Completed；两个host编译器各2427 signed+2428 unsigned向量及边界入口通过；实际RV64 guest同组向量/GOOD TRAP；CPU全集36 PASS+1 XFAIL，21项最终核对通过 |
| F0040 | 分析Completed、生产未修复/Deferred；真实RV64重复初始化反例与原FUNC DSO证据已保存，用户明确选择待正式需求裁决；不计入已修数 |
| 产品边界 | 仅int64.c三个有符号helper函数体变化，unsigned核心、cpp.c、Makefile和消费端源码不变；65个新构建消费者ELF未保留修改函数，RT/nanos运行因此NotRun |
| 提交/范围 | 前批已提交d9a3d423928bfbc6e008500a0c2cbd36d4121cbb，本批修复/报告未commit，index空，未push；仅最小生产补丁/报告/索引/局部忽略可跟踪，测试/生成证据本地保存 |

最终int64.c SHA256：`ed54fd2fd4310e3f4213f86aa799f725f6e95ae09b24f68d344619b70bcef373`；本轮副本`/tmp/crp-int64-89mq_l4e`。local/validation.json、cpu-validation.json、consumer-impact.json、host-before/after、各命令日志/结果及artifacts绑定源码/ELF/archive；local/repair.patch保存补丁，manifest.json绑定本轮证据。root/REF解释器未变，原F0049和P5证据不覆盖。

累计已修16/剩余103（含5CQ）；F0040延期已获用户明确确认，本项仍保留在剩余问题中，其他独立修复不等待它。此为存量C辅助函数局部闭环，不代表所有ISA、完整C++或M2能力完成。无安装、无运行中任务。已更新记录索引/进展与.agent，本组末停止等待F0039结果确认/commit；后续仅沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动进入下一组。


<a id="submit-20261018"></a>
## 2026-10-18 确认及连续批次授权

用户“完成后提交并继续”确认本项已报告范围并授权提交，另明确允许在上下文不影响质量时连续验证/留档/提交及开启后续批次；不直接阻塞后续独立批次的未决项集中记录，最后汇总为下次任务启动前须人工决定或明确豁免的guard。该授权不把未测能力记为通过、不授权push，不改变M2等其他主线的阶段规则。

提交前114份证据及已测源码无漂移；复用21项核对、host/RV64向量和CPU验收，不重跑测试或重复完成快照。仅四份归属明确文件入库，实际hash记local/submit-20261018和.agent。F0040按用户既有选择仅分析，继续延期。

## F0040后续条件修复（2026-10-18）

原“只分析”保留为当时决定；用户后续授权先核对原入口影响、兼容部分直接修复。本轮已做ABI签名/完成字节/DSO及串行修正，[报告](../crp-compatibility-20261018/README.md)记录真实RV64与链接闭包。线程同步/异常/析构未实现，F0040仍Partial、未计全部已修，修改未提交。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0039 — 根仓库

本报告同名 F0040 当时未实施；其后已实施的串行 ABI 部分见 compatibility 报告，不合并为已完全修复。

- 差异路径相对于仓库 `.`；旧版本：`d9a3d423928bfbc6e008500a0c2cbd36d4121cbb`；新版本：`b2229ef5cfb17224b5987f087af17266192961f1`。

#### `abstract-machine/klib/src/int64.c`

F0039：符号掩码、绝对幅值与恢复符号的异或/减法改在 du_int 域执行，INT64_MIN 的幅值可以无符号表示；调用 __udivmoddi4 后再转换回 di_int。divmod 的 `a - d*b` 也在 du_int 中形成，消除中间有符号乘减溢出。保持既有位模式结果；不由此赋予 C 除零或不可表示商新的语言语义。

```diff
diff --git a/abstract-machine/klib/src/int64.c b/abstract-machine/klib/src/int64.c
index 13376f429deb9d9855355c6a45adeabb980c1b29..41a9ce685d06a512c315ec28d08ce8d2e26b218d 100755
--- a/abstract-machine/klib/src/int64.c
+++ b/abstract-machine/klib/src/int64.c
@@ -370,12 +370,12 @@ COMPILER_RT_ABI di_int
 __divdi3(di_int a, di_int b)
 {
     const int bits_in_dword_m1 = (int)(sizeof(di_int) * CHAR_BIT) - 1;
-    di_int s_a = a >> bits_in_dword_m1;           /* s_a = a < 0 ? -1 : 0 */
-    di_int s_b = b >> bits_in_dword_m1;           /* s_b = b < 0 ? -1 : 0 */
-    a = (a ^ s_a) - s_a;                         /* negate if s_a == -1 */
-    b = (b ^ s_b) - s_b;                         /* negate if s_b == -1 */
+    du_int s_a = (du_int)(a >> bits_in_dword_m1); /* unsigned sign mask */
+    du_int s_b = (du_int)(b >> bits_in_dword_m1);
+    du_int a_u = ((du_int)a ^ s_a) - s_a;         /* includes magnitude of MIN */
+    du_int b_u = ((du_int)b ^ s_b) - s_b;
     s_a ^= s_b;                                  /*sign of quotient */
-    return (__udivmoddi4(a, b, (du_int*)0) ^ s_a) - s_a;  /* negate if s_a == -1 */
+    return (di_int)((__udivmoddi4(a_u, b_u, (du_int*)0) ^ s_a) - s_a);
 }
 
 /* Returns: a / b, *rem = a % b  */
@@ -384,7 +384,7 @@ COMPILER_RT_ABI di_int
 __divmoddi4(di_int a, di_int b, di_int* rem)
 {
   di_int d = __divdi3(a,b);
-  *rem = a - (d*b);
+  *rem = (di_int)((du_int)a - (du_int)d * (du_int)b);
   return d;
 }
 
@@ -394,13 +394,13 @@ COMPILER_RT_ABI di_int
 __moddi3(di_int a, di_int b)
 {
     const int bits_in_dword_m1 = (int)(sizeof(di_int) * CHAR_BIT) - 1;
-    di_int s = b >> bits_in_dword_m1;  /* s = b < 0 ? -1 : 0 */
-    b = (b ^ s) - s;                   /* negate if s == -1 */
-    s = a >> bits_in_dword_m1;         /* s = a < 0 ? -1 : 0 */
-    a = (a ^ s) - s;                   /* negate if s == -1 */
+    du_int s = (du_int)(b >> bits_in_dword_m1);
+    du_int b_u = ((du_int)b ^ s) - s;
+    s = (du_int)(a >> bits_in_dword_m1);
+    du_int a_u = ((du_int)a ^ s) - s;
     du_int r;
-    __udivmoddi4(a, b, &r);
-    return ((di_int)r ^ s) - s;                /* negate if s == -1 */
+    __udivmoddi4(a_u, b_u, &r);
+    return (di_int)((r ^ s) - s);
 }
 
 /* Returns: a / b */
```
