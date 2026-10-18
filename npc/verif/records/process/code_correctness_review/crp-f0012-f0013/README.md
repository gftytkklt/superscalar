# CRP F0012/F0013 — monitor 输入与 watchpoint 边界

## 计划与授权（2026-10-18）

用户“继续CRP修复”授权 TASK_QUEUE 唯一入口的一个工作单元；前组已确认提交
`12afa5894afb86b82ff4f2609aef451c553221c3`，root/index 干净。沿用现行
[CRP 规则](../workflow/README.md)，F0043、五 CQ、F0040 Partial 和 PAL 性能风险
不依赖本组且继续保留。本轮不 commit/push、不推进 M2、不安装。

目标：F0012 的 token 数量/存储边界和 NULL/空输入安全拒绝；F0013 在分配前检查
表达式保存长度，保留首次求值的完整文本，处理池耗尽并验证释放复用。仅修改
`nemu/src/monitor/sdb/` 中相关实现，不改正常命令、ISA、REF 或 Make 接口。

本组作为一个执行/验收单元：逐项最小修复与定向验证，最终组合真实 native CLI
验收并留档。验收包括 NULL/空白、31/32/33 token、31/32/33 字节数字及长输入、
127/128/129 字节 watchpoint 文本、32 项耗尽/释放复用、含 n 文本与正常求值。
host ASan/UBSan 使用生产源码；真实 native CLI 验证 p/w/x、info/d 以及真实 guest
执行。CPU/RT/nanos 批处理及 NPC 不链接或不调用此交互修复，不机械重跑全套。

无人工裁决/安装事项；若发现真实契约冲突则停相关项。完成后同步记录索引、逐项
状态和 .agent，停止等待用户确认/提交，不自动进入下一组。一次性测试/日志/快照
保留在本地 `local/`，不纳入提交；commit 也不代表这些资产已备份。

