# CRP F0010/F0011 — 声卡初始化触发与欠载填零

## 计划、范围及授权（2026-10-18）

用户“确认WR属性是允许读写还是只允许写，然后提交并进入下一批修改”确认并提交前兼容性单元，root 1603f888371578d987925aa296bb26c801a2d163，初始root/index干净；F0044已提交、F0040仍Partial。复用[总计划](../REPAIR_AND_REGRESSION.md)、[现行规则](../workflow/README.md)及TASK_QUEUE唯一入口。本批只修NEMU现有音频设备，不删除TARGET_AM条件分支、不改AM公开接口、Make/测试入口、旧COUNT寄存器绝对值含义或增加设备。

F0043的异步读改写覆盖消费进度需要协调AM/NEMU提交方式；不能只锁最终赋值。保留旧绝对值客户端/新旧引擎配对的兼容性策略尚待具体选择，本批不擅自把COUNT改成增量，也不把它当F0010/F0011的前置。转向同设备独立已明确错误，原P10已确认现有AM init→CTRL/samples可到回调。

执行：先复制原反例并按源码构造最少定向；F0010仅在完整init写入请求时按配置启动/重启，对原AM的先init后freq/channels/samples保留一次延迟启动兼容，读/不相关写不误触发；失败打印实际SDL错误且不启动播放。F0011仅补齐stream[nread..len)静音，样本/环回/消费计数保持。逐项最小改动、原版与修复后对照，再真实SDL线程/原audio_test及超容量样本/nanos回归，最终组合留档。

验收：配置→init写确实打开；init读/零写/不完整写/普通samples更新不重开；legacy init先行等配置就绪后仍首次打开，显式重init正确close/open，失败不Pause；空/1/len−1/满count及wrap保留有效样本、其余全0且保护哨兵不变。host sanitizer/mock只用于确定边界；真实SDL回调必须有不同线程、完整原PCM并检查欠载静音；nanos原八状态/后台hello保持。CPU/RT/NPC REF不编译该设备无需重复运行；源码、二进制和实际日志绑定。F0043仍未修，不冒称并发安全或真实声音/全配置通过。

正常本组Completed后停止，等待用户确认/提交；当前指令仅授权前批提交，不自动提交下一批、不push/安装/M2。一次性夹具/生成证据仅local保存。

## 逐项完成与兼容性结果（2026-10-18）

F0010/F0011均Completed，结果确认/commit Pending。生产只改nemu/src/device/audio.c，TARGET_AM三处MUXDEF保持原字节；AM实现、测试函数、PCM、Make入口及旧COUNT读写语义均未改。全部已修23（21已提交、本组2项未提交），未修完96，含5CQ及F0040Partial。

| 项目 | 最终实现 | 验收与限制 |
|---|---|---|
| F0010 | 完整32位init写设置一次请求；配置齐全时打开。配置初始为0，兼容原AM先init、后CTRL的顺序，配置就绪消费一次请求；读/零init/不完整init/未请求的samples更新不误重开。显式重init先关闭已开设备再打开；SDL子系统只成功初始化一次，失败打印实际错误、不Pause，可显式重试 | host直接init、legacy、非触发、部分写、重init及两种SDL失败；真实配置→init512B、原AM首次打开一次、重init两次Open/一次Close及新参数通过。仅保留首次旧顺序兼容，不把普通配置写当作无条件重启 |
| F0011 | 欠载尾部用memset(stream+nread,0,len−nread)，有效样本/消费数量/环回逻辑不变 | host空/1/len−1/满/环回/零长与哨兵；真实SDL原版空队列4096B中留4094B非零哨兵，修复4096B全0 |

WR是AM抽象写请求接口，不是RW，不决定底层MMIO寄存器是否可读。native分发表共用handler没有提供读回保证。前批WR依据已随1603f88提交；本批只修设备行为，不改变AM读写方向规则。

## 原版、修复后及真实线程证据

GCC/Clang ASan/UBSan各14例，共28项，原版10/28符合修复契约，最终28/28；原先正常legacy/满缓冲等保持，不用删除原路径换取PASS。SDL_OpenAudio/InitSubSystem失败分别有错误日志、无Pause，显式重试通过。LSan因已知沙箱限制关闭，不宣称泄漏检测。

