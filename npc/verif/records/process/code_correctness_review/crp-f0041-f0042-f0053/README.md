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


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0041/F0042 — 根仓库

F0053 的消费者修复属于 am-kernels，见同报告下一块。

- 差异路径相对于仓库 `.`；旧版本：`dd015ef94a4bf81f7af93496567e2112ce600b17`；新版本：`e83df62d7b7b3d0b37e42ab2cdbecce27bc0e278`。

#### `abstract-machine/am/src/platform/nemu/ioe/gpu.c`

F0041：把 `outl(SYNC_ADDR, 1)` 移到像素复制完成之后，避免刷新时读取旧帧；宽或高为零的分支仍按 sync 单独写刷新寄存器，保持只刷新不绘制的调用。

```diff
diff --git a/abstract-machine/am/src/platform/nemu/ioe/gpu.c b/abstract-machine/am/src/platform/nemu/ioe/gpu.c
index 17ae911b52ebfbdf9646da5c9e058d5cc94f9bdf..b7ea97d3e42c0d885696a211d5b6b05bf5d9461c 100755
--- a/abstract-machine/am/src/platform/nemu/ioe/gpu.c
+++ b/abstract-machine/am/src/platform/nemu/ioe/gpu.c
@@ -24,14 +24,14 @@ void __am_gpu_config(AM_GPU_CONFIG_T *cfg) {
 }
 
 void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *ctl) {
-  if (ctl->sync) {
-    outl(SYNC_ADDR, 1);
-  }
   int x = ctl->x;
   int y = ctl->y;
   int blk_w = ctl->w;
   int blk_h = ctl->h;
-  if(blk_w == 0 || blk_h == 0) {return;}
+  if(blk_w == 0 || blk_h == 0) {
+    if (ctl->sync) outl(SYNC_ADDR, 1);
+    return;
+  }
   // printf("%d, %d: %d*%d\n", x, y, blk_w, blk_h);
   int *pixels = (int *)ctl->pixels;
   int base = w*y+x;
@@ -49,6 +49,7 @@ void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *ctl) {
     }
     // base += w*4;
   }
+  if (ctl->sync) outl(SYNC_ADDR, 1);
 }
 
 void __am_gpu_status(AM_GPU_STATUS_T *status) {
```

#### `abstract-machine/am/src/riscv/npc/ioe.c`

F0042：补 UART_TX 到 putch 的处理函数及分发表槽；对音频/磁盘/网络配置查询返回初始化的 present=false（并清音频容量/磁盘字段），使客户端可探测缺失设备。没有给不存在设备补数据通路，其他未支持访问仍失败。

```diff
diff --git a/abstract-machine/am/src/riscv/npc/ioe.c b/abstract-machine/am/src/riscv/npc/ioe.c
index b954045da20e7d0622a7c022ec637d0adbbfcfa4..c07ef194692b4a1e79938808fb0b02ae944b764b 100755
--- a/abstract-machine/am/src/riscv/npc/ioe.c
+++ b/abstract-machine/am/src/riscv/npc/ioe.c
@@ -18,6 +18,16 @@ void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *);
 static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = true; }
 static void __am_input_config(AM_INPUT_CONFIG_T *cfg) { cfg->present = true; }
 static void __am_uart_config(AM_UART_CONFIG_T *cfg) { cfg->present = true; }
+static void __am_uart_tx(AM_UART_TX_T *tx) { putch(tx->data); }
+static void __am_audio_config(AM_AUDIO_CONFIG_T *cfg) {
+  *cfg = (AM_AUDIO_CONFIG_T) { .present = false, .bufsize = 0 };
+}
+static void __am_disk_config(AM_DISK_CONFIG_T *cfg) {
+  *cfg = (AM_DISK_CONFIG_T) { .present = false, .blksz = 0, .blkcnt = 0 };
+}
+static void __am_net_config(AM_NET_CONFIG_T *cfg) {
+  *cfg = (AM_NET_CONFIG_T) { .present = false };
+}
 
 // AM_UART_RX：读 UART RBR，无数据返回 0xff（AM 规范）。
 static void __am_uart_rx(AM_UART_RX_T *rx) {
@@ -36,10 +46,14 @@ static void *lut[128] = {
   [AM_INPUT_CONFIG] = __am_input_config,
   [AM_INPUT_KEYBRD] = __am_input_keybrd,
   [AM_UART_CONFIG ] = __am_uart_config,
+  [AM_UART_TX     ] = __am_uart_tx,
   [AM_UART_RX     ] = __am_uart_rx,
   [AM_GPU_CONFIG  ] = __am_gpu_config,
   [AM_GPU_STATUS  ] = __am_gpu_status,
   [AM_GPU_FBDRAW  ] = __am_gpu_fbdraw,
+  [AM_AUDIO_CONFIG] = __am_audio_config,
+  [AM_DISK_CONFIG ] = __am_disk_config,
+  [AM_NET_CONFIG  ] = __am_net_config,
 };
 
 static void fail(void *buf) { panic("access nonexist register"); }
@@ -52,4 +66,4 @@ bool ioe_init() {
 }
 
 void ioe_read (int reg, void *buf) { ((handler_t)lut[reg])(buf); }
-void ioe_write(int reg, void *buf) { ((handler_t)lut[reg])(buf); }
\ No newline at end of file
+void ioe_write(int reg, void *buf) { ((handler_t)lut[reg])(buf); }
```


