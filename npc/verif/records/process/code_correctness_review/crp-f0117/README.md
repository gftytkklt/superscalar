# CRP F0117 — libam 64位累计微秒

现行交付为下方“NDL64最终实现与验收”；前面的直接系统函数候选已经撤回，按历史事实保留，不作为最终验收。

2026-10-20，用户“提交后继续”确认F0119并授权本单元；前组实际提交7912c42。复用CRP整体计划及workflow，当前Active。

## 本单元计划

仅修复libam/src/ioe.c AM_TIMER_UPTIME，经现有gettimeofday的64位秒/微秒直接换算，消除NDL uint32毫秒截断；沿用后端起点，不引入初始化偏移或NDL/SDL公开API变化。局部timeval零初始化，读取失败输出0，不使用旧值或未初始化字段；不增加时钟缓存/回绕状态。现有nanos gettimeofday成功返回0，失败只做定向注入验证。

1. 记录双方源码/HEAD/正式资产及旧回绕反例。
2. 最小实现，host普通及UBSan/ASan验证2^32ms前后、超过两个周期、秒微秒精度、多次及重复/失败初始化、读取失败；旧源码须明确失败。
3. 实际RV64运行同版libam/NDL，注入边界时间和实际gettimeofday调用链均验证；按影响覆盖标准Navy update→run，核对象/链接/盘身份，不推进VME/CTE。
4. 报告内嵌完整diff、逐语句说明、正反归档、最终身份、必要产物清理与records/.agent更新；完成后停等确认/提交，不自动commit/push/下一组/M2。无需安装，无真实未决项。

## 用户纠正与候选撤回（2026-10-20）

用户明确“讲义要求使用NDL接口，不要私自调用系统函数”。前述直接gettimeofday候选越过libam→NDL层次，已从生产ioe.c精确撤回至7912c42字节；其host/真实RV6467断言及标准update→run只是撤回候选的观察，不是F0117最终验收，F0117仍未修/Active。两种host普通及ASan/UBSan各67项、RV64注入边界及真实时钟67项、三前台/hello38→167原始日志保留；LeakSanitizer ptrace失败和最初runner预期68/实际67的计数错误亦保留。未提交此候选、未替换正式资产，所有本组进程已结束。

现NDL_GetTicks返回uint32毫秒。只用该值可做相邻采样的模差累计，但无法恢复首次调用前或两次调用间漏掉的完整2^32ms周期；不能无条件宣称完整64位时钟。若需完整64位且保留NDL层次，应由NDL新增64位时间接口，在NDL内读取后端，libam仅调用NDL；原32位接口/SDL行为可保持。此为原单元范围之外的接口/保证取舍，按AGENTS/WORKFLOW_POLICY§3等待用户裁决；未自行新增API或采用隐含采样间隔限制。候选完整补丁见local/ndl64-proposal.patch，仅用于审阅，未应用/未验收。

撤回候选收尾：8帧已目视；正式资产逐项SHA不变，生产ioe.c精确恢复；已清理9400文件/链接、507009648逻辑字节、0 tracked删除。完整patch/日志/身份/最小配方保留在local；旧候选的archive-validation与脚本只能用于解释撤回方案，不能作为当前或未来修复通过证据。F0117未完成，不生成Completion快照、不增加修复计数。

## NDL64方案已批准与实施计划（2026-10-20）

用户“同意，不要影响现有行为正确性即可”批准新增NDL64接口，覆盖上方待裁决状态；不恢复直接系统函数方案。现行交付：NDL.h新增NDL_GetTicks64(void)，NDL.c在原层内读原timevar并作64位毫秒换算，旧NDL_GetTicks仍返回低32位；libam仅调用NDL_GetTicks64()*1000。沿用原后端起点/毫秒精度/读取失败沿用timevar及Init/Quit不重置时间行为，不改SDL/API/系统调用后端或Make入口。