真实NEMU+SDL dummy五例全部GOOD TRAP/exit0，另有原版缺陷见证：

- 原audio_test及56844B小星星PCM逐字节未改；4.02秒、Open一次、28次真实callback、57344B流中完整PCM连续出现，前后静音全0。
- 原AM API的65537B超容量调用4.83秒完成，Open一次，34次callback/69632B流中完整样本，前后静音全0；未改前批分片实现。
- 先配置再显式init，512B样本0.87秒完成，只有一次成功Open，证明不依赖samples误触发。
- 空队列0.77秒，两次callback/4096B全0；同一guest/观察器运行原版engine，正常guest终止但4094B哨兵仍在，作为预期缺陷见证，不把GOOD TRAP当作旧实现正确。
- 显式重新初始化1.12秒：Open(8000/1/1024)→Close→Open(11025/2/256)，7次callback/8192B静音；观察到新的callback线程。

宿主观察器在实际SDL提供的stream中预填0xa5，随后调用生产callback，只记录返回字节；不替换生产消费逻辑或计数。原版与修复都用相同预填，故能验证回调完整覆盖缓冲区。所有真实callback线程均不同于guest执行线程；这不是对F0043计数并发正确性的证明，也不是人工听音。

nanos真实八状态（pal、nterm及命令、slides0/1/0、pal返回/输入）保持响应，后台hello1396→6490递增，slides回页hash一致；51.74秒后自有组SIGTERM，make=-15，不是guest正常退出。根NEMU build/模型/REF未改，隔离引擎重新构建。

最终26项核对通过，8种判据故障全部拒绝：缺完成/缺trap、BAD TRAP、DIFF ABORT、SIM_END、工具失败、任一未清字节及重复Open。只改native NEMU设备，CPU ISA/RT的NPC/REF不编译该设备，不重复运行CPU/RT；Navy与AM源码未变，不重新打包fsimg。原平台条件及Make命令保留。

## 保留问题与下一入口

F0043仍未修：只给旧绝对count赋值加锁无法消除读/写之间的消费丢失。可审阅候选为保留旧COUNT绝对含义、追加独立增量提交，并约定新旧AM/引擎配对或能力发现；直接将COUNT改成增量会破坏旧MMIO客户端。二者涉及不同兼容性范围，尚未代用户裁决。本批不修改COUNT/map或提交协议，不扩大为独立修复的前置。

F0040并发/异常/析构与五CQ保持原范围。本组完成后等待确认/提交，唯一下一入口由TASK_QUEUE维护；独立候选转向F0012/F0013 monitor输入边界与watchpoint池，未Start。不自动提交本组、不push/安装/M2。

## 恢复与持久化

实际引擎SHA256 `f3102128a11230ad1ea2c46b012e6efdac7d27f7ea69fc43e2412cd2b4df9e45`；原版 `911476b02b5f686ea007dec5dac3a0fc23fa05d1b9d3acd87e7cc7c24f8c2ae5`。最终源码SHA256 `65048c00750517d9e94d8a209b880d55468744d818147ae09e28f333d45eebae`。REF/SoC身份见local/tested-identity.json，未修改。副本沿用/tmp/crp-ioe-t400f090，原批artifacts与manifest不改写。

local保留原/最终设备源、host.local/源与前后28项、真实原函数/数据、5种guest ELF/BIN/反汇编、before/after引擎、观察器/原流/回调线程日志、原版缺陷见证、nanos八状态、verify/validation/checker-faults/repair.patch及manifest。初次host缺宏头、初次guest缺私有ISA include的编译失败保留并补齐测试include；一次offset精确匹配补充后重跑定向28项，最终真实回归使用精确补充后的源码，不改正常入口。测试/生成资产均本地忽略，不随commit备份。

<a id="performance-review-20261018"></a>
## 卡顿反馈后的补充检查计划（2026-10-18，Reopened）

