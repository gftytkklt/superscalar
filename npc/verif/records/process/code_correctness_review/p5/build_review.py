#!/usr/bin/env python3
"""Persist P5 responsibility records; preserve original row IDs and other phases."""
from pathlib import Path
import collections,gzip,hashlib,json,re,struct,subprocess
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());B=H.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
original=[json.loads(x) for x in gzip.decompress((H/'coverage.before.jsonl.gz').read_bytes()).decode().splitlines()]
def selected(r):return r.get('review_scope')!='Excluded' and ('CCR-P5' in r.get('effective_phase_responsibilities',{}) or r.get('effective_phase')=='CCR-P5')
files=[r for r in original if selected(r) and r['row_kind']=='file']; branches=[r for r in original if selected(r) and r['row_kind']!='file']
new=[]
def finding(title,severity,status,locs,basis,actual,reach,validation,fix,limit='仅审阅，未修改生产源码；没有RV64 guest或硬件运行。'):
    item={'id':f'CCR-F{33+len(new):04d}','title':title,'severity':severity,'status':status,'phase':'CCR-P5','locations':[],'expected_contract_and_basis':basis,'actual_and_root_cause':actual,'reachability_and_impact':reach,'validation':validation,'minimal_fix':fix,'recommended_regression':'覆盖所列触发、正常对照、零/末端/失败状态；隔离复验两平台相关路径。','unconfirmed_assumptions_and_limits':limit,'evidence':['P5.md','AM_RUNTIME.md','p5/file-review.jsonl','p5/probe-results.json','p5/supplement-results.json','p5/final-probe-results.json']}
    for path,needles in locs:
        lines=(R/path).read_text(errors='replace').splitlines();nums=[i+1 for i,l in enumerate(lines) if any(n in l for n in needles)]
        assert nums,(path,needles)
        item['locations'].append({'path':path,'lines':nums,'sha256':sha(R/path)})
    new.append(item)
K='abstract-machine/klib/src/';N='abstract-machine/am/src/platform/nemu/ioe/';P='abstract-machine/am/src/riscv/npc/';RT='rt/bsp/abstract-machine/';AT='am-kernels/tests/'
EXCLUDED='am-kernels/tests/riscv-tests/debug/bin/RTOSDemo32.axf'
EXCLUSION='S06 already excludes non-RV64 target implementations/artifacts; ELFCLASS32/EM_RISCV, used only by debug/targets/RISC-V/spike32.py; RV64 spike64.py uses RTOSDemo64.axf. P1 profile retention corrected; identity/hash retained, not counted reviewed.'
finding('strncpy在长度边界越读且不完成零填充','Medium','Confirmed',[(K+'string.c',['while((src[i]','if(i<n)'])],
 'klib.h的libc兼容接口；N1570 §7.24.2.4。','先求src[i]再检查i<n；短串仅补一个NUL，余下n字节未清。','非NUL结尾的n字节源是合法输入；n=0也先读src[0]。短串输出残留旧字节。','strncpy-bound.log ASan越读退出1；strncpy-pad.log=61 00 5a 5a 5a，期望61 00 00 00 00。','先检查长度，复制到首NUL后填满剩余n字节；保持返回dst。')
finding('格式转换属性取自转换字符之后的字节','Medium','Confirmed',[(K+'stdio.c',["switch (*tmp++)","info->issigned =","info->isupperdigit ="])],
 '实现明确支持d/i/u/x/X；N1570 §7.21.6.1。','switch已推进tmp，后续用*tmp识别u/X，属性取自后一个字符。','%X输出小写；%du的d会受尾随u影响，合法格式含普通尾字符即触发。','format.log：%X 0xab→ab而非AB；%du -7→18446744073709551609u而非-7u。','保存当前转换符后再推进指针，用该转换符决定属性。')
finding('整数格式化未取负数幅值且无符号参数沿有符号通路扩展','Medium','Confirmed',[(K+'stdio.c',['unsigned long val_abs','long val_num =','va_arg(ap, long)'])],
 'N1570 §7.21.6.1/§7.16.1.1；RV64 int32/long64，unsigned32参数需按32位解释。','负数只加负号，val_abs仍是补码转unsigned long；%x/%u取int后扩展为long；%p也按long取参而非void*。','-7被转成2^64-7的十进制数再加负号；%x 0x80000000u被符号扩展成64位。','format.log %x实际ffffffff80000000，期望80000000；format-negative.log还触发内部越界。','按转换类型取int/unsigned/long/unsigned long/void*；在无符号域求幅值，处理MIN及符号补零位置。')
finding('格式化内部21字节数字缓冲装不下RV64八进制结果','Medium','Confirmed',[(K+'stdio.c',['char numstr[21]','*p++ = usestr','*p ='])],
 '支持%lo且long64；N1570 §7.21.6.1；64位八进制最多22位加NUL。','numstr固定21字节，num2str无容量参数。sink截断在数字转换之后，不能保护内部栈。','snprintf(out,2,"%lo",ULONG_MAX)是合法调用也会越界；负数错误转换另外放大越界。','format-octal.log UBSan在stdio.c数字写入报insufficient space，退出1。','按最大位数+符号/前缀/NUL定容量或逐字符产生数字；回归目标LP64所有radix。')
finding('malloc无对齐和容量检查并越过公开heap边界','High','Confirmed',[(K+'stdlib.c',['void *malloc','void *addr = heap.start','heap.start += size'])],
 'TRM heap有效区间；klib libc兼容分配，N1570 §7.22.3。不依赖是否批准free为空。','直接按字节推进全局heap.start，未对齐、未检查剩余容量或加法溢出，耗尽也返回非NULL。','malloc(1)后malloc(8)地址不满足uint64_t对齐；默认NPC32KiB堆下locality链表请求64KiB+32仍被接受。','malloc.log：offsets0/1/9，第二块mod8=1，申请累计89而heap容量64，返回均非NULL。','独立cursor；按目标所需对齐，先减法检查容量/溢出，失败返回NULL并保留cursor。')
finding('atoi忽略正负号和非空格空白','Low','Confirmed',[(K+'stdlib.c',['int atoi','while (*nptr'])],
 'klib.h libc兼容声明；N1570 §7.22.1.2/strtol基本十进制词法。','仅跳ASCII空格后读数字，不识别+/-与tab等空白。','合法且int可表示的-12、+12、tab12返回0，影响参数解释。溢出输入本就不要求定义结果。','atoi.log含正常123/空串/尾字母对照，三种符号空白例均返回0。','处理标准空白与单一可选符号，再在可表示范围内转换。')
