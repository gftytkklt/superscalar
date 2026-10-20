# CRP F0075 — nanos磁盘容量/offset与块号边界

2026-10-20，用户“提交并继续”确认F0020并授权本单元；前组实际8e5b1ca。复用整体修复计划/CRP workflow及TASK_QUEUE#crp-next，不推进M2。

## 本单元计划

目标/范围：nanos-lite/src/disk.c的设备盘块容量/字节算术/AM int块号窄化；保留512B恒等映射内核bounce buffer，核fs/loader消费者及内嵌fallback。未扩AM void错误接口或新增构建入口。

一个工作单元：先现源和旧反例，范围/失败边界未决先用户裁决；明确后同轮最小修改、同一夹具host普通/san及真实RV64新NEMU+AM+nanos disk/受影响标准update→run消费者验证。坏offset/len/容量/溢出/零长、正常跨块与RMW/内嵌回退、底层实际错误沿F0009已批准终止；不伪造上层可恢复错误。

交付：生产最小修复（获裁决后）、本报告/.gitignore、本地最小配方/实际命令结果/身份/完整diff及正反归档、records和.agent。正式配置/用户引擎/盘不覆盖，隔离镜像/模型验证后清理。验收明确后完成即停等结果确认/commit，不push/安装/下一组。必要人工项：设备盘越界应像内嵌盘截短还是严格拒绝，已发最少裁决问题；不因继续或SD策略推定。

## 必要现源分析/旧见证（策略待裁决，生产未改）

实际盘配置512B×2；同版生产disk.c与受控AM调用记录器观察：offset1020/len8返回8、发两块请求且第二块越界；offset1024/len1返回1并发盘外请求；offset=SIZE_MAX-2/len6返回6、首块块号窄化为无效值，offset+done随后回绕至块0。正常跨块读与RMW独立六项检查通过。旧源对拟采用的截短契约首先在尾读长度断言失败exit1；最终策略未裁决前，此候选oracle不等于已获准修复。

fs_read/write按disk返回数推进偏移；TEST_DUMMY loader要求精确读满，短读返回false。内嵌盘已有offset>=size返回0、len截短至size-offset。AM_DISK_BLKIO仍void，无可恢复I/O错误；NEMU设备F0009已批准实际I/O错误诊断终止。上述既有事实并未唯一决定设备盘越界应截短还是终止，已按WORKFLOW_POLICY§3/TASK_QUEUE最少提问，不自动把SD选择推广到本接口。

现产物local/before及最小harness/include；命令/输出见before-results与before-*.log，host调用桩不冒称真实DMA/guest，生产零修改/无新完成计数。本组Active，95完全已修/24未修完不变；待策略答复后直接续作，不新增分析文档commit门槛。

分析收尾：17项身份/现象/保护检查通过，11份最小证据身份固定；已删除唯一测试可执行文件39072B，0 tracked删除，未复制镜像或生产源码。生产零修改；无运行中测试/guest。可由`python3 local/reproduce.py`在当前目录按8e5b1ca旧源再生，输出相同三项观察/正常6检查/候选尾读断言拒绝，再自动清理临时旧源及可执行文件。只有host必要分析，不是功能修复、真实guest或完整标准消费者验收；不执行Phase Completion、不增加计数。等待用户越界语义答复后续作本单元，不要求单独提交分析资料。

## 用户裁决与直接实施（2026-10-20）

用户明确选择“沿用内嵌盘：跨尾截短，起点在盘外返回0”。同单元继续，前述待决状态为历史；无需提交分析文档或再次确认。设备盘取有效512B配置容量，使用capacity-offset截短再计算块号/位置；零长在配置读取与内嵌memcpy之前返回0。底层void错误接口不扩展，实际I/O失败沿F0009终止；普通合法读/RMW保持。配置已不符合现有512B缓冲或缺盘/非正块数/容量乘法溢出时容量为0，不发I/O；这沿disk_size既有无效容量返回0规则。

<a id="f0075-final-20261020"></a>
## 最终实现与验收（2026-10-20）

F0075实施与功能验证完成，结果确认/本组commit Pending；累计96完全已修/23未修完，前95已确认提交。旧必要分析/待决文字为当时截面，用户后续已明确选择截短。HEAD `8e5b1ca8a8b03a6a7c37b04c025521db44747938`，Working tree contains uncommitted F0075 repair/documentation changes；不push/安装/下一单元/M2。

### 实现及调用链

生产仅`nanos-lite/src/disk.c`，16增3删，Git mode100644保持。