用户报告原入口 `nanos-lite: make ARCH=riscv64-nemu run` 的画面和声音变卡，要求检查所有声卡相关修改，覆盖 miniSDL/NDL，而非只看最后一批。下一组 F0012/F0013 尚未开始，本问题属于本组原入口兼容性及消费者验收，故本组 Reopen；原完成记录和动态证据保留，不将功能响应通过扩写为性能通过。

范围：核对 CRP 修复前 0ee3778 至当前工作树的完整音频调用链、图形/IOE 共享修改和构建身份。在隔离副本中复用相同 NEMU 配置、同一磁盘镜像及原始 nanos/PAL，分离 NEMU 声卡改动与 AM/共享改动；检查成功/失败 Open、Close、频率/通道/samples、实际回调间隔/执行时间/欠载、COUNT 轮询与提交间隔、屏幕更新及后台进度。探针只放隔离副本/宿主观察库，不修改生产入口或把计数协议另行修复。先小规模对照，有明确差异再扩大定位，不无故重跑 CPU/RT。

交付：本节补充实际测量、复现命令与限制，本地新证据放 `local/perf-review-20261018/`，不改写旧 manifest。以同条件 A/B 的方向和量级判断，未复现或无真实音频后端时明确限制。检查完成后总结并停止，不提交、不启动下一组；若确证需修改现行契约或环境安装，按既有规则裁决。

### 补充检查结果（2026-10-18）

用户补充卡顿在 **PAL 启动画面** 已出现。本次定向检查已完成，没有新增生产代码修改；原组保持 Reopened，用户报告的“相比之前新增卡顿”尚未闭合，不能把以下对照解释为用户反馈已解决。没有提交或开始下一组。

核对 `0ee3778` 至工作树：miniSDL 的 audio/timer/event、NDL、SDL_mixer、nanos-lite 音频接口无源码改动；直接音频差异为 AM AUDIO_PLAY 容量分片及 NEMU init/欠载，另检查了 AM IOE 方向/边界、GPU sync 先后和 klib 共享变化。原图形/音频参数未改。根 `.config` 与原隔离配置逐字节一致（O2，无 trace/difftest），根当前 guest 与其自身 ramdisk 配对，PAL ELF 与实际 ramdisk extent 逐字节相同。root guest/engine 和旧修复引擎均记录 SHA，AM 对照在同一路径/编译环境构建，使用同一根 ramdisk，未重打包应用。

宿主观测库只记录 SDL_OpenAudio/CloseAudio、原回调时间和 SDL_UpdateTexture，不预填或改写 stream。额外的 COUNT/PCM 消费、复制和应用回调探针只编译进隔离 NEMU，guest/PAL 指令不改。先做 dummy 对照，再经已批准的沙箱外执行取得 **真实 PulseAudio**，并完成真实窗口对照；不宣称人工听音。11 个真实后端测量均有有效回调/画面/hello且无 BAD/ABORT，各 18 秒，定时发送本次自有进程组 SIGTERM（SDL 捕获后可返回 0，不是 guest 正常退出）。未并行跑性能用例。

