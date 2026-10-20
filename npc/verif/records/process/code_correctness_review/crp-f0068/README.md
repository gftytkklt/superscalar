# CRP CCR-F0068 — framebuffer 写入容量边界

## 本轮计划（2026-10-20）

用户“继续CRP修复”授权唯一入口F0068一个单元；前组已确认提交07bba74，
开始时root/index干净，无状态冲突。M2不变，不延续旧连续提交授权。

目标/范围：只改nanos device.c的fb_write及fs.c的FB容量初始化。特殊文件不经过
普通文件remain限制，须在callback保护实际AM FBDRAW。先验证正尺寸与容量可表示，
offset>=容量返回0，len按容量-offset截短，再沿用offset/4、len/4整像素和逐行sync。
现有非对齐offset向下取像素、非整像素尾部不写；不引入字节级读改写、缓存或新像素协议。
初始化容量在size_t域计算并限制到现有signed long文件偏移可表示范围；无效尺寸容量0。

执行顺序/交付：
1. 原实现EOF/跨末端反例；实际device/fs host定向，零长、末像素、EOF/越界、超长/
   SIZE_MAX、非对齐、跨行、非法尺寸/大乘积，核返回值、offset、AM坐标/调用/像素及输入哨兵。
2. 最小源码修改与上述回归；隔离RV64用户ecall真实写FB的旧/新对照与正常跨行/超长/
   EOF路径；默认三前台图像、终端/翻页/返回PAL及后台hello，保留源码/输入/配置身份。
3. 记录结果/限制与补丁，目视后清理本组可再生镜像/截图/构建副本，更新process索引、
   逐项台账、既有计划及.agent状态/唯一入口，整组完成后停止，等待确认/commit。

验收：原反例明确失败、新实现返回实际完整像素字节且所有AM调用在屏内；正常绘图
及逐行sync保持；受影响真实消费端通过。host/fake不冒充真实guest，未测范围单列。
不安装、不改Make/日常流程、不commit/push或启动下一组。遇到真实契约/策略冲突停下裁决。