### F0053 — am-kernels

本差异在独立 am-kernels 仓库，根提交 e83df62 不包含这份源码。

- 差异路径相对于仓库 `am-kernels`；旧版本：`c1ba0bb884eaefc75925401759c9fbdfa6f86124`；新版本：`6dc302a117ae282c7f3f50a593b46134f77b2b86`。

#### `tests/am-tests/src/tests/devscan.c`

F0053：video_test 先检 present/正尺寸，无设备明确 SKIP；无加速能力时只绘制不大于 64×64 的 framebuffer 色块并返回，不调用 GPU 加速接口。storage_test 先检 present，再验证 blksz 为正、不大于 512、整除 512 且总块数足够，才请求完整样本。避免缺设备 panic、除零及读取未填充样本；SKIP 不算硬件加速或磁盘功能通过。

```diff
diff --git a/tests/am-tests/src/tests/devscan.c b/tests/am-tests/src/tests/devscan.c
index d2c1a54a6f859bdc63ffaa10971176e1af672eb3..5997e05538045a5f80f39dc92ff4feb27ac3a509 100644
--- a/tests/am-tests/src/tests/devscan.c
+++ b/tests/am-tests/src/tests/devscan.c
@@ -24,8 +24,20 @@ static inline gpuptr_t to_guest(void *ptr) { return ptr ? (uint8_t *)ptr - vmem
 
 static void video_test() {
   AM_GPU_CONFIG_T info = io_read(AM_GPU_CONFIG);
+  if (!info.present || info.width <= 0 || info.height <= 0) {
+    printf("SKIP video: no usable display.\n");
+    return;
+  }
   int w = info.width, h = info.height;
   printf("Screen size: %d x %d\n", w, h);
+  if (!info.has_accel) {
+    printf("SKIP GPU acceleration: testing framebuffer instead.\n");
+    int bw = w < 64 ? w : 64, bh = h < 64 ? h : 64;
+    uint32_t *pixels = (void *)vmem;
+    for (int i = 0; i < bw * bh; i++) pixels[i] = 0x00ff8000;
+    io_write(AM_GPU_FBDRAW, 0, 0, pixels, bw, bh, true);
+    return;
+  }
 
   struct gpu_canvas *cv = (void *)vmem;
 
@@ -50,6 +62,15 @@ static void storage_test() {
   #define nbytes 512
   static char buf[nbytes];
   AM_DISK_CONFIG_T info = io_read(AM_DISK_CONFIG);
+  if (!info.present) {
+    printf("SKIP storage: no disk.\n");
+    return;
+  }
+  if (info.blksz <= 0 || info.blksz > nbytes || nbytes % info.blksz != 0 ||
+      info.blkcnt < nbytes / info.blksz) {
+    printf("SKIP storage: cannot read a full 512-byte sample.\n");
+    return;
+  }
   printf("Storage: %d blocks of %d size. Show first 512 bytes\n", info.blkcnt, info.blksz);
   io_write(AM_DISK_BLKIO, false, buf, 0, nbytes / info.blksz);
   for (uint32_t i = 0; i < nbytes; i += 2) {
```
