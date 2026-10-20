# CRP F0062 / F0063 / F0089 — 堆与页表容量事务

## 计划与启动（2026-10-20）

复用CRP整体计划/工作流，一个独立单元。用户“提交后继续”确认F0083并授权
nested 8101fad、root 4b7570f提交后一个单元。双index/root干净、nested内容干净，
原850执行位差异保持。M2不变，不自动提交新组/push/安装。

目标/范围：只修libos _sbrk增量转地址的溢出和end下界；用uintptr_t地址域先检查
再计算，负增量在无符号域取幅值，兼容INTPTR_MIN；成功才更新program_break，
保留旧break返回、SYS_brk 0成功/非0失败、弱hook和errno现行契约。unsigned上界
是UINTPTR_MAX，不将高地址误判为有符号负地址；不以此宣称地址已映射或OS有容量。

阶段/交付/验收：本组最小生产修改、内嵌完整diff及语句解释、原版失败见证与
host UBSan边界、实际RV64 _sbrk/newlib sbrk链的小步堆读写/低层拒绝/极值保护，
复用隔离标准nanos update→run及三前台/hello，核对最终链接和盘内字节身份。
测试涵盖0/±值、INTPTR_MIN/MAX、UINTPTR_MAX/溢出、end下/恰end、低层拒绝时
状态与errno保持。host只替换低层，guest危险大地址仅经既有弱hook受控拒绝，
不实际触发巨大OS分配。CPU/RT/REF不消费Navy libos，不重跑。完成目视、归档
正反应用及正式资产保护后清理隔离产物，留最小本地证据。结束节点为整组完成
或真实策略/安装，报告后等待结果确认/提交；不进入下一组/M2。