- `disk_size()`在已初始化设备路径检查当前present、固定512B块长、正块数及乘法可表示性；无效容量返回0，沿既有无效容量规则。512B约束与`blkbuf[512]`及原init断言一致，不接收更大块后覆盖bounce buffer。
- 新`disk_transfer_size()`先取容量，`offset >= capacity`返回0；其余用`capacity - offset`限制len，在任何`offset + done`和AM int块号转换之前收束范围。`done < len <= capacity-offset`保证pos不回绕；有效块号小于正int类型blkcnt，因而能装入AM的int。正常块号/每次1块/内核物理bounce buffer均保持。
- `disk_read/write`最前面`len==0`直接返回0，不查询配置、发块I/O或调用内嵌memcpy；设备盘按实际截短长度循环并返回该长度。读取只改实际返回长度内的buf；写仍逐块读改写，保留块内区间外字节。
- FS按disk实际返回数推进offset；TEST_DUMMY loader精确读满判据沿用，截短不会冒充完整镜像读成功。未改变AM_DISK_BLKIO的void接口、寄存器、用户ABI或Make入口；底层真实I/O错误按已批准F0009诊断终止，未新增可恢复错误或把失败当0字节成功。

### 本次验证

| 验证 | 结果及范围 |
|---|---|
| 旧源反例（必要分析复用） | 两块盘offset1020/len8回8且请求第三块；盘外1024/1回1；SIZE_MAX-2/6首块窄化无效并随后回绕块0。旧源对本次获准尾部截短判据精确exit1拒绝，正常跨块/RMW六项通过；原before-results/日志不改写。 |
| 最终host普通及ASan/UBSan | 两构建各79条断言；正常跨块/RMW、尾部截短/目标尾哨兵、盘外与极大offset、len=SIZE_MAX、零长NULL不读配置/不I/O、已初始化后无效配置、最大正int块数的最后一字节及AM块号、无盘与内嵌分支。六构建/运行命令exit0；LSan关闭，不宣称泄漏验收。 |
| 新旧观察对照 | 两最终构建均TAIL回4/命令1/越界0，PAST回0/命令0，OVERFLOW回0/命令0；未删旧反例或放宽oracle。 |
| 实际RV64 NEMU+AM+nanos disk | 当前隔离NEMU、真实AM DISK驱动及实际nanos disk.c编译单元，17项正常/跨尾/盘外/极值/零长/RMW检查，GOOD TRAP/exit0。宿主独立构造预期，完整1024B镜像逐字节相同。 |
| 后端错误/无盘 | 同版真实MMIO路径注入fread短读0/512，预期NEMU SIGABRT并打印disk short read，不会返回guest的成功；无盘3项检查/GOOD TRAP/exit0。共七条实际目标构建/运行命令exit与预期一致。 |
| 标准update→run消费者 | 当前隔离源码/已有资源，nanos标准update exit0约25.735s，随后标准run，真实10个SDL按键；nterm输入qzx后命令未找到并返回prompt，幻灯片0→1→0、PAL初始/返回/Enter继续渲染，8帧目视；hello41→178。约53.448s后自有进程组SIGTERM，make -15非正常guest退出。 |
| 归档/身份/正式资产 | 155项preclean PASS，5925项输入/产物身份；生产、目标guest与标准消费者三份disk.c SHA一致，目标和标准NEMU同一身份。108项ramdisk extent与各fsimg内容一致、末尾只有padding；4个前后台ELF链接/安装身份匹配。五项正式配置/用户引擎/盘/header SHA与entry相同。完整patch正向等新源、反向等旧源。 |

目标guest初次仅因测试源for后紧接断言触发-Werror=misleading-indentation，已加测试循环花括号，未改生产编译规则；初次日志单列。必要分析manifest作为旧截面保留，其中harness.c在授权实施时增加最终79项检查，变动会另存implementation-input-changes，不把原分析探针/host桩当真实guest。原baseline可从8e5b1ca及保留配方再生。

### 完整框架修复diff

根仓ysyx-workbench；旧完整commit `8e5b1ca8a8b03a6a7c37b04c025521db44747938`，新为2026-10-20未提交工作树。
旧SHA256 `64cb8d3576021e93bbcfe57c1774eda1cf36f590f1fee96e14cbc919b7c292f8`；新SHA256 `f57cfb5e472d0cdb53613d11fd101dbc0b1a1dffa76d6188b776eef470f4fe25`。

