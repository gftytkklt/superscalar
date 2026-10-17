#!/usr/bin/env python3
"""CCR-P8 evidence/coverage at explicit depths. Never writes production sources."""
from pathlib import Path
import json,gzip,hashlib,re,collections
ROOT=Path(__file__).resolve().parents[6];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jsonl(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
rows=[json.loads(x) for x in gzip.open(HERE/'coverage.before.jsonl.gz','rt')]
before=json.loads((HERE/'findings.before.json').read_text());assert len(before)==89
issues=[]
NDL='navy-apps/libs/libndl/NDL.c';SDL='navy-apps/libs/libminiSDL/src/';MIX='navy-apps/libs/libSDL_mixer/src/mixer.c';APP='navy-apps/apps/'
def add(title,status,locs,func,expected,actual,trigger,validation,fix,regression,evidence):
 n=90+len(issues)
 issues.append(dict(id=f'CCR-F{n:04}',phase='CCR-P8',title=title,status=status,severity='Low' if n in [90,103,110] else 'Medium',
  locations=[dict(path=p,lines=lines,sha256=sha(p)) for p,lines in locs],functions=func,
  expected_contract_and_basis=expected,actual_and_root_cause=actual,reachability_and_impact=trigger,
  validation=validation,minimal_fix=fix,recommended_regression=regression,
  evidence=['p8/baseline.json',*evidence],conclusion=status,
  upstream_downstream_contracts='C-U05–U14 / SERVICE_RUNTIME.md / MEDIA_RUNTIME.md / APP_OS_CALLS.md；仅P8责任，P9端到端未执行',
  existing_test_coverage='U13四个媒体/事件/时间示例只覆盖正常演示，无本触发条件自动oracle；见APP_OS_CALLS.md',
  missing_evidence='无真实RV64 guest/NPC硬件/GUI与声音观察；复现仅限明确的host桩或单元编译',
  unconfirmed_assumptions_and_limits='不推定完整SDL/POSIX能力已承诺；Confirmed依据本地调用/数据流或已实现格式，Robustness为异常输入/失败边界；不主张实际应用已被利用。',
  severity_rationale='内存范围/状态/格式或资源生命周期错误；当前教学栈局部影响，未证明跨权限利用',
  evidence_origin='本轮静态源码和隔离定向探针；历史P1–P7仅复用身份/契约导航，不冒充本轮运行'))
add('NDL错误返回被当作事件，初始化/退出未维护失败状态','Robustness',[(NDL,[23,24,98,119,125,128,129,130])],
 'NDL_Init/PollEvent/Quit','read返回负数表示失败，不应让消费者解析未写入的buf；初始化应传播已打开fd的失败。',
 'PollEvent用非零判断，-1成为1；Init忽略open/read失败总返回0；Quit不重置fd，重复退出仍使用旧fd。',
 '设备打开失败或未初始化/退出后调用可把未初始化buf送入SDL/libam；当前nanos非法fd后果另见F0064。',
 '静态检查各fd赋值、read返回和所有退出边；未向真实nanos提交非法fd。','统一fd有效状态，负read失败时不得报事件，部分初始化失败清理已开资源。','open/read各点失败、两次init/quit、空事件、合法事件。',['SERVICE_RUNTIME.md'])
add('NDL绘图缺少坐标/长度与有符号乘法边界','Robustness',[(NDL,[50,51,52,53,55,56,57,65,66])],
 'NDL_OpenCanvas/DrawRect','rect应与已建立canvas/framebuffer尺寸一致，byte offset/length可表示；裁剪策略未声明处不强加SDL行为。',
 '只在OpenCanvas断言宽高上界，没有下界/rect范围检查；offset*4、w*h*4、w*4在int域计算，再送64位seek/write。',
 '负坐标、画布外矩形、大尺寸可形成负offset/回绕长度；kernel fb不检查边界F0068放大影响。','静态算术和参数链；正常一行/全屏路径未跑guest。','先明确越界策略，checked size/offset计算，禁止非法矩形进入syscall。','零/负/边缘/跨行/大乘积、center canvas、短写和seek失败。',['SERVICE_RUNTIME.md'])
add('SDL事件队列用未验证的key sym写83字节状态数组','Robustness',[(SDL+'event.c',[20,24,25]),('navy-apps/libs/libminiSDL/include/sdl-event.h',[20,42])],
 'SDL_PushEvent/PeepEvents→push_event','公开事件结构sym是uint8_t；入队前须验证是否属于NR_KEYS。',
 'sym & 0xff仍可能255，keystate只有83项；KEYDOWN/UP都会越界。',
 '应用构造的错误键值可通过PushEvent或ADDEVENT写数组外；NDL正常键名映射不会生成255。','生产event.c+host NDL桩，sym255 UBSan退出1定位24行。','限制键值范围并定义非法事件失败返回，不用掩码代替范围。','0/82/83/255、满队列、peek/get移除和按键状态。',['p8/probes-fixed/keys.log'])
add('SDL定时器在回调提交状态前允许同一到期任务重入','Confirmed',[(SDL+'timer.c',[61,64,65,66,67,69,70]),(SDL+'audio.c',[18,19,20])],
 'CallbackHelper/SDL_TimerHelper/SDL_GetTicks','计时callback可调用时间API，单个到期事件不能在原回调尚未返回时重复派发。',
 'audio_in_callback只围绕audio callback设置；TimerHelper调用callback之后才更新used/last，callback内GetTicks再次进入TimerHelper。',
 '合法callback查询时间即可无限递归/重复副作用；返回0也来不及停用。','host实际生产timer/audio，回调深度限制3，观察单个due timer回调3次、嵌套深度3。','定时器派发前建立running/调度状态与重入保护，处理callback内remove/add的generation。','回调GetTicks/PollEvent、self-remove/re-add、interval0/NULL、16槽耗尽、wrap。',['p8/probes-fixed/timer.log'])
add('SDL_CloseAudio后仍保留运行中的callback并访问已关闭fd','Confirmed',[(SDL+'audio.c',[20,23,29,37,39,54,55]),(NDL,[81,82,83,84])],
 'SDL_CloseAudio/CallbackHelper','Close关闭audio processing；本地应用PAL/nplayer随后释放回调依赖对象。官方SDL1.2.15 CloseAudio正文见SERVICE_RUNTIME。',
 'Close只调NDL_CloseAudio，未置paused、清callback/userdata；之后GetTicks/PollEvent继续查询fd并执行旧callback。',
 '任何unpaused audio关闭后继续SDL API都可触发；下游fd=-1可触发F0064，用户对象释放则可能UAF。','host生产audio/timer：close后又一次callback、invalid query1、invalid write1。','关闭时先停止派发并清理state，再关闭fd；明确callback内Close处理。','open/unpause/close/poll、重开、callback内close、对象释放后继续计时。',['p8/probes-fixed/close.log'])
add('SDL_MixAudio按两字节步进却没有检查奇数长度','Robustness',[(SDL+'audio.c',[71,72,73,74,79,80])],
 'SDL_MixAudio','len是字节数；操作不能访问超出len的source/destination。',
 '最后一次i<len成立仍无条件读写i+1。',
 'len1/奇数长缓冲越读写；callback以available bytes截断也未保证样本对齐。','生产audio.c，单字节heap缓冲ASan退出1。','按frame/sample对齐接受长度或安全处理尾字节，记录当前格式约束。','0/1/2/3、单/双声道、极值混音、volume范围。',['p8/probes-fixed/oddmix.log'])
add('SDL音频接受U8及任意mixer格式却没有与后端PCM契约匹配','Confirmed',[(SDL+'audio.c',[25,29,30,31,42,44,45]),(MIX,[112,117,120,126,128,132,140,141,142]),(NDL,[78,79]),('nemu/src/device/audio.c',[106,107,108])],
 'SDL_OpenAudio/Mix_OpenAudio/mix_audio','NDL/AM控制仅freq/channels/samples，NEMU实际输出AUDIO_S16SYS；mixer自己的mix_audio固定S16 stereo。',
 'SDL接受AUDIO_U8按每sample1byte生成但NDL不传格式；Mix_OpenAudio透传任意format/channels，mix_audio仍按每frame4byte解释，QuerySpec硬报S16/2且返回0。',
 '本地公开U8或Mix_OpenAudio(...,S16,1,...)成功后播放速度/样本/声道均可能错误；freq0还使callback除零。',
 '核对header→SDL→NDL→nanos→AM→NEMU字段；无声音人工确认。','验证/拒绝不支持的format/channel/rate，或显式转换；query与实际一致，字节数frame对齐。','S16 mono/stereo、U8、rate0/负、samples0、非整frame空闲字节、obtained.size。',['SERVICE_RUNTIME.md','MEDIA_RUNTIME.md'])
add('SDL_ConvertSurface无条件交换红蓝导致同格式转换损坏像素','Confirmed',[(SDL+'video.c',[276,281,284,285,286])],
 'SDL_ConvertSurface','本地API接收任意受支持32位fmt；相同fmt转换必须保留颜色，SDL1.2.15文档明确映射到指定格式。',
 '没有判断src/dst R/Bmask是否相同，始终ConvertPixelsARGB_ABGR。','ONS image文件路径用tmp→目标fmt；相同格式调用00112233变00332211。','生产video.c host探针精确验证同fmt交换；未用GUI观察。','相同fmt直接复制；仅反向R/B映射才交换，其他mask明确支持/失败。','同fmt/互换fmt/透明字节、非整16像素、stride。',['p8/probes-fixed/video.log'])
add('SDL_UpdateRect忽略32位surface像素mask直接送framebuffer','Confirmed',[(SDL+'video.c',[79,93,94,96]),('navy-apps/libs/libSDL_image/src/SDL_stbimage.h',[197,198,199,202])],
 'SDL_UpdateRect/STBIMG surface','NDL fb为0x00RRGGBB；image包装产生Rmask0xff/Bmask0xff0000的RGBA字节surface。',
 'UpdateRect只OR alpha，不按surface的mask/shift映射。','直接显示IMG_Load的RGBA surface时红蓝交换；当前正常bird显式Convert可以掩盖，不代表Update契约正确。','host构造同image mask：raw00332211送出ff332211而非ff112233。','按fmt映射到fb格式或限制display surface的格式并验证。','默认/相反R/Bmask、8bit palette、子矩形/stride、是否保留源像素。',['p8/probes-fixed/video.log'])
add('SDL内存RWops长度乘积转有符号后可使位置为负并越读','Robustness',[(SDL+'file.c',[58,61,62,64,71,74,75,77,83,85])],
 'mem_read/mem_write/mem_seek','size_t size*nmemb必须检查溢出/有符号表示，并保持0<=pos<=size。',
 '乘积未经检查赋ssize_t；SIZE_MAX*1变-1，n=-1不copy却把pos改-1；下一次read从base-1读取。seek CUR/END加法也无溢出防御。',
 '错误的大请求可污染后续正常请求；零size返回0且不前移正常；constructor还接受负mem.size。','生产file.c host/ASan：SIZE_MAX请求后一次1byte读取越界退出1。另记录部分元素请求返回2但消耗5bytes的语义差异，不单列Confirmed。','先检查乘积及剩余容量，保持状态不变；seek checked arithmetic；明确元素边界规则。','size/nmemb0/1/MAX、负size、非法whence、末端partial item、只读buffer。',['p8/supplement/rwoverflow-bounds.log','p8/probes-fixed/rw.log'])
add('两套WAV加载器跳过chunk时漏掉RIFF奇数字节padding','Confirmed',[(SDL+'audio.c',[114,129,141,142]),(MIX,[185,198,207,208])],
 'SDL_LoadWAV/parse_wav','RIFF chunk data按WORD补齐，chunkSize不含pad；Microsoft RIFF官方正文见MEDIA_RUNTIME。',
 'fseek/SDL_RWseek仅跳size，不加size&1，下一chunk头从padding字节开始读取。','合法JUNK size1+pad+data的PCM WAV被拒绝；与编解码数学算法无关。','host实际两个loader，构造fmt16+JUNK1+pad+data，均返回NULL；数据与配方在run_supplement。','checked计算pad和chunk剩余边界，同时处理fmt扩展和data padding。','奇/偶JUNK、fmt扩展、chunk跨EOF、seek失败。',['p8/supplement/wav-sdl-odd.log','p8/supplement/wav-mix-odd.log'])
add('WAV加载未验证fmt存在及sample/channel/rate/data长度一致性','Robustness',[(SDL+'audio.c',[111,120,126,128,130,132,138]),(MIX,[163,164,177,191,195,213,215,224])],
 'SDL_LoadWAV/parse_wav','已支持PCM也须有完整fmt，bits/channel/rate/frame length一致后才公布输出。',
 'data可先于fmt返回；SDL spec可能保留调用者旧值，mixer初始化freq/channels0；非8bit都按16bit，fmt size<16仍读16bytes。','缺fmt/截断/非法channel音频可被接收并使后续除零/错误长度；SDL assert路径不是NULL失败。','mixer data-only RIFF实际返回非NULL且channels0/rate0；其余静态。','显式状态机和最小chunk长度检查；拒绝不支持格式，输出只在成功后提交。','data-before-fmt、fmt0/15/16、bits24/32、channels0/3、rate0、短data、frame不整。',['p8/supplement/wav-nofmt.log'])
add('mixer以32位16.16累计frame位置，长chunk播放回绕','Confirmed',[(MIX,[30,91,94,101,103])],
 'Channel.pos/mix_chunk','本地Chunk.len支持32位字节长度，非循环chunk应在全部frame后停止。',
 'uint32_t pos16.16最多65535.x frames；每次+=step可先回绕，再比较src_frames，65536帧等速永远达不到结束。','44100Hz双声道约1.486秒以上WAV可重复开头/不完成，影响finished回调。','生产mixer静态函数host探针：65536帧后pos0、playing1。','扩大累积位置并checked step/end，保留小数跨callback连续性。','65535/65536/65537帧、不同rate、loops0/1/-1、末尾buffer补静音。',['p8/probes-fixed/mixer-wrap.log'])
add('Mix_LoadMUS_RW保留编码内存却在FreeMusic丢失所有权','Confirmed',[(MIX,[310,312,316,317,320,322,324,345,346])],
 'Mix_LoadMUS_RW/Mix_FreeMusic','stb_vorbis_open_memory借用整段data直到close；包装负责释放自己分配的编码data。',
 'malloc读取编码data后仅保存decoder和info，Music无data字段；close只释放decoder内部状态，free(m)没有编码buffer。','每次成功加载/释放音乐泄漏完整OGG文件；失败路径已经free(data)。','跟踪实际stb_vorbis_open_memory的stream借用及deinit释放项，静态证据；未作heap统计。','在Music保留编码buffer，先close decoder再free buffer；所有失败分支统一清理。','重复load/play/free、OOM/decoder失败、RWops借用与调用者free独立。',['MEDIA_RUNTIME.md'])
add('BMP加载错误分支漏关文件且忽略像素短读和尺寸边界','Robustness',[('navy-apps/libs/libbmp/src/BMP.c',[34,36,38,40,41,44,46,50])],
 'BMP_Load/SDL_LoadBMP','系统交互包装须核定header/offset/stride/alloc/read长度及资源cleanup。',
 'bitcount/compression早返不fclose；不核type/planes/offset/尺寸，malloc无失败处理；nread未用，仍转换未读区域。','不支持BMP反复加载泄漏FILE/fd；截断或大/负height文件导致未初始化像素或错误分配。','逐语句静态核对；未宣称所带BMP显示失败。','集中cleanup、限制当前24bit bottom-up子集、checked尺寸/stride、短读返回失败。','不支持bitcount/compression、top-down、0/极大尺寸、截断每行、allocation失败。',['MEDIA_RUNTIME.md'])
add('BDF文件解析没有限制token、bitmap行数与换行边界','Robustness',[('navy-apps/libs/libbdf/src/BDF.cpp',[37,39,62,63,65,67,81,85]),('navy-apps/libs/libbdf/src/SDL_bdf.cpp',[6])],
 'BDF_Font constructor/create/BDF_CreateSurface','文件适配保留buf256/cmd32/bm32及字体索引的实际边界，纯glyph排版算法不审。',
 '%s无width可溢cmd，bm_idx不限制32；for直到newline不验证NUL，长/无newline行越读；char ch直接作为font256索引。','异常BDF资源或高位signed char可越读写；不存在font时w/h也未初始化。','静态追踪fgets容量和各数组写入；没有运行恶意字体或GUI。','字段验证/限宽解析，保存实际行长度，约束glyph尺寸/index，失败对象不可用。','缺文件、无末newline、长token、33行bitmap、w>32、negative/high-bit char。',['MEDIA_RUNTIME.md'])
add('IMG_Load_RW的freesrc和RWops位置限制没有在公共入口校验','Robustness',[('navy-apps/libs/libSDL_image/src/image.c',[13,14,15,16]),(APP+'onscripter/repo/src/builtin_dll/layer_snow.cpp',[119])],
 'IMG_Load_RW/IMG_LoadJPG_RW','layer_snow用MEM RWops并传freesrc1，但USE_BUILTIN_LAYER_EFFECTS在当前Navy外层未定义；不能用host repo Makefile的DEFS推定当前选入。',
 '直接assert(freesrc==0)，只接受MEM且总从mem.base开始，不消费当前位置或关闭src。','当前正常ONS image路径freesrc0从0开始符合实现；扩展路径/非0位置会断言或错误解码，不宣称已触发当前游戏失败。','caller/callee静态匹配；ONS本轮编译未启用builtin layer宏。','核定freesrc/position协议，支持或明确失败FILE RWops；不能静默泄漏。','MEM/FILE、当前位置非0、freesrc0/1、错误解码时cleanup。',['APP_OS_CALLS.md','MEDIA_RUNTIME.md'])
add('ONS字体缓存把RWops seek的offset和whence参数交换','Confirmed',[(APP+'onscripter/repo/src/system/ONScripter.cpp',[385,386,387,388]),('navy-apps/libs/libminiSDL/include/sdl-file.h',[12])],
 'ONScripter::init cacheFont','RWops.seek签名为(f,int64_t offset,int whence)，末端长度须seek(f,0,SEEK_END)。',
 'seek(f,RW_SEEK_END,0)实际offset2/SEEK_SET返回2；所谓rewind为offset0/SEEK_SET正常，但只分配/缓存2bytes。','启用cacheFont后仅缓存字体前2bytes，后续缓存font路径不可用。','静态实参对照，未启用真实游戏缓存场景。','按当前RWops参数顺序调用并检查size/read/seek结果，保持64位size。','cacheFont开关、缺文件/seek失败、正常TTF长度、短读。',['APP_OS_CALLS.md'])
add('ONS缓存字体调用到明确未实现的ConstMem和OpenFontRW','Confirmed',[(APP+'onscripter/repo/src/misc/mySDL.cpp',[9,10,11]),(APP+'onscripter/repo/src/text/FontInfo.cpp',[95,100]),('navy-apps/libs/libSDL_ttf/src/ttf.c',[46,47,48])],
 'SDL_RWFromConstMem/TTF_OpenFontRW/FontInfo::openFont','实际cache_font_file匹配分支以内存借用方式打开字体；不要求实现任意完整SDL_ttf。',
 '两级入口均assert(0)，没有只读RWops类型也无font内存所有权路径。','启用字体缓存即使修复F0107长度也会在ConstMem断言；两问题独立。','静态调用链与生产编译；默认非cacheFont路径不触发。','为实际需求实现只读借用/释放协议和FontRW，或明确禁用该选项并失败返回。','缓存命中/未命中、freesrc语义、字体关闭和共享buffer生命周期。',['APP_OS_CALLS.md','MEDIA_RUNTIME.md'])
add('终端escape解析未用count限制读指针','Robustness',[(APP+'nterm/src/term.cpp',[205,214,220,224,248,252])],
 'Terminal::write_escape/write','write(str,count)可来自read的有界字节序列，不能依赖count外NUL。',
 '固定pattern字符匹配无限制*s；数字循环先读*s再判断s-str<count，部分ESC/CSI读取buffer末端以外。','外部应用输出在读块边界切断ESC序列时可越读；当前RV64 extern pipe尚不支持，不宣称已guest复现。','静态索引；Terminal::write普通文本遍历按count限界，问题限escape子路径。','所有读前先验count，跨块保存未完成escape parser状态，checked数字参数。','1byte ESC、CSI/数字在每个切分点、无NUL、长数字、非法pattern。',['APP_OS_CALLS.md'])
add('NWM外部窗口未初始化尺寸且EOF处理不退出','Robustness',[(APP+'nwm/src/window.cpp',[55,57,132,193,225,230,237]),(APP+'nwm/include/nwm.h',[39])],
 'Window constructor/resize/update/destructor','fw/fh/fb需在第一次resize/update前处于确定状态；IPC EOF不是可重试空消息。',
 'constructor不初始化fw/fh/dx/dy；首次resize先munmap(fb,fw*fh*4)，update在无尺寸握手时也遍历fh；read返回0永远继续do/while。','非阻塞pipe首次EAGAIN/子进程EOF可出现未初始化读取/忙循环；当前RV64先有IPC/mmap能力断点。','静态路径，保留RV64 window.cpp编译系统头冲突，未按此认定host GUI结果。','初始化所有字段、映射存在时才unmap；EOF关闭窗口并释放资源；严格解析尺寸握手。','创建未握手/首次resize/重resize、EAGAIN/EOF/短消息、负/大尺寸、fork失败。',['APP_OS_CALLS.md','p8/supplement/rv64-nwm-window.log'])
add('bird资源描述文本未限制名称和矩形，失败时texture未初始化','Robustness',[(APP+'bird/repo/src/Sprite.cpp',[48,63,216,240,260,272]),(APP+'bird/repo/include/Sprite.h',[45])],
 'CSprite constructor/Load/LoadTxt','文件加载后buffer坐标/length仍属OS交互，非游戏业务算法；失败对象须有确定所有权。',
 'm_pTexture未先初始化，IMG_Load失败直接return后析构读它；%s无256容量限制，文本x/y/w/h未约束就访问texture alpha。','缺资源或错误txt会释放不确定指针/越读写；实际资源不等于输入验证。','静态文件/constructor/destructor跟踪；RV64 Sprite.cpp独立编译成功。','初始化所有资源指针，限宽读取并验证rect在surface内；hsearch条目释放/重复实例协议明确。','缺图/缺txt、长名称、负/越界rect、重复load/destroy。',['APP_OS_CALLS.md'])
add('PAL RIX文件读取长度不受16384字节buffer容量限制','Robustness',[(APP+'pal/repo/src/sound/adplug/rix.cpp',[95,96,98,155,158,161,163]),(APP+'pal/repo/src/sound/adplug/rix.h',[48])],
 'CrixPlayer::load/rewindReInit','保留系统fread长度与对象容量核对，OPL合成算法按S01/S02排除。',
 '单RIX按ftell的全文件长fread，MKF按index2-index读取，均不核sizeof(rix_buf)=16384；负/错误offset差还可能转巨大size。','超大或错误资源使C++对象内存越写；load坏signature还fclose后保留fp供析构再次close。','静态核对声明容量/两条读取链；未运行破坏内存的RIX。','读取前checked offset/length与buffer容量，短读失败；关闭后清fp并维护独占所有权。','16383/16384/16385bytes、短header、反序index、坏signature后析构。',['APP_OS_CALLS.md'])
add('nanos-lite-guest的软件syscall钩子会截获自身后端IO并递归','Confirmed',[(APP+'nanos-lite-guest/Makefile',[9,14]),('navy-apps/libs/libam/src/cte.c',[44,49,50]),('navy-apps/libs/libam/src/ioe.c',[30,43]),('navy-apps/libs/libos/src/syscall.c',[58,59]),('nanos-lite/src/irq.c',[13])],
 'guest init_irq→libos→__am_cte_syscall→do_syscall→libam/NDL→libos','嵌套guest请求与承载guest的OS IO需要两个独立派发域，不能让backend再陷入同一guest handler。',
 'libos只要弱hook存在就转软件CTE；guest注册handler后，gettimeofday/read经其device/ioe→NDL再进入同一个hook/current_ctx，无backend bypass。',
 '修复F0086清洁构建后仍有逻辑递归；当前HAS_VME/缺ramdisk等先行阻塞，未声称当前二进制已执行到该点。','静态闭合caller/callee；VME占位、heap空和switch占位复用P7限制，非动态guest结论。','区分内外syscall域并为backend提供直接宿主调用；共享current_ctx需可重入设计。','安装handler前后分别time/read/write、嵌套调用、real context switching、失败不递归。',['APP_OS_CALLS.md'])
add('SDL_SoftStretch缩放路径没有矩形裁剪或buffer范围检查','Robustness',[(SDL+'video.c',[201,206,211,218,220,221,224])],
 'SDL_SoftStretch','surface/rect传递给显示前，采样与写入坐标必须在对应surface有效像素域。',
 '等尺寸交给Blit有clip，不同尺寸直接以dx/dy/sx/sy读写，负dstrect或越界source未裁剪；乘法j*sh/i*sw也无边界。','不同尺寸的部分屏外rect可写surface前/后；PAL使用该路径，当前常规合法rect不触发。','静态逐循环/stride核对；没有宣称真实PAL显示错误。','裁剪并调整采样映射或拒绝非法rect，checked尺寸计算。','同尺寸/缩放、零尺寸、部分屏外rect、8bit pitch、极端矩形。',['SERVICE_RUNTIME.md'])
add('ONS请求54个mixer通道而实际只有16个，播放失败仍报成功','Confirmed',[(APP+'onscripter/repo/include/ONScripter.h',[54]),(APP+'onscripter/repo/src/system/ONScripter.cpp',[130]),(MIX,[7,233,234,265]),(APP+'onscripter/repo/src/audio/ONScripter_sound.cpp',[155,160])],
 'ONS init/playWave→Mix_AllocateChannels/Mix_PlayChannel','适配须按实际返回的channel容量和播放结果工作；特殊BGM/WAVE编号50–53必须能路由或报告失败。',
 'ONS常量50+4请求54，Mix裁到MAX_CHANNELS16；ONS忽略AllocateChannels结果，playWave也忽略PlayChannel的-1而return0。',
 '实际SOUND_CHUNK高编号WAVE/BGM/loop通道静默不播放；未人工观察声音，但双方索引与错误返回已静态确定。',
 '当前RV64生产单元编译，双方常量/边界/返回流静态匹配。','统一通道预算/映射并检查Allocate/Play返回。','channel15/16/49/50–53、auto耗尽、preload/play失败、回调编号。',['APP_OS_CALLS.md','MEDIA_RUNTIME.md'])
# Resolve evidence lines by literal source anchors, avoiding stale draft line guesses.
anchors={
90:[['return read(evtdev','evtdev = open','fbdev = open','close(evtdev);']],
91:[['int offset_y','int offset =','offset*4','w*h*4','w*4']],
92:[['keystate[ev->key.keysym.sym'],['uint8_t sym;']],
93:[['timers[i].callback','timers[i].used = false','timers[i].last = NDL_GetTicks'],['if (audio_in_callback)','SDL_TimerHelper();']],
94:[['void SDL_CloseAudio','NDL_CloseAudio();','NDL_QueryAudio();','audio_spec.callback(audio_spec.userdata'],['void NDL_CloseAudio','sbctl_fd = sb_fd = -1']],
95:[['i < len; i += 2','dst[i + 1]','src[i + 1]']],
96:[['audio_spec.format == AUDIO_S16','audio_spec = *desired','NDL_OpenAudio(desired'],['int Mix_OpenAudio','int out_n = len /','if (format) *format','if (channels) *channels'],['int p[3]'],['s.format = AUDIO_S16SYS']],
97:[['SDL_Surface *SDL_ConvertSurface','ConvertPixelsARGB_ABGR(ret','assert(fmt->Gmask']],
98:[['src_row[j] |','NDL_DrawRect(buf'],['rmask = 0x000000ff','bmask = 0x00ff0000']],
99:[['ssize_t need = size * nmemb','pos + n','pos += offset','pos = f->mem.size + offset']],
100:[['if (size > 16) fseek','fseek(fp, size, SEEK_CUR)'],['if (size > 16) SDL_RWseek','SDL_RWseek(src, size, RW_SEEK_CUR)']],
101:[['spec->channels =','spec->format =','memcmp(id, "data"'],['int channels = 0','if (bits == 8)','ch->channels = channels','memcmp(id, "data"']],
102:[['uint32_t pos;','c->pos += step','c->pos >> 16','src_frames =']],
103:[['uint8_t *data = malloc(size)','stb_vorbis_open_memory(data','m->vorbis = v','stb_vorbis_close(m->vorbis)','free(m);']],
104:[['hdr.bitcount != 24','hdr.compression != 0','int w = hdr.width','uint32_t *pixels = malloc','int nread = fread']],
105:[['sscanf(buf, "%s','uint32_t bm[32]','bm[bm_idx]','*p !=','bm_idx ++'],['font->font[ch]']],
106:[['assert(src->type','assert(freesrc','STBIMG_LoadFromMemory(src'],['IMG_Load_RW(SDL_RWFromMem(buffer, length), 1)']],
107:[['fontfp->seek(fontfp, RW_SEEK_END, 0)','fontfp->seek(fontfp, RW_SEEK_SET, 0)'],['(*seek)']],
108:[['SDL_RWFromConstMem','assert(0)'],['SDL_RWFromConstMem','TTF_OpenFontRW'],['TTF_Font *TTF_OpenFontRW','assert(0);']],
109:[['size_t Terminal::write_escape','if (*s != *cur)','for (; *s >=','i += write_escape']],
110:[['x = y = w = h = 0','if (fbdev_fd != -1) munmap','int nread = read','if (nread == -1)','for (y = 0; y < fh'],['int fw, fh, dx, dy']],
111:[['CSprite::CSprite','IMG_Load(szImageFileName)','if (fscanf(fp','m_pTexture->pixels'],['*m_pTexture;']],
112:[['length = (uint32_t)ftell','fread(rix_buf','length = index2 - index','fclose(fp);return false'],['uint8_t rix_buf[16384]']],
113:[['SRCS =','LIBS += libam'],['intptr_t __am_cte_syscall','cte_handler(ev, &current_ctx)'],['t->us = (uint64_t)NDL_GetTicks','NDL_PollEvent'],['if (__am_cte_syscall)','return __am_cte_syscall'],['case EVENT_SYSCALL:']],
114:[['if (dw == sw && dh == sh)','for (int j = 0; j < dh','sy0 = sy +','*dp = dst->pixels','dp[i] = sp[sx0]']],
115:[['#define ONS_MIX_CHANNELS','MIX_WAVE_CHANNEL','MIX_BGM_CHANNEL'],['Mix_AllocateChannels('],['#define MAX_CHANNELS','if (n > MAX_CHANNELS)','if (channel >= num_channels) return -1'],['Mix_PlayChannel( channel','return 0;']]
}
for issue in issues:
 n=int(issue['id'][5:]);assert len(anchors[n])==len(issue['locations'])
 for loc,needles in zip(issue['locations'],anchors[n]):
  source=(ROOT/loc['path']).read_text(errors='replace').splitlines()
  loc['lines']=sorted({i for needle in needles for i,line in enumerate(source,1) if needle in line})
  assert loc['lines'],(n,loc['path'],needles)
dump(HERE/'findings.json',issues);dump(BASE/'findings.json',before+issues)

calls={r['path']:r['sites'] for r in json.loads((HERE/'call-sites.json').read_text())}
module_notes={
 'U05':'NDL时间sec/usec→ms32、事件read、dispinfo解析、canvas居中与fb逐行byte seek/write、NWM fd3/4/5握手、audio12byte控制/4byte空闲、fd生命周期。',
 'U06':'general/event/ring/keystate/timer/audio/file RWops/video surface全部函数与公开头；host探针只是局部，不等同GUI。',
 'U07':'媒体包装文件/RWops尺寸、surface mask/stride、编码buffer与decoder/font/glyph所有权；数学编解码/栅格化算法排除S01/S02，不假设源码纯上游。',
 'U08':'固定点目录/调用登记；TTF字体像素尺寸和PCM/绘图转换在调用侧保留；纯fixedpt数学S02排除。',
 'U09':'应用事件/exec/env/stdio/GUI/audio/IPC路径；仅OS及服务调用、输出buffer尺寸与生命周期，业务算法排除。',
 'U10':'guest两个stub及共享nanos源重新以libam软件CTE/OS后端消费关系检查；不能用P6去重消掉新派发域。',
 'U11':'可见包装复用P7构建核定；am-kernels系统接入引用P5/P7；fceux/oslab0缺源MissingSource非已审。',
 'U12':'S01/S02：第三方系统适配/调用契约/本地差异保留；游戏/VM/压缩/OPL/业务文本算法不审。详逐文件calls与APP_OS_CALLS。',
 'U13':'audiotest/bmp/event/timer四示例触发接口与oracle/边界；GUI/声音为ManualNotRun。',
 'U14':'复用P7 asset/fsimg-match生成消费审阅；本轮重核输入哈希/链接，无新镜像构建，产物与源码版本配对限制保留。'}
file_reviews=[]; selected=[]
for r in rows:
 if not (r.get('effective_phase')=='CCR-P8' or 'CCR-P8' in r.get('effective_phase_responsibilities',{})):continue
 selected.append(r)
 if r['row_kind']!='file':continue
 path=r['path']; f=ROOT/path; m=r['module_id']; note=module_notes[m]
 missing=not f.exists() and not f.is_symlink(); source=f.suffix in ['.c','.cpp','.h','.S','.cc','.hpp']; sites=calls.get(path,[])
 if missing and m=='U11':depth='MissingSource';status='Unavailable';exclude='S05保留，不是范围排除；必须补源或获明确范围调整'
 elif missing:depth='MissingHistoricalMetadata';status='BoundaryReviewed';exclude='既有删除保留；PAL AUTHORS/README定向读取HEAD原文补导航，不冒充当前文件存在，不restore'
 elif m=='U14' or '/.git/' in path or '/build/' in path or not source:depth='AssetOrProvenanceBoundary';status='BoundaryReviewed';exclude='S03资源/产物/元数据，不逐行机器码/资源审阅；来源身份不证明正确性'
 elif m=='U08':depth='BusinessAlgorithmBoundary';status='BoundaryReviewed';exclude='S02纯固定点数学算法；参与接口的转换在调用者核定'
 elif path.endswith(('stb_image.h','stb_truetype.h','stb_vorbis.c','vorbis.h')):depth='CodecInterfaceBoundary';status='BoundaryReviewed';exclude='S01/S02纯编解码、曲线/栅格算法不审；API/分配/stdio/borrowed内存接口保留'
 elif '/busybox/repo/' in path:
  depth='ThirdPartySystemBoundary';status='BoundaryReviewed';exclude='S01非本地相关上游内部不逐函数审；所有byte delta、Navy补丁/header、enabled applet系统契约在APP_OS_CALLS；禁用功能不是运行覆盖'
 elif m=='U12':
  depth='ApplicationInterface' if sites else 'BusinessAlgorithmBoundary';status='ReviewedStatic' if sites else 'BoundaryReviewed';exclude='S02逐文件排除游戏逻辑/脚本VM/压缩/排版/OPL数学；仅列出的服务调用及buffer尺寸/所有权保留。无匹配点不证明无间接调用，公共适配宏和headers另登记'
 else:depth='TestOracle' if m=='U13' else 'ServiceOrApplicationInterface';status='ReviewedStatic';exclude='S02业务行为/纯视觉样式不审；函数中的系统参数/长度/返回/状态保留'
 ids=[x['id'] for x in issues if any(l['path']==path for l in x['locations'])]
 # Existing root causes stay under their original stable IDs.
 if path==NDL:ids+=['CCR-F0064','CCR-F0066','CCR-F0067','CCR-F0068']
 review=dict(row_id=r['row_id'],path=path,module_id=m,source_sha256=r.get('source_sha256'),hash_semantics=r.get('hash_semantics'),review_depth=depth,review_status=status,
  normal=note,boundary_zero_empty_invalid='空/零长、失败返回、checked尺寸、格式和可用能力按模块报告逐路径核定；未定义错误策略不自选。',
  failure_state_return_cleanup='公开返回与上游能力逐项核；Assert/No-op/Unsupported单列，不当作功能PASS；新问题见issue_ids。',
  integer_alignment_lifetime='RV64 size_t/long/offset64，int32；sample/frame/byte/pixel/ms/us分别保留；borrowed/owned内存和fd见报告。',
  init_repeat='初始化/重复/退出由SERVICE/MEDIA/APP报告核；无通用幂等承诺。',
  excluded_parts=exclude,call_sites=sites,issue_ids=ids,evidence=['SERVICE_RUNTIME.md','MEDIA_RUNTIME.md','APP_OS_CALLS.md','BOUNDARIES_P8.md','p8/baseline.json','p8/provenance.json'],
  dynamic_validation='TargetNotRun; GUI/audio ManualNotRun; exact host/compile applicability in findings/results',responsibility='CCR-P8 only; P9 pending')
 file_reviews.append(review);r['p8_review']=review
 r['evidence_ids']=list(dict.fromkeys(r.get('evidence_ids',[])+['CCR-E-P8-static','CCR-E-P8-probes']))
 r['issue_ids']=list(dict.fromkeys(r.get('issue_ids',[])+ids));r['limits']=r.get('limits',[])+['P8仅所列深度；S05缺源未审，当前Final Gate Partial；无真实guest/GUI/声音验收，P9未Start。']
 if r.get('effective_phase')=='CCR-P8':r['review_status']=status;r['phase']='CCR-P8'
files={r['path']:r for r in file_reviews}; branches=[]
for r in selected:
 if r['row_kind']=='file':continue
 f=files[r['path']]; review=dict(row_id=r['row_id'],path=r['path'],line_range=r.get('line_range'),function_or_path=r.get('function_or_path'),source_sha256=r.get('source_sha256'),
   file_depth=f['review_depth'],disposition='ConditionNavigationAtDeclaredDepth',basis='继承逐文件接口/已批准S01/S02/S03边界；条件不是独立功能路径或动态覆盖。当前仅RV64 __NAVY__、非__ISA_NATIVE__分支；注释示例/算法条件仅边界。',
   responsibility='CCR-P8 only',evidence=['p8/file-review.jsonl','SERVICE_RUNTIME.md','MEDIA_RUNTIME.md','APP_OS_CALLS.md'],dynamic_validation='NotRun for target')
 r['p8_review']=review;branches.append(review)
jsonl(HERE/'file-review.jsonl',file_reviews);jsonl(HERE/'branch-review.jsonl',branches);jsonl(BASE/'coverage.jsonl',rows)
summary=dict(files=len(file_reviews),conditions=len(branches),modules=dict(collections.Counter(r['module_id'] for r in file_reviews)),depths=dict(collections.Counter(r['review_depth'] for r in file_reviews)),
 statuses=dict(collections.Counter(r['review_status'] for r in file_reviews)),new_findings=len(issues),new_statuses=dict(collections.Counter(r['status'] for r in issues)),cumulative=len(before+issues),
 unavailable=[r['path'] for r in file_reviews if r['review_status']=='Unavailable'],final_gate='PARTIAL — retained missing source prevents full P8 acceptance; not Completed')
dump(HERE/'review-summary.json',summary)
text=['# CCR-P8 逐文件边界表\n','2026-10-17。主分母、来源与全部6,434身份（含资产/缺源）在 [file-review.jsonl](p8/file-review.jsonl)；条件导航见 [branch-review](p8/branch-review.jsonl)。每行保留稳定ID/hash/模块、审阅深度、排除部分/理由与实际调用位置。S01/S02/S03为既有批准边界，S05缺源仍保留并未审。\n',
 '不把第三方HEAD字节相同解释为未改上游：NJU fork已含适配，四repo当前差异逐项核，见 [provenance](p8/provenance.json)。stb/truetype/vorbis固定点算法改写与业务数学按S02排除；接口buffer/stdio/分配不排除。\n',
 '以下逐文件列出所有源码/头的算法边界（混合文件仅排除业务部分，调用点仍审）；资源和产物逐身份见JSONL，不计功能验证。\n','| 文件 | 深度 / 范围内接口 | 明确排除与依据 |\n|---|---|---|\n']
for r in file_reviews:
 if r['path'].endswith(('.c','.cpp','.h','.S','.cc','.hpp')) and '/build/' not in r['path'] and '/.git/' not in r['path'] and '/busybox/repo/' not in r['path']:
  text.append('| `'+r['path']+'` | '+r['review_depth']+('；'+str(len(r['call_sites']))+'个调用导航' if r['call_sites'] else '')+' | '+r['excluded_parts']+' |\n')
text.append('\nBusyBox全部上游源码/头、算法/disabled applet的逐文件名称与S01理由保存在同一JSONL（不以一个目录行冒充逐文件覆盖）。本地byte delta5个、13个Navy头和配置/补丁不适用无关上游排除；系统调用清单见APP_OS_CALLS。\n')
(BASE/'BOUNDARIES_P8.md').write_text(''.join(text))
print(json.dumps(summary,ensure_ascii=False,indent=2))
