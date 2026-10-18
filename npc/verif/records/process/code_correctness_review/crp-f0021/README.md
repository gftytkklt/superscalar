# CRP F0021 — FTRACE ELF 输入边界

## 计划与授权（2026-10-18）

用户“提交后继续CRP”确认空间维护并授权提交485548c后执行唯一入口F0021；前组
F0018已确认提交37b3195，Start前root/index干净。沿用[CRP规则](../workflow/README.md)，
本单元只处理既有native FTRACE ELF64解析，保留正常命令/Make/ISA及原全局函数筛选。
不新增ELF32、扩展section编号、动态链接或其他业务功能，不推进M2。

目标/范围：monitor.c读取header/section/symbol/string前校验长度、表项尺寸、索引和
完整区间，避免除零、越界、未初始化值、错误字符串表及函数地址区间溢出；错误不
发布可用于trace的残缺结果。原显式-e打不开使用Assert终止启动，本次延续启动失败类：
非法/不支持输入给诊断并非零退出，不静默宣称正常trace；无新策略裁决或安装事项。

单个执行/验收单元：逐项最小修复 → 原版见证/host ASan/UBSan → 真实FTRACE native
正常调用返回/坏文件/多-e与FTRACE关闭对照 → 同版证据/索引/状态留档后停止，等待本组
用户确认/commit；不自动提交本轮修复或下一单元。交付为生产修复、本报告/局部ignore、
records索引/逐项镜像/.agent；一次性脚本、合成ELF、日志及binary只保留local/。

验收涵盖无SYMTAB、entsize0/错误、短header/节/表、超界offset/索引/字符串及函数
地址溢出，失败可区分且不先崩溃；正常ELF和原guest执行/FTRACE输出保持。按实际影响
选消费者，不为可选调试解析器机械重跑不调用它的CPU全集/RT/nanos/NPC。

