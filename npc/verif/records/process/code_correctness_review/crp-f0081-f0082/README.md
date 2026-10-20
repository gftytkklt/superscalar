# CRP F0081/F0082 — exec wrapper 输入边界

## 计划与启动（2026-10-20）

用户“继续CRP修复”授权唯一队列入口一个单元。前57项已确认提交，root
23b0313、nested71fac82；根树/index干净，nested内容/index干净，原850执行位差异
保留。Guard无冲突，M2保持。本组不自动commit/push或进入下一组。

范围：execl/execlp/execle保留256指针栈表，最多255非NULL参数并留终止NULL；
写前拒绝超限，va_end后errno=E2BIG/-1，不调用exec。正确处理arg0=NULL与
execle的紧随终止NULL的envp。execvp保留MAXNAMLEN=1024缓冲，以减法检查
组件+可选斜杠+file+NUL，超限ENAMETOOLONG/-1，不调用该候选exec。
无PATH与含斜杠直接转发；现有空PATH不搜索/errno保持、首部及中间空段当前目录、
尾部空段不再搜索、仅ENOENT继续等语义保持。超限行为原为越界，使用原审阅建议
的明确错误，不增加全POSIX兼容、不处理F0061/F0076/setenv。

顺序/验收：先保存原版ASan越界见证，逐项最小修复；host sanitizer验证0/1/255/
256/257参数、envp、路径1023/1024和组合边界、空组件及错误短路。实际新newlib
链接guest复用定向用例，捕获层区分wrapper拒绝和低层执行；补实际成功exec链。
按现有nanos make ARCH=riscv64-nemu update→run重建消费端，三前台/hello回归，
核对链接及盘extent身份。CPU/RT/REF不消费Navy newlib，不重复测试。最后目视、
身份/正式资产保护检查、清理本组可再生产物，更新records索引/台账及.agent。

