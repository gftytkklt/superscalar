# CRP F0026 — NPC 链接期静态布局越界检查

> 当前实施方向（2026-10-21）：用户质询后明确这是静态越界诊断，而非重新制定固定栈预算；agent撤回2/4KiB预留建议，用户“同意你此次分析”确认修正方向。沿同一F0026实施四脚本链接期检查，保留SP/各正常段布局/Make接口，限制跨SP的静态放置并报告最终ELF静态余量。下方原64次候选实验与预算建议作为历史分析保留，原“等待预算裁决”已失效。实际修复/验收见文末：本轮已完成，结果确认/commit Pending；无commit/push授权。

2026-10-21。用户“继续”授权 TASK_QUEUE#crp-next 的一个必要分析单元；前 F0017 已确认、分析已提交 `3296304aa8a417e1a4087c50af5bb4c4e1c87cf6`，开始前 root/index 干净。复用[整体修复计划](../REPAIR_AND_REGRESSION.md)和[CRP workflow](../workflow/README.md)，不重立业务 Phase，M2 保持。

## 本单元计划与停点

- 目标/范围：核对 AM 四个受影响链接脚本、npc.mk 的启动选择及栈初始化，结合 P4 和已有真实布局证据，确定最小保护方案及真实预算缺口。
- 交付：本报告、local 中当前源码/工具身份、原脚本链接反例和隔离候选实验的命令/结果、清理回执；同步 records 索引、修复镜像与本地状态。
- 验收：四路径可达闭包与 static/SSBL/sp 边界可定位；正常和越界反例来自当前原脚本；候选实验与生产实施严格区分；预算建议说明依据和限制；生产源码与正式资产保持。
- 结束节点：必要分析留档后停止。栈预算改变 SRAM 静态容量，须用户裁决；不擅自预留栈、不安装、不 commit/push、不启动下一组/M2。

以下实验以 `0x800`（2 KiB）作**未批准的隔离候选参数**，不是当前配置或已认定的安全栈预算。

## 分析结论与当前可达路径

**必要分析 Completed；F0026 未修，分析结果确认/commit Pending。** 生产脚本、启动代码、Make 接口均无修改；不将候选实验记为修复或运行验收。119 项仍为 103 已修 + 12 CRP 待修 + 2 Linux 能力移交 + 2 无需实施闭合。

AM `scripts/riscv64-npc.mk` → `scripts/platform/npc.mk` 读取 `npc/.npc_config`（本轮仍为 `BOOT_MODE=xip`），命令行 `LDS/BOOT_S` 可覆盖；npc.mk 将 `_sram_start=0x0f000000`、`_stack_offt=0x1800` 传给链接器。三种启动汇编均先 `la sp, _stack_pointer` 再调用 C，栈向低地址增长。SRAM 物理区间 `[0x0f000000,0x0f002000)` 为 8 KiB，初始 SP 为 `0x0f001800`；顶上 2 KiB 不会因栈向下生长而自动成为栈容量。

| 路径 | 当前选择/入口 | SRAM 中与栈竞争的内容 | 主要边界 |
|---|---|---|---|
| xip | 默认，`linker-soc.ld` / `start.S` → `_trm_init` | `.data/.bss`；text/rodata 在 flash | `_bss_end`；TRM 先建 C 帧，再调用 loader 搬 data/清 BSS |
| sram | `BOOT_MODE=sram`，`linker-sram.ld` / `start_sram.S` → `_boot_loader` | 主程序 text/rodata/data/BSS | `_bss_end`；搬主程序时 bootloader 已在使用同一 SRAM 栈 |
| sdram-heap | 同名 BOOT_MODE，`linker-sdram-heap.ld` / `start.S` | `.data/.bss`；只有 heap 改到 SDRAM | `_bss_end`；风险不随 heap 移动消失 |
| psram-ssbl | 同名 BOOT_MODE；RT BSP 另显式导出 LDS/BOOT_S；`start_fsbl.S` → `_fsbl_loader` → `_ssbl_entry` | `.ssbl`，主程序在 PSRAM | `_ssbl_end_vma`；FSBL 搬 SSBL 时已使用 SRAM 栈，SSBL 继续复用 |