| 待检查点 | 实测结果 | 结论/边界 |
|---|---|---|
| 重复初始化、参数变化 | 所有有效例均只 Open 成功一次，Close 零次；11025 Hz、2 通道、1024 samples。当前 NEMU 的 init 请求及三个配置写各一次 | 启动阶段没有反复 close/open，也没有调大回调间隔的参数变化 |
| 宿主回调节奏/耗时 | 同一根 guest，旧/新引擎真实音频平均间隔 92.8166/92.8137 ms；无设备内探针时回调平均 2.98/2.87 μs，最大 19.13/6.97 μs。真实窗口对照平均间隔 92.8144/92.7780 ms | 未见声卡修改造成持续回调变慢；PulseAudio 约 85/107 ms 的分组节奏两版均有，非严格等间隔 |
| 欠载 | 设备探针对照：旧版 172 次消费中 90 次为空，当前 172 次中 87 次为空，均不是仅启动前的短暂空队列；当前录得 85 次 4096 B 提交、平均间隔 173.25 ms，最长 498.70 ms | **PCM 供给明显慢于约 93 ms 的消费节奏，旧版也存在**；新清零会把欠载输出为静音，可能让断续更明显，不能由此断言全部主观差异的原因 |
| AM 写入忙等/分片 | 每次包长均 4096 B，小于 64 KiB。已完成的每个包都只有一次容量等待处 COUNT 读取，另各一次状态/提交读取；复制平均约 1.6 ms、最大 1.80 ms（当前根 guest） | 此场景没有等待循环反复轮询，不触发多片发送；本次不能将卡顿归因于“新增分片让 AM 长时间忙等”。不推广到所有消费者或包长 |
| miniSDL 应用回调/NDL | 85 次 PAL `AUDIO_FillBuffer` 回调往返平均 114.98 ms、p95 130.04 ms，含 guest 调度及观测开销；每次生成 4096 B，即约 92.88 ms 音频。回调起始间隔平均 172.53 ms、最长 472.51 ms；NDL_PlayAudio 平均 1.89 ms、p95 1.66 ms、最大 18.34 ms | 当前测量中主要时间消耗在应用填音及其调用间隙，NDL 写入并非主要等待。应用回调依赖 GetTicks/PollEvent/Delay 轮询，这些源码本轮均未改；不是独立线程持续补音 |
| AM/共享代码回退 | 同引擎/磁盘：当前 AM 两次提交平均间隔 185.70/176.21 ms，修复前 AM+klib 为 172.74 ms，仅回退 AUDIO_PLAY 为 169.70 ms；各例均大量空队列，COUNT 等待处仍每包读取一次 | 无论回退哪组都未消除供给不足；存在几％至约一成的短时变化，样本不足以证明小幅性能退化已排除，不能宣称改动完全无开销 |
| 画面推进 | 真实窗口+真实音频、同根 guest，18 秒旧/新引擎 SDL 纹理提交 116/127 次；后台 hello 2471/2405。两版画面提交长间隔均存在，p95 约 782/799 ms，最大 833/867 ms；纹理上传平均均约 134 μs | 没有复现当前版本一致更慢；提交计数包含部分画面刷新，**不是游戏 FPS**，也未得到全部场景及用户原先流畅基线的因果对照 |

以上支持继续定位 PAL 填音/轮询与图形推进的共同执行预算，**不支持**将当前卡顿直接归因于反复初始化、宿主回调执行过慢或 AM 容量忙等；也没有修复/证明 F0043 的并发计数协议。欠载清零是讲义要求，不能用保留未初始化或旧声音数据来掩盖供给不足。现有证据没有识别出需要立即回退的单一修复；不改频率、samples、应用回调调度或 COUNT 契约来凑通过。

恢复与复现：`local/perf-review-20261018/{measure.py,host-probe.c,device-probe.h,guest-probe.h,build-probed.py,build-guests.py,build-guest-probe.py,analysis.json,validation.json,identities.json,checker-faults.json,manifest.json}`；每个测量目录保存完整 argv/env、engine/guest SHA、host/device/app 原始事件与 guest log。基本命令为 `python3 measure.py <新目录名> <engine> <guest.bin> default 18`；自定义 guest 用 `CRP_PERF_NAVY=<根navy-apps路径>` 指向匹配磁盘，真实窗口另设 `CRP_PERF_VIDEO=default`。未安装软件，真实后端需要能访问本机 PulseAudio。数据核对 11/11，通过缺 Open/零回调/BAD 三种判据负例。

保留的夹具/环境失败：首次将根 guest 配到隔离 ramdisk 导致 ELF 魔数断言，已拒绝并保留，修正为根磁盘后所有对应对照一致；两次沙箱内真实音频尝试被 PulseAudio 本地唤醒权限阻塞，未打开设备、无回调，均排除，沙箱外已正常测得。首个 dummy 收集器按 exit=0 误写退出类别，已明确补正为超时后自有 SIGTERM，保留更正说明，原时间/事件不改。原本组及兼容性组 199+199 项 manifest 全部无漂移，隔离构建后的源码和引擎已恢复；生产源码 SHA 仍为 `65048c00750517d9e94d8a209b880d55468744d818147ae09e28f333d45eebae`。

