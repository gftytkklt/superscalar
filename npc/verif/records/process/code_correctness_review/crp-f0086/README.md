# CRP F0086 — nanos-lite-guest源清单承接

## 整体计划与启动（2026-10-21）

用户“继续”授权TASK_QUEUE#crp-next的F0086一个单元。Guard：前F0072 Completed/用户已确认/实际提交4c2019c3c28b1e32449129b6886970dd18d40453，根工作树/index干净；M2未推进，F0031/F0071作为NPC能力扩展移交Linux的用户裁决保持。

目标/范围：处理wrapper SRCS仍引用不存在ramdisk.c的问题，核清当前disk.c、资源/stub符号和libam闭包。生产拟仅将失效源引用更新为当前disk.c；不自行启用KERNEL_EMBED_RAMDISK、不内嵌正式盘、不为wrapper增加VME/调度/设备/堆能力或改变公开Make流程。保持原logo/空ramdisk stub，不将链接或运行能力缺口藏成成功。

阶段：本组一个单元。固定源码/正式资产身份→隔离无build的旧wrapper失败见证→最小候选修复与同版干净构建/源前置条件和符号核对→按实际结果选择可执行受影响验证或记录独立能力阻塞→完整diff与语句说明/正反应用、证据/索引/状态/清理收尾。

交付：本报告、最小生产差异（若契约明确）、实际命令/退出码/配置/身份及清理回执；保留原审阅历史和唯一未来入口。验收：旧明确缺ramdisk.o源、修正后所有SRCS能从wrapper/VPATH找到唯一真实输入并实际交叉编译；当前disk与stub不重复定义资源，不启用未声明存储；真实库/最终链接与受影响运行分别核验，独立未实现能力造成的失败/NotRun如实列出，不能将仅对象编译称为完整wrapper可运行。

结束节点：范围内完成实施/验证/留档后停止等用户确认/commit，不自动push/下一单元。若只有部分闭环，分别记录源清单修复和完整wrapper限制；若需要新后端/能力/失败契约决策，按WORKFLOW_POLICY先最少裁决，不擅自扩展。无安装授权、软件安装/系统改动即停。CPU/RT/完整nanos是否重跑按实际生产修改影响决定。


## 用户质询后的结论限定与核实（2026-10-21）

用户指出：ramdisk改disk只是将app的存放位置从NEMU的128MB内存区间移到独立disk空间，没有因此改变内核接口，要求确认符号未实现的结论。确认结果：**不是正常NEMU内核缺少这些实现，也不是disk迁移导致VME符号缺失；这是当前Navy wrapper选用的库与复用内核配置/内部依赖不配套。** 此限定优先于对本次ld错误的任何宽泛“接口未实现”解释。

重新建立隔离树，从实际源码重建两条链：

1. 普通nanos原Make入口`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= image`实际exit0，最终ELF中map/vme_init/protect/__am_lookup_page/__am_user_area五个符号全部已定义。riscv64-nemu.mk选择真实`riscv/nemu/vme.c`，提供这些定义。
2. 当前wrapper原入口`make --no-print-directory -j4 ISA=riscv64 app`仍exit2，实际新libam archive的nm表没有上述五个定义。其`LIBS += libam`并不选择NEMU平台AM归档；所以不能把wrapper的链接问题解释成NEMU/disk内核缺实现，也不能把整个平台AM库强塞进用户态程序绕过。
3. 在旧SRCS和新SRCS下，显式构建复用的同一当前mm.c/loader.c对象：两份mm.o SHA均d44c661e92f3e821a552877088b79e45e63e2e9395386230b68cabdc2e78b07b，loader.o均3bdc5f4a1703ebb22a1d6e2decc4646a3bddd37821130b79d2510f714d70635a，逐字节相同。旧源清单的ramdisk缺源先遮住了独立的链接断点；本次替换没有修改这两个内核对象。

