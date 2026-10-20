# CRP F0023 — NEMU trap 来源与内核栈约定

2026-10-18。既有修复计划/唯一入口承接；用户“提交修改，并继续CRP修复”授权存档说明提交及本单元。存档说明实际提交47063cd，F0022已确认提交bc7a110；M2保持。

## 本单元计划与验收

仅修复riscv/nemu CTE的M/U trap来源、内核执行期间mscratch=0、用户返回时内核栈顶装入、cte_init初始化及Context大小推导。保持CTE/yield/kcontext/ucontext/Make接口；不扩展S态CTE、VME权限或F0024地址空间生命周期。无需安装或新策略裁决。

顺序：原版真实RV64失败见证 → 最小生产修改 → 真实guest M态yield/改sp/嵌套/计时、U态返回/改sp/上下文切换、np/MPP/mscratch/活栈哨兵 → 受影响RT NEMU到msh及nanos三前台/hello → 最终版本与证据核对留档。host只能辅助。组完成后停等用户确认，新修复不自动commit/push。

讲义参考：2026-10-18读取[PA4.1多道程序](https://ysyx.oscc.cc/docs/ics-pa/4.1.html)，其中Context指针/不同线程栈/内核线程接口说明用于本次栈切换验证；[PA3.2异常响应机制](https://ysyx.oscc.cc/docs/ics-pa/3.2.html)两次读取超时，不声明已读正文。本地NEMU trap入口保存前态MPP，mret按MPP恢复；原问题见[CCR-F0023](../FINAL_FINDINGS.md#ccr-f0023)，原P4证据保持。

## 执行结果

**Completed，结果确认/修复commit Pending。** 生产仅修改`abstract-machine/am/src/riscv/nemu/cte.c`：

- 每次入口按保存的MPP记录`np`，在读取地址空间或调用handler前清`mscratch`，包括无handler路径。
- 返回M上下文明确写0；返回U上下文用`c + 1`取得对应内核栈顶，删除硬编码288。trap汇编及Context布局保持。
- `cte_init`显式建立初始内核`mscratch=0`。不更改事件解码、mret或既有MPRV行为。

最终生产SHA256：`612381ad8f06d98d391e294648cef9a6f5ff2c9f0f24e875b921f9be3e78e3c4`，与隔离AM、保存的after副本一致。

| 验收 | 本轮结果 / 原始入口 |
|---|---|
| 原版真实RV64反例 | `before-rebuilt/`三模式均exit1/BAD TRAP：M来源实际MPP=3却np=0；无handler直接CTE调用不能建立正确np/清scratch；非零scratch初始化未清。最终夹具相同，明确重编cte.o |
| 修复后真实RV64 | `final/`三模式均exit0/GOOD TRAP；完整模式16次M yield、9次嵌套、1次真实MTIMER中断、2次U trap与1次kcontext线程启动/返回主线程；np/MPP、M scratch=0、U内核frame顶、改sp/活栈哨兵通过 |
| 无handler/初始化 | 两个独立guest分别检查直接`__am_irq_handle`的M/U上下文返回及脏scratch初始化。无handler场景是guest内直接调用CTE，不声明无handler的ecall事件处理或进度能力 |
| RT共享CTE | `make -j1 ARCH=riscv64-nemu git_commit= update`成功；隔离链接配置下image成功。真实NEMU到msh，预置help/date/version/free/ps/pwd/ls/memtrace/memcheck/utest_list/am_hello执行，出现Hello AbstractMachine及后续msh；观察后发送自有组SIGTERM，进程exit0，不声称guest正常退出/GOOD TRAP或difftest ON |
| nanos共享CTE/VME消费者 | `nanos-stable/`沿既有make run，约51.72秒，8个截图观察点：F2终端输入响应、F3翻页/返回页hash一致、F1返回PAL及Enter继续；hello计数1440→6648，8点严格递增。最后自有组SIGTERM、make=-15；不是guest正常退出 |
| 判据与版本 | 5个判据负例（错误exit、缺PASS、缺GOOD TRAP、BAD TRAP、assertion）均被拒绝；`validation.json`18/18，生产/隔离源码相同，trap.S未变，最终构建/命令/镜像身份已落档 |

RT/NEMU测试链接配置必须单列：当前RT默认布局针对NPC，NEMU标准脚本缺少既有am-apps段符号；第一次加原`extra.ld`仍因四个应用段符号未定义而链接失败。最终仅在本地`rt-extra-test.ld`补入NPC现有应用data/bss及8字节对齐，环境`LDFLAGS="-T <local>/rt-extra-test.ld"`，其余继续由既有NEMU脚本添加。此为测试配置，不提交或改变生产Make/链接脚本，不宣称原始无补充参数的RT/NEMU命令通过。链接片段第一版漏了表前对齐，RT在help后EVENT_ERROR；修正测试对齐后完整预置命令及am_hello通过。两次失败日志均保留，不归因为本组CTE。

Navy/生成器未改，nanos复用当前完整`navy-apps/build/ramdisk.img`与header，未重新update Navy；对应SHA见identities。CPU-tests没有CTE调用，NPC有独立cte.c，均不机械重跑；本次RT回归实际消费修改的NEMU CTE。没有改默认NEMU配置、重建NEMU解释器/REF/NPC或修改日常运行入口。

## 夹具纠错及证据有效边界

- 初次修复测试的测试调度器未在内核线程启动时清除测试切换标志，导致错误地重用初始Context；只修夹具标志，生产修复不变，最终完整模式通过。
- `before-final/`不作为原版见证：copy2保留老mtime，make复用修复后的cte.o。已明确INVALID，并用copyfile/当前mtime强制重编形成`before-rebuilt/`；原版三模式全部精确失败。其脚本当时对非`before`标签仍断言全PASS，因预期负例退出1；判断依据是各guest的实际exit/日志，不把runner断言当作产品反例。
- `nanos-final/`不验收：重跑构建脚本时重写了正在被LD_PRELOAD消费者映射的observe_sdl.so，污染运行资产，NEMU和make段错误。该轮7点观察及日志保留，但不计PASS、不推定产品回归。停止所有构建/共享库写入后完整`nanos-stable/`重跑通过；本组未修改音频协议或据此关闭F0043。

## 限制、留档和停点

仅验收RV64 NEMU既有M/U CTE。S态CTE、RV32/RVE、真实音频输出、长时调度、全部AM应用、Linux及NPC动态回归未测。嵌套例子返回原嵌套Context，没有在两个页表间切走再恢复，**不证明F0024地址空间保存已修**；权限/撤映射/回收及五CQ保持。PAL性能与音频竞争等原风险保持。

原始源码、命令、日志、ELF/bin、观察帧、隔离AM/RT/AM-kernels/nanos构建资产、测试链接片段、结果、身份、精确repair.patch与manifest在`local/`（约97MiB），本地忽略；不提交一次性夹具/生成证据，普通Git提交不代表这些资产已备份。Navy镜像、解释器与配置仍在原工程路径，identities只记录身份，不声称本组已复制其完整字节。

累计30项修复Completed，其中29已确认提交、本组待确认提交；89未修完含5CQ/F0040Partial。停止等待本组结果确认/commit，未来只沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动Start下一单元或M2、不push。

<a id="approval-submit-20261018"></a>
## 用户确认与提交（2026-10-18）

用户在核对MPP/mscratch及sp保存逻辑后，以“提交，然后继续CRP修复”确认本组已报告范围/限制并授权提交。3,958项manifest无漂移，原18项终检及生产patch相同，复用真实验收未重跑。仅提交生产cte.c、本组报告/局部ignore及3份相关索引/维护回执；ignored测试/.agent仍本地，不代表已备份。实际提交回执见local/submit-receipt及.agent；同条明确指令授权提交后执行F0024一个单元，新修复不自动提交，不push/M2。

实际提交补充：F0023已提交c9be8980d76b85f4f517f2c5ac21d8cf9e181def（6文件69增16删），提交检查点root/index干净、未push。随后按同条指令执行F0024；本组原3,958项证据在后组终检仍无漂移。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0023 — 根仓库

对应 AM 的 NEMU 平台 trap 适配，不是新增特权模式能力。

- 差异路径相对于仓库 `.`；旧版本：`47063cd2155083ed8e0a3b71791c426ebf0f733e`；新版本：`c9be8980d76b85f4f517f2c5ac21d8cf9e181def`。

#### `abstract-machine/am/src/riscv/nemu/cte.c`

F0023：按保存的 `mstatus.MPP` 设置 `c->np`，不再用 trap.S 已交换成旧 sp 的 mscratch 值猜测来源。处理入口立即清 mscratch，保证嵌套内核 trap 使用内核栈规则；返回前根据所选 Context 的 np 写用户内核栈顶或零。`(uintptr_t)(c + 1)` 代替写死 288 字节，随 Context 布局确定栈顶；cte_init 初始清零 mscratch。保留事件分类及地址空间切换。

```diff
diff --git a/abstract-machine/am/src/riscv/nemu/cte.c b/abstract-machine/am/src/riscv/nemu/cte.c
index 54d7f6e1027453d335cdce9bb1d7b23bf749d119..904a8208a51619de3891ffba998b1ee0e1d90232 100755
--- a/abstract-machine/am/src/riscv/nemu/cte.c
+++ b/abstract-machine/am/src/riscv/nemu/cte.c
@@ -1,24 +1,18 @@
 #include <am.h>
 #include <riscv/riscv.h>
 #include <klib.h>
-#define CONTEXT_SIZE 288
 static Context* (*user_handler)(Event, Context*) = NULL;
 
 Context* __am_irq_handle(Context *c) {
-  uintptr_t ksp = 0;
+  // trap.S leaves the interrupted sp in mscratch for both M and U traps.
+  // The saved MPP, rather than that exchanged pointer, identifies the source.
+  c->np = ((c->mstatus >> 11) & 3) == MODE_M ? KERNEL_MODE : USER_MODE;
+  asm volatile("csrw mscratch, zero"); // kernel execution, including nested CTE
   // record the current address space into the context
   __am_get_cur_as(c);
 
   if (user_handler) {
     Event ev = {0};
-    // Determine the next privilege (np): trap.S swapped mscratch into sp, so
-    // mscratch now holds the original sp. It is non-zero for a user trap and
-    // 0 for a kernel trap (kernel threads never have mscratch armed).
-    asm volatile("csrr %0, mscratch" : "=r"(ksp));
-    c->np = (ksp == 0) ? KERNEL_MODE : USER_MODE;
-    ksp = 0;
-    asm volatile("csrw mscratch, %0" : : "r"(ksp)); // support re-entry of CTE
-
     switch (c->mcause) {
       case 0x0b: case 0x8: c->mepc += 4;ev.event = (c->gpr[17] == -1) ? EVENT_YIELD : EVENT_SYSCALL; break;
       case 0x8000000000000007: ev.event = EVENT_IRQ_TIMER; break;
@@ -34,10 +28,8 @@ Context* __am_irq_handle(Context *c) {
 
   // Before returning to a user context, arm mscratch with that context's kernel
   // stack top, so the next user trap can switch to the kernel stack.
-  if (c->np == USER_MODE) {
-    ksp = (uintptr_t)c + CONTEXT_SIZE;
-    asm volatile("csrw mscratch, %0" : : "r"(ksp));
-  }
+  uintptr_t ksp = c->np == USER_MODE ? (uintptr_t)(c + 1) : 0;
+  asm volatile("csrw mscratch, %0" : : "r"(ksp));
 
   return c;
 }
@@ -45,6 +37,7 @@ Context* __am_irq_handle(Context *c) {
 extern void __am_asm_trap(void);
 
 bool cte_init(Context*(*handler)(Event, Context*)) {
+  asm volatile("csrw mscratch, zero"); // establish the initial kernel-stack rule
   // initialize exception entry
   asm volatile("csrw mtvec, %0" : : "r"(__am_asm_trap));
 
```
