# CRP F0066/F0067 — 事件及音频状态读取边界（2026-10-20）

## 整体计划、协议核对与停点

用户“提交，继续”授权前组提交后执行唯一下一组。前组实际
`5941586720da24f51af299274f0220e23c2206a0`，6文件132增10删，暂存/实际blob一致，
Start前root/index干净；前49项已确认提交。复用CRP流程/既有计划，M2不推进。

现有events_read每次轮询一个AM键，返回kd/ku文本，不保存剩余字节；NDL_PollEvent
转为布尔，SDL和libam使用128字节缓冲找换行。沿用这个无缓存轮询边界，对非零
短读仅交付前缀，不新建事件队列/余字节重放；len0不读取设备。完整文本有额外空间
时保留原NUL兼容，但返回字节数不含NUL。F键前台控制仍消费相应keydown。
sbctl由NDL_QueryAudio提供sizeof(int)空间，状态是空闲字节数，不是PCM数据；
短读复制原整数的前min(len,4)字节，完整调用仍4字节，即使free=0也返回4字节0。
这是已有消息格式的有界复制，不引入新缓存/音频提交/errno协议；新能力需求另裁决。

1. F0066只修device.c的len边界、可选NUL、合法keyname验证；正常kd/ku/F键行为保持。
2. F0067只修状态复制长度和未对齐写入；保留原空闲量计算、现4字节消费者及音频时序。
3. 原版事件/音频短缓冲和len0/非对齐见证；实际生产函数host sanitizer检查len0/1/
   恰消息长/额外NUL空间、最长键名/无键/坏键/F键、audio len0～5/非对齐/free边界，
   返回值、全部哨兵和设备调用数。真实RV64用户设备read及正常消费者/默认三前台/
   hello/音频路径，旧/新对照；不能仅以host或无GUI替代真实guest。
4. 保存命令/退出码、源码/输入/配置/构建身份、最小测试源/patch；验证/目视后清理
   本组可再生产物，更新records/台账/.agent及唯一未来入口，完整交付后停止。

不安装、不改Make/日常入口，不提交新组/push或自动进入再下一组。新结果确认与
commit分开；原测试/清理复用，不重复旧Phase Completion。计划落档时Active，现已Completed，新结果确认/commit Pending。

## 实施与逐项验证

**F0066/F0067均Completed，新结果确认/commit Pending。** 生产仅device.c，16增12删。
事件按现有三部分kd/ku前缀、键名、换行逐字节限量复制；len0提前返回，先验证键码
范围及非NULL键名，正常前台F键控制保持。完整事件且有余量时写兼容NUL，NUL不计
返回长度；短读无余字节缓存，下一次仍轮询新事件，不承诺lossless字节流/事件重放。
音频状态用memcpy复制min(len,sizeof(int))，返回实际字节，消除未对齐int存储。
移除把音频空闲量误作“状态回复长度”的无效len计算：free=0仍是可正常读取的四字节0，
不改变正常NDL_QueryAudio数据、音频提交/回调或时钟行为。

