# CRP F0076 — 内核错误码与libos/newlib errno契约

2026-10-20，前F0075已确认实际015841a；用户“提交后继续”授权本单元，后续明确选择A：已实现内核返回具体-errno，libos统一转失败-1并写低层全局errno，newlib更新请求的_reent。96已修/23未修完，本组Active，不推进M2。

## 本单元计划

范围：nanos fs/mm现有失败原因与libos/src/syscall.c（syscall.c仅核调用链，无生产修改）；不实现缺失POSIX能力、线程/TLS或修改Make入口。exec保留ENOENT/ENOEXEC/E2BIG等既有原因；open缺路径ENOENT，读写/close坏fd EBADF，seek坏fd EBADF/非法位置或whence EINVAL，brk不能满足ENOMEM；libos自有sbrk算术拒绝也用ENOMEM。低层_fstat占位只报告ENOSYS，不把assert/exit占位改成可运行能力。

一个单元：现源/旧反例→最小实现→host普通与san实际newlib默认/独立_reent及成功错误槽保持→真实RV64+nanos调用链与标准update→run三前台/hello。归档全部实际修复diff/逐句说明、正反字节核验、命令/退出/身份与限制，保护正式配置/引擎/盘/header，验证后清理隔离产物。交付本报告/.gitignore/local最小配方、代码、records索引/.agent。完成后停等结果确认/commit，不push/安装/下一组；未决契约按WORKFLOW_POLICY§3裁决。A已获用户明确批准，无待决安装。

