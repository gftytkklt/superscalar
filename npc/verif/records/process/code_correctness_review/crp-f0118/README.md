# CRP F0118 — 音频后端失败与最小静音降级

现行结论见“最小静音最终结果”：用户已选报错后从AM阻止PCM写入、继续仿真；原A/B待决与分析零生产差异均是此前检查点。F0118仅此子范围完成，普通改配置重开不一致仍未修，整项Partial。

2026-10-20。用户“提交后继续”确认F0117并授权本单元；前组已实际提交b3b3b88。复用CRP整体计划/workflow和唯一队列入口，不推进M2/M3，不新立业务Phase。

## 当前单元计划与停点

1. 以当前源码核miniSDL→NDL→nanos→AM→NEMU返回/状态/初始化与close/reopen链，区分F0010/F0011已修行为与F0118未闭合问题。
2. 用实际NEMU/AM源码配同步MMIO/可控SDL后端，复现首次子系统失败、首次Open失败、显式init重开失败/重试、普通AM CTRL及当前上层重开，核旧/新配置、Pause、Close和ring状态/返回。用实际上层源码桥接可达路径；桥接不冒称真实OS/声卡或线程验收。必要时真实SDL dummy观察只佐证重开资源/参数，不能替代失败注入。
3. 若错误呈现/恢复/重开契约未决，保留最少充分证据、给出具体取舍及建议，等待用户裁决后才改生产代码，不自行新增MMIO/改AM接口或选全局终止/静音降级。F0043并发协议/新格式/性能不纳入。
4. 分析留档/身份/必要产物清理、更新records/当前状态/唯一入口；不把分析Completed记成F0118功能已修，不自动commit/push/下一组。无需软件安装。

## 现源结论与证据（必要分析完成，功能未修）

F0118整体仍Active / 待失败策略裁决，不增加已修计数。当前94已修均确认提交，25未修完含F0118/5CQ/F0040 Partial。F0117实际commit `b3b3b881010bb9b6956ebc5405cf053715c71371`，本单元无生产修改、无新commit/push。

旧P9文字“未检查SDL返回、失败仍Pause”已不适用于现源：F0010/F0011现已检查SDL_InitSubSystem/SDL_OpenAudio、打印错误、不在失败后Pause，并在显式重init前close旧后端。本轮不改写历史审阅原事实。余下问题是失败状态不上行、普通CTRL未重发init，以及旧PCM/配置生命周期。

| 当前生产端点 | 实际契约/根因 |
|---|---|
| nemu/src/device/audio.c:81–97 | InitSubSystem/Open失败打印并return；无法改变AM调用返回。显式重开先close旧设备，失败后audio_opened=false。 |
| 同文件:100–114 | init_pending只由完整init写设置，配置齐全时在尝试打开之前清零；失败后普通配置写不再尝试，须新的init。普通samples写不误重开是F0010已验收契约，不能再把samples写改成无条件重开。 |
| abstract-machine/am/src/platform/nemu/ioe/audio.c:14–27 | 全局初始化写init一次；后续AM_AUDIO_CTRL只顺序写freq/channels/samples，没有最后提交init，且CTRL为void WR。 |
| abstract-machine/am/include/amdev.h:23–26 | CONFIG只有present/bufsize，STATUS只有count，CTRL/PLAY无返回字段，没有约定后端失败状态。 |
| nanos-lite/src/device.c:105–125 | 状态只返回bufsize-count；控制/播放无条件返回len，无法表示后端打开失败。fs_close只使文件描述符失效，不发硬件停止请求。 |
| navy-apps/libs/libndl/NDL.c:107–131 | NDL_OpenAudio为void且忽略write返回，Close仅关两个fd；Play/Query按字节/空闲量工作，无后端失败协议。 |
| navy-apps/libs/libminiSDL/src/audio.c:48–71 | 已校验格式和输入参数；调用void NDL_OpenAudio后将audio_open=1、obtained=请求配置并返回0。Close已停止上层回调，但不等于关闭NEMU全局SDL设备。 |