检查到此停止。原功能修复及历史验收保留，性能反馈未标记已修；下一动作在现有 TASK_QUEUE 维护，先处理本次补查的反馈/后续定位，再解除原组确认提交门槛，不自动进入 F0012/F0013。

### 寄存器读取次数澄清（2026-10-18）

用户追问 handler 修改是否因“整块读取”而大量增加 io_read。准确口径：原 handler 已按 offset 判断，不会因注册为整个 audio 映射的回调就读取整个寄存器组。F0010 修改依据是旧条件 `offset == 8` 实际对应 samples，而 init 位于 `0x10`，不是将整块读取拆成 freq/channels/samples。AM CTRL 的三个 outl 保持原字节，映射层每次访问仍调用一次 handler。

当前 `riscv64-nemu` 为宿主 native NEMU，CONFIG_TARGET_AM 未定义；三个 helper 的实际分支一直是 `audio_base[reg_*]` 宿主内存取值，相关 `io_read(AM_AUDIO_CTRL)` 编译分支未选中。新条件在 init_pending 时增加少量配置字段检查，不产生 guest MMIO 或嵌套 io_read；COUNT 读取在 handler 首个 read 判断直接返回，COUNT 写入在 offset 判断返回。已核对当前实际二进制反汇编，配置检查/取值为直接内存访问，没有 ioe_read 调用。

`io_read(AM_AUDIO_CTRL).freq` 的语法含义是一回 AM 抽象 ioe_read 调用后取结果结构体字段；它不保证或等价于“整块硬件寄存器读取”，底层访问由实现决定。旧 TARGET_AM/WR 候选已按兼容性报告撤回，本次不恢复该候选或改变方向契约。性能原始证据中旧版83包、三个COUNT读取点各83次；当前85包、三个读取点各85次，均每包3次（状态、容量等待检查、提交前读取），未观察到读取数量成倍增加。本次只复核源码/实际反汇编及既有测量，未改生产代码、重跑动态测试或改变Reopened状态。

<a id="closeout-approval-20261018"></a>
## 用户确认、重新闭合及提交（2026-10-18）

用户最新“我了解了，闭合并提交你做过的相关修改”确认已报告的修复、补查和限制，授权闭合本组并提交归属明确的修改。本条承接原功能Completion及性能反馈Reopen，原记录保持；本组现重新Completed，结果已获用户确认，本次提交包含F0010/F0011生产修复、报告/忽略规则、状态/索引、前批提交回执及用户指定讲义参考。实际提交身份以包含本节的Git提交为准，本地 `local/closeout-20261018/` 保存提交回执；不把尚未执行的Git操作写成历史完成。

重新验收复用已报告结果：host 28/28、真实SDL原audio_test/超容量/初始化/重初始化/静音和原版欠载见证、nanos八状态/26核对/8负例；补查11有效真实PulseAudio测量、真实窗口旧/新对照、AM回退/复测、PAL回调及3判据负例。提交前核对生产源码与已验收SHA完全相同，本组199项、前兼容性组199项、补查113项manifest全部无漂移，空白与提交范围检查；没有新的生产改动，不无故重跑动态测试。

**闭合范围**：F0010/F0011的既有修复及本次定向检查结束，不再把性能Reopen作为本组提交阻塞。PAL音频供给不足、未证明用户原先流畅基线的新增退化原因、小幅性能变化及F0043竞争仍作为已披露风险保留，不能记成性能问题已修或并发正确性通过；没有回退欠载清零，也未改应用回调/参数/COUNT契约。后续如专项优化，须另行明确目标和验收。

一次性探针、夹具、日志/JSON、镜像等仅本地保留，不随本次提交入库；只提交必要生产修复和可审阅记录，`.agent`及ignored资料沿用现有持久化约定，commit不等于其已备份。全部已有功能修复23，未修完96含5CQ及F0040Partial；未来独立F0012/F0013恢复为Next，未Start。本轮按用户指令提交后停止，不自动开始下一组，不push或安装。
