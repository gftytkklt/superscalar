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


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0025/F0027/F0028 — 根仓库

F0025/F0027/F0028 分别对应 BSS 起点、分节加载和堆容量；下列九个文件为本批完整生产修复。

- 差异路径相对于仓库 `.`；旧版本：`fc7835ed53caf187d38c8937e9fb4ca82c697d3c`；新版本：`f3a5d0cf8c2b85c047981fb50ec9a871969c9dbd`。

#### `abstract-machine/am/src/riscv/npc/boot_sram.c`

F0027：声明 text/rodata 各自的 LMA、VMA 和 end；分别按 `(uintptr_t)end - (uintptr_t)vma` 拷贝，替代假定两节 VMA/LMA 间隙相同的合并搬运。独立节允许不同对齐及空节长度零，data 原搬运保持；对应链接脚本提供同名边界。

```diff
diff --git a/abstract-machine/am/src/riscv/npc/boot_sram.c b/abstract-machine/am/src/riscv/npc/boot_sram.c
index 688f4f47ae6db51058c16c3afbc9fb32115a505f..e41a8b0282d432db377a5c2c1251b4a540ed894d 100644
--- a/abstract-machine/am/src/riscv/npc/boot_sram.c
+++ b/abstract-machine/am/src/riscv/npc/boot_sram.c
@@ -26,21 +26,20 @@ static void copy_bytes(char *dst, const char *src, size_t n) {
 }
 
 // 由 linker 提供：LMA(flash) / VMA(目标区) 边界。
-extern char _text_lma[], _text_vma[], _sidata[], _sdata[], _edata[];
+extern char _text_lma[], _text_vma[], _text_end[];
+extern char _rodata_lma[], _rodata_vma[], _rodata_end[];
+extern char _sidata[], _sdata[], _edata[];
 extern char _bss_start[], _bss_end[];
 extern void _trm_init();
 
 __attribute__((section(".bootloader")))
 void _boot_loader() {
-  char *dst, *src;
+  char *dst;
   long n;
 
-  // 搬 .text+.rodata: flash[_text_lma .. _sidata) -> VMA[_text_vma .. _sdata)
-  // 注意 LMA 与 VMA 区间长度一致（链接器保证段连续）。
-  src = _text_lma;
-  dst = _text_vma;
-  n   = _sdata - _text_vma;
-  if (n > 0) copy_bytes(dst, src, (size_t)n);
+  // Each output section can have a different LMA/VMA alignment gap.
+  copy_bytes(_text_vma, _text_lma, (uintptr_t)_text_end - (uintptr_t)_text_vma);
+  copy_bytes(_rodata_vma, _rodata_lma, (uintptr_t)_rodata_end - (uintptr_t)_rodata_vma);
 
   // 搬 .data: flash[_sidata .. +len) -> VMA[_sdata .. _edata)
   n = _edata - _sdata;
```

#### `abstract-machine/am/src/riscv/npc/ssbl.c`

F0027：声明 text/rodata 各自的 LMA、VMA 和 end；分别按 `(uintptr_t)end - (uintptr_t)vma` 拷贝，替代假定两节 VMA/LMA 间隙相同的合并搬运。独立节允许不同对齐及空节长度零，data 原搬运保持；对应链接脚本提供同名边界。