### 实际同步桥接结果

本地`backend.c`直接include当前NEMU audio.c及AM audio.c，`device.c`整个生产文件独立编译；另独立编译生产NDL.c和miniSDL audio.c。NDL open/read/write/close仅在测试链接包装为到真实nanos音频处理函数的同步调用；AM分发表和MMIO访问由明确桥接实现，NEMU宿主SDL由可控失败桩替换（为避免与miniSDL同名，仅在NEMU测试TU重命名SDL符号）。没有复制/改写生产函数或只用返回值模型代替整链。

每例独立进程，普通与ASan/UBSan两构建的五例输出逐字节一致，共10实际运行/48断言；22构建/运行命令均exit0。这里PASS表示精确观察到现缺陷/正常对照，不表示F0118修好。43项分析身份/现象核对通过。

| 情景 | 本轮观察 |
|---|---|
| 正常首次打开 | 后端Open=1/Pause=1、实际44100，上层返回0；正常路径对照成立。 |
| 首次InitSubSystem失败 | Init=1/Open=0/Pause=0/未打开；上层仍ret0、obtained44100/free65536；写4B返回4/count4/free65532。解除故障后上层普通Close/Open仍不重新请求；显式init才成功，旧4B仍在。 |
| 首次SDL_OpenAudio失败 | Init=1/Open=1/Pause=0/未打开；同样ret0并接受4B。普通重试不再尝试Open；显式init后Open=2/Pause=1，旧count4保持。 |
| 上层关闭再改频率重开 | 首次44100成功、入队4B；Close只关两个fd，后端Close=0、仍打开/count4。再Open22050返回0/obtained22050，寄存器22050；实际后端仍44100，累计Open仍1。 |
| 显式init重开失败 | 新配置22050后显式init，Open=2/Close=1/Pause仍1，旧后端已关、新后端未开/count4；继续写4B成功，count8。 |

原日志：local/{normal,san}-{normal,init-fail,open-fail,reopen-no-init,explicit-reopen-fail}.log；results.json记录实际argv/返回，validation.json绑定源码和正式资产身份。首次夹具链接缺AM assert所需halt，补测试halt退出哨兵后完成；原失败日志initial-link-missing-halt.log保留，不改生产代码。LSan按已知ptrace环境限制关闭，不声称泄漏验收。

### 证明范围

本轮是当前五层实际函数的host同步桥接，替换了文件描述符/系统调用陷入、AM/MMIO传输和宿主SDL后端；未运行真实RV64 guest、真实声卡、SDL线程或标准nanos三前台。它足以复现返回/触发/状态转换；不能证明实际声音质量、耗尽卡死发生时长或F0043并发安全。无消费时最终写满后AM等待属于现源码推导，未用无限循环测试冒充动态结果。

没有生产修改，故本分析不重跑CPU-tests/RT/标准Navy update→run；选定修复策略后须新同版动态验收和受影响真实音频/消费者回归，不能用本分析代替。CONFIG_TARGET_AM/native.cpp独立宿主路径未动态验证；不将本轮桥接扩写为它们已修。

