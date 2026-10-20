# CRP F0047 — RT BSP tick时钟与中断返回切换

2026-10-20；用户“提交后继续”授权F0032提交后执行本单元，前组实际30bbde81dea31297365b3e5fa8cccba0c1e9004f。M2保持。

**当前结论：uptime方案已批准并实施，F0047 Completed，结果确认/本组commit Pending。累计100完全已修/19未修完。** 前述提交后分析/待决历史保留，当前结果见“本次实施与验收”。

## 本单元计划与停点

复用TASK_QUEUE：核EVENT_IRQ_TIMER空分支、100Hz配置、AM/NEMU时间源与RT中断调度契约；现源计数/超时见证后，契约明确则最小修复，验证频率换算/timeout/软timer/时间片与真实RT update/run消费者，完整源码diff/正反身份及清理留档。发生实际时间/频率/能力取舍先最少裁决；不扩NPC硬件/其他组，不改公开Make或擅自安装。完成或待决后停止，结果确认/commit分开；本次无新组commit/push/M2授权。

交付：BSP必要源码（仅策略明确后）、本报告/局部ignore/local配方与日志/结果/身份/清理回执、records索引/repair-status/.agent。分析文档不新增实施前commit门槛。

## 实际源链与未决时间语义

- RT rtconfig.h配置RT_TICK_PER_SECOND=100及RT_USING_TIMER_SOFT；BSP context.c EVENT_IRQ_TIMER直接break，当前没有tick推进。
- NEMU alarm.h TIMER_HZ=60，alarm.c设置ITIMER_VIRTUAL/SIGVTALRM（进程用户CPU时间）且timer.c的timer_intr仅置待处理中断，可能合并。不能把每个事件当10ms，也不能保证每墙钟秒正好60次。
- AM NEMU uptime读RTC寄存器；当前NEMU .config选择CLOCK_GETTIME，get_time使用CLOCK_MONOTONIC_COARSE差值。它是宿主单调经过时间，与ITIMER_VIRTUAL不是同一时间域。讲义[分时多任务](https://ysyx.oscc.cc/docs/ics-pa/4.4.html)（2026-10-20访问）描述的是每10ms理想事件，不能替代本地60Hz虚拟CPU计时现状。
- RT clock.c的rt_tick_increase可因时间片/定时器调用rt_schedule；scheduler_up.c先更新rt_current_thread，再按rt_interrupt_nest分普通切换/中断切换。BSP必须enter/leave建立nest并在中断返回时交还正确Context，不能直接按普通yield路径切换。
- 当前RT非SMP rthw.h声明rt_hw_context_switch_interrupt(from,to,from_thread,to_thread)，BSP却定义SMP式(context,from,to,to_thread)且assert(0)；timer原先不tick掩盖该断点。启用tick需要一并接通当前非SMP中断切换，不扩SMP能力。
- 初始化实际在src/init.c：ioe_init→__am_cte_init→RT entry。NPC CTE能识别timer cause但未由此证明NPC硬件周期tick可达；本单元不增加硬件或伪称NPC已支持周期抢占。

建议A：保留NEMU中断/时间源及100Hz配置，以AM uptime自初始化基准计算已过周期，在timer事件补计全部欠tick（包括宿主长暂停），建立RT中断nest，记录最初from/最终to并在最外层中断返回时保存/选择Context。代价是补计处理时间随欠tick数增长，无法声称硬实时中断延迟上界。B：先另定模拟时间域/定时源统一方案，会影响共享NEMU/nanos等消费者，不在本次直接扩改。已按WORKFLOW_POLICY§3提出A/B选择；生产尚未修改，不能从“继续”自行裁决这一时间语义。

## 必要观察与方案批准（2026-10-20）

host使用实际AM/RT头与BSP源，喂入60个timer事件：现源tick调用0；仅测试副本把空分支改为每事件rt_tick_increase得到60，不等100Hz要求；另一测试副本加enter/tick/leave后，受控tick桩模拟RT中断调度调用，当前BSP中断切换assert/halt1精确复现。实际rthw.h与原context.c同编译单元出现conflicting types，证实非SMP签名不一致。共7条编译/运行命令符合预期。该计数并非实测每秒60次IRQ，tick/内核调度为受控边界，不冒称真实RTOS验收。初编译缺finsh.h，补入现有finsh include后再验，初失败日志保留。

用户对具体问题明确选择“按 uptime 补齐 tick（推荐）”：批准保留NEMU定时源/100Hz，按AM uptime自基准补计全部欠tick（长暂停也补计），实现RT中断返回切换，不增加NPC硬件能力。解除本项待决，直接继续当前F0047实施与真实回归；分析文档未提交不新增门槛。本选择不是新结果确认或commit授权。

## 完整实际修复diff

所属根仓ysyx-workbench，路径相对根。旧完整commit `30bbde81dea31297365b3e5fa8cccba0c1e9004f`；新为2026-10-20未提交工作树。旧SHA256 `a240995aa54d5ac2acc74958f586c20548d9d57ab3ed68c051e7cb05d6ad05b0`；新SHA256 `95dd8996e9d44d3808e27de9d3118169401991032e1e4698125f25005003a96a`，Git mode100755保持。

```diff
diff --git a/rt/bsp/abstract-machine/src/context.c b/rt/bsp/abstract-machine/src/context.c
index 0e490b5eda053f8affc40fcd60aa80d82c2b99cb..e131d8683088639330dab9de7bbf8b68a2e6a1c3 100755
--- a/rt/bsp/abstract-machine/src/context.c
+++ b/rt/bsp/abstract-machine/src/context.c
@@ -1,6 +1,12 @@
 #include <am.h>
 #include <klib.h>
+#include <klib-macros.h>
 #include <rtthread.h>
+#include <rthw.h>
+
+static uint64_t tick_time_us;
+static uint64_t tick_fraction;
+static rt_ubase_t irq_from, irq_to;
 
 typedef struct {
   void (*tentry)(void*);
@@ -27,7 +33,24 @@ static Context* ev_handler(Event e, Context *c) {
       c = *((Context**) cp_addr->to);
       break;
     }
-    case EVENT_IRQ_TIMER: break;
+    case EVENT_IRQ_TIMER: {
+      rt_interrupt_enter();
+      uint64_t now = io_read(AM_TIMER_UPTIME).us;
+      uint64_t elapsed = now - tick_time_us;
+      tick_time_us = now;
+      // Preserve fractional ticks; an IRQ is a delivery opportunity, not a tick.
+      uint64_t fraction = (elapsed % 1000000) * RT_TICK_PER_SECOND + tick_fraction;
+      uint64_t ticks = (elapsed / 1000000) * RT_TICK_PER_SECOND + fraction / 1000000;
+      tick_fraction = fraction % 1000000;
+      while (ticks-- != 0) rt_tick_increase();
+      rt_interrupt_leave();
+      if (rt_interrupt_get_nest() == 0 && irq_from != 0) {
+        *((Context **)irq_from) = c;
+        c = *((Context **)irq_to);
+        irq_from = irq_to = 0;
+      }
+      break;
+    }
     default: printf("Unhandled event ID = %d\n", e.event); assert(0);
   }
   return c;
@@ -40,6 +63,9 @@ void wrapper_function(void *arg) {
 }
 
 void __am_cte_init() {
+  tick_time_us = io_read(AM_TIMER_UPTIME).us;
+  tick_fraction = 0;
+  irq_from = irq_to = 0;
   cte_init(ev_handler);
 }
 
@@ -65,8 +91,11 @@ void rt_hw_context_switch(rt_ubase_t from, rt_ubase_t to) {
   yield();
 }
 
-void rt_hw_context_switch_interrupt(void *context, rt_ubase_t from, rt_ubase_t to, struct rt_thread *to_thread) {
-  assert(0);
+void rt_hw_context_switch_interrupt(rt_ubase_t from, rt_ubase_t to,
+                                  rt_thread_t from_thread, rt_thread_t to_thread) {
+  // Several catch-up ticks may schedule: save the interrupted thread only once.
+  if (irq_from == 0) irq_from = from;
+  irq_to = to;
 }
 
 rt_uint8_t *rt_hw_stack_init(void *tentry, void *parameter, rt_uint8_t *stack_addr, void *texit) {
@@ -88,4 +117,4 @@ rt_uint8_t *rt_hw_stack_init(void *tentry, void *parameter, rt_uint8_t *stack_ad
   // remain valid throughout the wrapper's execution.
   Context *cp = kcontext((Area) { args_addr - sizeof(Context), args_addr }, wrapper_function, ctx_args);
   return (rt_uint8_t *) cp;
-}
\ No newline at end of file
+}
```

实现语句：__am_cte_init在CTE注册前记录uptime微秒基准并清小数/切换记录；每次timer先enter，再取now、更新基准，按整秒与不足1秒部分换算100Hz并保留不足一tick的分子余数（单位为tick×微秒），避免60Hz当100Hz和逐事件截断漂移。循环补足全部欠tick，不设截断；按批准策略长暂停可增加处理时间。leave后只有最外层nest=0时才把原timer Context保存至第一次from，并返回最后一次to的Context。中断切换函数改用当前非SMP rthw签名，记录首次from/最新to，不在ISR里普通yield。原EVENT_YIELD的user_data恢复/Context桥接保持。新增rthw头使签名静态校验生效，klib宏头提供io_read；EOF补齐换行亦在完整diff内，不改变运行语义。

正反patch在隔离目录逐字节/执行位核验通过，反向保留旧EOF无换行；身份见implementation/archive-validation.json。

## 本次实施与验收（2026-10-20）

用户批准uptime补齐方案后直接完成本F0047；生产仅根仓RT BSP context.c33增4删，含EOF补齐换行，公开Make/配置/共享定时源不变。功能Completed，结果确认/本组commit Pending；累计100完全已修/19未修完，前99已确认提交30bbde8，M2保持。前述必要分析/待决是批准前历史。

| 验证 | 结果与实际范围 |
|---|---|
| 原问题/简单候选 | 原BSP喂60事件tick0；测试副本逐事件加一为60；测试副本加RT nest后触发中断切换占位assert，实际rthw.h揭示非SMP签名冲突。仅host受控观察，不把60个合成事件当实测1秒。 |
| 最终host | 实际BSP/AM/RT头，普通、ASan+UBSan、NDEBUG加san全部通过，六编译/运行命令exit0。覆盖高64位uptime起点、60事件1秒精确100tick、9999/10000us边界/重复事件不多记、余数保持、超过32位微秒的长暂停（补500001tick）、首个from/最后to与中间sp不覆盖、嵌套返回不早切换、原yield/user_data恢复。500404检查包含长暂停循环重复检查，不称为独立场景数量。 |
| 原完整RT guest | 相同测试/真实RT clock/irq/scheduler/timer核心配原context源，NEMU实际执行：1秒tick=0，明确F47 FAIL stage=clock value=0/BAD/exit1；不以超时猜测旧错误。 |
| 最终完整RT guest | 真实RT核心+最终BSP：约1000009us增长100tick；信号量5tick超时返回-2且实测5tick；soft timer单次回调，约100001us；两个同优先级线程忙循环无主动yield，peer885468/own159897次循环、16次ISR调度，s2/s3寄存器哨兵保持；GOOD/exit0。 |
| context.c NDEBUG真实guest | 只给本次模块编译-DNDEBUG，RT其他模块按原配置：约1000008us=100tick、5tick超时、soft回调100001us、peer899895/own176359及16次ISR调度，GOOD/exit0。未声称全RT NDEBUG构建支持。 |
| 生产NEMU RT消费者 | 现有update产出集成4应用，按既有NEMU测试链接片段配置image，再运行无测试源的完整生产RT，msh后继续2秒无失败；2.434秒后自有组SIGTERM，宿主NEMU handler退出0，非guest正常GOOD终止。实际命令/链接配置明确保存，不声称无需链接配置的原生NEMU Make默认路径。 |
| 生产NPC/REF消费者 | 现源码新构建NPC/REF并核REF ABI，原update/image ARCH=riscv64-npc成功；新模型/REF实际RT到msh，difftest ON，151.618秒后自有组SIGTERM/exit-15。此证明BSP初始化/正常切换兼容，**不证明NPC新增100Hz硬件中断/抢占能力**。 |
| 最终归档/保护 | 53项preclean通过，3232份隔离输入/产物身份及50份实际共享RT核心源身份；最终target普通/模块NDEBUG/生产BSP同SHA，完整正文diff正反逐字节/执行位通过；8项正式配置/引擎/盘/header/内核/RT资产保持entry SHA，根HEAD30bbde8/index空。 |

实际命令/环境/退出和身份见local/implementation/host-results、real-results、prepare-results、npc-build-results、standard-nemu-result、rt-result、archive-validation及各日志。旧/最终/模块NDEBUG完整RT均使用同一本次源码构建NEMU，未改timer-source（默认legacy）。pure标准NEMU和NPC均不含测试源。REF只用于NPC生产到msh，对NEMU异步时钟测试不冒称有difftest。

夹具与中间修正：首次生产编译漏io_read所需klib宏头，host指出后补齐该必要include，再对最终源验收。首次目标复制am-apps.mk时对已带build前缀条目重复加路径，未找到源前置；改为复制本组已生成的隔离集成目录，初失败日志保留initial-app-path。曾尝试整个RT加NDEBUG，现存init.c断言变量未用及libc assert占位无返回导致-Werror失败；未改无关代码或关闭警告，改为只对本次context.c目标加NDEBUG并明确限界，原失败保留initial-global-ndebug。host与guest曾共享ndebug-run.log名，预清理检查发现覆盖，改为host专用前缀并重跑三host配置保存完整新日志；旧正常/san日志与历史JSON仍保留，不谎称被覆盖的原host NDEBUG原日志存在。最终guest无需因此重复运行。

## 复现、影响与未测

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0047/local/implementation/host.py
python3 npc/verif/records/process/code_correctness_review/crp-f0047/local/implementation/prepare.py
python3 npc/verif/records/process/code_correctness_review/crp-f0047/local/implementation/real.py
python3 npc/verif/records/process/code_correctness_review/crp-f0047/local/implementation/standard-nemu.py
python3 npc/verif/records/process/code_correctness_review/crp-f0047/local/implementation/npc-build.py
python3 npc/verif/records/process/code_correctness_review/crp-f0047/local/implementation/npc-run.py
```

prepare/npc-build拒绝覆写已有目录；恢复先核进程与现存结果。real.py按已成功且源码身份一致的条目补做缺失项，失败原日志另存，不从头重跑已验收路径。重建旧源取30bbde81dea31297365b3e5fa8cccba0c1e9004f，最终源取本文SHA/repair.patch，不在未来修改源上冒充本次身份。隔离RT核心通过只读使用原文件的目录symlink构建，生成文件均在记录树内；配置/输入哈希和配方保留，无下载/安装/系统改动。

本修复仅RT BSP，不修改NEMU/AM/Navy/nanos/RTL；CPU-tests、nanos不消费BSP，不重复其回归；AM集成应用已按实际平台update编译纳入RT生产镜像，但未运行四个应用业务。NEMU正常time源单调，假设AM uptime不倒退；长暂停全补计，无ISR处理上界，补计批次中调度选择延至最外层返回、可能出现未实际运行中间线程却消耗其逻辑时间片，这是所选补计/延后切换策略的结果，不承诺公平性/硬实时指标。高64位/嵌套中断用host证明，真实NEMU没有主动在IRQ内重新开中断，未动态声称硬件嵌套；未测SMP/native/其他ISA/任意无效Context、所有RT配置、长期tick回绕或NPC周期timer。全RT NDEBUG原有构建断点未修。F0031/F0043/F0118等独立未决/Partial保持，不扩M2。

## 最终清理与完成边界

53preclean/3232隔离身份/50共享RT源身份、完整diff正反与实际消费者均完成，所有构建/guest已结束；删除3243文件/链接、321639506逻辑B/330768384分配B，0tracked/正式资产删除，仅本组记录树下模型/REF/镜像/对象/构建目录及源码副本。保留本报告、最小host/guest/准备/执行配方、实际日志/结果/配置/身份/patch/归档/cleanup-plan与receipt；不跟随RT核心目录symlink删除正式源。旧模型须重建，hash只标识当时身份。

F0047 Completed，Working tree contains uncommitted F0047 code/documentation changes，根HEAD30bbde8/index空；无push/安装/运行中动作。本组结果确认/commit Pending，100已修19未修完；唯一后续TASK_QUEUE#crp-next，下一F0072未Start，当前停止，不自动提交或下一组/M2。建议开启新对话：本轮跨VME提交、时间策略裁决及两平台RT调度验证，下一项转启动布局；恢复入口和未测边界完整。

最终一致性终检：36项PASS、84份保留证据身份，实际生产patch/8正式资产/3243预期清理/119行100与19及唯一下一入口一致。未新增动态测试或commit；F0047 Completed，结果确认/commit Pending，当前停止。

## 提交时平台时间基准说明（2026-10-20）

来源：用户本轮要求“提交，并解释NEMU/NPC变化及NPC now含义”。这只是对当前代码事实的说明，不重开功能Phase、不新增NPC时钟实施范围。

NEMU原本已产生timer事件，但BSP忽略它，RT tick停留不动；现在每次事件按真实AM uptime微秒累计100Hz tick，驱动时间片、阻塞超时和软件timer，并通过中断返回切换线程。事件仍是原有约60Hz虚拟CPU计时源，并未变为每10ms一次硬件事件；100Hz是软件逻辑时间基准，递送可批量/迟到。已验收1秒100tick/5tick超时/soft timer和无主动yield抢占，长暂停仍全补计。

NPC不同：am/src/riscv/npc/timer.c直接用64位ld读0x0200bff8并把mtime原值放入uptime->us；RTL clint每posedge clock加1，复位为0，与CPU接同一clock（显式软件写mtime可改变原值）。故此now是采样时累计的模拟硬件周期计数，不是指令数、RT tick数或宿主经过的微秒。字段名.us沿用现有相对时基，代码注释明确未定义真实频率、不除divisor。若mtime频率将来定义为f_Hz，真实微秒换算应为mtime×1000000/f_Hz；不能直接用综合f_max或仿真跑速替代f_Hz。RT初始化基准已包含启动阶段消耗的周期，elapsed=now-tick_time_us才是两次采样间增量。

当前NPC AM CTE初始化只设mtvec和handler，不开mie.MTIE；RT/AM NPC代码也不设置或周期重装mtimecmp，RTL复位mie=0。因此当前标准RT/NPC启动不因本改动自动具有周期timer tick/抢占：__am_cte_init新增初始uptime采样，原yield路径保持；若未来投递timer事件，新增处理分支才会执行。在沿用当前未经校准的NPC uptime时，该算法会把10000个mtime计数当作一个RT tick，并不能称为真实100Hz。仅打开MTIE也不够：mtimecmp复位0使MTIP持续为真，需要周期重装比较值，否则可能形成连续中断。NPC本次验收仅是新BSP兼容启动/msh/difftest ON，并未验收NPC周期抢占。后续如要启用NPC周期RT时钟，应独立明确mtime频率/换算及mtimecmp重装/MTIE，按已有阶段门槛规划，不在本轮擅改。

以上静态链路来源：AM NPC timer.c/cte.c、npc/vsrc/ysyx_22040750.v的clint计数/比较及CSR门控、NEMU timer/alarm/utils timer；身份保存在local/submit-explanation-sources.json。本次不新增动态测试，不把静态说明改写为新硬件运行结论。

## 用户确认与提交收尾（2026-10-20）

用户“提交，并解释”确认已报告范围并授权精确提交F0047及本平台时间说明；不授权下一F0072。提交前84份证据身份、完整生产patch/8正式资产与36项终检复核一致，复用动态验收，不重复Completion。实际commit/路径/blob核验见local/submit-receipt及.agent；无push。建议开启新对话：已跨VME提交、RT调度和平台时基核对，下一项转布局，恢复入口完整。