五个符号还应区分来源：map/vme_init/protect是既有公开AM VME接口；两个__am_*是此前a92ccf9的loader安全修复引入的**NEMU私有辅助依赖**，不是ramdisk→disk迁移新增的接口，也不应笼统称作libam承诺实现的公开API。当前wrapper复用HAS_VME内核，缺少相应provider/适配；本单元不擅自扩展能力或将其归入已移交Linux的NPC F0031。相关配置/内部依赖可移植性限制如实保留，F0086仍仅闭合过期源引用。

复核的实际命令/退出码、库定义表、旧对象未定义表和正常内核定义表保留在local/confirmation-commands/results及confirm-*.log。原NEMU正式产物未覆盖，未执行正式update/盘改写；这次是实际构建/符号确认，不声称运行了完整wrapper。

## 实施结果 — F0086 Completed（仅源清单缺陷），结果确认/commit Pending

生产根仓仅修改`navy-apps/apps/nanos-lite-guest/Makefile`：SRCS中的`ramdisk.c`改为`disk.c`，同时补齐原文件EOF换行。其余10个输入、VPATH、include、LIBS及Make入口保持；没有添加存储后端或调整nanos配置。该修复闭合F0086“引用不存在源文件”的明确缺陷，**完整wrapper构建仍失败、实际wrapper运行NotRun**，不把后续VME缺口计入本项已实现能力。

`SRCS`决定Navy公共Makefile派生的11个.o；`disk.c`经已有VPATH解析到真实nanos实现，提供`init_disk/disk_size/disk_read/disk_write`，供fs/loader引用。wrapper未定义KERNEL_EMBED_RAMDISK，故本次disk.o不依赖ramdisk_start/end，不会读入正式盘；原空extent stub和logo stub保持，与disk.o合并无重复定义。没有将resources.S一并加入、没有改.incbin路径或启用嵌入，避免引入另一套存储选择。

| 验收 | 本次事实与证据 |
|---|---|
| 干净旧wrapper | 隔离源码、无build，真实`make --no-print-directory -j4 ISA=riscv64 app`，exit2，明确`No rule to make target …/ramdisk.o`；before-build.json/log，约0.219s。并行已启动对象的编译完成后make退出，不把旧build二进制视为当前产物 |
| 最小修复后 | 新wrapper目录同样无build，实际11个源均唯一解析并交叉编译；.d依赖逐一核对真实源路径。真实libam/libndl/libc/libos均在隔离树从源码构建archive；不是fake-make或忽略libs。after-build.json/log，约5.734s |
| 实际最终链接 | make仍exit2，已消除ramdisk.o缺源错误；最终ld仅报告5个不同VME符号缺失：`map`、`vme_init`、`protect`、`__am_lookup_page`、`__am_user_area`。当前wrapper选择的libam未提供这些定义，当前common仍HAS_VME/FG_PROCESS，完整ELF未生成。本组未提供假VME符号、未改common关闭功能绕过问题 |
| 源/符号闭环 | 11个真实.o用`riscv64-linux-gnu-ld -r`成功合并，无重复定义；disk四API、logo、ramdisk_start/end各一份定义，start=end；disk.o无ramdisk未定义引用。combined/disk-undefined日志、sources-symbols.json |
| 边界/归档 | 57项检查PASS：实际旧/新make退出/源解析/11对象及依赖/4真实库/符号/独立缺口、HEAD与8正式资产/原AM-libam-nanos其他源、newlib nested HEAD和既有mode状态保持；完整补丁正反应用exit0且逐字节恢复。validation-preclean.json/archive-validation.json |

当前缺失VME是libam上的嵌套wrapper能力限制，不是NPC F0031能力移交后就自动可用；`libam/cte.c`的ucontext仍panic、真实上下文切换仍占位，公开heap空区间F0084及syscall递归F0113均保持原归属。无需为源清单修复实施这些能力，也没有把它们转成已修。`libam/ioe.c`尚不处理AM_DISK_CONFIG，现wrapper没有已验收磁盘运行后端；不从disk.o存在推定实际磁盘可用。

