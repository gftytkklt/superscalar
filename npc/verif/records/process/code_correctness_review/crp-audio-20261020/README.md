# CRP SDL 音频合组（2026-10-20）

## 计划与授权

目标：合并修复F0094/F0095/F0096/F0100/F0101/F0102/F0103/F0115，逐项保留结论，最终组合统一验收。用户“提交后继续”及产物保留确认后，F0093实际提交e42b6b3119f1462148799694e9037e972eda55e5；用户进一步明确音频相关问题可合组。格式策略用户明确选择最小限制：SDL输出S16单/双声道，mixer输出S16双声道；U8/其他输出格式及非法参数返回失败，WAV U8加载/转换保持。

范围：miniSDL audio.c/general.c和私有WAV解析头、NDL音频fd幂等辅助、SDL_mixer、ONS实际通道分配/播放错误传播。根/ONS独立仓分别归属；ONS已有一处字体字符串编码差异原样保留，不纳入本批修复diff。F0043 AM异步提交未决、F0118 NEMU宿主打开失败和PAL RIX F0112等非SDL层独立事项保留，不宣称整条音频栈已全部修复。音质算法/并发/其他ISA不扩展，不改Make选项和日常update→run流程，不安装/下载。

工作顺序：在既有CRP工作单元内分析/实施八项，完成组合host与真实RV64和标准消费者验收，再归档/清理/报告；不为每项设置确认或commit停点。交付为必要生产源码、完整diff及语句解释/版本身份、本地最小验证源/命令/日志/结果，索引/状态/完成快照。只有真实未决契约/安装才暂停依赖工作。

验收：原版关闭后回调/非法IO、奇数字节越界、错误格式/QuerySpec、奇数chunk及缺fmt、65536帧回绕、编码内存泄漏及ONS高通道失败见证；最终host生产audio/timer/event/NDL及mixer/真实vorbis，普通与ASan+UBSan，明确模型边界；真实RV64链接同版生产库/真实设备和时钟，关闭/重复关闭/回调关闭重开、参数失败保持、WAV文件/内存、长chunk/loop/OGG load/play/free及通道54；隔离原nanos目录标准update→run三前台和hello、源码/对象/库/链接=安装=盘同版及实际目视。CPU/RT/REF不依赖Navy SDL，不无故重跑；NPC/实体听音/线程并发/长时NotRun。判据检查有效PASS/正常main退出及GOOD，诊断末端观测与标准消费者分开。

收尾：完整根/ONS相对已记录旧基线diff正反精确、全部修改有逐句说明；保护用户重生成的正式盘/header/kernel及NEMU/配置、libc850原mode，保留ONS已有差异。记录路径/字节/SHA后删除本组可再生产物/截图/生产副本，保留最小测试源及证据。Completed、用户确认、commit分别记录；本轮完成后等待本组结果确认与提交，不自动push/下一组/M2。

必读与规则：AGENTS/WORKFLOW_POLICY、CRP workflow（archive/cleanup）、FINAL_FINDINGS八条、SERVICE_RUNTIME/MEDIA_RUNTIME、F0093真实回归配方。2026-10-20查阅ICS-PA输入输出、SDL1.2 OpenAudio/CloseAudio及Microsoft RIFF官方文档；仅佐证本地已实现PCM/生命周期，不承诺完整SDL兼容。来源链接：<https://ysyx.oscc.cc/docs/ics-pa/2.5.html>、<https://www.libsdl.org/release/SDL-1.2.15/docs/html/sdlopenaudio.html>、<https://www.libsdl.org/release/SDL-1.2.15/docs/html/sdlcloseaudio.html>、<https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff->。

## 实施与组合验收结果

八项Completed，结果确认/根与ONS源码commit Pending；F0093已确认提交e42b6b3。本组未自动提交/push/M2推进。根生产4个已跟踪文件及1个新私有头，ONS两个源文件；实际路径/完整版本与SHA见下文及local/archive-validation。ONS原编码差异保持，不作为F0115实现。

