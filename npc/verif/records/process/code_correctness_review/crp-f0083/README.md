# CRP F0083 — setenv分配失败的环境所有权

## 计划及启动（2026-10-20）

用户“提交后继续”确认前组并授权提交后一个单元。前59项已确认提交nested
d923fa4/root5423bd7，双index和root干净、nested内容干净/850既有mode差异保留。
Guard无冲突，复用CRP整体计划/流程，M2不变。本组完成后停，不自动提交新组。

范围/方案：只修newlib setenv_r.c分配/发布顺序。保留rewrite=0、足够长旧值原地
复用、已有输入规则/锁/errno协议；需要新字符串时先完成字符串，再分配/扩容向量，
成功后才发布槽位/终止NULL/向量所有权。用临时指针承接realloc，失败释放本次
临时字符串、保留原environ/值/终止项；只realloc本函数当前自有向量，不能对crt
或调用者提供的借用向量realloc/free。旧字符串可能借用，继续不猜测其所有权。
不重做环境系统/线程策略、不处理F0076 errno或F0061/真实OS OOM等其他问题。

交付/阶段：一个独立修复单元，nested单源及根最小报告/忽略规则/索引台账；本地
最小受控allocator/host sanitizer夹具和实际新libc guest，复用标准update→run观察。
验收包括首次向量分配失败后重试、自有向量扩容失败/重试、新增/替换字符串失败、
rewrite=0/原地复用/正常新增/查找/删除/原环境保持；失败时指针表与字符串不变、
锁平衡/临时分配释放、不realloc/free借用对象。保存原版精确失败见证；host不能
代替实际newlib，guest受控分配失败与真实成功路径分开，不宣称制造真实OS OOM。
按影响覆盖新库消费者和标准nanos update→run/三前台/hello，CPU/RT/REF不消费
Navy不重跑。记录源码/链接/命令/结果/正式资产保护，目视后清理隔离产物并落档。
结束节点：整组完成/真实策略或安装事项，等待结果确认/提交，不push/下一组/M2。

## 实施结果 — Completed，结果确认/commit Pending

nested仅`src/stdlib/setenv_r.c`，37增37删。将所有权标记从布尔值改为当前自有向量
指针；只有当前environ与它相等才realloc，否则复制借用向量到新分配。新字符串
先分配/填充，再通过临时指针扩容向量；失败释放本轮新字符串，保留原向量/条目/
终止NULL/所有权。成功后才发布条目和向量。替换旧值的新字符串也先构造成功再
换槽位，不在失败时写NULL。沿用rewrite=0、可复用旧值原地改写、已有输入与锁
行为；NULL环境按已有findenv防护视为空表，不解引用NULL。

当前累计60已修/59未修完，前59均确认提交，本组结果确认/commit Pending。

| 验收 | 结果 / local证据 |
|---|---|
| 原版四见证 | 四次独立host进程：首次向量分配失败后重试触发对借用表的非法realloc（捕获bad=1）；自有表扩容失败丢失environ；新增字符串失败提前发布新表/NULL洞；替换字符串失败覆盖旧槽位。均在指定状态断言ENV FAIL/exit1，不是编译或sanitizer工具失败。unit/before-1～4.log |
| 失败恢复 | 首向量失败/重试、自有向量扩容失败/移动重试、首字符串失败/重试、替换失败/重试、已有自有表新增/替换字符串失败；检查原指针/字符串/后续条目/NULL终止及存活分配数保持。向量失败时临时字符串释放、借用对象从未realloc/free |
| 正常/所有权 | rewrite=0及短值原地复用零分配，成功新增/替换、实际非强制realloc和强制搬移、getenv/unsetenv及public/_r入口、调用者改回借用向量/NULL表后的新增、原借用字符串保持，递归环境锁平衡 |
| host组合 | 8场景/259断言（含夹具状态与计数检查），ASan+UBSan无告警；14条最终命令含两次编译/四原失败/八新通过。每场景独立进程使static所有权起始一致。unit-results及unit/after-1～8.log |
| 实际新库guest | 实际public/reentrant setenv/getenv/unsetenv及分配器，8场景/273断言，七次真实execve将小argv/env从旧进程交给新进程；每次新CRT的envp==environ并保持CRP_EXEC_ENV=ok。最终ENV ALL PASS/GOOD/exit0，7,475,705指令。注入仅在测试操作时控制分配失败/跟踪所有权，内层实际分配器调用不重复跟踪；其中一例强制搬移，其他成功扩容使用实际realloc。不宣称制造真实OS OOM。guest-builds/result/run、linked-env-symbols |
| 标准入口/消费者 | 完整隔离nanos目录现有make -j4 ARCH=riscv64-nemu git_commit= update exit0/27.181秒，再同参数run。108 extent连续且逐字节匹配安装文件，PAL/NTerm/NSlider/hello四新链接等于安装与盘；单源与实际新库相同，setenv_r archive成员等于对应对象 |
| 三前台/hello | 标准run54.06秒/8帧，PAL标题/飞鸟、nterm输入qzx/not found/prompt、slide0→1→0帧SHA恢复、返回PAL/Enter继续动画，10条实际SDL输入顺序正确，hello34→153。全部RGB帧已目视，原PAL返回蓝边保持。自有SIGTERM make-15属于观察结束，不是guest正常退出或长期/实体音视频验收 |
| 证据/保护 | 146项preclean，4890源/头/Makefile/配置及850链接身份；6种判据缺失/非零/混BAD/重复场景等故障拒绝。正式盘/header/kernel/config身份保持，双HEAD/index不变，nested仅单源内容变化/原850mode差异保持。validation-preclean/checker-negatives |

