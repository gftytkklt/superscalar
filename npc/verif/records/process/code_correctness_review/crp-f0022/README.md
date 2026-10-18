# CRP F0022 — TARGET_AM嵌入镜像装载边界

## 范围、验收与停点

用户2026-10-18“提交，继续”确认F0021并授权提交后执行唯一下一入口。
F0021实际提交2a96eb3；开始前working tree/index干净，M2保持。
复用REPAIR_AND_REGRESSION与workflow，单项复杂边界作为一个工作单元。

仅修改monitor.c的CONFIG_TARGET_AM load_img：复制前校验bin符号顺序、
长度表示范围、RESET偏移/物理地址表示及PMEM剩余容量；保留Make/mainargs接口、
空嵌入镜像的内置程序回退。am-bin.S不定义BIN_PATH时两符号相等，
init_isa先写内置程序，故空镜像原本就是可用路径，无需新增策略裁决。
非法输入明确终止，不能部分复制。无安装/系统改动，无AM声卡能力扩展。

验收：容量-1/等于/+1，reset起点/最后字节/越界/回绕，符号逆序/巨大长度/空镜像；
拒绝前不形成目标指针、不复制，PMEM和哨兵保持。保留原版失败见证；
最终host ASan/UBSan定向测试，以及实际NEMU-on-AM小guest/内置程序启动。
按影响核对native构建及配置/REF/NPC保持；不机械重跑未受影响消费者。

结果写入本目录、process索引与repair-status及.agent，完成后停止，
等待用户确认及提交新修复，不自动push/下一单元/M2。local测试资产本地忽略。

参考：[ICS-PA 2.5 在NEMU上运行NEMU](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)，
2026-10-18读取，明确TARGET_AM为内层NEMU，通过mainargs嵌入guest。

## 实施结果

**F0022 Completed，结果确认/commit Pending。** F0021已确认提交
`2a96eb3a7be152463efe6d84bb06474f2af3cd1f`；本轮新修复未提交、未push。

monitor.c使用uintptr_t比较链接符号地址，避免对两个独立声明对象作指针相减；
先校验符号顺序，再作无符号差，要求长度能由size_t/long表示。RESET偏移必须位于
PMEM内，且base+offset能由paddr_t表示；随后用size<=MSIZE-offset检查剩余容量，
避免先相加造成回绕。全部检查先于guest_to_host和嵌入镜像memcpy；失败沿已有
Assert/AM halt(1)终止。正常Log显式转long，返回类型和Make/mainargs接口保持。
空镜像仍复制0字节、保留init_isa写入的内置程序，没有强制要求bin非空。

实际AM构建暴露前置问题：TARGET_AM的Kconfig只能选择PMEM_MALLOC，而paddr.c的
静态表用动态pmem指针初始化，在C下报initializer element is not constant。
本组最小修正一处表达式：malloc模式初值NULL，继续由既有init_mem填入分配地址；
静态数组模式仍用pmem常量地址，保留REF不调用init_mem的既有用法。不扩展内存接口。
原编译失败日志为local/build-native-am.log，修正后原配置构建及真实执行通过。

## 验证与证据

| 检查 | 本次结果 |
|---|---|
| 原版有区分力见证 | 容量64的正常控制通过；容量64复制65和offset16剩余48复制49均未拒绝。原版translate/copy均为1，第一例尾哨兵由a5变37；同一判据失败。local/host-before-*.log |
| 修复host ASan/UBSan | 28/28：起点/中段/最后字节的空、容量减一/恰好/加一；reset恰尾/域外/负数/大跨度；符号逆序/超长；paddr32上界/加法溢出与64位物理基址。正常核对完整PMEM及两侧哨兵；拒绝核对translate/copy均为0且全部字节不变。local/host-results.json |
| 真实AM-native | 6/6：32MiB PMEM嵌入20B RV64 call/ret guest和未定义BIN_PATH的空镜像均GOOD TRAP/exit0；32KiB PMEM嵌入32769B拒绝/exit1；offset16下32751/32752B正常执行至0x80000018，32753B拒绝。错误均无Welcome/guest执行。local/am-results.json、am-extra-results.json |
| 真实RISC-V NEMU-on-AM | 内层TARGET_AM、RV64、32MiB PMEM，通过现有ARCH=riscv64-nemu构建53,364B镜像；实际外层native NEMU执行内层，再由内层执行20B guest，两次Welcome和两次GOOD TRAP、外层exit0，5,853,415条外层指令。local/nested-default.run.log |
| 默认native | 按原app入口重编译并链接，内置guest GOOD TRAP/exit0。local/build-default-native.log、default-native.run.log |
| 判据控制 | 真实正常/拒绝/两层启动日志通过；空exit0、正常日志非零退出、拒绝无诊断、拒绝混入GOOD TRAP、缺内层成功五个负例均拒绝。local/judge-controls.json |
| 身份和终检 | before源码等于前HEAD；最终两个源码快照等于已测版本，隔离AM源码一致；根.config/generated header、REF、NPC未变，默认native按本轮源码重建。local/identities.json、validation.json、manifest.sha256 |

