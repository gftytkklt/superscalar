# CRP F0070 — VME初始化失败立即停止

2026-10-20；用户“提交并继续”授权F0076提交后执行本单元，前组已提交e7a3e2610b32de736e2e9f706b91aa317a1c5e23。M2保持。

## 本单元计划

目标/范围：只检查nanos init_mm的vme_init返回值；false诊断停止，成功仍初始化正常，HAS_VME关闭时不调用。采用已有panic_on，其halt(1)不受NDEBUG影响；不实现NPC VME/MPE、内存预算、ramdisk链接/启动复制或用户指针恢复。旧发现/调用链见FINAL_FINDINGS F0070、OS_RUNTIME、CROSS_LAYER_P6。NPC实际Make选择platform/dummy/vme.c，返回false；同名riscv/npc/vme.c并非当前链接选源。main先init_mm再device/irq/fs/proc；失败应在所有后续动作前停止。

一个单元：旧反例→最小修改→host普通/sanitizer/NDEBUG及成功/失败→实际RV64目标失败路径和正常NEMU三前台/hello；明确隔离失败夹具与实际NPC整机能力限制。必要时复用F0089页表/容量配方，不扩内存策略。交付生产一处修复、本报告内嵌完整diff及逐语句说明、local最小配方/命令/身份/日志/清理回执、records索引/修复镜像/.agent。正反patch逐字节验证，正式五资产保护。完成后停等结果确认/commit，不安装/push/下一组/M2。没有新能力/策略裁决；遇真实未决/安装依既有规则停止。

参考[讲义虚存/VME](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)（2026-10-20访问）：作为VME抽象和分页启动的背景，具体false及停止契约以本地am.h/实现、已规划F0070验收为准。

## 完整修复diff与语句说明

所属根仓ysyx-workbench，路径相对根；旧完整commit `e7a3e2610b32de736e2e9f706b91aa317a1c5e23`；新为2026-10-20未提交工作树。旧mm.c SHA256 `0c25b302ec1d9f18699fb8cad56c734dc3661f4a26255a1bb0805c324a22a259`，新 `f219788724b1a4a2afbe9c07368bd1f872aea10fde828bd6f6d4690f595a0311`，mode 100755保持。

仅将vme_init的结果用于panic_on的条件：vme_init仍恰好求值一次，返回true则条件为false，继续原初始化；返回false则输出固定诊断后halt(1)，main不能进入init_device/irq/fs/proc，因此不能沿loader进入protect/ucontext。pg_alloc/free_page回调和分配策略不变；现有panic_on宏不依赖assert/NDEBUG，关闭HAS_VME时该行仍被预处理去除。此检查不回滚AM内部已完成的部分初始化，不将失败目标降级为无VME启动，也不实现缺失的NPC能力。

```diff
diff --git a/nanos-lite/src/mm.c b/nanos-lite/src/mm.c
index c626aa8afd28d20a95629a25f1222146d274b1c9..cbfa105a3d509d69fd2091c5b9b5a9c13a49c513 100755
--- a/nanos-lite/src/mm.c
+++ b/nanos-lite/src/mm.c
@@ -89,6 +89,6 @@ void init_mm() {
   Log("free physical pages starting from %p", first);
 
 #ifdef HAS_VME
-  vme_init(pg_alloc, free_page);
+  panic_on(!vme_init(pg_alloc, free_page), "VME initialization failed");
 #endif
 }
```

归档正向逐字节得到当前mm.c，反向逐字节恢复旧commit，mode核验保持；见local/archive-validation.json。

## 验证结果与限制（2026-10-20）

- host：编译实际mm.c/main.c、实际nanos/AM头与当前NPC选中的dummy VME实现；main只重命名为nanos_main。受控true回调还实际调用pg_alloc，检查一页清零及堆推进；后续device/irq/fs/proc/yield为顺序观测桩。旧版false三配置均错误进入五个后续步骤，精确FAIL/exit1；最终false/true在普通、ASan+UBSan、NDEBUG三配置全部PASS/exit0（24条最终编译/运行命令符合预期）。false检查调用恰一次、零后续步骤、堆不变；true仍正常到yield。此为host受控环境，不代替真实guest。
- 真实RV64失败：实际mm.c/main.c与NPC Make所选的platform/dummy/vme.c配对，在NEMU上执行；仅后续初始化由标记桩替代，旧版到init_device输出REACHED并halt(42)，新版及NDEBUG在init_mm输出`AM Panic: VME initialization failed`并halt(1)，绝不出现后续标记。NEMU三例均exit1/HIT BAD TRAP属于预期负例，靠具体诊断区分，不能仅凭非零当通过。最终三例使用与标准消费者相同的本次源码重建执行器SHA256 `3185d124de279635b0d23c857032bdda6d3ea226eacc10c60e98cc9806903fc0`；标准make重建前的预装引擎结果另存initial-engine，不混作最终同版身份。
- 成功消费者：隔离沿既有`make ARCH=riscv64-nemu update`（25.926秒，exit0）→`run`，原NEMU真VME分页/装载/调度。三前台八帧实际查看（合图及PAL/终端原分辨率PNG）：PAL初始绘制、返回及Enter后标题画面继续变化；nterm输入qzx，显示command not found并回prompt；slides 0→1→0且返回像素SHA完全一致。十个SDL按键实际进入队列，hello41→181逐阶段递增；54.052秒后自有组SIGTERM/make -15，非guest正常退出。108个extent与已安装文件逐字节匹配，四个应用链接ELF与安装身份一致，尾部仅512B对齐填零。
- 157项preclean全部通过，9347份输入/产物身份固定；三目标/标准mm.c与生产相同SHA，完整正文diff正反字节一致，五项正式配置/引擎/盘/header/内核bin保持entry身份，根HEAD e7a3e26/index空。实际命令/退出/环境/中间与最终结果见local各JSON/log。

