# CRP F0020 — SD卡访问方向、文件I/O与按需空间

2026-10-20，复用CRP整体计划及workflow。前F0118最小静音子范围已确认提交be8a4c0，整项仍Partial，不推进M2。

## 本单元计划

目标：修复SDCMD读取重放、反向SDDATA推进；维持原MMC多块PIO及EXT_CSD消费者。只改nemu/src/device/sdcard.c，不新增Make/设备公开接口或自动创建镜像。

用户明确要求16 GiB不在启动预占；随后明确裁决缺盘/越界/实际I/O失败诊断终止NEMU，容量以内未写区域读零、写入时按需增长。这替代原队列中待决失败语义，不自动继承F0009。标称16 GiB保持，打开/读长度不扫描镜像、不malloc/mmap整盘、不ftruncate预扩展、不写零填盘。稀疏文件空洞由宿主文件系统承担；测试分别记录逻辑长度与st_blocks实际占用。

阶段/交付/验收/停点：一个F0020单元；先旧源同夹具见证，再生产最小修复，host普通/ASan+UBSan及真实RV64新NEMU的MMIO guest验证方向/命令不重放、正常多块/EXT_CSD、零填尾部、容量边界、短I/O失败及实际空间。SD默认关闭，使用隔离配置/临时镜像，不替换默认配置/引擎/盘。保留命令、身份、完整diff与结果，清理本组可再生产物，更新records与.agent后停等结果确认/commit；不提交本组、不push、不安装。完整Linux驱动启动无已配套镜像/内核时记NotRun，不以host代替。无需软件安装；失败/尾部策略已获用户确认。

<a id="f0020-final-20261020"></a>
## 最终结果（2026-10-20）

F0020 Completed，结果确认/commit Pending；95完全已修/24未修完，前94及F0118最小静音子范围已确认提交。旧审阅、前组完成快照及manifest保留，不回写历史。当前HEAD `be8a4c0aaa679c09e9411c0303a669a0ac220bc5`，本组Working tree contains uncommitted repair/documentation changes；未push/安装/下一单元/M2。

### 实现与空间边界

- `SDCMD`仅写入触发`sdcard_handle_cmd`，读取只取寄存器；`SDDATA`必须处于活动传输且`is_write == write_cmd`才消费/写入数据。反方向访问允许落寄存器但不推进文件或EXT_CSD游标。EXT_CSD读完512字节退出；STOP/GO_IDLE结束传输，新的读写命令退出旧EXT_CSD。访问宽度固定4字节、偏移必须4字节对齐；现有resource/sdcard驱动使用readl/writel符合这一约束。
- 原`long blk_addr << 9`改为64位`disk_pos = (uint64_t)SDARG * 512`，先检查16 GiB容量及off_t可表示性再fseeko；每4字节读写再次检查容量，防止流式跨末端。保留原CMD23块数记录/由驱动循环控制传输，不在此修复增加完整卡状态机或单块命令支持。
- 初始化只打开现有可写镜像、SEEK_END/ftello取长度并回到起点，寄存器仍仅0x80字节（映射层页对齐）；不会创建缺失文件、扩大文件、扫描内容、malloc/mmap整盘或写16 GiB零数据。容量仍由CSD/EXT_CSD报告16 GiB；镜像逻辑长度和实际占用独立。
- 读取时先清零4字节目标，再只读初始化或本设备写入后已知有效文件长度内的字节；不足4字节尾部和其后未写区域为零。读完整稀疏文件的宿主空洞同样为零。写入从目标偏移按4字节增长，跳过区间由宿主文件系统以稀疏空洞表示；不做全盘初始化。实际占用粒度依文件系统而定。
- 检查fopen/fseeko/ftello/fread/fwrite/fflush；已知有效区内异常短读、短写、flush失败及越界明确诊断并终止NEMU，符合用户裁决；不静默回报成功或新增可恢复错误ABI。写每个完整512字节PIO块后flush，在STOP/复位/切换传输前flush剩余写缓存；这不承诺fsync持久化、故障回滚或并发修改镜像的一致性。

### 本次验收