host include完整生产monitor.c及真实项目头文件，只有链接符号改成可注入地址的表达式、
Assert拦截、Log/内存翻译/copy观察钩子；不替代实际AM集成。编译命令逐条保存在
local/host-commands.json，使用gcc -O1 -g -fsanitize=address,undefined
-fno-omit-frame-pointer -no-pie；ASAN_OPTIONS=detect_leaks=0，UBSAN_OPTIONS=halt_on_error=1。
LSan沿既有环境限制禁用，不声明泄漏检查通过。本组不新增动态分配。

实际AM通过local/nemu与local/am隔离源码树构建，不更改根配置或AM库。
选项由现有Kconfig生成，CONFIG_ISA_riscv=y、CONFIG_RV64=y、CONFIG_TARGET_AM=y、
CONFIG_DEVICE=y、TRACE关闭、32MiB PMEM；小容量/offset测试另存配置。
原riscv64-am_defconfig使用旧ISA_riscv64选项，本组未修改该独立配置文件，
隔离配置按现行Kconfig明确RV64，不将旧命名的默认结果冒称RV64验收。

主要命令（绝对路径/环境/全部argv见local/am-commands.json和am-extra-commands.json）：

```sh
make -C <isolated-nemu> f0022_defconfig ARCH=native 'git_commit='
make -C <isolated-nemu> -j4 image ARCH=native mainargs=<call.bin> 'git_commit='
make -C <isolated-nemu> -j4 image ARCH=riscv64-nemu mainargs=<call.bin> 'git_commit='
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy nemu/build/riscv64-nemu-interpreter -b <inner.bin>
CCACHE_DISABLE=1 make -C nemu -j4 app NEMU_HOME="$PWD/nemu" 'git_commit='
```

RISC-V测试仅把无关FLASH存储缩为4KiB以控制产物大小，PMEM保持32MiB，架构编译参数
使用现有Make默认rv64g/默认ABI。早期临时rv64im/lp64尝试遇到系统缺gnu/stubs-lp64.h，
未安装或伪造系统头；改用已支持的默认参数实际成功，失败日志原样保留，不计PASS。
测试脚本/构建树/小镜像/日志在local本地保留，总约6MiB，不提交一次性代码和build。
local/before、monitor.c.after、paddr.c.after、repair.patch保留原/新源码与精确差异。

## 影响、限制及停点

28个边界场景针对load_img本身；不声称任意错误的全局内存配置都能安全启动。
am_init_monitor仍先调用init_isa，其内置镜像复制依赖既有合法reset/内存容量前置；
例如只剩1字节的reset测试没有启动完整ISA初始化。本组修复嵌入镜像复制越界，
没有重构所有ISA内置镜像装载或整个配置校验，生产正常配置已真实验证。

错误终止沿项目Assert契约，未验证NDEBUG禁用断言配置；未跑全部ISA/32位AM宿主。
实际AM-native和RISC-V路径均覆盖；CPU全集/RT/nanos与NPC不执行TARGET_AM装载，
静态PMEM表达式保持，不重跑其完整产品回归。REF/NPC产物未替换，AM声卡及VME能力未扩展。

全部已修29，未修完90（含5CQ/F0040 Partial）；前28已确认提交，本组待确认/提交。
PAL供给/性能因果、F0043协议、五CQ、F0040并发和两缺源限制保持。
本组结果/索引/.agent统一留档后停止；未来仅沿TASK_QUEUE唯一入口，不自动提交/push/M2。
本地ignored证据和.agent不从commit推定备份。

<a id="approval-submit-20261018"></a>
## 用户确认与提交授权（2026-10-18）

用户“提交，检查所有crp任务的存档目录”确认上述结果/限制，授权提交本批，
并要求逐目录检查独立构建存档。本次复核687条manifest无漂移，复用原18项终检、
28个sanitizer场景及真实AM/native验收，不重复运行产品测试。仅提交两个生产C、
本批报告/忽略声明、过程索引及状态镜像；不提交local资产，不push、不Start F0023。

## 2026-10-19 F0005清单补验闭合

本报告F0022中随AM构建修复的malloc静态表初始化，实际提交bc7a110，正是原CCR-F0005根因。此前逐项修复清单未镜像该项；[宿主内存组](../crp-f0004-f0005-f0008/README.md)现补验旧编译失败、当前static/malloc/AM构建与真实执行及分配失败拒绝后闭合F0005。本次不重复修改该表达式、不改写本报告原完成时计数/验收；补验结果确认待本组review。