```diff
diff --git a/abstract-machine/am/src/riscv/npc/ssbl.c b/abstract-machine/am/src/riscv/npc/ssbl.c
index 906aa2520aeb0105c6bafe10a74b1375b751c88c..055178b6e4efaf88b08ada9d63ba34c06e2678c9 100644
--- a/abstract-machine/am/src/riscv/npc/ssbl.c
+++ b/abstract-machine/am/src/riscv/npc/ssbl.c
@@ -18,20 +18,20 @@ static void ssbl_copy_bytes(char *dst, const char *src, size_t n) {
 }
 
 // 由 linker 提供：主程序 LMA(flash) / VMA(PSRAM) 边界。
-extern char _text_lma[], _text_vma[], _sidata[], _sdata[], _edata[];
+extern char _text_lma[], _text_vma[], _text_end[];
+extern char _rodata_lma[], _rodata_vma[], _rodata_end[];
+extern char _sidata[], _sdata[], _edata[];
 extern char _bss_start[], _bss_end[];
 extern void _trm_init();
 
 __attribute__((section(".ssbl")))
 void _ssbl_entry() {
-  char *dst, *src;
+  char *dst;
   long n;
 
-  // 搬 .text+.rodata: flash[_text_lma .. _sidata) -> VMA[_text_vma .. _sdata)
-  src = _text_lma;
-  dst = _text_vma;
-  n   = _sdata - _text_vma;
-  if (n > 0) ssbl_copy_bytes(dst, src, (size_t)n);
+  // Each output section can have a different LMA/VMA alignment gap.
+  ssbl_copy_bytes(_text_vma, _text_lma, (uintptr_t)_text_end - (uintptr_t)_text_vma);
+  ssbl_copy_bytes(_rodata_vma, _rodata_lma, (uintptr_t)_rodata_end - (uintptr_t)_rodata_vma);
 
   // 搬 .data: flash[_sidata .. +len) -> VMA[_sdata .. _edata)
   n = _edata - _sdata;
```

#### `abstract-machine/scripts/linker-psram-ssbl.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0027：新增 `_text_end` 及 `_rodata_vma/_lma/_end`，由 ADDR/LOADADDR/SIZEOF 明确每节源/目标范围，供 boot/SSBL 独立搬运。

```diff
diff --git a/abstract-machine/scripts/linker-psram-ssbl.ld b/abstract-machine/scripts/linker-psram-ssbl.ld
index 7bbac9099aa1f826e9e6984e72cad19f39e7a95a..e6f36f982f232a2a380078ad2129bc57875f335e 100644
--- a/abstract-machine/scripts/linker-psram-ssbl.ld
+++ b/abstract-machine/scripts/linker-psram-ssbl.ld
@@ -42,12 +42,16 @@ SECTIONS {
   } > psram AT> flash
   _text_vma = ADDR(.text);
   _text_lma = LOADADDR(.text);
+  _text_end = ADDR(.text) + SIZEOF(.text);
   etext = .;
   _etext = .;
   .rodata : ALIGN(0x8) {
     *(.rodata*)
     *(.srodata*)
   } > psram AT> flash
+  _rodata_vma = ADDR(.rodata);
+  _rodata_lma = LOADADDR(.rodata);
+  _rodata_end = ADDR(.rodata) + SIZEOF(.rodata);
   .data : ALIGN(0x8) {
     _sdata = .;
     *(.data*)
@@ -82,8 +86,8 @@ SECTIONS {
   } > psram AT> flash
   _sidata = LOADADDR(.data);
   _sidata_end = LOADADDR(.data) + SIZEOF(.data);
-  .bss : {
-    _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+    _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
```

#### `abstract-machine/scripts/linker-psram.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0027：新增 `_text_end` 及 `_rodata_vma/_lma/_end`，由 ADDR/LOADADDR/SIZEOF 明确每节源/目标范围，供 boot/SSBL 独立搬运。

```diff
diff --git a/abstract-machine/scripts/linker-psram.ld b/abstract-machine/scripts/linker-psram.ld
index 800ee944a0e0f06b08c78bc4b4eae30f5b50f489..366a0db6cd1f87b047a7033fccc25c791a633104 100644
--- a/abstract-machine/scripts/linker-psram.ld
+++ b/abstract-machine/scripts/linker-psram.ld
@@ -27,12 +27,16 @@ SECTIONS {
   } > psram AT> flash
   _text_vma = ADDR(.text);
   _text_lma = LOADADDR(.text);
+  _text_end = ADDR(.text) + SIZEOF(.text);
   etext = .;
   _etext = .;
   .rodata : ALIGN(0x8) {
     *(.rodata*)
     *(.srodata*)
   } > psram AT> flash
+  _rodata_vma = ADDR(.rodata);
+  _rodata_lma = LOADADDR(.rodata);
+  _rodata_end = ADDR(.rodata) + SIZEOF(.rodata);
   .data : ALIGN(0x8) {
     _sdata = .;
     *(.data*)
@@ -61,8 +65,8 @@ SECTIONS {
   } > psram AT> flash
   _sidata = LOADADDR(.data);
   _sidata_end = LOADADDR(.data) + SIZEOF(.data);
-  .bss : {
-    _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+    _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
```