| 验证 | 本轮结果 / local证据 |
|---|---|
| 原实现四反例 | Git5941586 device.c：事件len1与音频len1均ASan越界/exit-6；音频len0写入/返回4被断言拒绝exit-6；未对齐buf的int存储被UBSan拒绝exit1。unit-results.json/before日志 |
| host最终组合 | 普通与FG两编译分支各135场景，共270，ASan/UBSan通过；含A/最长RIGHTBRACKET/F1-3的kd/ku与len0/1/恰消息长/多一字节/128、无/负/超界/NULL键名、len0不轮询且保留待键、非零短读后不重放后缀；音频5种count×7种len×2种对齐、free0/1/63/64及超容量count钳零。分别21647/21734断言，多为逐字节哨兵，不冒作这些数量的独立场景。actual AM键表/设备类型，ioe_read/write为stub；LSan关闭不宣称通过 |
| 真实原实现 | 两个原内核+相同类型用户payload，事件A通过SDL真实队列注入后len0读在step002失败；音频len0读同样step002失败。均DEVICE-GUEST FAIL+BAD TRAP/exit1，不把启动/夹具失败当作漏洞见证。runs.json、before-event/audio-run.log |
| 真实新组合 | freestanding RV64用户ecall→FS→真实AM/MMIO：零长不写buf，A的len1前缀后紧接ku A完整事件，B的恰5字节消息不写NUL/有余量时保留NUL、空轮询不写；音频len0～5及两种对齐、原65536空闲整数前缀均正确。实际打开音频22050Hz/双声道/256 samples并写512B PCM，再按4字节查询处于有效范围；DEVICE-GUEST PASS+GOOD TRAP/exit0。SDL两个输入对均down=1/up=1；guest/日志/observe结果保留 |
| 构建/纯生产 | 两小型payload和四内核（旧event/旧audio/新guest/新FG）实际构建通过；原NEMU执行器身份保持，无CPU观察改动。新FG内核1亿指令后q/exit0、hello11条，不带诊断的生产实现运行。builds/fixtures/runs.json |
| 默认消费者 | 52.88秒8观察点，PAL场景/标题；nterm输入qzx的command not found和新提示符；nslider 0→1→0且返回像素SHA相同；F1/Enter后PAL有场景；后台hello38→169。contact已目视，返回PAL保留前一窗口蓝边这一既有观察不隐去；自有组SIGTERM/实际exit0，非guest正常完成或全屏重绘/物理音视频通过。nanos/result/visual-qa.json |
| 同版核对 | 24项preclean检查与174份consumer源码/header身份保留；新/旧device源与相应Git/当前源一致，原盘/默认内核/native/config、fs/loader/proc及NDL/SDL源码保持，两临时盘全SHA未变，ELF与实际追加extent完全相符 |

夹具开发中host shim补齐了原AM IO宏及其局部变量命名，未改生产IO接口；最初
freestanding链接缺编译器为512字节初始化生成的memset，补了最小自包含helper后
通过，不安装或引入库。initial-builds/guest日志保留，未算成功构建；最终用例与
原始见证均使用修正后的同一夹具。测试脚本/临时头只local，不随修复提交。

背景参考：[ICS-PA输入输出](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)，2026-10-20
读取其AM键盘/音频设备背景；sfs消息协议与短读边界以本项目已有device.c、NDL/
SDL/libam实际接口及本组计划为准，不从讲义推定新增事件队列或音频并发保证。

## 影响、限制与再生

本组影响nanos事件及状态读，已做真实用户read、默认NDL/SDL消费端交互和正常
PCM/status路径。NDL/SDL/libam的正常调用使用128B事件缓冲及4B状态；未改其源码、
未逐次计数PAL所有音频查询，未声明音乐/物理声音质量。CPU-tests/RT/REF接口/NPC
RTL不消费nanos该函数，未重跑；未测NPC nanos、所有应用/配置、长期、实体输入/
输出。F0043并发提交、F0068 framebuffer、SDL其他独立问题保持，不从本组推定
完整设备协议或全部GUI无缺陷。非零短事件读取沿用单次轮询、后缀不重放；需要完整
事件的调用者仍须提供足够空间，len0不会消费输入。

累计51已修/68未修完，前49项已确认提交，本组两项待用户确认/commit。统一留档
后停止；未来F0068 framebuffer边界仅TASK_QUEUE#crp-next维护范围/必读/验收/门槛，
不自动提交/push/下一组/M2/M3。无新架构决策，不重复旧完成快照。

local保留unit.py、guest.c/start.S（含最小memset）、prepare/run.py、SDL观察/input
脚本、源/配置/ELF/输入身份、实际argv/exit/结果和repair.patch。从Git5941586取得源
并应用repair.patch，在新的空local目录依次运行unit.py/prepare.py/run.py及
`python3 nanos-run.local nanos`，使用entry-identity所列原Navy盘及表/原native身份；
不覆盖旧结果，不更新真实盘或新增日常步骤。Make使用git_commit=避免自动提交。
已目视并保存文字结果后，按本组清理回执删除镜像/ELF/截图/编译/生产源副本；旧
identity产物预期缺失合并cleanup回执解释。ignored/.agent不由普通commit备份。