| 问题 | 最终实现与本轮验收 |
|---|---|
| F0094 | Close先暂停/清callback与userdata、递增generation并撤销open，再关闭fd；callback保存generation，返回后只有仍打开且同代才Play，旧stream仍free。Quit调用Close，NDL负fd不做系统调用，重复Close幂等。host明确模型见证原Close后继续callback/非法Query/Play；最终含释放userdata后poll、Close/Close→Open、普通Open/Pause/reopen/定时器；旧stream提交到新实例也由host标记检测。实际RV64同套关闭/重开路径、13轮设备open/close日志且无非法fd；设备模型不代替实体听音 |
| F0095 | `i < len / 2 * 2`只处理完整S16 sample，奇数尾字节保持；volume限0..128，避免异常大volume乘法溢出。原单字节heap越界ASan精确失败；最终len0/1/2/3、饱和极值及大volume通过。派发bytes再按channels*2对齐，host stereo空闲7→4/3→0、mono3→2，实际RV64合法完整frame路径通过 |
| F0096 | 用户批准只支持SDL S16 mono/stereo、mixer S16 stereo。Open参数在改状态/开fd前检查；SDL复制desired后计算size，不采信输入size，成功后发布obtained并暂停。mixer先验证int通道/缓冲数再窄化，失败保持旧freq/open状态；QuerySpec关闭0且不改输出、打开1及真实字段。原U8误接收见证；最终U8/频率0和负/非法channels/零samples/NULL callback等拒绝，失败obtained及旧活动状态保持；host与真实RV64通过 |
| F0100/F0101 | 两个入口使用私有`load_pcm_wav`。以当前位置/真实总长度约束RIFF范围，每chunk用uint64计算size+pad，检查界内才读/seek；fmt至少16字节且唯一，PCM1、1/2声道、8/16位、正freq及INT_MAX、byte_rate/block_align与frame一致，data须在fmt后且完整。只有malloc/read/seek全部成功才发布spec/buffer/len；无assert处理坏文件。SDL入口统一关闭其RWops，mixer按freesrc只关wrapper；U8以减128乘256转S16，检查分配与2倍长度。空data合法，分配1字节owner而len0。原odd JUNK及缺fmt见证精确失败；最终两个真实loader各68文件（含所有前缀截断、fmt奇数扩展、空data、重复fmt、超大长度等），普通/ASan+UBSan各201断言，失败SDL三个输出原样保持。真实RV64含文件/内存U8、odd JUNK、坏fmt9类和空data；不宣称支持其他codec或data先于fmt |
| F0102 | pos改uint64 48.16、step也用uint64，覆盖uint32字节长度允许的完整frame范围，跨callback保留fraction，现有到尾时loop状态保持。原65536帧pos回绕且playing1见证；最终65535/65536/65537帧的末样本、停止/补静音及loops0/1/-1与44100→48000小数连续性通过。实际RV64经真实设备播放65537帧，finished1正常结束；不扩修既有循环接缝/重采样音质算法 |
| F0103 | Music保存encoded；加载检查decoder int长度及read/restore，失败释放已分配资源；成功Free先close decoder再free encoded与Music。真实vorbis借用缓冲不再丢失owner。原实际OGG成功load/free后残留1个mixer分配见证；最终重复真实OGG load/play/free、编码buffer/对象两处分配失败和坏decoder均归零。本轮跟踪mixer自身分配，decoder实际执行；LSan按沙箱限制关闭，不夸称通用泄漏或解码数学证明。真实RV64三轮实际OGG加载/播放/释放通过 |
| F0115 | 通道表按n checked realloc，失败保留旧表/数量；新增部分置零，n<0查询/0释放。ONS核对54请求返回，不足则Close并撤销audio_open_flag；playWave验证编号且将PlayChannel失败向playSound传播。原mixer裁到16及ONS忽略分配失败动态见证；最终54通道及15/16/49/50–53、越界/auto耗尽、OOM保持、释放、完成回调编号通过；实际RV64七个高编号均播放完成。ONS两原方法精确提取的host分支模型验证不足容量、播放失败和preload；真实完整ONS RV64应用编译exit0。ONS脚本资源/整部游戏执行未测，方法模型不写成完整应用运行 |

组合host：真实audio/timer/event/file/general、mixer（含实际静态routine）、真实vorbis/fixedpt。NDL时钟/设备由明确模型提供；普通与ASan+UBSan最终各174条断言，mixer-owned live=0；另真实NDL.c对open/read/write/close模型两构建均10open/10close/5read/10write、invalid0；F0093十五类普通/ASan+UBSan各111断言全部保持。decoder数学未启用UBSan，改变的封装代码均启用ASan+UBSan；不以其替代真实设备。WAV两入口另68文件/201断言×两构建。OOM覆盖WAV data/转换/Chunk、OGG encoded/Music和通道realloc，失败不丢旧表/不留mixer-owner。

实际RV64：同一api.h链接真实miniSDL/mixer/NDL/libc/libos/vorbis/fixedpt和真实gettimeofday、AM/NEMU音频；125断言、65537帧完成、main0、NEMU exit0/GOOD，2.570秒（本次最终重复实际值见local/guest-results）。只在隔离内核末端打印main码并halt、fs末端记录设备操作，不stub音频/时钟/库。六oracle变异（非零exit、缺PASS、错断言数、错main码、重复PASS、BAD）均拒绝。初次oracle误预计126/117，实际guest/host公共入口均计116，最终总125；原始GOOD日志保留为initial，核对共同源码与主函数计数后修正并重跑，初次不算通过。NDL-host初次FORTIFY符号重定向导致未挂到open/read，已明确关闭FORTIFY后重跑，未把夹具失败写成生产缺陷。

标准最终消费者：隔离原nanos目录`make -j4 ARCH=riscv64-nemu git_commit= update` exit0/27.835秒，再同目录run54.652秒，PAL→NTerm输入qzx错误并回prompt→slide0/1/0→PAL/Return后继续渲染；10实际SDL输入、8帧实际目视、hello33→147，slide0返回SHA精确恢复。SIGTERM/make-15为自有组有限观察结束，非guest正常退出；不凭Return的帧变化声称特定菜单。正式用户update/run三产物及NEMU/配置保持，最终源码/对象/库成员、链接=安装=盘和标准/诊断隔离核对见local验证与身份记录。

CPU/RT/REF不消费Navy SDL不重跑；NPC/其他ISA/native共享伪fd重开/NWM/实体听音/线程并发/长期NotRun。NDL native shim沿用已存在关闭语义，重复关闭不会再次close伪fd，但真实native reopen未测。外部直接混用SDL与Mix生命周期、任意恶意callback longjmp/并发和2^64次重开不承诺。F0043/F0118/PAL RIX等独立项保持未修；mixer空闲查询/互斥stub和既有音质限制不升级为新能力。

## 版本身份与完整修复diff

所属根仓与相对路径如下。旧完整commit为`e42b6b3119f1462148799694e9037e972eda55e5`；新版本均为2026-10-20未提交工作树，SHA逐文件列明。新私有头为新增文件，无旧源码；不新增公开链接符号或Make接口。