最终验收单独放local/approved：旧libam回绕反例、原/新NDL32跨边界/随机及失败序列逐项等价、最终真实libam+NDL普通与sanitizer、实际RV64注入边界及不注入真实gettimeofday→NDL→libam链、标准隔离update→run三前台/hello、同版对象/ELF/盘身份。最后内嵌三文件完整diff/正反归档、保护正式资产与清理/索引/状态；完成后停等用户确认/commit，不自动下一组或提交。

<a id="final-ndl64"></a>
## NDL64最终实现与验收（2026-10-20）

F0117 Completed，结果确认/commit Pending。用户已批准新增NDL64并要求不影响现有正确行为；3生产文件9增3删（含声明注释），不在libam直接调用系统时间函数。

- `NDL_GetTicks64(void)`仍在NDL层调用原`gettimeofday(&timevar, NULL)`，用`(uint64_t)tv_sec * 1000 + (uint64_t)tv_usec / 1000`计算毫秒，转换在乘法之前，避免32位结果截断。沿用现共享timevar、时间起点和向下取整毫秒精度。
- 原`uint32_t NDL_GetTicks()`只转发到64位函数并截为uint32，保持现公开签名、低32位周期和每次一次后端读取。未改SDL_GetTicks的起点或模减行为。
- libam仅调用`NDL_GetTicks64() * 1000`适配AM微秒字段；不会恢复不存在的亚毫秒精度，不依赖调用间隔或首次之前的采样。NDL Init/Quit不新增时钟重置/偏移。读取失败时仍沿用后端留下的timevar行为，未顺带增加错误协议、缓存或线程保证。

| 本轮验证（全部local/approved） | 结果及证明范围 |
|---|---|
| 旧libam确定性见证 | 从7912c42重建旧ioe.c，链接同一NDL；首次超过两个周期只得123000而非8589934715000，边界4294967295000→0，exit1精确拒绝。不是旧无参UB或随机时钟观察。 |
| host普通/ASan+UBSan | 每组90断言通过，实际生产ioe.c+NDL.c参与；首次晚调用、多周期/2^32ms边界、毫秒截断、32/64接口互调、重复初始化/失败初始化/Quit后起点、读取失败沿用上次值和恢复、实际系统时钟2ms进展。 |
| 原32位行为等价 | 原/新NDL分别链接同一受控时间后端，1000个有效timeval样本及首次失败、不写入失败、部分写入失败、Quit序列输出逐字节一致，每次一次后端调用。并非宣称非法timeval或线程并发全部等价。 |
| 真实RV64 libam消费链 | 实际生产libam/NDL归档链接进诊断Navy应用，88断言/main0/GOOD TRAP；边界由gettimeofday链接包装注入，随后切换到真实libos→nanos→AM时钟，同一libam/NDL读取158000us并实际递增2000us。只在隔离kernel把SYS_exit记录后halt，以核main返回，不改生产OS语义。 |
| 判据负例 | 同一真实日志的非零host退出/缺PASS/错断言数/错main返回/重复PASS/BAD TRAP六种都拒绝；最初runner沿用旧lo=标签而新日志为lo_ms=导致拒绝，修正判据后重审同一原日志，不伪造重跑。 |
| 标准Navy update→run | 隔离当前源码/已有资源，nanos目录现有make ARCH=riscv64-nemu update exit0（25.986s），再run；新NDL参与标准构建。三前台10个实际SDL按键、nterm qzx返回prompt、slides0/1/0及PAL返回/Enter，hello38→168，8帧已目视。54.054s后自有进程组SIGTERM，make -15不是正常guest退出。 |
| 实际对象/链接/盘 | libam归档成员与实际ioe.o一致，undefined只引用NDL_GetTicks64且无gettimeofday；NDL归档成员/三源复制一致。诊断ELF/盘payload一致；标准108 extent逐项匹配、四启动ELF与安装文件一致；正式资产未替换。 |