实际清理完成：390文件315392054逻辑字节（约300.8MiB），零tracked删除/零剩余产物。cleanup-plan/receipt保留路径/类别/删除前SHA及实际结果；原盘、默认构建及文字证据保持。


<a id="audio-review-20261020"></a>
## 当前99:1音频卡顿补查计划（2026-10-20，Reopened）

用户要求同时关注三前台+hello、99前台/1hello下音频卡顿；若证实为当前程序执行预算导致PCM欠填充而非音频库实现问题，则不考虑修复。原F0066/F0067完成快照与验证保留，下一F0068未Start，本轮重新打开本组消费者音频验收，补查不预先修改生产音频行为。当前HEAD5941586，device.c原16增12删未提交；原结果确认/commit仍Pending。

本补充为一个诊断单元：核对当前guest/盘/PAL ELF/调度/音频全链身份，在隔离副本重建当前nanos，复用既有宿主SDL和guest PC探针；测量PAL启动画面的PCM包长、生成回调时间/指令数、调用间隙、写入及宿主消费/欠填充，检查COUNT守恒和轮询触发限制。有区分力时使用只在诊断副本的对照（去填音计算、取消补音间隔限制等），明确其改变的行为及探针开销，不能作为生产修复。先dummy后真实可用音频后端，串行运行；旧50:50证据只作历史参考。若需安装/系统改动或真实契约裁决即停，已知旧流畅版本身份可由用户补充但不阻塞当前测量。

交付为本节补充结果及local/audio-review-20261020的脚本、配置、命令/退出码/日志/统计/源码与输入哈希、结论限制；验收要求实际当前99:1三前台+hello有效运行，量化供需并分别讨论程序计算、miniSDL轮询、NDL/AM/设备和未识别历史基线。无法排除的实现问题如实保留，不由“有欠填充”倒推库无错。测量结束清理本组可再生产物，更新索引和补充Completion/唯一入口后停止，不提交、不进入F0068或M2。原两项修复计数51/68不变。


### 诊断范围补充（用户本轮反馈）

用户回忆旧流畅版同样为三前台，但可能尚未实现disk等外设且分辨率400×300（现在800×600中间PAL小窗）；旧commit/镜像仍Unknown，只做单独分辨率对照，不冒作旧版全复现。随后用户明确收敛验收：“搞清楚音频填充的时机……如果能证明高程序负载下会降低音频填充的频率，那就足够说明问题了”。本轮据此以实际轮询/填音/绘图时间及仅减轻绘图负载的诊断对照为主；不要求人为恢复旧版听感或扩展音频修复。源码中实际触发为miniSDL的GetTicks/PollEvent/WaitEvent/Delay调用CallbackHelper，yield/schedule不直接调用该用户回调。dummy可用于供需和触发频率证明，不能冒作物理听音结果。

### 补充检查结果与结束（2026-10-20）

**本补查Completed，按用户收敛后的验收已证明：当前程序的长绘图负载降低补音轮询/填充频率，足以造成持续欠填充。本轮不修复这种执行预算问题，没有新增生产代码修改。** 原F0066/F0067功能修复仍为device.c16增12删，结果确认/commit Pending；未进入F0068，累计51/68不变。历史功能快照/manifest保持，下面为独立补充证据，不将原“未测音乐”历史重写成已测听感。

触发链核对：PAL的SDL_GetTicks/SDL_PollEvent/SDL_WaitEvent/SDL_Delay调用miniSDL CallbackHelper；它在未暂停、非回调重入且距audio_last达到 `samples*1000/freq` 时，查询空闲量并调用PAL AUDIO_FillBuffer，随后NDL_PlayAudio→nanos→AM→NEMU sb。yield/时钟中断只改变调度，不直接进入用户音频回调；当前FG模式也没有MULTIPROGRAM_YIELD的设备主动yield。这里不是按每次yield固定补一包。单次Helper最多生成一包，无独立音频线程或逾期包补跑；长计算/绘图期间不执行这些服务点，补音就会推迟。