- root `navy-apps/libs/libminiSDL/src/audio.c`：old SHA256 `012ce23162928de4ddb3dd82ecc0d857187c0b96d689d9932c743a0468c5cc1b`；new SHA256 `dd065cd51503cc44dd47e8299e66d719528ed33ec0220f576df6f789e8baf172`。
- root `navy-apps/libs/libminiSDL/src/general.c`：old SHA256 `3b272acc60b05b14c7f8b08d9e980705d461740e249fbbde06bef879a3b97207`；new SHA256 `bd343f28d6c73e0af2a50fca9788d6d81305637a257d36a14780b58fbe90f36a`。
- root `navy-apps/libs/libndl/NDL.c`：old SHA256 `ee65b9521e14e2139672dde077f3245031512ef6465fe266f6f7a6dd20af53ec`；new SHA256 `1bf265443620e9d285c33effc4575d53aa7a6b81e1c2a1cbf17a3ca32f6bab5a`。
- root `navy-apps/libs/libSDL_mixer/src/mixer.c`：old SHA256 `0f26519622583081bd317fff72e9983bcc415e41040acccd3171c4875147c06e`；new SHA256 `ddef6b3f6967c3494c1f64256721977bd140364fb869732e22a2281523e3c19f`。
- root `navy-apps/libs/libminiSDL/include/sdl-wav-internal.h`：old SHA256 `None`；new SHA256 `ff470963cf9f5c1762d0558c465b7a1d3bcb0733ab079c090825c8a2ade6b3c6`。
- ons `src/system/ONScripter.cpp`：old SHA256 `c1dd8bbaae99c9257fd0aa2c96b33c1260bea56cf39aa3ef48bba8cedd0485e5`；new SHA256 `0b10265ac5884030c90c05864dc5f1be2befe9cded75f4d7f244abd3cf1bce44`。
- ons `src/audio/ONScripter_sound.cpp`：old SHA256 `f203fca83cde455fe9e6111f4c018f980db5a2578677cbdb8cb3a87a7c1f4f3a`；new SHA256 `43d7658052611f942cd025fac14888140deb33f8f362ce5f5274b264faca28f2`。

根仓完整diff：