#### `abstract-machine/scripts/linker-sdram-heap.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0028：先 ASSERT 堆起点不超过 region 尾，再以 `_heap_size <= region_end - _heap_start` 校验剩余容量，最后才求 heap_end，避免加法回绕放行越界。 堆起点取 ORIGIN(sdram)，旧注释的 16MB 改为实际 128MB；没有扩大硬件。

```diff
diff --git a/abstract-machine/scripts/linker-sdram-heap.ld b/abstract-machine/scripts/linker-sdram-heap.ld
index 123662d259b10b9e86ac4508a9f6b31f09336a0f..77e1dec4234f83894556f89294893fef3b91c3dc 100644
--- a/abstract-machine/scripts/linker-sdram-heap.ld
+++ b/abstract-machine/scripts/linker-sdram-heap.ld
@@ -28,8 +28,8 @@ SECTIONS {
     *(.sdata*)
     _edata = .;
   } > sram AT> flash
-  .bss : {
-    _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+    _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
@@ -39,8 +39,11 @@ SECTIONS {
   _sidata_end = LOADADDR(.data) + SIZEOF(.data);
   _stack_pointer = _sram_start + _stack_offt;
   . = _stack_pointer;
-  /* 堆区：SDRAM（0xa0000000 起，可缓存 16MB），大小 = HEAP_SIZE（默认 32KB）。 */
-  _heap_start = 0xa0000000;
+  /* 堆区：SDRAM（0xa0000000 起，可缓存 128MB），大小 = HEAP_SIZE（默认 32KB）。 */
+  _heap_start = ORIGIN(sdram);
+  /* Check the size before addition so a wrapped end cannot pass the bound. */
+  ASSERT(_heap_start <= ORIGIN(sdram) + LENGTH(sdram), "heap start exceeds sdram")
+  ASSERT(_heap_size <= ORIGIN(sdram) + LENGTH(sdram) - _heap_start, "heap size exceeds sdram")
   _heap_end = _heap_start + _heap_size;
   end = .;
   _end = .;
```

#### `abstract-machine/scripts/linker-sdram-rt.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0027：新增 `_text_end` 及 `_rodata_vma/_lma/_end`，由 ADDR/LOADADDR/SIZEOF 明确每节源/目标范围，供 boot/SSBL 独立搬运。

```diff
diff --git a/abstract-machine/scripts/linker-sdram-rt.ld b/abstract-machine/scripts/linker-sdram-rt.ld
index d4f21a09589c1ed0b8cc828eb0a940ab717f530d..55ebccbe08062cc59dc659b9ee4d15f186a5b53b 100644
--- a/abstract-machine/scripts/linker-sdram-rt.ld
+++ b/abstract-machine/scripts/linker-sdram-rt.ld
@@ -28,12 +28,16 @@ SECTIONS {
   } > sdram AT> flash
   _text_vma = ADDR(.text);
   _text_lma = LOADADDR(.text);
+  _text_end = ADDR(.text) + SIZEOF(.text);
   etext = .;
   _etext = .;
   .rodata : ALIGN(0x8) {
     *(.rodata*)
     *(.srodata*)
   } > sdram AT> flash
+  _rodata_vma = ADDR(.rodata);
+  _rodata_lma = LOADADDR(.rodata);
+  _rodata_end = ADDR(.rodata) + SIZEOF(.rodata);
   .data : ALIGN(0x8) {
     _sdata = .;
     *(.data*)
@@ -65,8 +69,8 @@ SECTIONS {
   } > sdram AT> flash
   _sidata = LOADADDR(.data);
   _sidata_end = LOADADDR(.data) + SIZEOF(.data);
-  .bss : {
-    _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+    _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
```

