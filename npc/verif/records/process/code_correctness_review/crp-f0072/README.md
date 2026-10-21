# CRP F0072 — 内嵌 ramdisk 纳入 NPC 启动复制范围

## 整体计划与启动（2026-10-21）

用户“继续CRP修复”授权唯一 TASK_QUEUE#crp-next 的 F0072 一个单元。Guard：前 F0047 Completed / 已确认 / 实际提交 aa13b0493cdf80b4a3f10a39f806f36fcd2923eb，根 working tree/index 干净；M2 保持规划状态。复用 CRP 总体计划及 workflow，不恢复旧连续提交授权。

目标/范围：修复 nanos resources.S 内嵌 ramdisk 的孤儿节脱离 NPC 数据复制范围。拟将其声明为可写 `.data.ramdisk` 输入节，使现有七链接脚本的 `*(.data*)` 与 `_sdata.._edata`、flash LMA 边界覆盖它；保持 incbin 字节、首尾符号、可写属性、公开 Make 流程和启动程序不变。不扩大完整 ramdisk 容量，不实现 NPC VME，不处理 F0031/F0071。

本组一个阶段：固定当前源码/正式资产身份 → 原 resources.S 小盘反例及各模式边界 → 最小修改 → 七模式空/8字节/跨页小盘的链接与真实 NPC 启动、逐字节/可写验证 → 完整 diff 正反应用核验、记录/索引/状态与可再生产物清理。

交付：生产单文件修改、本报告（内嵌完整 diff/语句说明）、必要配方/实际命令日志/退出码/身份/清理回执与唯一下一入口。定向验证使用实际资源汇编、链接脚本和启动链，复制阶段检查早于搬运模式 TRM 二次 loader，避免掩盖漏复制；同时在正常 TRM/main 路径消费小盘。生产资源仅 NPC 内嵌分支变更，NEMU/RT/CPU 未消费该分支，按影响不重跑无关消费者。

验收：旧非空盘出现精确未复制失败；最终各可容纳布局的首尾均在数据复制区内、LMA 在 flash/bin 内，磁盘字节逐一相同并可写，BSS/前后数据不破坏，空盘保持空范围；容量超限明确拒绝，不能把小夹具当完整 nanos/NPC 已运行。若出现新能力/容量布局策略未决，先分析后最少裁决；软件安装/系统改动停下。验证完成、留档及清理后停止，等用户确认/commit，不自动提交/push/下一单元/M2。


## 用户补充的存储边界

用户2026-10-21明确指出：“ramdisk在NPC中目前没有物理存储区域存放，flash大小是不够的”。本轮据此明确验收含义：正式盘现为149,021,696字节（约142.12 MiB），flash仅16 MiB，完整盘没有本轮可用的装载布局；不是改节名就获得存储容量。F0071保持未修，F0031/VME亦保持独立未决。本轮未裁盘、未改boot配置、未扩flash/RAM或增加物理设备，也没有生成/运行完整NPC nanos镜像。

## 实施结果 — Completed，结果确认/本组commit Pending

生产仅 `nanos-lite/src/resources.S` 2增1删：将可写输入节改为`.data.ramdisk`。七链接脚本已有`*(.data*)`，因此incbin内容进入`.data`输出节，并在`_edata`设置前占据空间；`ramdisk_start/end`仍精确包围原磁盘字节。`_sidata`提供flash源，`_sdata.._edata`提供目标：XIP的TRM loader、单级boot_loader和SSBL原有数据搬运都覆盖它，BSS清零范围随后开始，不覆盖盘。`"aw"`使运行地址仍可写，磁盘写回不改成flash写入；未引入额外复制阶段、接口或Make步骤。