当前输入：从未提交device.c及HEAD5941586的当前nanos/AM隔离重建；FG_PROCESS、HAS_VME、proc.c的99:1保持，四个实际ELF均与临时磁盘extent逐字节对应，四个加载entry与ELF e_entry按proc顺序一致，hello均继续。PAL ELF、原盘、默认内核/根NEMU及.config保持，48项源/输入身份全部无漂移。PAL参数11025 Hz、双声道、S16、1024 samples，单包4096 B；消费44100 B/s，即每92.8798 ms至少一包（约10.7666包/s）。每个测量只成功Open一次、Close零次，无反复初始化。

四次串行SDL dummy运行各26秒（首例28秒），分析各自探针相对时间4～24秒，排除启动段；不同日志的epoch不混用。全部自有组到时SIGTERM、实际exit0，非guest正常完成。没有本轮实体音频/人工听音或真实窗口验收；用户已将本补查验收收敛为负载与填音频率，未再扩展PulseAudio/历史全版本重建。

| 诊断场景 | PCM提交平均间隔 / 频率 | PAL生成回调平均耗时 | 稳定段欠填充回调 |
|---|---|---|---|
| 当前800×600，仅音频/轮询PC观察 | 182.07 ms / 5.49包/s | 46.94 ms | 107/217，缺供给49.31% |
| 仅分辨率改400×300，其余保持 | 190.58 ms / 5.25包/s | 49.36 ms | 112/217，缺供给51.61% |
| 当前800×600，增加绘图PC观察 | 200.63 ms / 4.98包/s | 51.24 ms | 117/217，缺供给53.92% |
| **同上引擎/guest/盘，仅诊断跳过SDL_UpdateRect** | **92.03 ms / 10.87包/s** | **52.44 ms** | **0/217，缺供给0%** |

绘图观察：当前SDL_UpdateRect单次平均70.81 ms、约150万条guest指令；99个超音频预算的轮询间隙内，平均有141.44 ms落在绘图调用内（常见连续两次），而填音回调约90万条指令/51 ms。跳过绘图对照仍执行原PAL音频生成，指令数约90万、耗时52.44 ms，与正常例相近；未跳过/替换/静音填音回调，未改92ms间隔检查、音频格式、PCM长度、NDL/AM/COUNT或调度。仅由诊断CPU hook在已核对的PAL SDL_UpdateRect入口模拟立即ret；所有guest和盘字节一致，画面故意缺失，不能作为修复交付或正常图形通过。对照的最长补音检查间隙76.28 ms，正常例最长165.85 ms；恢复供给直接支持长绘图阻塞服务点这一原因。

探针有开销：增加每指令绘图入口/返回地址检查后，正常填音周期从182 ms增到201 ms，不能把不同探针的绝对差解释成生产退化。关键200.63→92.03 ms对照使用完全相同引擎/guest及探针，差异仅CRP_VIDEO_SKIP；无需依赖探针无开销假设。高频空轮询也会写日志，短时结果不能推广到全部场景/长时保证。

NDL/AM写入往返平均约1.24～1.60 ms；四例每次完整提交均4096 B，COUNT写前后增量均4096，拷贝总字节减实际消费等于最后观测count；正常例每包状态/容量/提交读各一次，无容量忙等积压。**本次未观察到计数丢失来解释欠填充，但不等于修复或证明F0043并发协议。** 正常例持续缺包已有足够供需证据，不从中推出全部音频库实现无错。主观卡顿、其他SDL问题/所有后端仍未完整排除。

旧版本线索：400×300单因素对照仍约5.25包/s，不能恢复旧流畅表现；当前PAL绘制面积仍320×200，并未因宿主分辨率减少到四分之一。旧版外设、guest代码、构建、配置及commit未识别，不能把此次结果写成历史版本因果比较，也不据此认定disk是根因。按用户“证明高负载降低填音频率即可”的明确要求，到此结束诊断，不继续寻求无证据的旧版还原或性能修复。

