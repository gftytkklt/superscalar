# CRP F0025 / F0027 / F0028 — NPC启动布局修复

2026-10-18。用户“继续CRP修复”授权TASK_QUEUE唯一下一入口一个自适应组；F0024已确认提交fc7835e，Start前根工作树/index干净，M2保持。本组不复用旧连续commit预授权。

## 本组计划与完成范围

**三项Completed；本组结果用户确认/修复commit Pending。** 既有整体计划与[CRP执行规则](../workflow/README.md)承接，一个阶段逐项反例/修复/定向验证、组合真实回归及留档后停止。目标/验收：七NPC链接模式低/高/混合对齐与空节、真实启动前BSS哨兵及逐节字节核对；四可调heap模式0/恰容量/+1/回绕/负值链接；CPU全集及RT四应用update/image/真实NPC到msh。生产只改七链接脚本、boot_sram.c和ssbl.c；交付本报告/局部ignore/local原始证据、索引/状态。不改业务RTL，不安装，不改变BOOT_MODE/LDS/BOOT_S/HEAP_SIZE和日常构建流程，不自动commit/push/下一组。

参考：2026-10-18读取[ICS-PA2.3 程序、运行时环境与AM](https://ysyx.oscc.cc/docs/ics-pa/2.3.html)运行时加载/AM平台分工，以本项目NPC加载链及硬件容量为具体契约。原P4分类/证据不改写；F0026栈预算、五CQ、F0040Partial保持。

| 问题 | 最终修改 | 本次证据 |
|---|---|---|
| F0025 BSS前缀 | 七脚本输出.bss本身ALIGN(8)，_bss_start取当前位置；符号覆盖实际完整节 | 原xip/sram/sdram-heap低对齐各BAD TRAP code1，prefill直接遍历实际ADDR/SIZEOF(.bss)写0xa5并读回；最终七模式BSS从起点到末端全部为0，首尾符号与实际节边界相同 |
| F0027 段搬运 | 五搬运脚本提供text/rodata各自LMA/VMA/end；boot_sram/SSBL分别精确拷贝两节，保留data独立搬运/fence.i/TRM入口 | 原五模式高对齐均BAD TRAP code3；最终每个搬运模式跳入已复制代码后、TRM二次loader前逐字节比较text/rodata/data的VMA与各自LMA，随后正常TRM/main退出。空rodata/data及空BSS、text32/rodata128/data16混合对齐通过 |
| F0028 heap容量 | xip/sram声明实际4MiB PSRAM MEMORY并用ORIGIN；四可调布局ASSERT start不超region尾、size不超剩余容量后才加法。SDRAM以128MiB硬件容量为准，修正旧16MiB注释 | 原四布局12种非法配置全部link0；最终0/恰剩余容量8种合法link0，容量+1/64位回绕/负值12种link非零并诊断heap size exceeds。默认HEAP_SIZE及接口不变 |

## 最终同版验证

| 验收 | 真实结果 / local入口 |
|---|---|
| 原版精确反例与控制 | before-current：21次真实NPC，3个BSS漏清+5个rodata错位精确失败，其余13个合法控制GOOD TRAP；不是host替代 |
| 最终七模式矩阵 | current/21 + edge-current/14 = **35/35 GOOD TRAP**，每次difftest ON且无分歧/预算耗尽。七模式是xip/sram/psram/psram-ssbl/sdram/sdram-rt/sdram-heap；低对齐、高64对齐、空rodata/data、混合32/128/16对齐、空BSS各一组；text非空是执行入口所必需 |
| heap边界 | current/heap.json **20/20**，8个合法/12个非法，基线相同对象及参数12个非法未拒绝 |
| CPU真实全集 | cpu-current/及cpu-current-results.json：当前NPC执行器、新生成riscv64-npc镜像、当前REF，**36 PASS + wrong 1 XFAIL**，37次exit0/difftest ON，无分歧/超时；正常NPC终态与预期BAD code1分别核验 |
| RT生成及真实执行 | 当前源四应用make -j1 ARCH=riscv64-npc git_commit= update与image成功；同一新镜像/当前执行器/REF **153.72秒到msh，difftest ON，无分歧**。观察后对自有进程组SIGTERM，实际exit=-15，不是guest正常退出。rt-current-run.log/rt-current-result.json |
| 判据及终检 | CPU分类10个故障负例、guest判据7个负例均拒绝；validation.json **18/18**。源码与消费者隔离副本相同，Make接口无变化；identity.json/repair.patch/tools.json及evidence-manifest.json保存身份/命令与必要产物，文件清单数量不等于测试数量 |

真实NPC探针以flash前置入口预填实际BSS并读回，再跳生产start；只重命名生产_start为production_start以插入探针。搬运模式检查点在生产boot/SSBL之后、生产TRM loader之前，避免二次清零掩盖boot错误；xip先调用生产loader再检查。最终常规消费者使用原始AM入口与真实klib，没有探针替换。空rodata/data探针允许TRM路径被gc而直接终止，静态符号确认两节size=0；其他正常路径进入真实TRM/main。

## 失败尝试与验收条件

第一次CPU make run返回2：现有汇总脚本把NPC和REF各自的终止日志一起计数，37项被记ERROR。保留cpu-npc.log/consumers-builds.json；按NPC数字前缀终态与每项make退出码重判36PASS+1XFAIL，后续又用当前匹配执行器完整重跑37项同样通过。**不声称原始make run命令通过**；生产汇总脚本本组未改，列为TASK_QUEUE后续独立F0052补充验证入口。

初次RT使用根npc/build/ysyxSoCFull（旧二进制）在ienabled读mstatus处MPP差0x1800触发DIFF ABORT，exit0仍判失败。该MRET问题此前F0046已修，根旧执行器没有包含修复；本次不改RTL、不重建/覆盖根模型。最终复制F0014已验收NPC执行器为local/npc-tested，SHA256 `1ced513005f8e30df4d1b9b7ebcd7f2be9290dcae32304ef3f4cf971a582f208`，核对原consumer-fixture和194d2c0到当前HEAD的npc/csrc、vsrc、ysyxSoC、Makefile无源码差异。executor.json保存来源及根旧SHA。用此执行器重跑原版21、最终35、CPU37和RT；最终身份来自这轮，旧执行器结果不混作最终组合验收。

开发中保留：首次编译ccache只读失败（启用已有CCACHE_DISABLE后恢复）；初判据误计REF附加GOOD而出现假失败（修正为NPC锚定行）；中间绝对size符号转地址使编译器错误假定非零，空rodata拷贝跑到SIM_END。最终改为两个真实节首尾地址的uintptr_t差值，空节已真实通过。该中间runner未结束时更新链接符号，后续出现旧对象/新脚本未定义符号而停止；其after/为明确未通过的中间尝试，未计验收。后续所有最终构建输入固定后才执行/观察，不运行中改写模型或源。

## 复现、影响与持久化

- local/directed.py before-current/current/edge-current、consumers.py、cpu-current.py、rt-current.py、verify.py保存命令配方，各commands.json记录实际argv/log/exit。已有目录不能覆盖；复现须新目录并保持before/current/edge前缀或定向调整输出名称。before-src及final-src保存相关源码；identity.json记录工具/源/镜像/模型身份。
- 复用现有NPC与REF，无安装。AM完整小源码副本、四应用及CPU源、RT小BSP独立build；RT公共源以链接引用当前树，外部引用不是本地字节备份。构建不改原RT/NPC配置，默认根旧NPC模型仍未更新；后续必须按executor.json使用匹配执行器。
- 本组只改NPC启动链，NEMU TRM/CTE/VME/链接脚本、Navy及nanos NEMU闭包不变，故nanos三前台/hello不重跑；没有把CPU/RT结果扩写为nanos/NPC可运行。NPC nanos的孤立ramdisk F0072仍独立未修，不在本组扩展孤立节加载规则。
- 自定义LDS若使用生产boot_sram/SSBL，需与新增节边界符号契约配套；本仓五搬运脚本已同步。未验证任意外部自定义脚本、RV32/RVE、所有AM应用、长时调度、GUI/音频或Linux。heap0测试只验证允许空Area的链接，不承诺应用可在零堆下正常运行；恰容量验证链接边界，不扫描整片内存。
- F0026固定栈预算未修，本组未预留或改变栈策略；五CQ/F0040并发/PAL性能/F0043/两缺源保持。原始测试源/脚本/日志/ELF/bin/模型/输入副本仅local保存，本批不提交一次性测试代码/生成资产；普通commit不等于ignored证据和.agent已备份。

累计**34项修复Completed（31已确认提交，本组三项待确认提交）/85未修完**，含5CQ/F0040Partial。报告/records索引/逐项镜像/状态已承接，历史P4不回写。当前HEADfc7835e，Working tree contains uncommitted CRP repair/documentation changes，index空，无运行中动作；本组留档后停止，等用户确认/commit。下一组仅沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动推进M2/commit/push。

<a id="approval-submit-20261018"></a>
## 用户确认及本轮提交授权（2026-10-18）

用户“提交，继续修改”确认已报告的三项修复、模型版本解释及验收限制，授权提交本组后按唯一入口执行F0052 CPU汇总补充一个单元。681条必要文件清单/最终生产源码无漂移，复用18项验收，不重复测试/Completion。实际提交回执见local/submit-receipt.json及.agent；本组授权不自动覆盖下一单元的结果提交，不push、不推进M2。