```diff
diff --git a/navy-apps/libs/libSDL_mixer/src/mixer.c b/navy-apps/libs/libSDL_mixer/src/mixer.c
index 6cb868d2e8f6331034aff76be65187055f45797b..d63e641716d221a21a77df97623526470d1e328f 100755
--- a/navy-apps/libs/libSDL_mixer/src/mixer.c
+++ b/navy-apps/libs/libSDL_mixer/src/mixer.c
@@ -3,14 +3,15 @@
 #include <assert.h>
 #include <stdlib.h>
 #include <string.h>
+#include <sdl-wav-internal.h>
 
-#define MAX_CHANNELS 16
 
 /* ---- internal layout of the opaque Mix_Music / Mix_Chunk handles ---- */
 
 typedef struct {
   stb_vorbis *vorbis;      // OGG decoder
   stb_vorbis_info info;    // sample_rate / channels
+  uint8_t *encoded;        // borrowed by the decoder until close
   int playing;
   int loops;               // -1 = infinite, 0 = play once, n = n replays
   int volume;              // 0 .. MIX_MAX_VOLUME
@@ -25,7 +26,7 @@ typedef struct {
 
 typedef struct {
   Chunk *chunk;
-  uint32_t pos;            // 16.16 fixed-point position in source frames
+  uint64_t pos;            // 48.16 fixed-point position in source frames
   int loops;
   int volume;
   int playing;
@@ -34,7 +35,8 @@ typedef struct {
 
 static int audio_freq = 44100;
 static int num_channels = 0;
-static Channel channels[MAX_CHANNELS];
+static Channel *channels;
+static int mixer_open;
 static void (*channel_finished_cb)(int channel) = NULL;
 static Music *cur_music = NULL;
 
@@ -51,9 +53,12 @@ static void mix_music(int16_t *out, int out_n) {
   Music *m = cur_music;
   uint32_t src_rate = m->info.sample_rate;
   int src_ch = m->info.channels;
-  int need = (int)(((uint64_t)out_n * src_rate + audio_freq - 1) / audio_freq);
-  int16_t *tmp = malloc(need * src_ch * 2);
-  assert(tmp);
+  uint64_t need64 = ((uint64_t)out_n * src_rate + audio_freq - 1) / audio_freq;
+  if (src_ch < 1 || src_ch > 2 || need64 > INT_MAX / (src_ch * 2) ||
+      need64 > SIZE_MAX / (src_ch * 2)) { m->playing = 0; return; }
+  int need = need64;
+  int16_t *tmp = malloc((size_t)need * src_ch * 2);
+  if (tmp == NULL) { m->playing = 0; return; }
   int got = stb_vorbis_get_samples_short_interleaved(m->vorbis, src_ch, tmp, need * src_ch);
   if (got < need) {
     // reached the end of the stream: restart if looping
@@ -79,15 +84,15 @@ static void mix_music(int16_t *out, int out_n) {
   free(tmp);
 }
 
-// Mix one channel's chunk into `out`. Advances the 16.16 position and stops the
+// Mix one channel's chunk into `out`. Advances the 48.16 position and stops the
 // channel (with loop handling) when the chunk is exhausted.
 static void mix_chunk(Channel *c, int16_t *out, int out_n) {
   Chunk *ch = c->chunk;
   int src_frames = ch->len / (2 * ch->channels);
   int16_t *pcm = (int16_t *)ch->data;
-  uint32_t step = (uint32_t)(((uint64_t)ch->freq << 16) / audio_freq);
+  uint64_t step = ((uint64_t)ch->freq << 16) / audio_freq;
   for (int i = 0; i < out_n; i ++) {
-    int f = c->pos >> 16;
+    uint64_t f = c->pos >> 16;
     if (f >= src_frames) break;
     int16_t l, r;
     if (ch->channels == 2) { l = pcm[f * 2]; r = pcm[f * 2 + 1]; }
@@ -123,7 +128,8 @@ static void mix_audio(void *userdata, uint8_t *stream, int len) {
 /* ---- General ---- */
 
 int Mix_OpenAudio(int frequency, uint16_t format, int channels, int chunksize) {
-  audio_freq = frequency;
+  if (frequency <= 0 || format != AUDIO_S16 || channels != 2 ||
+      chunksize <= 0 || chunksize > UINT16_MAX) return -1;
   SDL_AudioSpec spec = {
     .freq = frequency,
     .format = format,
@@ -133,12 +139,17 @@ int Mix_OpenAudio(int frequency, uint16_t format, int channels, int chunksize) {
     .userdata = NULL,
   };
   if (SDL_OpenAudio(&spec, NULL) != 0) return -1;
+  audio_freq = frequency;
+  mixer_open = 1;
   SDL_PauseAudio(0);
   return 0;
 }
 
 void Mix_CloseAudio() {
   SDL_CloseAudio();
+  mixer_open = 0;
+  for (int i = 0; i < num_channels; i ++) channels[i].playing = 0;
+  if (cur_music) cur_music->playing = 0;
 }
 
 char *Mix_GetError() {
@@ -146,74 +157,38 @@ char *Mix_GetError() {
 }
 
 int Mix_QuerySpec(int *frequency, uint16_t *format, int *channels) {
+  if (!mixer_open) return 0;
   if (frequency) *frequency = audio_freq;
   if (format) *format = AUDIO_S16;
   if (channels) *channels = 2;
-  return 0;
+  return 1;
 }
 
 /* ---- WAV loading ---- */
 
 static Chunk *parse_wav(SDL_RWops *src) {
-  char riff[4], wave[4];
-  uint32_t riff_size;
-  if (SDL_RWread(src, riff, 1, 4) != 4 || memcmp(riff, "RIFF", 4) != 0) return NULL;
-  if (SDL_RWread(src, &riff_size, 4, 1) != 1) return NULL;
-  if (SDL_RWread(src, wave, 1, 4) != 4 || memcmp(wave, "WAVE", 4) != 0) return NULL;
-
-  uint32_t freq = 0;
-  int channels = 0, bits = 0;
-  uint8_t *data = NULL;
-  uint32_t data_size = 0;
-
-  for (;;) {
-    char id[4];
-    uint32_t size;
-    if (SDL_RWread(src, id, 1, 4) != 4) break;
-    if (SDL_RWread(src, &size, 4, 1) != 1) break;
-    if (memcmp(id, "fmt ", 4) == 0) {
-      uint16_t format;
-      if (SDL_RWread(src, &format, 2, 1) != 1) return NULL;
-      if (SDL_RWread(src, &channels, 2, 1) != 1) return NULL;
-      if (SDL_RWread(src, &freq, 4, 1) != 1) return NULL;
-      SDL_RWseek(src, 6, RW_SEEK_CUR); // byte rate + block align
-      if (SDL_RWread(src, &bits, 2, 1) != 1) return NULL;
-      if (format != 1) return NULL; // only PCM
-      if (size > 16) SDL_RWseek(src, size - 16, RW_SEEK_CUR);
-    } else if (memcmp(id, "data", 4) == 0) {
-      data = malloc(size);
-      if (data == NULL) return NULL;
-      if (SDL_RWread(src, data, 1, size) != size) { free(data); return NULL; }
-      data_size = size;
-      break;
-    } else {
-      SDL_RWseek(src, size, RW_SEEK_CUR);
-    }
-  }
-  if (data == NULL) return NULL;
-
-  Chunk *ch = malloc(sizeof(Chunk));
-  assert(ch);
-  ch->freq = freq;
-  ch->channels = channels;
-  if (bits == 8) {
-    // convert unsigned 8-bit to 16-bit
-    uint16_t *pcm16 = malloc(data_size * 2);
-    assert(pcm16);
-    for (uint32_t i = 0; i < data_size; i ++) pcm16[i] = ((int)data[i] - 128) << 8;
+  SDL_AudioSpec spec;
+  uint8_t *data;
+  uint32_t size;
+  if (!load_pcm_wav(src, &spec, &data, &size)) return NULL;
+  if (spec.format == AUDIO_U8) {
+    if (size > UINT32_MAX / 2 || size > SIZE_MAX / 2) { free(data); return NULL; }
+    int16_t *pcm = malloc(size ? (size_t)size * 2 : 1);
+    if (pcm == NULL) { free(data); return NULL; }
+    for (uint32_t i = 0; i < size; i ++) pcm[i] = ((int)data[i] - 128) * 256;
     free(data);
-    ch->data = (uint8_t *)pcm16;
-    ch->len = data_size * 2;
-  } else {
-    ch->data = data;
-    ch->len = data_size;
+    data = (uint8_t *)pcm;
+    size *= 2;
   }
+  Chunk *ch = malloc(sizeof(Chunk));
+  if (ch == NULL) { free(data); return NULL; }
+  *ch = (Chunk){ .data = data, .len = size, .freq = spec.freq, .channels = spec.channels };
   return ch;
 }
 
 Mix_Chunk *Mix_LoadWAV_RW(SDL_RWops *src, int freesrc) {
   Chunk *ch = parse_wav(src);
-  if (freesrc) SDL_RWclose(src);
+  if (freesrc && src != NULL) SDL_RWclose(src);
   return (Mix_Chunk *)ch;
 }
 
@@ -227,21 +202,33 @@ void Mix_FreeChunk(Mix_Chunk *chunk) {
 /* ---- Channels ---- */
 
 int Mix_AllocateChannels(int n) {
-  if (n < 0) n = 0;
-  if (n > MAX_CHANNELS) n = MAX_CHANNELS;
+  if (n < 0) return num_channels;
+  if (n == num_channels) return n;
+  if (n == 0) {
+    free(channels);
+    channels = NULL;
+  } else {
+    if ((size_t)n > SIZE_MAX / sizeof(Channel)) return num_channels;
+    Channel *next = realloc(channels, (size_t)n * sizeof(Channel));
+    if (next == NULL) return num_channels;
+    if (n > num_channels) memset(next + num_channels, 0, (n - num_channels) * sizeof(Channel));
+    channels = next;
+  }
   num_channels = n;
   return num_channels;
 }
 
 int Mix_Volume(int channel, int volume) {
   if (channel < 0) { // all channels
+    if (num_channels == 0) return 0;
     int prev = channels[0].volume;
-    for (int i = 0; i < num_channels; i ++) channels[i].volume = volume;
+    if (volume >= 0) for (int i = 0; i < num_channels; i ++)
+      channels[i].volume = volume > MIX_MAX_VOLUME ? MIX_MAX_VOLUME : volume;
     return prev;
   }
   if (channel >= num_channels) return -1;
   int prev = channels[channel].volume;
-  channels[channel].volume = volume;
+  if (volume >= 0) channels[channel].volume = volume > MIX_MAX_VOLUME ? MIX_MAX_VOLUME : volume;
   return prev;
 }
 
@@ -279,22 +266,25 @@ void Mix_ChannelFinished(void (*channel_finished)(int channel)) {
 /* ---- Music ---- */
 
 Mix_Music *Mix_LoadMUS_RW(SDL_RWops *src) {
+  if (src == NULL) return NULL;
   int64_t pos = SDL_RWtell(src);
   if (SDL_RWseek(src, 0, RW_SEEK_SET) != 0) return NULL;
   int64_t size = SDL_RWsize(src);
-  if (size <= 0) return NULL;
+  if (pos < 0 || size <= 0 || size > INT_MAX || (uint64_t)size > SIZE_MAX) return NULL;
   uint8_t *data = malloc(size);
   if (data == NULL) return NULL;
-  if (SDL_RWread(src, data, 1, size) != (size_t)size) { free(data); return NULL; }
-  SDL_RWseek(src, pos, RW_SEEK_SET);
+  size_t got = SDL_RWread(src, data, 1, size);
+  int restored = SDL_RWseek(src, pos, RW_SEEK_SET) == pos;
+  if (got != (size_t)size || !restored) { free(data); return NULL; }
 
   int err = 0;
   stb_vorbis *v = stb_vorbis_open_memory(data, size, &err, NULL);
   if (v == NULL) { free(data); return NULL; }
 
   Music *m = malloc(sizeof(Music));
-  assert(m);
+  if (m == NULL) { stb_vorbis_close(v); free(data); return NULL; }
   m->vorbis = v;
+  m->encoded = data;
   m->info = stb_vorbis_get_info(v);
   m->playing = 0;
   m->loops = 0;
@@ -315,6 +305,7 @@ void Mix_FreeMusic(Mix_Music *music) {
   Music *m = (Music *)music;
   if (m == cur_music) cur_music = NULL;
   stb_vorbis_close(m->vorbis);
+  free(m->encoded);
   free(m);
 }
 
@@ -331,7 +322,7 @@ int Mix_PlayMusic(Mix_Music *music, int loops) {
 int Mix_VolumeMusic(int volume) {
   if (cur_music == NULL) return -1;
   int prev = cur_music->volume;
-  cur_music->volume = volume;
+  if (volume >= 0) cur_music->volume = volume > MIX_MAX_VOLUME ? MIX_MAX_VOLUME : volume;
   return prev;
 }
 
@@ -348,4 +339,4 @@ int Mix_PlayingMusic() {
 
 int Mix_SetMusicPosition(double position) { return -1; }
 int Mix_SetMusicCMD(const char *command) { return -1; }
-void Mix_HookMusicFinished(void (*music_finished)()) { }
\ No newline at end of file
+void Mix_HookMusicFinished(void (*music_finished)()) { }
diff --git a/navy-apps/libs/libminiSDL/src/audio.c b/navy-apps/libs/libminiSDL/src/audio.c
index ed826cffc0e5cb005739cbf2567ba4720aa4b8c1..249f9cc283bbbdfdba651ec18d1d437697152b53 100755
--- a/navy-apps/libs/libminiSDL/src/audio.c
+++ b/navy-apps/libs/libminiSDL/src/audio.c
@@ -4,11 +4,14 @@
 #include <stdio.h>
 #include <stdlib.h>
 #include <string.h>
+#include <sdl-wav-internal.h>
 
 static SDL_AudioSpec audio_spec;
 static int audio_paused = 1;   // 打开后处于暂停状态
 static uint32_t audio_last = 0;
 static int audio_in_callback = 0;  // 重入保护标志
+static uint64_t audio_generation;
+static int audio_open;
 
 // 定期调用应用回调，获取 PCM 数据写入流缓冲区。
 // Nanos-lite 无信号机制，只能在被频繁调用的 API 中主动查询时间。
@@ -24,25 +27,35 @@ void CallbackHelper() {
   if (now - audio_last < interval) return;
   audio_last = now;
 
-  int bytes = audio_spec.samples * audio_spec.channels * (audio_spec.format == AUDIO_S16 ? 2 : 1);
+  int frame_bytes = audio_spec.channels * 2;
+  int bytes = audio_spec.size;
   // 不超过流缓冲区空闲空间，避免阻塞写入
   int space = NDL_QueryAudio();
   if (space < bytes) bytes = space;
+  if (bytes > 0) bytes -= bytes % frame_bytes;
   if (bytes <= 0) return;
 
   uint8_t *stream = malloc(bytes);
   assert(stream);
   audio_in_callback = 1;       // 进入回调，标记"正在回调中"
+  uint64_t generation = audio_generation;
   audio_spec.callback(audio_spec.userdata, stream, bytes);
   audio_in_callback = 0;       // 退出回调
-  NDL_PlayAudio(stream, bytes);
+  if (audio_open && audio_generation == generation) NDL_PlayAudio(stream, bytes);
   free(stream);
 }
 
 int SDL_OpenAudio(SDL_AudioSpec *desired, SDL_AudioSpec *obtained) {
-  assert(desired != NULL);
-  audio_spec = *desired;
+  if (desired == NULL || desired->format != AUDIO_S16 || desired->freq <= 0 ||
+      (desired->channels != 1 && desired->channels != 2) ||
+      desired->samples == 0 || desired->callback == NULL) return -1;
+  SDL_AudioSpec spec = *desired;
+  spec.size = (uint32_t)spec.samples * spec.channels * 2;
+  if (audio_open) SDL_CloseAudio();
   NDL_OpenAudio(desired->freq, desired->channels, desired->samples);
+  audio_spec = spec;
+  audio_generation ++;
+  audio_open = 1;
   if (obtained != NULL) *obtained = audio_spec;
   audio_paused = 1;
   audio_last = NDL_GetTicks();
@@ -50,6 +63,11 @@ int SDL_OpenAudio(SDL_AudioSpec *desired, SDL_AudioSpec *obtained) {
 }
 
 void SDL_CloseAudio() {
+  audio_paused = 1;
+  audio_spec.callback = NULL;
+  audio_spec.userdata = NULL;
+  audio_generation ++;
+  audio_open = 0;
   NDL_CloseAudio();
 }
 
@@ -65,7 +83,9 @@ void SDL_UnlockAudio() {
 }
 
 void SDL_MixAudio(uint8_t *dst, uint8_t *src, uint32_t len, int volume) {
-  for (uint32_t i = 0; i < len; i += 2) {
+  if (volume < 0) volume = 0;
+  if (volume > SDL_MIX_MAXVOLUME) volume = SDL_MIX_MAXVOLUME;
+  for (uint32_t i = 0; i < len / 2 * 2; i += 2) {
     int16_t d = (int16_t)(dst[i] | (dst[i + 1] << 8));
     int16_t s = (int16_t)(src[i] | (src[i + 1] << 8));
     int32_t v = d + (int32_t)s * volume / SDL_MIX_MAXVOLUME;
@@ -77,57 +97,14 @@ void SDL_MixAudio(uint8_t *dst, uint8_t *src, uint32_t len, int volume) {
 }
 
 SDL_AudioSpec *SDL_LoadWAV(const char *file, SDL_AudioSpec *spec, uint8_t **audio_buf, uint32_t *audio_len) {
-  FILE *fp = fopen(file, "r");
-  if (fp == NULL) return NULL;
-
-  // RIFF 头
-  char riff[4];
-  uint32_t riff_size;
-  char wave[4];
-  assert(1 == fread(riff, 4, 1, fp));
-  assert(memcmp(riff, "RIFF", 4) == 0);
-  assert(1 == fread(&riff_size, 4, 1, fp));
-  assert(1 == fread(wave, 4, 1, fp));
-  assert(memcmp(wave, "WAVE", 4) == 0);
-
-  // 遍历块，找到 fmt 与 data
-  while (1) {
-    char id[4];
-    uint32_t size;
-    if (fread(id, 4, 1, fp) != 1) break;
-    assert(1 == fread(&size, 4, 1, fp));
-    if (memcmp(id, "fmt ", 4) == 0) {
-      uint16_t format, channels, bits;
-      uint32_t freq, byte_rate;
-      assert(1 == fread(&format, 2, 1, fp));
-      assert(1 == fread(&channels, 2, 1, fp));
-      assert(1 == fread(&freq, 4, 1, fp));
-      assert(1 == fread(&byte_rate, 4, 1, fp));
-      fseek(fp, 2, SEEK_CUR);             // block align
-      assert(1 == fread(&bits, 2, 1, fp));
-      assert(format == 1);                // PCM
-      spec->freq = freq;
-      spec->channels = channels;
-      spec->samples = 4096;
-      spec->format = (bits == 8) ? AUDIO_U8 : AUDIO_S16;
-      if (size > 16) fseek(fp, size - 16, SEEK_CUR);
-    } else if (memcmp(id, "data", 4) == 0) {
-      uint8_t *buf = malloc(size);
-      assert(buf);
-      assert(size == fread(buf, 1, size, fp));
-      fclose(fp);
-      *audio_buf = buf;
-      *audio_len = size;
-      return spec;
-    } else {
-      fseek(fp, size, SEEK_CUR);
-    }
-  }
-
-  fclose(fp);
-  return NULL;
+  if (file == NULL || spec == NULL || audio_buf == NULL || audio_len == NULL) return NULL;
+  SDL_RWops *src = SDL_RWFromFile(file, "rb");
+  if (src == NULL) return NULL;
+  int ok = load_pcm_wav(src, spec, audio_buf, audio_len);
+  SDL_RWclose(src);
+  return ok ? spec : NULL;
 }
 
 void SDL_FreeWAV(uint8_t *audio_buf) {
   free(audio_buf);
-}
\ No newline at end of file
+}
diff --git a/navy-apps/libs/libminiSDL/src/general.c b/navy-apps/libs/libminiSDL/src/general.c
index d1884d631efb646a79ba8808b027c60d64e288e3..11ca87f314b56ed296a46f267e056e35bb8da251 100755
--- a/navy-apps/libs/libminiSDL/src/general.c
+++ b/navy-apps/libs/libminiSDL/src/general.c
@@ -1,10 +1,12 @@
 #include <NDL.h>
+#include <SDL.h>
 
 int SDL_Init(uint32_t flags) {
   return NDL_Init(flags);
 }
 
 void SDL_Quit() {
+  SDL_CloseAudio();
   NDL_Quit();
 }
 
diff --git a/navy-apps/libs/libndl/NDL.c b/navy-apps/libs/libndl/NDL.c
index 7a908f298c1e518b61219fe849a6eefcd3533252..6bd6fb1d93d342e7aa4c179754a8c05fb95ec960 100755
--- a/navy-apps/libs/libndl/NDL.c
+++ b/navy-apps/libs/libndl/NDL.c
@@ -86,16 +86,18 @@ void NDL_OpenAudio(int freq, int channels, int samples) {
 }
 
 void NDL_CloseAudio() {
-  close(sbctl_fd);
-  close(sb_fd);
+  if (sbctl_fd >= 0) close(sbctl_fd);
+  if (sb_fd >= 0) close(sb_fd);
   sbctl_fd = sb_fd = -1;
 }
 
 int NDL_PlayAudio(void *buf, int len) {
+  if (sb_fd < 0 || len <= 0) return 0;
   return write(sb_fd, buf, len);
 }
 
 int NDL_QueryAudio() {
+  if (sbctl_fd < 0) return 0;
   int free = 0;
   read(sbctl_fd, &free, sizeof(free));
   return free;
diff --git a/navy-apps/libs/libminiSDL/include/sdl-wav-internal.h b/navy-apps/libs/libminiSDL/include/sdl-wav-internal.h
new file mode 100644
index 0000000000000000000000000000000000000000..211d360ad5189542a53f2f9aca163dde32f8fac1
--- /dev/null
+++ b/navy-apps/libs/libminiSDL/include/sdl-wav-internal.h
@@ -0,0 +1,72 @@
+#ifndef __SDL_WAV_INTERNAL_H__
+#define __SDL_WAV_INTERNAL_H__
+
+// Shared by the two PCM WAV wrappers; this is not a public SDL API.
+#include <limits.h>
+#include <stdlib.h>
+#include <string.h>
+
+static uint32_t wav_le32(const uint8_t *p) {
+  return (uint32_t)p[0] | (uint32_t)p[1] << 8 |
+         (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
+}
+
+static uint16_t wav_le16(const uint8_t *p) {
+  return (uint16_t)p[0] | (uint16_t)p[1] << 8;
+}
+
+static int load_pcm_wav(SDL_RWops *src, SDL_AudioSpec *spec,
+                        uint8_t **audio_buf, uint32_t *audio_len) {
+  if (src == NULL) return 0;
+  int64_t start = SDL_RWtell(src), total = SDL_RWsize(src);
+  uint8_t header[16];
+  if (start < 0 || total < start || total - start < 12 ||
+      SDL_RWread(src, header, 1, 12) != 12 ||
+      memcmp(header, "RIFF", 4) != 0 || memcmp(header + 8, "WAVE", 4) != 0) return 0;
+  uint32_t riff_size = wav_le32(header + 4);
+  if (riff_size < 4 || (uint64_t)riff_size > (uint64_t)(total - start - 8)) return 0;
+  int64_t end = start + 8 + riff_size, pos = start + 12;
+  SDL_AudioSpec parsed = {0};
+  unsigned align = 0;
+  int have_fmt = 0;
+  while (end - pos >= 8) {
+    if (SDL_RWread(src, header, 1, 8) != 8) return 0;
+    uint32_t size = wav_le32(header + 4);
+    pos += 8;
+    uint64_t padded = (uint64_t)size + (size & 1);
+    if (padded > (uint64_t)(end - pos)) return 0;
+    int64_t next = pos + padded;
+    if (memcmp(header, "fmt ", 4) == 0) {
+      if (have_fmt || size < 16 || SDL_RWread(src, header, 1, 16) != 16) return 0;
+      unsigned channels = wav_le16(header + 2), bits = wav_le16(header + 14);
+      uint32_t freq = wav_le32(header + 4);
+      if (wav_le16(header) != 1 || (channels != 1 && channels != 2) ||
+          (bits != 8 && bits != 16) || freq == 0 || freq > INT_MAX) return 0;
+      align = channels * (bits / 8);
+      uint64_t byte_rate = (uint64_t)freq * align;
+      if (wav_le16(header + 12) != align || byte_rate > UINT32_MAX ||
+          wav_le32(header + 8) != byte_rate) return 0;
+      parsed.freq = freq;
+      parsed.channels = channels;
+      parsed.format = bits == 8 ? AUDIO_U8 : AUDIO_S16;
+      parsed.samples = 4096;
+      parsed.size = parsed.samples * align;
+      have_fmt = 1;
+    } else if (memcmp(header, "data", 4) == 0) {
+      if (!have_fmt || size % align != 0) return 0;
+      uint8_t *data = malloc(size ? size : 1);
+      if (data == NULL) return 0;
+      if (SDL_RWread(src, data, 1, size) != size ||
+          SDL_RWseek(src, next, RW_SEEK_SET) != next) { free(data); return 0; }
+      *spec = parsed;
+      *audio_buf = data;
+      *audio_len = size;
+      return 1;
+    }
+    if (SDL_RWseek(src, next, RW_SEEK_SET) != next) return 0;
+    pos = next;
+  }
+  return 0;
+}
+
+#endif
```