| 验证 | 结果/范围 |
|---|---|
| Git旧版同夹具反例 | `be8a4c0`源，读SDCMD重放回到原文件偏移、反向写SDDATA继续读盘分别被同一新契约精确拒绝；均SIGABRT，失败行记录在old-baseline/old-reverse.log，不当成新实现PASS。 |
| 实际map.c+SD源host | 普通与ASan+UBSan各529条正常断言；真实生产map_read/write的先回调读/先存储写顺序，覆盖命令重复读、反方向、STOP/IDLE、512字节EXT_CSD、部分尾字、完整读写及最后扇区/未写空洞。两构建各空盘132断言，读末扇区仍logical=0/allocated=0。 |
| 失败注入/边界 | 普通及san各10情形：缺盘、起始块越界、连续读跨末端、未对齐、宽度2、seek失败、短read、实际有效区被截断、短write、flush失败共10个失败模式（包括正常与空盘共12运行）；所有预期SIGABRT和诊断独立核对。总3构建+26运行=29条命令通过，ASan泄漏检测因环境限制关闭，UBSan遇错停止。 |
| 空间观察 | 1027B镜像初始化前后logical=1027/allocated=4096，不增长；写最后一个512B扇区后logical=17179869184/allocated=8192。是16 GiB逻辑容量、8 KiB实际分配；空盘只读后0/0。 |
| 新完整NEMU/真实RV64 | 隔离开启SD并指向临时镜像，当前源-Werror构建，直接客户机MMIO验证命令/方向/EXT_CSD/CMD23两块写读/最后块/未写空洞，输出`SD GUEST PASS ...`并GOOD TRAP/exit0；此次正常运行约0.367s。起始块越界/跨末端/缺盘三例均诊断SIGABRT。13条真实构建/运行命令exit匹配预期。 |
| 初始化内存界限 | 同版真实guest在RLIMIT_AS=512 MiB下完成，末端写后逻辑16 GiB/实际8 KiB，证明本路径无需16 GiB内存映射或分配；限制仅为本配置实测，不承诺全平台峰值内存。 |
| 保护/归档/清理 | 16项preclean PASS；默认配置/用户NEMU与nanos引擎/正式盘/header五项SHA不变，隔离已执行SD源SHA与生产最终源相同。完整diff正向逐字节等于新源、反向恢复旧源；Git mode仍100755。已清理1996文件，逻辑85912869061B/实际19857408B，0 tracked/默认资产删除。稀疏镜像身份只核数据extent及长度，未扫描16 GiB空洞。 |


测试夹具早期旧源复制缺mmc.h搜索路径已修正；truncate负例需对测试流关闭stdio缓冲，防止已预读缓存掩盖实际EOF，不更改生产流缓冲。首次裸guest带GNU build-id导致镜像开头为note/非法指令，已在测试链接禁用build-id，最终所有真实guest均由修正后的ELF/BIN执行，初次失败日志单列。生产源format类型告警已通过uint64_t显式转换解决，最终host新源及真实-Werror构建无告警；旧源夹具未使用的拦截函数告警不属于生产缺陷。

### 完整修复diff与身份

根仓ysyx-workbench，旧完整commit `be8a4c0aaa679c09e9411c0303a669a0ac220bc5`，新为2026-10-20未提交工作树。
旧SD源SHA256 `4732d73acb3c8ccf5d18962f5f09c926a5d393739b63e75c69722d93ce0d646a`；新SHA256 `0335bcc96825c3d9633d850b12111cbaf8b1804b560581befe712a03d8973da2`。