证据/复现：`local/audio-review-20261020/{prepare.py,device-probe.h,guest-probe-initial.h,guest-probe.h,add-video-probe.py,host-probe.c,measure.py,analyze.py,verify-clean.py}`，同目录entry/app/fixture身份、两份.config/generated config、PAL反汇编、各build日志和四目录原始host/device/app/guest日志、process/result、analysis/validation/checker-corrections/run-controls及cleanup回执。新空目录从当前Git+原repair.patch重建，先prepare（guest-probe使用initial版本），运行前两例，再恢复最终guest-probe并运行add-video-probe及后两例；完整argv/env和诊断差异见run-controls。Make均禁教学自动commit，未安装或改系统/日常入口。

收尾13项检查全部通过，3个判据负例（零回调/四ELF不匹配/零hello）均拒绝。早期runner按路径文字查加载结果为False（实际日志只打印entry）、analyzer误用盘表顺序的失败均留纠正说明，最终对四个实际ELF entry逐一验证，不修改原始日志。已结束全部本组进程，删除本补查819份可再生文件153775247逻辑字节（约146.7MiB），零tracked删除/零剩余编译或镜像资产；原功能组390份清理回执保留不重复计算。本节新增使原manifest中的README身份预期变化，其余原61项中60项仍一致，补充manifest记录最新报告及新增证据，不覆写旧manifest/validation。

### 关于及时补音与sb容量的后续问答（建议，未实施）

用户询问“通过及时触发保证供给的方法，以及提高回调频率是否使sb溢出”。建议优先将长绘图切成有界小段，在段间执行用户态音频服务；提高**检查**频率，以队列余量/目标水位决定是否生成一整帧对齐的PCM包，可在不足目标时补多包。水位覆盖最长不可服务时间与生成耗时并留余量，同时带来音频延迟；不能只把固定92ms间隔缩小、无条件多生成。平均生成能力若长期低于消费，任何有限缓冲仍会耗尽；增加音频服务也会占CPU，可能降低绘图吞吐。这属于新策略/性能取舍，用户本轮只问方法，未实施。

现有Helper已用 `min(期望包长, NDL_QueryAudio空闲字节)` 限制本次生成量，AM也有容量等待；因此增加检查/回调机会本身不必导致sb越界，满时应停止生成/等待消费。严格容量保证仍要求正确的生产消费计数、帧对齐及并发协议，F0043的绝对COUNT读改写竞争未解，不能承诺所有并发情况下都不丢/重数据。不要直接在内核yield/时钟中断上下文运行PAL的用户回调：它涉及用户地址空间、malloc/库状态和重入；真正独立音频生产线程/可调度音频任务需系统支持及另一组接口/调度设计。若以后选择实施，须单独明确水位、延迟/画面取舍及并发验收。


<a id="submit-20261020"></a>
## 用户确认及提交收尾（2026-10-20）

用户最新“提交”确认本组F0066/F0067设备read修复、99:1音频补查及已披露限制，授权提交归属明确的本批改动；不授权下一组或push。复用原功能19终检、音频补充15终检与13项测量核对/3判据负例，提交前9项身份核对通过，原60份非README证据及补充64份manifest项无漂移、48源输入及生产repair.patch保持，未重跑已验收测试或重复Completion/清理。

本次仅纳入device.c、报告/.gitignore、process索引和repair-status共5个文件；测试源/原始证据及.agent沿用本地忽略约定，不由commit备份。实际提交身份以包含本节的Git提交和local/submit-receipt.json为准；提交后核对文件/blob集合与root/index干净状态，并记录实际回执。51已修/68未修完，已报告范围获用户确认；F0043、旧流畅版身份未知、实体听音未测及其他剩余项仍保留。按本条指令提交后停止，不进入F0068或M2/M3。


<a id="framework-diff-20261020"></a>
## 框架代码前后 diff 与实现说明（2026-10-20 补充）

按本轮用户要求追加；保留上文验收时间、结果及限制。以下为实际修复差异，`-` 是修复前，`+` 是修复后，未省略所列文件的修复 hunks。仓库路径和前后版本分开标明；旧版本指本批修复前版本，不等同于框架最初上游版本。原产品测试不在本轮重跑；本轮只核验差异/源码身份、可正反应用及说明一致性。全范围盘点见[留档记录](../framework-diffs-20261020/README.md)。