用户补充要求核实F0063：确为同链未修的内核边界问题；原队列“F0063完成记录”
是错误引用，已核实不存在。F0063完整物理耗尽原子性还依赖F0062和AM map无失败
返回的接口，目前范围裁决待用户回复；先执行不依赖该裁决的F0089。本报告不将
F0063或宿主stub通过误记为内核容量修复。实际源码见nanos mm/new_page/loader、
proc PCB及AM NEMU vme；讲义参考2026-10-20读取[用户程序和系统调用](https://ysyx.oscc.cc/docs/ics-pa/3.3.html)，
该页说明运行时/系统调用分层，不代替本地堆边界与分配失败契约。

## 用户扩大本组范围及执行契约（2026-10-20）

用户明确选择“扩大本轮范围，连同F0062和页表分配失败事务一起修复”，本组
纳入F0062/F0063/F0089，不另开Phase。更正前述等待状态与队列误引用；F0063
原审阅记录保留未修历史，不伪造旧完成证据。

F0062：new_page以uintptr_t检查页对齐/容量/乘法，失败NULL且不动heap.start；
0页不推进游标。现有loader/初始化/AM页表的不可恢复分配调用检查NULL并受控
停止，不继续解引用；不新增通用回收、exec失败回滚或物理OOM恢复策略。

F0063：PCB记实际ELF段末heap下界，loader重载时清零重建；upper为AM area.end
减同一STACK_SIZE，增长不能覆盖栈或用户域外，checked roundup后才操作。
不回收/撤映射，max_brk仍是映射高水位，小幅缩减后再增长不重映射已有页。
在写任何页表前，用只读AM内部查询精确计算当前Sv39缺失的中间表页，一次checked
new_page预留全部数据+表页。失败原break/heap游标/页表不动；成功map只从预留池
取表页，容量已保证，提交后回收未消费的预留尾部。标准AM map(void)接口不变；
新增内部弱查询只由当前NEMU实现、nanos使用，其他目标保守预算现有表深度，
不宣称其他ISA/VME新能力已验收。串行单核syscall内不yield，预留期间不调用malloc。

新增验收：原版物理越界/乘法与brk越栈见证；host sanitizer checked页分配、
真实AM Sv39页表及query、数据/表容量分别不足的多页事务、原页表/游标/PCB不变、
精确够用、既有页表复用/跨2MiB/高水位及exec重建。实际RV64诊断需覆盖真实sys_brk
边界拒绝/正常小步与受控物理容量不足，标准三前台/hello按最终组合重跑。
共享AM仅新增只读查询，既有map行为不变；CPU/RT不调用新查询、不消费本组nanos/
libos修改，按调用闭包不重跑。最终记录完整组合身份和内嵌各文件diff，再清理产物。

## 实施结果 — Completed，结果确认与commit Pending

本组3项均完成当前RV64/NEMU/VME范围修复；6个根仓生产文件105增20删，
具体差异以下方完整diff及local/repair.patch为准。F0063真实未修和队列旧引用
错误已区分并更正；未改写原审阅FINAL_FINDINGS/P6/P7的历史结论。
累计63已修/56未修完（含5CQ及F0040部分）；前60已确认提交，本组3项待确认/提交。

| 验收 | 实际结果与local证据 |
|---|---|
| 原版见证 | F0089：INTPTR_MAX附近地址相加由UBSan准确报告有符号溢出；end以下缩减被接受，状态断言失败。F0062：越物理末端、页数乘法回绕均在指定断言失败；F0063：7fffe000→80001000越栈/用户域请求原版仍成功。五例均不是编译或工具失败。unit/before-overflow、before-lower；mm/before-p/w/b |
| F0089 host | 16场景84断言，0/±小值、恰end/低于end、INTPTR_MIN/MAX、UINTPTR_MAX临界与回绕拒绝、低层拒绝/旧值返回、参数及errno保持。最终UBSan无告警，unit-results |
| F0062/F0063 host | 实际最终mm.c及实际AM Sv39 query/map，ASan+UBSan默认/NDEBUG各137断言；0页/非对齐游标/末端恰满/反向物理域/roundup和乘法溢出，虚拟下界/栈底/上界，数据+表容量0至4页失败不动原arena/PTE/游标/highwater，精确5页容纳3数据+2表，已有表零额外预算、跨2MiB、恰栈底、同页增长和缩减不重映射；pg_alloc耗尽在两种构建均于memset前受控abort。LeakSanitizer因当前ptrace环境禁用，ASan内存访问和UBSan保持启用；不声称通用内存回收已验证。mm-unit-results |
| 实际RV64运行时/内核 | 最终实际_sbrk/_sbrk_r及new_page/mm_brk/query，84边界断言、8362累计真实堆/内核断言、exec重载新CRT后4断言；正常小步读写64B、实际malloc8192B写读，内核拒绝低于end/越栈/用户上界/最大地址/极值增量。GOOD TRAP/exit0，5,267,401指令。guest-result/run、符号与反汇编 |
| 页表容量失败事务 | 隔离诊断内核的测试专用SYS_times分派暂时缩小heap.end、随后还原；先零可用数据页，再仅容纳501数据页但缺跨2MiB新表页。两次真实mm_brk均-1，当前用户根/中间/叶表指纹、heap.start、max_brk保持；用户program_break亦保持。不把受控容量限制写成耗尽整个模拟器物理内存；生产系统调用接口未修改。kernel-mm-test、guest日志KERNEL MM CAPACITY PASS |
| 最终标准入口 | nanos目录现有make -j4 ARCH=riscv64-nemu git_commit= update exit0/18.061秒，再同参数run；108连续extent逐字节匹配当前安装文件，PAL/NTerm/NSlider/hello ELF链接/安装/盘内字节一致，libos和AM archive成员等于实际最终对象。standard-path/update-final、nanos-final2及165项preclean |
| 三前台与hello | 最终运行53.462秒，PAL标题/飞鸟→NTerm qzx not found并回prompt→幻灯片0/1/0→PAL/Enter继续；10条SDL事件顺序正确、8帧已实际目视；slide0恢复SHA一致，hello34→152。自有进程组SIGTERM/make-15是观察结束，不是guest正常退出或长期/实体音视频验收 |
| 身份/归档/判据 | 165项preclean全PASS，4891最终源/配置和851构建产物身份；6文件diff临时目录逐一正反应用精确；8种缺失/重复/非零/混BAD等故障均拒绝。正式盘/header/kernel/config/NEMU和proc.c字节保持，root4b7570f/nested8101fad与两index保持、850既有mode差异保留。archive-validation、validation-preclean、final-source/artifact-identity |

初次诊断guest虽已输出断言通过，return触发nanos sys_exit重载nterm，缺终止
GOOD而45秒超时；该轮未验收。测试夹具改为完成后exec一次验证新进程，再以
fflush+ebreak(0)结束，最终GOOD/exit0。后续完整组将新分配失败检查改为不随
NDEBUG移除的panic_on，host默认/NDEBUG及实际RV64/标准update→run均按最终
源码重跑。中间单F0089及pre-panic观察保留为历史尝试，不替代本组最终结果。

## 范围、限制和恢复

容量预留事务证明适用于当前单核串行syscall与NEMU Sv39 map配对；预留后map
仅消费池内表页，现有map没有其他可恢复失败返回。若未来页表层级、分配规则、
并发或map错误协议变化，必须同步查询/事务证明。未改变标准AM接口、页权限、
撤映射/回收或通用free策略；缩减仍保留已映射高水位。其他目标缺内部查询时
采用每数据页三中间表页的保守预算，可能提前拒绝；该路径未动态验收，不宣称
NPC VME、其他ISA、非VME brk语义或多核能力已补齐。

初始化/loader页耗尽明确panic停止，不承诺继续执行或回滚整个exec/ELF装载；
brk容量失败在任何PTE发布前拒绝。ELF合法性、参数/用户指针完整校验、实际堆
回收和errno重入仍各归既有未修项/CQ。CPU-tests/RT/REF不调用新增query、不消费
nanos/libos修改，既有AM map行为未变，按影响闭包不另跑；未测NPC nanos、
物理音视频、长期运行或完整Linux。无下载/安装/push，不推进M2。

root代码基线4b7570f7b674c67f2966afe8a03b4d185a22a7c5，nested基线
8101fad4376b7df0e3ec18db2db8cfa32746ad3a，均未推进；6源全归根仓，
嵌套库本轮内容未改。Working tree contains uncommitted CRP changes；本组新结果
不自动获确认/提交授权。最小一次性测试源/脚本与原始文字证据保存在local，默认
不入库；本报告/.gitignore/索引及生产源为未来精确提交范围。

从root基线+local/repair.patch恢复生产新源，正式资产/已有工具来源见entry与
standard-path/source-input-identity；无需下载。全新输出树按顺序执行：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/mm-unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/prepare-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/run-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/standard-path/run-standard.local nanos-final2
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/visualize.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/archive.py
python3 npc/verif/records/process/code_correctness_review/crp-f0089/local/check.py
# 目视后cleanup.py；最后final-check.py核对保留资料/状态。
```

整组完成留档后停止；唯一未来入口由TASK_QUEUE#crp-next维护，其他索引仅引用。

<a id="repair-diffs"></a>
## 最终框架/OS完整diff与实现说明

仓库：根`ysyx-workbench`。旧版本：`4b7570f7b674c67f2966afe8a03b4d185a22a7c5`；新版本：
`WORKTREE（2026-10-20，尚未提交）`。以下6份完整修复diff与工作树一致，逐文件
SHA256见各段；临时目录正向应用逐字节等于新源，反向应用逐字节恢复旧源。
核验记录local/archive-validation.json，完整原补丁local/repair.patch。

### `abstract-machine/am/src/riscv/nemu/vme.c`

新源SHA256：`f140e2389980a1a11ab831db521e26edb31ec534dac6dc60a2fcf545468ac592`。

F0063：__am_map_table_pages只读扫描当前根表及覆盖的2MiB区间；不存在的1GiB中间表仅计一次，每个缺失末级表各计一页。步长以end-va截断，避免地址步进溢出；不调用分配器、不写PTE。现有map代码不变，查询与其Sv39两级中间表分配规则配对。该内部辅助不改变标准AM map(void)接口。

```diff
diff --git a/abstract-machine/am/src/riscv/nemu/vme.c b/abstract-machine/am/src/riscv/nemu/vme.c
index b25904f6fcf27248baaa14029ff5f2de73ededba..917b65590a3dd9851ac80bbb346d34945fc62457 100755
--- a/abstract-machine/am/src/riscv/nemu/vme.c
+++ b/abstract-machine/am/src/riscv/nemu/vme.c
@@ -69,6 +69,29 @@ void __am_switch(Context *c) {
   }
 }
 
