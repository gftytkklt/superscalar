# CRP — CCR-F0037 / CCR-F0038：klib stdlib 修复（2026-10-18）

## 范围、授权与验收

复用 [REPAIR_AND_REGRESSION](../REPAIR_AND_REGRESSION.md) 的既有修复计划及
[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next) 的已规划小批次。
用户“提交当前改动，并且继续CRP修复任务”确认规则维护并授权提交后执行本批；规则文档实际提交
`bc2d2d00f05d504673ab5a112d68d947c2a88c56`，提交后 root/index 干净。
本批仅处理已实现 stdlib.c 的两个明确契约问题，按 [CRP 执行规则](../workflow/README.md) 留档；
不改变 Make 入口、free CQ、堆布局或 M2 状态，不安装、不自动提交本轮新增修复。

| 问题 | 修改与失败语义 | 独立验收 |
|---|---|---|
| F0037 / High | malloc 按 `_Alignof(max_align_t)` 对齐，先检查 padding/剩余容量，成功后推进共享 `heap.start`；容量不足/溢出返回 NULL 且游标不变 | 1→8→16、非对齐起点、恰末端/超1/SIZE_MAX、padding耗尽/恰好、非法范围/高地址roundup、失败重试、共享游标；零大小保留标准允许行为 |
| F0038 / Low | atoi 跳六种 ASCII 标准空白、识别单一可选符号、负数累积支持 INT_MIN；无转换返回0，尾文本停止 | 六类空白/组合、±、多符号/中间空白、无转换、尾文本、0、INT_MIN/INT_MAX、非ASCII字节；只测试int可表示输入 |

消费端核对发现 `nanos-lite/src/mm.c:new_page()` 与 malloc 协作修改 `heap.start`，因此保留共享游标；
原审阅“独立cursor”只是修复建议，不作为改变公开heap语义的授权。局部临时变量计算候选地址，只在成功后发布，
并保留零大小原有的可返回非NULL行为和 native/use-klib 初始化分支。没有新增策略裁决或长期 Decision。

执行顺序：原版反例 → 最小源码修复 → 同版定向检查 → 共享真实消费者回归 → 统一留档并停止。
共享 klib 被 CPU-tests、RT/AM集成及 nanos 消费，均选择真实回归：CPU-tests 全集，RT update/run 到 msh，
nanos update/run 及 F1/F2/F3 三前台继续执行与后台 hello；host/fake 不代替 guest。
不跑 Linux、完整 NPC CPU-tests、音频或长时游戏：这些不属于本批两个函数的验收能力。
只在 `/tmp/crp-stdlib-h3d8ibwg` 源码副本生成产物；保留现有模拟器/REF，禁止自动 Git 钩子或无关重建。
`.agent`、原始证据、本批 local 下的一次性脚本/源码/镜像均保持本地忽略，提交范围仅最小生产修复/报告/索引/局部忽略。
完成后统一等待结果确认/commit，不自动进入下一批或 push。

## 定向验证（已完成）

`local/stdlib.before.c` 保留原版（审阅身份同源）；`local/host-check.local before` 的41项检查中21项失败：
F0037为11/14失败，F0038为10/27失败；malloc共享cursor/恰末端等对照通过。before退出1。
修复后 `local/host-check.local after` 以 ASan/UBSan、`-fno-sanitize-recover=all -O2 -Wall -Werror -fno-builtin` 编译，
**F0037 14/14、F0038 27/27，合计41/41通过，退出0**。
编译实际生产 stdlib.c，对host符号重命名以避免劫持宿主libc；检查使用真实AM/klib头。
初次编译因ccache只读缓存失败，启用进程级 `CCACHE_DISABLE=1` 后继续；不记作功能反例。

同一检查程序通过原 AM→NEMU `make ARCH=riscv64-nemu run` 入口交叉构建并执行：
41项/0失败、目标alignment=16，HIT GOOD TRAP；原生产 NEMU SHA不变。
命令/退出码/日志：`local/{before,after}-result.json`、对应 `*-run.log`、`direct-result.json/direct.log`。

## 真实消费者回归