参考：[Navy设备契约](../../../../../../navy-apps/README.md)把FB定义为W*H*4行优先32位
颜色数组；[ICS-PA图形应用](https://ysyx.oscc.cc/docs/ics-pa/3.5.html)（2026-10-20读取）
提供NDL/SDL/NSlider消费背景。非对齐兼容及截短以本地既有函数/本组边界为准，
不从讲义推定完整POSIX/SDL裁剪行为。

## 实施结果 — Completed，用户确认/commit Pending

生产仅device.c/fs.c，9增1删；前51项已确认提交，本组使累计52已修/67未修完。
fb_write在任何坐标窄化、像素指针推进或FBDRAW前验证正尺寸及LONG_MAX容量，
按`size-offset`限制len，EOF/越界不调用GPU。fs初始化在size_t域安全计算同一容量，
非法或不可表示尺寸容量为0。沿用offset/4、len/4：内部非对齐offset仍向下取像素，
不足4字节不画；靠近末端时先截字节再取完整像素，因此offset45/4×3屏幕只剩3字节时
返回0。没有新增字节级FB写协议、颜色/alpha策略、调度或图形库修改。

| 验证 | 结果 / local证据 |
|---|---|
| 原4反例 | Git07bba74实际device/fs：4×3屏幕EOF写4、末像素写8返回超量被断言拒绝exit-6；50000×50000容量在旧int域溢出、零宽除零被UBSan拒绝exit1。unit-results.json/before日志 |
| host最终组合 | 普通和MULTIPROGRAM分支各55场景、各1547 ASan/UBSan断言；fs_write与直接callback，首像素/零长/不足像素/非4倍/跨行/末像素/恰EOF/直接越界/SIZE_MAX offset与len、非对齐offset、0/负尺寸/INT_MAX²和有效100亿字节容量。检查实际返回、fs offset、AM每段坐标/连续像素/高1及sync、输入全部哨兵不变。AM类型真实，IO/盘为stub；LSan关闭；非32位宿主测试 |
| 真实旧内核 | 同一个RV64 payload已完成正常首/跨行/末像素写，输出FB-EOF-BEGIN后EOF写4触发EVENT_ERROR4、BAD TRAP/exit1。补充monitor寄存器证明mcause7、mtval=0xa11d4c00，恰为800×600×4真实vmem映射后一字节，mepc符号__am_gpu_fbdraw。不是把启动/夹具失败当反例；before-registers.json/log |
| 真实新内核 | freestanding RV64用户ecall→FS→实际AM/MMIO，正常跨行/末像素、EOF、跨末端/超长/SIZE_MAX len、非对齐offset与不足像素、非法seek不污染offset及输入哨兵均通过，FB-GUEST PASS+GOOD TRAP/exit0。runs.json/after-guest-run.log |
| 构建/纯生产 | 1个payload、旧guest/新guest/新FG三内核构建成功；真实NEMU执行器未改，新FG 1亿指令后monitor q/exit0、hello进展正常。builds/fixtures/runs.json |
| 默认三前台 | 52.88秒8观察点：PAL标题/动画；nterm qzx报command not found后新prompt；nslider0→1→0且返回帧SHA相同；返回PAL仍有标题与原窗口蓝边。10条SDL真实队列命令顺序完整，hello37→156。nanos/result.json/observe.log、visual-qa.json |
| PAL补充 | 同一FG生产内核另运行58.56秒，25秒后标题、Enter后15/30秒标题/飞鸟动画进展，hello86→180；全部实际RGB帧已目视。两次观察均自有组SIGTERM/实际exit0，非guest正常完成或实体音视频/长期游戏声明。pal-long/result.json |
| 身份与清理 | 27项preclean核对、159份消费者源码/头/链接脚本身份；原盘/默认kernel/native/config及NDL/SDL/loader/proc身份保持，两个临时盘全SHA保持、payload ELF与追加extent完全一致。353文件320985531逻辑字节（约306.1MiB）清理，零tracked删除/零剩余产物。cleanup-plan/receipt解释已删除路径 |

夹具/观察更正：首次host编译漏ARCH_H，按原夹具补arch/riscv.h；早期guest检查器
只接受用户FAIL/ABORT，实际原实现触发内核EVENT_ERROR/BAD，初始误判记录保留，
后续独立CSR/符号证据确认原因。最初预清理检查器误数SDL命令为9，改为核对10条
明确顺序；均无生产修改/安装。初始PAL缩略图为黑色是PIL缩放RGBA时把协议未使用
的alpha0作透明再预乘所致；先转RGB再缩放后，原8帧即显示正常PAL，并已重看原帧。
额外长观察同样通过；不得把这次缩略图错误写成guest黑屏。fixture-corrections.json
保留说明，visual-qa.json保留最终目视与帧身份。

## 影响、限制与再生

影响仅nanos FB特殊写及FB size初始化；正常NDL/SDL绘图使用对齐整像素范围，本组
覆盖实际用户写、三前台及hello。CPU-tests/RT/REF/NPC RTL不调用这两个nanos函数，
闭包未受影响不重跑；未测NPC nanos、全部app/配置、长期/物理显示/声音。用户指针
隔离F0073、NDL非法矩形F0091、其他SDL问题及原PAL返回蓝边保持，不从本组推定
完整图形协议/全屏重绘正确。设备尺寸稳定沿用现行配置，未新增热插拔能力。

旧实现从Git07bba74重建，新实现以该版本+local/repair.patch；原Navy盘/header输入
来源和SHA见entry-identity，追加仅本地生成的小payload，未改正式盘或默认内核。
复现（从仓库根目录执行，无安装/Make新选项/日常流程改变）：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0068/local/unit.py
python3 npc/verif/records/process/code_correctness_review/crp-f0068/local/prepare.py
python3 npc/verif/records/process/code_correctness_review/crp-f0068/local/run.py
python3 npc/verif/records/process/code_correctness_review/crp-f0068/local/inspect-old.py
python3 npc/verif/records/process/code_correctness_review/crp-f0068/local/nanos-run.local nanos
python3 npc/verif/records/process/code_correctness_review/crp-f0068/local/pal-run.local pal-long
```

观察输出目录须为空或另取名字；所有编译命令/环境/退出码在builds、unit-results、
fixtures、runs及process/result中；prepare复制当前AM与nanos并明确替换旧device/fs，
guest用TEST_NTERM，FG保留原99:1。RGB接触图配方见local/visualize.py。验证/目视完成
后再执行本地check/cleanup，不能先删除运行输入。现镜像/ELF/截图/构建源码副本
已经清理，哈希是当时身份；恢复不依赖已删二进制。保留最小测试源、脚本、配置、
日志/结果/patch及清理回执，local和.agent继续忽略，不随普通commit备份。

本组统一留档完成后停止，确认/commit Pending，无自动提交/push/安装/下一组或
M2推进。未来候选与门槛只见[唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。


<a id="submit-20261020"></a>
## 用户确认与提交收尾（2026-10-20）

用户“提交后继续”确认本组已报告范围/限制并授权提交后执行唯一下一组。复用原27preclean/15终检及清理，69项现存manifest身份无漂移，不重复产品测试/Completion/清理。只提交本组两生产源、报告/.gitignore、process索引及逐项台账6文件；local/.agent仍忽略。实际commit/文件blob及干净状态见local/submit-receipt.json，后续执行只按TASK_QUEUE唯一入口；无push。原报告中的Pending为交付时截面。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0068 — 根仓库

容量校验在初始化与实际写入两侧保持一致。

- 差异路径相对于仓库 `.`；旧版本：`07bba7481b1910c00bbfd634d0df513122dc0ab6`；新版本：`9fb8831caab7b1e79d279f7a9026e983204de41c`。

#### `nanos-lite/src/device.c`

F0068：先拒绝非正宽高，再以 `width > LONG_MAX / 4 / height` 检查容量乘法，短路保证不除零；合法后计算屏幕总字节数。offset 已到尾部返回 0，len 按 `size-offset` 截断，再进入原按行写像素循环，防止向屏幕外发起绘制。原 len/4 的整像素计数语义保持。

```diff
diff --git a/nanos-lite/src/device.c b/nanos-lite/src/device.c
index 484f5c5c0e3f8d3a6335c477ade4f4050b95aa23..e689f25dae0594677b55b5b290be1f27a5a50c3c 100755
--- a/nanos-lite/src/device.c
+++ b/nanos-lite/src/device.c
@@ -1,5 +1,6 @@
 #include <common.h>
 #include <proc.h>
+#include <limits.h>
 
 #if defined(MULTIPROGRAM) && !defined(TIME_SHARING)
 # define MULTIPROGRAM_YIELD() yield()
@@ -78,6 +79,11 @@ size_t dispinfo_read(void *buf, size_t offset, size_t len) {
 size_t fb_write(const void *buf, size_t offset, size_t len) {
   MULTIPROGRAM_YIELD();
   cfg = io_read(AM_GPU_CONFIG);
+  if (cfg.width <= 0 || cfg.height <= 0 ||
+      (size_t)cfg.width > (size_t)LONG_MAX / 4 / (size_t)cfg.height) { return 0; }
+  size_t size = (size_t)cfg.width * cfg.height * 4;
+  if (offset >= size) { return 0; }
+  if (len > size - offset) { len = size - offset; }
   size_t px = offset / 4, left = len / 4, done = 0;
   while (left > 0) {
     int y = px / cfg.width, x = px % cfg.width;
```

#### `nanos-lite/src/fs.c`

F0068：init_fs 使用同样的宽高/容量判断设置 `/dev/fb` 尺寸，不合法配置记 0；先转 size_t 后乘法，避免原 int 乘积溢出，保证文件 seek 上界与 fb_write 的容量一致。

```diff
diff --git a/nanos-lite/src/fs.c b/nanos-lite/src/fs.c
index e55821e2eb7c9572523f9a11182f272ebf7966ac..e6e3323390f1d3120ea0d72345ed0f2cd8372196 100755
--- a/nanos-lite/src/fs.c
+++ b/nanos-lite/src/fs.c
@@ -167,7 +167,9 @@ void init_fs() {
   for(int i=0;i<filenum;i++){fp_offt[i] = 0;}
   // initialize the size of /dev/fb (screen_w * screen_h * 4)
   AM_GPU_CONFIG_T cfg = io_read(AM_GPU_CONFIG);
-  file_table[FD_FB].size = cfg.width * cfg.height * 4;
+  file_table[FD_FB].size = (cfg.width > 0 && cfg.height > 0 &&
+      (size_t)cfg.width <= (size_t)LONG_MAX / 4 / (size_t)cfg.height)
+    ? (size_t)cfg.width * cfg.height * 4 : 0;
   // initialize the sound card
   audio_init();
 }
```