finding('64位有符号除余辅助函数在合法MIN操作数上溢出','Low','Confirmed',[(K+'int64.c',['a = (a ^ s_a)','b = (b ^ s_b)','b = (b ^ s)','a = (a ^ s)'])],
 'N1570 §6.5与编译器64位signed divide/remainder ABI；MIN/1及MIN%1均有定义。','在signed di_int中通过(x^sign)-sign求绝对值；MIN产生有符号溢出。','显式调用__divdi3(MIN,1)、__moddi3等；当前RV64G普通64位表达式通常用硬件DIV，不推定普通程序必经该helper。','int64-min.log UBSan退出1；int64.log普通signed、10056 unsigned向量和64位bit-count通过。','在无符号域形成绝对值及商/余数符号；除0与MIN/-1按既定编译器ABI单独定义。')
finding('C++局部静态初始化辅助符号不满足编译器ABI','Low','Confirmed',[(K+'cpp.c',['void __dso_handle','void __cxa_guard_acquire','void __cxa_guard_release'])],
 '当前C++17 flags未禁用threadsafe-statics；Itanium C++ ABI §3.3.2的guard接口；实际RV64 G++调用证据。','acquire定义void空函数、release不置guard，__dso_handle是函数而非对象。RV64 acquire仅ret保留a0指针。','编译器生成的局部静态动态初始化会每次再走make，guard永不完成；不要求完整异常/析构支持才能确认。','cpp-guard-disasm.log展示读guard/调用/测a0；cpp-stub-disasm.log两个helper仅ret。未执行RV64 C++ guest。','实现匹配签名和guard首字节协议；明确dso_handle对象及析构能力；不以空stub承诺完整C++运行时。')
finding('NEMU GPU在像素写入之前提交sync','Medium','Confirmed',[(N+'gpu.c',['if (ctl->sync)','outl(SYNC_ADDR','outl(FB_ADDR'])],
 'ics2024 §2.5 AM_GPU_FBDRAW：本次矩形更新后同步；已有slider/litenes以同一调用draw+sync。','先outl(SYNC_ADDR,1)，后才遍历写像素。异步device_update可在中间消费sync。','合法非空矩形且sync=true；屏幕可能显示旧帧或部分新帧，本调用结束后没有新的sync。','device-gpu.log记录sync事件位于第0个像素写之前；未运行真实GUI。','把sync提交放在矩形写入之后，保留0x0 NULL的sync-only调用。')
finding('NPC设备分发表缺少不可用CONFIG及已声明UART的TX','Medium','Confirmed',[(P+'ioe.c',['static void *lut','[AM_UART_CONFIG','[AM_UART_RX','static void fail'])],
 'amdev.h各CONFIG结构及AM调用者能力查询约定：audio_test/bad-apple先读present；UART_CONFIG.present=true。','AUDIO_CONFIG/DISK_CONFIG/NET_CONFIG无处理，ioe_init填fail；UART声明present=true但TX没有处理。','合法能力查询在尚未访问audio/disk前就panic；AM_UART_TX也panic，不能优雅报告无设备。','npc-audio-config/npc-disk-config/npc-uart-tx.log均halt映射退出61；TX先打印present=1。','缺设备CONFIG返回确定性present=false；UART_TX接公开TX接口；不新增不存在硬件。')
finding('AM音频count绝对值读改写会覆盖异步消费进度','Medium','Confirmed',[(N+'audio.c',['outl(AUDIO_COUNT_ADDR,inl']) ,('nemu/src/device/audio.c',['audio_base[reg_count] -= nread'])],
 'AM_AUDIO_STATUS.count和NEMU回调按字节计数；设备异步消费与软件提交必须保留双方增减。','软件读取count后写count+len；SDL callback可在两者之间减count，后一次写覆盖该减量。','count10→AM读10→回调消费4变6→提交3写13，正确待播应9；即使同一设备AM调用互斥也存在。','真实两端源码的确定交错；未启动SDL线程、不以host MMIO mock验证并发正确性。','协调host callback与寄存器提交，或采用提交增量/生产消费索引协议；原子地维护数量。')
finding('音频单次长度大于容量时永久等待','Low','Robustness',[(N+'audio.c',['uint32_t len','while(bufsize'])],
 'Area字节范围和AUDIO_CONFIG.bufsize；没有给出单次必须不大于bufsize的显式前置。','等待整个len一次容纳后才写；len>bufsize时即使空缓冲也永远不满足。Area差还窄化uint32。','oversize、反向Area或>4GiB长度；可见测试分片4096正常，未推定正常应用均触发。','device-audio-oversize.log：容量8、len9、count0，30次状态读后harness退出42。','分片推进或先明确拒绝超容量/非法Area；说明阻塞与错误返回策略。')
finding('双平台IOE未校验reg下标及read/write方向','Low','Robustness',[(P+'ioe.c',['((handler_t)lut[reg])']),(N+'ioe.c',['((handler_t)lut[reg])'])],
 'ioe_read/write接收int reg及指定数据结构；无效编号/方向没有既定错误返回承诺。','直接索引128项表；read/write共享表，不校验amdev.h RD/WR元数据（宏未保存perm）。','reg<0或>=128可越界间接调用；把read用于FBDRAW还会按未初始化结构写设备。正常io_read宏编号在1..24。','静态检查；未实际执行无效间接跳转。','可选显式范围/方向校验并fail-fast；保留合法API调用者前置，不强加通用errno。')
finding('RT AM BSP中断屏蔽接口丢失保存与恢复状态','High','Confirmed',[(RT+'src/interrupt.c',['void rt_hw_interrupt','iset(']),('rt/include/rthw.h',['rt_base_t rt_hw_interrupt_disable','void rt_hw_interrupt_enable(rt_base_t'])],
 '当前RT rthw.h准确签名；scheduler/irq调用保存level并恢复，支持嵌套临界区。','disable返回void而非旧level；enable不接level且总iset(1)，破坏原本禁中断及嵌套状态。','调度、锁、嵌套临界区均调用；从禁用状态恢复会意外开中断，调用者还读取未定义返回值。','bsp-interrupt.log mie=1期望0；interrupt-real-declarations.log在真实RT头下准确报两个签名不匹配。','读取ienabled作为返回值再关MIE，enable按传入level恢复；所有声明与定义一致。')
