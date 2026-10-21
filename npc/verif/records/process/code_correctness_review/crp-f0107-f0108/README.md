# CRP F0107/F0108 — 字体缓存与只读 RWops / FontRW 生命周期

> **本批提交确认（2026-10-21）**：用户“提交”已确认已报告实现与真实输入结果，ONS六源已实际提交`5e72dbb9739ae39a3a2dc520ed89f20219e92f84`；根四共享源与报告/索引共八路径随本次根提交交付，实际回执在local/submit-20261021及.agent。既有未提交差异实际是DEFAULT_ENV_FONT编码行，仍保留工作区；此前“原音频差异”分类有误，见文末提交勘误。未push或开始下一组。

> **最新输入验证已完成（2026-10-21）**：原样修复版通过真实键盘输入已从黑屏推进到制作信息及《planetarian／星之梦》标题菜单，用户手动可见画面的说明得到本轮独立重现。此前黑屏仅是当时观察，不代表无法推进。见[输入结果](#input-result-20261021)；无新增生产修改/commit。

> **本批补充验证完成（2026-10-21）**：修复版已在隔离标准update→run中通过NTerm启动，缓存与默认两种启动均为黑底鼠标框，未见标题/对白。诊断运行确认完整字体缓存及首次字体打开成功，最终停点为start首行全角空格文本；完整游戏未通过。见[补充结果](#game-run-result-20261021)，原完成/勘误保留，未commit或开始下一组。

> **资源结论更正（2026-10-21）**：ONS程序、脚本、字体和两个NSA资源包均已在现有磁盘中逐字节确认。下文“缺资源/未提供脚本字体”是本轮漏查fsimg根目录导致的错误，已撤回；真实限制为修复版尚未安装打包并启动完整游戏。见[复核附记](#resource-recheck-20261021)，不能把模块测试与完整链接记为完整游戏通过。

> 当前执行（2026-10-21）：用户“同意，继续”批准补齐现有缓存功能及必要释放接口。下方必要分析与未定状态为历史截面；本轮同一批实施已完成，修复结果确认/commit Pending；不再要求重复范围确认。

2026-10-21。用户“提交，可以直接继续就继续，否则停下”确认F0026并允许具备条件时续作唯一入口；F0026已实际提交 `5a48a8ffcf3dbc81ae752231e623fc06339917c3`、八路径核验、root/index干净。按既有修复计划/CRP workflow执行一个必要分析单元，不启动业务M2，不从旧连续提交授权推定后续commit。

## 范围、验收和停点

目标为当前 `--fontcache` 参数 → 缓存文件长度/读入 → FontInfo命中 → ConstMem/OpenFontRW 的可达路径、失败/所有权边界及最小修复方向。交付本报告及local当前源码/工具身份、原版正常/失败探针、最小方案与清理回执；更新records索引/逐项状态及唯一下一入口。

验收为从当前源定位参数、默认状态与生命周期，隔离复现错误seek长度和两个占位入口，区分真实原函数、提取片段和桩的证据范围；不把host运行/独立RV64编译当真实游戏或guest通过。先确定已有功能最小修复边界；新生命周期契约/禁用选项策略未定时分析后交用户，不擅自实现完整SDL或关闭选项。不安装、不修改生产、不commit/push，分析完成后停下。

## 当前结论与调用闭包

**必要分析Completed，F0107/F0108仍未修；分析结果确认/commit Pending。** 本轮没有生产源码、Make或正式镜像修改；119项仍为104已修+11 CRP待修+2 Linux能力移交+2无需实施闭合。

当前 `src/main.cpp:31` 定义静态存储期全局 `ONScripter ons`；`cacheFont` 在零初始化后默认为false（不把构造函数未显式设置推广成所有创建方式都安全）。help列出 `--fontcache`，parseOption调用 `setFontCache()` 将其设为true；`ONScripter::init()` 的385行分支在加载资源/SDL初始化等前置步骤之后读字体缓存，随后调用 `sentence_font.openFont()`。该选项不是无入口死代码，也不应只因默认未开就把缺陷闭合。

F0107当前仍把 `seek(f, offset, whence)` 传成 `(RW_SEEK_END, 0)`，在本地实现上即移到文件偏移2并返回2；所谓rewind `(RW_SEEK_SET, 0)` 碰巧是0/SEEK_SET。结果进入int size→malloc→read→发布三个FontInfo静态缓存字段，未检查长度错误/窄化、分配失败或短读，空文件也可能发布未填满的2字节缓存。缺文件分支会打印错误并return -1，不应误报成所有失败都继续。

F0108为独立后续断点：FontInfo按缓存文件名匹配，首次字体size cache miss时先调用并关闭 `SDL_RWFromConstMem` 作为检查，再以另一个ConstMem RWops调用 `TTF_OpenFontRW(...,1,...)`。当前前者位于ONS私有 `mySDL.cpp`，后者位于共享 `libSDL_ttf/src/ttf.c`，两者均无条件assert(0)。所以只改seek参数后，该已选入路径仍会先在ConstMem中止；独立调用OpenFontRW同样中止，不能把F0107一行改动当作字体缓存已修。

当前已有 `SDL_RWFromMem` 可借用外部缓冲，close只释放RWops包装、不释放buf，并且允许write；**不能直接用它替换ConstMem后声称只读语义已实现**。SDL_RWops现有enum只有FILE/MEM，内存position在私有包装里；要复用须有明确只读构造/写拒绝实现，同时保留可写消费者。

当前TTF文件路径先完整读取到owned buf，再让stbtt_fontinfo借用该buf，TTF_Font保存finfo/buf等。公开头没有 `TTF_CloseFont`，ONS的FontContainer/root和font_cache也没有本轮可找到的显式回收；不能默默把全局生命周期缓存更改成关闭RWops时释放字体数据。FontInfo在fp/字体失败前先把新FontContainer挂入链表，修复后的返回失败还要避免失败节点冒充缓存命中。现行SDL_TTF版本条件下不预设outline/font[1]分支可用。

## 原版动态观察与编译

`local/probe.py`记录完整最小夹具生成、命令、cwd和退出码；`entry.json`冻结当前13个生产文件SHA、八正式资产、根HEAD与ONS嵌套仓库原HEAD/差异身份。ONS嵌套HEAD为 `6326adf488985b9752fab47833a8acd0f9264e15`，原有 `src/system/ONScripter.cpp` 内容修改保留，未restore或混入本轮改动。

| 场景 | 实际结果与边界 |
|---|---|
| 原F0107缓存分支，64字节文件 | 精确提取当前 `if(cacheFont)` 块、提供同名字段/打印桩，链接当前生产file.c；exit0，`cached=2 published=1`，证实长度错误。不是完整ONS init运行 |
| 同一分支，空文件 | exit0，仍 `cached=2 published=1`，没有把短读当失败 |
| 同一分支，缺文件 | exit0为观察夹具正常退出；打印 `rc=-1 cached=0 published=0`，表示被观察函数实际返回-1。不是生产失败返回0 |
| 当前原mySDL.cpp的ConstMem | 链接整个原翻译单元并gc未用函数，调用后SIGABRT/exit -6，断言文本定位原文件 |
| 当前原ttf.c的OpenFontRW | 链接整个原翻译单元并gc未用函数，调用后SIGABRT/exit -6，断言文本定位原文件。空src只是触发无条件断言的最小输入，不是有效字体完整运行 |
| 原可写MemRW控制 | 读/seek/write生效、close后借用的栈buf仍有效，exit0；仅表明复用基础存在，不是ConstMem已实现 |
| RV64受影响单元编译 | ONScripter.cpp/FontInfo.cpp/mySDL.cpp/ttf.c四单元以现有 `rv64g` / Navy headers独立编译exit0；不等于完整应用链接或guest运行 |

最终17条命令：2条版本查询、9条编译/链接（其中4条为独立RV64编译）、6次host运行（含两次预期SIGABRT），均按预期完成。第一次C++提取夹具直接include sdl-file.h漏了真实SDL.h的extern-C包装而链接失败，已改夹具include真实SDL.h后重新采集；attempt1原日志/生成配方保留，未改生产头。

所有core dump在自有子进程通过RLIMIT_CORE=0禁用，未更改系统配置；未运行原Make（避免clone/自动commit和正式资产重写）。未执行真实ONS、字体解析/字形渲染、GUI或RV64 guest；不受生产影响的CPU/RT/nanos不重跑。正常测试文件为64字节序列，仅验证文件长度/缓存发布，不伪称合法TTF。fsimg/share/games当前仅bird/pal，fsimg/share/fonts为BDF，未提供ONS游戏脚本/default.ttf；另确认系统已有DejaVuSans.ttf可供未来隔离字体试验，无需安装/下载，但本轮未将其装入guest或冒充真实游戏资源。

## 最小后续方案与真实待定范围

建议保留已经公开的 `--fontcache` 功能，按实际调用闭包补齐必要路径：

1. F0107改成正确的offset/whence次序，以int64_t核长度并在窄化到当前int接口前检查；成功seek/完整read/分配后再发布缓存，失败保留旧缓存并清理本轮资源。不能只改两行参数而忽略读取/发布。
2. F0108需要只读借用内存RWops（seek/read/close包装且write拒绝）、FontRW字体初始化及明确的buf/finfo/font/源RWops所有权；保留可写RWFromMem。FontInfo失败不留下假命中，缓存buf与多个字体size/重复打开的生命周期匹配。
3. 不扩展outline、任意字体集合/完整SDL兼容或恶意字体校验；本地stb头明确没有完整长度校验，不把前端读入检查说成已防御所有畸形字体。

**当前真实待定点是字体对象/RWops的释放契约及是否在本次补齐该缓存功能。** 官方接口的freesrc语义包含字体关闭时关闭源，而本地没有字体关闭API；“加载时复制并立即关闭源”与“保留源到字体关闭”是不同可观察生命周期。不能为了消除assert就默认其中一个契约，亦不能擅自禁用现有命令行选项。建议按本地实际消费者冻结最小所有权/释放边界后再实施；若用户选择不支持缓存，应明确收窄该选项并在入口受控失败，不将其计作已实现完整缓存。

本地代码借鉴接口而非完整SDL实现：2026-10-21只读参考 [SDL_RWFromConstMem官方说明](https://wiki.libsdl.org/SDL2/SDL_RWFromConstMem)（借用/只读/关闭不释放原buf）与 [TTF_OpenFontRW官方说明](https://wiki.libsdl.org/SDL2_ttf/TTF_OpenFontRW)（freesrc及字体关闭）。这是识别差异的依据，不能从SDL2文档推定本地已承诺完整SDL2/TTF生命周期；具体待用户决定本次支持范围。

实施验收建议：正常合法字体的文件/缓存结果一致，缓存启闭/命中/不同size/重复打开；文件缺失/空/seek失败/短读/分配失败不发布半成品；ConstMem write拒绝/close不free buf、freesrc0/1和字体回收；同版真实RV64字体加载/字形结果及受影响Navy标准update→run消费者回归。完整游戏缺资源则单列NotRun；host不能代替受影响真实guest。此为待实施验收，不是本轮通过。

按[WORKFLOW_POLICY §3](../../../../docs/WORKFLOW_POLICY.md)及[CRP workflow](../workflow/README.md)真实接口/范围取舍停点，本轮分析后停止，不自动实施、关闭选项或提交新分析；原104+11+2+2保持，唯一下一动作见TASK_QUEUE#crp-next。


## 收尾核验与恢复

37项采集/源码/身份/范围核对通过；两次SIGABRT是原占位的预期观察，不是功能PASS。已结束自有子进程，再按cleanup-plan/receipt删除两次隔离build目录内19文件314,010字节，0 tracked/正式资产删除；生产源码副本未保存，最小生成配方/提取片段、命令、日志和结果保留。清理后无o/ELF/bin/a/so，13生产输入/8正式资产及ONS既有嵌套状态/差异保持；local manifest只覆盖保留证据，不宣称清理后的二进制可复用。

本轮仅新增分析报告/.gitignore与记录导航，分析结果确认/commit Pending，根HEAD仍为5a48a8f、index空；F0026已确认已实际提交状态不回退。未来恢复从TASK_QUEUE#crp-next定位同一F0107/F0108：先冻结FontRW源/字体数据与释放时点，不因“可继续”自行选支持子集或禁用选项。忽略证据/.agent非Git备份，无push/M2推进。会话建议：可在当前对话继续；下一动作是这一缓存路径的有限契约确认，证据和唯一入口已保存。


<a id="implementation-20261021"></a>
## 已批准实施计划与契约（2026-10-21）

用户“同意，继续”确认补齐现有缓存功能和必要释放接口，沿同一F0107/F0108实施，不另加分析commit前置。范围为miniSDL只读借用RWops、SDL_ttf FontRW/CloseFont及ONS缓存读取/成功发布/失败节点/退出清理；不扩展outline或完整SDL/不可信字体解析保证。此前root两份导航和本报告为本批未提交分析，ONS原有音频改动在nested-preexisting.patch单独冻结并保持，不混成本轮新差异。

固定执行契约：ConstMem不复制/不释放借用buf，write返回0且不前移；FontRW复制当前读位置至源末尾的数据为字体私有buf，源freesrc=1成功后由字体持有并在CloseFont关闭，失败也关闭一次；freesrc=0不关闭源。File OpenFont复用同一解析但保持原有读取后关闭文件的行为。CloseFont释放finfo/私有buf/字体与所持源，NULL安全。ONS全局缓存是engine所有，TTF私有副本不依赖缓存后续替换；清空字体cache和engine销毁时先关字体再释放缓存，失败新字体节点不入表。

阶段交付与验收：逐项最小修改和host正常/失败/分配注入、不同字体size/重复命中/失败重试、freesrc0/1和释放计数；受影响RV64编译/真实字体加载和字形结果、Navy标准update→run三前台消费者回归（按共享miniSDL影响选测），完整游戏无资源单列NotRun。完整9文件前后diff/身份与正反核验，records/状态/清理收尾后停止，结果确认和commit另计，不安装/commit/push/M2。


## 实际修复与同版验证

**F0107/F0108 Completed，修复结果用户确认/commit Pending。** 用户“同意，继续”批准实现范围和必要释放接口，不代表用户已复核本轮结果。119项现为106已修+9 CRP待修+2能力移交+2无需实施闭合；原必要分析/未修状态保留为历史。

最终10文件：根仓miniSDL/TTF四文件，ONS嵌套仓库六文件。原计划9文件后补ONScripter.h的旧缓存所有权链字段：FontRW虽保存字体数据私有副本，仍按freesrc契约保留源RWops到字体关闭；这个源借用的旧cache也必须活到源关闭。因此成功重载时将旧cache纳入engine所有权链，而非立即free，析构先关闭字体和源，再free当前/旧cache及链节点。链节点分配失败也不发布新cache；这是已批准生命周期实现的必要字段，不扩大完整SDL范围。

| 问题/层 | 实现及失败边界 |
|---|---|
| F0107 ONS读入/发布 | 正确seek参数；int64长度检查正数和INT_MAX后转当前int接口；检查rewind、分配、完整read和close。所有这些失败都清理新资源并return -1，旧cache/路径/size保持；完整成功才发布。显式初始化cacheFont=false |
| F0108 ConstMem | 公共miniSDL声明/实现，复用现有MEM包装，write回调返回0且不改position，close只free包装。删除ONS私有同名占位/声明，统一C链接，无FILE/MEM枚举变化。可写RWFromMem保持 |
| F0108 FontRW | 从源当前position至末尾读取，检查长度/短读、外层sfnt/TTC目录范围后初始化已有stb。所有成功字体持有独立buf/finfo/font，freesrc=1的源在TTF_CloseFont关闭；失败关一次，freesrc=0不关。TTF_CloseFont(NULL)安全，File OpenFont通过同解析而保持原先读取后关闭文件行为 |
| F0108 FontInfo/engine | 新字体容器只在成功后入表，失败不留下假命中；malloc失败/重试可恢复。公开closeFonts清空字体池/缓存借用描述，ONS析构关闭字体后释放当前及退休缓存，保持借用源生命周期 |
| 文件RWops必要支持 | file_size/file_seek传播fseek/ftell失败，file_close返回真实fclose结果；否则缓存层检查可能把I/O失败误当成功。没有新增Make选项/目标或日常更新步骤 |

### 本轮证据

- `unit/normal-run.log`、`asan-run.log`：普通和ASan各**86个主断言通过**，只读写拒绝/position、可写控制、源当前offset、freesrc0/1关闭计数、坏长度/短读/小header、三个TTF分配失败、五个FontInfo链分配失败与重试、不同size/重复命中/显式回收。实际提取的生产缓存读入和析构释放段也在其中执行，重载后重新读取旧字体源RWops的字节，检验退休缓存仍存活；最终受观察模块分配计数为0。
- `cache-tests`：当前生产缓存块的普通/ASan各**10场景/31断言**通过。正常完整读取、打开失败、末端seek失败、空/过大长度、rewind失败、短读、cache分配失败、close失败及退休节点分配失败，核对失败不发布和旧状态/资源保持。外围I/O故障为明确桩，不冒充真实ONS完整init。
- LeakSanitizer在环境ptrace限制下报fatal；最终ASan仅禁用leak scanning、仍启用越界/释放错误检查，且本轮allocator/close计数显式归零。没有将LSan写成通过，也不声称这些计数证明整个第三方进程无任何泄漏。早期host夹具stdlib宏/extern-C/依赖和转义问题的失败日志保留，最终结果来自修正后的同版夹具。
- `guest-final-result.json`：真实RV64 user-mode/Navy/nanos/NEMU中**86断言通过**，包含生产FontInfo、文件/缓存加载、分配注入与重载旧缓冲生命周期，exit syscall显式记录0，NEMU GOOD TRAP。fixture只选择目标程序并在其exit时halt，模块源码来自当前生产；allocator替换用于计数/故障注入。五种判据故障正确拒绝。
- `guest-results.json`的pure项：另外一个**未替换分配器、使用实际共享Navy库**的RV64字体加载/字形程序通过，正常退出0。最终86计数版替换了最初85版的扩展不足；最初结果保留，不把两者混为两个独立最终覆盖。
- `baseline-result.json`：原TTF_OpenFont/字形实现、修复后host文件/缓存及RV64共享库的合法字体结果一致：height18/ascent14/descent-4，A字形11×12、像素FNV hash304558583。测试字体是系统已有DejaVuSans.ttf（759720B，来源/哈希在guest-results assets），未安装/下载。这里只验证选定字体/字形，不扩大为任意字体。
- `guest-final-commands.json`：最终当前源ONS完整RV64 app构建/链接exit0，包含新CloseFont公共声明和去掉私有ConstMem占位后的调用链；没有把单元编译冒充完整链接。
- `standard-path`：在隔离副本按既有nanos目录 **update→run** 成功；实际当前三前台PAL/NTerm/nslider切换，终端qzx+回车产生command not found并回到提示，幻灯片0→1→0的返回frame hash相同，PAL返回/回车后画面继续变化；hello从36到156。55.86秒后自有组SIGTERM，exit -15，不是guest正常退出。

上述三前台在最后仅ONS退休缓存字段/逻辑补充之前运行；共享miniSDL/TTF及相关消费者源码此后未变，最终source-identity仍完全一致，故不重复这一不受后续ONS局部补充影响的回归。后续改动已由最终host/ASan、真实RV64缓存生命周期和完整ONS最终链接覆盖。

截图清理前已目视接触表：PAL山水标题/启动画面、终端实际错误反馈、蓝底0页/绿底1页均可辨；与真实SDL输入/帧原始记录相符。保留文字与frame hash，清理后不宣称可再查看原图。完整ONS游戏脚本/default.ttf未提供，**完整游戏/--fontcache实际游戏场景NotRun**；已以真实RV64字体路径验证模块，未伪称游戏通过。此次不影响AM/RT/CPU，不重跑它们。

### 完整diff与身份

根旧完整commit为 `5a48a8ffcf3dbc81ae752231e623fc06339917c3`，ONS嵌套旧完整commit为 `6326adf488985b9752fab47833a8acd0f9264e15`。嵌套旧源在该commit基础上应用本轮开始前已有的音频diff `local/implementation/nested-preexisting.patch`（SHA256 `683a908ab9a4344a8803d62e6ad52ae7262075eec35a4d3f2296040e24b8f665`）才能恢复实际修复前字节，不能把这项旧改动归入本轮。新源为2026-10-21未提交工作树，没有新commit身份。完整十文件修复diff从实际before/new字节生成，旧基线重建、正向逐字节相同及反向还原均通过；命令在archive-validation.json。

| 仓库相对项目路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `navy-apps/libs/libminiSDL/include/sdl-file.h` | `4f1db0376d75b6c9a586e6d66d463a6cd6e6508118b0191455be5b0edf7fe711` | `b12907dc77ee4c633d9c4055fba2e5b252ddb918740afd9c41fbcf19649af2c5` |
| `navy-apps/libs/libminiSDL/src/file.c` | `17e652880d0be76123cce2746e5b07e224ebff3c0f2eda8cf83470ccd7f79d24` | `8ac1995ea442edc1447632d2c76b048c9341b446a44d923e790bbfb901427c9d` |
| `navy-apps/libs/libSDL_ttf/include/SDL_ttf.h` | `a12df5333b5450e3d780593bb99fbab4feadf48ae5d2fd99321cda701a99a00b` | `379857f9a25349657c02ea4de48606cf922104b357f3322d02da3f50b6c90018` |
| `navy-apps/libs/libSDL_ttf/src/ttf.c` | `f5fa96de57b6c23e4a2570ab2ca827ecf6670d8c725d6e93eff032b0596cea21` | `736af892a52bb7524fc5c26a1edf82b7d47dd4690882bb0570f07c61ccfb03cc` |
| `navy-apps/apps/onscripter/repo/include/mySDL.h` | `9068a9b5f55113684496665715614e35ae3829f6aac1250a45a120a7d9883d81` | `53fc38e0089e8a0b23eb295ecb910f63b1df164ad9e63426f95102ceb6ae26d8` |
| `navy-apps/apps/onscripter/repo/include/FontInfo.h` | `d7126f204b737cb690f4fe6fcf31d3181fbadf74964efea235def1501c3137ca` | `dd9761a9b9defdd9b9840fb0a2a3e39349a9471bb461f9201c51be5ee9c155c4` |
| `navy-apps/apps/onscripter/repo/src/misc/mySDL.cpp` | `9c3ccf4e6c4a581ed71efb483e78e9fe7b3041c15943e925af43855e4b8968ad` | `e69132e31803eb6935a0a09991489c33501c2725c91b4fd90540dcc2973aed20` |
| `navy-apps/apps/onscripter/repo/src/text/FontInfo.cpp` | `b3efaf4520494197b3096411bcfdd0d435aa6be6d5b478d95a110711c514ad76` | `772382d2d82d230976b3860ef061b89ee3722ee95c3593befded1afb6eec47d4` |
| `navy-apps/apps/onscripter/repo/src/system/ONScripter.cpp` | `0b10265ac5884030c90c05864dc5f1be2befe9cded75f4d7f244abd3cf1bce44` | `85ec9afdc34074ba89b08f24b0fedbbe5a59c66d7c11a67e3651798b00f33876` |
| `navy-apps/apps/onscripter/repo/include/ONScripter.h` | `cb798ecf1523e92e951583694b17a50a56d89be72b68bdc10a40b5dc861d6079` | `2b078332e73131ca69c77c244a8a3a5d8b39fbdf3f435aeb563d6003a2e8a312` |

```diff
--- a/navy-apps/libs/libminiSDL/include/sdl-file.h
+++ b/navy-apps/libs/libminiSDL/include/sdl-file.h
@@ -22,6 +22,8 @@
 
 SDL_RWops* SDL_RWFromFile(const char *filename, const char *mode);
 SDL_RWops* SDL_RWFromMem(void *mem, int size);
+/* Both memory constructors borrow the buffer; close frees only the RWops. */
+SDL_RWops* SDL_RWFromConstMem(const void *mem, int size);
 
 #define SDL_RWtell(f)  SDL_RWseek(f, 0, RW_SEEK_CUR)
 #define SDL_RWsize(f)  f->size(f)
--- a/navy-apps/libs/libminiSDL/src/file.c
+++ b/navy-apps/libs/libminiSDL/src/file.c
@@ -6,14 +6,14 @@
 
 static int64_t file_size(SDL_RWops *f) {
   long cur = ftell(f->fp);
-  fseek(f->fp, 0, RW_SEEK_END);
+  if (cur < 0 || fseek(f->fp, 0, RW_SEEK_END) != 0) return -1;
   long size = ftell(f->fp);
-  fseek(f->fp, cur, RW_SEEK_SET);
+  if (fseek(f->fp, cur, RW_SEEK_SET) != 0) return -1;
   return size;
 }
 
 static int64_t file_seek(SDL_RWops *f, int64_t offset, int whence) {
-  fseek(f->fp, (long)offset, whence);
+  if (fseek(f->fp, (long)offset, whence) != 0) return -1;
   return ftell(f->fp);
 }
 
@@ -26,9 +26,9 @@
 }
 
 static int file_close(SDL_RWops *f) {
-  fclose(f->fp);
+  int ret = fclose(f->fp);
   free(f);
-  return 0;
+  return ret;
 }
 
 /* ---- memory-backed RWops: read/write directly on mem.base ----
@@ -115,3 +115,14 @@
   };
   return &m->rw;
 }
+
+static size_t const_mem_write(SDL_RWops *f, const void *buf, size_t size, size_t nmemb) {
+  (void)f; (void)buf; (void)size; (void)nmemb;
+  return 0;
+}
+
+SDL_RWops* SDL_RWFromConstMem(const void *mem, int size) {
+  SDL_RWops *rw = SDL_RWFromMem((void *)mem, size);
+  if (rw != NULL) rw->write = const_mem_write;
+  return rw;
+}
--- a/navy-apps/libs/libSDL_ttf/include/SDL_ttf.h
+++ b/navy-apps/libs/libSDL_ttf/include/SDL_ttf.h
@@ -11,6 +11,7 @@
   long factor;  // this is used as fixedpt type
   int height;
   int ascent, descent;
+  SDL_RWops *src;  // owned only for a successful OpenFontRW with freesrc != 0
 } TTF_Font;
 
 #ifdef __cplusplus
@@ -20,6 +21,7 @@
 int TTF_Init();
 TTF_Font* TTF_OpenFont(const char *file, int size);
 TTF_Font *TTF_OpenFontRW(SDL_RWops *src, int freesrc, int ptsize);
+void TTF_CloseFont(TTF_Font *font);
 int TTF_GlyphMetrics(TTF_Font *font, Uint16 ch, int *minx, int *maxx, int *miny, int *maxy, int *advance);
 int TTF_FontAscent(TTF_Font *font);
 int TTF_FontHeight(TTF_Font *font);
--- a/navy-apps/libs/libSDL_ttf/src/ttf.c
+++ b/navy-apps/libs/libSDL_ttf/src/ttf.c
@@ -1,6 +1,7 @@
 #include <SDL_ttf.h>
 #include <fixedptc.h>
 #include <assert.h>
+#include <limits.h>
 
 #define STB_TRUETYPE_IMPLEMENTATION
 #include "stb_truetype.h"
@@ -10,25 +11,56 @@
 }
 
 TTF_Font* TTF_OpenFont(const char *file, int ptsize) {
-  SDL_RWops *f = SDL_RWFromFile(file, "r");
+  SDL_RWops *f = SDL_RWFromFile(file, "rb");
   if (f == NULL) return NULL;
-  size_t size = SDL_RWsize(f);
-  void *buf = malloc(size);
-  assert(buf);
-  size_t nread = SDL_RWread(f, buf, size, 1);
-  assert(nread == 1);
+  TTF_Font *font = TTF_OpenFontRW(f, 0, ptsize);
   SDL_RWclose(f);
+  return font;
+}
 
-  stbtt_fontinfo *finfo = malloc(sizeof(*finfo));
-  assert(finfo);
-  int ret = stbtt_InitFont(finfo, buf, stbtt_GetFontOffsetForIndex(buf,0));
-  assert(ret == 1);
+static uint32_t font_be32(const uint8_t *p) {
+  return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
+}
 
-  TTF_Font *font = malloc(sizeof(*font));
-  font->finfo = finfo;
-  font->file.buf = buf;
-  font->file.size = size;
-  font->ptsize = ptsize;
+/* Check the outer directory before calling stb. This is not a validator for
+ * arbitrary untrusted font tables; the bundled stb parser has that limitation. */
+static int font_offset(const uint8_t *buf, size_t size) {
+  if (size < 12) return -1;
+  if (font_be32(buf) == 0x74746366) { // TTC
+    if (size < 16) return -1;
+    uint32_t count = font_be32(buf + 8), off = font_be32(buf + 12);
+    if (count == 0 || count > (size - 12) / 4 || off > size - 12 || off > INT_MAX) return -1;
+  }
+  int off = stbtt_GetFontOffsetForIndex(buf, 0);
+  if (off < 0 || (size_t)off > size - 12) return -1;
+  size_t count = (unsigned)buf[off + 4] << 8 | buf[off + 5];
+  if (count > (size - off - 12) / 16) return -1;
+  for (size_t i = 0; i < count; i++) {
+    const uint8_t *table = buf + off + 12 + i * 16;
+    uint32_t start = font_be32(table + 8), len = font_be32(table + 12);
+    if (start > size || len > size - start) return -1;
+  }
+  return off;
+}
+
+TTF_Font *TTF_OpenFontRW(SDL_RWops *src, int freesrc, int ptsize) {
+  uint8_t *buf = NULL;
+  stbtt_fontinfo *finfo = NULL;
+  TTF_Font *font = NULL;
+  if (src == NULL || ptsize <= 0) goto fail;
+  int64_t pos = SDL_RWtell(src), end = SDL_RWsize(src);
+  if (pos < 0 || end < pos || end - pos < 12 || end - pos > INT_MAX) goto fail;
+  size_t size = (size_t)(end - pos);
+  buf = malloc(size);
+  if (buf == NULL || SDL_RWread(src, buf, 1, size) != size) goto fail;
+  int off = font_offset(buf, size);
+  if (off < 0) goto fail;
+  finfo = malloc(sizeof(*finfo));
+  if (finfo == NULL || !stbtt_InitFont(finfo, buf, off)) goto fail;
+  font = malloc(sizeof(*font));
+  if (font == NULL) goto fail;
+  *font = (TTF_Font){ .finfo = finfo, .file = { buf, size }, .ptsize = ptsize,
+                      .src = freesrc ? src : NULL };
 
   // pre-computed data
   fixedpt pixel = fixedpt_muli(fixedpt_rconst(1.333333), ptsize);
@@ -39,11 +71,21 @@
   font->descent = fixedpt_toint(fixedpt_muli(font->factor, font->descent));
 
   return font;
+
+fail:
+  free(font);
+  free(finfo);
+  free(buf);
+  if (freesrc && src != NULL) SDL_RWclose(src);
+  return NULL;
 }
 
-TTF_Font *TTF_OpenFontRW(SDL_RWops *src, int freesrc, int ptsize) {
-  assert(0);
-  return NULL;
+void TTF_CloseFont(TTF_Font *font) {
+  if (font == NULL) return;
+  free(font->finfo);
+  free(font->file.buf);
+  if (font->src != NULL) SDL_RWclose(font->src);
+  free(font);
 }
 
 int TTF_GlyphMetrics(TTF_Font *font, Uint16 ch, int *minx, int *maxx, int *miny, int *maxy, int *advance) {
--- a/navy-apps/apps/onscripter/repo/include/mySDL.h
+++ b/navy-apps/apps/onscripter/repo/include/mySDL.h
@@ -20,8 +20,6 @@
 
 #define SDL_ALPHA_OPAQUE 0
 
-SDL_RWops *SDL_RWFromConstMem(void *buf, int len);
-
 #else
 
 #define DEFAULT_VIDEO_SURFACE_FLAG (SDL_SWSURFACE)
--- a/navy-apps/apps/onscripter/repo/include/FontInfo.h
+++ b/navy-apps/apps/onscripter/repo/include/FontInfo.h
@@ -61,6 +61,7 @@
     FontInfo();
     void reset();
     void *openFont( char *font_file, int ratio1, int ratio2 );
+    static void closeFonts();
     void setTateyokoMode( int tateyoko_mode );
     int getTateyokoMode();
     int getRemainingLine();
--- a/navy-apps/apps/onscripter/repo/src/misc/mySDL.cpp
+++ b/navy-apps/apps/onscripter/repo/src/misc/mySDL.cpp
@@ -6,9 +6,4 @@
   return 0;
 }
 
-SDL_RWops *SDL_RWFromConstMem(void *buf, int len) {
-  assert(0);
-  return NULL;
-}
-
 #endif
--- a/navy-apps/apps/onscripter/repo/src/text/FontInfo.cpp
+++ b/navy-apps/apps/onscripter/repo/src/text/FontInfo.cpp
@@ -26,6 +26,8 @@
 #include "Utils.h"
 #include <stdio.h>
 #include <string.h>
+#include <stdlib.h>
+#include <limits.h>
 #include "mySDL.h"
 
 
@@ -34,11 +36,6 @@
     int size;
     TTF_Font *font[2];
 
-    FontContainer(){
-        size = 0;
-        next = NULL;
-        font[0] = font[1] = NULL;
-    };
 } root_font_container;
 
 char *FontInfo::cache_font_file = NULL;
@@ -85,33 +82,49 @@
         fc = fc->next;
     }
     if ( !fc->next ){
-        fc->next = new FontContainer();
-        fc->next->size = font_size;
-        SDL_RWops *fp;
+        if (font_size <= 0 || ratio1 <= 0 || ratio2 <= 0) return NULL;
+        int64_t scaled = (int64_t)font_size * ratio1 / ratio2;
+        if (scaled <= 0 || scaled > INT_MAX) return NULL;
+        FontContainer *next = (FontContainer *)malloc(sizeof(*next));
+        if (next == NULL) return NULL;
+        *next = FontContainer{NULL, font_size, {NULL, NULL}};
         bool useFile = (cache_font_file == NULL || strcmp(cache_font_file, font_file) != 0);
-        if (useFile) {
-          fp = SDL_RWFromFile(font_file, "r");
-        } else {
-          fp = SDL_RWFromConstMem(font_cache, font_cache_size);
-        }
-        if ( fp == NULL ) return NULL;
-        fp->close(fp);
-        if (useFile) fc->next->font[0] = TTF_OpenFont(font_file, font_size * ratio1 / ratio2);
-        else fc->next->font[0] = TTF_OpenFontRW(SDL_RWFromConstMem(font_cache, font_cache_size), 1, font_size * ratio1 / ratio2);
+        if (useFile) next->font[0] = TTF_OpenFont(font_file, (int)scaled);
+        else next->font[0] = TTF_OpenFontRW(SDL_RWFromConstMem(font_cache, font_cache_size), 1, (int)scaled);
+        if (next->font[0] == NULL) { free(next); return NULL; }
 #if (SDL_TTF_MAJOR_VERSION>=2) && (SDL_TTF_MINOR_VERSION>=0) && (SDL_TTF_PATCHLEVEL>=10)
-        if (useFile) fc->next->font[1] = TTF_OpenFont(font_file, font_size * ratio1 / ratio2);
-        else fc->next->font[1] = TTF_OpenFontRW(SDL_RWFromConstMem(font_cache, font_cache_size), 1, font_size * ratio1 / ratio2);
-        if (fc->next->font[1] == nullptr) {
-            utils::printError("Open font failed: %s\n", TTF_GetError());
-        }
-        TTF_SetFontOutline(fc->next->font[1], 1);
+        if (useFile) next->font[1] = TTF_OpenFont(font_file, (int)scaled);
+        else next->font[1] = TTF_OpenFontRW(SDL_RWFromConstMem(font_cache, font_cache_size), 1, (int)scaled);
+        if (next->font[1] == NULL) {
+            TTF_CloseFont(next->font[0]);
+            free(next);
+            return NULL;
+        }
+        TTF_SetFontOutline(next->font[1], 1);
 #endif
+        fc->next = next;
     }
 
     ttf_font[0] = (void*)fc->next->font[0];
     ttf_font[1] = (void*)fc->next->font[1];
     
     return fc->next->font;
+}
+
+void FontInfo::closeFonts()
+{
+    FontContainer *fc = root_font_container.next;
+    root_font_container.next = NULL;
+    while (fc != NULL) {
+        FontContainer *next = fc->next;
+        TTF_CloseFont(fc->font[0]);
+        TTF_CloseFont(fc->font[1]);
+        free(fc);
+        fc = next;
+    }
+    cache_font_file = NULL;
+    font_cache = NULL;
+    font_cache_size = 0;
 }
 
 void FontInfo::setTateyokoMode( int tateyoko_mode )
--- a/navy-apps/apps/onscripter/repo/src/system/ONScripter.cpp
+++ b/navy-apps/apps/onscripter/repo/src/system/ONScripter.cpp
@@ -26,6 +26,7 @@
 #include "Utils.h"
 #include "coding2utf16.h"
 #include <stdlib.h>
+#include <limits.h>
 
 extern Coding2UTF16 *coding2utf16;
 extern "C" void waveCallback(int channel);
@@ -141,6 +142,7 @@
 ONScripter::ONScripter()
 {
     is_script_read = false;
+    cacheFont = false;
 
     cdrom_drive_number = 0;
     cdaudio_flag = false;
@@ -180,6 +182,14 @@
 
     delete[] sprite_info;
     delete[] sprite2_info;
+    FontInfo::closeFonts();
+    free(font_cache);
+    while (retired_font_caches != NULL) {
+        RetiredFontCache *next = retired_font_caches->next;
+        free(retired_font_caches->buf);
+        free(retired_font_caches);
+        retired_font_caches = next;
+    }
 }
 
 void ONScripter::enableCDAudio(){
@@ -388,14 +398,40 @@
             utils::printError("can't open font file: %s\n", font_file);
             return -1;
         }
-        int size = fontfp->seek(fontfp, RW_SEEK_END, 0);
-        fontfp->seek(fontfp, RW_SEEK_SET, 0);
-        font_cache = malloc(size);
-        fontfp->read(fontfp, font_cache, 1, size);
-        fontfp->close(fontfp);
+        int64_t size = fontfp->seek(fontfp, 0, RW_SEEK_END);
+        if (size <= 0 || size > INT_MAX || fontfp->seek(fontfp, 0, RW_SEEK_SET) != 0) {
+            fontfp->close(fontfp);
+            utils::printError("invalid font file size: %s\n", font_file);
+            return -1;
+        }
+        void *next_cache = malloc((size_t)size);
+        if (next_cache == NULL || fontfp->read(fontfp, next_cache, 1, (size_t)size) != (size_t)size) {
+            free(next_cache);
+            fontfp->close(fontfp);
+            utils::printError("can't read font file: %s\n", font_file);
+            return -1;
+        }
+        if (fontfp->close(fontfp) != 0) {
+            free(next_cache);
+            utils::printError("can't close font file: %s\n", font_file);
+            return -1;
+        }
+        // Existing FontRW sources borrow earlier cache buffers until close.
+        RetiredFontCache *retired = NULL;
+        if (font_cache != NULL) {
+            retired = (RetiredFontCache *)malloc(sizeof(*retired));
+            if (retired == NULL) {
+                free(next_cache);
+                return -1;
+            }
+            retired->buf = font_cache;
+            retired->next = retired_font_caches;
+        }
+        font_cache = next_cache;
         FontInfo::cache_font_file = font_file;
         FontInfo::font_cache = font_cache;
-        FontInfo::font_cache_size = size;
+        FontInfo::font_cache_size = (int)size;
+        if (retired != NULL) retired_font_caches = retired;
     }
 
     if ( sentence_font.openFont( font_file, screen_ratio1, screen_ratio2 ) == NULL ){
--- a/navy-apps/apps/onscripter/repo/include/ONScripter.h
+++ b/navy-apps/apps/onscripter/repo/include/ONScripter.h
@@ -740,6 +740,11 @@
     AnimationInfo sentence_font_info;
     char *font_file;
     void *font_cache = NULL;
+    struct RetiredFontCache {
+        void *buf;
+        RetiredFontCache *next;
+    };
+    RetiredFontCache *retired_font_caches = NULL;
     int erase_text_window_mode;
     bool text_on_flag; // suppress the effect of erase_text_window_mode
     bool draw_cursor_flag;
```


Diff覆盖10个实际功能文件，完整hunk不省略。旧音频改动保持且不在本轮修复patch；根与嵌套仓库实际提交状态分别记录，根文档提交不能替代嵌套源码提交。diff空上下文行的单个空格保持证据原样，仅正文需无尾随空白。

限制：外层字体目录检查不是完整不可信字体验证，stb内部复杂表仍沿原安全边界；不扩outline/任意字体集合/完整SDL错误消息。多次engine成功重载会将旧cache保留到engine析构，以满足仍存活字体源的借用生命周期；必要释放接口/退出释放段已定向执行，未在缺资源的完整游戏中实测析构。FontInfo原字体池按size索引，不增加任意运行时不同font路径切换契约。

测试准备的一个早期unit build目录在扩展夹具时直接再生，未先落逐文件删除哈希，旧临时二进制身份Unknown；仅此准备目录的日志/命令仍在pre-expanded，不能将最终清理清单虚构为覆盖该次历史重建。最终同版证据/正式资产和后续所有保留构建树按下节清单收尾，可由明确基线/配方复现。


## 本轮完成与清理回执

56项收尾核对通过（不是56个独立功能用例）：10个最终生产输入和实际消费者副本相同、普通/ASan/RV64结果、完整diff正反及8正式资产保持。构建、guest和观察进程已结束后，按cleanup-plan/receipt删除9544路径（9499普通文件、45个symlink），515,887,671字节；不跟随目录symlink，0 tracked/正式资产删除。最终十份before及重建源码、隔离Navy/AM/nanos/NEMU工程、编译/磁盘夹具、已目视截图和observer.so清理完毕；日志、JSON、最小测试/生成配方、完整修复patch及原嵌套音频baseline patch保留，无剩余o/a/ELF/bin/so/img/BMP/PNG。早期重建缺删除哈希的例外已在上节单独记录，未混入本清单。

清理后十源新SHA和八正式资产再次匹配，根HEAD仍5a48a8f、ONS嵌套HEAD仍6326adf，两个index均空。根仓四共享库功能文件和本批报告/导航未提交；ONS六功能文件未提交，ONScripter.cpp还含早于本批的音频改动，不能把整个嵌套diff当本批修复。将来提交需按仓库和实际新hunk分别归属，原音频差异另保留/按其原授权处理，不以根文档commit代替嵌套源码commit。

本轮修复结果用户确认/commit Pending，无安装/commit/push。必要接口已按用户批准范围落地，无新的本批策略阻塞；唯一未来入口TASK_QUEUE#crp-next先等待本批结果确认/提交，F0110 NWM状态/EOF必要分析仅Planned未Start，M2不变。Ignored原始证据/.agent不随普通Git提交备份。

<a id="resource-recheck-20261021"></a>
## 资源与磁盘结论更正（2026-10-21）

用户质询“完整游戏缺什么资源？onscripter不是已经编译进磁盘了吗”。定向复核发现，先前只检查`fsimg/share/games`与`share/fonts`，漏查`fsimg/`根目录；“未提供ONS脚本/default.ttf”“完整游戏因缺资源NotRun”的判断错误，现撤回。此为既有完成报告的事实勘误，不改变源码修复、原测试实绩或确认/提交状态，不开始下一单元。

| 盘内路径 | 字节数 | 当前证据 |
|---|---:|---|
| `/bin/onscripter` | 745984 | ONS可执行文件，当前盘内仍为旧实现 |
| `/nscript.dat` | 216962 | 游戏脚本；ScriptHandler原代码支持读取该文件 |
| `/default.ttf` | 3917384 | ONS默认字体 |
| `/arc.nsa` | 106999077 | 1015个资源条目：784 OGG、230 PNG、1 DAT |
| `/arc1.nsa` | 295964 | 46个PNG条目 |
| `/envdata` | 51 | 已有环境数据 |

六文件均以`navy-apps/build/ramdisk.h`记录的size/offset直接读取`ramdisk.img`，与fsimg源文件逐字节相等；nanos-lite的files.h与该header字节一致，build/ramdisk.img链接指向同一镜像。两个NSA目录解析到的末端均等于数据基址，1061个条目的存储区间均在各自文件内。这证明程序及上述资源已打包；不据此宣称任意分支的每个资源引用都已覆盖，更没有已确认的缺失资源清单。

对盘内可执行文件反汇编，`TTF_OpenFontRW`仍直接调用`__assert_func`（旧ttf.c第45行），证明它不是本轮修复版。先前`ons-final-build.log`只到`LD -> build/onscripter-riscv64`；命令为`make ... app`，没有install。Navy默认APPS列表也不含ONS。标准update→run实际运行的是PAL/NTerm/nslider，不能算修复版ONS已打包/运行。

因此完整游戏与实际`--fontcache`场景保持**NotRun**，正确理由为**本轮尚未将修复版ONS安装打包并启动真实游戏**；不是缺少游戏资源，也不虚构另一项阻塞。补充验证若执行，应沿本批范围使用现有资源做修复版实际运行；本次仅回答/更正资源事实，未新增构建或guest运行、未提交。

证据为`local/resource-recheck-20261021/audit.py`、`result.json`与`packed-openfontrw-disassembly.txt`：全部只读检查现有正式资产，无副本/二进制产物需清理。初版审计夹具按ASCII解码整个文件名，遇归档中非ASCII字节而停止；修正为按原字节保留名称、只统计ASCII后缀后复核通过，未改生产代码。原分析/实施manifest及完成快照保留不重写，追加本附记纠正其资源判断；十源及八正式资产保持，修复结果确认/root与ONS nested commit仍Pending。


<a id="game-run-20261021"></a>
## 从NTerm启动真实ONS的补充验证计划（2026-10-21）

用户“尝试执行，在nterm输入其对应路径即可执行”明确授权本批补充真实游戏验证。原F0107/F0108已完成、F0110尚未开始，本次验证属于原目标与验收范围，按Reopen处理；原完成快照不覆盖。当前源码/八正式资产先核身份，隔离复制现有Navy/AM/nanos/NEMU及游戏资源，禁止下载或改正式镜像。

复用既有构建入口，先在隔离ONS目录以ISA=riscv64/VME=1执行install，明确将本轮十源修复编入新应用；随后隔离nanos执行标准update→run。通过原SDL事件队列按F2切换NTerm，逐键输入/bin/onscripter --fontcache并Return；观察真实exec、字体缓存日志、游戏画面/字形及必要按键反馈。验收区分已启动/缓存路径已执行/进入游戏与完整流程通关，不以构建或固定等待代替通过；若失败记录首个实际断点，仅进行范围内定位，不擅自扩新能力/策略。

交付为本节补充结果、local/game-run-20261021下命令/输入/日志/截图hash/产品身份与清理回执，更新records索引和状态；截图须目视检查后按既有清理规则删除，原测试不无故重跑。无安装新软件/系统修改/commit/push/下一组授权；验证、留档、清理后停止。


<a id="game-run-result-20261021"></a>
## 从NTerm真实启动的补充结果（2026-10-21）

**本次尝试Completed；完整游戏Attempted / 未通过，结果确认及root/ONS nested commit Pending。** 用户明确要求尝试执行，按原组范围Reopen后补充验证；本节是原implementation完成快照的Supplemental，不改写先前实绩，不开始F0110/M2。正式生产十源未新增修改，诊断差异仅存在于隔离副本并已随产物清理。

### 实际安装、打包和启动

隔离复制当前Navy/AM/nanos/NEMU与已有游戏资源，排除Git/build并重映射绝对symlink。源/工具均已存在，无下载/新软件安装。先在隔离`navy-apps/apps/onscripter`执行`make --no-print-directory -j4 ISA=riscv64 VME=1 install`（exit0，10.34秒），再在隔离nanos-lite执行`make --no-print-directory -j4 ARCH=riscv64-nemu git_commit= update`（exit0，22.57秒）；运行仍用同参数`run`，未修改原Make目标/APPS/日常流程。

首次可执行文件大小/偏移/hash见local/game-run-20261021/preflight.json；已逐字节确认built ELF等于fsimg安装文件和新磁盘区间，包含新增TTF_CloseFont符号，十个修复源码与已验收新SHA及实际消费者副本一致。此轮已补上“仅app链接而未install”的遗漏；正式ramdisk和正式fsimg均未覆盖。

宿主观察helper仅将按键送入真实SDL队列并保存原texture帧；通过原NEMU键盘MMIO→nanos→NTerm路径，F2切换终端，逐键输入完整路径/参数并Return。截图目视确认命令完整；串口出现新的context_uload入口、ONS版本、800x600显示和音频初始化日志。四次均用SDL dummy后端及宿主观察库，不声称真实屏幕/音频听感通过。

| 实际运行 | 源码/命令 | 观察结果与结束 |
|---|---|---|
| cached-01 | 本轮原样十源，`/bin/onscripter --fontcache` | 109.62秒；游戏阶段hello89→305，黑底小白鼠标框；Enter/Space后无画面变化 |
| diagnostic-01 | 隔离ONS副本仅加初始化阶段输出，同上命令 | 55.86秒；明确cache size=3917384及first font opened，随后黑底鼠标框 |
| diagnostic-debug-01 | 隔离副本阶段输出+启用原debug_level，同上命令 | 45.35秒；完整日志执行到start首行全角空格文本，未见后续图片命令 |
| default-01 | 恢复原样十源，`/bin/onscripter` | 41.75秒；hello86→116，仍同一黑底鼠标框 |

默认对照前已删除隔离诊断语句、重建install/update，十源SHA恢复且ELF SHA与首次未加诊断的修复版相同。两次原样运行未出现BAD TRAP/断言/ABORT/进程早退，四次均由自有进程组SIGTERM结束（make -15），**不是guest正常退出**。runner的error=null仅表示输入/采集完成，不表示游戏PASS。

### 最终停点与证据范围

两个诊断副本的patch分别留在diagnostic-only.patch和diagnostic-debug.patch，未混入本批生产repair.patch。诊断执行真实引擎、已有脚本/字体/NSA：缓存完整读取3917384字节，缓存分支返回，首次FontInfo字体打开成功；这些里程碑来自明确加输出的运行，不能冒充原样版自身输出。原样版启动和黑屏则有独立实际执行证据。

完整debug日志最后为`executeLabel start:1/7`与`ONScripter::Parseline`后的GBK A1 A1（全角空格）。对应nscript.dat的`*start`下一行是该文本，后面才是`lsp 201,"pic\system\S_TT_WAR00.png"`；源码parseLine将文本交给textCommand。先前只见增量日志时暂定位在define/game，后续完整日志已推翻该中间判断；本节以**start首行文本处理停点**为准，尚未定位到该函数内部的确定根因。

日志另有默认回看光标uoncur/uoffcur/doncur/doffcur.bmp以及cursor0/1.bmp查找失败；之后引擎仍进入start，不能仅凭这些输出认定它们造成黑屏，亦不补造资源或修改脚本绕过。尚未做旧版相同场景对照，不能从默认启动同样黑屏推出共享TTF修改必然无关。字体对象成功打开不等于中文字形/文本/游戏流程通过，缺失的验收是可见标题、对白及实际交互推进，不能记成NotRun或完整游戏PASS。

29张图（27原帧、2接触表）清理前完成目视：终端命令与黑底小白鼠标框可辨；四次所有游戏阶段帧hash相同，没有标题、图片或可读对白。图片清理后仅保留hash和文字观察。读入、释放、重载等此前模块/ASan/RV64测试不无故重跑，旧结论继续保留；本次不新增生产修复或扩大缓存接口契约。

### 收尾、恢复和停点

local/game-run-20261021保留prepare-runtime.py、run-game/run-trace/run-debug/run-default、observe_sdl.c、verify/cleanup配方、每次build命令/日志、输入队列/串口/结果、两份隔离诊断patch、原样源/ELF身份、validation及visual-review。复现须将这些最小配方放入新的证据目录再构建，避免覆盖原日志；prepare从现有主工作区源码/资源复制，首次install→update→run及后续诊断的准确命令/字段见JSON。一次诊断脚本在准备结束前误启动报文件未生成，等待构建完成后重试；验证脚本初用UTF-8遇GBK字节失败，改按实际编码/保留原字节，最终还拒绝了错误的define/game停点假设，原日志均保持。

全部自有进程结束后，按cleanup-plan逐路径记录hash/字节再删除9421路径397677913字节，包括隔离工程/编译物/磁盘/观察库/29图；不跟随目录symlink，0 tracked/正式资产删除。清理后十生产新源及八正式资产复核保持；原分析36、实施148及资源复核4项manifest保持，无新增产品构建物或源码快照遗留。

本次重新完成已同步CURRENT_STATE/TASK_QUEUE并追加Supplemental完成快照；用户结果确认、root及ONS nested commit仍Pending，原ONS音频差异保持且不混入本批patch。后续若授权继续定位，应沿本批start文本/事件/字形链排查；当前不自行修新问题/改脚本、不commit/push或开始下一组/M2。Ignored证据/.agent仍需本地保管，Git提交不等于备份。


<a id="input-run-20261021"></a>
## 真实外设输入推进补充计划（2026-10-21）

用户明确要求通过注入空格或其他外设输入验证进入下一画面；原组已完成、下一F0110未开始，按同组Reopen补充。复用隔离复制/新ONS install/标准nanos update→run与真实SDL队列，保留旧证据。此次先核源/输入映射，实际注入分离的keydown/keyup（避免仅瞬时按键）、Space/Return/方向键及当前引擎支持的Ctrl跳过；观察画面与脚本进度。必要时只在隔离副本输出guest接收/模式/事件拒绝原因，不改变生产处理语义或游戏资源；鼠标如无现有硬件通路则不伪称注入成功。

验收是命令/真实输入到达及可见下一画面，若不能推进则保留具体停点与输入未生效的证据，不把宿主入队当guest消费或游戏PASS。交付local/input-run-20261021输入/命令/串口/帧hash/诊断patch及结果，目视/留档后按既有规则清理隔离工程和图片；本轮尝试完成后再Completion并停止，无生产修复/安装软件/commit/push/下一组授权。


<a id="input-result-20261021"></a>
## 真实键盘输入推进成功（2026-10-21）

**本次输入验证Completed / PASS：已进入下一画面和标题菜单。** 用户要求注入空格或其他外设输入，并补充此前手动运行显示过画面；在同组Reopen后，以本轮未加诊断的原样十源修复版，独立重现了从黑屏到制作信息、再到《planetarian／星之梦》标题菜单。旧完成/黑屏快照不改写，由本补充更新当前验收，不开始F0110/M2。

### 实际输入和画面

复用local/game-run-20261021配方，在新的local/input-run-20261021隔离复制工程/已有游戏资源，ONS `make -j4 ISA=riscv64 VME=1 install`与nanos标准`make -j4 ARCH=riscv64-nemu git_commit= update`均成功，后者21.52秒。built/安装ELF/盘内区间字节相同；十源与已验收SHA和正式源码一致。再通过标准run、F2切NTerm，输入`/bin/onscripter --fontcache`并Return。

本轮host helper沿原SDL队列/NEMU键盘MMIO/nanos/NTerm和游戏输入链，增加独立down/up命令；LCTRL明确映射SDL_SCANCODE_LCTRL=224。helper没有修改guest内存或事件处理结果。Space/Return/方向键按下约0.5秒后松开；Ctrl按下约0.7秒再松开，间隔观察。整个运行84.70秒，游戏阶段后台hello89→259，无断言/BAD TRAP；最终仍为自有SIGTERM/-15，非guest正常退出。

| 采集时刻/操作 | 实际可见结果 |
|---|---|
| 31.83秒，启动后 | 黑底小白鼠标框 |
| 两次Space、两次Return、Right/Down | 本次采集仍为相同黑屏 |
| 连续Ctrl按下/松开序列，第4次后采集（68.48秒） | 人物及中文化/KEY FANS CLUB制作信息画面 |
| 六次Ctrl序列后，再输入Down/Return并观察至84.69秒 | 《planetarian／星之梦》标题菜单：翻开封面、查阅目录/书签、CG鉴赏、音乐鉴赏、结束 |

这描述实测顺序，不宣称必须四次Ctrl或最后Down/Return单独造成标题出现；资源解码/转场耗时也在观察间隔内。宿主入队回执之外，游戏实际加载并显示两张后续图片，证明本轮输入链能够推进引擎。早先只试Space/Return未推进，不能推广成无法输入或无法显示游戏；本轮没有修游戏代码/脚本、跳转PC或直接注入结束等待的内部事件。

### 真实性核验与边界

制作信息与标题帧均已目视。再只读解析现有arc.nsa中的`pic\system\s_tt_war00.png`及`pic\system\title.png`，对照原始帧：直接逐像素有差异，经同一254/256淡入系数后，480000像素分别匹配479952/479936，剩余48/64像素与左上8×8假鼠标框区域相符。该系数为图像比较实测拟合，不冒充来自引擎内部状态；raw差异与拟合值均保留于resource-frame-comparison.json。帧未被修改后冒充guest输出。

verify.py核对运行标记、按键入队结果/非零scancode、三种实际画面hash及后台推进；故意替换为全黑帧、移除ONS启动标记、加入BAD TRAP三种假PASS均被拒绝。标题与制作信息中的文字来自图片，不能据此宣称动态TTF中文对白或完整通关/音频听感通过。完整缓存读取和首次字体打开仍引用上轮明确标识的诊断实绩，本轮额外证明真实缓存启动能到游戏标题菜单。

源码静态阅读另见miniSDL `push_event`拒绝`type > SDL_USEREVENT`，而ONS使用`SDL_USEREVENT+5`等事件；这仍只是本轮未动态验证的定时/事件兼容线索，不能把它当成已证实的黑屏根因或用户手动不能运行的证据。Ctrl处理本身已有退出等待/跳过逻辑，本轮仅使用现有外设输入。鉴于下一画面目标已达到，没有继续加诊断或擅自修新事件接口。

### 收尾与恢复

19张图（17原帧及2转换/接触表）清理前完成目视，保留visual-review的hash和文字；原样输入脚本/host观察源/prepare/verify/cleanup、build与run命令/输入/日志/JSON、preflight、resource-frame-comparison及validation在local/input-run-20261021。复现须复制最小配方到新的证据目录，避免覆盖本轮日志；资源由主工作区既有fsimg提供，无下载。原analysis36/implementation148/resource-recheck4/game-run54项manifest保持。

进程结束后逐路径盘点hash/字节再清理9411路径378899203字节（含隔离工程/镜像/库/19图），不跟随目录symlink、0 tracked/正式资产删除；十生产源/八正式资产保持。root HEAD5a48a8f、ONS nested6326adf及原音频差异保持，index空，无新生产修改/软件安装/commit/push。本次Supplemental重新完成、结果确认及root/ONS nested commit仍Pending；唯一TASK_QUEUE#crp-next先等待本批确认/提交，F0110未开始/M2不变。Ignored原始证据/.agent不等于Git备份。


<a id="submit-20261021"></a>
## 用户确认与本批精确提交（2026-10-21）

用户最新“提交”确认本批已报告源码修复/补充验证并授权归属明确的root和ONS nested提交，不授权push或执行下一单元。复用原Completed/Supplemental与清理，无新产品测试、构建或guest；十源/八正式资产及原36+148+4+54+24=266个证据文件SHA保持，完整内嵌repair.patch保持。此次只补确认、提交前身份/范围核对、实际回执及下述归属更正，不重复完成快照。

**既有差异归属更正**：提交时逐字节检查发现，nested-preexisting.patch实际只包含`DEFAULT_ENV_FONT`由原GBK字节CB CE CC E5变成四个U+FFFD替代字符的编码行；本轮未改变该工作区字节。音频错误传播修复早已在旧HEAD `6326adf488985b9752fab47833a8acd0f9264e15`中提交。因此此前把这个未提交patch叫作“原音频差异”不准确，现撤回该分类；原patch/manifest和历史快照保留。技术修复diff始终基于实际旧源生成，排除了这条既有差异，原功能改动归属未扩大。

ONS六源实际提交为`5e72dbb9739ae39a3a2dc520ed89f20219e92f84`（父`6326adf488985b9752fab47833a8acd0f9264e15`，83增35删）。五文件按已验收工作区字节暂存；ONScripter.cpp在index中只暂存字体修复，把该既有编码行保留HEAD原字节，工作区仍保留用户原差异。逐文件校验暂存blob及路径，提交后仅余该行1增1删、index空。新增提交不包含已在旧HEAD中的音频修复或该编码变化。

根仓只提交miniSDL/TTF四功能文件、本报告/.gitignore及process/repair-status两索引，共八路径。原根HEAD为`5a48a8ffcf3dbc81ae752231e623fc06339917c3`；本报告随根修复提交，实际完整新commit/mode/blob/路径回执见local/submit-20261021。一次性测试/采集脚本、日志/JSON、已清理镜像/截图及.agent不加跟踪，不改ignore政策。

当前工作源码与原验收SHA保持；nested HEAD与工作区之间仅上述未提交编码行不同，不把两者说成整文件字节相同或宣称重测了新HEAD。原已验证范围为模块/生命周期、真实RV64字体与共享消费者，以及原样修复版真实键盘推进到制作信息/标题菜单；不扩为完整通关/音频/动态中文对白或事件接口修复通过。

复用precheck、nested-staged.patch/nested-commit、root暂存/实际提交及最终receipt/manifest，更新状态/唯一入口后停止，不push或开始F0110/M2。Ignored证据/.agent仍需本地保管，Git提交不代表备份。会话建议：建议开启新对话；本组已积累多轮资源勘误和真实输入证据，下一单元将转入NWM，恢复入口已整理。
