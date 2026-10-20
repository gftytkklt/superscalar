# CRP F0079/F0080 — newlib 零长度写与数组分配溢出

## 本轮计划（2026-10-20）

用户“提交后继续”确认前组F0068并授权提交后一个既有单元；实际9fb8831，六文件
集合/blob及root/index干净已核对。复用既有CRP总计划与本组唯一入口，不推进M2。

目标/范围：F0079只在_fwrite_r进入两个模板分支前处理size或count为0，返回0且不
改FILE状态/位置；普通完整元素计数/短写/错误保持，含unlocked同源变体。F0080只
在calloc模板乘法、allocator/锁/清零前检查size_t溢出，按现有RERRNO设ENOMEM并
返回NULL；零尺寸保持原malloc(0)路径，正常分配仍清零，不改变allocator或errno ABI。

交付与执行顺序：
1. 复现P7原反例；实际生产源host最小夹具检验fwrite两分支/零值维度/完整写/短写/
   错误及FILE与输入哨兵，calloc零/正常/刚可表示和刚溢出/极大参数，核allocator调用、
   清零与独立_reent errno。逐项保留原/新命令、退出码和源身份。
2. 最小修复；隔离重建真实Navy libc，使用实际库链接用户payload验证_fwrite_r/
   fwrite及_calloc_r/calloc、正常分配/释放复用/错误后堆保持，旧新同payload对照。
   重建受影响默认三前台/hello并实际交互/目视，不用旧ELF替代新libc回归。
3. 保存构建/输入/产物身份、必要最小测试源与patch；实际验证/目视后清理本组可再生
   镜像/截图/编译副本，更新records索引/逐项状态/既有计划/.agent与唯一未来入口。

验收：每项原失败/新通过；host不能替代实际libc/guest。CPU/RT不消费Navy libc不
重跑，NPC nanos/全配置/长期/实体音视频未测单列。未更改runner核心判据时复用，
新增判据保留有效结果数/拒绝失败检查。不安装、不改Make/日常流程；真实契约冲突
即停，不自定新能力。整组完成后停止等确认/commit，不自动提交新组/push/下一组。