交付：nested四个posix源、最小报告/忽略规则和本地夹具/命令/日志/patch/身份。
完成整组后停，等待结果确认/提交。无安装需求；真实策略冲突立即停。
参考讲义[超越容量的界限](https://ysyx.oscc.cc/docs/ics-pa/4.3.html)（2026-10-20
读取，说明用户程序地址空间背景）；wrapper容量/错误与空PATH实际契约以本地
P7/USER_RUNTIME/FINAL_FINDINGS和当前代码为准，不声称全POSIX。

## 实施结果 — 两项Completed，结果确认/commit Pending

nested newlib仅四个posix源60增36删，root无生产修改。F0081逐项取参前验证剩余
指针位置，255参数+NULL可执行，256/257参数E2BIG/-1且无exec；arg0=NULL直接
成为终止项，不多取一个参数，execle正确读取其后的envp。F0082去除无界strccpy/
strcat，以有界扫描/减法验证组合容量后memcpy；最多1023字节路径+NUL，超限
ENAMETOOLONG/-1，不尝试该候选。前面合法候选可能已经按ENOENT规则尝试，
不会回滚此前尝试。直接含斜杠或无PATH的file继续不受本地拼接容量限制。

| 验收 | 结果 / local证据 |
|---|---|
| 原版见证 | Git nested71fac82四入口：execl/execlp/execle各256参数，execvp1024字节PATH组件，ASan各精确报stack-buffer-overflow，四次非零；不是无关编译失败。unit-results及unit/before-0～3.log |
| F0081定向 | 三入口×0/1/255/256/257共15场景，检查返回/errno/调用次数、参数/终止NULL和继承或显式环境指针；超限零exec。合法NULL终止输入，不包含调用者漏传NULL |
| F0082定向 | 28路径场景，组件/组合1023/1024、已有斜杠、空file、长file/直接含斜杠、PATH未设/空/首尾与中间空段；ENOENT继续、EACCES/ENOEXEC/E2BIG短路、先合法后超长。明确保持原空PATH零调用且errno不变、尾部空段不额外搜索 |
| host组合 | 以上43场景/169断言，ASan+UBSan通过且无运行时告警；最终7命令含两次编译/四原反例/一次完整新测试。unit/after.log、unit-results |
| 实际RV64组合 | 新完整libc链接真实execl/execle/execlp/execvp/execv，重复43场景/169断言；只在execve/getenv捕获层控制候选/错误及参数，不替换被修wrapper。随后放行execve到真实ecall/内核，execl→execlp→execle三次进程替换，最终argv/sentinel及唯一CRP_ENV=ok经loader/_start保持，PASS/GOOD/exit0，6,641,086指令。guest-result/run/linked-exec-symbols |
| 既有标准入口 | 在隔离完整源码和既有资源上，nanos目录make -j4 ARCH=riscv64-nemu git_commit= update exit0/28.185秒，再同参数run。108 extent逐字节等于安装文件、四个新链接应用等于安装与盘内容；四生产源与最终库一致、四archive成员等于对应新对象。未新增Make接口/日常步骤 |
| 三前台/hello | 标准run54.65秒/8帧，PAL标题/飞鸟、nterm qzx command not found及prompt、slide0→1→0字节SHA恢复、返回PAL/Enter动画；10条实际SDL队列输入顺序通过，hello34→149。RGB接触图已逐帧目视，原返回PAL蓝边保持；自有SIGTERM make -15为观察结束，非guest正常退出。standard-path/nanos、visual-qa |
| 证据/判据 | 145项preclean通过，4890份最终源/头/Makefile/配置身份、850份链接产物身份；6类非零/缺标记/重复标记/混BAD/缺GOOD等判据失败均拒绝。正式盘/header/kernel/config身份不变，两HEAD/index不变，nested仍仅四源内容及原850mode差异。validation-preclean/checker-negatives |

夹具更正：第一次host复用了glibc unistd的nonnull(arg0)属性，与本地newlib不符，
导致0参数env检查失败并报UBSan；改用本地同等原型的最小host头，最终完整测试通过。
首版RV64诊断main返回后遵循原sys_exit重启nterm，四组PASS标记已出现但未GOOD，
60秒超时后进程被subprocess清理；改诊断终点为现有测试ebreak，并重新构建payload/
kernel运行，最终exit0/GOOD。首次日志单列initial-*，不作为通过的完整guest。
该重试只改测试程序；标准update/run与生产代码不受影响。

## 持久化、限制与再生

累计59已修/60未修完；前57已确认提交，新两项结果确认/commit Pending。root基线
`23b031327d97e9cd3cecf2fa6eee4a6fc23ef736`，nested基线
`71fac82b295316c80acf5bd3dc825ff2ff202a46`。未来提交四源归nested，排除850既有
执行位差异；root只归属报告/.gitignore/索引/台账，两index未动，无commit/push。
一次性夹具本地忽略，不加入公共测试入口，无新的长期架构裁决。

未测NPC nanos、其他ISA/全newlib配置、完整POSIX行为、长期/实体音视频；
CPU/RT/REF不消费Navy newlib，按依赖不重跑。F0061内核参数容量、F0076底层errno、
setenv所有权与其他未修不因本组通过而闭合；注入错误检查的是wrapper传播，
不宣称真实OS错误映射正确。guest成功exec链只使用3个小参数，不把255参数的
捕获层测试冒作内核容量验收。所有指针/字符串均合法，缺NULL与坏指针不在本组。

已完成目视/身份验证后，清理9398文件506946335逻辑字节（约483.5MiB）的隔离
源码/编译/盘/截图，零tracked删除、清单内零剩余；cleanup-plan/receipt解释历史
manifest/身份中的预期缺失。保留最小夹具、patch、配置/命令/日志/身份/结果，
不保留生产源码副本。local/.agent不随普通commit备份。

再生从上述双Git基线加local/nested-repair.patch，使用当前工作区已有资源/工具，
不下载/安装；正式Navy盘/header等来源SHA见entry.json。以下在全新输出树执行：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/generate.py
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/standard-path/run-standard.local nanos
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/prepare-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/run-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/visualize.py
python3 npc/verif/records/process/code_correctness_review/crp-f0081-f0082/local/check.py
# 实际目视后再执行cleanup.py；final-check.py复核保留证据与收尾。
```

整组到此停下，等待结果确认/精确归属提交；未来范围/必读/验收只在TASK_QUEUE
唯一入口维护，不自动启动下一组或M2。原历史审阅快照不改写。


<a id="submit-20261020"></a>
## 用户确认及提交（2026-10-20）

用户“提交后继续”确认本组已报告范围并授权精确归属提交后继续F0083一个单元。
67项原manifest无漂移，复用原145收尾/22终检及产品验收，不重跑测试/重复Completion。
nested实际`d923fa4be105c14ffdf8c1bab0b613a0e3b8a64c`，四源60增36删、原100644/blob均一致，内容/index干净，
原850执行位差异保留；root仅本报告/.gitignore/两个索引台账，实际SHA见
local/submit-receipt.json。59项均确认提交，剩余60未修完；无push。
本地测试/原始证据/.agent继续忽略，commit不是备份；未测限制保持。
随后仅沿TASK_QUEUE开始F0083，新结果不自动提交。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0081/F0082 — navy-apps/libs/libc

三个参数 wrapper 与路径拼接均保留固定栈缓冲；实际成功 exec 的内核容量证明范围仍以原报告为准。

- 差异路径相对于仓库 `navy-apps/libs/libc`；旧版本：`71fac82b295316c80acf5bd3dc825ff2ff202a46`；新版本：`d923fa4be105c14ffdf8c1bab0b613a0e3b8a64c`。

#### `src/posix/execl.c`

F0081：`argv[0] = arg0; i = 0; while (argv[i] != NULL)` 先检查已有参数；arg0 为 NULL 时不再额外取参。每次 `argv[++i] = va_arg(...)` 前检查是否已处于最后槽位；若最后槽位仍非 NULL，执行 `va_end`、设 `E2BIG`、返回 -1，不调用 execve。256 指针容纳最多 255 个非 NULL 参数及一个终止 NULL；恰好 255 个参数时可读取终止项到槽位 255。

```diff
diff --git a/src/posix/execl.c b/src/posix/execl.c
index e22bdc09cdd7b324af0b94910785e837b218ebf2..88cc26161a55e38c63f3c24a2d74e4995192a015 100644
--- a/src/posix/execl.c
+++ b/src/posix/execl.c
@@ -7,6 +7,7 @@
 
 #include <_ansi.h>
 #include <unistd.h>
+#include <errno.h>
 
 /* Only deal with a pointer to environ, to work around subtle bugs with shared
    libraries and/or small data systems where the user declares his own
@@ -28,10 +29,17 @@ execl (const char *path,
 
   va_start (args, arg0);
   argv[0] = arg0;
-  i = 1;
-  do
-      argv[i] = va_arg (args, const char *);
-  while (argv[i++] != NULL);
+  i = 0;
+  while (argv[i] != NULL)
+    {
+      if (i == sizeof (argv) / sizeof (argv[0]) - 1)
+        {
+          va_end (args);
+          errno = E2BIG;
+          return -1;
+        }
+      argv[++i] = va_arg (args, const char *);
+    }
   va_end (args);
 
   return execve (path, (char * const  *) argv, *p_environ);
```

#### `src/posix/execlp.c`

F0081：与 execl 相同的写前容量检查和 `va_end/errno=E2BIG/-1`，保护本函数自己的 256 指针表；合法参数继续交给 `execvp` 进行 PATH 搜索。arg0 为 NULL 直接终止参数表，超限不进入 execvp。

```diff
diff --git a/src/posix/execlp.c b/src/posix/execlp.c
index 23c65366b7445bdf80df024b1d5c1dd67f20975e..662804ece7e55d340ce4479822abb0a88bc3148a 100644
--- a/src/posix/execlp.c
+++ b/src/posix/execlp.c
@@ -7,6 +7,7 @@
 
 #include <_ansi.h>
 #include <unistd.h>
+#include <errno.h>
 
 
 #include <stdarg.h>
@@ -23,10 +24,17 @@ execlp (const char *path,
 
   va_start (args, arg0);
   argv[0] = arg0;
-  i = 1;
-  do
-      argv[i] = va_arg (args, const char *);
-  while (argv[i++] != NULL);
+  i = 0;
+  while (argv[i] != NULL)
+    {
+      if (i == sizeof (argv) / sizeof (argv[0]) - 1)
+        {
+          va_end (args);
+          errno = E2BIG;
+          return -1;
+        }
+      argv[++i] = va_arg (args, const char *);
+    }
   va_end (args);
 
   return execvp (path, (char * const *) argv);
```

#### `src/posix/execle.c`

F0081：同样从槽位 0 检查并在取下一参前验证容量；循环结束后 `envp = va_arg(args, const char * const *)` 读取紧随终止 NULL 的环境指针。因 arg0=NULL 不再多读一项，零参数时也能正确读取 envp；超限在读取环境前就清理 va_list 并返回 E2BIG。

```diff
diff --git a/src/posix/execle.c b/src/posix/execle.c
index 7e12ab4a1e50b5010cf030206d1d14522c9b9e71..5a1631ab8af7c600b188ffbe0aa69aa38d20139d 100644
--- a/src/posix/execle.c
+++ b/src/posix/execle.c
@@ -7,6 +7,7 @@
 
 #include <_ansi.h>
 #include <unistd.h>
+#include <errno.h>
 
 
 #include <stdarg.h>
@@ -24,10 +25,17 @@ execle (const char *path,
 
   va_start (args, arg0);
   argv[0] = arg0;
-  i = 1;
-  do
-    argv[i] = va_arg (args, const char *);
-  while (argv[i++] != NULL);
+  i = 0;
+  while (argv[i] != NULL)
+    {
+      if (i == sizeof (argv) / sizeof (argv[0]) - 1)
+        {
+          va_end (args);
+          errno = E2BIG;
+          return -1;
+        }
+      argv[++i] = va_arg (args, const char *);
+    }
   envp = va_arg (args, const char * const *);
   va_end (args);
 
```

#### `src/posix/execvp.c`

F0082：删除无界 `strccpy/strcat`。PATH 组件扫描最多 sizeof(buf)，到上界即 ENAMETOOLONG；`strnlen(file, sizeof(buf))` 限制文件名扫描。`sizeof(buf)-1-path_len` 先预留 NUL，再减可选 slash，以剩余容量比较避免加法溢出；短路确保减 slash 时不会下溢。验证后 memcpy 组件，按需写斜杠，再复制 `file_len+1` 含终止符，允许最多 1023 字节有效路径。仅拒绝本地拼接超限；含斜杠/无 PATH 的直接路径、原空段和 ENOENT 搜索规则保留，前面已尝试的合法候选不回滚。

```diff
diff --git a/src/posix/execvp.c b/src/posix/execvp.c
index fb4699afbe5e746f249205d018a6ab4de3af17ca..c7f39f3c0dffa09c94c061dac710f208c52602b4 100644
--- a/src/posix/execvp.c
+++ b/src/posix/execvp.c
@@ -15,25 +15,6 @@
 
 #define PATH_DELIM ':'
 
-/*
- * Copy string, until c or <nul> is encountered.
- * NUL-terminate the destination string (s1).
- */
-
-static char *
-strccpy (char *s1,
-	char *s2,
-	char c)
-{
-  char *dest = s1;
-
-  while (*s2 && *s2 != c)
-    *s1++ = *s2++;
-  *s1 = 0;
-
-  return dest;
-}
-
 int
 execvp (const char *file,
 	char * const argv[])
@@ -52,11 +33,30 @@ execvp (const char *file,
 
   while (*path)
     {
-      strccpy (buf, path, PATH_DELIM);
-      /* An empty entry means the current directory.  */
-      if (*buf != 0 && buf[strlen(buf) - 1] != '/')
-	strcat (buf, "/");
-      strcat (buf, file);
+      size_t path_len = 0;
+      size_t file_len;
+      size_t slash;
+
+      while (path_len < sizeof (buf) && path[path_len]
+             && path[path_len] != PATH_DELIM)
+        path_len++;
+      if (path_len == sizeof (buf))
+        {
+          errno = ENAMETOOLONG;
+          return -1;
+        }
+      slash = path_len != 0 && path[path_len - 1] != '/';
+      file_len = strnlen (file, sizeof (buf));
+      if (slash > sizeof (buf) - 1 - path_len
+          || file_len > sizeof (buf) - 1 - path_len - slash)
+        {
+          errno = ENAMETOOLONG;
+          return -1;
+        }
+      memcpy (buf, path, path_len);
+      if (slash)
+        buf[path_len++] = '/';
+      memcpy (buf + path_len, file, file_len + 1);
       if (execv (buf, argv) == -1 && errno != ENOENT)
 	return -1;
       while (*path && *path != PATH_DELIM)
```