ONS仓完整diff（仅本组F0115）：

```diff
diff --git a/src/system/ONScripter.cpp b/src/system/ONScripter.cpp
index 840d73f0b7fb4f7472738e8e051285812e830511..7cad0c56c1da0e0f01ce7a561b6eba9f1e86eaca 100644
--- a/src/system/ONScripter.cpp
+++ b/src/system/ONScripter.cpp
@@ -127,7 +127,13 @@ void ONScripter::openAudio(int freq)
 
         audio_open_flag = true;
 
-        Mix_AllocateChannels( ONS_MIX_CHANNELS+ONS_MIX_EXTRA_CHANNELS );
+        const int requested = ONS_MIX_CHANNELS+ONS_MIX_EXTRA_CHANNELS;
+        if (Mix_AllocateChannels(requested) != requested) {
+            utils::printError("Couldn't allocate audio channels!\n");
+            Mix_CloseAudio();
+            audio_open_flag = false;
+            return;
+        }
         Mix_ChannelFinished( waveCallback );
     }
 }
diff --git a/src/audio/ONScripter_sound.cpp b/src/audio/ONScripter_sound.cpp
index b68f747ffb6209ff429af7ba32b8a5067f9591b4..2c72bf280122f889f32107497a91368fec9898bd 100644
--- a/src/audio/ONScripter_sound.cpp
+++ b/src/audio/ONScripter_sound.cpp
@@ -145,7 +145,7 @@ void ONScripter::playCDAudio()
 
 int ONScripter::playWave(Mix_Chunk *chunk, int format, bool loop_flag, int channel)
 {
-    if (!chunk) return -1;
+    if (!chunk || channel < 0 || channel >= ONS_MIX_CHANNELS+ONS_MIX_EXTRA_CHANNELS) return -1;
 
     Mix_Pause( channel );
     if ( wave_sample[channel] ) Mix_FreeChunk( wave_sample[channel] );
@@ -155,8 +155,9 @@ int ONScripter::playWave(Mix_Chunk *chunk, int format, bool loop_flag, int chann
     else if (channel == MIX_BGM_CHANNEL) Mix_Volume( channel, music_volume * MIX_MAX_VOLUME / 100 );
     else                                 Mix_Volume( channel, se_volume * MIX_MAX_VOLUME / 100 );
 
-    if ( !(format & SOUND_PRELOAD) )
-        Mix_PlayChannel( channel, wave_sample[channel], loop_flag?-1:0 );
+    if ( !(format & SOUND_PRELOAD) &&
+         Mix_PlayChannel( channel, wave_sample[channel], loop_flag?-1:0 ) < 0 )
+        return -1;
 
     return 0;
 }
```