参考（2026-10-18）：[ICS-PA基础设施(2)/FTRACE](https://ysyx.oscc.cc/docs/ics-pa/2.4.html)
介绍ELF符号与函数调用/返回关系；字段及范围依据本机elf.h与ELF gABI，实际使用的
原始规范链接在结果中补录。不是完整ELF验证器或所有配置能力承诺。


## 实施结果及失败语义

**F0021 Completed，结果确认/commit Pending。** HEAD为485548c，index空；Working tree
contains uncommitted CRP repair/documentation changes。本组仅生产monitor.c有差异。

原魔法偏移/char缓冲强转改为本机elf.h的Elf64_Ehdr/Shdr/Sym结构读取。每次读取先以
offset<=file_size、size<=file_size-offset判界，再检查fseek/fread/ferror，避免加法
回绕与残缺值继续使用。校验ELF64/LSB/版本、header/table entry尺寸、普通section
数量和shstr索引；NULL/NOBITS不作为文件内容读取，其他section需完整在文件中。

保持原“选最后一个SHT_SYMTAB”的策略，要求固定Elf64_Sym尺寸、完整表项计数和合法
sh_link；按sh_link取关联STRTAB，避免误选其他字符串表。名称offset及NUL有界检查，
空名称初始化为确定的空串，长名称按既有127字符截断策略保存。保留原GLOBAL/FUNC
过滤，跳过无定义的符号，不扩展LOCAL/WEAK支持。函数value/size和池容量增长均防溢出。

文件/结构/分配/IO失败统一清理本次文件、临时表/字符串；init_elf清空整个函数池，
输出FTRACE拒绝诊断并exit1，未进入guest或使用先前已解析的部分结果。显式-e打不开
原本即Assert终止，本次保留启动失败类，不静默跳过坏文件；不是要求用户新增日常步骤。

## 逐项验证

| 本次验证 | 结果及证据 |
|---|---|
| 原版见证 | 正常ELF控制通过；无SYMTAB、entsize=0在UBSan捕获除零，诱饵STRTAB使原函数名foo错读为WRONG。三反例均不能通过同一判据；local/before-*.log、host-results.json |
| 最终版ASan/UBSan | 32/32场景通过：7个正常控制（标准/诱饵字符串表/40函数扩容/长名称/空名称/无文件内容的NULL及NOBITS），25个拒绝控制覆盖header/版本/class/data/entry尺寸/保留或扩展编号、短表/超界offset、缺SYMTAB/零尺寸或残缺符号、字符串链接/索引/NUL、符号section和函数地址回绕。local/after-*.log |
| 资源与IO错误 | 8/8场景：1正常清理控制、7个open/seek/短read/close/section malloc/string malloc/池realloc失败注入。截获exit时确认status=1、函数池NULL/计数0、所有本次分配和文件余额0，无ASan/UBSan报错。local/fault-results.json、fault-*.log；真实进程退出另由native验证 |
| 真实native | 39/39：32同版ELF场景、真实call/ret小guest、多-e、先好后坏/缺文件/目录错误、未指定-e和FTRACE关闭对照。非法输入诊断exit1且guest未开始；正常guestGOOD TRAP/exit0。local/native-results.json及native-*.log |
| 真实调用返回 | 安装好的RISC-V工具链构建20B原生RV64指令guest，FTRACE显示80000000 call [foo@0x8000000c]、80000010 ret [foo]，80000008 ebreak/GOOD TRAP。多-e同样通过，未使用fake CPU或内存代替实际执行 |
| 判据负例 | 实际正/负日志控制通过；空exit0、缺ret、非零但无parser诊断、拒绝日志追加GOOD TRAP四种变异均拒绝。local/judge-controls.json |
| 最终核对 | local/validation.json的16项源码/编译/结果/配置/REF/NPC/HEAD/index检查全部通过；before源码等于HEAD，最终快照等于已测源码 |

host直接include完整原/新monitor.c，日志/断言钩子隔离，不启动完整系统；faults夹具
包装分配/文件调用并截获exit以核对清理。真实native覆盖实际退出/guest。ASan配置
使用detect_leaks=0（既有执行环境不支持LSan），不声明LSan通过；资源释放由明确
计数检查。最终补核ELF NULL/NOBITS/保留section数量后重跑受影响矩阵及两个构建，
最终结果来自同一组合版本，不混用中间版的29/36结果。

## 构建、命令及证据

默认构建沿用既有入口，不改变.config或Makefile：

```sh
CCACHE_DISABLE=1 make -C nemu -j4 app NEMU_HOME="$PWD/nemu" 'git_commit='
```

FTRACE测试构建额外传CFLAGS_BUILD='-O2 -DCONFIG_FTRACE'，OBJ_DIR/BINARY指向本组
local/obj-ftrace和local/nemu-ftrace。FTRACE在Kconfig中独立可选；本次只有该宏差异，
不是新增构建选项或要求用户运行新流程。两个构建都按原代码命令行清空教学tracer提交宏。

真实命令为 `local/nemu-ftrace -b -e local/call.elf local/call.bin`（实际argv均为
绝对路径，见native-results.json），SDL_VIDEODRIVER=dummy/SDL_AUDIODRIVER=dummy；
local/run-native.py是一次性执行脚本。来宾由riscv64-linux-gnu-gcc -nostdlib -static
-march=rv64im -mabi=lp64链接0x80000000后objcopy为raw bin，精确命令见
local/guest-build-commands.json，未安装或下载新工具。

- local/before/monitor.c、monitor.after.c、repair.patch：原/新生产源码及精确差异。
- local/elf/、elf-cases.json：全部小型输入和预期；保留实际字节，不再生成大镜像/临时ramdisk。
- local/harness-{before,after}.c、host-commands.json、host-final-commands.json：原版/最终host编译与执行argv；gcc -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -no-pie及真实项目头文件。
- local/faults.c、fault-commands/results、native-results、judge-controls、build*.log：注入、实际消费者及判据证据。
- local/identities.json、validation.json、manifest.sha256：最终源/配置/两个native binary与guest身份；本组约1.5MiB，local为一次性测试与证据，不纳入提交。

原始参考（访问2026-10-18）：[ELF gABI section定义/sh_link](https://gabi.xinuos.com/elf/03-sheader.html)、
[字符串表](https://gabi.xinuos.com/elf/04-strtab.html)、[符号表](https://gabi.xinuos.com/elf/05-symtab.html)。
它们定义了section文件范围、SYMTAB关联字符串表及NUL/索引结构；本次仅实现当前已有
ELF64路径需要的读取边界。旧linuxfoundation HTML入口本次访问失败，未据未读正文作结论。

## 影响、限制及停点

本组不修改print_ftrace调用/返回识别或正常指令执行，仅解析器和初始化失败清理。
默认native真实guest、FTRACE启用与关闭路径均覆盖；CPU全集、RT update/msh、nanos
三前台/hello及NPC/REF不消费该可选-e解析器，本轮不重跑，不用小guest冒充其回归。
根.config/generated header、REF与NPC binary未改变；默认native按本次源码重建。

不是完整ELF合法性/链接验证器：只接受现有ELF64 little-endian、普通section编号及
非空SYMTAB/关联STRTAB；ELF32/大端/扩展编号或无符号表输入明确拒绝。未增加LOCAL/
WEAK过滤、动态符号/重定位/PIE地址基址处理，未验证所有无关section的语义。保留
截断名称/选最后SYMTAB等原有策略，未跑所有ISA/宿主字节序/巨型文件压力或完整Linux。
初始函数池malloc仍沿原Assert策略，后续分配/IO的显式清理已按上述范围验证。

全部已修28，未修完91（含5CQ/F0040 Partial）；前27已提交，本组1项待确认/提交。
PAL供给/性能因果、F0043协议、五CQ、F0040并发和两缺源风险保留，无新长期技术裁决。
统一留档后停止；未来只沿TASK_QUEUE，不自动提交新修复/下一单元/push/安装/M2。
ignored证据/.agent沿本地持久化，不从commit推定备份。

<a id="approval-submit-20261018"></a>
## 用户确认与提交授权（2026-10-18）

用户“提交，继续”确认上述已报告范围及限制，授权本批提交并执行唯一下一入口F0022。
提交前226条manifest全部无漂移，复用原16项终检与32/8/39验收，不重复产品测试。
仅提交本批monitor.c、报告/忽略声明、状态镜像/过程索引及前维护提交回执；
本地证据与.agent不随commit备份，不push。实际commit回执见后续状态记录。