`linker-psram.ld`、`linker-sdram.ld` 和显式 RT 变体 `linker-sdram-rt.ld` 的常规主程序段均在外部 RAM，SRAM 仅供栈，未发现同一常规静态区竞争；本轮读取它们核对边界，不扩展其能力或修改它们。`npc/scripts/linker-soc.ld`、`linker-sram.ld` 是另外两份文件，不是 npc.mk 当前映射的脚本；本轮未将其混作 AM 活跃链接路径，也不作全仓无消费者的断言。

原 [P4](../P4.md) 的三种 7 KiB BSS 反例及原 source/probe evidence 保持历史事实。后续 [F0025/F0027/F0028](../crp-f0025-f0027-f0028/README.md) 已修改 BSS 对齐、搬运和 heap 边界，因此本轮直接读取和链接当前源，不复用旧脚本作为当前身份。当前四脚本仍只有 SRAM 总容量约束，没有静态区与栈的隔离。

## 当前源码链接实验

证据为 `local/entry.json`、`commands.json`、`results.json` 和逐条 `.log/.map`。工具为系统现有 `/usr/bin/riscv64-linux-gnu-gcc`、`ld`、`nm`、`objdump`（版本日志保留），无安装。直接编译当前真实 start/boot_sram/fsbl/ssbl，不执行项目 Make 或自动 commit hook。`_trm_init` 使用最小汇编夹具引用负载，**不运行 loader、应用或 guest**。

复现：从本报告父仓的 `entry.json.head` 取对应源码，参照 `local/analyze.py` 和逐条 `commands.json` 在新的隔离输出目录执行；脚本拒绝覆盖已有 `results.json`。编译参数含 `-march=rv64g -mcmodel=medany -mstrict-align -fno-pic -O2 -fno-builtin -fno-stack-protector -fno-asynchronous-unwind-tables -ffunction-sections -fdata-sections -fstack-usage`；链接保留 `--gc-sections`、原脚本和现有 defsym 值。最小夹具通过实际引用确保负载不被 GC。

候选仅改隔离脚本：一类追加静态末端 `ASSERT(end <= _stack_pointer - 0x800, ...)`；一类将 SRAM 的静态放置区域限到低端 `0x1000` 字节，初始 SP 和其他区域不变。正式脚本均未写入这些改动。

| 负载场景（四模式逐一） | 当前原脚本 | 末端 ASSERT 候选 | 静态 region 限额候选 |
|---|---|---|---|
| 小程序 | 4/4 link 0 | 4/4 link 0 | 4/4 link 0 |
| static/SSBL 恰好结束于候选栈底 `0x0f001000` | 4/4 link 0 | 4/4 link 0 | 4/4 link 0 |
| static/SSBL 结束于 `0x0f001001`（越 1 字节） | 4/4 link 0 | 4/4 非零，预期 overlap 诊断 | 4/4 非零，预期 region overflow |
| static/SSBL 结束于 `0x0f001c00`（7 KiB，越过 SP） | 4/4 link 0 | 4/4 拒绝 | 4/4 拒绝 |
| 小程序另带 7 KiB `.noinit` orphan 输入节 | 4/4 link 0 | 4/4 link 0 | xip/sram/sdram-heap 3/3 拒绝；SSBL 模式 link 0，因该节实际在 PSRAM，不占 SRAM |

另有四次原脚本校准，总计 **64 次链接观察**：原脚本 24 次成功；ASSERT 候选 12 次成功/8 次正确拒绝；region 候选 9 次成功/11 次正确拒绝。最终采集记录 **231 条命令**，全部与预期一致；拒绝不仅检查非零，还核对具体诊断。原脚本没有实际运行，所以 link 0 只表示允许布局，不表示能正常启动。

三个 SRAM 主静态区模式的 `.noinit` 分别从 `0x0f000009`、`0x0f000029`、`0x0f000009` 起，大小 `0x1c00`，实际跨过初始 SP；`_bss_end` 仍停在该节之前，故单独检查它会漏报。SSBL 模式该节落在 `0x80000028`，候选 region 没有误拒绝这个 PSRAM 控制例。未把 `.noinit` 加入生产，也未顺带承诺该节的初始化语义。