ONS旧完整commit `35df8d32df791ab0248163c5c69dd0434e31e67f`，修复前已有一处字体字符串编码差异；上述old SHA是已存在的工作树基线，不将那处差异归入本组。冷恢复从该commit读取文件，先按以下hex行替换重现已有基线，再应用本组ONS diff；不需要保存整份旧生产源码。

```json
[
  {
    "path": "src/system/ONScripter.cpp",
    "old_line_hex": "23646566696e652044454641554c545f454e565f464f4e542022cbcecce5220a",
    "baseline_line_hex": "23646566696e652044454641554c545f454e565f464f4e542022efbfbdefbfbdefbfbdefbfbd220a"
  }
]
```

归档核验：根5文件/ONS2文件全部从注明旧版本正向应用精确等于新字节，反向精确恢复旧基线（新增头消失）；ONS已有字体编码差异恢复配方亦实际核对。local/archive-validation和repair-root/ons.patch保留；正文diff内原空上下文/历史空白逐条核对后保留字节，正文不豁免空白错误。


实施补充：mix_music用uint64计算decoder所需frame数，在转int及乘声道/字节前核界；不合理长度或临时分配失败时停止该音乐，避免溢出后分配/写入。Mix_Volume/Mix_VolumeMusic仅在非负设置时更新，限制上界128，负值保留查询行为。通道Close停止活动，不释放调用者拥有的Chunk/Music；通道表由AllocateChannels(0)释放，重开可复用容量。固定buffer末尾只处理完整frame，SDL_MixAudio的奇数尾字节原样保留；不引入新转换/采样算法。

