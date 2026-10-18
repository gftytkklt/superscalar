# CRP F0018 — load 失败保留 CPU/PMEM

## 计划与授权（2026-10-18）

用户“提交，继续”确认前组结果，授权F0014提交后执行唯一下一单元；前组实际提交
`194d2c0`，提交后root/index干净。沿用[CRP规则](../workflow/README.md)及原问题
F0018/P3证据，不推进M2。本单元只改native monitor cmd_load，兼容原命令及
CPU_state+PMEM raw格式；不新增版本/校验和/全机恢复协议，不改save的既有格式。

目标：读入临时CPU及PMEM，所有必要读操作和文件关闭成功后才替换活状态；打开、
分配、短读、IO错误时CPU/PMEM逐字节保持，释放临时内存/文件后仍可继续执行。
原格式不包含设备、timer、REF、watchpoint或其他模拟器全局状态，此限制保持。

本单元为逐项修复/组合验收边界：先最小生产修改和原版见证，再host ASan/UBSan
与真实native CLI验证；产出本报告/局部ignore、records索引/逐项镜像/.agent与
本地证据，完成后停止等待用户确认/commit，不自动提交或下一单元。

验收：CPU/PMEM多个代表截断点、空文件、缺文件/路径、分配失败、读/close错误，
失败前后CPU/PMEM逐字节一致，无资源泄漏；完整既有raw快照成功恢复、再次保存
字节一致并继续真实guest到GOOD TRAP。host夹具注入难以稳定制造的IO/分配失败，
真实CLI覆盖原save/load和截断文件。按调用影响不重跑不消费此交互命令的NPC/RT/
nanos/CPU全集；保留全部未测限制。无安装/新策略裁决事项；若发现真实契约冲突
则停止相关实施，不能以继续推定批准。


## 实施与逐项结果

**Completed，结果确认/commit Pending。** HEAD仍为前组194d2c0；Working tree
contains uncommitted CRP repair/documentation changes，index空。仅生产文件
`nemu/src/monitor/sdb/sdb.c` 的cmd_load修改：CPU结构读入栈上临时对象，PMEM读入
malloc(CONFIG_MSIZE)内存，检查两次fread、ferror及fclose后才memcpy到活状态。
任一失败都关闭文件/释放临时内存并返回，不改变活CPU/PMEM。save格式/命令未改。

| 验证 | 本次结果/证据 |
|---|---|
| 原版三反例 | CPU缺最后1B、PMEM缺最后1B、完整read但FILE错误标志三个场景均被状态memcmp断言判失败（exit1）；原版前两者提示load失败却已改活状态，第三者误报成功。local/before-*.log |
| 修复后定向 | 三反例全部通过；ASan/UBSan组合16场景/124断言通过，含7个截断点、打开失败、分配失败、两次read分别短读、ferror、close失败、连续两次完整成功和真实缺文件。每场景检查整个CPU/PMEM、数组canary、文件与临时分配余额。local/host-results.json、after-all.log |
| 真实native构建 | 原make app入口重建/链接成功；未改.config、headers、Make或REF产物。local/build.log、identities.json |
| 真实native CLI | 当前CPU440B、PMEM128MiB；si 1后保存不同的active快照。无参数、缺文件、目录IO错误、0/1/439/440/441/67109304/134218167B截断共10场景，每次失败后再次save的全CPU/PMEM哈希均与active一致。21项判据全部通过，local/cli-results.json、cli.log |
| 成功及继续运行 | load原完整raw快照后再次save与original逐字节身份相同，PC从0x80000004回到0x80000000，扫描原指令正确，c到GOOD TRAP/exit0；不是只检查命令返回0 |
| 最终核对 | local/validation.json共14项全部通过；源码/配置/真实binary身份与测试一致，前组HEAD/index/空白检查通过 |

host直接引用原/新完整sdb.c及真实项目头文件，临时配置仅将PMEM缩为4KiB，以便
检查全部字节并注入确定的malloc/read/close错误；CPU结构仍真实RV64的440B。
CPU执行、内存映射和非load命令在该夹具中为隔离stub，不替代真实128MiB CLI。
真实CLI使用未改动save命令记录整个状态，并核对实际文件长度及哈希。

初次启用LeakSanitizer被当前执行环境以ptrace不受支持拒绝，initial-lsan结果/
日志保留，未计入PASS；随后使用ASAN_OPTIONS=detect_leaks=0:abort_on_error=1及
UBSAN_OPTIONS=halt_on_error=1得到上述有效结果。未宣称LSan通过；夹具的文件/
分配计数验证各错误路径均释放本次资源，ASan/UBSan无错误。

## 命令、身份与本地证据

