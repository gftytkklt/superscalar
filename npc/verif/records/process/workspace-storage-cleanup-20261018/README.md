# 工作区空间清理（2026-10-18）

## 计划、授权及边界

用户明确要求提交F0018，并检查工作区内占据大量空间的临时文件存档，“如有直接删除”。
F0018已确认提交37b3195，提交后root/index干净；本轮独立维护任务不Start F0021或推进M2。

单个清理单元：测量实际磁盘块占用 → 列出候选/核对未跟踪及非活动产物 → 记录路径、
尺寸、哈希后直接删除 → 复测空间/关键资产/Git状态并同步索引。无新安装或人工未决策略。
目标是释放可重建缓存和一次性大型测试存档，不删除源码、PDK/工具依赖、当前运行镜像/
仿真器/REF、核心审查矩阵、STA网表及指标报告；不调用git clean或整目录rm -rf。

已确认候选分类：大于1MiB的.gch预编译头缓存、STA详细yosys.log、CRP归档ramdisk副本、
F0018一次性raw快照数据、nanos生成resources.o、大于1MiB的tmp旧波形。
最终仅删除实际占用至少1MiB的精确文件清单，保留小型反例/稀疏输入；检查根/最近嵌套仓库均未跟踪；不追随符号链接，不清理工作区外/tmp。
保留日志尾部/原文件SHA及结果报告，记录哪些历史manifest将因授权清理出现缺失。

验收：删除项均为已核对候选，跟踪源码/当前binary/配置/PDK保护哈希不变，index空；
报告实际释放空间和剩余大目录。此次清理会使归档原始大文件无法直接复核，保留原验证
事实、文本结论/哈希和复现输入；不能把哈希视为原字节备份。完成后停止，不自动提交
维护文档或开始CRP下一项；本轮用户“提交”对应已报告的F0018修改。


## 执行结果

**清理Completed。** F0018已提交37b3195；本维护结果尚未commit，本轮不Start F0021。
仅按冻结清单逐个unlink普通文件，根/最近嵌套仓库均未跟踪；不跟随符号链接，不删除
整棵build或工具依赖。删除前核对device/inode/尺寸/mtime并记录SHA256；29条删除
日志均已落档，全部目标路径已不存在。

| 分类 | 文件数 | 删除前实际分配字节 | 约MiB |
|---|---:|---:|---:|
| STA详细yosys.log（保留每份末64KiB） | 9 | 1,092,628,480 | 1042.0 |
| 预编译头.gch缓存 | 11 | 810,164,224 | 772.6 |
| CRP归档ramdisk副本 | 4 | 593,539,072 | 566.0 |
| F0018一次性完整raw快照 | 3 | 402,677,760 | 384.0 |
| nanos生成resources.o | 2 | 149,397,504 | 142.5 |

29个文件原分配共3,048,407,040B。独立du -s -B1测量整个工作区：
8,124,690,432B → 5,076,992,000B，净减少
3,047,698,432B，约3.05GB / 2.84GiB。
净值包含新增的小型清理记录/日志尾部，故略小于删除文件的块占用之和；后续留档只增加少量文本。

删除后核对868个受保护文件SHA256全部不变，包含所有根仓库tracked普通文件、当前
NEMU/native/REF/NPC binary及配置、当前navy ramdisk/游戏资源、主要CCR覆盖矩阵、
Linux Image等。清理后、记录附记写入前，tracked working tree及index均干净；
其后差异仅本维护的索引/说明/状态。未重跑业务测试，删除对象不含运行产物；
不从这次哈希检查推定完整功能重验。

## 剩余大目录及保留依据

- npc/verif/build约1.69GB：其中约1.5GiB是Linux完整源码树nemu-src，非临时编译产物；内核/boot镜像与恢复配置保留。
- npc/verif/sta约975MB：保留历史STA网表/源码截面、面积/时序/功耗报告；清理的是大型详细综合日志。
- npc/verif/records约925MB：核心CCR逐文件覆盖矩阵、条件/审阅证据与修复日志保留，不能把它们一概当作临时缓存。
- yosys-sta约429MiB含PDK和工具；navy-apps/fsimg约111MiB含当前应用资源；Mill launcher jar等现有工具依赖保留，避免以后需要重新下载/安装。
- 当前navy-apps/build/ramdisk.img、NEMU/native/REF/NPC可执行文件保留；仅nanos的resources.o需下次make时重新生成，.gch缓存也会按正常构建重建。