恢复命令：从entry中的根/ONS旧commit恢复基线（ONS先应用上述编码行配方），应用正文两个patch；按现有F0074资产/工具链与用户保留产物来源，运行`local/unit.py`、`ndl-host-run.py`、`corpus.py`、`timer-regression.py`、`ons-methods.py`。隔离实际链按`prepare-runtime.py`→`standard-path/run-standard.local nanos`→`prepare-guest.py`→`run-guest.py`，ONS完整应用构建命令/环境见ons-build-result及entry；`visualize.py`后实际目视，再archive/check/cleanup/final-check。standard update生成的源树始终位于本组local，正式根资产不写；诊断追加目标与WAV另盘，不能将其视为标准盘的一部分。源/产物身份和清理前日志保留；local/.agent不随普通commit备份。


## 最终收尾

251项preclean通过，4898份源码/配置与886份产物身份保存；根5文件与ONS2文件完整diff正反及8帧实际目视完成后，清理9546项513514966逻辑字节（约489.7MiB），零tracked删除。仅本组local隔离源码/构建/磁盘、测试可再生输入、ELF/对象及截图；保留最小测试源/实际命令/退出/日志/JSON/patch/基线恢复配方。原图已删除，不再宣称可直接查看；路径/字节/SHA与预期缺失见cleanup-plan/receipt。