finding('BSP计时事件未推进已配置的RT tick','Medium','Confirmed',[(RT+'src/context.c',['case EVENT_IRQ_TIMER: break;']),(RT+'rtconfig.h',['RT_TICK_PER_SECOND','RT_USING_TIMER_SOFT'])],
 'RT_TICK_PER_SECOND=100、RT_USING_TIMER_SOFT及rt/src/clock.c的rt_tick_increase入口；BSP负责时钟接入。','EVENT_IRQ_TIMER直接break；BSP无rt_tick_increase/等价时钟驱动，未将AM定时事件接RT clock。','NEMU timer事件进入BSP后tick不推进，超时/软定时器/时间片无法依此工作；NPC当前CTE事件支持限制继承P4。','静态调用闭包：BSP六C文件无tick增量；未运行完整RTOS，不能声称所有shell命令都失败。','按平台时间源正确驱动RT tick并处理中断嵌套/调度契约；不得简单把60Hz事件冒充100Hz。')
finding('BSP应用堆成功分配后公布的长度被减半','Low','Confirmed',[(RT+'src/init.c',['for (; p == NULL','am_apps_heap = RANGE'])],
 'AM_APPS_HEAP_SIZE及rt_malloc成功请求的实际字节范围；应用应能使用已保留内存。','for更新表达式在成功当次仍执行size/=2，循环退出后用缩小的size构造Area。','正常32MiB分配成功公布16MiB；真实小堆回退成功同样浪费一半；全部失败仍继续公布NULL空区。','bsp-heap.log返回32MiB成功指针但Area=16777216；heap-fail.log为空区继续。','保存成功请求大小，成功即break；全部失败明确禁用应用启动或报告失败。')
finding('AM应用线程启动参数引用调用者栈且未处理创建失败','Medium','Confirmed',[(RT+'integrate-am-apps.py',['void *args[2]','rt_thread_create','rt_thread_startup']), (RT+'build/am-apps.c',['void *args[2]','rt_thread_create','rt_thread_startup'])],
 'RT线程异步执行和C对象lifetime；本地rt_thread_create可返回RT_NULL，startup需要合法对象。','args[2]在wrapper栈上；新线程仅持其地址，mainargs也借用argv；创建失败仍startup(NULL)。','延迟启动/调度锁下wrapper先返回时悬挂；默认prio0立即运行可掩盖args问题但不建立所有权保证。','wrapper-lifetime.log从生成器原模板提取代码，以合法延迟启动mock复现ASan stack-use-after-return。','分配线程自有启动数据并复制参数字符串，约定线程释放；检查create/startup失败并回滚。')
finding('BSP UART忽略注册失败并无条件使用NEMU不支持的RX','Medium','Confirmed',[(RT+'src/uart.c',['rt_hw_serial_register','return 0;','ioe_read(AM_UART_RX']) ,(N+'ioe.c',['cfg->present = false'])],
 'RT串口注册错误状态；NEMU UART_CONFIG.present=false且分发表无UART_RX；当前BSP可被RV64双平台构建选择。','rt_hw_uart_init总返回0；预置命令耗尽后_getc直接读AM_UART_RX，无能力判断。','注册失败仍报告成功；NEMU端脚本命令后读RX会fail，NPC RX路径可用不受此项影响。','静态两端链路；没有将预置命令输出当成双平台交互通过。','传播注册返回值并在board init处理；按present选输入能力或明确限制平台，不能隐式panic。')
finding('AM应用集成脚本忽略外部构建和符号工具失败','Medium','Confirmed',[(RT+'integrate-am-apps.py',['os.system','subprocess.run','res.stdout'])],
 '生成器应在子工具失败时失败并避免发布旧对象的成功mk；计划S03产物来源一致性。','make/objcopy的os.system返回值均忽略；nm返回码未检查，已有build可继续copy旧对象并输出mk。','目标构建失败但旧build仍在时脚本可退出0、导入stale.o；没有执行真实项目构建。','generator-failed-make.log/.mk：四个fake make均exit7，预置旧mock对象后脚本仍exit0并发布SRCS。','使用check=True的参数数组；先全成功再原子发布mk/C；隔离输出并清理本轮失败产物。')
finding('cpu-tests run判据的管道吞掉全部FAIL','Medium','Confirmed',[(AT+'cpu-tests/Makefile',['grep -q "FAIL"'])],
 '测试run目标应在真实失败时非零退出；Makefile输出***FAIL***的本地判据。','grep -q不输出内容，后续grep -v总收到空输入并返回1；test FAIL-ne0恒成功。','任意失败（不限wrong负例）都可返回shell成功，已有PASS摘要不能代替逐测试日志。','cpu-oracle-fail.log：单个dummy ***FAIL***的精确recipe退出0；PASS对照也退出0。','直接测试grep返回码并显式过滤负例行；管道任一失败不应由空输出掩盖。')
finding('am-tests devscan无条件调用未支持的GPU加速接口','Low','Confirmed',[(AT+'am-tests/src/tests/devscan.c',['io_write(AM_GPU_MEMCPY','io_write(AM_GPU_RENDER','nbytes / info.blksz'])],
 'GPU_CONFIG.has_accel=false；两个平台lut均未实现GPU_MEMCPY/RENDER；DISK present/blksz需有效。','devscan读取GPU配置后不判断has_accel即调用加速寄存器；storage_test也不检查present及blksz。','当前两个平台的devscan在video_test必panic，后续disk测试不可到达；缺盘/零blksz另外有边界风险。','静态分发表与devscan调用对照；未运行交互性无限循环测试。','按present/has_accel调度子测试；无加速时用FBDRAW验证；缺盘跳过且不除零。')
finding('klib free空实现的教学分配契约未冻结','Low','ContractQuestion',[(K+'stdlib.c',['void free(void *ptr)'])],
 'N1570 §7.22.3.3与ics2024 malloc教学子集候选不同；尚无本项目允许不回收的明确批准来源。','free空函数，heap.start单调推进；demo galton/bf等确有free调用，不由“教学”自动豁免。','反复创建销毁后内存不能重用；是否要求通用释放/单次arena子集需后续裁决。','源码与malloc.log free前后cursor不变；不以本条掩盖F0037独立越界缺陷。','先冻结释放/arena/reset所有权契约，再实现或限制调用者。','保留CQ-001/007；不批准简化，不据C全库要求强行扩成通用libc实现；本轮只记录差异。')