| 验收 | 本次实际结果 / local证据 |
|---|---|
| 同版执行器 | 从当前aa13b04源码隔离重建NPC（DIFF=1/PERF=1/PERF_R45=1/无trace/SDL）及REF，构建exit0；REF ABI 33字/选择复制/哨兵/5域/exec通过。engine-build.json、engines.json、ref-abi.log |
| 原版精确见证 | 七布局×空/8/4109字节，共21次真实NPC；7个空盘GOOD控制、14个非空盘均在检查复制内容处BAD code72，且符号位于数据复制范围外。入口先把实际盘范围填0xa5并读回，排除偶然RAM初值；before/results及commands/guest日志 |
| 修复后七布局 | xip/sram/psram/psram-ssbl/sdram/sdram-rt/sdram-heap各3例，**21/21 GOOD TRAP，全部difftest ON**；逐字节检查、全盘异或写入/读回/恢复、data邻接值与BSS清零均通过。空盘首尾相同；静态均在`_sdata.._edata`内，flash/bin对应字节相同，输出.data具有ALLOC/LOAD/DATA可写属性，无.ramdisk孤儿节。after/results与每例sections/segments/symbols |
| 正常AM及nanos disk消费 | 使用完整当前AM/klib、原始启动入口、实际NPC IOE absent-disk配置与生产nanos disk.c，标准`make ARCH=riscv64-npc BOOT_MODE=… image`；xip空/8字节、psram-ssbl及sdram各4109字节，**4/4 GOOD/difftest ON**。真实disk_size、逐字节分块disk_read、末端disk_write/读回/恢复及越界0通过，非host模拟，不使用prefill/重命名入口。consumer-final-results及构建/运行日志 |
| 容量保护 | 生成16 MiB+1稀疏小盘输入（独立于正式盘），实际资源汇编后七脚本链接均非零并报告flash装不下；**7/7拒绝**，部分布局同时报告目标RAM超限。未静默切模式、裁盘或扩大硬件。capacity-results及capacity/*.log |
| 非内嵌分支 | 原/新resources.S在相同cwd/输入、不定义KERNEL_EMBED_RAMDISK交叉编译，两个.o逐字节完全一致。NEMU资源分支不变；noembed-results |
| 判据与身份 | **87项preclean全PASS**，含8种消费者判据故障拒绝、七布局范围/属性/栈安全、HEAD与8正式资产保持、其余入口AM源码不变及执行器身份；validation-preclean、entry、archive-validation |

搬运模式的定向检查在boot/SSBL之后、TRM二次loader之前，避免二次复制掩盖错误；xip/sdram-heap由TRM loader负责数据初始化。定向probe只将生产_start/原_trm_init重命名以插检查，未改生产加载代码；正常AM消费者则完全使用原入口和真实库。两类证据的边界分开记录。

正常sdram消费者初次runner将交错的`BASE R: addr=… data=… last=…`硬件调试行误算为PASS打印缺失，结果原始good=false；实际guest已GOOD、无分歧。保留consumer-results-before-log-normalization与原始日志，只去除精确匹配该格式的调试记录后还原UART打印，4/4通过，未修改生产日志/源码或重跑伪造结果。8种BAD/ABORT/空日志/非零/预算耗尽/缺marker/重复终态/diff关闭判据负例均拒绝。原probe的difftest字段最初使用错误字符串匹配，已依据原日志`difftest: ON`修正，不影响原始动态执行或终态结论。

本次依CRP要求尝试读取ICS-PA3.1参考页（https://ysyx.oscc.cc/docs/ics-pa/3.1.html），两次fetch timeout，未从不可读取内容推导契约；结论依据本地实际七脚本与启动链。

## 完整源码diff与版本身份

仓库为根ysyx-workbench，路径相对根；旧版本`aa13b0493cdf80b4a3f10a39f806f36fcd2923eb`，旧源码SHA256 `fc0d99788116c3cb47999c99eed563eaf8ba6232e5c0d3076bad754ce2dab31c`。新版本为**WORKTREE（2026-10-21，尚未提交）**，SHA256 `7c5b146f08390f3f7c8512050a4c580348c1033aa1382cebe6db5776cab3ab3e`。下面是本批全部生产差异，没有新增其他文件/模式或更换incbin输入。正向应用逐字节等于新源、反向恢复旧源，两方向exit0；archive-validation.json与repair.patch固定核验事实。

```diff
diff --git a/nanos-lite/src/resources.S b/nanos-lite/src/resources.S
index 6b790f41bf994ffaa6bb6e84d406142187d0bb31..904d5e2a13a4cf5b508077ae624602fb2514e4af 100755
--- a/nanos-lite/src/resources.S
+++ b/nanos-lite/src/resources.S
@@ -7,7 +7,8 @@ logo:
 #ifdef KERNEL_EMBED_RAMDISK
 // Embedded fsimg for platforms without a disk device (NPC SoC).
 // The section is kept writable so that game save data works in-memory.
-.section .ramdisk,"aw"
+// Use the initialized data family so every NPC boot path copies it from flash.
+.section .data.ramdisk,"aw"
 .globl ramdisk_start, ramdisk_end
 ramdisk_start:
 .incbin "build/ramdisk.img"
```

## 影响、限制与恢复

本批关闭F0072的资源节加载归属错误，不关闭完整盘/PCB/栈预算F0071，也不关闭NPC VME/MPE F0031、权限CQ或其他未修能力。未验收完整NPC nanos、完整Navy盘、所有ISA/外部自定义linker、长期/GUI/声音/物理硬件。CPU-tests与RT不链接此nanos资源，NEMU分支已证明对象相同，故不重跑其全集或nanos三前台/hello；小盘真实disk消费者证明受影响的嵌入后端，不能扩大成完整OS可用声明。

复现先从旧完整commit取resources.S（git show），AM/NPC/REF依本轮HEAD；原/新源的差异用本报告或local/repair.patch应用。保留local/build-engine.py、directed.py、probe.c、consumer.py/consumer.c、capacity.py/check.py/archive.py、实际命令/cwd/环境/退出码/日志/配置/身份。原盘用`bytes((i*37+11)&255 for i in range(n))`生成，n=0/8/4109；容量盘生成16MiB+1稀疏零输入。old/new在同一执行器/REF和各自固定资源汇编上执行；先运行directed.py before，再应用补丁运行after；使用新输出目录避免覆盖历史结果。标准消费者是隔离的小AM程序，未声称执行完整nanos Make update/run。

正式盘、NEMU配置/模型/内核、RT产物及配置八资产保持entry SHA，未覆盖或删除。验证产物在归档/身份固定且进程结束后按workflow清理，精确回执后附。local/.agent仍本地忽略，普通commit不等于其备份；旧源码可由Git及本报告补丁重建，模型/ELF需重建。本组留档后停止，等待结果确认与commit，不自动提交/push/下一单元/M2。唯一未来入口为TASK_QUEUE#crp-next。


## 清理与最终状态（2026-10-21）

归档/87项preclean通过、943份清理前文件/链接身份固定，确认无运行中的夹具后，删除572个可再生文件/链接，171,104,479逻辑字节/155,926,528分配字节；包括隔离模型/AM生产副本、对象/ELF/bin、小盘输入与源副本，不跟随指向正式ysyxSoC/verif/playground的链接。零tracked/正式资产删除，8正式资产SHA保持。cleanup-plan/receipt保存删除前身份与预期缺失；保留实际日志/脚本/配置/JSON/完整补丁与正文，不宣称已删模型仍可复用。

F0072 **Completed**，累计101完全已修/18未修完，前100已确认提交aa13b04；本组结果确认/commit Pending，Working tree contains uncommitted F0072 code/documentation changes。M2不变。CURRENT_STATE/TASK_QUEUE、修复镜像、REPAIR_AND_REGRESSION、process及DOCUMENT_INDEX同步，完整历史审阅记录不改写。本轮按单元停点停止，无commit/push/下一组。

最终一致性终检：969项检查PASS（包括943个清理前身份的保留/预期删除逐项核对），371份原始证据身份仍保留；完整内嵌diff与实际源码一致，8正式资产、101/18计数及唯一入口一致。正文新文件及tracked diff空白检查无告警。final-validation.json/retained-identities.json保存事实；此处数量是静态与身份核对数，不另算969个动态测试。复用本次Completion，不新增快照或运行。

## 2026-10-21 后续范围裁决补充

用户进一步明确F0071/F0031均为NPC能力扩展，交由Linux启动主线根据需求与ysyxSoC框架修改，CRP不处理此类扩展。当前处置见[修复计划](../REPAIR_AND_REGRESSION.md#npc-capability-scope-20261021)。上文“未修/未决、101已修18未修完”保留为本组原交付截面；当前总表为101已修+16 CRP待修+2扩展移交，移交两项未实施、不算已修。本组F0072小镜像复制修复及容量事实保持，结果确认/commit仍Pending；本次仅文档范围承接，未新增动态测试或生产修改。此前manifest文档身份变化由本附记解释，不改写旧证据。

范围维护验证：32项静态检查通过、17条范围链接有效，119行对账101+16+2一致；F0072生产patch及8正式资产保持。仅文档调整，未重跑动态测试、未commit/push；F0072结果确认/commit门槛保持。


<a id="submit-20261021"></a>
## 2026-10-21 用户确认与提交收尾

用户“提交”确认本批已报告F0072修复/验证限制及F0031/F0071能力扩展移交范围，并授权提交本批可归属改动；不授权push或开始F0086。复用既有Completion、动态验收和清理结果，仅作提交前身份/范围/空白检查：11项PASS，377份本地验收证据保持，范围维护32检查及其文档身份、实际生产patch/正文diff、8正式资产及572项清理状态保持。

本批根仓提交范围为resources.S、process索引、repair-status、workflow范围规则及本报告/.gitignore六路径；一次性local测试源/日志/JSON不入库。完整提交身份由包含本节与本批生产diff的Git commit定位，精确暂存和实际提交回执保留local/submit-staged.json、submit-receipt.json。修复后的resources.S SHA与上文已验收WORKTREE身份相同；提交不会改变技术验收范围。

REPAIR_AND_REGRESSION、FINAL_FINDINGS/LIMITATIONS补充、LINUX_PLAN能力接收范围及.agent等既有忽略资料沿用本地持久化约定，不强行更改跟踪规则；本次commit不代表这些资产已备份。提交成功后停止，101已修均获本轮或此前确认，另16 CRP待修+2 Linux能力扩展移交；唯一未来入口仍TASK_QUEUE#crp-next，F0086未Start。

会话建议：可在当前对话继续。本组修复、范围裁决及下一入口均已完整落档，当前恢复信息清楚；后续执行仍须新的“继续”授权。