旧/新编译保留已有日志格式warning（uintptr_t配%d/%p），并未将warning当本次新错误或改动其实现。标准nanos update打包的APPS/TESTS不含nanos-lite-guest，本组既不install wrapper也不更新正式盘；默认CPU/RT/三前台hello未消费该Makefile，不重跑其无关回归。真正受影响的wrapper已执行实际完整构建并固定失败原因；无最终ELF，运行为NotRun，没有用小夹具或host冒充实际wrapper运行。

依CRP参考要求尝试访问ICS-PA3.1（https://ysyx.oscc.cc/docs/ics-pa/3.1.html）返回fetch timeout；未从不可读内容推导契约。结论依据本地原问题、真实Make/源与链接结果，保留P7/P8历史审阅事实。

## 完整生产diff与版本

所属仓库：根ysyx-workbench；路径相对仓库根。旧版本`4c2019c3c28b1e32449129b6886970dd18d40453`、旧Makefile SHA256 `637e04e6d68aae2717cf008738321dd19c93b97c5b69ad106eecb830b8f78aa4`；新版本**WORKTREE（2026-10-21，未提交）**，SHA256 `6f21f80a69b2adc33a439588b1cf1e20812d7b7d88c1ee011b843465a7e747fb`。下列为本批全部生产差异，包括EOF补换行。内嵌diff正向产生新源、反向恢复旧源，逐字节核验通过；本报告与local/repair.patch一致。

```diff
diff --git a/navy-apps/apps/nanos-lite-guest/Makefile b/navy-apps/apps/nanos-lite-guest/Makefile
index 0e83e39b7c1f146209ca1fa524af63c918619847..baf773276e26f85eb76012cad03b1372cda0e9ca 100644
--- a/navy-apps/apps/nanos-lite-guest/Makefile
+++ b/navy-apps/apps/nanos-lite-guest/Makefile
@@ -6,11 +6,11 @@ NANOS_LITE_HOME = $(abspath ../../../nanos-lite)
 
 # 复用 nanos-lite/src 下的源文件（VPATH 定位），
 # 以便其中的 "files.h"/"syscall.h" 等引号头文件按原路径解析。
-SRCS = main.c mm.c device.c fs.c syscall.c loader.c proc.c irq.c ramdisk.c ramdisk_stubs.S stubs.c
+SRCS = main.c mm.c device.c fs.c syscall.c loader.c proc.c irq.c disk.c ramdisk_stubs.S stubs.c
 VPATH = $(NANOS_LITE_HOME)/src
 INC_PATH += $(NANOS_LITE_HOME)/include
 
 # libam 提供 AM 的 TRM/IOE/CTE 实现；libc/libos 由 Navy Makefile 对非 native 自动加入
 LIBS += libam
 
-include $(NAVY_HOME)/Makefile
\ No newline at end of file
+include $(NAVY_HOME)/Makefile
```

## 恢复与未测范围

复现源基线为上述旧完整commit；当前nanos/libam/libos/newlib源身份见local/entry及保留的隔离输入manifest。newlib已有本地mode噪声与实际nested HEAD沿用原状态，未修改或提交nested。复制现有Navy Make/scripts及libam/libndl/libos/libc、nanos src/include到本组local/work，排除.git/build，保留只读header symlink；所有libs均来自本工作区已有源码，不下载/安装。local/build.py before构造旧无build wrapper，应用本补丁后build.py after构造另一个无build wrapper；随后check.py检查对象/符号及正反应用。两次实际命令/cwd/环境/退出码与日志均保留，不将复现脚本exit0解释成子make通过。若要再次复现，用新的local输出目录，不能覆盖本次entry/结果，也不要在正式安装盘上做失败实验。

保留最小build/check/archive配方、源/配置/工具及对象身份、命令日志/JSON/完整patch。一次性fixture与库/对象在验证/归档/身份固定、进程结束后按CRP workflow删除，准确清理回执后附。正式8资产不变；未测试native/其他ISA/运行时磁盘/VME/实际上下文切换/真实wrapper进程/长期/GUI音视频。此处不声称完整应用可编译运行，也不推进Linux主线或NPC能力扩展。local/.agent仍被忽略，commit不等于备份。