初次sanitizer夹具在NDL初始化断言失败；仅在测试编译禁用_FORTIFY_SOURCE后同一用例通过，生产编译/配置不变。ASan/UBSan有效；LeakSanitizer仍按环境ptrace限制关闭，不声称内存泄漏检测通过。原失败日志保留。

本轮不重跑CPU全集/RT：仅改Navy NDL/libam，CPU-tests与RT AM timer路径不链接这两个Navy库。F0086/F0113的完整nanos-lite-guest/VME/CTE能力未实现；诊断直接可执行libam IOE链不依赖它们。没有连续运行49.7天，边界注入证明换算/宽度；真实短时clock只证明实际链路及进展。不扩线程同步、单调时钟或故障返回契约。

参考已读[讲义“精彩纷呈的应用程序”](https://ysyx.oscc.cc/docs/ics-pa/3.5.html)（2026-10-20）的NDL/上层库抽象分层；具体libam只经NDL的约束以及新增64位接口批准以本轮用户明确指令为准，不将新增接口说成讲义原有标准。

## 最终三文件完整diff与身份

根仓ysyx-workbench；旧完整commit `7912c421e3ca183378c18b8717de18ad59d9bf5f`。新为2026-10-20未提交工作树，三源原mode100755保持；无nested源码修改。

- `navy-apps/libs/libndl/include/NDL.h`：旧SHA256 `2f5eb8a7c35cd009b9b47af63b1a6dbbcc4e4d1516b1a6558f5534b11921a0bc`；新SHA256 `d8ed7c7db5e1af7b1edc951767321107db2b20621d5540b7c522068e3a81a7bb`。
- `navy-apps/libs/libndl/NDL.c`：旧SHA256 `9ef9e15dedb8413db855a798bdcf11c97fff3273b8ffaa4dff8a56dca4252777`；新SHA256 `5cd7c3f859dfa06bd88738d484419e8ba1ef2ec80574f48a1ccf007bc5c74683`。
- `navy-apps/libs/libam/src/ioe.c`：旧SHA256 `e5e13eff1ff24fbbb494cff57b20be29cf1f5e8f2a24b26338589220e4f0b16f`；新SHA256 `84c5299886699f67cad5736030b0a0c27968e9191cd10048093c4278fe29e381`。

```diff
diff --git a/navy-apps/libs/libam/src/ioe.c b/navy-apps/libs/libam/src/ioe.c
index 4f08f22fa01895e31fbeef02675fbabca9aa5554..40b499e533864c22522720bbe0164f8139855e4d 100755
--- a/navy-apps/libs/libam/src/ioe.c
+++ b/navy-apps/libs/libam/src/ioe.c
@@ -36,7 +36,7 @@ void ioe_read(int reg, void *buf) {
     }
     case AM_TIMER_UPTIME: {
       AM_TIMER_UPTIME_T *t = (AM_TIMER_UPTIME_T *)buf;
-      t->us = (uint64_t)NDL_GetTicks() * 1000;
+      t->us = NDL_GetTicks64() * 1000;
       break;
     }
     case AM_INPUT_CONFIG: {
diff --git a/navy-apps/libs/libndl/NDL.c b/navy-apps/libs/libndl/NDL.c
index 471125a4fe49d12ffd85f7167d7939e561efc58d..7f9487a5e4270f295ab0ec7a7e2019c7f462694c 100755
--- a/navy-apps/libs/libndl/NDL.c
+++ b/navy-apps/libs/libndl/NDL.c
@@ -15,9 +15,13 @@ static int screen_w = 0, screen_h = 0;
 static int canvas_w = 0, canvas_h = 0;
 static struct timeval timevar = {};
 
-uint32_t NDL_GetTicks() {
+uint64_t NDL_GetTicks64(void) {
   gettimeofday(&timevar, NULL);
-  return (timevar.tv_sec*1000 + (timevar.tv_usec)/1000);
+  return (uint64_t)timevar.tv_sec * 1000 + (uint64_t)timevar.tv_usec / 1000;
+}
+
+uint32_t NDL_GetTicks() {
+  return (uint32_t)NDL_GetTicks64();
 }
 
 int NDL_PollEvent(char *buf, int len) {
diff --git a/navy-apps/libs/libndl/include/NDL.h b/navy-apps/libs/libndl/include/NDL.h
index 957d9b3f4ab3579244e407001e4b87fc38c89ea4..418fad613f922f8d6e71fe34557a7e416beb35cb 100755
--- a/navy-apps/libs/libndl/include/NDL.h
+++ b/navy-apps/libs/libndl/include/NDL.h
@@ -10,6 +10,8 @@ extern "C" {
 int NDL_Init(uint32_t flags);
 void NDL_Quit();
 uint32_t NDL_GetTicks();
+// Same time source and millisecond unit as NDL_GetTicks, without 32-bit wrap.
+uint64_t NDL_GetTicks64(void);
 void NDL_OpenCanvas(int *w, int *h);
 int NDL_PollEvent(char *buf, int len);
 void NDL_DrawRect(uint32_t *pixels, int x, int y, int w, int h);
```

内嵌diff等于实际三源完整差异，已从注明旧Git版本正向应用逐字节等于最终源，反向逐字节恢复；archive-validation.json/repair.patch记录结果。撤回方案patch和早先manifest留在local根，仅为历史，不与approved混用。

## 最小复现与停点

在根工作区设`H=npc/verif/records/process/code_correctness_review/crp-f0117/local/approved`，源码按本报告版本/身份恢复；只使用已有资源及工具，不下载、不安装，不替换正式产物：

```sh
python3 "$H/host.py"
python3 "$H/prepare-runtime.py"
python3 "$H/standard-path/run-standard.py" nanos
python3 "$H/prepare-guest.py"
python3 "$H/run-guest.py"
```

运行前确认本组隔离目录已按清理回执不存在；这些一次性脚本/原始证据本地忽略，不提交。最终提交候选仅三生产源、报告/.gitignore及两个records索引。ignored/.agent不随commit备份。未来只沿TASK_QUEUE唯一入口，本单元完成停等用户结果确认及提交；无自动commit/push/下一组/M2。

最终收尾：166项preclean通过（主要为身份/归档/盘对应检查，非166功能场景）；6002份源码/产物身份保存在approved/final-identities.json。验收与8帧目视完成、进程已结束后，删除9400文件/链接、507473688逻辑字节，0 tracked删除；包括隔离源码/构建树、两盘/ELF/对象/库、host与截图，保留配置/patch/日志/最小配方。旧产物身份哈希只说明当时产物，清理后不可直接执行；按配方重建。正式native/NPC/配置/盘保护身份不变；未操作或替换REF。

累计94已修/25未修完（含5CQ/F0040 Partial），前93已确认提交；F0117 Completed、结果确认/commit Pending。Working tree contains uncommitted F0117 repair/documentation changes，root HEAD7912c42/index空。下一单元只沿TASK_QUEUE#crp-next，F0118尚未Start，不自动提交或推进M2。

会话建议：可在当前对话继续；本轮只有NDL64修订及其验收，恢复入口和撤回/最终证据已区分。

最终终检20项全部通过，55份保留证据manifest已固定；内嵌diff精确、生产身份与正式资产保持、9400路径预期缺失及119行计数94已修/25未修完核对。无新动态测试或commit。

<a id="submit-20261020"></a>
## 用户确认与提交（2026-10-20）

用户再次“提交后继续”确认已报告的NDL64最终实现与验收，授权精确提交本组并在提交后执行唯一入口F0118一个单元。55份保留证据manifest/三生产源SHA及完整patch核对无漂移，复用20项终检和原动态验收/清理，不重复Completion或测试。候选只含三源、报告/.gitignore和两个索引；实际commit记录local/approved/submit-receipt.json及.agent，无push，ignored证据不随commit备份。

会话建议：可在当前对话继续；本次入口明确，NDL修订和最终证据已区分，F0118按现源先核失败契约。
