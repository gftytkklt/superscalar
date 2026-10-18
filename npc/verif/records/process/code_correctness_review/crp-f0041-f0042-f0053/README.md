# CRP — F0041/F0042/F0053：IOE 同步、能力查询与 devscan

## 计划、范围和授权

用户2026-10-18授权当前CRP连续验证/留档/提交及开启新组；复用[总计划](../REPAIR_AND_REGRESSION.md)、[连续规则](../workflow/README.md#continuous-authorization-20261018)、[逐项状态](../repair-status/README.md)及TASK_QUEUE唯一入口。前批F0039已确认提交b2229ef，授权/状态维护dd015ef，初始root/index干净。M2及其他主线不变。

本组只改NEMU gpu.c的FBDRAW sync先后（F0041），NPC ioe.c无设备CONFIG/现有UART TX映射（F0042），am-tests devscan能力/磁盘几何检查与无加速时现有FBDRAW路径（F0053）；不新增设备、GPU加速、Make接口或RTC契约。按原反例→各项最小改动→host定向→真实RV64/消费者组合验证→留档/提交推进，未决只阻塞其依赖，组末不另等确认。

验收：F0041同步观察时所有像素已写，false不提交且0×0 NULL sync-only保留；F0042audio/disk/net CONFIG完整确定false，UART_TX调用现有putch，已支持RX不退化；F0053无显示/无加速/无盘/零或不适合512字节采样的块几何显式跳过且不访问不支持寄存器，有能力保持原路径。复用P5/MMIO反例、前批可靠NEMU/NPC/RT/nanos观察器；shared AM按影响做真实guest与消费者回归，不以host替代。

正常完成核验最终源码/日志/状态、逐项留证后按连续授权提交；一次性夹具/生成证据local保存不入库。结束连续执行时统一冻结人工启动guard，不push、不安装、不裁决新能力。

## 结果与逐项验收（2026-10-18）

三项修复 Completed；依据本轮连续授权由代理完成验收后提交，未声称用户已逐项review。F0053独立仓库实际提交 `6dc302a117ae282c7f3f50a593b46134f77b2b86`；根仓库提交回执由后续状态记录补齐。累计已修19、剩余100（仍含5CQ及F0040延期）。

- F0041：仅将非空FBDRAW的sync移到全部像素写完后；零宽/高sync-only仍提交。host观察sync时4个像素全部可见，false不提交；真实NEMU devscan framebuffer及nanos图形消费通过。
- F0042：NPC缺少的audio/disk/net CONFIG完整初始化为不具备设备，UART_TX映射现有putch；不增加设备。host查询/回调通过；独立真实NPC程序确认CONFIG、TX及无输入RX=0xff，difftest ON、数值前缀NPC GOOD TRAP，4.02秒exit0。
- F0053：devscan按present/尺寸/has_accel执行，未加速时绘制最多64×64 framebuffer；无盘或无法安全采样512字节时明确SKIP。host六种能力组合保留有加速/合法盘路径；真实NEMU完成framebuffer和盘采样，真实NPC完成framebuffer并SKIP无盘，difftest ON/GOOD TRAP、模拟器exit0（222.72秒）。完整无限devscan循环未运行，实际调用其video_test/storage_test原函数。

原版host八项仅1项符合新契约（已有合法加速/磁盘路径）；修复GCC ASan/UBSan 8/8。LSan因既知沙箱限制关闭，不扩写为泄漏检测。最终17项源码/结果/回归/范围核对通过；六种判据故障（缺标志、BAD TRAP、DIFF ABORT、SIM_END、无difftest、非零退出）全部拒绝。

## 真实消费者回归与限制

隔离副本 `/tmp/crp-ioe-t400f090` 使用本组最终AM源码；根build产物未修改。RT真实update exit0，NPC difftest ON，约161.07秒到msh后自有进程组SIGTERM（make=-15）；本次未运行四应用，不是guest正常退出。nanos image exit0，NEMU真实SDL观察八状态（pal、nterm及命令、slides 0/1/0、pal返回/输入）通过：前台帧按操作变化、回页hash一致，后台hello逐步递增1353→5915、最终5916；51.76秒后自有组SIGTERM。Navy源码未变，复用前批完整fsimg/ramdisk，来源与SHA见local/reused-navy-assets.json，未声称本次重跑navy update。

本组不涉及CPU指令/算术库，CPU-tests不重跑；真实设备guest、受影响RT/nanos均覆盖。SDL dummy及观察库用于收集真实前台，不改guest/NEMU逻辑。不声称真实窗口、音频、RTC、完整GPU加速或磁盘异常恢复验收。

测试夹具问题单独保留：初次复用fsimg的旧symlink合并失败、nanos缺ramdisk消费链接，均只修复隔离副本后重新构建；第一次NPC devscan测试包装器误用 `__PLATFORM_NPC__`，使F0042分支未编入，组合checker记录false，但F0053模拟器exit0/实际标志及GOOD TRAP通过。原raw/JSON保留，local/npc-devscan-supplemental.json分项补判，再以独立caps程序真正验证F0042。caps首编漏klib-macros.h，保留失败日志，补齐测试头后构建/运行通过。未以夹具失败修改生产接口或掩盖失败。

## 恢复与证据

本地 `local/`（不入库）包含host.local、run.local、npc-guest.local、npc-f0042.local、rt/nanos runner、verify.local；host-before/after、各build/run日志与JSON、checker-faults/validation、patch、artifacts及manifest。`guest-f0053-tested.c`是实际跑过的原包装器，`caps.c`为实际独立能力测试；当前guest.c的宏修正不冒充已运行的组合测试。

使用模型SHA256 `1ced513005f8e30df4d1b9b7ebcd7f2be9290dcae32304ef3f4cf971a582f208`，NEMU解释器 `455a618de1da2d0c8b69562750640dbc977668b3acfab03f8000eb111929eb35`，REF `ea44e661db1b9ef12612ef6d07449bc9c5efa920c8267149801d45f4a134ee62`。artifacts绑定三份最终源码和实际ELF/BIN。manifest在收尾生成，ignored资料不随commit备份；am-kernels既有五类untracked资产保持原状。无安装/push/业务M2推进。

<a id="submit-20261018"></a>
## 实际提交回执（2026-10-18）

按本轮连续预授权提交：root e83df62d7b7b3d0b37e42ab2cdbecce27bc0e278（6文件62增9删）；am-kernels 6dc302a117ae282c7f3f50a593b46134f77b2b86（单一devscan.c21增）。提交后root/index干净，nested既有untracked保留；复用本组已完成验收，未无故重跑，未push。整体收尾冻结的[人工guard](../repair-status/README.md#manual-start-guard)须下一次Start前明确决定或豁免。