```diff
diff --git a/nemu/src/device/sdcard.c b/nemu/src/device/sdcard.c
index 7e486340cbccba8aa3cb1adfaae685cc62231514..108e2af89b6f1ab97c12eea5866e3b63ec85c0e9 100755
--- a/nemu/src/device/sdcard.c
+++ b/nemu/src/device/sdcard.c
@@ -43,21 +43,37 @@ enum {
 static FILE *fp = NULL;
 static uint32_t *base = NULL;
 static uint32_t blkcnt = 0;
-static long blk_addr = 0;
+static uint64_t disk_pos = 0;
+static uint64_t image_size = 0;
 static uint32_t addr = 0;
 static bool write_cmd = 0;
 static bool read_ext_csd = false;
+static bool transfer_active = false;
+
+static void flush_write() {
+  if (transfer_active && write_cmd && !read_ext_csd) {
+    Assert(fflush(fp) == 0, "sdcard flush failed");
+  }
+}
 
 static void prepare_rw(int is_write) {
-  blk_addr = base[SDARG];
-  addr = 0;
-  if (fp) fseek(fp, blk_addr << 9, SEEK_SET);
+  flush_write();
+  disk_pos = (uint64_t)base[SDARG] * 512;
+  Assert(disk_pos < MEMORY_SIZE && (off_t)disk_pos >= 0 &&
+      (uint64_t)(off_t)disk_pos == disk_pos, "sdcard block out of range: %u", base[SDARG]);
+  Assert(fp != NULL && fseeko(fp, (off_t)disk_pos, SEEK_SET) == 0,
+      "sdcard seek failed: offset=%" PRIu64, disk_pos);
   write_cmd = is_write;
+  read_ext_csd = false;
+  transfer_active = true;
 }
 
 static void sdcard_handle_cmd(int cmd) {
   switch (cmd) {
-    case MMC_GO_IDLE_STATE: break;
+    case MMC_GO_IDLE_STATE:
+      flush_write();
+      transfer_active = read_ext_csd = false;
+      break;
     case MMC_SEND_OP_COND: base[SDRSP0] = 0x80ff8000; break;
     case MMC_ALL_SEND_CID:
       base[SDRSP0] = 0x00000001;
@@ -73,7 +89,12 @@ static void sdcard_handle_cmd(int cmd) {
       base[SDRSP2] = 0x0f508000 | (C_SIZE >> 2) | (READ_BL_LEN << 16);
       base[SDRSP3] = 0x9026012a;
       break;
-    case MMC_SEND_EXT_CSD: read_ext_csd = true; addr = 0; break;
+    case MMC_SEND_EXT_CSD:
+      flush_write();
+      read_ext_csd = transfer_active = true;
+      write_cmd = false;
+      addr = 0;
+      break;
     case MMC_SLEEP_AWAKE: break;
     case MMC_APP_CMD: break;
     case MMC_SET_RELATIVE_ADDR: break;
@@ -82,16 +103,22 @@ static void sdcard_handle_cmd(int cmd) {
     case MMC_READ_MULTIPLE_BLOCK: prepare_rw(false); break;
     case MMC_WRITE_MULTIPLE_BLOCK: prepare_rw(true); break;
     case MMC_SEND_STATUS: base[SDRSP0] = 0x900; base[SDRSP1] = base[SDRSP2] = base[SDRSP3] = 0; break;
-    case MMC_STOP_TRANSMISSION: break;
+    case MMC_STOP_TRANSMISSION:
+      flush_write();
+      transfer_active = read_ext_csd = false;
+      break;
     default:
       panic("unhandled command = %d", cmd);
   }
 }
 
 static void sdcard_io_handler(uint32_t offset, int len, bool is_write) {
+  Assert(len == 4 && offset % 4 == 0, "invalid sdcard register access: offset=%u len=%d", offset, len);
   int idx = offset / 4;
   switch (idx) {
-    case SDCMD: sdcard_handle_cmd(base[SDCMD] & 0x3f); break;
+    case SDCMD:
+      if (is_write) sdcard_handle_cmd(base[SDCMD] & 0x3f);
+      break;
     case SDARG:
     case SDRSP0:
     case SDRSP1:
@@ -99,6 +126,7 @@ static void sdcard_io_handler(uint32_t offset, int len, bool is_write) {
     case SDRSP3:
       break;
     case SDDATA:
+       if (!transfer_active || is_write != write_cmd) break;
        if (read_ext_csd) {
          // See section 8.1 JEDEC Standard JED84-A441
          uint32_t data;
@@ -108,13 +136,26 @@ static void sdcard_io_handler(uint32_t offset, int len, bool is_write) {
            default: data = 0;
          }
          base[SDDATA] = data;
-         if (addr == 512 - 4) read_ext_csd = false;
-       } else if (fp) {
-         __attribute__((unused)) int ret;
-         if (!write_cmd) { ret = fread(&base[SDDATA], 4, 1, fp); }
-         else { ret = fwrite(&base[SDDATA], 4, 1, fp); }
+         addr += 4;
+         if (addr == 512) read_ext_csd = transfer_active = false;
+       } else {
+         Assert(disk_pos <= MEMORY_SIZE - 4, "sdcard transfer out of range: offset=%" PRIu64, disk_pos);
+         if (!write_cmd) {
+           // Unwritten capacity reads as zero; an unexpected short read is an error.
+           size_t expected = disk_pos < image_size ?
+             (image_size - disk_pos < 4 ? (size_t)(image_size - disk_pos) : 4) : 0;
+           base[SDDATA] = 0;
+           size_t done = fread(&base[SDDATA], 1, expected, fp);
+           Assert(done == expected && !ferror(fp), "sdcard short read: %zu/%zu", done, expected);
+         } else {
+           size_t done = fwrite(&base[SDDATA], 1, 4, fp);
+           Assert(done == 4 && !ferror(fp), "sdcard short write: %zu/4", done);
+           if (disk_pos + 4 > image_size) image_size = disk_pos + 4;
+         }
+         disk_pos += 4;
+         // Complete each PIO block before the driver can report it as transferred.
+         if (write_cmd && disk_pos % 512 == 0) flush_write();
        }
-       addr += 4;
        break;
     default:
       Log("offset = 0x%x(idx = %d), is_write = %d, data = 0x%x", offset, idx, is_write, base[idx]);
@@ -130,5 +171,12 @@ void init_sdcard() {
 
   const char *img = CONFIG_SDCARD_IMG_PATH;
   fp = fopen(img, "r+");
-  if (fp == NULL) Log("Can not find sdcard image: %s", img);
+  Assert(fp != NULL, "can not open sdcard image: %s", img);
+  Assert(fseeko(fp, 0, SEEK_END) == 0, "sdcard image seek failed: %s", img);
+  off_t size = ftello(fp);
+  Assert(size >= 0, "sdcard image size failed: %s", img);
+  image_size = (uint64_t)size;
+  Assert(fseeko(fp, 0, SEEK_SET) == 0, "sdcard image rewind failed: %s", img);
+  // Keep the 16 GiB capacity virtual: no allocation, prefill, or file extension.
+  Log("sdcard image: %s (%" PRIu64 " bytes, capacity=%" PRIu64 ")", img, image_size, (uint64_t)MEMORY_SIZE);
 }
```