#### `abstract-machine/scripts/linker-sdram.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0027：新增 `_text_end` 及 `_rodata_vma/_lma/_end`，由 ADDR/LOADADDR/SIZEOF 明确每节源/目标范围，供 boot/SSBL 独立搬运。 F0028：先 ASSERT 堆起点不超过 region 尾，再以 `_heap_size <= region_end - _heap_start` 校验剩余容量，最后才求 heap_end，避免加法回绕放行越界。

```diff
diff --git a/abstract-machine/scripts/linker-sdram.ld b/abstract-machine/scripts/linker-sdram.ld
index b7b37760987d9e6216ee9c6daa3fc5dc0c79d878..cccbac11b389961180525cb6b325ecf20864cbb3 100644
--- a/abstract-machine/scripts/linker-sdram.ld
+++ b/abstract-machine/scripts/linker-sdram.ld
@@ -27,12 +27,16 @@ SECTIONS {
   } > sdram AT> flash
   _text_vma = ADDR(.text);
   _text_lma = LOADADDR(.text);
+  _text_end = ADDR(.text) + SIZEOF(.text);
   etext = .;
   _etext = .;
   .rodata : ALIGN(0x8) {
     *(.rodata*)
     *(.srodata*)
   } > sdram AT> flash
+  _rodata_vma = ADDR(.rodata);
+  _rodata_lma = LOADADDR(.rodata);
+  _rodata_end = ADDR(.rodata) + SIZEOF(.rodata);
   .data : ALIGN(0x8) {
     _sdata = .;
     *(.data*)
@@ -59,8 +63,8 @@ SECTIONS {
   } > sdram AT> flash
   _sidata = LOADADDR(.data);
   _sidata_end = LOADADDR(.data) + SIZEOF(.data);
-  .bss : {
-    _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+    _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
@@ -74,6 +78,9 @@ SECTIONS {
    * 默认 32KB；mem-test 用小堆（如 HEAP_SIZE=0x1000=4KB）快速扫测。 */
   . = ALIGN(0x1000);
   _heap_start = .;
+  /* Check the size before addition so a wrapped end cannot pass the bound. */
+  ASSERT(_heap_start <= ORIGIN(sdram) + LENGTH(sdram), "heap start exceeds sdram")
+  ASSERT(_heap_size <= ORIGIN(sdram) + LENGTH(sdram) - _heap_start, "heap size exceeds sdram")
   _heap_end = _heap_start + _heap_size;
   end = .;
   _end = .;
```

#### `abstract-machine/scripts/linker-soc.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0028：先 ASSERT 堆起点不超过 region 尾，再以 `_heap_size <= region_end - _heap_start` 校验剩余容量，最后才求 heap_end，避免加法回绕放行越界。 声明 4MiB PSRAM region 并由 ORIGIN 取堆起点，与既有硬件范围一致。

```diff
diff --git a/abstract-machine/scripts/linker-soc.ld b/abstract-machine/scripts/linker-soc.ld
index 2d7849d5e67d2dace03ce7f9974849b75fbb2d15..2f2569f11824a48e986c6d1f76354ee592a1ce68 100755
--- a/abstract-machine/scripts/linker-soc.ld
+++ b/abstract-machine/scripts/linker-soc.ld
@@ -4,6 +4,7 @@ ENTRY(_start)
 MEMORY {
   mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
   sram (rw) : ORIGIN = 0x0f000000, LENGTH = 8K
+  psram (rw) : ORIGIN = 0x80000000, LENGTH = 4M
   flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
 }
 
@@ -31,8 +32,8 @@ SECTIONS {
   } > sram */
   /* _edata = .; */
   /* _data = .; */
-  .bss : {
-	  _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+	  _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
@@ -47,7 +48,10 @@ SECTIONS {
   /* 堆区分配在 PSRAM(0x80000000, 可缓存 4MB)。大小由 LDFLAGS --defsym=_heap_size 指定
    * （npc.mk 的 HEAP_SIZE，默认 32KB；microbench 等大堆程序传 HEAP_SIZE=0x400000）。
    * 不要写死整个 4MB，否则 mem-test(用 _heap_start~_heap_end) 会扫描 4MB 极慢。 */
-  _heap_start = 0x80000000;
+  _heap_start = ORIGIN(psram);
+  /* Check the size before addition so a wrapped end cannot pass the bound. */
+  ASSERT(_heap_start <= ORIGIN(psram) + LENGTH(psram), "heap start exceeds psram")
+  ASSERT(_heap_size <= ORIGIN(psram) + LENGTH(psram) - _heap_start, "heap size exceeds psram")
   _heap_end = _heap_start + _heap_size;
   end = .;
   _end = .;
```

