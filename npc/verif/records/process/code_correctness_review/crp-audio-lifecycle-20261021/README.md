# CRP F0043 / F0118 — 音频提交与重开生命周期必要分析

## 整体计划（2026-10-21）

来源：用户“提交后继续”；F0073分析已确认提交00c3b04，F0073/F0029联合延期保持。本单元沿TASK_QUEUE#crp-next，复用CRP整体计划及workflow，不推进M2。

目标/范围：仅核现有NEMU/AM/miniSDL/NDL/nanos实际COUNT提交、ring游标、控制配置与Close/reopen调用；区分F0043未修异步竞争、F0118已批准且已提交的失败后写入前静音与剩余普通重开不一致。参考讲义允许简化与现有Linux需求；不从“继续”推定新协议、跨进程声卡所有权或队列重置策略获批。

阶段与交付：冻结必要源码/八正式资产及ONS既有差异→复用五层host桥接的最小夹具，以实际生产函数确定性交错观察COUNT、普通重开/关闭/失败，核读写游标和IRQ边界→形成建议及最少真实裁决→验证身份/清理构建产物、留报告/命令/退出码/配置SHA并同步records及.agent唯一入口。

验收：分别记录正常首开、普通Close后换配置、显式INIT与旧PCM、失败静音保持、COUNT读后消费再提交的结果。同步桩/确定性交错只证明现函数可达行为，不冒称真实线程安全、真实RV64/声音质量或整项已修；不改生产则无须重跑CPU/RT/游戏。保留最小探针/日志，构建目录验证后记录SHA再删除。

结束节点/人工项：真实COUNT协议、重开队列丢弃/保留与游标同步策略未决时分析后停下裁决；不实施生产代码，不自动commit本分析/push/下一组；安装或系统改动即停。本单元不重新裁决既有最小失败静音。

## 用户裁决与同单元实施计划

用户对本轮两个问题明确选择：**F0043“延期并保留风险（推荐）”；F0118“清空旧PCM后重开（推荐）”**。因此F0043仍Confirmed未修/批准延期；F0118继续本单元实施，不增加分析文档提交门槛。已批准清队列、同步读写游标、完整配置重开；失败后AM写入前静音及应用Close只停上层供给/不关闭全局设备保持。

实现边界：仅AM NEMU音频与NEMU音频两源。AM init仅读容量并写INIT=0取消旧延迟请求，避免第一轮配置最后一个寄存器写时提前Open；CTRL写完整配置、将软件wr_index归零，再写既有INIT寄存器值2作为“重开并重置流”提交。NEMU识别此值，在停止旧SDL回调后清COUNT/rd_index，随后打开新配置；失败仍置INIT0/诊断/AM不写ring。INIT1保留旧init-before-CTRL/显式重试语义与既有游标续接，不新增寄存器、公开AM/NDL接口或日常Make步骤。INIT1/2都不冒充通用ready；新AM/NEMU需配对，旧引擎不能保证新清队列语义。

验收：以本次Git00c3b04旧源为反例；最终普通/ASan+UBSan实际五层桥接验证首开一次、同配置/换配置清队列/游标同步、旧PCM不输出、新PCM按顺序输出、失败静音/显式重试及legacy INIT1保持。真实SDL dummy线程/真实RV64使用现有隔离配方验证控制提交、队列/PCM和故障；标准nanos update→run覆盖受影响AM消费者。保留F0043确定性交错缺陷见证，不宣称线程竞争已修。两源完整diff内嵌并正反核验后清理可再生产物，留档/索引/状态后停；新修复不自动commit/push/下一组/M2。

## 现源分析结果

本次旧基线为根`00c3b04`（完整身份见local/entry.json），15必要源码、八正式资产及ONS既有编码diff固定；旧F0118静音修复已确认提交be8a4c0。原FINAL_FINDINGS仍是历史审阅，不改写其原始“未修”截面。