累计80已修/39未修完；前72已确认提交（F0093根e42b6b3），本组八项Completed、结果确认及根/ONS提交Pending。Working tree contains uncommitted CRP repair/documentation changes。ONS原编码差异/libc850mode与用户三份正式update/run产物保持；根和ONS的index均空，无push/安装/本组运行中动作。records索引、REPAIR、逐项状态、CURRENT_STATE/TASK_QUEUE与Completion Snapshot已同步；格式策略持久化到DECISIONS。未来单元仅见TASK_QUEUE#crp-next，本组完成后停止，不自动提交/下一组/M2。

建议开启新对话：本组八项已累积多种库/设备/嵌套仓证据，下一单元转图形链；完整恢复入口已准备。建议不增加审批/启动Prompt，不影响本组确认与提交授权规则。

最终终检：118项通过，87份保留身份落manifest，46条正文空白逐条确认来自完整diff原证据字节；根/ONS实际源码patch仍精确、所有清理路径均缺失、正式用户资产哈希保持，三仓HEAD/index状态及80/39计数一致。没有重跑或虚构已清理产物验证。


<a id="submit-20261020"></a>
## 用户确认及提交收尾（2026-10-20）

用户“提交后继续，并进行执行性能分析”确认本组已报告范围并授权根/ONS精确提交；后续明确分析对象为音频、图形修复后的nanos-lite实际画面/音频卡顿与应用运行瓶颈。复用原验收/Completion/清理，不重跑已验收功能。提交前87份manifest身份、7个生产源码与8份正式输入SHA保持，118项最终终检及251preclean历史证据复用。ONS实际提交`6326adf488985b9752fab47833a8acd0f9264e15`（2文件11增4删），只含本批音频失败传播；提交后仅原字体编码差异留在工作树，index为空。libc原850mode、正式用户产物/配置保持。

根仓提交纳入5个生产源/头与本报告、局部忽略和两个索引，共9路径；根实际commit以local/submit-receipt及.agent实际回执为准，避免自引用commit哈希。根/ONS提交差异分别核对到已验收版本，ONS提交源码按原编码行配方可恢复到实际验收字节；未push。local/.agent及正式忽略资产不由普通commit备份，原manifest的报告身份因本附记有来源改变，不覆盖旧验收记录。累计80项已修并获确认，39项未修完；下一工作单元仅沿TASK_QUEUE#crp-next。

可在当前对话继续：本轮恢复资料完整，已明确授权图形组及随后实际运行性能分析；常规提交核对尚未形成长调试累积。新组完成后停，不自动提交新组/下一组/M2。