内嵌diff与local/repair.patch及实际生产差异一致；archive-validation.json保存正反应用与身份结果。隔离模型/源码及guest身份见real-identities/runtime-identities；模型已清理，哈希仅标识当时产物，不声称仍可执行。

### 复现与限制

保留最小配方`local/run.py`、harness.c/include及`real.py`、guest.c/guest.ld、配置/实际命令/结果/诊断/patch。恢复注明Git版本加patch后，在现有工具环境执行：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0020/local/run.py
python3 npc/verif/records/process/code_correctness_review/crp-f0020/local/real.py
```

run.py旧源从be8a4c0再生；real.py仅复制NEMU，不下载或安装，使用已有交叉编译器。重跑后须按已有清理策略删除本组镜像/模型；local/cleanup.py仅用于本组验证后清理。RLIMIT_AS追加验收命令见real-limited.json，正式资产见entry.json；本地证据不随普通commit备份。

真实消费者范围为新NEMU上客户机直接寄存器访问，并非宿主函数模拟；完整Linux MMC驱动/文件系统挂载/实体卡仍NotRun。默认SD关闭，不改disk/audio/AM/Navy/RT/CPU或REF，未重跑不依赖SD的三前台/RT全量测试；resource/sdcard驱动仅核对readl/writel及CMD23→多块PIO调用契约，未编译/执行整个Linux。单块命令、完整MMC错误状态、计时/IRQ/DMA、32位宿主大文件、外部并发修改镜像及掉电持久性不在本组验收范围。用户已选失败终止，未将其记成客户机可恢复错误。

本单元完成后停止，等待结果确认/本组commit，不自动下一单元。唯一未来入口TASK_QUEUE#crp-next；会话建议：可在当前对话继续，当前SD修复边界与证据已完整落档，下一次操作仅需沿该入口恢复。

最终终检：42项全部通过，70份保留证据身份固定。逐一核对普通/san十种失败及真实三负例均为预期诊断，未用其他sanitizer崩溃充当预期拒绝；完整patch/五正式资产/1996预期清理/119行95与24计数及唯一入口一致。无新增生产改动或commit。背景参考：2026-10-20读取[ICS-PA输入输出](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)中MMIO/命令字与状态访问说明；它不规定本项目SD卡错误或空间策略，这两项以上述用户裁决及本地实现为准。

## 用户确认与提交收尾（2026-10-20）

用户“提交并继续”确认已报告的F0020范围并授权精确提交后F0075一个单元。70保留证据身份/生产完整patch无漂移，复用42项终检、真实RV64及空间验收，不重跑。仅提交SD源、本报告/.gitignore、process及逐项索引；实际提交回执在local/submit-receipt.json与.agent，ignored资料不随commit备份，不push。可在当前对话继续：磁盘下一单元与本轮存储上下文相关且恢复入口明确。