### F0066/F0067 — 根仓库

两个设备读取修复均直接包含在同一文件差异。

- 差异路径相对于仓库 `.`；旧版本：`5941586720da24f51af299274f0220e23c2206a0`；新版本：`07bba7481b1910c00bbfd634d0df513122dc0ab6`。

#### `nanos-lite/src/device.c`

F0066：`len==0` 在 yield/读取按键前返回；校验 keycode 为正、未超 keyname 且条目非 NULL 后才索引。把三段事件文本逐字节按 `n < len` 复制；有余量才追加 NUL，返回实际写入字节数，满缓冲不额外写终止符；原 F 键切前台逻辑保持。F0067：音频状态零长度不访问设备，`len` 仅截到 sizeof(int)，用 `memcpy(buf, &free, len)` 支持短缓冲与非对齐地址，返回实际复制长度。空闲样本字节数 free 是状态内容，不再被错误当作状态结构可读长度；free=0 仍可读出四字节整数零。本补充不把原音频预算诊断改写为流畅播放验收。

```diff
diff --git a/nanos-lite/src/device.c b/nanos-lite/src/device.c
index 073df470f46eb9b2a18f29a1267cca0f06fe5de2..484f5c5c0e3f8d3a6335c477ade4f4050b95aa23 100755
--- a/nanos-lite/src/device.c
+++ b/nanos-lite/src/device.c
@@ -29,6 +29,7 @@ size_t serial_write(const void *buf, size_t offset, size_t len) {
 }
 
 size_t events_read(void *buf, size_t offset, size_t len) {
+  if (len == 0) { return 0; }
   MULTIPROGRAM_YIELD();
   AM_INPUT_KEYBRD_T kbd = {};
   bool keydown = 0;
@@ -36,10 +37,9 @@ size_t events_read(void *buf, size_t offset, size_t len) {
   kbd = io_read(AM_INPUT_KEYBRD);
   keydown = kbd.keydown;
   keycode = kbd.keycode;
-  if(!keycode) {return 0;}
-  char *tmp = (char *)buf;
-  char *down_const = "kd ";
-  char *up_const = "ku ";
+  if (keycode <= 0 || keycode >= LENGTH(keyname) || keyname[keycode] == NULL) {
+    return 0;
+  }
 
   #ifdef FG_PROCESS
   // PA4.5: F1/F2/F3 switch the foreground process. The key is consumed by the
@@ -51,11 +51,15 @@ size_t events_read(void *buf, size_t offset, size_t len) {
   }
   #endif
 
-  if(keydown){strcpy(tmp, down_const);}
-  else{strcpy(tmp, up_const);}
-  strcat(tmp, keyname[keycode]);
-  strcat(tmp, "\n");
-  return strlen(tmp);
+  const char *parts[] = {keydown ? "kd " : "ku ", keyname[keycode], "\n"};
+  size_t n = 0;
+  for (int i = 0; i < LENGTH(parts); i++) {
+    for (const char *p = parts[i]; *p && n < len; p++) {
+      ((char *)buf)[n++] = *p;
+    }
+  }
+  if (n < len) { ((char *)buf)[n] = '\0'; }
+  return n;
 }
 
 size_t dispinfo_read(void *buf, size_t offset, size_t len) {
@@ -93,13 +97,13 @@ size_t audio_init() {
 }
 
 size_t audio_read(void *buf, size_t offset, size_t len) {
+  if (len == 0) { return 0; }
   AM_AUDIO_STATUS_T stat = io_read(AM_AUDIO_STATUS);
   int free = audio_sbuf_size - stat.count;
   if (free < 0) free = 0;
   if (len > sizeof(int)) len = sizeof(int);
-  if (len > (size_t)free) len = free;
-  *(int *)buf = free;
-  return sizeof(int);
+  memcpy(buf, &free, len);
+  return len;
 }
 
 size_t audio_ctrl_write(const void *buf, size_t offset, size_t len) {
```