finding('双平台has_rtc=true与固定历法占位的能力契约待定','Low','ContractQuestion',[(N+'ioe.c',['cfg->has_rtc','cfg->present = true; cfg->has_rtc']), (N+'timer.c',['rtc->year','rtc->day','rtc->month']), (P+'ioe.c',['cfg->present = true; cfg->has_rtc']), (P+'timer.c',['rtc->year'])],
 'TIMER_CONFIG.has_rtc与RTC字段公开语义；ics2024 AM时间与本地J4无真实墙钟的教学描述。','NEMU恒1900/0/0，NPC恒1970/1/1，两者仍has_rtc=true；不是正在运行的日历。','日期消费者无法依has_rtc判断真实历法能力。NPC uptime的周期数/相对时基另有J4既有决策，不重判为未批准换算。','静态字段写入与已有J4记录；NEMU uptime latch测试通过，不混同RTC与UPTIME。','先确定has_rtc是否表示真实历法或固定占位；不支持时如契约要求则返回false。','CQ-007保留，不改变J4时基决定；不批准RTC简化，也不宣称该占位一定违反本项目已冻结日历承诺。')
finding('memmove使用与长度等大的栈VLA且零长度触发边界风险','Low','Robustness',[(K+'string.c',['char tmp[n]'])],
 'memmove允许重叠与零长；N1570 §6.7.6.2/§7.24.2.2；GNU零长扩展和有限AM栈需区分。','先分配n字节VLA再复制两遍，零长形成非正VLA；大堆块搬运可能耗尽小栈。','正常重叠小块结果正确；本地RV64程序有小栈，合法大内存移动不代表有同样大的栈。','memory.log两向重叠通过；move-zero.log UBSan报告bound0。未把sanitizer报告单独当成当前GNU11必然运行失败。','依据地址顺序选择前/后向复制，使用O(1)栈；先处理n=0/相同地址。')
assert len(new)==24
dump(H/'findings.json',new)
old=json.loads((B/'findings.json').read_text());old=[x for x in old if x['phase']!='CCR-P5'];assert len(old)==32
dump(B/'findings.json',old+new)
md=(B/'FINDINGS.md').read_text();anchor='<a id="ccr-p5-findings-20261017"></a>'
if anchor in md:md=md[:md.index(anchor)].rstrip()+'\n'
md+='\n'+anchor+'\n## CCR-P5 — 双平台 AM runtime / klib / BSP（2026-10-17）\n\n24项新增：19 Confirmed、3 Robustness、2 ContractQuestion（High2/Medium12/Low10）；均未修。旧32项原记录保留。必要复现与限制见[P5](P5.md)、[AM_RUNTIME](AM_RUNTIME.md)。CQ为审阅分类，不批准教学简化，不作修复契约选择。\n\n| ID | 严重程度 | 状态 | 问题 |\n|---|---|---|---|\n'
for i in new:md+=f"| [{i['id']}](#{i['id'].lower()}) | {i['severity']} | {i['status']} | {i['title']} |\n"
for i in new:
    md+=f"\n<a id=\"{i['id'].lower()}\"></a>\n### {i['id']} — {i['title']}\n\n- 严重程度 / 状态：**{i['severity']} / {i['status']}**；CCR-P5。\n"
    for l in i['locations']:md+=f"- 位置：`{l['path']}:{','.join(map(str,l['lines']))}`；SHA-256 `{l['sha256']}`。\n"
    for key,title in [('expected_contract_and_basis','预期/依据'),('actual_and_root_cause','实际/根因'),('reachability_and_impact','可达条件/影响'),('validation','本次验证'),('minimal_fix','最小建议（未实施）'),('recommended_regression','回归'),('unconfirmed_assumptions_and_limits','限制')]:md+=f"- **{title}**：{i[key]}\n"
    md+='- 证据：[P5 findings](p5/findings.json)、[逐文件](p5/file-review.jsonl)、[验证命令](p5/probe-results.json)、[BSP/NPC](p5/supplement-results.json)、[最终探针](p5/final-probe-results.json)。\n'
line='当前状态（2026-10-17）：P5新增24项（19 Confirmed、3 Robustness、2 ContractQuestion）；累计56项（46 Confirmed、5 Robustness、5 ContractQuestion；High6/Medium34/Low16），均未修。见[P5问题](#ccr-p5-findings-20261017)及[P5审阅](P5.md)。P5结果确认/commit Pending，P6未开始；下方P2–P4正文保留历史截面。'
md=re.sub(r'当前状态（2026-10-17）：[^\n]+',line,md,count=1);(B/'FINDINGS.md').write_text(md)