| 验收 | 本轮结果与证据 |
|---|---|
| CPU-tests 真实 RV64 NEMU 全集 | **36 PASS + wrong 1 XFAIL，37/37，exit0**；`local/cpu-compat-serial-result.json`、`cpu-compat-serial.log`、`cpu-final-evidence/` |
| RT AM集成 update | 真实生成四应用，exit0，约1.42秒；`local/rt-update-result.json` 与日志 |
| RT 真实 NPC run | **约154.08秒到达 Hello RISC-V! / msh />，difftest ON，无比较分歧/坏trap**；`local/rt-run-result.json` 与日志。不声称四应用已执行 |
| nanos 真实 update/run | 完整navy更新 exit0，约22.11秒；108个extent与当前fsimg逐字节一致；真实 NEMU run 约52.33秒，F2 nterm输入qzx返回提示符，F3 slides 0→1→0，F1 pal切回/输入后继续刷新 |
| 后台hello/画面 | 八阶段计数1378→2169→2882→3674→4244→4812→5608→6401；原始BMP、帧hash及contact.png已视觉核对。SDL队列输入、MMIO、guest处理/显示均走原路径，观察库只在host采集/注入 |

CPU-tests首次原始命令 `make -j4 ARCH=riscv64-nemu git_commit= 'MAKE=/usr/bin/make -o <副本NEMU>' run`
得到35 PASS/1 XFAIL/1 ERROR：存量未跟踪的 `mem-test.c` 引用 `_heap_end`，NEMU linker.ld只给 `_heap_start`，因此未能链接。
这是测试平台接口缺口，不由两个stdlib函数引起，也没有删除该测试或缩小全集分母。
仅在后续验证命令补 `--eval=export LDFLAGS += --defsym=_heap_end=_heap_start+0x8000`，
为该测试提供32KiB堆区终点，位于真实PMEM内；原heap Area、生产linker及测试源不改。
首个compat命令未export变量到递归make，仍保留该失败记录；export后的-j4运行mem-test通过，
但div/shift遇到AM库并发重建导致无_start/空ELF的工具失败。最终使用**-j1**重新执行全部37项，
连同mem-test通过，不把中间失败冒充已验收。该结果仅证明上述测试配置下全集通过；原始默认命令的链接缺口仍存在。

RT/nanos持续guest均由本批监督器对自有进程组SIGTERM收停，make -15表示受控停止，
不声称guest正常退出。RT保留原仿真器/REF，nanos保留原NEMU；不改guest/NEMU/NPC源码以取得结果。
未跑完整NPC CPU全集、Linux、音频、长时游戏、RT四应用运行或人工GUI按键；本次回归范围不扩写这些能力。
共享page allocator `new_page()` 的容量检查F0062仍独立未修，不从malloc修复推定整个内存分配链已安全。

## 身份、持久化与完成状态

- **F0037：修复Completed；F0038：修复Completed。** 两项分别通过14/14与27/27定向断言，并在同版RV64 guest复验；共享回归结果如上。
- 生产唯一修改：`abstract-machine/klib/src/stdlib.c`，15增15删，mode保持100755。
  原SHA `e772d41c112d0d43d5555881113aa4c0e859aa4f44e6e0610143ef1b5df168ca`；
  新SHA `34c43586aaf18b8ea35540b2ce4b3656d60277c03a008a369992ecd8e662fecb`。
- 两平台编译对象、真实源码副本及当前生产SHA已绑定；工具为GCC/cross GCC13.3.0、Make4.3。
  NEMU/REF/NPC二进制SHA分别 `455a618d…` / `ea44e661…` / `a9a2f8b7…`，与既有冻结产物相同，完整hash见 `local/tested-identity.json`。
- 原/修复源码、精确patch、命令/退出/日志、fixture/source manifest、CPU逐项证据、rt/nanos/定向ELF/BIN、ramdisk及运行器在`local/`；
  `local/validation.json`九项证据核对全部通过，`local/manifest.json`为本批本地证据清单。
  副本配方 `local/prepare.local`：复制现有源码，排除Git/build，重定位绝对symlink/files.mk，复制现有运行器；无安装/下载。
- 一次性host/guest夹具、收集器与生成证据均本地忽略，**本批不提交测试代码**；它们没有现有常规回归入口，按修复工作流只保留生产最小修复与文字报告。
  本批局部.gitignore只限制该记录目录，不改全仓跟踪规则或既有测试跟踪。
- root HEAD为 `bc2d2d0`，index空；**Working tree contains uncommitted CRP repair/documentation changes**。
  本批结果确认Pending、修复commit Pending，未push。此次“提交当前改动”只用于先前规则文档，不将新修复冒充已提交。
