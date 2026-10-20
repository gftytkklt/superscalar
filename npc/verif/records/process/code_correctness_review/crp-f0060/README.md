# CRP F0060 — 用户启动参数栈对齐（2026-10-20）

## 整体计划、授权与停点

用户“同意你提交以后进入下一项”授权F0069提交后执行唯一下一F0060。前组实际
提交 `e58bbd0a37e4d9c0680d047297ca4ea73eb51e94`，12文件173增17删，范围/身份一致，
Start前root/index干净。复用既有CRP计划、workflow和TASK_QUEUE，不推进M2/M3。

本单元只在context_uload中加入参数表与字符串之间的padding，使argc/指针表自然
对齐且交给_start/call_main的sp为16字节对齐；保持argc/argv/envp连续布局、字符串
地址和内容、VME/非VME翻译及既有入口。不改crt、分配/exec失败策略或Make流程。
F0061超容量、F0057/58非法ELF、F0074镜像地址契约保留；若发现真实新策略先停。

1. 从前组HEAD复现PAL、NTERM及有区分力的其他参数组合；实际生产context_uload
   的host sanitizer验证VME/非VME、空argv/envp、多参数与16种字符串长度余数。
   验收sp%16==0、各指针自然对齐、argc/argv/envp/NUL和全部字符串保持。
2. 只做最小生产padding修改。隔离构建实际nanos内核及必要一次性NEMU观察副本，
   在真实_start调用首次C函数前测量sp/a0，核对当前Navy ELF/磁盘身份；旧版应
   暴露未对齐，新版应通过。默认真实三前台/hello继续执行，纯生产内核另验。
3. 保存命令/退出码/输入/源码与配置/产物身份、必要patch；验证/目视后清理本组
   大镜像/构建/截图/生产源码副本，更新records、逐项台账与.agent/唯一未来入口。

结束节点：本组完成留档后停止，等待用户确认/commit；本条授权不自动提交新组、
push或启动下一项。无安装/系统改动。CPU/RT/NPC按调用闭包说明未测，不把host
夹具当真实guest，也不把首次入口对齐推定为全系统ABI/全部exec场景已验收。

计划落档时为Active；当前Completed，结果确认/commit Pending，结果及限制见下文。


## 本轮实施与验证结果

**Completed；新结果确认/commit Pending。** 生产仅loader.c增加5行：计算argc、
argv/envp指针表（含两个NULL）的总字节数，在表与字符串之间放0～15字节间隙，
使最终argc地址向下对齐16字节。字符串已经写好，地址和内容保持；表内仍为
argc/argv/NULL/envp/NULL连续排列，不改crt或新增辅助接口/Make开关。

| 验证 | 实际结果 / 本地证据 |
|---|---|
| 原版局部反例 | 从e58bbd0取loader.c；VME/非VME的PAL均sp%16=8而被断言拒绝（SIGABRT/exit-6），NTERM均触发UBSan未对齐uintptr_t写入（exit1）。`unit-results.json`与before日志 |
| 最终局部组合 | VME/非VME各99例，共198例，ASan/UBSan通过；含PAL、NTERM、空argv/envp，以及6种argc/envc组合×16种字符串长度余数。检查sp16对齐、argc/指针表布局、NULL与全部字符串内容/原地址、栈两侧canary及页分配/映射数。host直接include完整生产loader.c，FS提供零段ELF以隔离参数构造，AM/PCB头是stub，不替代真实ELF装载/目标ABI。LSan关闭，不声称LSan通过 |
| 实际构建与身份 | 一次性NEMU观察副本配置和生产.config相同，只在真实call_main第一条指令前记录寄存器；四个实际nanos内核（旧FG/旧NTERM/新FG/新非VME-NTERM）构建成功。四个Navy ELF与真实ramdisk对应extent全字节一致后才使用符号PC。`builds.json`、`fixtures.json`、`apps.json`、`observer-identity.json`、`consumer-source-identity.json` |
| 真实原版入口 | 旧FG：PAL sp=0x7fffffc8（mod16=8）、hello=0x7fffffd5（5）；旧NTERM=0x7fffffd5（5）。全是真实_start设置sp后、call_main首条指令前观察，a0与sp一致。原版运行exit0表示程序继续，不是ABI判据通过；检查器明确要求其不对齐 |
| 真实新版入口 | 新FG：PAL=0x7fffffc0，其余hello/NTERM/nslider=0x7fffffd0；四者sp%16均0且sp=a0。新非VME-NTERM实际入口也16对齐（sp=0x80041fd0）。`actual-C-entries.json`及runs/nanos日志；观察钩子只读寄存器，不改guest/寄存器/内存/异常 |
| 纯生产与有限运行 | 六次实际各1亿指令后输入q，均exit0：旧FG/旧NTERM观察、新FG观察及原NEMU、新非VME-NTERM观察及原NEMU；纯生产执行器不含观察钩子。无BAD/ABORT。`runs.json` |
| 默认三前台/后台 | 约52.85秒、8观察点：PAL标题/场景；nterm输入qzx得到command not found与新提示符；nslider 0→1→0且返回0像素SHA相同；F1/Enter后PAL有画面；hello37→167。contact已目视，PAL返回仍有既有蓝边，未声明全屏重绘/物理音视频通过。自有组SIGTERM后实际exit0，非guest正常完成。`nanos/result.json`、`visual-qa.json` |
| 身份/判据终检 | 97项预清理核验通过，含逐NEMU源文件身份（不是97个guest用例）；原NEMU/默认内核产物/配置、proc.c、Navy盘/表和crt源码保持，临时盘同SHA，修复与构建版本一致。`validation-preclean.json` |