# Each owned file gets concrete API paths; boundary-only assets retain S01/S02/S03 depth.
details={
'abstract-machine/am/include/am.h':('IOE三个函数签名、Area及amdev.h包含；其他核心定义复用P4','reg/void*依调用方选准确结构；无errno通道；IOE只准初始化一次','Area双RV64指针16字节；同步借用buf，不转移所有权；布局在ioe-layout编译断言'),
'abstract-machine/am/include/amdev.h':('24个DEVREG id/字段/perm、AM_KEYS、gpuptr与packed GPU描述','CONFIG/STATUS与控制长度单位分开；RD/WR宏未生成动态校验','GPU_FBDRAW32、DISK_BLKIO24、Area16，见layout；packed canvas26/texture8，gpuptr是32位设备内偏移，不能当RV64宿主指针'),
'abstract-machine/am/src/platform/nemu/include/nemu.h':('设备地址、PMEM128MiB、NEMU_PADDR_SPACE与IOE对应','AUDIO_SBUF64KiB、FB2MiB映射；DISK控制页包含在MMIO0x1000区域','uint32 MMIO、inw显示尺寸；RTC高低半字latch、DMA64位指针拆分；TRM/VME核心复用P4'),
'abstract-machine/klib/include/klib.h':('全部string/stdio/stdlib签名、extern C、assert/NDEBUG','signed/unsigned可变参数、size_t64；assert失败printf→halt','不包含全套libc；公开函数名兼容契约需逐项，不能由框架注释自动免除；本地头不是RT libc最终链接选择证明'),
'abstract-machine/klib/include/klib-macros.h':('ROUNDUP/DOWN、LENGTH、RANGE、IN_RANGE、io_read/write、putstr/panic','round sz须正的2幂且加法不溢出；多次求值宏参数不得有副作用；io_read结果由handler完整初始化','io宏在调用栈建结构并同步调用，无跨调用lifetime；GNU statement-expression/void*关系是当前GNU方言，不机械按纯ISO拒绝'),
'abstract-machine/klib/Makefile':('find src/*.c全部选入，include AM公共规则','cpp/int64编成archive但按引用抽取；不直接make覆盖原build','当前__ISA_NATIVE__不定义；两RV64平台同klib；构建成功不保证格式/分配运行正确'),
RT+'Makefile':('src六C + files.mk + 可选am-apps.mk；LDS/BOOT_S export及update','ARCH默认native但用户目标RV64两平台；旧mk自动include，update只显式触发；init/menuconfig有原地副作用','rtconfig.py SCons flags不是AM最终flags；不执行scons/update/clean；绝对files.mk绑定工作区'),
RT+'files.mk':('50个RT/组件源码路径与include导出，只核AM实际依赖入口','绝对路径移动会失效；本轮不进入全部RT源码算法','RT core/DFS/serial/libc仅沿BSP具体声明/调用定向读，不把50个外部实现标为已审'),
RT+'SConstruct':('RTT_ROOT/EXEC_PATH、PrepareBuilding/DoBuilding、工具命令','SCons会构建/生成配置；不执行；native默认和RV64来源不混淆','此处riscv64imac/lp64不等于AM构建rv64g/默认lp64d，历史对象需逐配置配对'),
RT+'SConscript':('按子目录SConscript收集objs','目录枚举顺序与生成环境保持原样；本轮无执行','仅SCons依赖导航，无运行时buffer、ownership或初始化对象（N/A）'),
RT+'rtconfig.py':('RTT_ROOT/CC_PREFIX/EXEC_PATH/BUILD与RV64 flags','环境可覆盖工具前缀；LFLAGS引用link.lds不代表AM实际LDS','SCons dry-run收集C路径与AM最终重编分开；现有pyc仅S03来源，不运行'),
RT+'rtconfig.h':('当前RT5.0.1、tick100、heap/console/serial/DFS/soft timer配置','UART DMA开关存在但BSP ops无DMA；TIME/RTC宏不创造AM真实能力','与.config和files.mk逐接口核对；不扩RT完整feature审计，timer接入F0047'),
RT+'.config':('Kconfig持久选择与rtconfig.h的当前BSP选项','当前保留配置而非旧binary证据；不运行配置生成器','文件无运行时指针/ownership（N/A）；宏的后续消费者见RT BSP记录'),
RT+'Kconfig':('BSP/RTT/PKGS环境路径、source、BOARD_AM select','缺packages不下载安装；相关生成状态不改变','只读配置定义，无运行时对象（N/A）；选项由rtconfig.h消费'),
RT+'extra.ld':('FSymTab/VSymTab/rti/Utest节KEEP与边界符号','当前BSP Makefile不选extra.ld，已移入P4所审NPC链接脚本；不重复布局审阅','仅P5注册表消费者责任；不是当前成功链接产物证据'),
RT+'include/extra.h':('suseconds_t/useconds_t与sys/types；native重命名','RV64非native保留API名；native整组重命名S06排除','long/unsigned long8字节；只核本地声明/冲突边界，P7 newlib/用户接口不提前审'),
RT+'include/asm/errno.h':('转发工具链asm-generic errno定义','引用实际RT/compiler include路径；不推定支持全POSIX','头转发无运行时buffer/状态（N/A），数值消费者不在P5全面展开'),
RT+'src/hello.c':('INIT_ENV_EXPORT(hello)输出与返回0','init section须KEEP且组件初始化开启；与P4链接记录一致','只借用字符串常量；无动态对象；IO/调度正确性不由hello输出证明'),
K+'string.c':('strlen/strcpy/strncpy/strcat/strcmp/strncmp/memset/memmove/memcpy/memcmp','n=0、非NUL n字节源、短串padding、两向重叠、高位字节；F0033/56','有效可访问buffer、strcpy/strcat容量及非重叠由调用者保证；RV64默认unsigned char；不把host signed-char差异当RV64缺陷'),
K+'stdio.c':('decode_fmt/num2str/vformat/sink_emit/putch_emit及五种printf入口','n=0/1/截断/返回would-have-written、%%、STR/CHAR/NUMBER、long/unsigned/负数/八进制；F0034–36','输出buffer调用者所有，回调不持有；NULL fmt被当空串但不是C标准承诺；不支持precision/h/ll/浮点，不批准完整printf兼容；超INT_MAX计数及全局putch_counter不可重入风险保留'),
K+'stdlib.c':('rand/srand/abs/atoi/malloc/free及替换条件','0长度/对齐/堆尾/失败/释放；符号/空白/空串；abs(INT_MIN)为调用者域外','LCG无符号wrap，范围0..32767；malloc修改公开heap、无独立ownership元数据；free回收CQ；native替换分支S06排除'),
K+'int64.c':('__divdi3/__divmoddi4/__moddi3/__udivdi3/__umoddi3/__udivmoddi4与clz/ctz32/64','n高低半字零/幂二/比较/通用长除法、rem=NULL；MIN及符号；clz/ctz前置a!=0','LP64 little-endian union32+32；普通RV64G的DIV直接指令，不把helper导出等同编译器选入；无__ARCH_RISCV64_MYCPU定义，guard臂有效'),
K+'cpp.c':('dso_handle/guard_acquire/guard_release/cxa_atexit','动态局部static、atexit assert、NDEBUG改变占位失败行为；F0040','编译器生成guard需求有证；不承诺完整异常/析构运行时；__ISA_NATIVE__体排除'),
N+'ioe.c':('ioe_init/read/write、128项表、全部CONFIG/handlers、fail','缺表项由init填fail；AM已选device被关闭时init仍无条件触MMIO；reg下标/方向无校验','初始化只能一次；lut func/data pointer转换依GCC目标；buf须匹配结构、同步借用，未持有；NEMU当前全设备配置与REF无设备目标分开'),
P+'ioe.c':('ioe_init/read/write、UART CONFIG/RX、设备表/fail','UART LSR_DR/empty0xff、缺AUDIO/DISK/NET CONFIG及TX；F0042/45','当前RV64 unsigned char使rx.data==0xff可成立，不凭x86 signed-char误报；MMIO无错误返回，ioe_init=true不证明所有设备可用'),
N+'timer.c':('timer_init/uptime/rtc','RTC高读触发锁存再读低；64位组合与2^32 rollover；固定日历CQ','UPTIME微秒沿宿主get_time起点，不在init再清零；独占设备访问下匹配NEMU latch，不要求low-high-low重试'),
P+'timer.c':('timer_init/uptime/rtc','单ld对齐访问CLINT，固定日历CQ；无墙钟','J4 2026-09-02既有决定us=mtime相对基准；不宣称物理微秒；asm volatile只做load不构成一般memory fence；硬件NotRun'),
N+'input.c':('KEYDOWN_MASK/KEYNUM_MASK与一次KBD读取','空0、按下bit15/释放、int keycode全赋值','NEMU返回AM keycode而非PS2，bool转换正确；单次取事件，无buffer ownership'),
P+'input.c':('PS2扫描码表/ext/brk、push/pop、硬件排空','正常make/break、E0分段前缀、未知键丢弃、内部队列满20→15','索引uint8限制0..255，15可用slot；overflow丢事件的已实现策略不等于无丢失保证；Pause NVBoard未支持，不虚构当前E1可达缺陷；无CTE重入承诺'),
N+'gpu.c':('gpu_init/config/status/fbdraw','0x0 sync-only、正矩形row-major/32bit、sync时序F0041','像素buffer仅调用期借用；无裁剪/负坐标/乘法溢出保护，调用者需合法屏内矩形；w/h来自16位MMIO，真实大设备值int乘法需限制'),
P+'video.c':('gpu_init/config/status/fbdraw','640x480、0x0/负长返回、跨行矩形未裁剪；mmap探针','当前扫描式FB无显式present提交；sync忽略是平台实现事实，不把它当NEMU sync寄存器；越界/负坐标和大整数为未防护输入，未强加裁剪契约'),
N+'audio.c':('audio_init/config/ctrl/status/play','配置freq/channels/samples按帧、count/bufsize按字节；环绕、empty/oversize/逆Area、异步count交错','输入Area在返回前复制，不转移所有权；wr_index单实例init不重置（ioe只准一次）；NEMU samples触发初始化F0010沿用，不重复新建；异步消费不可由AM互斥消除'),
N+'disk.c':('disk_config/status/blkio','present/512B block、blkno/blkcnt零/负转uint32、ready==1、指针高低32提交、CMD最后','当前无VME的合法物理buffer同步DMA；接口没有错误码，ready不等于成功；范围/短IO/PA截断缺陷沿用F0009；用户VA非DMA物理地址，不提前审P6映射'),
RT+'src/context.c':('ev_handler、wrapper、cte_init、context_switch/to/interrupt、stack_init','EVENT_YIELD保存from/选to、恢复userdata、初始frame/参数区16字节对齐、timer break和interrupt-switch assert','scheduler_up先更新rt_current_thread再进BSP，因此self为目标线程是既有调用约定；cp_addr在源线程栈同步yield内消费；线程args在自身栈sp以上；核心trap不重审P4'),
RT+'src/interrupt.c':('rt_hw_interrupt_enable/disable','旧MIE保存/恢复及嵌套；F0046','真实rthw声明与定义不一致；纯AM/RT边界审阅，不推导完整锁/RTOS调度正确性'),
RT+'src/init.c':('board_init/entry main、IOE→CTE→RT entry','分配回退成功/全失败、data0/非0快照、console/components/heap条件','rt heap归RT allocator；app预留区由RT分配但独立借出，size减半F0048；data_content持久副本；assert非空但NDEBUG无保证；shared global app memory不可默认支持并发启动'),
RT+'src/uart.c':('configure/control/putc/getc、uart_init/debug_init','脚本命令耗尽、RX空0xff、注册错误、DMA/control no-op','putch TX同步借用；NEMU没有UART_RX；register返回值丢弃F0050；config/control总EOK不证明硬件/DMA支持；无完整串口驱动审计'),
RT+'src/libc.c':('weak strchr/strrchr/strstr/strtol/strncat','除strstr外assert占位；NDEBUG会变无返回值','弱符号可被RT强定义替换，rt_strstr需匹配RT宏实际定义；不把弱stub文件存在等同最终链接生效；旧ELF不证明同版源码'),
RT+'integrate-am-apps.py':('argv/env解析、read_lib_symbols/integrate、符号重写、生成wrapper与dummy初始化','工具失败/旧对象、线程创建失败与参数lifetime；不执行原make/update','四应用共享am_apps_data/bss/heap；缺并发序列化；生成dummy true不建立真实CTE/VME/MPE隔离；SHELL字符串假定可信路径不作外部攻击面扩展'),
AT+'cpu-tests/Makefile':('ALL清单、动态Makefile、result收集、run/gdb/clean','解析就清.result；真实失败recipe仍退出0，wrong负例不能解释全部FAIL丢失','只在隔离sh执行精确recipe；未运行原make、不清理历史build；PASS输出不是oracle闭环'),
AT+'am-tests/src/tests/devscan.c':('input/timer/video/storage/devscan','无accel调用MEMCPY/RENDER；缺盘与blksz0；heap printf用%x接指针不匹配RV64','只审oracle/设备接入；无加速功能不能报告am-tests d通过；当前可达panic发生在disk之前'),
}
source=[];assets=[];review=[];stats=collections.Counter()
callpat=re.compile(r'\b(?:io_read|io_write|ioe_(?:read|write|init)|AM_[A-Z_]+|heap|rt_hw_[a-z_]+|rt_thread_[a-z_]+|malloc|free|bench_alloc|bench_free|printf|snprintf|putch|halt|yield|kcontext|vme_init|mpe_init|cte_init)\b')
for r in files:
    p=r['path'];q=R/p;raw=q.read_bytes() if q.exists() else b'';suffix=q.suffix
    asset='/build/' in p or r.get('classification') in ['generated_or_build_artifact','binary_asset_provenance_pending','git_metadata'] or '/.git/' in p or p.endswith('.sconsign.dblite')
    is_generated_source=asset and suffix in ['.c','.h','.mk']
    if p in details:
        group='OwnedRuntime';normal,boundary,abi=details[p]
    elif is_generated_source:
        group='S03GeneratedInterface';normal='生成源码/配置必须检查内容与消费者；'+('am-apps wrapper同当前generator模板，含4个MSH命令' if p.endswith('am-apps.c') else '逐项解析生成入口/编译依赖与宏')
        boundary='配置/对象列表可能陈旧；不重建或覆盖原build；旧产物配对Unknown';abi='生成器和当前消费者已审；build/am-apps.c保留F0049，不以S03跳过生成源码ABI'
    elif asset:
        group='S03Asset';normal='逐身份哈希、类型/ELF/归档/依赖元数据与生产消费入口';boundary='旧binary/config/source配对Unknown；不计为本轮功能验证';abi='按S03保护原字节；资源/对象不承担独立运行时ownership，消费者决定大小/生命周期'
    elif '/riscv-tests/' in p:
        group='S01RiscvTests';normal='第三方文件的版本/HEAD字节、接口token与入口责任；env/p/riscv_test.h本地修改全读'
        boundary='RV64编译/exit oracle、RVTEST_ADAPTED/RVTEST_NPC与上游default flags分开；未选RV32路径只保留身份/共享边界';abi='S01不逐指令审上游测试算法；p环境ebreak/a0退出，本地多hart/PMP/特权缩减不得当完整ISA验证；不执行configure/make/install'
    elif p.startswith('am-kernels/'):
        group='S02CallerBoundary';normal='AM调用、test oracle、构建/资源和运行时接入逐文件核对；纯业务算法按S02边界'
        boundary='按参数、能力失败、尺寸/时间/分配边界核调用；assert/无限演示/负例与自动PASS分开';abi='RV64指针8字节，接口int4字节；文件内AM/klib buffer借用及持久静态资源；算法内核不宣称逐函数审'
    elif p.startswith('fceux-am/'):
        group='X04CallerBoundary';normal='只沿AM input/video/audio/time、入口与相关头契约；非完整fceux核心审计'
        boundary='SOUND_NONE/HAS_GUI/NO_FILE_SYSTEM有效条件分别登记；PCM int32→int16后Area字节，GetWriteSound先除2为样本';abi='canvas/PCM静态buffer在同步IO返回前有效；Navy filesystem分支留P8；此目录不替代缺失fceux'
    else:
        group='RuntimeSupport';normal='头/构建/链接/来源与P5职责；TRM/MPE/Context核心复用P4，不重复主审';boundary='按当前双平台配置、空/失败状态核接口前提；不扩大其他ISA或P6';abi='契约/来源见AM_RUNTIME.md；libgcc未被当前AM_SRCS选入，静态审与交叉编译均不证明实际被调用'
    if p.endswith(('/LICENSE','/README','/.gitignore')):
        normal='来源/许可/入口和忽略规则逐件核对；不改已有跟踪与构建边界'
        boundary='N/A：非执行代码，无运行期成功/错误状态；旧说明不是同版运行证据'
        abi='N/A：无运行期buffer/ownership/lifetime；仅保留生产消费导航与S03保护'
    if p.startswith(P+'libgcc/'):
        group='DormantLocalHelper';normal='完整本地helper源码及RV64有效头分支：mul64/div64、multi128/ashl128、soft-float panic占位'
        boundary='mul0/MAX；div正负/零/溢出由汇编分支处理；shift0/<64/>=64至127，越域不承诺；RV32改名臂S06排除'
        abi='GCC版权2016–2022但导入commit Unknown，不能称未修改上游；RV64 libgcc2将DW映射TI：ashldi3实际符号__ashlti3；普通rv64g选硬件M；当前AM_SRCS不包含这8文件'
    if p.endswith('arch/riscv.h') or p.endswith('riscv/riscv.h') or p.endswith('/mpe.c') or p.endswith('/trm.c') or '/scripts/linker' in p:
        normal='复用P4已完成Context/TRM/MPE/链接核心；P5仅字宽、MMIO helpers、heap/putch及运行时消费者责任'
    if p==EXCLUDED:
        group='ScopeCorrectionS06';normal='仅保留身份/哈希及ELF32目标证据；不计入RV64已审分子'
        boundary='S06已批准排除非RV64目标；P1误保留的profile本轮更正，无新增范围取舍'
        abi=EXCLUSION
    issue=[i['id'] for i in new if any(l['path']==p for l in i['locations'])]
    text=raw.decode(errors='replace') if b'\0' not in raw[:4096] else ''
    refs=[{'line':n,'text':l.strip()[:450]} for n,l in enumerate(text.splitlines(),1) if callpat.search(l)]
    source.append({'row_id':r['row_id'],'path':p,'sha256':r['source_sha256'],'depth':group,'interface_lines':refs,'limitations':abi})
    if asset:
        typ='opaque/resource';meta={}
        if raw.startswith(b'\x7fELF'):
            typ='ELF';le='<' if raw[5]==1 else '>';cl=raw[4];meta={'class':cl*32,'byte_order':raw[5],'type':struct.unpack_from(le+'H',raw,16)[0],'machine':struct.unpack_from(le+'H',raw,18)[0],'flags':struct.unpack_from(le+'I',raw,48 if cl==2 else 36)[0]}
        elif raw.startswith(b'!<arch>\n'):
            typ='archive';meta={'members':subprocess.check_output(['ar','t',q],text=True).splitlines()}
        elif suffix=='.d':typ='dependency';meta={'text':text[:16000]}
        elif text:typ='text/generated';meta={'lines':len(text.splitlines()),'interface_lines':refs}
        assets.append({'row_id':r['row_id'],'path':p,'sha256':r['source_sha256'],'type':typ,'metadata':meta,'producer_consumer':'GENERATORS.md + AM_RUNTIME.md; build owner path','pairing':'Unknown historical exact source/config/flags; not runtime evidence','scope_disposition':'Excluded/S06' if p==EXCLUDED else 'retained S03 responsibility'})
    rec={'row_id':r['row_id'],'path':p,'module_id':r['module_id'],'source_sha256':r['source_sha256'],'responsibility':'CCR-P5 only','depth':group,'review_status':'ReviewedStatic','normal':normal,'boundary_zero_empty_invalid':boundary,'failure_state_return_cleanup':boundary+'；失败未定义处明确为能力/前置限制，不虚构错误码','integer_alignment_lifetime':abi,'init_repeat':'IOE/CTE等扩展一次初始化；不要求幂等；klib静态状态/RT初始化与应用reset的重复生命周期见AM_RUNTIME.md','conditional_upstream_downstream':'当前RV64 NEMU/NPC分别核对；'+abi,'issue_ids':issue,'evidence_ids':['CCR-E-P5-static','CCR-E-P5-probes'],'dynamic_validation':'NotRun for target; host/compile probes individually in three command records'}
    review.append(rec);stats[group]+=1
    if p==EXCLUDED:
        rec['review_status']='Excluded';rec['scope_basis']=EXCLUSION