第一次 SSBL 实验将 padding 排在真实 SSBL 对象前，后续对象对齐影响末端的 +1 字节校准，脚本自检失败并停止；该次记录完整保留在 `local/attempt1/`。最终调整隔离夹具的链接顺序，使 padding 位于 SSBL 末尾后重做，四模式 `0x1000/0x1001/0x1c00` 均由 nm 实测，不把失败采集算进上述 64 次最终结果。

## 栈预算依据及最小建议

本轮 `-fstack-usage`/反汇编观察：`_fsbl_loader`、`_ssbl_entry`、`_boot_loader`、TRM `loader` 和 `_trm_init` 各有 16 字节自身帧，部分叶函数为 0。FSBL 调用 SSBL、SSBL 调用 TRM 前没有重设 SP，存活帧须累加；TRM 后还有 main/库函数、可能的递归和 trap（当前 NPC Context 帧 288 字节）等。本轮没有枚举应用最深调用链、栈水位或中断嵌套，**不能从单函数帧推导整个程序只需要几十字节，也不能把 2 KiB 认定为已证明足够**。

本轮只读留存 RT ELF：`.ssbl=[0x0f000000,0x0f0000b8)`（184 字节），SP 为 `0x0f001800`，二者距离 5960 字节，主程序 BSS 在 PSRAM。详见 `local/existing-rt.json` 及 symbols/sections 日志；这与 [DEBUG_WORKFLOW §5.2](../../../../docs/DEBUG_WORKFLOW.md) 的历史小 SSBL 布局相符，但留存 ELF 未在本轮重建/运行，不能用其体积证明当前所有构建或应用的栈安全。

**建议待用户裁决后实施：保留现有 SP，给四个竞争布局统一预留 2 KiB 栈区间 `[0x0f001000,0x0f001800)`，把 SRAM 静态区/SSBL 的可放置范围限制为低端 4 KiB。** 本建议是在静态容量和栈余量间选取初始工程预算，并非依据实验宣称通用最小值。若选择 4 KiB 栈，则栈底降至 `0x0f000800`，静态区/SSBL 仅剩 2 KiB；当前文档也没有充分依据自动替用户选择这一容量损失。未建议移动 SP、搬迁栈或扩大物理 SRAM，这些会改变现有启动布局。

最小实施方向：在四脚本内明确栈边界/物理边界，限制 static region，核对 SP 位于 SRAM 且满足 16 字节对齐，使用减法/先检查再计算避免预算下溢；不新增 Make 选项、目标或日常步骤。region 方案可覆盖上面 orphan 漏洞，优于仅针对 `_bss_end/_ssbl_end_vma` 的断言。最终实现仍须核对 orphan 放置、PHDR/LMA/二进制输出、空节和现有 heap 符号，不把本轮常量候选直接当最终 patch。

预算获准后的验收范围：四路径小程序/栈底恰界/+1/7 KiB、orphan、无效边界；受影响真实 NPC 启动/CPU 全集及 RT update→run 到 msh。用隔离的真实运行检查所选代表负载的主栈水位/哨兵，记录其覆盖范围；只测代表负载不承诺任意程序永不栈溢出。其他三个无常规 SRAM 静态竞争模式做布局不变控制即可；本轮没有生产修改，因此 CPU/RT/nanos 新运行均 NotRun，无影响的软件不额外重跑。

## 参考与限制