+// Internal read-only preflight for nanos-lite's heap allocation transaction.
+// Count each missing Sv39 table once, without allocating or publishing a PTE.
+size_t __am_map_table_pages(AddrSpace *as, uintptr_t start, uintptr_t end) {
+  PTE *root = (PTE *)as->ptr;
+  size_t pages = 0;
+  uintptr_t previous = (uintptr_t)-1;
+  for (uintptr_t va = start; va < end;) {
+    uintptr_t vpn2 = (va >> 30) & 0x1ff;
+    uintptr_t vpn1 = (va >> 21) & 0x1ff;
+    if (!(root[vpn2] & PTE_V)) {
+      if (vpn2 != previous) pages++;
+      pages++;
+    } else {
+      PTE *pt = (PTE *)((((root[vpn2] >> 10) & 0xfffffffff) << 12));
+      if (!(pt[vpn1] & PTE_V)) pages++;
+    }
+    previous = vpn2;
+    uintptr_t step = (1ul << 21) - (va & ((1ul << 21) - 1));
+    va += (end - va < step ? end - va : step);
+  }
+  return pages;
+}
+
 void map(AddrSpace *as, void *va, void *pa, int prot) {
   // Sv39 three-level page table: VPN[2]=va[38:30], VPN[1]=va[29:21], VPN[0]=va[20:12]
   uintptr_t vaddr = (uintptr_t)va;
```

### `nanos-lite/include/memory.h`

新源SHA256：`809e18804ba2679bd57d0ed4f20cf4bc18aa5ba07b6987c00670696b31e96caa`。

F0062：记录new_page的NULL失败/失败不推进及0页不推进契约，调用方必须处理或受控停止。

```diff
diff --git a/nanos-lite/include/memory.h b/nanos-lite/include/memory.h
index 1a9acd37b45c847466d35040dd43fe889cbb624f..43a5c547dfdb9e6381ebd089ac5bfe5a412f6738 100755
--- a/nanos-lite/include/memory.h
+++ b/nanos-lite/include/memory.h
@@ -9,6 +9,7 @@
 
 #define PG_ALIGN __attribute((aligned(PGSIZE)))
 
+// NULL on overflow/exhaustion; failure and zero pages do not advance heap.start.
 void* new_page(size_t);
 
 /* The brk() system call handler. */
```

### `nanos-lite/include/proc.h`

新源SHA256：`dde24dd4dcb628c776f0b9dfe3ea17765149fa613798b74abfe9a5b2f28f248b`。

F0063：brk_start独立保存未按页上取整的最高ELF段末，max_brk仍表示已映射高水位；两者不能互相替代。

```diff
diff --git a/nanos-lite/include/proc.h b/nanos-lite/include/proc.h
index 837675529c11cd1063466aa33b754f0d3c5aabff..4463fcfc4db88e69d3a26a826d2cb8600dae198e 100755
--- a/nanos-lite/include/proc.h
+++ b/nanos-lite/include/proc.h
@@ -13,6 +13,7 @@ typedef union {
     AddrSpace as;
     // we do not free memory, so use `max_brk' to determine when to call _map()
     uintptr_t max_brk;
+    uintptr_t brk_start;  // actual ELF segment end, before page rounding
   };
 } PCB;
 