```diff
diff --git a/nanos-lite/src/disk.c b/nanos-lite/src/disk.c
index 8b89cb173ecfadec2902f0eedc48ba5c27fa181d..514069cee682142d3f04af3487868c24b9e99ba4 100644
--- a/nanos-lite/src/disk.c
+++ b/nanos-lite/src/disk.c
@@ -35,7 +35,7 @@ void init_disk() {
 size_t disk_size(void) {
   if (!disk_present) return embed_size;
   AM_DISK_CONFIG_T cfg = io_read(AM_DISK_CONFIG);
-  if (cfg.blksz <= 0 || cfg.blkcnt <= 0 ||
+  if (!cfg.present || cfg.blksz != BLKSZ || cfg.blkcnt <= 0 ||
       (size_t)cfg.blkcnt > SIZE_MAX / (size_t)cfg.blksz) return 0;
   return (size_t)cfg.blksz * (size_t)cfg.blkcnt;
 }
@@ -47,10 +47,20 @@ static size_t embed_read(void *buf, size_t offset, size_t len) {
   return len;
 }
 
+static size_t disk_transfer_size(size_t offset, size_t len) {
+  size_t capacity = disk_size();
+  if (offset >= capacity) return 0;
+  // Subtract before adding offsets or narrowing block numbers to the AM int.
+  return len > capacity - offset ? capacity - offset : len;
+}
+
 /* read `len` bytes at byte offset `offset` from the disk into `buf` */
 size_t disk_read(void *buf, size_t offset, size_t len) {
+  if (len == 0) return 0;
   if (!disk_present) return embed_read(buf, offset, len);
-  size_t blksz = io_read(AM_DISK_CONFIG).blksz;
+  len = disk_transfer_size(offset, len);
+  if (len == 0) return 0;
+  size_t blksz = BLKSZ;
   size_t done = 0;
   while (done < len) {
     size_t pos = offset + done;
@@ -67,6 +77,7 @@ size_t disk_read(void *buf, size_t offset, size_t len) {
 
 /* write `len` bytes from `buf` to byte offset `offset` on the disk */
 size_t disk_write(const void *buf, size_t offset, size_t len) {
+  if (len == 0) return 0;
   if (!disk_present) {
     // embedded ramdisk: in-memory write-back (the section is writable)
     if (!embed_ptr) return 0;
@@ -75,7 +86,9 @@ size_t disk_write(const void *buf, size_t offset, size_t len) {
     memcpy(embed_ptr + offset, buf, len);
     return len;
   }
-  size_t blksz = io_read(AM_DISK_CONFIG).blksz;
+  len = disk_transfer_size(offset, len);
+  if (len == 0) return 0;
+  size_t blksz = BLKSZ;
   size_t done = 0;
   while (done < len) {
     size_t pos = offset + done;
```

上述为全部修复hunk，与local/repair.patch及实际生产差异一致；archive-validation保存正反逐字节核验及Git mode100644。没有将报告中的历史空上下文行改写成别的补丁。

### 复现、限制与停点

本地最小源/配方、实际命令/退出码/结果、配置/输入身份/完整patch保留；运行旧源可执行local/reproduce.py；最终验收使用：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0075/local/run.py
python3 npc/verif/records/process/code_correctness_review/crp-f0075/local/prepare-runtime.py
python3 npc/verif/records/process/code_correctness_review/crp-f0075/local/real.py
python3 npc/verif/records/process/code_correctness_review/crp-f0075/local/standard-path/run-standard.py nanos
```

prepare-runtime复用已有当前源码/资源和工具，隔离复制并重映射绝对symlink，无下载/安装；只在本批已清理的work不存在时执行。恢复后按entry/最终身份及注明patch配对，不拿之后源变化当本次验收。无新增日常Make步骤，标准入口仍update→run。

单bounce buffer仍依赖现单核串行调用，不保证多核/可重入/热插拔中途配置变化；本组不校验调用者任意无效内存地址，不增加AM错误ABI或文件表事务。底层部分写入后失败仍按F0009终止，不保证回滚。内嵌分支为实际C函数host内存夹具验证；NPC整机/RT/32位宿主/额外ISA未运行，未改其硬件与配置。用户选择的截短使上层获得实际字节数，不代表所有POSIX errno能力已实现；F0076独立未修。默认资产保持，完整框架diff及实际消费者同版验收已完成；本组完成留档后停等结果确认/commit，不自动提交或下一单元。

## 最终清理与完成边界

155项preclean/5925输入与产物身份、完整diff正反/8帧实际目视完成后，已删除本组9343文件/链接、357724084逻辑字节、385490944分配字节，0 tracked/正式资产删除。包括隔离源码/模型/镜像/对象/guest及截图；保留最小配方、实际日志/配置/身份/完整patch，清理明细implementation-cleanup-receipt.json。旧分析唯一ELF清理记录仍原位，不改写历史manifest；模型/截图哈希仅标识当时产物，复现需重建。

F0075 **Completed，结果确认/本组commit Pending**，96完全已修/23未修完；无运行中构建/guest，HEAD8e5b1ca/index空。唯一未来入口TASK_QUEUE#crp-next，下一F0076尚未开始；不自动commit/push/下一单元/M2。会话建议：建议开启新对话；当前对话已跨SD与nanos磁盘并积累多轮构建/证据，下一项转libos/newlib errno，恢复入口已完整保存。此建议不增加执行门槛。

最终终检22项全部通过，59份保留证据身份固定；155preclean复用、当前完整diff/两向归档/五正式资产/9343预期清理/旧分析授权夹具变化/119行96与23计数/唯一入口一致。无新增动态测试或commit；F0075 Completed，结果确认/本组commit Pending，本轮停止。

<a id="submit-20261020"></a>
## 用户确认及提交收尾（2026-10-20）

用户“提交后继续”确认上述已披露结果并授权精确提交，随后执行TASK_QUEUE唯一入口的F0076一个单元。提交前59保留证据身份、完整生产patch、五正式资产与22项既有终检复核一致；不重跑动态测试、不重复Completion。实际commit与路径/blob核验保存在local/submit-receipt及.agent。local/与.agent不随commit备份，无push。可在当前对话继续：本轮由完整恢复入口接管，F0076范围和验收清楚。