本轮只清理当前工作区，未处理工作区外/tmp已有测试副本。小型故障夹具及F0018稀疏
截断输入保留；不为几十KiB收益破坏反例资料。未改任何源码/Make/.gitignore全局规则，
未安装、下载、push或触发业务Phase。

## 证据持久化变化及恢复

按用户本轮明确授权，CRP F0037/F0038、F0033/F0056、F0034/F0035/F0036和F0085的
4份大型归档ramdisk副本，以及F0018 original/active/restored完整raw已删除。
对应历史manifest的这些条目现在是**授权删除**，不是技术验收被重写，也不是当前
源码漂移。原报告/命令/输入长度/结果/哈希仍保留；若要逐字节复核这些旧产物，需要
依原版本/配置重建或重新运行测试，不能把SHA当作字节备份。

STA大日志保留末64KiB及原SHA，完整中间过程日志不再可直接读取。预编译头与nanos
resources.o只需沿原构建命令重建，本轮不为验证清理效果重建这些缓存。

local/deletion-manifest.json保存29份原路径、分类、logical/allocated尺寸、mtime、
设备/inode/links、SHA256及日志尾部路径；local/deleted.jsonl为逐项删除回执，
local/protected-before.json记录868项保护哈希，local/result.json和du-before/after
记录实际空间及检查结果。本记录目录local/仍按本地资产管理，不从本次F0018 commit
推定其获备份；删除后不再声称大文件原字节仍保留。

本维护完成后停止。当前提交授权仅用于已报告的F0018；新增维护说明/索引待用户
后续提交指令。未来CRP入口仍在TASK_QUEUE，本轮没有执行F0021。


<a id="approval-submit-20261018"></a>
## 用户确认与提交授权（2026-10-18）

用户“提交后继续CRP”确认已报告的清理及保留范围，授权提交维护说明/索引后恢复
CRP唯一入口F0021。复用已有删除/保护验证，提交前29删除路径仍缺失，原10项
final-validation全部通过；不重复删除、重建缓存或重跑已验收guest。实际commit
以包含本节的Git提交及local回执为准；不授权push或扩大为后续修复自动提交。


2026-10-18 实际提交回执：`485548c30d5e5238c7bcdf050de50fa6913dec36`，9文件148增2删，
暂存/实际范围一致，提交后root/index干净、未push；复用清理核对、未重复删除。
local/submit-precheck.json、submit-receipt.json保存回执。用户同条授权恢复CRP，
本轮随后执行F0021；原Pending为维护提交前截面。

<a id="crp-build-audit-20261018"></a>
## CRP存档构建资产盘点（2026-10-18）

计划/授权：用户“提交，检查所有crp任务的存档目录，对每个目录，是否都有独立的nemu等build文件的存档？”；
F0022已确认提交bc7a110。本维护单元仅盘点records下CRP任务目录，逐一统计隔离源码、
build/obj目录、ELF/对象/库/镜像及占用，避免将日志或symlink当独立构建。
不重新运行测试、不开始F0023。交付本节逐目录结果、local/crp-build-audit.json详细清单及过程索引。
验收：所有顶层CRP任务均有一行、嵌套快照不重复计任务；实际块占用/文件类型有据，
说明完整源码构建副本、仅二进制/对象和纯文本差异。结果落档后停止。

### 盘点结果

**检查完成，未删除任何资产。** F0022实际提交bc7a110（六份文件，提交范围/空白通过）；
本轮无产品代码修改，无测试重跑，不Start F0023/M2。

共19个顶层CRP任务目录，总实际块占用217,047,040B，约206.99MiB。
18个含编译产物/镜像，只有F0052未发现此类产物；13个含名为build或obj-*的目录，
并不表示保存了完整独立产品构建。7个含实际NEMU执行器或REF副本；只有F0022
保留隔离NEMU/AM必要源码与实际构建树（也不是整个工作区或完整工具依赖的备份）。

识别出的ELF、ar库、对象、.gch及.bin/.img/.raw镜像共40,062,976B，约38.21MiB，
截图另计123,473,920B，约117.75MiB；其余约51MiB为源码截面、配置、日志、JSON、
反汇编及目录开销。故这些CRP目录目前没有GB级独立build副本；较大目录主要由截图
及文本证据构成，不能从目录总量推定其全是可删除缓存。前轮清理的大镜像/raw/gch已不在本次清单。

下表“占用”包含该任务所有证据；“产物”列仅统计上述二进制/镜像类型的实际块占用，
不含截图/日志/源码。“NEMU/REF”不把名字带nemu的guest或host夹具当成NEMU本体。