夹具问题：首次host编译遇ccache只读，改为显式CCACHE_DISABLE=1；首次RV目标把libc include放在nanos include之前，误选libc memory.h而编译失败，修正夹具include优先级后再验，初始失败日志/结果保留initial-header-order。归档初验临时文件默认mode644产生告警，临时旧文件改用实际755后重做正反通过；生产mode不变。终检曾错误要求安静make日志打印-DNDEBUG，改核实际目标Makefile的CFLAGS及确实重编mm.c的CC日志；未改验收语义或生产代码。

范围/未测：真实失败在NEMU硬件执行链上运行NPC选源的dummy，**不是NPC整机nanos启动成功**；不实现NPC VME，不消除F0031/F0071内存预算或F0072启动复制问题，本轮未运行NPC完整链接/启动。CPU-tests/RT不消费nanos init_mm，不重跑；AM分配器本身未改，不重复F0089页表/OOM矩阵。成功正常真页表路径已由标准三前台覆盖。非VME分支仅按既有ifdef静态核对，未动态运行；其他ISA/完整Linux/长期/实体音视频未测。失败停止不保证AM部分初始化回滚；没有修改分配/错误ABI。无安装/下载/公开Make流程改动；本组源码和测试配方尚未提交。

## 复现与结束节点

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0070/local/host.py
python3 npc/verif/records/process/code_correctness_review/crp-f0070/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0070/local/real-failure.py
python3 npc/verif/records/process/code_correctness_review/crp-f0070/local/standard-path/run-standard.py nanos
# 标准run重建执行器后，复跑real-failure以固定与标准同一引擎身份
python3 npc/verif/records/process/code_correctness_review/crp-f0070/local/real-failure.py
```

使用本地现有资源，无下载/安装。准备脚本拒绝覆盖已有work，恢复时先核现状；清理后须按配方重建。archive.py/check.py是当次归档/身份核验配方，结果不以再跑覆写原历史；旧源由e7a3e2610b32de736e2e9f706b91aa317a1c5e23重建。一次性夹具不提交，报告/必要源码和局部ignore入库；local/.agent不由commit备份。F0070完成后等待结果确认/commit，唯一后续TASK_QUEUE#crp-next；不自动提交/下一组/M2。

## 清理与完成

F0070 Completed，结果确认/本组commit Pending；98完全已修/21未修完，前97已确认提交e7a3e2610b32de736e2e9f706b91aa317a1c5e23。本组生产仅mm.c一行替换，Working tree contains uncommitted F0070 code/documentation changes，index空；无push/安装/运行中任务。

验证/八帧查看/完整diff正反及157preclean完成后，删除9401文件/链接、357915628逻辑字节/385843200分配字节，0 tracked/正式资产删除；隔离源码/模型/盘/ELF/对象/截图及接触图均已清理，不声称原图/模型仍可直接使用。保留最小配方、命令/日志/配置、9347历史身份、patch/归档与cleanup-plan/receipt解释预期缺失。正式五资产未改。

下一单元/门槛只见TASK_QUEUE#crp-next，等待结果确认/commit及后续执行授权，不自动提交或开始F0032/M2。会话建议：可在当前对话继续；本轮修改单一、恢复入口完整，下一项仍围绕VME初始化。

最终终检补充：30项PASS、69份保留证据身份，实际生产patch/五正式资产/9401项预期清理/119行98与21计数及唯一下一入口一致。无新增动态测试/commit；F0070 Completed，结果确认/commit Pending，当前停止。

## 用户确认与提交收尾（2026-10-20）

用户“提交后继续”确认本组已报告范围和限制，授权精确提交后执行TASK_QUEUE唯一入口F0032一个单元。提交前69保留证据身份/完整patch/正式资产与30项终检复核一致，复用动态验收，不重复Completion。实际commit/路径/blob核验见local/submit-receipt及.agent；无push。可在当前对话继续：下一项同属VME，入口与验收边界完整。