- **F0043**：实际AM最终执行`outl(COUNT, inl(COUNT) + len)`；旧10B排队，读取10后插入真实生产audio_play消费4B，实际COUNT变6，再提交3B却写13，应为9。随后真实生产回调复制有效9B及4B未提交哨兵，读游标走到17、写游标13。此为真实函数的确定性交错，不是实际线程调度证明。最终修复组合仍复现同一现象，已明确延期，不宣称并发修好。
- guest中断屏蔽只约束模拟CPU；NEMU宿主SDL回调仍可运行。nanos当前ecall进入M态会清MIE，irq/syscall路径没有重新开中断，并不能排除host竞争。AM裸机可有自己的中断调用，不能把当前nanos串行路径推广为所有AM调用已互斥。
- 通用map_write先host_write寄存器内存再调用设备handler，map_read也在callback之后读共享内存。仅在COUNT handler最终赋值周围加锁，既不覆盖跨MMIO读改写间隙，也不自动保护handler之外的共享访问。若以后修F0043，应冻结整个发布/查询协议及权威计数存储，而非仅锁一条赋值；本轮未设计/实施增量COUNT或跨层锁命令。
- **F0118剩余普通重开**：五层实际函数桥接首次44100成功，入队10B；上层Close之后后端仍打开/Close=0/COUNT10，再Open22050/单声道/256返回成功但后端仍44100。裸INIT1能使后端重开，却保留旧PCM；相同配置Close/Open也保留旧队列。这与F0043不同，即使无异步消费仍成立。
- `SDL_CloseAudio`停止上层回调，NDL_CloseAudio调用close并将自身两fd设-1；**现nanos fs_close实际上只重置固定文件表偏移，没有动态fd销毁或设备关闭回调**。此前F0118分析把内核fs_close描述为“使fd失效”不够准确，本次按现源补正，不改写旧证据。当前全局设备无进程所有权协议，因此不将应用Close扩成全局声卡关闭。

原版六例（正常、COUNT交错、普通换配置重开、显式INIT保留PCM、相同配置重开、失败静音）各普通/ASan+UBSan一次，共12观察/24构建运行命令；普通与san同例输出一致。失败已按用户旧策略不写PCM；普通重试未重开仍如旧。这里只是分析观察PASS，不是旧版功能正确或F0043已修。

