# CRP — CCR-F0017 QEMU RV64 adapter 必要分析

## 现行处置（用户2026-10-21裁决）

**F0017 Closed / QEMU不作为difftest来源，未实施、不计已修；用户已确认并授权提交本批分析。**
当前119项=103已修+12 CRP待修+2 Linux能力扩展移交+2无需实施闭合（F0017/F0084）。
下文“等待QEMU环境/分析确认或commit Pending”为分析完成时历史截面，
现由[本次范围闭合](#qemu-scope-closure-20261021)覆盖；不再要求为本问题安装QEMU或补真实QEMU验收。

## 本轮计划与范围（2026-10-21）

用户“继续CRP修复”承接 `.agent/TASK_QUEUE.md#crp-next`，前F0084已确认提交
`7eb4c6c235f51657192033586dcfaee3dc439d42`，根working tree/index干净，无状态冲突。
本单元仅核当前adapter/构建入口、寄存器包、物理地址ABI和失败语义，复用既有CRP整体计划及workflow。

交付：正常/失败反例、实际源码和配置身份、所查上游资料、最小修复建议及验收缺口；
更新本报告、records索引、逐项修复镜像和本地状态。
验收：当前源码隔离编译/运行，区分mock与真实QEMU，说明布局/长度/高地址边界、实际构建闭包和消费者影响；
不凭历史union布局推定远端协议，不把分析完成记为修复完成。
停止节点：本分析完成留档后停止，安装、QEMU版本/支持范围等真实人工决定交用户；
不安装、不改生产源码/现行配置、不commit/push、不进入其他组或M2。

证据在 `local/`，一次性夹具不提交；编译产物验收后清理，保留命令、日志、源码身份与最小重建配方。

## 本阶段结论

**必要分析 Completed；F0017 仍未修，分析结果确认/commit Pending。**
当前119项仍为103已修+13 CRP待修+2 Linux能力扩展移交+1无需实施闭合；不增加已修数。
本轮只修改分析报告/索引/状态，没有生产源码或配置修改。

1. 当前QEMU RV64标准构建首先失败；明确宏后可编译的旧源码还存在回复越界解码、错误回复被接受、
   写失败不传播、地址/长度缩窄问题。
2. **更正原审阅中“前33字会把FPR0当PC”的推断。** 原union声明的`pc`确在字64，
   但远端PC位置不能由这个C结构推定。所查QEMU上游把PC编号定为32；mock正常对照证明，
   若包前缀为32 GPR+PC，当前`memcpy`前264字节能正确传PC。不能据此把union声明和包长问题一并撤销。
3. PATH及定向文件查找未发现`qemu-system-riscv64`/`qemu-system-riscv32`；真实目标版本、
   machine/CPU、target description与g/G包均 **Unknown / NotRun**。实际安装/版本支持范围未由agent代决。

## 当前可达闭包与配置身份

基线根HEAD为`7eb4c6c235f51657192033586dcfaee3dc439d42`，文件SHA256见`local/entry.json`。
本轮源码均来自此工作树，逐文件身份终检保持。`.config`实际为RV64、32 GPR、
`CONFIG_DIFFTEST`关闭、REF路径/名称为`none`；原P3“选Spike”是历史截面，不能当作本轮配置。

可选入口：`nemu/Kconfig` 的`DIFFTEST_REF_QEMU` → `tools/difftest.mk`递归
`GUEST_ISA=riscv64` → `tools/qemu-diff/Makefile` → adapter共享库 → NEMU的`--diff`/`dlsym`。
本轮没有切换主配置，也未运行NEMU主Make的自动commit hook。

独立调用adapter既有Make，输出重定向到本组`local/build/standard`：

```sh
make -s -C nemu/tools/qemu-diff GUEST_ISA=riscv64 \
  NEMU_HOME="$PWD/nemu" CC=/usr/bin/gcc \
  BUILD_DIR="$PWD/npc/verif/records/process/code_correctness_review/crp-f0017/local/build/standard" \
  OBJ_DIR="$PWD/npc/verif/records/process/code_correctness_review/crp-f0017/local/build/standard/obj" \
  BINARY="$PWD/npc/verif/records/process/code_correctness_review/crp-f0017/local/build/standard/qemu-so"
```

实际exit2，首对象`diff-test.c`报`#error Unsupport ISA`。Make只给
`-DCONFIG_ISA_riscv64`，`isa.h`判断`CONFIG_ISA_riscv`/`CONFIG_RV64`；
`common.h`在读取`isa.h`前没有导入generated配置，`diff-test.c`稍后才经`difftest-def.h`导入，
其他adapter翻译单元更没有该入口。该错误先于QEMU启动，不表示包错误已不可达或已修复。
隔离反例统一给所有翻译单元显式宏，只为观察旧实现，不作为正式构建修复或日常替代步骤。

## 所查上游依据与历史判断勘误

2026-10-21查阅官方ICS-PA [DiffTest章节](https://ysyx.oscc.cc/docs/ics-pa/2.4.html#differential-testing)：
强调寄存器顺序与初始化同步；现行讲义的RISC-V参考为Spike，QEMU示例主要为MIPS，
没有给当前RV64 QEMU adapter提供“FPR在PC之前”的依据。

核对QEMU **v9.2.0源码标签**（只作上游静态参照，不是本机已安装/选定版本）：

- [RISC-V gdbstub](https://raw.githubusercontent.com/qemu/qemu/v9.2.0/target/riscv/gdbstub.c)：
  `n<32`读GPR，`n==32`读PC，RV64返回64位；FPU等另注册，`g_pos=0`。
- [通用gdbstub](https://raw.githubusercontent.com/qemu/qemu/v9.2.0/gdbstub/gdbstub.c)：
  g/G按`gdb_num_g_regs`处理；coprocessor的`g_pos=0`不扩展该范围。
- [CPU初始化](https://raw.githubusercontent.com/qemu/qemu/v9.2.0/target/riscv/cpu.c)：
  RV64选择`riscv-64bit-cpu.xml`。

据这些源码，正常core模型按32 GPR+PC（264字节/528 hex字符）建立反例；
XML原文多次请求Cache miss，真实远端XML也未获取，因此这只是上游支持的候选包模型，
**不能宣称已动态确认某个本机QEMU包、FPR总数或整个target description**。
`local/upstream-sources.json`记录成功/失败资料与限制。没有下载二进制、克隆或构建QEMU。

原审阅`FINAL_FINDINGS`/P3历史快照保留，追加本报告的勘误链接；不覆盖历史证据。
应把最小修复目标改为“构建一致性、实际core包长/失败验证、地址ABI一致”，
不能按旧误判把真实编号32的PC迁到字64。

## 当前源码实际观察

`local/probe.py`分别编译未改的`gdb-host.c`、`diff-test.c`和`protocol.c`。
只替换连接/收发边界；hex编码/解码仍用原`protocol.c`，无网络或真实QEMU。
所有执行30秒上限；精确命令/退出码在`local/commands.json`（20条，包括1次预期构建失败、8次成功编译链接、11次运行）。

| 场景 | 实际结果与证明范围 |
|---|---|
| 520B完整mock正常包，普通+ASan/UBSan | 两次exit0；union=520、声明pc偏移512、DUT=264；前缀PC=`1234567880001234`、尾哨兵=`feedfacecafebeef`，实际DUT读到前缀PC。此控制包不是实际QEMU采样 |
| 264B core包，4096B填零底层容量 | exit0且`get_ok=1`；前缀PC正确，但仍解码至520B，读取超出有效回复的内容 |
| `E01`回复，4096B填零容量 | exit0且`get_ok=1`；未拒绝错误回复，伪造出寄存器内容 |
| 1040个`z`的非hex回复 | exit0且`get_ok=1`；未检查hex有效性 |
| TO_REF写入收到`E01` | exit0且调用返回，发出的G命令1041字符（520B数据）；`difftest_regcpy`忽略`gdb_setregs`的false |
| 高地址`0x100000123`、1B | 发成`M0x123,1:00`；当前adapter入口`paddr_t`先截断 |
| `0xffffff00`跨边界1501B | 首包1500B，第二包地址`0x4dc`；32位分块游标回绕 |
| `size_t n=0x100000001` | 只发1B；传入`int len`发生缩窄，未实际分配/读取4GiB |
| 264B与空回复，精确分配容量，ASan/UBSan | 两次预期exit1，原`gdb_getregs:71`的`p[8]`发生heap-buffer-overflow；不是修复后的PASS |

ASan最后两例用精确回复分配暴露函数越界，不等于真实QEMU路径一定触发同样ASan报告：
实际`protocol.c`初始分配4096B，短包下更直接的问题是解码有效长度外的未初始化容量；
填零容量测试只证明可以错误接受，不以填充值冒充实际未初始化字节。

物理地址ABI另单独编译NEMU真实`common.h`：当前配置`word_t=8/paddr_t=4`；
隔离generated配置只改`CONFIG_MBASE=0x100000000`后为`word_t=8/paddr_t=8`。
adapter始终`paddr_t=4`。因此“RV64一律paddr64”也不符合当前主工程ABI；
应按主工程的`CONFIG_MBASE+CONFIG_MSIZE`判定统一类型，并在传输/分块/格式化全链保持宽度。
高地址反例是原函数边界观察；当前正式128MiB低地址配置没有真实高地址可运行，不声称已经验证高地址RAM。

## 最小修复建议与后续验收

生产方案尚未实施；候选边界仅QEMU adapter内部，不改Make目标/选项或用户执行流程：

1. 所有翻译单元在ISA分支与地址类型前读取同一generated配置，修复标准RV64构建入口。
2. 按所选QEMU真实core描述确定32 GPR+PC包；RV64结构/实际传输长度一致，显式核对PC编号32。
   `array[77]`本身也会影响union大小，不能只移动`pc`并继续用`sizeof(union)`作为协议长度。
   保持其他ISA既有布局，不引入完整XML解析器或FPR/CSR/priv对拍新能力。
3. 解码前核长度、错误回复、hex有效性；只在完整有效时发布寄存器。
   g/G失败必须传至void difftest接口的明确诊断终止，不能继续冒充同步成功；不增加可恢复错误API。
4. 按主工程配置统一`paddr_t`，传输地址/格式化/分块计数全链一致；保留`size_t`长度并防端点回绕。

后续验收须先获得实际QEMU可执行文件及版本：读取目标XML/core描述和g包，
在支持machine/CPU配置下验证GPR/PC哨兵双向同步、单步、低/高地址内存读回与跨MTU边界；
短包/非hex/错误回复需定向故障注入，标准Make与实际NEMU→QEMU小guest链必须通过。
具体machine/CPU/内存映射以实际版本核定；不能用本轮mock替代，也不凭上游标签安装特定版本。
共享legacy路径若修改，补受影响ISA构建/包回归；其余CPU-tests/RT/nanos当前未链接此adapter，
本分析生产diff空，故未重跑这些消费者；既有Spike/native/NPC结果不冒充QEMU验收。

本轮结束节点已到：请用户提供现有`qemu-system-riscv64`路径，或自行完成安装后续作；
若当前目标不需要可选QEMU路径，也须用户明确范围裁决，agent不因当前DIFFTEST关闭自动闭合。
安装停点直接来自[WORKFLOW_POLICY §3](../../../../docs/WORKFLOW_POLICY.md#3-人工确认--软件安装-停点触发即停)，
生产修复/实际QEMU验收未完成；无需先commit分析才能补充环境继续同一F0017。

## 留档、保护与清理

本轮文件：本README/.gitignore、process索引、repair-status；本地忽略的FINAL_FINDINGS/REPAIR与.agent同步。
没有生产修复diff，故没有以空diff伪造框架修复归档。原始快照不改写。
正式配置/解释器、Navy盘/清单、nanos bin、RT bin/配置/清单共8资产及本轮源码逐文件SHA保持，
根HEAD/index保持；验证身份见`local/validation-preclean.json`。

复现：从上述根HEAD恢复原文件，运行本组本地`probe.py`；显式宏与mock边界见夹具。
地址宽度观察的编译命令保存在`current-width-command.json`/`high-width-command.json`；
高地址副本只改generated配置中MBASE为`0x100000000`，然后编译包含主`common.h`并打印两种类型sizeof的小程序。
副本/执行文件按清单清理，保留这些配方与日志而不保留整份源码/镜像。
本地ignored证据/.agent不由普通commit备份。唯一下一入口仍为`.agent/TASK_QUEUE.md#crp-next`。

收尾实绩：`local/validation-preclean.json` **68项PASS**，119行计数仍103/13/2/1；
`local/cleanup-plan.json`逐路径记录15项462153B构建产物/生成配置/类型观察副本的SHA，
全部子进程已回收后删除，`cleanup-receipt.json`确认15项及build目录不存在，0 tracked/正式资产。
清理后8正式资产SHA再次保持，生产diff/index空；原日志中的构建路径是当时执行身份，已删产物须按配方重建。
本轮报告与导航完成留档后停止，不commit/push。

<a id="qemu-scope-closure-20261021"></a>
## QEMU来源范围闭合与提交（2026-10-21）

用户最新明确：“不使用QEMU作为difftest来源，可关闭当前问题，执行提交”。
据此F0017按项目参考源范围裁决 **Closed / 未实施**，不是Fixed；
此前等待QEMU路径/安装、真实目标XML/包/guest及后续adapter实施的门槛撤销。
现存adapter缺陷、正常前33字PC对照和原PC判断勘误保留，真实QEMU仍NotRun，
不从范围闭合推定该adapter可用；未来只有明确恢复QEMU参考源需求时才重新评估。
当前difftest来源与配置不因本次文档提交而切换；源码/Make/Kconfig保持原样。
不向Linux转交QEMU待办，不改变Spike或NPC→NEMU REF范围，不推进M阶段。

本轮收尾计划/交付：复用已完成的68项/19项检查和15项462153B清理，
核对既有36份保留证据manifest、生产身份/8资产与计数、更新报告/索引/本地裁决及唯一入口，
仅提交本批四个归属明确路径（本README/.gitignore、process索引、repair-status）。
原问题清单/修复计划/.agent与local证据仍按既有本地忽略约定保留，commit不等于备份。
验收为119行103/12/2/2一致、无生产diff、暂存路径/内容与实际commit一致；
无新编译/guest或产品验收，不重复分析Completion，提交后记录真实回执并停止，不push/下一组/M2。

本次闭合与分析提交已获用户授权；实际commit身份在提交后的本地`closure-submit-receipt.json`
及CURRENT_STATE/CHANGELOG_AGENT补充记录中保存，避免在提交前虚构新commit。
