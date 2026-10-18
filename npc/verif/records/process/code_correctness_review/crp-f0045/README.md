# CRP F0045 — 双平台IOE编号及读写方向

## 计划、范围与验收

用户2026-10-18连续验证/留档/提交及开启新组预授权内执行；前组F0041/F0042/F0053已Completed且提交root e83df62d7b7b3d0b37e42ab2cdbecce27bc0e278、am-kernels 6dc302a。复用[总计划](../REPAIR_AND_REGRESSION.md)、[连续规则](../workflow/README.md#continuous-authorization-20261018)、[逐项状态](../repair-status/README.md)及TASK_QUEUE唯一入口。初始root/index干净；M2不变。

只修改NEMU/NPC的ioe_read/write分发：先校验int下标有效范围及amdev.h声明的RD/WR方向，再调用已有handler；非法参数沿用现有fail/panic，不新增返回协议或设备。公开amdev.h不改。表内未知编号保持原fail，调用前须先ioe_init，缓冲区合法性不在本项范围。

按原版host见证→最小修复→host全RD/WR/边界及合法路由→双平台真实非法输入/合法控制→共享IOE受影响RT/nanos→源码/日志/判据/范围核对推进。验收覆盖-1、0、128、INT_MIN/MAX、表内未知、全部1..24方向和合法handler保持；真实负例须出现指定panic及BAD TRAP code1，不能把DIFF ABORT/段错误/超时或意外返回视为通过。正常真实控制GOOD TRAP，NPC difftest ON。测试/原始证据仅local保存；完成后按连续授权留档提交，非依赖未决最后汇总人工启动guard。

## 完成结果（2026-10-18）

F0045 Completed，按用户连续提交预授权交付；代理验收不记作用户逐项review。仅两平台ioe.c增加与amdev.h一致的9个WR方向元数据，并在查表前短路校验编号/方向。范围或方向错误沿用已有fail/panic，表内未知仍fail；正常注册handler及其设备语义不变。累计已修20、剩余99，含5CQ及F0040用户延期。

- 原版host124项中60项符合预期：48个合法路由及12个已有未知槽panic；其余64项为错方向仍调用handler或下标UB。修复GCC ASan/UBSan 124/124（48合法路由、76非法拒绝），包括每个平台1..24的双方向及INT_MIN/-1/0/25/127/128/INT_MAX。受控handler只验证分发，不表示24种设备均实现。LSan沿既知沙箱限制关闭。
- 真实NEMU/NPC各6例：正常GPU_CONFIG/UPTIME/NET_CONFIG、sync-only及NPC UART_TX控制GOOD TRAP；-1读、128写、读FBDRAW、写TIMER_CONFIG、表内25读均出现指定AM Panic及BAD TRAP，无意外返回。NEMU负例进程exit1；NPC模拟器负例exit0但明确数值前缀BAD TRAP和ret code=0x1h、difftest ON，不能以进程exit0冒充正常通过。panic源码halt(1)与意外返回halt(2)分开。
- 真实RT update exit0，最终NPC/difftest ON约150.07秒到msh；nanos image exit0、实际八前台状态/操作响应及后台hello1382→6358严格递增，slides回页hash一致，51.74秒观察通过。两者自有组SIGTERM（make=-15），不是guest正常退出；四AM应用实际运行未测。CPU指令/算术库未影响，不重跑CPU全集；Navy源码未变，复用前组已验证完整资产，不冒称重新update。
- 最终20项核对通过：两份源码与隔离副本逐字节一致、WR元数据与公开声明一致、真实结果/产物身份/源码范围/空白符合；NEMU 6种及NPC 8种checker负例全部拒绝。前组109份本地证据无漂移，nested无tracked差异且历史untracked保留。

测试夹具修正保留：第一次guest用了klib未声明的puts，编译明确失败；测试改用公开printf后12个镜像全部构建成功。第一次“移除difftest”故障注入因ANSI颜色未替换目标字符串，原故障结果false保留；先剥ANSI再生成故障，8/8拒绝，未改变接受谓词或重跑guest，原始真实6例均已通过。local/checker-supplement.local仅补判据测试。

## 兼容性边界与后续入口

定向消费者搜索仅发现nemu/src/device/audio.c三处在 `CONFIG_TARGET_AM` 分支 `io_read(AM_AUDIO_CTRL)`；CTRL公开为WR，这些旧调用在严格校验后会panic。当前被测NEMU为 `CONFIG_TARGET_NATIVE_ELF`、未启用该分支，本组未验证或修复NEMU-on-AM。它随下一组音频必要分析处理，并列入下次启动的范围guard；不能把这项写成音频/所有平台已验收。其他尚未决定的F0040/五CQ保持未修，不扩大为当前组阻塞。

## 恢复资料

`local/`保留baseline、两份before源、host.local/前后124项及原UB日志、guest.c、prepare.local、12份实际ELF/BIN/反汇编、guests.local/原始日志/6例结果、故障注入初始及补充结果、RT/nanos runner/日志/帧、direction-consumers、prior-evidence-preservation、verify.local/validation、repair.patch、tested-identity、manifest。源码/模型身份与前组一致，测试副本继续使用 `/tmp/crp-ioe-t400f090`；前组实际绑定产物及源码保留在其独立artifacts，未覆写旧证据。

模型/解释器/REF的完整SHA见local/tested-identity.json及[前组报告](../crp-f0041-f0042-f0053/README.md)。正常API只验证在ioe_init后且缓冲区满足契约的调用；没有增加NULL缓冲检查、并发初始化或新设备。无安装/push/M2推进；本地ignored证据与.agent不随commit备份。根实际提交回执由后续状态记录补齐；本轮收尾冻结[人工启动guard](../repair-status/README.md#manual-start-guard)后停止。

<a id="submit-20261018"></a>
## 实际提交回执（2026-10-18）

按本轮连续预授权提交：root f4e3c0cf840c0edeff5a3fbef1f3d75ce8283745（6文件84增9删）。提交后root/index干净，nested既有untracked保留；复用本组已完成验收，未无故重跑，未push。整体收尾冻结的[人工guard](../repair-status/README.md#manual-start-guard)须下一次Start前明确决定或豁免。

## 配置可达性勘误（2026-10-18，用户追问后）

前文把CONFIG_TARGET_AM音频三处读WR称作严格检查后会panic的兼容性边界，遗漏Kconfig/filelist门槛：HAS_AUDIO只在!TARGET_AM可选，audio.c仅按HAS_AUDIO编译。TARGET_AM是把NEMU本身作为AM应用运行，不能与运行AM guest混淆。因此原先描述不构成当前受支持配置的可达回归，也不应要求人工确认“是否纳入NEMU-on-AM音频”才能继续。原历史检查/日志不改写；[本轮完整核对](../crp-compatibility-20261018/README.md)记录归因、更正及撤回删除MUXDEF候选，最终NEMU设备音频源码保持原字节。

WR复核补充（2026-10-18）：WR是AM写请求接口，不是RW；native共用handler/丢弃perm不产生读回契约。底层MMIO读写权限另按设备定义。[官方声卡说明](https://nju-projectn.github.io/ics-pa-gitbook/ics2024/2.5.html#声卡)与[本轮回执](../crp-compatibility-20261018/README.md#wr-submit-20261018)保留依据。