```

### `nanos-lite/src/loader.c`

新源SHA256：`b0dc59f91a4a3151f84c45f641702840e2919933da7dfe95a29f755164650260`。

F0062/F0063：每次物理页/用户栈分配后立即panic_on检查NULL，避免带失败指针继续映射或拷贝；panic不因NDEBUG消失。exec先清零max_brk/brk_start，逐LOAD重新记录段末。用户栈分配和栈底统一使用STACK_SIZE，供mm_brk使用同一边界。未增加exec通用失败回滚、ELF可信性或参数容量能力。

```diff
diff --git a/nanos-lite/src/loader.c b/nanos-lite/src/loader.c
index 8db005a6e6799bedbc47066ac90ab432b7de80c6..ac82d334963e97c8bd7d04f120c901ed1b12b935 100755
--- a/nanos-lite/src/loader.c
+++ b/nanos-lite/src/loader.c
@@ -58,6 +58,7 @@ static uintptr_t loader(PCB *pcb, const char *filename) {
       for (uintptr_t va = page_start;
            va < ROUNDUP(vaddr + memsz, PGSIZE); va += PGSIZE) {
         void *pa = new_page(1);
+        panic_on(pa == NULL, "Out of physical pages loading ELF");
         map(&pcb->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);
 
         // copy the file part of this page (if any). Note the segment may start
@@ -80,6 +81,7 @@ static uintptr_t loader(PCB *pcb, const char *filename) {
       // record the peak program break (page-aligned) for mm_brk()
       uintptr_t brk = ROUNDUP(vaddr + memsz, PGSIZE);
       if (brk > pcb->max_brk) pcb->max_brk = brk;
+      if (vaddr + memsz > pcb->brk_start) pcb->brk_start = vaddr + memsz;
       #else
       fs_lseek(fd, offset, SEEK_SET);
       fs_read(fd, (void *)vaddr, filesz);
@@ -115,6 +117,7 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
   // skip mapping (brk <= max_brk) and the new program would run on unmapped
   // heap pages (exec-after-exit reload path).
   pcb->max_brk = 0;
+  pcb->brk_start = 0;
   Area kstack = {pcb->stack, pcb->stack + STACK_SIZE};
 
   // user stack: allocate a fresh 32KB region FIRST. Do not read argv/envp
@@ -125,15 +128,18 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
   // writes the arguments into the *physical* pages (reachable through the
   // kernel identical mapping), which are mapped to the user stack region.
   uintptr_t ustack = (uintptr_t)pcb->as.area.end;   // 0x80000000
-  uintptr_t ustack_lo = ustack - 8 * PGSIZE;        // 32KB
-  void *ustack_pa = new_page(8);
+  uintptr_t ustack_lo = ustack - STACK_SIZE;
+  void *ustack_pa = new_page(STACK_SIZE / PGSIZE);
+  panic_on(ustack_pa == NULL, "Out of physical pages for user stack");
   for (uintptr_t va = ustack_lo; va < ustack; va += PGSIZE) {
     map(&pcb->as, (void *)va, (void *)((uintptr_t)ustack_pa + (va - ustack_lo)),
         MMAP_READ | MMAP_WRITE);
   }
 # define USTACK_TO_PA(v) ((void *)((uintptr_t)ustack_pa + ((uintptr_t)(v) - ustack_lo)))
 #else
-  uintptr_t ustack = (uintptr_t)new_page(8) + 8 * PGSIZE;
+  void *ustack_pa = new_page(STACK_SIZE / PGSIZE);
+  panic_on(ustack_pa == NULL, "Out of physical pages for user stack");
+  uintptr_t ustack = (uintptr_t)ustack_pa + STACK_SIZE;
 # define USTACK_TO_PA(v) ((void *)(v))
 #endif
 
```

### `nanos-lite/src/mm.c`

新源SHA256：`3de04775726e379707fd7692accbc193a131dd43f014bd84927e02bc7362bfe4`。

F0062：new_page先检查cursor对齐相加，再用(limit-start)/PGSIZE验证页数，乘法只在确认容量后执行，NULL失败不写heap.start；0页返回可对齐位置但不推进。pg_alloc检查大小，正常初始化/loader耗尽panic，预留事务内只从table_next..table_end取页并清零。F0063：首先拒绝低于brk_start、越过area.end-STACK_SIZE及roundup不可表示的请求；缩减保留映射高水位。增长页数为0时不触碰物理堆；其余先查询缺失表页并checked new_page一次预留全部数据及表页。预留失败立即-1，未发布任何PTE；成功后map无需再向物理堆请求容量，最后提交max_brk并释放未用预留尾部。当前Sv39精确预算；缺少内部查询的其他既有目标保守预留每页至多三中间表页，未在本组动态验收。该证明依赖单核串行syscall、当前map表深度及预留期间无malloc/yield，代码变化须同步维护查询。

```diff
diff --git a/nanos-lite/src/mm.c b/nanos-lite/src/mm.c
index bbdcec366a77fbe3cf5df640f59f9383cb72ea6f..ad6ff094330593b18fbc9491fe3977d3e8788514 100755
--- a/nanos-lite/src/mm.c
+++ b/nanos-lite/src/mm.c
@@ -1,23 +1,35 @@
 #include <memory.h>
 #include <proc.h>
 
-static void *pf = NULL;
-
 void* new_page(size_t nr_page) {
-  // share the same cursor as klib's malloc (heap.start): read the current
-  // value, page-align it (malloc() may leave it unaligned), allocate nr_page
-  // pages, and write the advanced value back to heap.start. This keeps
-  // malloc() and new_page() on ONE coordinated cursor so they never hand out
-  // overlapping memory, and guarantees every returned address is page-aligned.
-  pf = (void *)ROUNDUP(heap.start, PGSIZE);
-  pf += nr_page * PGSIZE;
-  heap.start = pf;
-  return pf - nr_page * PGSIZE;
+  uintptr_t cursor = (uintptr_t)heap.start;
+  uintptr_t limit = (uintptr_t)heap.end;
+  if (cursor > UINTPTR_MAX - (PGSIZE - 1)) return NULL;
+  uintptr_t start = (cursor + PGSIZE - 1) & ~(uintptr_t)(PGSIZE - 1);
+  if (start > limit || nr_page > (limit - start) / PGSIZE) return NULL;
+  if (nr_page != 0) heap.start = (void *)(start + nr_page * PGSIZE);
+  return (void *)start;
 }
 
 #ifdef HAS_VME
+// Optional internal AM preflight; the supported NEMU Sv39 target counts exactly.
+extern size_t __am_map_table_pages(AddrSpace *, uintptr_t, uintptr_t)
+  __attribute__((weak));
+static uintptr_t table_next, table_end;
+
 static void* pg_alloc(int n) {
-  void *p = new_page(n / PGSIZE);
+  panic_on(n <= 0 || n % PGSIZE != 0, "Invalid page allocation size");
+  void *p;
+  if (table_end != 0) {
+    // mm_brk reserved the entire transaction before touching any PTE.
+    panic_on(table_next > table_end || (uintptr_t)n > table_end - table_next,
+             "Page table reservation exhausted");
+    p = (void *)table_next;
+    table_next += n;
+  } else {
+    p = new_page((size_t)n / PGSIZE);
+    panic_on(p == NULL, "Out of physical pages");
+  }
   memset(p, 0, n);
   return p;
 }
@@ -30,13 +42,40 @@ void free_page(void *p) {
 /* The brk() system call handler. */
 int mm_brk(uintptr_t brk) {
 #ifdef HAS_VME
+  if (current == NULL) return -1;
+  uintptr_t lo = (uintptr_t)current->as.area.start;
+  uintptr_t hi = (uintptr_t)current->as.area.end;
+  if (hi < lo || hi - lo < STACK_SIZE) return -1;
+  uintptr_t limit = hi - STACK_SIZE;
+  if (current->brk_start < lo || current->brk_start > limit ||
+      current->max_brk < current->brk_start || current->max_brk > limit ||
+      brk < current->brk_start || brk > limit ||
+      brk > UINTPTR_MAX - (PGSIZE - 1) ||
+      current->max_brk > UINTPTR_MAX - (PGSIZE - 1)) return -1;
   if (brk > current->max_brk) {
     uintptr_t start = ROUNDUP(current->max_brk, PGSIZE);
     uintptr_t end = ROUNDUP(brk, PGSIZE);
+    if (end > limit) return -1;
+    size_t pages = (end - start) / PGSIZE;
+    if (pages == 0) {
+      current->max_brk = brk;
+      return 0;
+    }
+    if (pages > SIZE_MAX / 4) return -1;
+    // Other existing AM targets have at most three intermediate table levels.
+    size_t tables = __am_map_table_pages ?
+      __am_map_table_pages(&current->as, start, end) : 3 * pages;
+    if (tables > SIZE_MAX - pages) return -1;
+    void *data = new_page(pages + tables);
+    if (data == NULL) return -1;
+    table_next = (uintptr_t)data + pages * PGSIZE;
+    table_end = table_next + tables * PGSIZE;
     for (uintptr_t va = start; va < end; va += PGSIZE) {
-      void *pa = new_page(1);
+      void *pa = (void *)((uintptr_t)data + (va - start));
       map(&current->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);
     }
+    heap.start = (void *)table_next;  // release any unused conservative budget
+    table_next = table_end = 0;
     current->max_brk = brk;
   }
 #endif
@@ -44,8 +83,9 @@ int mm_brk(uintptr_t brk) {
 }
 
 void init_mm() {
-  pf = (void *)ROUNDUP(heap.start, PGSIZE);
-  Log("free physical pages starting from %p", pf);
+  void *first = new_page(0);
+  panic_on(first == NULL, "Invalid physical heap");
+  Log("free physical pages starting from %p", first);
 
 #ifdef HAS_VME
   vme_init(pg_alloc, free_page);
```

### `navy-apps/libs/libos/src/syscall.c`

新源SHA256：`819a097066a66f69d5e2eab029e33b0c62870d8d9848231e655a511cc20e4089`。

F0089：把program_break和end转换到uintptr_t地址域，先检查当前地址不低于end。正增量与UINTPTR_MAX-current比较后再加；负增量用无符号0-increment得到幅值（含INTPTR_MIN），与current-base比较后再减。通过后沿原intptr_t syscall寄存器承载地址位模式，只有ret==0才将program_break设置为next并返回旧值。拒绝/内核失败返回(void*)-1且不改状态；不新增errno策略或改变弱hook/系统调用参数。

```diff
diff --git a/navy-apps/libs/libos/src/syscall.c b/navy-apps/libs/libos/src/syscall.c
index f8e32bb23ad9b13030557c635d4b18dc45d1ade2..f48b59df0564037a166d1ba12aa3cb7b1f1f8b71 100755
--- a/navy-apps/libs/libos/src/syscall.c
+++ b/navy-apps/libs/libos/src/syscall.c
@@ -4,6 +4,7 @@
 #include <assert.h>
 #include <errno.h>
 #include <time.h>
+#include <stdint.h>
 #include "syscall.h"
 
 // helper macros
@@ -80,10 +81,23 @@ long _write(int fd, void *buf, size_t count) {
 }
 
 void *_sbrk(intptr_t increment) {
-  int ret = _syscall_(SYS_brk, (intptr_t)program_break+increment, 0, 0);
+  uintptr_t current = (uintptr_t)program_break;
+  uintptr_t base = (uintptr_t)&end;
+  uintptr_t next;
+  if (current < base) return (void *)-1;
+  if (increment >= 0) {
+    if ((uintptr_t)increment > UINTPTR_MAX - current) return (void *)-1;
+    next = current + (uintptr_t)increment;
+  } else {
+    // Unsigned negation also handles INTPTR_MIN without signed overflow.
+    uintptr_t decrement = (uintptr_t)0 - (uintptr_t)increment;
+    if (decrement > current - base) return (void *)-1;
+    next = current - decrement;
+  }
+  int ret = _syscall_(SYS_brk, (intptr_t)next, 0, 0);
   if (ret == 0){
     void* addr = program_break;
-    program_break += increment;
+    program_break = (void *)next;
     return addr;
   }
   return (void *)-1;
```


## 最终产物清理与停点

165项preclean、最终8帧实际目视、6文件diff归档核验完成后，已删除9523文件
835,816,114逻辑字节（约797.1MiB），零tracked删除；范围仅本组隔离生产源码/
构建/盘、所有中间与最终诊断树、可执行夹具和截图/观察库。local/cleanup-plan.json
及cleanup-receipt.json列删除前路径/字节/SHA与删除后回执；源码可由根基线+repair.patch
再生，旧身份路径预期缺失，不宣称删除后仍能直接查看原图或复用旧镜像。
最小脚本/测试源/配置/命令/结果/身份/补丁继续本地保留，ignored/.agent不由commit备份。
本组完整收尾后停止，等待结果确认与精确根提交；下一单元仅见TASK_QUEUE#crp-next。


<a id="submit-20261020"></a>
## 用户确认与提交收尾（2026-10-20）

用户“提交”确认本组已报告的F0062/F0063/F0089范围并授权精确根提交。提交前
100项最终manifest均无漂移，6源与已验收repair.patch逐字节一致，复用既有360项
终检及动态验收，不重跑产品测试、不重复Completion或产物归档；9523清理路径
均按回执预期缺失，nested仍8101fad/内容及index干净、原850执行位差异保持。

本次根提交仅6份生产源、本报告/.gitignore及process/repair-status两份索引；
一次性local测试/日志/JSON与.agent/REPAIR未入库，未改跟踪规则。上文工作树版本/
未确认状态均为原验收截面；用户现已确认，修复后的正式源码版本以包含本附记的
根提交为准，完整SHA及路径/mode/blob/提交后工作树核对保存于
local/submit-staged.json和submit-receipt.json。原6份内嵌diff/前版本/新源SHA保留，
不将Git commit误认为本地证据备份。63已修均已获结果确认；本次只提交，不push、
不Start F0061或M2，后续仍沿TASK_QUEUE#crp-next恢复唯一入口。