参考2026-10-20读取的[SDL2 SDL_OpenAudio](https://wiki.libsdl.org/SDL2/SDL_OpenAudio)：失败返回负值，一次只能有一个该入口打开的设备；现后端返回已检查，上层失败传播仍属本项目协议问题。[讲义输入输出/声卡](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)用于核IOE/寄存器与声卡抽象层次，不将其变成新增恢复接口授权。

## 待用户裁决的具体方案

两方案共同建议：AM以“写完整配置→显式init提交”启动/重开，保持NEMU不因普通samples更新而误重开；切换配置时先停旧后端，清空旧PCM并同步复位读/写游标，以免旧数据按新格式播放。NDL/SDL应用层Close继续是停应用回调/关闭fd，NEMU设备按当前全局生命周期持有；不把单个应用Close擅自变成跨进程全局声卡关闭。是否采用这一重开清空语义随本次方案一并确认。

| 方案 | 明确行为及范围 | 代价 |
|---|---|---|
| A：保留现接口，后端失败立即终止仿真（建议最小方案） | SDL子系统/设备打开失败以不受NDEBUG删除的诊断终止NEMU，不返回guest伪成功、不让其继续填满无消费者队列。正常首次/重开通过完整CTRL提交；MMIO寄存器和AM/NDL公开接口保持。与F0009已选的不可恢复设备错误策略同类，但仍需本项明确批准。 | 主机无可用音频时，本次仿真终止，应用没有捕获/重试机会；不能把它描述成可恢复失败传播。 |
| B：可恢复错误贯通到应用 | 建立可查询打开/失败状态，AM/OS/NDL提供可检查结果，miniSDL/Mixer打开失败返回-1并不发布虚假obtained/已开状态；定义重试及新旧引擎配对。保留原NDL入口可采用新增检查接口，具体接口布局需在此授权范围内设计/核对。 | 修改涉及设备协议及AM/NDL能力，范围更大，须对失败、重开、错误返回与兼容配对做跨层真实验收。 |

现无此项策略批准；不因“提交后继续”自动选择仿真终止或扩展接口。依据根AGENTS“人工确认/软件安装即停”及WORKFLOW_POLICY§3，停在真实失败契约/正常重开队列语义裁决。可选明确延期而不改变94已修/25未修完。获裁决后继续同一F0118单元，无需重立计划；本轮分析文档尚未提交不是人为增加的同单元实施门槛，最终单元仍需验收/用户确认与commit。

## 身份、复现、清理与恢复

当前旧/新生产源相同，无实际修复diff。八个端点SHA/五项正式资产SHA及HEAD见local/entry.json；报告不将无源码差异伪造为修复归档。

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0118/local/run.py
python3 npc/verif/records/process/code_correctness_review/crp-f0118/local/verify.py
```

配方从根b3b3b88对应版本读取真实生产文件，后续源有变化须先按entry恢复，不把未来新源结果冒充本轮。验证结束后12个探针/对象共911184B已清理，零tracked删除；源夹具/最小mock头/完整日志/配置身份与命令保留，不提交一次性测试。生成探针现在不能直接执行，按配方重建；ignored/.agent不随commit备份。

当前只保留本单元报告/.gitignore及索引等文档候选；F0117确认提交回执已保存在其local/approved。唯一下一动作TASK_QUEUE#crp-next：等待本项A/B或延期裁决；无新commit/push/安装/M2推进。

会话建议：可在当前对话继续；F0118证据规模有限、决策边界明确，现源/未修/前组提交状态已保存。

最终终检22项通过，37份保留证据manifest固定；生产零diff/八源与五正式资产身份/12路径预期清理/119行计数94已修25未修完一致。复用43分析检查，不新增动态运行或功能完成宣称。

## 用户最新裁决与最小静音实施计划（2026-10-20）

来源：用户要求“简单输出错误信息，不播放音频”“如果没有[纠错措施]，采取最小改动，让错误可见即可”，继而明确“不播放音频应该是从不写入开始的”。本选择替代上方待决A/B，不终止仿真，不扩可恢复错误API。

现重试仅再次SDL_InitSubSystem/SDL_OpenAudio：子系统初始化成功后不重复初始化；显式重开先关闭旧设备。没有参数修复、驱动/环境纠错、自动fallback或自动重试策略。外部条件变化可能使以后显式请求成功，不承诺重试能纠错。

1. 仅NEMU audio.c与AM NEMU audio.c：后端失败保留SDL错误诊断并注明音频已禁用；现INIT寄存器置0，丢弃旧排队量并将消费游标推进到生产端已提交位置；AM每次准备写ring前检查INIT=0直接返回，不先写后丢。保持正常init请求/成功值1、不增加MMIO寄存器/AM/NDL公开接口，无自动重试。
2. 现有INIT值0代表未请求/取消，扩充为失败后禁用；1仍可能是延迟请求或成功，不能作为通用ready标志。新AM使用0保护，仅新旧配对的本轮失败路径保证不写；原始MMIO或旧AM绕过此检查不冒称已受保护。正常已有CTRL/Close语义不扩大，普通改配置重开不一致保留未修，F0118不冒称全部闭合。
3. 复用五层桥接，原版反例与最终普通/ASan+UBSan验证首次失败、重开失败、无ring写/COUNT保持0/超容量不阻塞、诊断/无Pause、以后显式成功与游标/旧PCM边界、正常路径保持。
4. 隔离当前NEMU/AM构建，真实RV64音频guest用SDL故障注入并核实际MMIO写计数0/正常返回、可用后端PCM实际消费和欠载静音；受影响标准nanos update→run/三前台与后台hello，正式资产保持。完整两源diff内嵌/正反归档、身份/清理、records/.agent收尾后停，不commit/push/下一组。无需安装。

<a id="mute-final-20261020"></a>
## 最小静音最终结果（2026-10-20）

用户限定的失败可见/写入前静音子范围 **Completed，结果确认/commit Pending**；F0118整项 **Partial**，普通CTRL改配置重开仍未修（上方分析/本轮reopen-no-init对照仍明确复现）。累计94完全已修/25未修完不变，不将软静音或上层ret0变成可恢复错误传播通过。没有选择原A终止仿真或B新增公开错误接口。

### 实现与重试答复

本地2生产源16增3删：

- NEMU两处已有失败诊断保留`SDL_GetError()`，追加`audio disabled`，均不Pause失败设备；调用`audio_disable()`把已有INIT置0。AM每个分片写ring之前读取INIT，0则直接return；容量等待期间也检查0返回，阻止新PCM写入而非写完再丢。
- `audio_disable()`清COUNT前用`rd_index = (rd_index + queued_count) % sbuf_size`推进到已提交PCM末端，随后COUNT=0。它仅丢弃失败前的待播队列，不写sbuf本体；保留AM原wr_index，使以后显式成功后消费游标对齐，避免播放失败前残留PCM。失败前已有后端时，原`SDL_CloseAudio()`已同步停旧回调，随后失败路径才改队列状态；并未解决正常播放COUNT的F0043异步竞争。
- INIT=0原有“未请求/取消”扩充为“失败后禁用”；INIT=1仍可能是延迟请求或打开成功，不能解释为普遍ready。没有增加寄存器、改COUNT单位/绝对值语义，或新增AM/NDL公共API；本轮新AM读取0保护，与新NEMU配对验收。旧AM/直接MMIO调用者若绕过检查，不保证静音不写或不等待。
- 失败之后仍有空闲容量不等于应该把数据写进ring；现Navy上层可以继续运行/生成音频，但AM不进行PCM传输，COUNT保持0。上层Open/Play沿现接口可能返回成功，这是用户选择的可见静音降级，不称为应用收到错误。空缓冲在已打开后端产生静音；打开失败本身没有该设备的播放回调。

**重试没有自动纠错措施。** 当前只会在显式INIT请求时再次调用SDL；子系统未初始化成功则重做InitSubSystem，已成功则只尝试OpenAudio。不会修改配置、修复驱动、自动切换后端或循环重试；宿主外部条件后来变化时可能成功，仍不承诺重试必然有用。普通AM CTRL目前不重发init，这一既有重开问题本轮明确不扩大修复。

### 本次实现验收（local/implementation）

| 验证 | 实际结果及范围 |
|---|---|
| Git旧源对照 | b3b3b88两旧源配同一新契约夹具，首次Init失败/Open失败/显式重开失败三例均精确拒绝；不执行旧版超容量忙等来制造假完成。旧五层实际可写4B反例仍在local分析记录。 |
| 最终host五层实际链 | 普通/ASan+UBSan五例各52断言，共10运行104断言；首次Init/Open失败、显式重开失败后INIT0/COUNT0、原有写字节计数不增加，连续3次65537B提交不阻塞。显式成功后fresh4B实际生产回调读出一致、其余静音；正常写/欠载及保留普通重开缺陷的对照保持。31条实际构建/运行命令包括3次预期旧失败。 |
| 真实RV64三种故障 | 新隔离当前NEMU+AM，实际AM guest与MMIO，SDL初始化/第1次Open/第2次Open受控失败；三次65537B共196611B API提交均返回、COUNT0，逐字节65536B ring前后相同（数据模式可区分）；三guest均GOOD TRAP/exit0，各一次明确audio disabled。后两例显式重试由注入转真实SDL dummy，fresh512B完整消费且回调余部全0。 |
| 真实正常PCM/欠载 | 同一新引擎/AM、真实SDL dummy，65537B测试模式样本连续完整出现在69632B捕获流，前后其余字节全0，guest约4.824s/GOOD；实际callback线程不同于guest线程，不是听音或F0043并发安全证明。 |
| 标准Navy update→run | 当前隔离源码/已有资源，nanos目录标准update exit0约25.781s→run；三前台/实际10按键、nterm qzx返回prompt、slides0/1/0及PAL恢复/Enter，hello40→179，8帧已目视。约53.480s后自有进程组SIGTERM，make -15非正常guest退出。原正式引擎/盘/配置不替换。 |

真实失败运行时长：Init失败0.415s、Open失败后显式成功0.766s、重开失败后显式成功1.167s；此为故障注入的实际短时执行，不是假定主机必然自然出现失败。成功重试仅说明在后端条件允许时状态/游标可正常恢复，不表示SDL有纠错算法。

初次真实guest构建缺私有ISA include，补测试INC_PATH；随后AM klib不提供puts，改测试为printf，均不改生产构建入口，失败日志保留。host旧例exit1是预期拒绝；LSan因环境ptrace限制关闭，ASan/UBSan实际运行。

### 完整两源diff与身份

根仓ysyx-workbench；旧完整Git `b3b3b881010bb9b6956ebc5405cf053715c71371`，新为2026-10-20未提交工作树，原mode100755保持。

- `nemu/src/device/audio.c`：旧SHA256 `65048c00750517d9e94d8a209b880d55468744d818147ae09e28f333d45eebae`，新SHA256 `bfded4a45cdc804146530e54b35a5ddd870856bd046cd85631478d8e0da9f567`。
- `abstract-machine/am/src/platform/nemu/ioe/audio.c`：旧SHA256 `13b37fd714a08ebbc5b443d85e9102877026174e61df0214072ce7ccc8cdeafd`，新SHA256 `429ba7c91a57c9bebc1648ed5e91a5a3200265da338dd6b9034c9ca5954466f0`。

```diff
diff --git a/abstract-machine/am/src/platform/nemu/ioe/audio.c b/abstract-machine/am/src/platform/nemu/ioe/audio.c
index 597d3e3555a5ea91af35573245bcb3dd543baffb..3bdc918c085216c6d85cf0484678842d299a3853 100755
--- a/abstract-machine/am/src/platform/nemu/ioe/audio.c
+++ b/abstract-machine/am/src/platform/nemu/ioe/audio.c
@@ -41,8 +41,12 @@ void __am_audio_play(AM_AUDIO_PLAY_T *ctl) {
   assert(bufsize != 0);
   const uint8_t *play_buf = ctl->buf.start;
   while (remaining != 0) {
+    // A failed backend clears INIT: remain silent without writing the ring.
+    if (inl(AUDIO_INIT_ADDR) == 0) return;
     uint32_t len = remaining < bufsize ? remaining : bufsize;
-    while (bufsize - inl(AUDIO_COUNT_ADDR) < len);
+    while (bufsize - inl(AUDIO_COUNT_ADDR) < len) {
+      if (inl(AUDIO_INIT_ADDR) == 0) return;
+    }
     for (uint32_t i = 0; i < len; i++) {
       if (wr_index >= bufsize) wr_index -= bufsize;
       outb(AUDIO_SBUF_ADDR + wr_index, play_buf[i]);
diff --git a/nemu/src/device/audio.c b/nemu/src/device/audio.c
index 55f9dc268fa52253201ed9d993b5b95590ca7bf8..c6afcc966a2c0fe2176cc54aabcaa0884c0849e4 100755
--- a/nemu/src/device/audio.c
+++ b/nemu/src/device/audio.c
@@ -68,6 +68,13 @@ static void audio_play(void *userdata, uint8_t *stream, int len){
   }
 }
 
+static void audio_disable() {
+  audio_base[reg_init] = 0;
+  // Discard queued PCM while preserving alignment with the AM write cursor.
+  rd_index = (rd_index + audio_base[reg_count]) % audio_base[reg_sbuf_size];
+  audio_base[reg_count] = 0;
+}
+
 static void SDL_audio_init(){
   SDL_AudioSpec s = {};
   s.freq = audio_freq();
@@ -80,7 +87,8 @@ static void SDL_audio_init(){
   //count = 0;
   if (!audio_initialized) {
     if (SDL_InitSubSystem(SDL_INIT_AUDIO) != 0) {
-      fprintf(stderr, "audio: SDL_InitSubSystem failed: %s\n", SDL_GetError());
+      fprintf(stderr, "audio: SDL_InitSubSystem failed: %s; audio disabled\n", SDL_GetError());
+      audio_disable();
       return;
     }
     audio_initialized = true;
@@ -90,7 +98,8 @@ static void SDL_audio_init(){
     audio_opened = false;
   }
   if (SDL_OpenAudio(&s, NULL) != 0) {
-    fprintf(stderr, "audio: SDL_OpenAudio failed: %s\n", SDL_GetError());
+    fprintf(stderr, "audio: SDL_OpenAudio failed: %s; audio disabled\n", SDL_GetError());
+    audio_disable();
     return;
   }
   audio_opened = true;
```

内嵌diff与两生产源完整差异一致，正向从注明旧版应用逐字节等于新源、反向恢复旧源，archive-validation.json已记录。并非只链接patch替代框架修复说明。

当时实际新NEMU SHA256 `0cc526d69cf3b8eba5dd7bf46a8b05c62fabafdb58ca689b75fc01894b722a18`；两生产源隔离复制/AM归档对象/guest ELF与BIN/观察库身份见implementation最终identity/real-identities。观察库只在宿主替换选定SDL失败返回，正常打开转给真实SDL并捕获生产回调输出，不修改音频消费函数。

### 限制、复现和停点

- 未改普通改配置CTRL重开、应用Close到NEMU全局设备、native.cpp或TARGET_AM独立路径；F0118整项Partial，相关未修不隐藏。
- 无应用错误返回/自动恢复；旧AM或裸MMIO绕过INIT检查不在本轮配对保证内。未声称实体声卡/听音、其他ISA、长期或F0043并发通过。
- 本次不改CPU/RT/REF执行语义，未无故重跑其全量回归；Navy源码未改，标准update/run用于新AM/后端消费者同版验收。

复现时从注明Git版本加本报告patch恢复两源，保留当前既有资源/配置，设`H=npc/verif/records/process/code_correctness_review/crp-f0118/local/implementation`：

```sh
python3 "$H/run.py"
python3 "$H/prepare-runtime.py"
python3 "$H/build-real.py"
python3 "$H/run-real.py"
python3 "$H/standard-path/run-standard.py" nanos
```

后续源码变化应按entry/最终身份恢复；原local/{run,verify}.py是分析配方，不可在已修源上重跑后仍冒称原缺陷观察。正式资产保护、最终验证及清理回执见implementation；只提交必要两生产源、报告/.gitignore及records索引，单次测试/原始日志本地忽略。不自动commit/push/下一组/M2，等待本子范围结果确认和提交。

## 收尾State Consistency Conflict检查点（待来源确认）

当前用户授权为本轮最小错误可见/写入前静音，没有声明修改默认产物。旧entry（沿分析开始时基线）记录默认NEMU bcef3bb3…/nanos e3ebd58f…，本次收尾观察默认NEMU c64535dc…/nanos 40bdba39…，mtime均为2026-10-20 20:45:10–11 +08:00；已知隔离make日志均指向implementation/standard-path/work，没有证据说明此次默认变化来源。根源码只有本轮两源预期diff，配置/正式盘仍同基线。

冲突位置为正式默认二进制保护身份，非本轮实际隔离新引擎/guest验收身份；后者已核对一致。state-conflict.json保存完整哈希/mtime/来源Unknown。没有覆盖/恢复默认文件，当前无运行中make/NEMU。已向用户询问是否同时在原工程构建；获来源确认前暂停正式Completion/确认转换，不能把“正式产物均未变”记为PASS。其余独立验证与留档继续，不把此冲突当作新代码测试失败。

### Guard冲突解除（用户确认来源）

用户对“本轮是否在原工程make run/构建更新默认NEMU和nanos内核”明确回答“是，保留我生成的产物”。因此原entry与默认产物的差异有Session解释：两项用户产物保留不覆盖；完整现哈希与来源见implementation/user-assets-receipt.json，原entry/state-conflict.json不改写。配置/盘仍原值，实际隔离验收身份保持；复用既有动态测试，只续作未完成的身份核对/归档/清理。该答复仅确认资产来源/保留，不推定本批实现结果已获确认或已授权commit。

## 本子范围收尾与剩余工作

193项preclean全部通过（含身份/盘extent/归档等，非193个功能情景），5978项源码/产物身份已固定。验收/8帧目视/完整diff正反和来源澄清完成后，清理9370文件/链接共360267188逻辑字节，0 tracked/默认产物删除；保留必要配方/日志/配置/身份/patch。两用户默认新产物明确保留，旧基线不改写；现在只凭哈希识别已删除隔离模型/镜像/PCM/截图，需按配方重建，不宣称仍可直接执行。

用户所选失败可见/AM写入前静音子范围Completed，结果确认/commit Pending；Working tree contains uncommitted F0118 partial repair/documentation changes，root HEADb3b3b88/index空，无本组运行中动作。F0118整项Partial：普通改配置重开不一致保留，应用错误返回按本轮明确策略不实现；累计94完全已修/25未修完（含F0040及F0118 Partial、5CQ）。未来只沿TASK_QUEUE唯一入口，本轮停止不自动commit/push/下一组/M2。

会话建议：建议开启新对话；本对话已累积NDL与音频多轮修订、构建及外部产物澄清，下一独立单元转SD卡寄存器方向，恢复入口完整。建议不增加执行门槛。

最终终检19项全部通过，92份保留证据manifest固定；完整两源diff/最终SHA/用户两默认产物保留/9370路径预期清理/94与25计数/唯一Next一致。无新增动态测试或commit；本子范围Completed、整项Partial，结果确认/commit Pending。

## 用户确认与提交收尾（2026-10-20）

用户“提交后继续”，先询问SD与disk区别，再明确“继续实现”及16 GiB不预占空间，确认本批已报告的最小静音子范围并授权精确提交、随后进入F0020。F0118整项仍Partial，94完全已修/25未修完不变。提交前92份保留证据身份及两源完整full-index patch无漂移，复用既有19项终检及动态验收，不重复运行。仅纳入两生产源、本报告/.gitignore及两records索引；实际commit回执保存在本地implementation/submit-receipt.json及.agent，不push。可在当前对话继续：本对话已恢复且SD下一范围明确；ignored证据不由commit备份。