2026-10-21 读取 [ICS-PA2.3 程序、运行时环境与 AM](https://ysyx.oscc.cc/docs/ics-pa/2.3.html)，用于运行时/平台分工背景；讲义未给本项目 NPC SRAM 栈预算，具体地址和容量以当前代码为准。另查阅 [GNU ld ASSERT 官方说明](https://sourceware.org/binutils/docs/ld/Miscellaneous-Commands.html)：条件为零会报错退出，且符号定义/求值时点会影响断言；本轮已实际链接候选，不仅依赖语法推测。2.1 页面一次读取超时，未作为结论依据。

生产身份、八份正式配置/镜像资产在分析开始和结束按 SHA256 比对；原问题根因仍存在。下一动作仅见 `.agent/TASK_QUEUE.md#crp-next`：先由用户确定栈预算/布局取舍，再恢复同一 F0026；分析文档尚未 commit 不另立技术实施阻塞，提交仍须授权。按 [WORKFLOW_POLICY §3](../../../../docs/WORKFLOW_POLICY.md) 的真实取舍停点结束，不自动实施或切换单元。

## 收尾核验与清理

508 项清理前证据/导航/身份核对通过；包含清理清单逐文件核对及清理后复核共 1086 项通过（属于链接证据和收尾一致性检查，不能当成 1086 个功能测试）。64 次最终链接的命令/退出码/诊断、119 项 103/12/2/2 对账、生产源码与八份正式资产身份保持；index 为空，未 commit/push。记录在 `local/validation-preclean.json`、`final-validation.json`。

确认本单元编译/链接进程均已结束后，按 `local/cleanup-plan.json` 删除本轮及首次校准的两个隔离 build 目录：**542 文件，2,036,695 字节**，0 tracked/正式资产删除；候选脚本、生成汇编和二进制均可由 Git 基线 + `local/analyze.py` 重建。删除后两个 build 目录不存在、无剩余 o/ELF/bin/镜像等产物，源码与八资产再次保持。保留文字日志、map、su、结果、失败说明、最小采集/收尾配方和身份；manifest 覆盖保留 local 证据。忽略证据/.agent 仍需本地持久化，Git 提交不等于备份。


<a id="implementation-20261021"></a>
## 用户确认后的实施计划（2026-10-21）

本轮范围：四AM脚本按现有SP限制SRAM静态布局上界，检查既有栈地址配置；无固定栈预算或新的内存分配。MEMORY限额覆盖未列出的orphan，不仅检查BSS/SSBL末端；最终ELF所有SRAM已分配节的高水位用于统计静态间隙，不能将其称为运行时安全栈容量。边界正好等于SP按半开静态区间接受，此时静态间隙为0，链接成功不证明启动/调用栈安全；跨SP才是本轮静态越界错误。

验收：当前HEAD原脚本与修复后的小程序/bin逐字节比较、四路径SP恰界/+1/7KiB和orphan、SP物理边界/对齐无效值；七模式真实NPC小程序、受影响CPU全集和RT update/image/run到msh，记录实际剩余静态间隙。动态水位不是本次验收或承诺。交付完整内嵌diff及正反应用、源码/产物身份、清理回执、records索引及唯一状态入口；完成报告后停下，结果确认/commit另计，不自动下一组/M2。


## 实际修复结果与验证

**F0026 Completed；修复结果用户确认/commit Pending。** 用户确认来源为本轮“同意你此次分析”，仅确认修正后的分析方向，不伪称用户已复核本轮结果；未自动commit/push。原103已修增为104，CRP待修由12降为11，另2能力移交/2无需实施闭合，119总数不变。

四脚本把用于静态放置的 `sram` MEMORY 长度从物理上限 `8K` 改成 `MIN(8K, _stack_offt)`；与已有 `_sram_start=ORIGIN(sram)` 一起，将上界准确绑定原初始SP。这个MEMORY值是链接放置限制，不改变硬件物理8KiB容量，不输出新的栈段，不分配固定栈预算。静态区跨过SP时，GNU ld按具体段报 `region sram overflowed by N bytes` 或 `will not fit`，比只对BSS末端断言更能覆盖orphan。没有修改Make选项、目标、正常启动段地址或启动汇编。

另三条ASSERT检查既有配置：栈基址与SRAM起点一致；偏移为正且不超过物理8KiB；SP按16字节对齐。先以MIN限制静态区，再拒绝不合法配置，避免把无效偏移解释成可用物理SRAM。上边界SP=SRAM末端是合法初始指针，因为栈向下增长；正常字节范围仍使用半开区间。**static end == SP可以链接、静态间隙为0；本项只诊断静态跨界，不保证首次C帧或后续动态栈安全。**

没有新增一个依赖BSS末端、却可能漏orphan的“可用栈”生产符号。静态余量从最终ELF所有SRAM内ALLOC节的最高结束地址到初始SP求差，包含orphan，结果保存在 `local/implementation/directed/results.json`；该数是布局间隙，不是调用栈安全证明。本轮小夹具xip/sram/sdram-heap/psram-ssbl分别为6135/6111/6135/5903字节；本轮RT的SSBL为240字节，SRAM静态间隙5904字节（与前一轮只读旧ELF的184字节SSBL区分）。

| 验证 | 本轮结果 |
|---|---|
| 当前HEAD原脚本与生产修复后定向 | 72次实际链接观察，正常/精确SP-1/SP/SP+1/7KiB、orphan和栈配置边界全部符合预期；四种正常小镜像bin逐字节一致。SP+1与7KiB在修复后拒绝，原脚本成功；0/负偏移/不对齐/超物理尾拒绝，SP在物理尾接受 |
| orphan覆盖 | xip/sram/sdram-heap的7KiB `.noinit`实际占SRAM，修复后拒绝；psram-ssbl的同名节落PSRAM，仍可链接。未按节名盲目拒绝外部RAM负载 |
| 真实NPC七模式 | 7/7 GOOD TRAP，difftest ON，真实启动/搬运及BSS/逐节字节核对；不以host链接结果代替guest运行 |
| CPU全集 | 隔离现有标准 `make -j1 ARCH=riscv64-npc ... run`，36 PASS + wrong 1 XFAIL，37/37；不是历史测试复用 |
| RT消费者 | 隔离标准update/image均exit0；真实NPC/difftest ON于148.01秒观测到msh，无BAD TRAP/对拍分歧，之后自有进程组SIGTERM，exit -15，不是guest正常退出。RT四应用生成与链接完成，不声称四应用逐项运行 |
| 真实RT前后镜像 | 用同一匹配FSBL配置的对象/库、替换原HEAD链接脚本重新链接，247948字节bin逐字节相同；完整命令/哈希见rt-binary-equivalence.json |
| 生产diff归档 | 四文件完整diff与实际工作树一致；在隔离目录正向应用逐字节等于新源、反向恢复旧源，patch-validation.json保存命令/结果 |

实现试验/夹具问题如实保留：首次“点号末端标记”原型仍漏orphan，未进入生产；随后采用MEMORY上界。首次隔离NPC构建因find不遍历vsrc目录symlink缺模块，补显式VSRC/CSRC清单后以当前源码构建成功（16.27秒，DIFF=1/PERF=1/PERF_R45=1、无GUI/trace）。CPU和RT共享隔离AM目录时，CPU切换启动配置后再做RT基线重链接遇到旧archive/start.o混入导致JAL超距；本轮只在隔离目录重建匹配FSBL archive再比较成功，原始失败log和后续命令保留，不把它误归因本修复或要求用户日常增加clean步骤。生产工程/正式资产未被这些隔离操作改写。

### 完整实现diff与源码身份

仓库：根 `/home/gftyt/ysyx-workbench`，路径均相对仓库根。旧完整commit：`3296304aa8a417e1a4087c50af5bb4c4e1c87cf6`；新源为2026-10-21尚未提交工作树，未虚构新commit。逐文件身份：

| 路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `abstract-machine/scripts/linker-soc.ld` | `f9c333088ea3eebe3703bcccaaaff0db996f1ca243875a8358536a0c35bb10d3` | `3483c8b2a4a7da1ea78e821233558cb21a1d855f76b489a4fe48514917c761fa` |
| `abstract-machine/scripts/linker-sram.ld` | `eace34929f2b5aae42697f72919b2d72a804612fd12553203c7b63e136a145d5` | `1055af077376a157d74b326cc43c42d926a4b9adac665018cdcd82f942c619f1` |
| `abstract-machine/scripts/linker-sdram-heap.ld` | `8eb45a733e92f9a98b209d7937852078253894b9b891ea093ab5c8d7c8b46489` | `cbeda14a8bd2bec192b7aa2862d233876265c0093597728fce70a725e402ed7a` |
| `abstract-machine/scripts/linker-psram-ssbl.ld` | `34962a60a09f699e33fe6579b02aa063f29e391e55cdd1c2adb6395308499eed` | `b556cec003a745e65ca9c846467a4114a6135e46a8b44933543f3cf56879f2de` |

```diff
diff --git a/abstract-machine/scripts/linker-psram-ssbl.ld b/abstract-machine/scripts/linker-psram-ssbl.ld
index e6f36f9..f622768 100644
--- a/abstract-machine/scripts/linker-psram-ssbl.ld
+++ b/abstract-machine/scripts/linker-psram-ssbl.ld
@@ -1,7 +1,7 @@
 ENTRY(_start)
 
 MEMORY {
-  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
+  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = MIN(8K, _stack_offt)
   psram (rwx) : ORIGIN = 0x80000000, LENGTH = 4M
   flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
 }
@@ -111,4 +111,9 @@ SECTIONS {
   _heap_end = ORIGIN(psram) + LENGTH(psram);
   end = .;
   _end = .;
-}
\ No newline at end of file
+}
+/* SRAM is physically 8 KiB. Bound static placement by the existing initial SP;
+ * this reserves no fixed stack budget and does not detect runtime stack growth. */
+ASSERT(_sram_start == ORIGIN(sram), "stack SRAM base does not match SRAM origin")
+ASSERT(_stack_offt > 0 && _stack_offt <= 8K, "initial stack pointer is outside SRAM")
+ASSERT((_stack_pointer & 0xf) == 0, "initial stack pointer must be 16-byte aligned")
diff --git a/abstract-machine/scripts/linker-sdram-heap.ld b/abstract-machine/scripts/linker-sdram-heap.ld
index 77e1dec..c9aebb1 100644
--- a/abstract-machine/scripts/linker-sdram-heap.ld
+++ b/abstract-machine/scripts/linker-sdram-heap.ld
@@ -2,7 +2,7 @@ ENTRY(_start)
 
 MEMORY {
   mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
-  sram (rw) : ORIGIN = 0x0f000000, LENGTH = 8K
+  sram (rw) : ORIGIN = 0x0f000000, LENGTH = MIN(8K, _stack_offt)
   sdram (rwx) : ORIGIN = 0xa0000000, LENGTH = 128M
   flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
 }
@@ -47,4 +47,9 @@ SECTIONS {
   _heap_end = _heap_start + _heap_size;
   end = .;
   _end = .;
-}
\ No newline at end of file
+}
+/* SRAM is physically 8 KiB. Bound static placement by the existing initial SP;
+ * this reserves no fixed stack budget and does not detect runtime stack growth. */
+ASSERT(_sram_start == ORIGIN(sram), "stack SRAM base does not match SRAM origin")
+ASSERT(_stack_offt > 0 && _stack_offt <= 8K, "initial stack pointer is outside SRAM")
+ASSERT((_stack_pointer & 0xf) == 0, "initial stack pointer must be 16-byte aligned")
diff --git a/abstract-machine/scripts/linker-soc.ld b/abstract-machine/scripts/linker-soc.ld
index 2f2569f..b6ffaff 100755
--- a/abstract-machine/scripts/linker-soc.ld
+++ b/abstract-machine/scripts/linker-soc.ld
@@ -3,7 +3,7 @@ ENTRY(_start)
 
 MEMORY {
   mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
-  sram (rw) : ORIGIN = 0x0f000000, LENGTH = 8K
+  sram (rw) : ORIGIN = 0x0f000000, LENGTH = MIN(8K, _stack_offt)
   psram (rw) : ORIGIN = 0x80000000, LENGTH = 4M
   flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
 }
@@ -56,3 +56,9 @@ SECTIONS {
   end = .;
   _end = .;
 }
+
+/* SRAM is physically 8 KiB. Bound static placement by the existing initial SP;
+ * this reserves no fixed stack budget and does not detect runtime stack growth. */
+ASSERT(_sram_start == ORIGIN(sram), "stack SRAM base does not match SRAM origin")
+ASSERT(_stack_offt > 0 && _stack_offt <= 8K, "initial stack pointer is outside SRAM")
+ASSERT((_stack_pointer & 0xf) == 0, "initial stack pointer must be 16-byte aligned")
diff --git a/abstract-machine/scripts/linker-sram.ld b/abstract-machine/scripts/linker-sram.ld
index 98a7b62..d9ef60f 100644
--- a/abstract-machine/scripts/linker-sram.ld
+++ b/abstract-machine/scripts/linker-sram.ld
@@ -1,7 +1,7 @@
 ENTRY(_start)
 
 MEMORY {
-  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
+  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = MIN(8K, _stack_offt)
   psram (rw) : ORIGIN = 0x80000000, LENGTH = 4M
   flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
 }
@@ -64,4 +64,9 @@ SECTIONS {
   _heap_end = _heap_start + _heap_size;
   end = .;
   _end = .;
-}
\ No newline at end of file
+}
+/* SRAM is physically 8 KiB. Bound static placement by the existing initial SP;
+ * this reserves no fixed stack budget and does not detect runtime stack growth. */
+ASSERT(_sram_start == ORIGIN(sram), "stack SRAM base does not match SRAM origin")
+ASSERT(_stack_offt > 0 && _stack_offt <= 8K, "initial stack pointer is outside SRAM")
+ASSERT((_stack_pointer & 0xf) == 0, "initial stack pointer must be 16-byte aligned")
```


完整diff已按框架修复归档要求正反核验。diff中空上下文行携带的一个空格属于证据字节，保持原样；不把它与报告正文空白错误混同。原分析64次实验、旧manifest与完成快照保持原事实，当前报告追加内容引起的文档变化不回写旧身份。

本轮未测运行时栈水位、任意递归/中断嵌套或所有应用的动态栈需求；这些不属于已确认的静态布局修复验收。Navy/nanos代码和布局未改，本轮不额外重跑三前台。具体生产身份、八正式资产保护、收尾核对和产物清理见下一节。唯一后续仍为TASK_QUEUE#crp-next；本批结果确认/commit门槛保持，其他任务未启动。


## 本轮实现收尾与停止状态

132项有名检查全部通过：定向链接/诊断、四正常bin一致、七真实guest、CPU/RT、diff正反及保护资产；不把收尾计数称为132个功能用例。清单在 `local/implementation/validation-preclean.json`，清理后结果在 `validation-postclean.json`。本轮已结束所有自有构建/运行进程（RT按msh停点发送SIGTERM并wait），随后删除五处完成验证的隔离构建/消费者树：**1184路径（1168普通文件、16个symlink），142,577,122字节**；不跟随目录symlink，0 tracked/正式资产删除。guest结果和原始运行日志先保存到 `guest-evidence/`，其余本轮最小配方、命令、log/map、身份、patch与清理前后清单保留；两个旧原型及生成源码/镜像均可从Git+脚本重建，不保留全量源码副本。清理后无剩余o/ELF/bin/a/so，四生产源码仍等于验收SHA，八正式资产保持。

本轮修复结果确认/commit Pending，HEAD仍为3296304；原“同意分析”不当作本轮结果验收或提交授权。根工作树含四生产脚本、本报告/.gitignore和两个记录索引的本批未提交改动；本地FINAL/REPAIR/.agent及原始证据仍忽略，commit不等于备份。唯一后续入口为TASK_QUEUE#crp-next，先等本批结果确认和commit；未来F0107/F0108字体缓存调用链必要分析仅Planned，不Start，不推进M2。


<a id="submit-20261021"></a>
## 结果确认与提交授权（2026-10-21）

用户“提交，可以直接继续就继续，否则停下”确认本批已报告修复范围，并授权八路径精确提交；同时授权在条件满足时提交后执行唯一未来入口F0107/F0108必要分析一个单元，覆盖先前“提交后停止/另有继续”的旧停点，不授权push、安装或未定策略。本批既有技术验收/清理与源、8正式资产及两份证据manifest复用核实，不重跑产品测试；104已修+11待修+2移交+2无需实施闭合保持。实际commit身份及逐路径mode/blob回执在local/implementation/submit-receipt.json，实际提交后补记本地状态；Git提交不备份忽略证据/.agent。