参考（访问 2026-10-18）：[表达式求值](https://ysyx.oscc.cc/docs/ics-pa/1.5.html)
明确 token.str 的有限容量须处理溢出；[监视点](https://ysyx.oscc.cc/docs/ics-pa/1.6.html)
说明固定池分配/释放及按表达式值变化暂停。项目本次选择可恢复拒绝，沿用已落档验收。


## 逐项结果与组合验收

**Completed，结果确认 Pending，commit Pending。** 根 HEAD 仍为 `12afa58`，
Working tree contains uncommitted CRP repair/documentation changes；index 空。

| 问题 | 修改及失败语义 | 验收 |
|---|---|---|
| F0012 | 入库前检查 32 项 token 容量；按匹配长度拷贝，去掉 hex 的 0x / reg 的 $ 前缀后最多保存 31 字节，并显式补 NUL；忽略空格不占容量。NULL、空/全空格输入不进入 eval，返回 0 且 success=false | 原版 NULL/33 token/32 位十进制反例失败；修复后 31/32/33 token，31/32/33 位 decimal/hex 数据、1000 位数字、1000 空格及正常算式通过 |
| F0013 | 使用同一 args 求值和完整复制，分配前拒绝 >=128 字节文本；new_wp 返回 NULL 时直接返回、不改已有节点。新建/复用时 triggered_time=0 | 原版 129 字节可求值文本和第 33 项分配失败见证；127 字节完整保存/重求值、128/129 字节拒绝、32 项耗尽/删除复用/全释放、命中计数重置通过 |

边界按 **存储数据** 计数：decimal 32 字节拒绝；hex 去除 0x 后 31 位仍可存，
32 位拒绝。每次失败后再次正常求值/建点验证恢复。未重写原 evaluator 的优先级、
数值溢出/截断或非当前 ISA 配置语义，不把本批边界修复记成全表达式规范证明。

原版与修复版使用同一夹具、真实生产 expr/sdb/watchpoint 源码。ASan/UBSan 下：
7 个独立场景中原版 6 个失败、1 个 hex 拒绝对照通过；修复版 7/7 通过，组合
**332 次断言检查通过**，无 sanitizer 报错。5 个失败是本组产品输入/池边界，
第 6 个含 n 文本场景使用隔离寄存器 stub，见下述限制。长文本原版失败由状态断言
捕获，不冒称 sanitizer 抓到了结构体内部越界。

真实 RV64 native CLI 两套构建（现有配置、仅额外定义 CONFIG_WATCHPOINT）分别
通过 15 个结果检查；另有开启 watchpoint 的真实内置 guest 执行通过 7 个检查，
共 **37/37**。覆盖 p 无参数/空白/长数/token、x 正常内存读取、w 空输入/文本长度、
info w、32 项耗尽不崩溃、d 后同编号复用、末尾正常 p=42，以及 c 到 GOOD TRAP。
真实 `$pc` 监视点在两条指令后分别记录 80000004/80000008 并暂停，复用命中次数
从 0 开始；删除后内置 guest 正常 GOOD TRAP，3 次 CLI 退出码均为 0。

**含 n 证据边界**：现有合法寄存器名无 n，真实 `$tn` / n 均拒绝且不占池；
不能声称原产品接受 `$tn`。隔离夹具仅令寄存器 stub 接受 lexer 可识别的 `$tn`，
从而独立证明原 `%[^n]` 会截断、修复后完整保存 `$tn+1` 且再次求值一致。
该 stub 不属于产品或新能力。真实 watchpoint 自动触发由上述 `$pc` 用例证明。

## 命令与本地证据

构建使用既有 make 入口；命令行清空教学 tracer 的 git_commit 宏，避免验证自动提交。
CCACHE_DISABLE=1 绕过只读缓存目录，不修改环境配置/安装软件：

```sh
CCACHE_DISABLE=1 make -C nemu -j4 app NEMU_HOME="$PWD/nemu" 'git_commit='
```

watchpoint 构建额外使用 `CFLAGS_BUILD='-O2 -DCONFIG_WATCHPOINT'`，OBJ_DIR/BINARY
指向本组 local/obj-wp 和 local/nemu-wp，不改 .config 或 Makefile。CLI 使用
`SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`，输入 local/cli-input.txt，执行
nemu/build/riscv64-nemu-interpreter 与 local/nemu-wp；触发用例输入
local/cli-trigger-input.txt。guest 为 nemu/src/isa/riscv64/init.c 原内置程序，无 fake CPU。

host 编译/执行 argv 完整保存在 local/host-commands.json；gcc 使用 -O1 -g、
-fsanitize=address,undefined、-fno-omit-frame-pointer 和 -no-pie，引用真实项目头文件。
运行设置 ASAN_OPTIONS=detect_leaks=0:abort_on_error=1、UBSAN_OPTIONS=halt_on_error=1。
local/harness-{before,after}.c 为一次性白盒测试，寄存器/内存读取是隔离 stub，
没有替代真实 CLI 的 CPU/内存/寄存器消费者。

- local/before、after、repair.patch、identities.json：同版源码/配置及两个 native binary SHA256。
- local/host-results.json、{before,after}-*.log：7 组对照与 332 检查结果；hex 对照原版本就拒绝，不计作原版失败。
- local/build*.log、cli-*.log、cli-results.json：真实构建/命令回显/输出与 37 结果检查。
- local/validation.json：13 项最终证据/源码/HEAD/index 检查；local/manifest.sha256 为本地证据身份。

## 影响、限制与停点

只改 native sdb 的 expr.c/sdb.c；watchpoint.c/sdb.h 未改。TARGET_SHARE 的 REF 和
TARGET_AM 均不依赖 native 交互输入；guest ABI、CPU 执行器、AM/klib/设备实现未改。
本批真实消费者是 native monitor，已额外覆盖 CONFIG_WATCHPOINT 执行链。
CPU-tests 全集、RT update/msh、nanos 三前台/hello、NPC 不调用本次改变的交互命令，
故本轮未重跑；3 次内置 guest GOOD TRAP 不是这些产品回归的替代证明。
未跑非 RV64、超大输入压力、完整表达式语法矩阵或实际窗口/音频。

全部功能已修 **25**，未修完 **94**（含 5 CQ、F0040 Partial）；本组 2 项未确认/
未提交，之前 23 项已提交。PAL 性能因果、F0043 协议、五 CQ、F0040 并发及两缺源
继续保留，既有延期仅作用于相关范围。无新长期架构裁决；不改 DECISIONS。

本组完成后停止；下一入口只在 TASK_QUEUE#crp-next，须本批用户确认/commit及后续
执行授权。不自动提交/下一组/M2，不 push。一次性测试、binary、日志与 .agent
仍为本地资产，不随普通提交备份。


<a id="approval-submit-20261018"></a>
## 用户确认及提交授权（2026-10-18）

用户“提交，继续”确认本组已报告范围并授权提交，然后执行 TASK_QUEUE 下一单元。
本次复用 host332/真实CLI37及三次内置guest验收，不重跑；提交前51条manifest
逐字节无漂移、原13项validation全部通过、index空。提交仅纳入两份生产文件、
本报告/局部ignore、repair-status与process索引；local测试/日志/binary和.agent
沿用本地持久化，不纳入提交。实际commit以包含本节的Git提交及local提交回执为准，
不将尚未执行的Git操作写成已完成。确认不扩大未测范围，不授权push或其他业务M2。


2026-10-18 实际提交回执：`77a9471d6da2ccbee3a5180b39852bedbe9189c5`，6文件156增20删；
精确匹配已核对的暂存清单，提交后root/index干净、未push。提交前51条manifest无漂移，
复用已报告验收。local/submit-precheck.json和submit-receipt.json保存回执；原Pending
为提交前截面，不重做Completion。按用户同条指令，提交后开始独立F0014单元。