| CRP目录（共同前缀code_correctness_review/） | 占用MiB | 产物MiB | 实际NEMU/REF副本 | 当前构建存档内容 |
|---|---:|---:|---|---|
| crp-compatibility-20261018 | 24.88 | 8.89 | 有 | NEMU前/候选/后binary；RT/nanos部分build、host程序 |
| crp-f0010-f0011 | 26.88 | 8.04 | 有 | NEMU前/后及探针binary；host程序，无整棵build |
| crp-f0012-f0013 | 1.20 | 0.75 | 有 | nemu-wp及obj-wp对象；host程序 |
| crp-f0014 | 1.86 | 1.22 | 有 | REF前/后.so；NPC binary/RT bin，无独立NEMU执行器 |
| crp-f0015 | 3.13 | 0.41 | 无 | build内host测试程序/对象；5份局部source快照，无NEMU构建树 |
| crp-f0018 | 0.42 | 0.24 | 无 | host测试程序、小型raw反例；大raw快照前轮已清理 |
| crp-f0021 | 1.50 | 0.76 | 有 | nemu-ftrace及obj-ftrace对象；host程序/ELF用例 |
| crp-f0022 | 6.47 | 2.82 | 有 | 隔离local/nemu与local/am必要源码、实际build/对象/库/native与RISC-V镜像 |
| crp-f0033-f0056 | 21.89 | 3.33 | 无 | RT/nanos/string-test/klib部分build；无NEMU执行器副本 |
| crp-f0034-f0035-f0036 | 19.74 | 1.14 | 无 | RT/nanos/stdio-test/klib部分build；无NEMU执行器副本 |
| crp-f0037-f0038 | 20.22 | 1.58 | 有 | NEMU native/REF及NPC binary；RT/nanos/stdlib部分build |
| crp-f0039-f0040 | 5.19 | 2.26 | 无 | RT/nanos/CPP/klib部分build及host程序；无NEMU执行器副本 |
| crp-f0041-f0042-f0053 | 18.80 | 1.17 | 无 | RT/nanos/NPC用例部分build及host程序；无NEMU执行器副本 |
| crp-f0045 | 18.35 | 1.28 | 无 | RT/nanos/双平台guest ELF/bin和host程序；host/nemu是局部测试夹具 |
| crp-f0046-f0048-f0050 | 10.57 | 2.45 | 无 | NPC binary、RT/BSP ELF/bin及部分build；无NEMU执行器副本 |
| crp-f0049 | 1.70 | 0.78 | 无 | RT部分build及host程序；无NEMU执行器副本 |
| crp-f0051 | 2.39 | 0.48 | 无 | RT ELF/bin；其余为源码/文本/脚本证据 |
| crp-f0052 | 3.61 | 0.00 | 无 | 没有ELF、对象、库或raw镜像；fake工具/脚本/文本见证 |
| crp-f0085 | 18.20 | 0.60 | 无 | nanos ELF/bin、多个小型host程序；无NEMU执行器副本 |

例如用户当前打开的crp-f0034-f0035-f0036：没有独立NEMU执行器或源码build树，
但local/artifacts下保留nanos-lite/build、navy-apps/build、abstract-machine/klib/build、
stdio-test/build、rt/bsp/abstract-machine/build的部分产物。总19.74MiB中产物约1.14MiB，
其余主要是截图与记录。F0022的local/nemu/build约1.33MiB，整个任务约6.47MiB。

核对方式：find定位records下全部crp*目录；把F0015内部5份同名局部source快照计入
所属任务而非新增任务。os.walk不追随符号链接，检查文件ELF/ar魔数和镜像/对象后缀，
逐目录du -s -B1核算块占用；记录每份产物的相对路径、逻辑大小/分配字节，以及
源码/build目录、symlink、最大文件。F0022的riscv64→riscv32 symlink单独登记，未重复计目标。
嵌套build目录的du数不可再次相加（父目录已包含子目录）；总量只汇总19个互不嵌套任务根。

原始清单：local/crp-build-audit.json；盘点脚本local/crp-build-audit.py。
二者本地忽略，不从git提交推定已有备份；本段报告/过程索引等维护说明尚未提交。
本轮不修改CRP既有manifest或重新判定历史验收；“有产物”也不保证完整可复现，
尤其/tmp测试树不属于这些存档目录，不能将历史外部构建路径视为本地存档备份。
下一动作仅为用户复核本次盘点结果；未来CRP实施仍只沿TASK_QUEUE唯一入口。
