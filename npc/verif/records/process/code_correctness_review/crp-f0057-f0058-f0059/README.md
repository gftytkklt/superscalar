# CRP F0057/F0058/F0059 — ELF预检与共享页加载

## 整体计划与启动（2026-10-20）

用户“提交修改后继续CRP修复”授权：先确认提交F0061及会话规则，再执行本组一个单元。F0061实际root 0ddd35c，7文件身份/提交核对，nested8101fad内容干净且850既有mode保持；不恢复旧连续提交授权，不push/安装/M2推进。

目标/范围：F0057核定ELF头/程序表格式、固定尺寸读及短读；F0058检查文件/虚址算术、用户域/栈、entry并在进程替换前完成预检；F0059复用同VA物理页，保留合法同页各段文件/BSS。当前RV64/NEMU/VME为真实验收目标；保留非VME历史载入模式但不引入通用权限/copyin/动态链接/内存回收或OOM恢复。

阶段：本组为一个独立可验证单元，沿用CRP总体计划，不另造业务Phase。先核对现有ELF几何/失败传播，再最小实现、逐项定向验证、最终共享回归和收尾。

交付/验收：生产最小补丁、完整内嵌diff及语句说明；原版动态失败和host ASan/UBSan的头/表/尺寸/溢出/短读/栈内核域/entry反例，拒绝无PCB/页表/分配变化；合法同页非重叠段、反序和BSS内容。实际RV64坏文件exec返回ENOEXEC后原程序继续，再exec真实合法同页载入。标准nanos update→run三前台/hello，同版链接/盘内容和最终生产身份，目视、正反补丁和清理留档。CPU/RT不消费nanos及新增只读AM查询，按闭包不重跑。

已知事实：正式旧盘nterm仍为0x83000000，其他启动程序0x40000000；先检查既有update能否产出VME一致ELF，不直接改正式盘或从历史隔离回归推定已修F0074。若标准更新后仍有冲突或需要新失败协议/范围策略则停止裁决；正常更新能解决时继续本组，不把F0074自动记已修。