- 累计已修6项（F0015/F0052/F0051/F0085/F0037/F0038），剩余113项含5CQ；CCR原审阅台账/快照保留历史事实。
  下一批只见[TASK_QUEUE / CRP Next](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本轮不执行；M2保持。

回滚仅反向应用 `local/repair.patch` 并核对原SHA；若目标已被后续修改，先核对差异，不整文件覆盖、不reset/clean、不回退嵌套仓库。
记录与.agent本地忽略资产需另行携带或按配方恢复，commit不等于备份。


<a id="f0037-f0038-submit-20261018"></a>
## 2026-10-18 用户确认与提交收尾

用户“提交”确认已报告的F0037/F0038修复范围并授权本批提交。复用原技术验收/完成记录；本轮核对188份本地证据hash、生产SHA及精确patch无漂移，未重跑产品测试、不重复完成快照。
提交范围仅stdlib.c、本报告/局部.gitignore及process索引；测试代码、镜像/原始证据/.agent继续本地保存。
实际commit及提交后working tree/index状态见本地 `local/submit-20261018/receipt.json` 和.agent确认/提交回执。
前文Pending/HEADbc2d2d0为完成时历史截面；本补充不扩写原验收及限制。提交后停止，F0033/F0056仍Planned未开始，无push授权。


2026-10-18 空间清理附记：用户明确授权删除工作区大型临时存档。本目录的大型归档
ramdisk或一次性完整raw测试快照已按[清理记录](../../workspace-storage-cleanup-20261018/README.md)
精确删除，原路径/尺寸/SHA见该记录local/deletion-manifest.json；原文本验收/命令/
结果与哈希保留，历史manifest缺失项须结合该授权清单解释，不视为源码漂移或验收
事实变更。旧产物字节不再本地保留，需复核时按原版本/配置重建或重新运行测试。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0037/F0038 — 根仓库

保留原 bump allocator/free 能力边界与 atoi 非法/超范围限制。

- 差异路径相对于仓库 `.`；旧版本：`bc2d2d00f05d504673ab5a112d68d947c2a88c56`；新版本：`0aa1dca5a49716461a1b09bf02f14fe26faa9dc9`。

#### `abstract-machine/klib/src/stdlib.c`

F0037：malloc 在 uintptr_t 地址域按 `_Alignof(max_align_t)` 算 padding，先检查 start/end、padding 与 size 是否超剩余容量，全部成功才发布共享 `heap.start = addr + size`；失败不推进 nanos new_page 共用游标，支持恰好用尽容量。F0038：atoi 跳过空格及 tab～CR，消费单个 +/-；`x = x * 10 - digit` 负向累计，使 INT_MIN 不必先形成不可表示的正数，最后按符号返回。仍不定义超出 int 范围输入的溢出处理。

```diff
diff --git a/abstract-machine/klib/src/stdlib.c b/abstract-machine/klib/src/stdlib.c
index 2e8ef7aac318560a99023c82ad32b64d0f864a3f..683ffa1fa9e07e30c7959a369f0c0b28280fdc40 100755
--- a/abstract-machine/klib/src/stdlib.c
+++ b/abstract-machine/klib/src/stdlib.c
@@ -21,12 +21,15 @@ int abs(int x) {
 
 int atoi(const char* nptr) {
   int x = 0;
-  while (*nptr == ' ') { nptr ++; }
+  while (*nptr == ' ' || (*nptr >= '\t' && *nptr <= '\r')) { nptr ++; }
+  int negative = (*nptr == '-');
+  if (*nptr == '+' || *nptr == '-') { nptr ++; }
+  // Accumulate negatively so INT_MIN does not require a positive int value.
   while (*nptr >= '0' && *nptr <= '9') {
-    x = x * 10 + *nptr - '0';
+    x = x * 10 - (*nptr - '0');
     nptr ++;
   }
-  return x;
+  return negative ? x : -x;
 }
 
 void *malloc(size_t size) {
@@ -34,18 +37,15 @@ void *malloc(size_t size) {
   // Therefore do not call panic() here, else it will yield a dead recursion:
   //   panic() -> putchar() -> (glibc) -> malloc() -> panic()
 #if !(defined(__ISA_NATIVE__) && defined(__NATIVE_USE_KLIB__))
-  // panic("Not implemented");
-  // if(size == 0){return NULL;}
-  
-  // size_t remainder = size % 8;
-  // size_t incr = (remainder == 0) ? size : (size + 8 - remainder);
-  // void *addr = heap.start;
-  // if (addr + incr >= heap.end){addr = NULL;}
-  // heap.start += incr;
-  void *addr = heap.start;
-  heap.start += size;
-  return addr;
-  
+  uintptr_t start = (uintptr_t)heap.start, end = (uintptr_t)heap.end;
+  const size_t alignment = _Alignof(max_align_t);
+  size_t padding = (alignment - start % alignment) % alignment;
+  if (start > end || padding > end - start) { return NULL; }
+  uintptr_t addr = start + padding;
+  if (size > end - addr) { return NULL; }
+  // nanos new_page() shares heap.start; publish only a successful allocation.
+  heap.start = (void *)(addr + size);
+  return (void *)addr;
 #endif
   return NULL;
 }
```