依据：newlib reent wrapper明确undef errno并使用extern int errno，在失败时写ptr->_errno；__errno访问_REENT默认槽。当前libos exec却写宏errno，其余多数失败不写低层槽。nanos fs多种失败共用-1，不能直接当Linux -errno。参考[讲义系统调用](https://ysyx.oscc.cc/docs/ics-pa/3.3.html)（2026-10-20访问）只作为libos/内核调用分层背景，具体错误契约以本次A裁决和现源为准。
<a id="f0076-final-20261020"></a>
## 最终实现与验收（2026-10-20）

F0076功能修复与验收完成，结果确认/本组commit Pending。累计97完全已修/22未修完，前96已确认提交015841a；HEAD未变，Working tree contains uncommitted F0076 repair/documentation changes。无本组commit/push/安装/下一组/M2。

### 实现与具体语句

根仓三份生产文件45增36删（实际统计以local/repair.patch与Git为准），mode100755保持；newlib源码未改、不需要nested源码提交。

- `fs_open`只在查表失败出口返回`-ENOENT`，内部`fs_open_normalized`的查表哨兵仍是-1；loader原`fd<0`分支保持。读写/close/seek的fd检查返回`-EBADF`；seek在非法whence、负偏移超下界、加法溢出或超文件范围时返回`-EINVAL`，仍先完成所有检查再写fp_offt。正常返回值、fd模型/路径归一化及盘读写行为不改，fs_filesz仍是内部-1哨兵。
- `mm_brk`所有既有失败出口返回`-ENOMEM`；请求范围、页数/表页checked算术和先预留再映射顺序保持。失败不推进program_break、max_brk、物理堆游标或PTE；非VME分支原有能力保持。本组没有新增回收/完整exec OOM恢复。
- libos在包含errno.h后`#undef errno; extern int errno;`，写newlib已存在于reent.c的低层全局槽，不写默认`_impure_ptr`。`syscall_result`仅在ret<0写`errno=-ret`并返回-1，成功直接返回原值，不改低层错误槽。open/read/write/close/lseek/gettimeofday/execve共用该转换；exec原ENOENT/ENOEXEC/E2BIG等原因保持。
- `_sbrk`自有current低于end、正加溢出、负减越界分支设置ENOMEM；内核brk经同一转换，仍只在ret==0发布新的program_break并返回旧地址。负增量和INTPTR_MIN处理不变。
- `_fstat`仍不提供stat能力，只在现有-1之前写ENOSYS，供`_fstat_r`复制；其余assert/exit占位、public dup2/ioctl没有纳入本项。newlib `_xxx_r`在调用前清低层槽，只在-1且低层非零时写请求的`ptr->_errno`，因此显式独立对象失败不会改默认对象，成功保留请求对象错误哨兵；public open/fopen/execve经默认对象链。

### 本次验证与边界

| 项目 | 结果与实际证明范围 |
|---|---|
| 旧libos host反例与最终同判据 | 从015841a读取旧libos；只替换硬件asm块为可控返回、重命名导出符号与低层errno以避宿主TLS冲突，使用实际newlib八个reent wrapper。旧源普通/san各157检查72失败、exit1；最终普通/san各157检查零失败、exit0。默认/独立对象、open/read/write/close/seek/exec/sbrk/fstat错误及成功哨兵、sbrk上下界/INTPTR_MIN/不发syscall/状态保持均覆盖。最终八条编译运行命令符合预期；LSan关闭。 |
| ABI与真实RV64 guest | 实际Navy Makefile编译guest并链接当前newlib/libos；实际nanos syscall→fs/mm/loader及AM/NEMU硬件ecall。123检查通过，GOOD TRAP、exit0；默认与独立_reent、public open/fopen/read/lseek/execve、缺文件ENOENT/坏fd EBADF/非法seek EINVAL/坏ELF ENOEXEC/参数过长E2BIG/内核和本地sbrk ENOMEM/fstat ENOSYS，成功read/ELF魔数/zero/write/time/sbrk增减/close不污染错误槽。真实libos.o为U errno，无U __errno。 |
| 内核错误码旧/新对照 | 同一最终guest+libos，仅内核fs/mm切015841a旧源：raw open/read/seek-fd/seek-arg/brk均-1，缺路径最终errno变1而不是2，准确BAD/exit1拒绝；最终内核raw为-2/-9/-9/-22/-12，正确PASS。这是故意的旧内核/新libos混配反例，不冒称纯旧全栈回归；两端需同步update/run。 |
| 内存容量失败保持 | 复用F0089最小内核测试（只将期望-1改-ENOMEM），实际Sv39页表fingerprint/物理heap/max_brk前后核对；无数据页容量与仅够数据但少表页两种失败均-12，500页附近跨2MiB测试最终492数据页，状态与PTE不变。只在测试内核用原未支持SYS_getpid号进入此诊断，不新增生产syscall能力。测试内核sys_exit只作halt/GOOD或BAD判定，文件身份及差异可由real.py重建。 |
| 标准update→run消费者 | 最终隔离update exit0，随后标准run三前台8帧实际目视、10个SDL按键：nterm qzx后command not found并返回prompt，slides0→1→0且回0像素SHA相同，PAL初始/返回/Enter继续渲染；hello37→166。53.452秒后自有进程组SIGTERM，make -15不是guest正常退出。108extent逐字节匹配各安装文件、尾部仅padding，4个前后台ELF安装与链接身份匹配。 |
| 归档/保护/身份 | 179项preclean PASS，9346输入与产物身份固定；三份生产/标准源和目标fs/mm同SHA、目标与标准NEMU相同身份。完整三文件diff正向得最终字节、反向恢复015841a旧字节；mode100755。五项正式配置/用户引擎/盘/header/内核bin保持entry SHA，root index空。截图已在清理前实际查看。 |

测试夹具的修正/中间结果单独保留：首次guest漏加libos/src include，误读宿主syscall.h，编译失败后补入隔离测试INC_PATH。初始host未加newlib的_COMPILING_NEWLIB，产生低层隐式声明警告；复核后仅wrapper加与实际libc相同标识，最终host编译日志无该告警并重测正反。曾把标识套到libos导致既有_write const与_gettimeofday原型冲突，编译失败原日志保留，改为分别使用实际编译边界，未因此修改生产ABI。最终host/guest判据未降低。

中间候选对public dup2/ioctl写低层ENOSYS不属于本项最终范围，已撤回两条赋值；最终源已重新执行host/实际RV64/隔离update→run，不拿先前中间源结果充作最终身份。final-source-changes.json列351项隔离输入变化，只有libos这一源变化，其余是正常生成的busybox产物/fsimg；prepare按.git/build目录排除，不能据此宣称排除了所有位于源码树内的旧构建产物。标准update及实际安装匹配是本次消费者判据。

一次补测命令遗漏环境参数，隔离nanos Makefile继承NAVY_HOME进入主工程，执行libbmp/libc两个薄归档ar后在libminiSDL timer/audio编译遇ccache只读exit2，未到install/ramdisk发布。失败日志update-final-source.log保留；两个薄归档在entry无原始身份，不声称逐字节不变、不擅自恢复未知原物。五项正式运行资产哈希均未变。随后显式传完整fixture env、CCACHE_DISABLE=1执行update-final-isolated及最终标准run成功；未安装/下载/修改系统。消费者第一次与定向目标曾共享AM构建目录，无失败；最终目标与标准的重新验证按顺序完成，固定同源同执行器身份。

### 完整框架/OS修复diff

所属根仓ysyx-workbench，以下路径相对仓根。旧完整commit `015841a4a42ba8b0c97f31ba508b580c17b665bb`；新为2026-10-20未提交工作树，具体字节身份：

| 文件 | 旧SHA256 | 新SHA256 |
|---|---|---|
| nanos-lite/src/fs.c | fd3fc57ca0d55c662b04b03e5dbb746f80c0e2ff4ea7249f20c28e7972dfc0eb | 8e9402a6fd9b547dca7f720b4fa0475104cbedf3076625b2b73b562f888f8fb9 |
| nanos-lite/src/mm.c | 3de04775726e379707fd7692accbc193a131dd43f014bd84927e02bc7362bfe4 | 0c25b302ec1d9f18699fb8cad56c734dc3661f4a26255a1bb0805c324a22a259 |
| navy-apps/libs/libos/src/syscall.c | 819a097066a66f69d5e2eab029e33b0c62870d8d9848231e655a511cc20e4089 | 0fe52fc62f01bd6cb9c6c92a97ec36439fd54d5eaee90f912025d9c07cc08f32 |

```diff
diff --git a/nanos-lite/src/fs.c b/nanos-lite/src/fs.c
index 736831bdeeae1c0399367b544c94bf0f46645c38..b51bc003fd0a65b8f9987c3a6773e4daa7c6f9b0 100755
--- a/nanos-lite/src/fs.c
+++ b/nanos-lite/src/fs.c
@@ -1,5 +1,6 @@
 #include <fs.h>
 #include <limits.h>
+#include <errno.h>
 
 typedef size_t (*ReadFn) (void *buf, size_t offset, size_t len);
 typedef size_t (*WriteFn) (const void *buf, size_t offset, size_t len);
@@ -88,13 +89,13 @@ int fs_open(const char *pathname, int flags, int mode) {
     fp_offt[fd] = 0;   // open 语义：文件偏移量从 0 开始（覆盖 execve 后残留的偏移量）
     return fd;
   }
-  // POSIX semantics: return -1 instead of panicking. Applications like
-  // ONScripter probe optional files (cursors, fonts) and tolerate failures.
-  return -1;
+  // libos converts the cause to the newlib errno ABI; applications such as
+  // ONScripter can still tolerate missing optional files (cursors, fonts).
+  return -ENOENT;
 }
 
 long fs_read(int fd, void *buf, size_t len) {
-  if (fd < 0 || fd >= filenum) { return -1; }
+  if (fd < 0 || fd >= filenum) { return -EBADF; }
   long rd_offt = fp_offt[fd] + file_table[fd].disk_offset;
   long offt_incr = 0;
   // normal file
@@ -112,7 +113,7 @@ long fs_read(int fd, void *buf, size_t len) {
 }
 
 long fs_write(int fd, const void *buf, size_t len) {
-  if (fd < 0 || fd >= filenum) { return -1; }
+  if (fd < 0 || fd >= filenum) { return -EBADF; }
   long wr_offt = fp_offt[fd] + file_table[fd].disk_offset;
   long offt_incr = 0;
   if (file_table[fd].write == NULL) {
@@ -129,28 +130,28 @@ long fs_write(int fd, const void *buf, size_t len) {
 }
 
 long fs_lseek(int fd, long offset, int whence) {
-  if (fd < 0 || fd >= filenum) { return -1; }
+  if (fd < 0 || fd >= filenum) { return -EBADF; }
   size_t base;
   switch(whence) {
     case SEEK_SET: base = 0; break;
     case SEEK_CUR:
-      if (fp_offt[fd] < 0) { return -1; }
+      if (fp_offt[fd] < 0) { return -EINVAL; }
       base = (size_t)fp_offt[fd];
       break;
     case SEEK_END: base = file_table[fd].size; break;
-    default: return -1;
+    default: return -EINVAL;
   }
   size_t next;
   if (offset < 0) {
     // Form the magnitude without negating LONG_MIN.
     size_t back = (size_t)(-(offset + 1)) + 1;
-    if (back > base) { return -1; }
+    if (back > base) { return -EINVAL; }
     next = base - back;
   } else {
-    if (base > (size_t)LONG_MAX - (size_t)offset) { return -1; }
+    if (base > (size_t)LONG_MAX - (size_t)offset) { return -EINVAL; }
     next = base + (size_t)offset;
   }
-  if (next > file_table[fd].size || next > (size_t)LONG_MAX) { return -1; }
+  if (next > file_table[fd].size || next > (size_t)LONG_MAX) { return -EINVAL; }
   fp_offt[fd] = (long)next;
   return fp_offt[fd];
 }
@@ -162,7 +163,7 @@ long fs_filesz(int fd) {
 }
 
 int fs_close(int fd) {
-  if (fd < 0 || fd >= filenum) { return -1; }
+  if (fd < 0 || fd >= filenum) { return -EBADF; }
   fp_offt[fd] = 0;
   return 0;
 }
diff --git a/nanos-lite/src/mm.c b/nanos-lite/src/mm.c
index ad6ff094330593b18fbc9491fe3977d3e8788514..c626aa8afd28d20a95629a25f1222146d274b1c9 100755
--- a/nanos-lite/src/mm.c
+++ b/nanos-lite/src/mm.c
@@ -1,5 +1,6 @@
 #include <memory.h>
 #include <proc.h>
+#include <errno.h>
 
 void* new_page(size_t nr_page) {
   uintptr_t cursor = (uintptr_t)heap.start;
@@ -42,32 +43,32 @@ void free_page(void *p) {
 /* The brk() system call handler. */
 int mm_brk(uintptr_t brk) {
 #ifdef HAS_VME
-  if (current == NULL) return -1;
+  if (current == NULL) return -ENOMEM;
   uintptr_t lo = (uintptr_t)current->as.area.start;
   uintptr_t hi = (uintptr_t)current->as.area.end;
-  if (hi < lo || hi - lo < STACK_SIZE) return -1;
+  if (hi < lo || hi - lo < STACK_SIZE) return -ENOMEM;
   uintptr_t limit = hi - STACK_SIZE;
   if (current->brk_start < lo || current->brk_start > limit ||
       current->max_brk < current->brk_start || current->max_brk > limit ||
       brk < current->brk_start || brk > limit ||
       brk > UINTPTR_MAX - (PGSIZE - 1) ||
-      current->max_brk > UINTPTR_MAX - (PGSIZE - 1)) return -1;
+      current->max_brk > UINTPTR_MAX - (PGSIZE - 1)) return -ENOMEM;
   if (brk > current->max_brk) {
     uintptr_t start = ROUNDUP(current->max_brk, PGSIZE);
     uintptr_t end = ROUNDUP(brk, PGSIZE);
-    if (end > limit) return -1;
+    if (end > limit) return -ENOMEM;
     size_t pages = (end - start) / PGSIZE;
     if (pages == 0) {
       current->max_brk = brk;
       return 0;
     }
-    if (pages > SIZE_MAX / 4) return -1;
+    if (pages > SIZE_MAX / 4) return -ENOMEM;
     // Other existing AM targets have at most three intermediate table levels.
     size_t tables = __am_map_table_pages ?
       __am_map_table_pages(&current->as, start, end) : 3 * pages;
-    if (tables > SIZE_MAX - pages) return -1;
+    if (tables > SIZE_MAX - pages) return -ENOMEM;
     void *data = new_page(pages + tables);
-    if (data == NULL) return -1;
+    if (data == NULL) return -ENOMEM;
     table_next = (uintptr_t)data + pages * PGSIZE;
     table_end = table_next + tables * PGSIZE;
     for (uintptr_t va = start; va < end; va += PGSIZE) {
diff --git a/navy-apps/libs/libos/src/syscall.c b/navy-apps/libs/libos/src/syscall.c
index f48b59df0564037a166d1ba12aa3cb7b1f1f8b71..c1590f1cf930b0855cd6865388e1596aa6b33550 100755
--- a/navy-apps/libs/libos/src/syscall.c
+++ b/navy-apps/libs/libos/src/syscall.c
@@ -7,6 +7,18 @@
 #include <stdint.h>
 #include "syscall.h"
 
+// newlib's _xxx_r wrappers copy this low-layer slot into the requested _reent.
+#undef errno
+extern int errno;
+
+static intptr_t syscall_result(intptr_t ret) {
+  if (ret < 0) {
+    errno = (int)-ret;
+    return -1;
+  }
+  return ret;
+}
+
 // helper macros
 #define _concat(x, y) x ## y
 #define concat(x, y) _concat(x, y)
@@ -73,28 +85,28 @@ void _exit(int status) {
 }
 
 int _open(const char *path, int flags, mode_t mode) {
-  return _syscall_(SYS_open, (intptr_t)path, flags, mode);
+  return syscall_result(_syscall_(SYS_open, (intptr_t)path, flags, mode));
 }
 
 long _write(int fd, void *buf, size_t count) {
-  return _syscall_(SYS_write, fd, (intptr_t)buf, count);
+  return syscall_result(_syscall_(SYS_write, fd, (intptr_t)buf, count));
 }
 
 void *_sbrk(intptr_t increment) {
   uintptr_t current = (uintptr_t)program_break;
   uintptr_t base = (uintptr_t)&end;
   uintptr_t next;
-  if (current < base) return (void *)-1;
+  if (current < base) { errno = ENOMEM; return (void *)-1; }
   if (increment >= 0) {
-    if ((uintptr_t)increment > UINTPTR_MAX - current) return (void *)-1;
+    if ((uintptr_t)increment > UINTPTR_MAX - current) { errno = ENOMEM; return (void *)-1; }
     next = current + (uintptr_t)increment;
   } else {
     // Unsigned negation also handles INTPTR_MIN without signed overflow.
     uintptr_t decrement = (uintptr_t)0 - (uintptr_t)increment;
-    if (decrement > current - base) return (void *)-1;
+    if (decrement > current - base) { errno = ENOMEM; return (void *)-1; }
     next = current - decrement;
   }
-  int ret = _syscall_(SYS_brk, (intptr_t)next, 0, 0);
+  intptr_t ret = syscall_result(_syscall_(SYS_brk, (intptr_t)next, 0, 0));
   if (ret == 0){
     void* addr = program_break;
     program_break = (void *)next;
@@ -104,35 +116,30 @@ void *_sbrk(intptr_t increment) {
 }
 
 long _read(int fd, void *buf, size_t count) {
-  return _syscall_(SYS_read, fd, (intptr_t)buf, count);
+  return syscall_result(_syscall_(SYS_read, fd, (intptr_t)buf, count));
 }
 
 int _close(int fd) {
-  return _syscall_(SYS_close, fd, 0, 0);
+  return syscall_result(_syscall_(SYS_close, fd, 0, 0));
 }
 
 off_t _lseek(int fd, off_t offset, int whence) {
-  return _syscall_(SYS_lseek, fd, offset, whence);
+  return syscall_result(_syscall_(SYS_lseek, fd, offset, whence));
 }
 
 int _gettimeofday(struct timeval *tv, struct timezone *tz) {
-  return _syscall_(SYS_gettimeofday, (intptr_t)tv, (intptr_t)tz, 0);
-  return 0;
+  return syscall_result(_syscall_(SYS_gettimeofday, (intptr_t)tv, (intptr_t)tz, 0));
 }
 
 int _execve(const char *fname, char * const argv[], char *const envp[]) {
-  int ret = _syscall_(SYS_execve, (intptr_t)fname, (intptr_t)argv, (intptr_t)envp);
-  if (ret < 0) {
-    errno = -ret;
-    return -1;
-  }
-  return ret;
+  return syscall_result(_syscall_(SYS_execve, (intptr_t)fname, (intptr_t)argv, (intptr_t)envp));
 }
 
 // Syscalls below are not used in Nanos-lite.
 // But to pass linking, they are defined as dummy functions.
 
 int _fstat(int fd, struct stat *buf) {
+  errno = ENOSYS;
   return -1;
 }
 
```

全部hunk与实际工作树及local/repair.patch一致，无省略；archive-validation保留正反逐字节及mode核对。报告中diff空上下文行保持原字节。

### 复现、未测与停点

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0076/local/run.py before
python3 npc/verif/records/process/code_correctness_review/crp-f0076/local/run.py after
python3 npc/verif/records/process/code_correctness_review/crp-f0076/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0076/local/real.py
python3 npc/verif/records/process/code_correctness_review/crp-f0076/local/standard-path/run-standard.py nanos
```

当前源恢复后，按015841a及三文件repair.patch配对重建；prepare复用本地现有资源，无下载/安装。prepare本身也执行一次标准update；最终重复update的完整env/argv保存在update-final-isolated-result.json，不能只切cwd继承外部NAVY_HOME。若隔离目录已存在先核查resume状态，不重复创建；最终模型/镜像/截图清理后须重建，哈希只标识当时身份。host为受控返回，真实guest按上表单独证明。全部一次性测试源/日志/JSON留local，不随代码提交。

全局低层errno是newlib当前串行适配契约，不是线程/TLS安全；不实现非法用户指针恢复、NULL路径/gettimeofday指针验证、完整POSIX/stat/process、device错误ABI、文件表隔离/并发或brk回收。底层盘错误仍按F0009终止；fs固定模型其他语义保持。仅当前RV64 NEMU目标及host，NPC nanos/完整Linux/其他ISA/32位/长期与实体音视频未测。CPU-tests/RT/REF不消费Navy/nanos用户错误链，未重复运行；M2保持。原F0073/F0040/F0043及独立CQ仍未修。

本组完成后保存必要配方/日志/配置/身份/完整patch，清理本目录内可再生模型/镜像/对象/截图/生产副本，清单与回执见下节。结果确认/本组commit Pending；唯一未来入口TASK_QUEUE#crp-next，下一F0070未Start；不自动commit/push/下一单元。建议开启新对话：本轮已跨提交、错误契约裁决、两套guest与标准消费者，下一项进入VME失败初始化；恢复入口完整。

## 最终清理与完成边界

179项preclean、9346输入/产物身份、三文件完整diff正反及8帧目视完成后，所有本组构建/guest均结束；删除9407文件/链接、522356632逻辑字节/550285312分配字节，0 tracked/正式资产删除。包含隔离源码/模型/目标与标准盘/ELF/对象/截图；保留最小配方、实际日志、配置和身份/patch，清单及回执local/cleanup-plan.json、cleanup-receipt.json。旧身份清单仍保留当时事实，合并清理回执解释预期缺失，不能声称旧模型/截图仍可用。

F0076 Completed，结果确认/本组commit Pending；97完全已修/22未修完，前96已确认提交015841a4a42ba8b0c97f31ba508b580c17b665bb。Working tree contains uncommitted F0076 repair/documentation changes，index空，无push/安装/运行中任务。唯一后续TASK_QUEUE#crp-next，下一F0070未Start；当前停止，不自动提交或下一组/M2。会话建议：建议开启新对话；本轮跨提交、裁决、两套guest和标准消费者，恢复入口和未测边界已完整保存。

最终终检49项PASS，81份保留证据身份固定；179preclean/9346历史身份/三文件完整diff/五正式资产/9407预期清理/119行97与22计数/唯一下一入口一致。正文18个单空格行均为原样diff空上下文。没有新增动态测试/commit；F0076 Completed，结果确认/commit Pending，当前停止。

## 用户确认与提交收尾（2026-10-20）

用户“提交并继续”确认上述已报告范围与限制，授权精确提交F0076后执行TASK_QUEUE唯一入口F0070一个单元。提交前81份保留证据身份、三源完整patch与正式资产复核一致，复用49项终检；未重跑动态测试或重复Completion。实际commit/路径核验保存在local/submit-receipt.json及.agent。local/.agent不由commit备份，无push。可在当前对话继续：已恢复完整入口，本轮授权及下一单元边界清楚。