依据：[RISC-V psABI §2.1](https://riscv-non-isa.github.io/riscv-elf-psabi-doc/#_integer_calling_convention)
要求标准调用入口栈16字节对齐；[ICS-PA用户进程参数](https://ysyx.oscc.cc/docs/ics-pa/4.1.html#用户进程的参数)
允许指针表与字符串间有间隙。2026-10-20读取；本项目仍采用既有GPRx指向argc、
_start将其作为sp/a0交给call_main的简化布局，无新ABI策略裁决。

## 影响、限制与下一入口

调用影响是所有context_uload参数构造：本次host两模式和真实RV64入口/默认消费者
已覆盖上述范围；CPU-tests/RT/REF接口/NPC RTL不消费nanos的参数布局，未重跑。
未测NPC nanos、所有app/任意exec链、长时/物理音视频；实际带环境变量/空argv的
目标执行仅host构造核验，不冒作所有组合真实运行。非法ELF、参数超容量/整数溢出/分配失败不属于本组，F0061等独立问题保持；
首次C入口验收不代表所有中断/函数调用ABI已核验，未宣称全ABI
或全系统正确。NTERM既有镜像地址F0074仍保留，本次非VME只用其现存对应路径。

累计47已修/72未修完，前46项含F0069已确认提交，本项新结果确认/commit Pending。
统一留档清理后停止；下一候选为既有F0064/F0065的文件描述符及定位边界，范围/
必读/验收和确认提交门槛只在TASK_QUEUE#crp-next维护，不自动开始/提交/push或推进M2。

## 再生与清理约定

local保留unit.py、prepare.py、run.py、nanos-run.local/observe_sdl.c、实际配置、
observer.patch/repair.patch、源/输入/构建/运行身份及退出码。复现应在新的空local
目录从Git e58bbd0重建并应用repair.patch，依次执行unit.py、prepare.py、run.py及
`python3 nanos-run.local nanos`；使用apps.json记录的原Navy ELF/ramdisk及对应表，
不把之后不同版本的ELF符号用于旧盘。prepare只复制当前输入，不修改真实盘、不安装，
构建使用-o compile_git或git_commit=避免自动提交。截图目视文字先落档，再清理
本组镜像/ELF/构建/生产源副本；具体删除数量/哈希见随后清理回执。ignored资料与
.agent不由普通commit备份，旧产物身份合并清理回执解释预期缺失。


实际清理完成：本组684文件、169182570逻辑字节（约161.3MiB），零tracked删除/零剩余产物。路径/类别/删除前SHA及实际回执见local/cleanup-plan.json与cleanup-receipt.json；原盘、默认构建与文字证据保持。


## 用户确认及提交授权（2026-10-20）

用户“提交后继续”确认本组已报告范围/验证/限制，授权提交后执行唯一F0064/F0065单元。58条manifest及18项终检保持，复用技术验收与清理，不重跑/重建。本节随提交落盘，实际SHA/文件集合见local/submit-receipt.json及.agent；不push、不自动提交新组。原Pending为完成时截面，ignored/.agent不由Git备份。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0060 — 根仓库

只展示已验收的五行栈布局修复。

- 差异路径相对于仓库 `.`；旧版本：`e58bbd0a37e4d9c0680d047297ca4ea73eb51e94`；新版本：`7b836855c4aeaacbbf399aa86b3829f79bac599f`。

#### `nanos-lite/src/loader.c`

F0060：`args_size = (argc + envc + 3) * sizeof(uintptr_t)` 计入 argc、两组指针及两项 NULL；`ROUNDDOWN(sp - args_size, 16) + args_size` 在字符串与表之间留出 padding。后续原代码依次压表/argc 后，入口 sp 正好为 16 字节对齐，字符串与已保存指针无需搬移。此处修对齐，不声称参数总容量/F0061 或异常指针已防护。

```diff
diff --git a/nanos-lite/src/loader.c b/nanos-lite/src/loader.c
index ef52e542d423d9579301ced9c265318d17b2763e..8db005a6e6799bedbc47066ac90ab432b7de80c6 100755
--- a/nanos-lite/src/loader.c
+++ b/nanos-lite/src/loader.c
@@ -168,6 +168,11 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
   }
   envp_addr[envc] = 0;
 
+  // Leave padding above the pointer tables so argc (and the initial sp)
+  // is 16-byte aligned without moving any of the strings.
+  size_t args_size = ((size_t)argc + (size_t)envc + 3) * sizeof(uintptr_t);
+  sp = ROUNDDOWN(sp - args_size, 16) + args_size;
+
   // 2. envp[] pointer array (with NULL)
   sp -= (envc + 1) * sizeof(uintptr_t);
   memcpy(USTACK_TO_PA(sp), envp_addr, (envc + 1) * sizeof(uintptr_t));
```
