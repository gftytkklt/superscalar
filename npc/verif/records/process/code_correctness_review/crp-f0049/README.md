# CRP — CCR-F0049：AM 应用线程启动数据生命周期（2026-10-18）

> **Completed；用户已确认并授权提交。** 前组已提交e9a71f3，当前批修复未提交。

## 范围、计划与验收

用户“提交现有改动后继续CRP修复任务”授权本单元；前组已确认提交e9a71f3，root/index干净。复用[总修复计划](../REPAIR_AND_REGRESSION.md)、[现行流程](../workflow/README.md)、[唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。本项生命周期较复杂，独立成组，不推进M2。

仅修改`rt/bsp/abstract-machine/integrate-am-apps.py`的运行时C模板及必要声明：线程持有堆分配的启动记录和参数副本；分配/create失败回收，startup失败删除未运行线程；在startup之前安装cleanup，由RT现有idle回收流程统一释放。覆盖正常返回、AM halt主动exit、外部delete（含尚未执行入口）。保持命令签名、优先级/栈、共享AM data/bss/heap行为、F0051单mk发布语义和既有Make接口/日常流程。并发AM应用隔离、时钟接入F0047、新平台能力及未决CQ不在范围。

实施顺序：核对thread.c/idle.c与真实rtconfig→复用P5模板反例→最小模板修改与host sanitizer定向验证→真实RV64 RT生命周期、真实update/run到msh→最终源码/产物/证据核对及留档。验收包括延迟执行/调用栈销毁/argv改写，空参数、分配/create失败、startup失败、立即调度、正常返回/主动退出/入口前后删除及重复调用；区分mock故障与本地RT实际可达路径。沿用真实RT声明并验证idle实际cleanup，不能只在普通函数返回后free。

仅RT生成模板改变，CPU-tests及nanos无依赖，不重复回归；F0051发布代码未变，复用既有13项失败传播验收并核对实现/实际update。组末停止等待确认/commit，不自动提交/push；若出现真实契约冲突或安装事项则停止相关实施。

## 实现与验证入口

生产模板采用一个RT堆块保存类型正确的`int (*)(const char *)`和尾部字符串。分配/create失败直接回收；创建成功后先设`thread->cleanup`，再startup。cleanup通过`thread->parameter`释放并清空记录，沿用`thread.c`的defunct队列与`idle.c`回收，涵盖普通返回、`__rt_am_halt`/`rt_thread_exit`以及入口前后delete；不借用上下文切换临时使用的user_data。startup错误分支删除线程，由同一个cleanup负责回收。当前RT有效INIT对象的startup固定返回EOK，错误分支只用受控注入验证。

局部命令（在本目录local内执行，默认拒绝覆盖已有最终结果；一次性测试/日志不入库）：

```text
python3 host.local before
python3 host.local after
python3 prepare.local
python3 update.local
python3 instrument.local
python3 rt-final.local
python3 validate.local
```

host从Python AST提取精确C模板，使用真实AM/RT头文件和ASan/UBSan；原版延迟/栈销毁反例确认stack-use-after-return，修复后8/8通过。LSan在此受跟踪沙箱环境不支持，保留失败日志；正式重跑禁用LSan，由分配地址集合及精确分配/释放计数核对，不能声称LSan通过。

真实RV64夹具在隔离副本运行，使用前组已验收的新NPC模型及不变REF，DIFF=1/WAVE=0/WITH_TRACE=0/WITH_SDL=0/PERF=1/PERF_R45=1，规避自动Git构建钩子；生产root build不改。仅测试副本加入linker malloc/free包装、额外检查C和exact-template头，及生成C末尾一个调用原静态am_hello的测试入口；未改变原生成命令的实现，未增加生产Make目标/步骤。`integrated-production.c`保存测试入口附加前的生成C。

初次guest启动先于update完成，未集成的镜像不作验收；日志移动导致旧监督器退出，受沙箱会话管理，无最终通过结果。随后一次完整集成尝试在测试的调度锁中分配触发RT mutex断言，说明该夹具不满足本配置调用约束；已改为子线程低于调用者优先级、真实startup成功后保持ready，从而合法延迟。另一次夹具review提前取消以保留idle hook至真实hello回收完成。无效/取消尝试保留为local/rt-run-*、rt-invalid-critical-*、rt-cancelled-hook-review-*，均不计PASS。最终运行使用独立rt-final-*，监督器补识别RT小写assertion failed，最终运行后再做受控判据负例核对。

最终11场景包含16次真实重复启动及每次data/bss重置，执行时间高于初估；观察到前10场景均完成并持续推进后延长初始480秒窗口。外部控制只暂停已核实路径的监督器，guest保持运行；看到完整guest证据或扩展到期后恢复监督器，后者仍按实际串口与状态判定，记录见watchdog-extension.json。原启动监督器保存于rt-final-started-480.local；复现脚本rt-final.local改为900秒窗口以免重复外部延长。

最终日志中一条PERF主机统计插入了guest汇总标记的`calls`单词；原始日志原样保留，rt-final-serial.txt仅删除已知完整PERF行以还原串口字节。最终验收谓词在该串口视图核对完整11场景顺序、21次调用和75/75/live0，并以六个负例确认拒绝错误；未放宽guest结果。生成清单中C相对BSP、对象相对build/ARCH，核对按实际AM解析基准处理。


## 最终验收结果（Completed）

| 检查 | 本轮有效结果 / local证据 |
|---|---|
| 原版 / 修复后host | 原版0/8满足本次契约（含精确ASan stack-use-after-return及startup NULL）；修复后8/8通过ASan/UBSan，地址集合/分配释放一致；host-before、host-after |
| 延迟/参数所有权 | 真实RT低优先级ready线程在wrapper返回、局部字符串改写后正确执行；空参数及16次重复调用通过；rt-final.log |
| 分配/create失败 | 启动记录分配失败、真实RT thread object分配失败、真实RT stack分配失败均安全返回；已分配部分全部回收 |
| startup失败 | 测试包装返回错误、真实rt_thread_delete及idle回收通过；当前RT有效startup无自然失败返回，不伪造该能力 |
| 退出/删除 | 真实正常返回、rt_thread_exit、首次entry前删除ready线程、entry挂起后外部delete均经idle实际回收 |
| 组合计数 | 11场景全部PASS，21次测试main调用；另真实生成am_hello输出`mainargs = 'generated path'.`，其启动与清理通过；累计75次被跟踪分配/75次释放、live=0 |
| 真实update / run | update exit0，16对象+1C发布，四个MSH命令集成；NPC difftest ON，541.76秒到完整验收标记及msh；rt-update-result.json、rt-final-result.json |
| 执行链 / 假PASS保护 | 最终组合核对17项通过；最终验收谓词六个有区分力负例（缺标记/缺场景/BAD TRAP/DIFF ABORT/残留分配/超时）全部拒绝；checker-faults.json |
| 版本边界 | tested generator与root相同，仅AM_APP_C AST改变；F0051生成/失败传播/发布逻辑完全相同，复用原13/13证据（历史，本次未重跑）；实际新update成功 |

最终生成器SHA256：`b90c87c93e9f670f0573adb3d140c08291d0d41f93c1b06e75b5bcb93e92c997`。隔离副本`/tmp/crp-f0049-ctsq6cp1`；源码/RT配置、实际生成清单/ELF/BIN、精确模板/测试入口见local/artifacts，修复补丁见local/repair.patch，命令/退出/判据见对应local脚本与JSON，最终manifest绑定本轮证据。

监督器在观察到11场景、真实hello及msh后对自有进程组SIGTERM，make=-15、监督器exit0，非guest正常退出。最终证据校验还核对有效场景顺序、75/75及live=0，并排除失败标记；不能用单个msh或make状态替代验收。

## 收尾与限制

F0049 Completed；结果确认Pending、修复commit Pending；累计已修15/剩余104（含5CQ），不改变历史审阅分类。修改仅生成器模板、报告/局部忽略、记录索引及本地状态/进展；无长期新架构决策。HEAD e9a71f3、index空，Working tree contains uncommitted CRP F0049 changes；本轮未提交本项或push。

CPU-tests与nanos未受此RT生成模板影响，按既有回归契约不重跑；本轮真实RT平台仅riscv64-npc，其他平台/四应用全部运行/并发AM隔离/时钟与抢占/析构完整C++能力NotRun。分配跟踪限启动记录、线程对象和栈，未声称全系统无泄漏。软件安装和生产配置/Make接口未改变；一次性测试、生成C、日志/JSON/镜像全部local保存，不随普通commit备份。后续仅沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本组末停等确认/commit，不自动进入下一组或M2。


<a id="submit-20261018"></a>
## 2026-10-18 确认与提交回执

用户“提交后继续”确认已报告F0049范围并授权提交后执行唯一下一入口。复用既有收尾及host 8/8、真实RT 11场景/生成hello/75分配释放验收；提交前101份本地证据与已测生产源码无漂移，未重复产品测试或完成快照。提交只含生产模板、报告/局部忽略及process索引；一次性测试/镜像/日志、.agent和进展总表本地保存，实际提交回执见local/submit-20261018与.agent。未push。

前轮时长澄清：541.76秒含专项场景及16次反复恢复data/清零bss；这些循环/故障注入/统计钩子只在隔离测试副本，不进入日常镜像，不要求以后普通RT到msh回归都执行。本轮未做同条件性能对比，不声称精确保持160秒或以专项时长认定性能退化。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0049 — 根仓库

这是 Python 字符串模板内生成 C 的修改，diff 中双反斜杠属于模板转义，不应手工删改。

- 差异路径相对于仓库 `.`；旧版本：`e9a71f3cd3d11205f2616129747dba888dd0ab64`；新版本：`d9a3d423928bfbc6e008500a0c2cbd36d4121cbb`。

#### `rt/bsp/abstract-machine/integrate-am-apps.py`

F0049：模板使用一个 rt_malloc 块保存类型正确的 `int (*main)(const char *)` 和柔性数组字符串副本，替代栈上 `void *args[2]` 与借用 argv；wrapper 返回后线程仍可安全读取。分配失败直接返回，create 失败释放块；成功后在 startup 前挂 `tid->cleanup`，正常退出/启动前删除等均由 RT 生命周期清理 parameter 并置空。startup 失败调用 rt_thread_delete，复用同一清理路径。共享 AM 数据/BSS/heap 的初始化保持，不推定多个 AM 应用可并发隔离。

```diff
diff --git a/rt/bsp/abstract-machine/integrate-am-apps.py b/rt/bsp/abstract-machine/integrate-am-apps.py
index 5554add0ee24efee414c0b41b0aa1c98c3a1fd6f..3d76ebe8bc1538e9ddbb00c8068a44a9628ecf67 100644
--- a/rt/bsp/abstract-machine/integrate-am-apps.py
+++ b/rt/bsp/abstract-machine/integrate-am-apps.py
@@ -89,18 +89,43 @@ AM_APP_C = """#include <am.h>
 #include <rtthread.h>
 extern Area am_apps_heap, am_apps_data, am_apps_bss;
 extern uint8_t * am_apps_data_content;
-static void am_app_start_thread(void *args) {
-  void (*fn)(const char *mainargs) = ((void **)args)[0];
-  const char *mainargs = ((void **)args)[1];
-  fn(mainargs);
+struct am_app_args {
+  int (*main)(const char *);
+  char mainargs[];
+};
+static void am_app_cleanup(struct rt_thread *thread) {
+  rt_free(thread->parameter);
+  thread->parameter = RT_NULL;
 }
-static void am_app_start_wrapper(const char *app_name, void *app_main, int argc, char *argv[]) {
+static void am_app_start_thread(void *parameter) {
+  struct am_app_args *args = parameter;
+  args->main(args->mainargs);
+}
+static void am_app_start_wrapper(const char *app_name, int (*app_main)(const char *), int argc, char *argv[]) {
+  const char *mainargs = (argc >= 2 ? argv[1] : "");
+  rt_size_t size = rt_strlen(mainargs) + 1;
+  struct am_app_args *args = rt_malloc(sizeof(*args) + size);
+  if (args == RT_NULL) {
+    rt_kprintf("AM app %s: no memory for arguments\\n", app_name);
+    return;
+  }
+  args->main = app_main;
+  rt_memcpy(args->mainargs, mainargs, size);
+  rt_thread_t tid = rt_thread_create(app_name, am_app_start_thread, args, 0x4000, 0, 20);
+  if (tid == RT_NULL) {
+    rt_free(args);
+    rt_kprintf("AM app %s: thread creation failed\\n", app_name);
+    return;
+  }
+  // RT's idle cleanup owns the record, including exit/delete before entry.
+  tid->cleanup = am_app_cleanup;
   memcpy(am_apps_data.start, am_apps_data_content, am_apps_data.end - am_apps_data.start);
   memset(am_apps_bss.start, 0, am_apps_bss.end - am_apps_bss.start);
   heap = am_apps_heap;
-  void *args[2] = { app_main, (argc >= 2 ? argv[1] : "") };
-  rt_thread_t tid = rt_thread_create(app_name, am_app_start_thread, args, 0x4000, 0, 20);
-  rt_thread_startup(tid);
+  if (rt_thread_startup(tid) != RT_EOK) {
+    rt_thread_delete(tid);
+    rt_kprintf("AM app %s: thread startup failed\\n", app_name);
+  }
 }
 bool __dummy_ioe_init() { return true; }
 bool __dummy_cte_init(Context *(*handler)(Event ev, Context *ctx)) { return true; }
```