by={r['path']:r for r in review}
breview=[]
for r in branches:
    p=r['path'];own=by[p];condition=r.get('function_or_path');lr=r.get('line_range')
    text=(R/p).read_text(errors='replace').splitlines();line=text[lr[0]-1] if lr and lr[0]<=len(text) else str(condition)
    if any(k in line for k in ['__ISA_NATIVE__','__NATIVE_USE_KLIB__','__ARCH_NATIVE','__ISA_X86__','__ISA_MIPS32__','__ISA_LOONGARCH','__ARM','_MSC_VER','__NetBSD__','__FreeBSD__','__APPLE__','_WIN32']):ev='按RV64 GCC/LP64 little-endian求值；native/其他ISA或其他compiler体不执行；保留endif/else结构与共享有效臂'
    elif any(k in line for k in ['__riscv_xlen','__riscv_mul','UNITS_PER_WORD','__BYTE_ORDER__','_YUGA_','__LP64__']):ev='RV64=64、LP64、little-endian、GCC rv64g具有M；libgcc DW=TI，macro重命名生效；非目标位宽臂S06排除语义'
    elif '__ARCH_RISCV64_MYCPU' in line:ev='当前构建未定义MYCPU；!defined臂含signed div/mod helper有效，MIN风险F0039'
    elif 'RT_' in line or 'BOARD_AM' in line:ev='按RT BSP .config/rtconfig.h检查当前feature；不以生成文件名或SCons不同flags冒充AM实际配置'
    elif 'NDEBUG' in line:ev='当前未定义NDEBUG，assert有效；NDEBUG分支会去掉失败保护，仅静态记录，不把弱stub视为成功实现'
    elif any(k in line for k in ['SOUND_CONFIG','SOUND_NONE','SOUND_HQ','HAS_GUI','__NO_FILE_SYSTEM__']):ev='按fceux-am Makefile和config.h具体AM调用域；禁用audio/GUI与Navy文件分支分别保留归属'
    else:ev='逐条件导航的职责判定与所属文件相同；'+own['depth']+'；不把词法endif/Make selector当独立运行场景'
    breview.append({'row_id':r['row_id'],'path':p,'line_range':lr,'source_line':line,'condition_evaluation':ev,'disposition':'ReviewedStatic at P5 declared depth','normal':own['normal'],'boundary_failure':own['boundary_zero_empty_invalid'],'abi_lifetime':own['integer_alignment_lifetime'],'issue_ids':own['issue_ids'],'evidence':'AM_RUNTIME.md / p5/source-evidence.jsonl / p5/file-review.jsonl','target_dynamic':'NotRun'})
    r['p5_review']=breview[-1];r['review_status']='ReviewedStatic';r['condition_evaluation']='P5: '+ev;r['evidence_ids']=sorted(set(r.get('evidence_ids',[])+['CCR-E-P5-static']));r['issue_ids']=sorted(set(r.get('issue_ids',[])+own['issue_ids']))