2026-10-21重新读取[讲义声卡](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)：声卡为选做，CTRL提供初始化配置；共享寄存器竞争允许不解决。Linux计划/M2计划未列nanos完整音频并发验收，不把这一缺省当作问题不存在。[SDL锁文档](https://wiki.libsdl.org/SDL2/SDL_LockAudioDevice)支持排除设备回调，但不替代guest完整读改写协议；[SDL关闭文档](https://wiki.libsdl.org/SDL2/SDL_CloseAudioDevice)说明关闭等待当前回调结束，支撑本次先停再清队列的顺序。仅核现行页面，不冒充用户历史讲义版本。

<a id="implementation-20261021"></a>
## F0118清队列重开实现与验收

本轮只有两生产源20增8删。F0043批准延期，不计Fixed/Closed/ApprovedGap；F0118在用户已选的可见静音降级及普通清队列重开契约内Completed，结果确认/新commit Pending。

### 具体实现与边界

1. AM init保留容量读取，INIT改写0；这样完整配置尚未写好时不会从旧pending请求提前打开。每次CTRL顺序写freq/channels/samples，wr_index归零，最后写INIT=2。新AM第一次CTRL只Open一次；普通同/异配置重开都提交，不依赖应用额外裸INIT或新日常步骤。
2. NEMU用reset_pending识别INIT2。SDL_audio_init先Close旧后端，等旧回调结束后才清rd_index/COUNT为0，继而按完整配置打开并PauseAudio(0)。不清写ring本体；COUNT0令旧内容不可消费，新AM从0开始写，新的回调从0读。清流发生在停旧回调之后，不需要持有SDL锁跨越Close，也不把配置阶段写寄存器当作重开。
3. INIT1保留原init-before-CTRL延迟一次打开和显式旧式重试/游标续接语义；普通samples寄存器写不再触发重开。INIT0仍是未请求/取消/失败禁用，INIT1或2均可能是pending或已打开，**不是统一ready标志**。新清流功能须新AM与新NEMU配对；旧引擎不识别清流语义，不能声称任意新旧混配正确。
4. 子系统/Open失败沿原诊断及audio_disable路径，INIT0、COUNT0，AM在写ring前返回。CTRL2失败时两端游标已归零；以后普通CTRL可再次提交新请求，不增自动循环重试、驱动纠错或应用错误API。上层Open/Play可能依旧返回成功，这是已批准可见静音降级；不是完整SDL后端错误传播。
5. 应用Close仍只停止供给/关闭NDL句柄，当前已提交PCM可能继续在全局设备消费；下一次CTRL明确丢弃旧队列。不扩跨进程所有权或多人并发生产；旧式INIT1直接调用者保留旧行为，不自动清旧PCM。正常COUNT异步竞争独立保留。

### 实际验证

| 项目 | 结果 / 证明范围 |
|---|---|
| 旧版新契约反例 | Git00c3b04两旧源，close-reopen、same-config、reopen-fail三例均在重开/清队列断言exit1；对应前期原行为对照保持。不是编译失败当反例 |
| 最终host实际五层链 | 8例×普通/ASan+UBSan共16成功运行：正常、新旧INIT延迟首开与裸samples不重开、INIT1已有PCM续接、同配置/换配置清旧队列、新PCM完整/欠载清零、首次Init/Open失败、重开失败/普通CTRL重试。19运行+18构建共37条命令含3旧失败；LSan关闭未宣称通过 |
| 判据/保留风险 | 两假PASS（丢完成标记、非零exit）被拒绝；最终实际函数COUNT交错仍13而非9、4B未提交哨兵被消费，F0043未修有新组合见证 |
| 真实RV64控制与PCM | 当前隔离引擎/AM，5 guest均GOOD TRAP/exit0。正常65537B负载在69632B生产回调输出中连续匹配，其他字节全0；callback确为不同host线程。不证明实体声音或线程竞争已修 |
| 真实换配置清队列 | 首次8000Hz/单声道/1024，观察库特意保持第一后端paused以确保旧512B排队；CTRL改16000Hz/双声道/256后COUNT0，旧后端Close一次，新512B完整出现于第二后端13312B输出，余部全0。未播放旧512B；暂停只用于隔离见证，不改生产源码/调度 |
| 真实三失败 | Init失败/首次Open失败/普通第二CTRL重开失败均INIT0/COUNT0，3×65537B API提交返回且65536B ring逐字节未变。后两例再次普通CTRL成功，新512B完整、余部静音；日志旧名EXPLICIT_SUCCESS指显式CTRL调用，**不是裸INIT1或自动重试** |
| 标准Navy update→run | 隔离现源/现有资源，nanos目录原update入口exit0（短路径恢复约16.107s）再run；真实10按键、8帧目视：nterm qzx→command not found→prompt，slides0/1/0、F1回PAL并继续绘制。hello40→169；53.478s后自有组SIGTERM，make-15不是guest正常退出 |

本次重开/三失败guest约1.017/0.415/0.666/1.067秒，正常连续PCM约4.825秒；环境使用SDL dummy，未听音。标准nanos不会单独证明其上层所有关闭重开组合，完整五层同步桥接与真实AM/MMIO/SDL线程分别界定，不互相冒充。

夹具/执行问题如实保留：初始较长隔离路径使BusyBox libs超过shell参数上限，迁移同一隔离树到`/tmp/crp-aud21-work`后原update成功，无下载/安装；首次nanos尝试与AM guest构建重叠，链接产物无sections而失败，后续顺序复跑成功，不能并发同一构建树。首次构建身份汇总仍按旧root取relative_to引发Python异常，全部编译已完成，仅补正确身份收尾；一次剩余风险探针未禁ccache而只读失败，补进程CCACHE_DISABLE后运行成功。原失败日志保留；这些不冒称guest失败或最终通过。CPU全集/RT/NPC REF/Linux未重跑：变动仅NEMU音频实现及该平台AM音频，NPC RT不编译此AM驱动；真实NEMU AM与受影响nanos已覆盖。

### 两源完整diff与身份

旧完整根commit、逐源SHA及新2026-10-21未提交工作树SHA见下方自动写入表；两文件mode100755保持。没有嵌套源修改，ONS既有编码diff保留。完整diff与实际工作树一致，正向应用得到新源，反向恢复旧源，local/implementation/archive-validation.json保存结果。

旧commit：`00c3b0487a53405fe31293c069420d90146041d5`。

| 路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `abstract-machine/am/src/platform/nemu/ioe/audio.c` | `429ba7c91a57c9bebc1648ed5e91a5a3200265da338dd6b9034c9ca5954466f0` | `dd3e2bb5e7846780dff39b8eba62eff044e44ef6dacfdd37f55b44648b84f96a` |
| `nemu/src/device/audio.c` | `bfded4a45cdc804146530e54b35a5ddd870856bd046cd85631478d8e0da9f567` | `d7ed4ae3987c80ef6860b9a505e2b1ed665de77ba3430a372d6d8a533ff3b272` |

```diff
diff --git a/abstract-machine/am/src/platform/nemu/ioe/audio.c b/abstract-machine/am/src/platform/nemu/ioe/audio.c
index 3bdc918c085216c6d85cf0484678842d299a3853..2aa9c20b539570948397181316f27059e1e47866 100755
--- a/abstract-machine/am/src/platform/nemu/ioe/audio.c
+++ b/abstract-machine/am/src/platform/nemu/ioe/audio.c
@@ -13,7 +13,8 @@ static uint32_t wr_index = 0;
 
 void __am_audio_init() {
   bufsize = inl(AUDIO_SBUF_SIZE_ADDR);
-  outl(AUDIO_INIT_ADDR,1);
+  // CTRL commits a complete configuration; do not open while it is being set.
+  outl(AUDIO_INIT_ADDR, 0);
 }
 
 void __am_audio_config(AM_AUDIO_CONFIG_T *cfg) {
@@ -25,6 +26,9 @@ void __am_audio_ctrl(AM_AUDIO_CTRL_T *ctrl) {
   outl(AUDIO_FREQ_ADDR, ctrl->freq);
   outl(AUDIO_CHANNELS_ADDR, ctrl->channels);
   outl(AUDIO_SAMPLES_ADDR, ctrl->samples);
+  wr_index = 0;
+  // INIT=2 reopens with an empty stream; legacy INIT=1 preserves its cursor.
+  outl(AUDIO_INIT_ADDR, 2);
 }
 
 void __am_audio_status(AM_AUDIO_STATUS_T *stat) {
diff --git a/nemu/src/device/audio.c b/nemu/src/device/audio.c
index c6afcc966a2c0fe2176cc54aabcaa0884c0849e4..221924ed25589777a44cc3ac7f483f42eed2a255 100755
--- a/nemu/src/device/audio.c
+++ b/nemu/src/device/audio.c
@@ -33,6 +33,7 @@ static uint32_t *audio_base = NULL;
 static bool audio_initialized = false;
 static bool audio_opened = false;
 static bool init_pending = false;
+static bool reset_pending = false;
 SDL_AudioSpec s = {};
 
 static uint32_t audio_freq() {
@@ -75,7 +76,7 @@ static void audio_disable() {
   audio_base[reg_count] = 0;
 }
 
-static void SDL_audio_init(){
+static void SDL_audio_init(bool reset_stream){
   SDL_AudioSpec s = {};
   s.freq = audio_freq();
   s.format = AUDIO_S16SYS;
@@ -84,7 +85,15 @@ static void SDL_audio_init(){
   s.callback = audio_play;
   s.userdata = NULL;
   //printf("%d %d %d\n",s.freq,s.channels,s.samples);
-  //count = 0;
+  if (audio_opened) {
+    SDL_CloseAudio();
+    audio_opened = false;
+  }
+  // CloseAudio has stopped the old callback before resetting the queue.
+  if (reset_stream) {
+    rd_index = 0;
+    audio_base[reg_count] = 0;
+  }
   if (!audio_initialized) {
     if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) {
       fprintf(stderr, "audio: SDL_InitSubSystem failed: %s; audio disabled\n", SDL_GetError());
@@ -93,10 +102,6 @@ static void SDL_audio_init(){
     }
     audio_initialized = true;
   }
-  if (audio_opened) {
-    SDL_CloseAudio();
-    audio_opened = false;
-  }
   if (SDL_OpenAudio(&s, NULL) != 0) {
     fprintf(stderr, "audio: SDL_OpenAudio failed: %s; audio disabled\n", SDL_GetError());
     audio_disable();
@@ -110,6 +115,7 @@ static void audio_io_handler(uint32_t offset, int len, bool is_write) {
   if (!is_write || len != sizeof(uint32_t)) return;
   if (offset == reg_init * sizeof(uint32_t)) {
     init_pending = audio_base[reg_init] != 0;
+    reset_pending = audio_base[reg_init] == 2;
   } else if (offset != reg_freq * sizeof(uint32_t) &&
              offset != reg_channels * sizeof(uint32_t) &&
              offset != reg_samples * sizeof(uint32_t)) {
@@ -119,7 +125,9 @@ static void audio_io_handler(uint32_t offset, int len, bool is_write) {
   // request waits for the configuration, then opens exactly once.
   if (init_pending && audio_freq() && audio_channels() && audio_samples()) {
     init_pending = false;
-    SDL_audio_init();
+    bool reset_stream = reset_pending;
+    reset_pending = false;
+    SDL_audio_init(reset_stream);
   }
 }
 
```

## 收尾、复现与当前停点

15必要生产输入中仅上述两源按patch变化，其余13源不变；八正式资产（原NEMU/配置、盘/header、nanos、RT二进制/配置/清单）及ONS既有编码diff均保持。隔离真实引擎SHA为`d4c164a4a1ba2a5870af44a7af8682cb0b8453b1c63fb1b230a19ae4da22ba80`，最终标准run与五guest同一引擎；正式默认引擎未覆盖。生产源/配置/产物身份与进程结束确认见implementation/final-identities.json。

验证/八帧实际目视/完整diff正反核验后，逐路径保存字节、SHA或symlink目标，清理9389文件/链接共360306085逻辑字节；0 tracked/正式资产删除。包含host对象/旧源副本、临时四工程生产副本及构建、guest BIN/ELF/PCM、截图/观察库，`/tmp/crp-aud21-work`和原迁移link均删除。保留报告、最小夹具/命令/退出码/日志/配置、SHA/patch/清理/目视回执；不再声称删除后的图片/引擎可直接查看或运行。

旧分析复现依据Git00c3b04及local/entry.json；新实现依据同一旧版加报告patch，配置为implementation/nemu.config，资源沿既有正式工作区，不下载/安装。为避免覆盖本轮证据，将最小local配方复制到records下新证据目录后，依次执行：

```sh
python3 "$H/implementation/run.py"
python3 "$H/implementation/prepare-runtime.py"
python3 "$H/implementation/build-real.py"
python3 "$H/implementation/run-real.py"
python3 "$H/implementation/standard-path/run-standard.py" nanos-final
```

prepare-runtime配方已改为直接创建短临时根，不需要重走已记录的长路径失败；build-real与标准run必须顺序执行，共用AM构建树不得并发。测试源码/配方/.config与本地原始证据继续忽略，不批量提交一次性测试；两生产源、报告/.gitignore及records必要索引是本批提交候选。WORKFLOW_POLICY/REPAIR/.agent为既有本地资产，Git提交不等于备份。

当前：F0118按批准契约Completed、结果确认/本轮commit Pending；F0043未修/用户批准延期，未来有明确音频并发需求再冻结跨层协议与真实并发验收。119=108已修+7CRP未修完+2能力移交+2无需实施闭合；剩余含F0029/F0073联合延期、F0030/F0054/F0055未决及F0040并发Partial。F0073分析已确认提交00c3b04，本轮修复未提交，index空，无运行中本组动作。唯一下一入口TASK_QUEUE#crp-next；本轮停止，等本批结果确认/提交，后续继续才做F0030/F0054内存回收契约必要分析，不自动修复/提交/push或推进M2。

会话建议：可在当前对话继续；本轮仅音频一组，结果/限制/复现和唯一入口已整理；后续按确认及提交门槛处理。

最终终检20项全部通过，142份本地保留证据manifest一致；包括逐源/八资产、原差异、归档、119行/108已修、空暂存、清理路径、下一门槛与报告链接。本轮新修复仍未提交，root HEAD`00c3b0487a53405fe31293c069420d90146041d5`，无push或下一组启动。


<a id="submit-20261021"></a>
## 用户确认与提交（2026-10-21）

用户“提交后继续”确认本批已报告结果及限制，授权本批两源/报告/索引七路径精确提交后执行F0030/F0054必要分析一个单元。提交前全部保留证据/15源/八正式资产/ONS原差异及两源完整patch核对保持，复用既有测试和清理，不重跑。实际身份/blob与工作树核对见local/implementation/submit-20261021及.agent回执；一次性测试和原始证据继续本地忽略，commit不等于备份，无push。会话建议：可在当前对话继续；本组已收尾，下一分析边界与恢复入口明确。