#### `abstract-machine/scripts/linker-sram.ld`

F0025：`.bss : ALIGN(0x8)` 对齐输出节本身，`_bss_start = .` 取实际节起点，替代只把符号向上对齐而漏清节前缀。 F0027：新增 `_text_end` 及 `_rodata_vma/_lma/_end`，由 ADDR/LOADADDR/SIZEOF 明确每节源/目标范围，供 boot/SSBL 独立搬运。 F0028：先 ASSERT 堆起点不超过 region 尾，再以 `_heap_size <= region_end - _heap_start` 校验剩余容量，最后才求 heap_end，避免加法回绕放行越界。 声明 4MiB PSRAM region 并由 ORIGIN 取堆起点，与既有硬件范围一致。

```diff
diff --git a/abstract-machine/scripts/linker-sram.ld b/abstract-machine/scripts/linker-sram.ld
index 2109d7e318b8cd52defa37f09446862c77cf1124..98a7b6256ac6878f079c2f0d6ecd213dddbf5b4c 100644
--- a/abstract-machine/scripts/linker-sram.ld
+++ b/abstract-machine/scripts/linker-sram.ld
@@ -2,6 +2,7 @@ ENTRY(_start)
 
 MEMORY {
   sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
+  psram (rw) : ORIGIN = 0x80000000, LENGTH = 4M
   flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
 }
 
@@ -25,12 +26,16 @@ SECTIONS {
   } > sram AT> flash
   _text_vma = ADDR(.text);
   _text_lma = LOADADDR(.text);
+  _text_end = ADDR(.text) + SIZEOF(.text);
   etext = .;
   _etext = .;
   .rodata : ALIGN(0x8) {
     *(.rodata*)
     *(.srodata*)
   } > sram AT> flash
+  _rodata_vma = ADDR(.rodata);
+  _rodata_lma = LOADADDR(.rodata);
+  _rodata_end = ADDR(.rodata) + SIZEOF(.rodata);
   .data : ALIGN(0x8) {
     _sdata = .;
     *(.data*)
@@ -39,8 +44,8 @@ SECTIONS {
   } > sram AT> flash
   _sidata = LOADADDR(.data);
   _sidata_end = LOADADDR(.data) + SIZEOF(.data);
-  .bss : {
-    _bss_start = ALIGN(0x0008);
+  .bss : ALIGN(0x8) {
+    _bss_start = .;
     *(.bss*)
     *(.sbss*)
     *(.scommon)
@@ -52,7 +57,10 @@ SECTIONS {
 
   /* 堆区：PSRAM（可缓存 4MB），大小由 --defsym=_heap_size 指定。 */
   . = _stack_pointer;
-  _heap_start = 0x80000000;
+  _heap_start = ORIGIN(psram);
+  /* Check the size before addition so a wrapped end cannot pass the bound. */
+  ASSERT(_heap_start <= ORIGIN(psram) + LENGTH(psram), "heap start exceeds psram")
+  ASSERT(_heap_size <= ORIGIN(psram) + LENGTH(psram) - _heap_start, "heap size exceeds psram")
   _heap_end = _heap_start + _heap_size;
   end = .;
   _end = .;
```