for r in files:
    rec=by[r['path']];r['p5_review']=rec;r['review_status']='ReviewedStatic'
    for k in ['normal','boundary_zero_empty_invalid','failure_state_return_cleanup','integer_alignment_lifetime','init_repeat','conditional_upstream_downstream']:r[k]=rec[k]
    r['evidence_ids']=sorted(set(r.get('evidence_ids',[])+rec['evidence_ids']));r['issue_ids']=sorted(set(r.get('issue_ids',[])+rec['issue_ids']));r['limits']=r.get('limits',[])+['P5责任结论按p5_review.depth解释；旧P1 Pending为历史，不覆盖P4/P6/P9责任；target动态NotRun。']
    if r['path']==EXCLUDED:
        r['review_status']='Excluded';r['review_scope']='Excluded';r['scope_reason']=EXCLUSION
        r['excluded_config']=sorted(set(r.get('excluded_config',[])+r.get('review_config',[])))
        r['review_config']=[];r['review_profiles']=[];r['effective_phase']=None;r['effective_phase_responsibilities']={};r['phase_role']='S06 excluded non-RV64 artifact; original identity retained'
        dump(H/'scope-correction.json',{'path':EXCLUDED,'row_id':r['row_id'],'source_sha256':r['source_sha256'],'basis':EXCLUSION,'approval':'SCOPE_RV64.md#s06-clarification-20261017; no new exclusion authorization inferred','before':next(x for x in [json.loads(s) for s in gzip.decompress((H/'coverage.before.jsonl.gz').read_bytes()).decode().splitlines()] if x['row_id']==r['row_id']),'after':r,'evidence':['ELF class32/machine243 in artifact-review.json','am-kernels/tests/riscv-tests/debug/targets/RISC-V/spike32.py:19','am-kernels/tests/riscv-tests/debug/targets/RISC-V/spike64.py:19']})
lookup={r['row_id']:r for r in files+branches};updated=[lookup.get(r['row_id'],r) for r in original]
for path,data in [(H/'file-review.jsonl',review),(H/'branch-review.jsonl',breview),(H/'source-evidence.jsonl',source),(B/'coverage.jsonl',updated)]:path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in data))
dump(H/'artifact-review.json',assets);dump(H/'review-summary.json',{'files':len(files),'retained_reviewed_files':len(files)-1,'S06_corrected_exclusions':1,'branches':len(branches),'depth':dict(stats),'artifacts':len(assets),'new_findings':len(new),'classification':dict(collections.Counter(x['status'] for x in new)),'severity':dict(collections.Counter(x['severity'] for x in new)),'total_classification':dict(collections.Counter(x['status'] for x in old+new)),'total_severity':dict(collections.Counter(x['severity'] for x in old+new))})
print((H/'review-summary.json').read_text())