夹具更正：初host复用glibc stdlib的leaf属性，改名后的setenv被优化器视为不会
回调本测试翻译单元，active=1跟踪开关被移除，结果未注入分配失败。该轮不作为
原版见证。换为与本地newlib一致的最小host声明，重编译原版/新版，最终四失败及
八通过均实际触发对应路径。实际guest使用newlib自己的头，无此问题；不改生产
编译选项或公共入口。细节与初结果见fixture-corrections/unit-initial-results。

## 归属、限制和恢复

root基线`5423bd7`，nested基线`d923fa4`，完整SHA见local/entry.json。新代码精确
归属nested单源，未来提交需排除850既有执行位噪声；root只含本组报告/.gitignore/
记录索引/repair-status。双index未动，Working tree contains uncommitted CRP changes。
本次只执行“提交后继续”的一个新单元，不从该指令推定新成果获确认/提交授权。
没有push/安装/新架构Decision，不推进M2。

不追踪/释放可能借用的旧环境字符串；成功长值替换沿用原有不回收旧字符串行为。
调用者自行替换environ时，不猜测/释放其仍可能持有的旧向量；只保证不错误realloc
当前借用对象，不新增通用环境回收器。保留当前锁协议，不宣称无锁并发读安全。
F0076 errno重入策略、极长名称/值的int长度域、真实OS OOM/堆容量及其他未修保持。
未测NPC nanos、其他ISA/全配置、长期/物理音视频；CPU/RT/REF不消费Navy newlib，
按闭包不重跑。失败是可控allocator注入，真实guest正常分配/查找/删除与exec已测。

完成身份/目视后，已清理9396文件506767180逻辑字节（约483.3MiB），零tracked
删除、清单内零剩余，范围为隔离源码/构建/盘/截图及host生产副本。保留最小夹具/
命令/结果/配置/源与产物身份/patch/清理回执，不保留整份生产源码副本。旧身份
路径预期缺失由cleanup-plan/receipt说明。local/.agent仍忽略，commit不等于备份。