本单元结束后停止，等结果确认/精确commit；无push或下一单元授权。唯一未来入口TASK_QUEUE#crp-next，不从本报告另排一份Next。


## 清理、状态与停点（2026-10-21）

首次57项核验/归档与2301份清理前身份固定后，删除2284个可再生文件/链接，9,778,853逻辑字节/15,101,952分配字节；用户要求确认后新增的两域构建与符号核对独立留档，删除2474个可再生文件/链接，10,961,703逻辑字节/16,699,392分配字节。两轮合计4758项、20,740,556逻辑字节；各自cleanup-plan/receipt保留前身份及预期缺失，不覆盖第一次清理历史。所有相关进程结束后才清理，不跟随symlink，零tracked/正式资产删除，8正式资产SHA保持；原始命令/日志/配置/最小脚本/JSON/补丁保留，模型/对象/源码副本需按Git及配方重建。

当前F0086 Completed（失效源清单已修；完整wrapper链接失败/运行NotRun），结果确认/本组commit Pending。累计102项已修（前101已确认提交4c2019c）+15 CRP待修+2移交Linux的NPC能力扩展。Working tree contains uncommitted F0086 code/documentation changes；索引/修复镜像/REPAIR及.agent同步，M2不变。用户的符号质询已用真实NEMU成功构建与wrapper独立库符号、mm/loader对象一致性确认并限定解释；此确认不等于用户已确认本组最终修复或授权提交。

本组停止，无commit/push/下一单元。建议开启新对话：本会话已累积启动布局、范围移交、提交与wrapper两域构建核实，后续F0113需重新聚焦syscall派发；现有唯一入口/证据完整，不额外增加执行门槛。

F0086最终终检：33项PASS，首次17份保留证据身份、两次4758项清理和8正式资产保持；正文完整diff与生产一致，3条空白告警逐一核对仅为原样diff的空上下文行。用户要求的NEMU/provider区分及旧新对象一致性证据已保存。无新增运行/commit，本组Completed仅源清单、完整wrapper仍链接失败/运行NotRun，结果确认/commit Pending，F0113未Start。


<a id="submit-20261021"></a>
## 2026-10-21 用户确认与提交收尾

用户“提交以后确认，libam真的需要调用这些接口吗？它的支持的宿主操作系统是nanos-lite吗？”确认本批已报告F0086源清单修复及wrapper/NEMU两域验收限制，并授权先精确提交，再定向核实libam职责与宿主。此后续核实不授权实施F0113或新增VME/存储能力。

复用本组Completion、57项构建/符号检查、33项最终核对及两次清理，提交前37份本地证据保持、实际完整生产patch/正文diff相同；没有重跑已验收测试。正式ramdisk.img/ramdisk.h及nanos NEMU内核在验收后变化，用户明确“是，我生成的，请保留”，已记录旧/新SHA及来源回执，三资产完整保留，其余五正式资产保持验收身份，不将本次变化误写为八资产均未变。local/user-assets-receipt-20261021.json保存当前八资产基线。状态冲突依用户明确来源解除，未回滚用户构建产物。

根提交范围仅wrapper Makefile、process索引、repair-status、本报告/.gitignore五路径；三条空白告警是原样统一diff中的空上下文行，逐条确认，无正文空白错误。完整提交身份由包含本节和本批生产差异的Git commit定位，精确暂存/实际回执保存local/submit-staged.json、submit-receipt.json；新源SHA与已验收WORKTREE身份一致。

local/REPAIR/.agent等忽略资料沿用本地持久化约定，commit不等于备份。102已修均获用户确认，另15 CRP待修+2 NPC能力扩展移交；完整wrapper仍链接失败/运行NotRun，不改变该限制。提交后仅完成用户本轮定向核实，不自动push/开始F0113或M阶段。

会话建议：建议开启新对话。本会话已累积布局/范围裁决及wrapper两域核实，下一独立修复涉及syscall派发，恢复入口完整；本轮已授权的定向问题仍在提交后完成。