结束节点：本组完整验证/记录/清理后停止，等待结果确认/commit。任何安装/真实策略待决即停，不自动新组。引用2026-10-20读取[课程加载器](https://ysyx.oscc.cc/docs/ics-pa/3.3.html#加载第一个用户程序)与[gABI程序头](https://gabi.xinuos.com/elf/07-pheader.html)：PT_LOAD文件字节及尾部零填充，以实际本地简化内核契约为边界。

## 实施结果 — Completed，结果确认与commit Pending

本组F0057/F0058/F0059在当前RV64/NEMU/VME范围完成。5份根生产源码199增83删；包括loader、fs.h/fs.c、disk.c及AM NEMU vme.c两个只读helper。原119项审阅记录及旧完成快照不重写；累计67已修/52未修完，前64已确认提交0ddd35c，本组3项等待结果确认/提交。root HEAD `0ddd35c1b4deeaa14a6b771dd3f96bcc6516d10f`；nested8101fad内容干净/既有850mode保持，两index为空，Working tree contains uncommitted CRP repair/documentation changes。

| 验收 | 最终结果 / local证据 |
|---|---|
| 原版见证 | 从本组旧commit重建实际loader。错误class仍被接受、共享页前段丢失，各在ELF FAIL断言处exit1；e_phentsize=128实际写56B栈对象，ASan stack-buffer-overflow。没有把编译失败当动态见证。unit/before-vme-*.log |
| host最终 | ASan/UBSan，实际生产loader及实际Sv39 map/query函数体，仅硬件CSR/protect等边界stub。VME 50场景1998断言、非VME44/1031、raw-dummy非VME43/1029，共137场景4058断言。头/表尺寸、类型/版本、ph溢出/短读、文件及VA溢出、p_align、entry gap/BSS/非可执行/1与2字节失配、用户下界/栈/内核域；失败整个PCB/根页/arena不变且无protect/new_page/map。合法同页正反序、纯BSS、跨页、恰用户下界/恰栈底、空段/NULL参数。raw容量来自stub，不冒充实际磁盘几何或raw guest |
| 目标栈帧 | 实际riscv64-linux-gnu-gcc编译完整生产loader，-Werror=vla及-Werror=frame-larger-than=1024通过；context_uload静态288B、validate_elf480B、load_elf208B。只证明独立函数编译帧，不宣称完整内核调用链上界。frame-compile.json/log及loader-frame.su |
| 实际RV64坏映像 | public execve→libos→SYS_execve→context_uload，27个实际文件：格式/尺寸/ph表/段边界/溢出/短Ehdr/Phdr/数据/entry范围与对齐；另/dev/fb拒绝，共28次ENOEXEC，缺文件仍ENOENT，原用户局部数据继续读写/打印。测试专用wrap在context_uload返回前核对PCB字段、当前trap上下文、原用户根/中间/叶表指纹与heap.start均保持。27条ELF REJECT、28条ELF KERNEL KEEP。guest.c/kernel-elf.c/bad-cases/guest-result |
| 实际同页执行 | 独立构造完整ELF64/EM_RISCV/ET_EXEC，两段合法页同余、字节不重叠；首段代码实际执行并检查第二段16文件字节/48B BSS及首段16B BSS，输出ELF SHARED PASS，GOOD TRAP/exit0，6,348,572条指令。不是仅核对虚拟stub内容；host另测Phdr反序。shared.S/prepare-guest.py/guest-run/helper符号及loader反汇编 |
| 标准消费者 | 隔离副本沿既有make -j4 ARCH=riscv64-nemu git_commit= update exit0/27.733秒→run。最终nanos-final2约53.446秒，PAL/NTerm/NSlider三前台、10真实SDL键事件、8帧已目视；qzx not found后prompt、slide0→1→0的SHA复原、PAL/Enter继续动画，hello36→159。观察结束自有进程组SIGTERM/make-15，不是guest正常退出/物理音视频/长期验收 |
| 几何/身份/归档 | 108extent连续且逐字节等于当前安装文件，48个新盘ELF全部满足用户域/entry及段几何；四启动ELF实际新链接等于安装。263项preclean全PASS、4891源/配置身份、851构建身份。5源内嵌完整diff正反应用精确；7种oracle缺失/重复/非零/混BAD等拒绝；正式旧盘/header/kernel/配置/NEMU/proc均保持入口身份 |

补测发现并修正了测试夹具的增量失效：新增两种entry对齐反例时，BAD_COUNT从25到27的CFLAGS变化没有触发测试应用C文件重编，oracle正确拒绝“少跑两例但GOOD”的旧结果。随后将数量写入生成的测试源，重新构造盘/内核，最终27文件逐项实际执行并通过；不改生产Make/日常流程，不将该次失败算最终通过。初期25例/中间标准run仅为历史，最终以guest-result及nanos-final2为准。收尾器初按带逗号指令数匹配未格式化NEMU日志，改为解析数字后通过；末尾打印曾硬编码25，已改动态打印，真正验收一直按fixture数量和逐条marker，不以打印摘要作PASS。

## 限制、F0074与停点

当前正式旧盘nterm仍为0x83000000，严格loader会拒绝它；本轮保护正式忽略资产未直接更新。隔离标准update确已生成0x40010608的nterm及48兼容ELF，说明现有update→run链可满足本组验收；这不等于F0074正式资产一致性已闭环，F0074仍未修，后续范围只由TASK_QUEUE唯一入口维护。没有放宽用户域以迁就旧镜像，也不声称历史镜像对应本轮源码。

无通用copyin/并发盘修改/动态链接/权限回收或OOM回滚；预检后的真实盘变化和物理耗尽继续受控停止。当前NEMU只读helper不扩展NPC VME/MPE能力；CPU/RT/REF不调用新增helper且不消费nanos，按调用闭包未重跑。未测NPC nanos/其他ISA/非VME或raw真实guest/全配置/人工GUI/长期；host不能替代这些NotRun。

完整验证、目视及归档后清理9544项、837197961逻辑字节（约798.4MiB），零tracked删除；仅本组隔离源码/构建/盘/诊断payload和截图、观察库，不跟随目录symlink，不删除正式资产。cleanup-plan/receipt保存删除前路径/字节/SHA及预期缺失，旧截图不可再直接查看。保留最小脚本/测试源/配置/真实命令/结果/身份/patch；local/.agent不随commit备份。

本轮停止，等待结果确认与精确根提交，不自动提交新组/push/新组/M2。可在当前对话继续：当前修复及唯一入口已完整留档，下一单元仍是同一ELF产物链；提交落档时仍按AGENTS第6条重新评估会话建议。

再生：从本组旧commit加repair.patch取得最终源码，沿entry中的现有资产/工具身份，在全新隔离目录运行local/unit.py→prepare-runtime.py→prepare-guest.py→run-guest.py→standard-path/run-standard.local nanos-final2→visualize.py→archive.py→check.py，实际目视后cleanup.py和final-check.py。frame编译精确argv在frame-compile.json。final-runtime.py记录中间补测顺序，不是从清理后直接重跑的冷启动入口；不能以未来HEAD或缺失旧盘作为基线。无下载/安装。

<a id="repair-diff"></a>
## 最终完整代码diff与语句说明

仓库：根ysyx-workbench。旧完整commit：`0ddd35c1b4deeaa14a6b771dd3f96bcc6516d10f`；新版本：`WORKTREE（2026-10-20，未提交）`。各相对路径与新SHA256：

- `abstract-machine/am/src/riscv/nemu/vme.c`：`b9568db08f09f75c87003b8bd55011421870aed72bc464227c2e3d7c9c7c14db`
- `nanos-lite/include/fs.h`：`14b85116d7f5b8186d8aa7abc21091037ae96c4a3ba9b792304c6f4af7f2ba8d`
- `nanos-lite/src/disk.c`：`64cb8d3576021e93bbcfe57c1774eda1cf36f590f1fee96e14cbc919b7c292f8`
- `nanos-lite/src/fs.c`：`fd3fc57ca0d55c662b04b03e5dbb746f80c0e2ff4ea7249f20c28e7972dfc0eb`
- `nanos-lite/src/loader.c`：`d4c1ec4339ce2493aa56c925e50fb0066b46f9377fed5e24bf0070ce7cf01590`

F0057：`image_open`以固定fd保持已检查映像，`fs_filesz`仅接受普通文件、拒绝设备，missing仍为-ENOENT；不合法格式/读数为-ENOEXEC。`image_read`先减法判界再固定长度读取，并验证seek/实际读数；`validate_elf`核对本机构建class、小端、版本、machine、ET_EXEC、Ehdr/Phdr尺寸与完整程序表，phnum使用除法边界避免乘加回绕。raw TEST_DUMMY用`disk_size`的已有设备/嵌入容量作上界，同样使用固定对象读数；不是新Make入口。

F0058：`p_filesz <= p_memsz`、文件范围及`UINTPTR_MAX - va`检查均先于加法；非空段再查roundup可表示和AM返回用户域减同一STACK_SIZE。空段不分配、不更新break；不引入0字节虚拟映射。对齐检查约束页同余及有效p_align；当前RISC-V IALIGN32要求entry四字节对齐，且entry属于带PF_X的文件字节。PT_INTERP/PT_DYNAMIC不属于既有静态加载契约而拒绝。逐段用256B固定scratch读取全部声明内容，所有预检通过才protect/清PCB/分配栈；经现有sys_execve/libos传播ENOEXEC，原程序可继续。后续单核无yield、固定盘不变是重读成立的前提；预检后异常I/O及物理OOM仍受控停止，不伪称通用回滚/并发磁盘事务。

F0059：`__am_lookup_page`只读当前Sv39三级表；`load_elf`先查询VA页，仅缺页才new_page/清页/map，已有页直接复用。只拷`f0..f1`文件交集、清`z0..z1`段BSS，保留同页其他非重叠段与不相关字节。逐Phdr顺序处理，零长度段跳过，最高实际末端重建brk_start/page-aligned max_brk。新只读用户域/查询helper只由当前NEMU VME实现和loader调用，标准AM map(void)不变；共享map/CPU/RT行为未改。页前后padding清零是新页初始化，不改既有段RWXU映射或F0029权限待决。

`context_uload`保留F0061预算先于fs及复制全部argv/envp后才载入的次序；最终GPRx仍是16字节对齐的initial_sp。naive批处理无错误返回协议，坏映像受控panic而不跳未知entry；当前FG路径返回错误。非VME只证明尺寸/算术与host直接载入，不承诺其具备VME隔离。旧TEST_DUMMY/FILE与HAS_VME+NULL PCB不是有效历史组合，本组未新支持该组合；其他ISA/NPC VME未验收。

五文件完整diff在隔离临时目录正向应用精确等于最终生产源码，反向恢复旧commit；local/archive-validation.json记录路径/身份。不是框架上游原始差异，不把Git整文件新增当修复。

```diff
diff --git a/abstract-machine/am/src/riscv/nemu/vme.c b/abstract-machine/am/src/riscv/nemu/vme.c
index 917b65590a3dd9851ac80bbb346d34945fc62457..ba9f8661163723cb08225b4683328524e6252670 100755
--- a/abstract-machine/am/src/riscv/nemu/vme.c
+++ b/abstract-machine/am/src/riscv/nemu/vme.c
@@ -92,6 +92,25 @@ size_t __am_map_table_pages(AddrSpace *as, uintptr_t start, uintptr_t end) {
   return pages;
 }
 
+// Read-only loader helpers: inspect the supported user domain and reuse leaves.
+Area __am_user_area(void) {
+  return USER_SPACE;
+}
+
+void *__am_lookup_page(AddrSpace *as, uintptr_t va) {
+  PTE *pt = (PTE *)as->ptr;
+  for (int shift = 30; shift >= 12; shift -= 9) {
+    PTE pte = pt[(va >> shift) & 0x1ff];
+    if (!(pte & PTE_V)) return NULL;
+    // map() creates only 4 KiB leaves in this address space.
+    if (shift != 12 && (pte & (PTE_R | PTE_W | PTE_X))) return NULL;
+    uintptr_t pa = ((pte >> 10) & 0xfffffffff) << 12;
+    if (shift == 12) return (void *)pa;
+    pt = (PTE *)pa;
+  }
+  return NULL;
+}
+
 void map(AddrSpace *as, void *va, void *pa, int prot) {
   // Sv39 three-level page table: VPN[2]=va[38:30], VPN[1]=va[29:21], VPN[0]=va[20:12]
   uintptr_t vaddr = (uintptr_t)va;
diff --git a/nanos-lite/include/fs.h b/nanos-lite/include/fs.h
index 6f2183b383f55c3a29e72893e5e7fcf2497beb8b..14d21ab945f4fc24cbe8f53c64e8a6a09e099903 100755
--- a/nanos-lite/include/fs.h
+++ b/nanos-lite/include/fs.h
@@ -10,6 +10,8 @@ int fs_open(const char *pathname, int flags, int mode);
 long fs_read(int fd, void *buf, size_t len);
 long fs_lseek(int fd, long offset, int whence);
 int fs_close(int fd);
+// Size of a regular file, or -1 for invalid descriptors/devices.
+long fs_filesz(int fd);
 long fs_write(int fd, const void *buf, size_t len);
 size_t ramdisk_read(void *buf, size_t offset, size_t len);
 size_t ramdisk_write(const void *buf, size_t offset, size_t len);
diff --git a/nanos-lite/src/disk.c b/nanos-lite/src/disk.c
index 47a7442b33f568ec8b5e091c63f80014d8deabb0..8b89cb173ecfadec2902f0eedc48ba5c27fa181d 100644
--- a/nanos-lite/src/disk.c
+++ b/nanos-lite/src/disk.c
@@ -31,6 +31,15 @@ void init_disk() {
 #endif
 }
 
+// The raw TEST_DUMMY loader has no filesystem extent to bound its reads.
+size_t disk_size(void) {
+  if (!disk_present) return embed_size;
+  AM_DISK_CONFIG_T cfg = io_read(AM_DISK_CONFIG);
+  if (cfg.blksz <= 0 || cfg.blkcnt <= 0 ||
+      (size_t)cfg.blkcnt > SIZE_MAX / (size_t)cfg.blksz) return 0;
+  return (size_t)cfg.blksz * (size_t)cfg.blkcnt;
+}
+
 static size_t embed_read(void *buf, size_t offset, size_t len) {
   if (offset >= embed_size) return 0;
   if (len > embed_size - offset) len = embed_size - offset;
diff --git a/nanos-lite/src/fs.c b/nanos-lite/src/fs.c
index e6e3323390f1d3120ea0d72345ed0f2cd8372196..736831bdeeae1c0399367b544c94bf0f46645c38 100755
--- a/nanos-lite/src/fs.c
+++ b/nanos-lite/src/fs.c
@@ -155,6 +155,12 @@ long fs_lseek(int fd, long offset, int whence) {
   return fp_offt[fd];
 }
 
+long fs_filesz(int fd) {
+  if (fd < 0 || fd >= filenum || file_table[fd].read != NULL ||
+      file_table[fd].write != NULL || file_table[fd].size > (size_t)LONG_MAX) return -1;
+  return (long)file_table[fd].size;
+}
+
 int fs_close(int fd) {
   if (fd < 0 || fd >= filenum) { return -1; }
   fp_offt[fd] = 0;
diff --git a/nanos-lite/src/loader.c b/nanos-lite/src/loader.c
index b86091d31d628421ce584fccd926933d02827e46..32806788b6ab96a2869cdb99ef1cd116daaae0c2 100755
--- a/nanos-lite/src/loader.c
+++ b/nanos-lite/src/loader.c
@@ -11,94 +11,176 @@
 # define Elf_Phdr Elf32_Phdr
 #endif
 
-static uintptr_t loader(PCB *pcb, const char *filename) {
-  #ifdef TEST_DUMMY
-  Elf_Ehdr ehdr = {};
-  Elf_Phdr phdr = {};
-  // naive version: the disk image's first file is dummy
+// The image stays open between validation and loading. The fixed ramdisk is
+// unchanged during this single-core, non-yielding operation.
+typedef struct {
+  int fd;
+  size_t size;
+} ElfImage;
+
+#ifdef HAS_VME
+// Internal NEMU VME helpers; no change to the AM map() interface.
+extern Area __am_user_area(void);
+extern void *__am_lookup_page(AddrSpace *as, uintptr_t va);
+#endif
+
+static bool image_read(ElfImage *image, size_t offset, void *buf, size_t len) {
+  if (offset > image->size || len > image->size - offset) return false;
+#ifdef TEST_DUMMY
   size_t disk_read(void *buf, size_t offset, size_t len);
-  disk_read(&ehdr, 0, sizeof(ehdr));
-  assert(*(uint32_t*)&ehdr.e_ident == 0x464c457f);
-  uint64_t phoff = ehdr.e_phoff;
-  uint16_t phentsize = ehdr.e_phentsize;
-  for (uint16_t i=0;i< ehdr.e_phnum; i++){
-    disk_read(&phdr, phoff, phentsize);
-    if (phdr.p_type == PT_LOAD){
-      size_t filesz = phdr.p_filesz;
-      size_t vaddr = phdr.p_vaddr;
-      size_t offset = phdr.p_offset;
-      size_t memsz = phdr.p_memsz;
-      disk_read((void*)vaddr, offset, filesz);
-      memset((void*)vaddr + filesz, 0, memsz-filesz);
+  return disk_read(buf, offset, len) == len;
+#else
+  return fs_lseek(image->fd, offset, SEEK_SET) == (long)offset &&
+         fs_read(image->fd, buf, len) == (long)len;
+#endif
+}
+
+static void image_close(ElfImage *image) {
+#ifndef TEST_DUMMY
+  fs_close(image->fd);
+#endif
+}
+
+static bool read_phdr(ElfImage *image, const Elf_Ehdr *ehdr,
+                      size_t i, Elf_Phdr *phdr) {
+  return image_read(image, ehdr->e_phoff + i * sizeof(*phdr), phdr, sizeof(*phdr));
+}
+
+static bool validate_elf(ElfImage *image, Elf_Ehdr *ehdr) {
+  if (!image_read(image, 0, ehdr, sizeof(*ehdr))) return false;
+#ifdef __LP64__
+  const int elf_class = ELFCLASS64;
+#else
+  const int elf_class = ELFCLASS32;
+#endif
+#if defined(__riscv)
+  const int machine = EM_RISCV;
+#elif defined(__x86_64__)
+  const int machine = EM_X86_64;
+#elif defined(__i386__)
+  const int machine = EM_386;
+#elif defined(__mips__)
+  const int machine = EM_MIPS;
+#else
+  const int machine = EM_NONE;
+  return false;
+#endif
+  if (memcmp(ehdr->e_ident, "\177ELF", 4) != 0 ||
+      ehdr->e_ident[EI_CLASS] != elf_class ||
+      ehdr->e_ident[EI_DATA] != ELFDATA2LSB ||
+      ehdr->e_ident[EI_VERSION] != EV_CURRENT || ehdr->e_version != EV_CURRENT ||
+      ehdr->e_machine != machine || ehdr->e_type != ET_EXEC ||
+      ehdr->e_ehsize != sizeof(*ehdr) || ehdr->e_phentsize != sizeof(Elf_Phdr) ||
+      ehdr->e_phnum == 0 || ehdr->e_phnum == PN_XNUM ||
+      ehdr->e_phoff > image->size ||
+      ehdr->e_phnum > (image->size - ehdr->e_phoff) / sizeof(Elf_Phdr)) return false;
+
+#ifdef HAS_VME
+  Area user = __am_user_area();
+  uintptr_t lower = (uintptr_t)user.start;
+  uintptr_t upper = (uintptr_t)user.end;
+  if (upper < STACK_SIZE || lower >= upper - STACK_SIZE) return false;
+  upper -= STACK_SIZE;
+#endif
+  // Current RISC-V targets use IALIGN=32 (no compressed instructions).
+  if (machine == EM_RISCV && (ehdr->e_entry & 3)) return false;
+  bool entry_ok = false;
+  for (size_t i = 0; i < ehdr->e_phnum; i++) {
+    Elf_Phdr phdr;
+    if (!read_phdr(image, ehdr, i, &phdr)) return false;
+    // This loader supports static executables, without an interpreter/relocator.
+    if (phdr.p_type == PT_INTERP || phdr.p_type == PT_DYNAMIC) return false;
+    if (phdr.p_type != PT_LOAD) continue;
+    uintptr_t va = phdr.p_vaddr;
+    if (phdr.p_filesz > phdr.p_memsz || phdr.p_offset > image->size ||
+        phdr.p_filesz > image->size - phdr.p_offset ||
+        phdr.p_memsz > UINTPTR_MAX - va ||
+        ((va ^ phdr.p_offset) & (PGSIZE - 1)) != 0 ||
+        (phdr.p_align > 1 && ((phdr.p_align & (phdr.p_align - 1)) != 0 ||
+         ((va ^ phdr.p_offset) & (phdr.p_align - 1)) != 0))) return false;
+    uintptr_t end = va + phdr.p_memsz;
+    if (phdr.p_memsz && end > UINTPTR_MAX - (PGSIZE - 1)) return false;
+#ifdef HAS_VME
+    if (phdr.p_memsz && (va < lower || va >= upper || end > upper)) return false;
+#endif
+    // The entry must point to a file-backed instruction in an executable load.
+    if ((phdr.p_flags & PF_X) && ehdr->e_entry >= va &&
+        ehdr->e_entry - va < phdr.p_filesz) entry_ok = true;
+    // Read all declared bytes before replacing the old PCB/address space.
+    char scratch[256];
+    for (size_t done = 0; done < phdr.p_filesz;) {
+      size_t n = phdr.p_filesz - done;
+      if (n > sizeof(scratch)) n = sizeof(scratch);
+      if (!image_read(image, phdr.p_offset + done, scratch, n)) return false;
+      done += n;
     }
-    phoff += phentsize;
   }
-  return ehdr.e_entry;
-  #elif defined(TEST_FILE) || defined(TEST_NTERM) || defined(MULTIPROGRAM) || defined(TIME_SHARING) || defined(FG_PROCESS)
-  Elf_Ehdr ehdr = {};
-  Elf_Phdr phdr = {};
-  int fd = fs_open(filename, 0, 0);
-  if(fd<0){return -1;}
-  fs_read(fd, &ehdr, 64);
-  assert(*(uint32_t*)&ehdr.e_ident == 0x464c457f);
-  uint64_t phoff = ehdr.e_phoff;
-  uint16_t phentsize = ehdr.e_phentsize;
-  for (uint16_t i=0;i< ehdr.e_phnum; i++){
-    fs_lseek(fd, phoff, SEEK_SET);
-    fs_read(fd, &phdr, phentsize);
-    if (phdr.p_type == PT_LOAD){
-      size_t filesz = phdr.p_filesz;
-      size_t vaddr = phdr.p_vaddr;
-      size_t offset = phdr.p_offset;
-      size_t memsz = phdr.p_memsz;
-      #ifdef HAS_VME
-      // load the segment page by page: allocate a physical page, map it to the
-      // segment's virtual page, then copy the file content into the physical page
-      uintptr_t page_start = ROUNDDOWN(vaddr, PGSIZE);
-      for (uintptr_t va = page_start;
-           va < ROUNDUP(vaddr + memsz, PGSIZE); va += PGSIZE) {
-        void *pa = new_page(1);
+  return entry_ok;
+}
+
+static int image_open(ElfImage *image, Elf_Ehdr *ehdr, const char *filename) {
+#ifdef TEST_DUMMY
+  size_t disk_size(void);
+  image->fd = -1;
+  image->size = disk_size();
+#else
+  image->fd = fs_open(filename, 0, 0);
+  if (image->fd < 0) return -ENOENT;
+  long size = fs_filesz(image->fd);
+  if (size < 0) { image_close(image); return -ENOEXEC; }
+  image->size = size;
+#endif
+  if (validate_elf(image, ehdr)) return 0;
+  image_close(image);
+  return -ENOEXEC;
+}
+
+static uintptr_t load_elf(PCB *pcb, ElfImage *image, const Elf_Ehdr *ehdr) {
+  for (size_t i = 0; i < ehdr->e_phnum; i++) {
+    Elf_Phdr phdr;
+    panic_on(!read_phdr(image, ehdr, i, &phdr), "ELF changed after validation");
+    if (phdr.p_type != PT_LOAD || phdr.p_memsz == 0) continue;
+    uintptr_t vaddr = phdr.p_vaddr, end = vaddr + phdr.p_memsz;
+    uintptr_t file_end = vaddr + phdr.p_filesz;
+#ifdef HAS_VME
+    for (uintptr_t va = ROUNDDOWN(vaddr, PGSIZE); va < ROUNDUP(end, PGSIZE); va += PGSIZE) {
+      void *pa = __am_lookup_page(&pcb->as, va);
+      if (pa == NULL) {
+        pa = new_page(1);
         panic_on(pa == NULL, "Out of physical pages loading ELF");
+        memset(pa, 0, PGSIZE);
         map(&pcb->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);
-
-        // copy the file part of this page (if any). Note the segment may start
-        // mid-page, so the file offset must be computed from the virtual address.
-        if (va < vaddr + filesz) {
-          uintptr_t fstart = (va > vaddr) ? va : vaddr;   // first vaddr in page that has file data
-          size_t n = (vaddr + filesz - fstart < PGSIZE - (fstart - va)) ?
-                     (vaddr + filesz - fstart) : (PGSIZE - (fstart - va));
-          if (n > 0) {
-            fs_lseek(fd, offset + (fstart - vaddr), SEEK_SET);
-            fs_read(fd, (char *)pa + (fstart - va), n);
-          }
-        }
-
-        // zero the bss part of this page (if any)
-        uintptr_t z0 = (vaddr + filesz > va) ? (vaddr + filesz) : va;
-        uintptr_t z1 = (vaddr + memsz < va + PGSIZE) ? (vaddr + memsz) : (va + PGSIZE);
-        if (z1 > z0) memset((char *)pa + (z0 - va), 0, z1 - z0);
       }
-      // record the peak program break (page-aligned) for mm_brk()
-      uintptr_t brk = ROUNDUP(vaddr + memsz, PGSIZE);
-      if (brk > pcb->max_brk) pcb->max_brk = brk;
-      if (vaddr + memsz > pcb->brk_start) pcb->brk_start = vaddr + memsz;
-      #else
-      fs_lseek(fd, offset, SEEK_SET);
-      fs_read(fd, (void *)vaddr, filesz);
-      memset((void *)(vaddr + filesz), 0, (memsz-filesz));
-      #endif
+      uintptr_t f0 = (va > vaddr ? va : vaddr);
+      uintptr_t f1 = (va + PGSIZE < file_end ? va + PGSIZE : file_end);
+      if (f1 > f0) {
+        panic_on(!image_read(image, phdr.p_offset + (f0 - vaddr),
+                            (char *)pa + (f0 - va), f1 - f0), "ELF changed after validation");
+      }
+      uintptr_t z0 = (file_end > va ? file_end : va);
+      uintptr_t z1 = (end < va + PGSIZE ? end : va + PGSIZE);
+      if (z1 > z0) memset((char *)pa + (z0 - va), 0, z1 - z0);
     }
-    phoff += phentsize;
+    uintptr_t brk = ROUNDUP(end, PGSIZE);
+    if (brk > pcb->max_brk) pcb->max_brk = brk;
+    if (end > pcb->brk_start) pcb->brk_start = end;
+#else
+    panic_on(!image_read(image, phdr.p_offset, (void *)vaddr, phdr.p_filesz),
+             "ELF changed after validation");
+    memset((void *)file_end, 0, end - file_end);
+#endif
   }
-  return ehdr.e_entry;
-  #else
-  panic("No test macro defined for loader");
-  #endif
+  image_close(image);
+  return ehdr->e_entry;
 }
 
 void naive_uload(PCB *pcb, const char *filename) {
   Log("Open %s", filename);
-  uintptr_t entry = loader(pcb, filename);
+  ElfImage image;
+  Elf_Ehdr ehdr;
+  int status = image_open(&image, &ehdr, filename);
+  panic_on(status < 0, "Invalid executable");
+  uintptr_t entry = load_elf(pcb, &image, &ehdr);
   Log("Jump to entry = %p", entry);
   ((void(*)())entry) ();
 }
@@ -125,11 +207,10 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
       count_args(envp, &envc, &used) < 0) return -E2BIG;
   // The page-aligned stack top and STACK_SIZE are multiples of 16.
   // Rounding a validated used <= STACK_SIZE up to 16 still fits the stack.
-  // Reject a missing executable before replacing the caller's address space
-  // or context. fs_open() uses a fixed file table; the loader opens it again.
-  int fd = fs_open(filename, 0, 0);
-  if (fd < 0) return -ENOENT;
-  fs_close(fd);
+  ElfImage image;
+  Elf_Ehdr ehdr;
+  int status = image_open(&image, &ehdr, filename);
+  if (status < 0) return status;
 #ifdef HAS_VME
   protect(&pcb->as);
 #endif
@@ -192,8 +273,7 @@ int context_uload(PCB *pcb, const char *filename, char *const argv[], char *cons
   envp_addr[envc] = 0;
 
   // load the new program (may overwrite the calling process's static data)
-  uintptr_t entry = loader(pcb, filename);
-  assert(entry != (uintptr_t)-1); // preflight found this file in the fixed table
+  uintptr_t entry = load_elf(pcb, &image, &ehdr);
   Log("Jump to entry = %p", entry);
 
   Context *cp = ucontext(&pcb->as, kstack, (void *)entry);
```