背景：本地fwrite/calloc文档及RERRNO既有实现；[newlib官方手册](https://sourceware.org/newlib/libc.html#fwrite)
（2026-10-20读取）说明fwrite返回完整元素数、calloc分配数组且清零/失败NULL。
Navy与nanos分层背景复用[ICS-PA](https://ysyx.oscc.cc/docs/ics-pa/3.3.html)既有阅读，
标准输入边界按本地库接口处理，不扩展教学OS的保护/并发/失败协议。

## 实施结果 — 两项Completed，用户确认/commit Pending

生产仅嵌套newlib的src/stdio/fwrite.c与src/stdlib/mallocr.h，共11增1删。
_fwrite_r在初始化/锁/方向/写权限/乘除法前处理任一零维度，locked/unlocked同源
变体及两模板受保护。calloc在size_t乘法前用除法界限判断，不可表示则用现有
RERRNO设ENOMEM、返回NULL；尚未碰allocator/锁/清零。零尺寸仍走原malloc(0)，
正常分配与清零不变。累计54已修/65未修完，前52均确认提交，本组两项待确认/提交。

| 验证 | 结果 / local证据 |
|---|---|
| F0079原host | 嵌套Git b7d992a源码，默认模板size0被UBSan拒绝exit1；stream模板size0返回count而非0，被断言拒绝exit2。原P7根因独立复现。unit-results/before日志 |
| F0079最终host | plain/stream/两个unlocked变体，共46场景；8个零维度/_r与public wrapper场景分别检查整个FILE、reent与errno、设备钩子未变；正常6字节、3字节短写只计完整元素、立即错误，plain还含只读写错误。ASan/UBSan全通过，FILE/外部stream hooks为stub，非实际OS；stream只验证可用模板，不宣称全部配置 |
| F0080原/新host | 原溢出请求仍调用allocator传小尺寸，被“不调用allocator”断言拒绝exit2。新12场景：正常3×8/1×1、三个零组合、SIZE_MAX×1/可表示边界仅观察传参且stub失败、刚溢出/交换维度/双SIZE_MAX拒绝、正常allocator失败；独立reent errno与全局errno隔离，实际模板清零72字节及后方哨兵保持。非真实大分配/真实堆证明；LSan关闭 |
| 真实旧库 | 初始-O2 RV64 writable零请求碰巧返回0，反汇编有独立零循环return0路径，不能声称旧真实DIV故障。补充合法只读FILE零请求不应改流状态：旧库读写检查错误设置ferror/errno，LIBC-GUEST FAIL step13/BAD/exit1。旧calloc独立payload在step2失败：实际allocator返回非NULL错误小块，未按超量容量写入，不制造越界。runs及before日志 |
| 真实新库 | 相同新版payload与真实newlib/libos链接：public/_r零维度、FILE状态与errno保持；正常fwrite6字节/位置/读回；只读非零写正确报错；真实funopen+无缓冲stream短写3字节时返回1完整2字节元素。calloc public/_r溢出NULL/ENOMEM、独立errno、sbrk不变、旧64B堆哨兵保持，正常分配/三个零尺寸/释放后3次重新清零通过。FWRITE/CALLOC/LIBC-GUEST PASS+GOOD TRAP/exit0 |
| 真实数据/链接 | 用户实际将16B夹具开头012345写为abcdef，其余10B仍6789abcdef；整盘除这16B之外SHA保持。7个最终ELF与盘extent逐字节一致：旧/新3payload与新编译PAL/NTerm/NSlider/hello四应用；738对象/库/ELF、1187份消费者源/头/链接脚本身份保存。正式盘/默认kernel/native/config/NDL/SDL/loader/proc保持 |
| 构建/消费者 | 19次实际成功构建（初12+补充payload3/kernel4），从空build重建newlib和四应用，并用新ELF替换隔离盘目录对应条目，未消费正式旧ELF冒充新libc。最终FG内核1亿指令q/exit0，hello进展正常；最终52.86秒8帧三前台交互：PAL标题/飞鸟、终端qzx报错后prompt、slider0→1→0帧SHA恢复、返回PAL仍有标题和原蓝边，hello33→148。全部最终RGB图已目视；自有组SIGTERM/实际exit0不是guest正常完成 |
| 判据/收尾 | 28项preclean通过；实际四run日志重判均接受，缺GOOD/任一分项PASS/非零退出/混BAD/错盘/原版早期无关失败共7类判据故障均拒绝。2914可再生文件198486916逻辑字节（约189.3MiB）清理，零tracked删除/零剩余产物；身份清单与cleanup-plan/receipt解释旧路径缺失 |

初始host正常FILE夹具漏buffer base，cantwrite正确拒绝；按有效无缓冲FILE补齐后
重跑，未改生产。真实初始payload未能通过零请求返回值区分旧O2实现，保留其
step27 calloc失败/初始图形观察；加入只读流状态用例，补编译3payload/4内核后在
最终配置重跑，不改写初始记录。对应函数契约见[C11草案N1570 §7.21.8.2¶3](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf#page=354)
（2026-10-20读取）：零size或nmemb返回0且流状态不变。Open Group网页返回403，
未作为正文依据。newlib源码UB与具体优化产物实际表现分别记录，不把host结果外推
成RV64必然除零崩溃；fixture-corrections及linked-fwrite-disassembly保存细节。

## 仓库归属、限制与恢复

libc是根仓库忽略的**独立嵌套Git仓库**，HEAD
`b7d992afd8335f89107787fcc75d7e483a9afa9d`。它原有850条执行位差异，本轮未chmod
或改Git设置；用只读`git -c core.fileMode=false diff`核对内容，只有本组两文件，
原两文件字节与P7身份/该HEAD一致。根HEAD为F0068提交9fb8831，本组尚未commit；
提交时应将两个生产源归到嵌套仓库，只提交归属本批的内容，排除原执行位噪声；根
只提交报告/忽略/索引/台账，不force-add整个libc、不改变忽略规则。根commit不能
代替嵌套源提交或本地证据备份。local/repair.patch不含mode噪声，保留本组源码恢复。

正式工作区libc archive与四应用/ramdisk未改写，实际测试使用隔离重建的产物；
日常仍沿用现有Navy构建/打包入口，无新增选项/必经步骤。当前构建中原有低层声明
warning等仍归F0077等，不宣称无警告或全ABI已修。CPU-tests/RT/REF不消费Navy libc，
按闭包不重跑；未测NPC nanos、32位宿主、全部libc配置/应用、真实OOM、长期/实体
音视频。fwrite非零乘法溢出、库并发、所有malloc内部边界等不在本组验收。

恢复从根9fb8831与上述嵌套HEAD+local/repair.patch重建；正式Navy盘/header的路径
与SHA见entry-identity。prepare复制当前AM/Navy库及实际应用源码，旧两源从嵌套Git
恢复，payload使用原Navy Make app，正常四ELF追加隔离盘并替换目录；配置/版本/
实际命令/退出码见tools、builds、fixtures、appended-files、两套nanos结果。

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0079-f0080/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0079-f0080/local/prepare.py
python3 npc/verif/records/process/code_correctness_review/crp-f0079-f0080/local/run.py
python3 npc/verif/records/process/code_correctness_review/crp-f0079-f0080/local/nanos-run.local nanos-final
```

全新再生直接使用最终guest.c，无需重放初始诊断/refresh；构建12次，实际本轮19次
因补充判据产生的7次构建保留为历史。观察目录须为空或换名。visualize.py生成
RGB接触图，目视/结果记录后才清理；check/cleanup是agent局部收尾工具。镜像/
ELF/截图/编译树/整份生产源码副本均已删除，哈希只作当时身份，不宣称仍可查看
原图或直接复用旧ELF。保留必要最小夹具、脚本、配置/日志/结果/patch及清理回执，
local/.agent继续忽略；本轮到此停止，等待结果确认/commit，不自动提交/push/
下一组或推进M2。未来只沿TASK_QUEUE#crp-next。


<a id="submit-20261020"></a>
## 用户确认与实际提交（2026-10-20）

用户“提交后继续”确认本组已报告范围/限制并授权提交后执行唯一下一组。100项manifest保持，原28preclean/18终检/7判据负例及产品验收/清理复用，不重复Completion或动态测试。嵌套两源实际提交5d9ffdb869f36282452a8f48a4655f53fb1745d5，11增1删，暂存/实际blob及原100644模式核对一致；仅原mode差异保留，内容/index干净。根仓库仅提交本组报告/.gitignore、process索引和逐项台账4文件，实际回执见local/submit-receipt.json。无push；原Pending为交付时截面，忽略资产/.agent不随普通commit备份。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0079/F0080 — navy-apps/libs/libc

两项分别对应零大小写入及数组分配乘法溢出；原报告的 host/实际新库与消费者验收不变。

- 差异路径相对于仓库 `navy-apps/libs/libc`；旧版本：`b7d992afd8335f89107787fcc75d7e483a9afa9d`；新版本：`5d9ffdb869f36282452a8f48a4655f53fb1745d5`。

#### `src/stdio/fwrite.c`

F0079：入口新增 `if (size == 0 || count == 0) return 0;`，在两个编译分支共同入口结束零请求。原默认分支可能走到除以 `size`，stream 分支可能把零大小请求错误报告为 `count`；提前返回既消除除零，又保证返回零且不进入流初始化/写入。非零请求仍走原写入及短写计算，不扩展为任意 `size * count` 溢出修复。

```diff
diff --git a/src/stdio/fwrite.c b/src/stdio/fwrite.c
index aa14421db6e2cfcbde95a0e48246b30229897aa0..52d3b9ee6b6d0320b6f51e84efed5c345e5e8f11 100644
--- a/src/stdio/fwrite.c
+++ b/src/stdio/fwrite.c
@@ -114,6 +114,9 @@ _fwrite_r (struct _reent * ptr,
        size_t count,
        FILE * __restrict fp)
 {
+  if (size == 0 || count == 0)
+    return 0;
+
   size_t n;
 #ifdef _FVWRITE_IN_STREAMIO
   struct __suio uio;
```

#### `src/stdlib/mallocr.h`

F0080：将 `sz = n * elem_size` 延后；先用 `n != 0 && elem_size > (size_t)-1 / n` 判断数学乘积是否超出 size_t，短路避免除零。超限直接写既有 `RERRNO = ENOMEM` 并返回空指针，不调用分配器；校验后才形成 `sz`，原分配/清零逻辑继续工作。零维度保留原 allocator 语义，不把绕回的小块当作完整数组。

```diff
diff --git a/src/stdlib/mallocr.h b/src/stdlib/mallocr.h
index 0a51549740e23423a31170ba8e68501ca2f2cd85..b8fe9d3980f23cc66fcc5c590cc49a78e2e39485 100644
--- a/src/stdlib/mallocr.h
+++ b/src/stdlib/mallocr.h
@@ -3194,7 +3194,7 @@ Void_t* cALLOc(RARG n, elem_size) RDECL size_t n; size_t elem_size;
   mchunkptr p;
   INTERNAL_SIZE_T csz;
 
-  INTERNAL_SIZE_T sz = n * elem_size;
+  INTERNAL_SIZE_T sz;
 
 #if MORECORE_CLEARS
   mchunkptr oldtop;
@@ -3202,6 +3202,13 @@ Void_t* cALLOc(RARG n, elem_size) RDECL size_t n; size_t elem_size;
 #endif
   Void_t* mem;
 
+  if (n != 0 && elem_size > (size_t) -1 / n)
+  {
+    RERRNO = ENOMEM;
+    return 0;
+  }
+  sz = n * elem_size;
+
   /* check if expand_top called, in which case don't need to clear */
 #if MORECORE_CLEARS
   MALLOC_LOCK;
```