```sh
CCACHE_DISABLE=1 make -C nemu -j4 app NEMU_HOME="$PWD/nemu" 'git_commit='
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy nemu/build/riscv64-nemu-interpreter < npc/verif/records/process/code_correctness_review/crp-f0018/local/cli-input.txt
```

第一条清空教学tracer的git_commit宏，构建不自动提交；CCACHE_DISABLE只对本次进程
生效。第二条展示原真实CLI调用；复跑应使用新输出目录/替换输入中的路径以保留
现有证据。真实运行的完整输入、原始输出、退出码/逐场景比较及参数分别在
local/cli-input.txt、cli.log、cli-results.json、cli-fixture.json。

- local/before/sdb.c、sdb.after.c、repair.patch：源与精确生产差异。
- local/harness-{before,after}.c、host-commands.json：一次性白盒夹具与精确gcc/执行argv；-O1 -g、-fsanitize=address,undefined、-fno-omit-frame-pointer、-no-pie，真实项目头文件加本地4KiB配置。
- local/cli/{original,active,restored}.raw：真实完整状态及恢复证据；截断输入为稀疏文件。10份重复失败后完整输出已在比较哈希/长度落档后删除，避免重复保存约1.25GiB，结论和哈希保留在cli-results.json。
- local/identities-before.json、identities.json、validation.json、manifest.sha256：构建前/后配置/产物和同版证据身份；不会将本地产物视为已备份。

讲义参考（2026-10-18访问）：[基础设施：简易调试器](https://ysyx.oscc.cc/docs/ics-pa/1.4.html)
介绍sdb及命令解析，本页未规定save/load格式；本组raw兼容性和失败保持要求来自
本地原实现、F0018/P3及已落档下一入口，不从该页推定全机快照契约。

## 影响、限制与停点

每次load额外暂存CONFIG_MSIZE字节（当前128MiB）及一个CPU_state；不足时明确
返回失败并保持原状态。这是当前原raw文件格式的失败原子性修复，不是并发事务。
原格式无magic/version/checksum，当前仍接受原完整前缀并忽略尾随内容；无法据此
识别所有同尺寸损坏/配置不匹配文件。设备、计时器、REF/difftest、watchpoint和
nemu_state等其他全局状态仍不在原文件中；不声明全机恢复或任意时刻恢复正确。
未改save的错误处理，不把本轮验证扩写为save所有IO失败均可靠。

本批调用影响为native交互load，已验证真实内置guest的失败恢复及成功后执行；
CPU-tests全集、RT update/msh、nanos三前台/hello和NPC/REF不调用此交互load，
本轮未重跑，不以host/内置guest代替它们。未跑非RV64/完整Linux/所有PMEM配置，
分配/close错误仅host注入，真实CLI没有注入系统级故障或依赖新增安装。

累计27项已修、92项未修完（含5CQ/F0040 Partial）；前26项已提交，本组1项待
确认/提交。PAL性能、F0043协议、五CQ、F0040并发和两缺源继续保留。无新长期
架构决策，不更新DECISIONS。完成后停止，下一入口仅TASK_QUEUE；不自动提交
新修复/下一组/push/M2，不安装。local/.agent沿用本地持久化，commit不等于备份。


<a id="approval-submit-20261018"></a>
## 用户确认及提交授权（2026-10-18）

用户“提交，检查该工作目录下是否仍存在占据大量空间的临时文件存档，如有直接删除”
确认本组已报告结果并授权提交，以及独立的空间检查/清理；不授权开始F0021。
提交前45条manifest逐字节无漂移，原14项validation全部通过、index空；复用16场景/
124断言和真实CLI21项验收，不重跑。只提交本组生产修复、报告/局部ignore、索引/
修复状态及前组实际提交回执；实际commit见包含本节的Git提交及local提交回执。
本地证据大文件后续若按本轮明确清理授权删除，须记录路径/身份及持久化影响，
不能从commit推定ignored资产已备份。不push、不自动进入新修复单元。


2026-10-18 实际提交回执：`37b3195b0ac0f4504165964d2f1b49aa71f09c82`，6文件149增7删，
暂存/实际文件集一致，提交后root/index干净、未push；45条manifest/原14项validation
复核通过，复用原验收。local/submit-precheck.json、submit-receipt.json保留回执。
用户同条指令转向独立空间清理，不Start F0021；原Pending为提交前截面。


2026-10-18 空间清理附记：用户明确授权删除工作区大型临时存档。本目录的大型归档
ramdisk或一次性完整raw测试快照已按[清理记录](../../workspace-storage-cleanup-20261018/README.md)
精确删除，原路径/尺寸/SHA见该记录local/deletion-manifest.json；原文本验收/命令/
结果与哈希保留，历史manifest缺失项须结合该授权清单解释，不视为源码漂移或验收
事实变更。旧产物字节不再本地保留，需复核时按原版本/配置重建或重新运行测试。