再生：从上述root/nested Git基线及local/nested-repair.patch恢复新源，现有正式盘/
资源/工具来源SHA见entry和standard-path/source-input-identity，无下载/安装。
在全新输出树按下列命令重建；运行时stdio/分配器额外调用不作为注入用例计数。

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/standard-path/run-standard.local nanos
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/prepare-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/run-guest.py
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/visualize.py
python3 npc/verif/records/process/code_correctness_review/crp-f0083/local/check.py
# 实际目视后执行cleanup.py；final-check.py检查最终保留证据/状态。
```

整组到此停止，待结果确认/精确归属提交；未来唯一TASK_QUEUE入口维护下一组范围/
必读/验收/门槛，F0089仍Planned未Start。历史P7/FINAL_FINDINGS及前组快照不改写。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0083 — navy-apps/libs/libc

此为已验收、尚未提交的工作树内容，不伪造修复 commit；文档保存补丁不等于该嵌套源码已提交或新获功能验收。

- 差异路径相对于仓库 `navy-apps/libs/libc`；旧版本：`d923fa4be105c14ffdf8c1bab0b613a0e3b8a64c`；新版本：`WORKTREE（2026-10-20，未提交）`。
- 未提交源 SHA256：`c3bd1469ea064982b7729c34be6be262be2542e6b5e319059ecc21ab36667c97`；与本组 `local/nested-repair.patch` 已验收内容核对。

#### `src/stdlib/setenv_r.c`

F0083：`static char **alloced` 保存当前自有向量地址，取代“曾分配过”的布尔值；只有 `*p_environ && *p_environ == alloced` 才 realloc，调用者/CRT 的借用向量改走 malloc+指针复制。`offset = -1` 区分新键与已有槽位，扫描加 `P && *P` 支持空环境。先把 `name=value` 写入 `new_entry`，再以局部 `P` 承接向量分配/扩容；失败释放临时字符串、解锁返回 -1，原 environ、旧槽位、终止 NULL 和所有权指针不变。全部分配成功后才写 `P[cnt]`、`P[cnt+1]=NULL` 并发布 `*p_environ = alloced = P`；替换长值只在字符串成功后换旧槽位。rewrite=0/原地短值复用保持；不猜测并释放借用旧字符串，也不解决调用者改换 environ 后旧向量的通用回收或并发读问题。

```diff
diff --git a/src/stdlib/setenv_r.c b/src/stdlib/setenv_r.c
index f1f885789ca6a62c0fa3db96c0fc7b43fc307322..932688411542120ef0a136aa1a8cf5cbda14a9f4 100644
--- a/src/stdlib/setenv_r.c
+++ b/src/stdlib/setenv_r.c
@@ -54,9 +54,10 @@ _setenv_r (struct _reent *reent_ptr,
 	const char *value,
 	int rewrite)
 {
-  static int alloced;		/* if allocated space before */
+  static char **alloced;		/* vector owned by this function */
   register char *C;
-  int l_value, offset;
+  char *new_entry;
+  int l_value, offset = -1;
 
   if (strchr(name, '='))
     {
@@ -81,47 +82,46 @@ _setenv_r (struct _reent *reent_ptr,
 	  return 0;
 	}
     }
-  else
-    {				/* create new slot */
-      register int cnt;
-      register char **P;
-
-      for (P = *p_environ, cnt = 0; *P; ++P, ++cnt);
-      if (alloced)
-	{			/* just increase size */
-	  *p_environ = (char **) _realloc_r (reent_ptr, (char *) environ,
-					     (size_t) (sizeof (char *) * (cnt + 2)));
-	  if (!*p_environ)
-            {
-              ENV_UNLOCK;
-	      return -1;
-            }
-	}
-      else
-	{			/* get new space */
-	  alloced = 1;		/* copy old entries into it */
-	  P = (char **) _malloc_r (reent_ptr, (size_t) (sizeof (char *) * (cnt + 2)));
-	  if (!P)
-            {
-              ENV_UNLOCK;
-	      return (-1);
-            }
-	  memcpy((char *) P,(char *) *p_environ, cnt * sizeof (char *));
-	  *p_environ = P;
-	}
-      (*p_environ)[cnt + 1] = NULL;
-      offset = cnt;
-    }
-  for (C = (char *) name; *C && *C != '='; ++C);	/* no `=' in name */
-  if (!((*p_environ)[offset] =	/* name + `=' + value */
-	_malloc_r (reent_ptr, (size_t) ((int) (C - name) + l_value + 2))))
+  for (C = (char *) name; *C && *C != '='; ++C);
+  new_entry = (char *) _malloc_r (reent_ptr,
+                                (size_t) ((int) (C - name) + l_value + 2));
+  if (!new_entry)
     {
       ENV_UNLOCK;
       return -1;
     }
-  for (C = (*p_environ)[offset]; (*C = *name++) && *C != '='; ++C);
+  for (C = new_entry; (*C = *name++) && *C != '='; ++C);
   for (*C++ = '='; (*C++ = *value++) != 0;);
 
+  if (offset < 0)
+    {                           /* create a new slot */
+      int cnt;
+      char **P;
+
+      for (P = *p_environ, cnt = 0; P && *P; ++P, ++cnt);
+      if (*p_environ && *p_environ == alloced)
+        P = (char **) _realloc_r (reent_ptr, (char *) *p_environ,
+                                  (size_t) (sizeof (char *) * (cnt + 2)));
+      else
+        {
+          P = (char **) _malloc_r (reent_ptr,
+                                  (size_t) (sizeof (char *) * (cnt + 2)));
+          if (P && cnt)
+            memcpy (P, *p_environ, cnt * sizeof (char *));
+        }
+      if (!P)
+        {
+          _free_r (reent_ptr, new_entry);
+          ENV_UNLOCK;
+          return -1;
+        }
+      P[cnt] = new_entry;
+      P[cnt + 1] = NULL;
+      *p_environ = alloced = P;
+    }
+  else
+    (*p_environ)[offset] = new_entry;
+
   ENV_UNLOCK;
 
   return 0;
```


### 本轮文档提交归属补充（2026-10-20）

本报告、内嵌 setenv diff 及既有 F0083 索引随本次[框架修复文档补充](../framework-diffs-20261020/README.md)提交根仓库；nested 的 setenv_r.c 未提交，代码结果确认/提交 Pending。上文“root 报告未提交”是原交付截面，本次只更新文档持久化事实，不把文档提交当作 F0083 代码提交或功能重新验收。实际根文档提交回执见该补充记录 local/submit-receipt.json；原 local/nested-repair.patch 保持。
