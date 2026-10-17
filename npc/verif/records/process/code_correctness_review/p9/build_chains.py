#!/usr/bin/env python3
"""P9 authored seam analysis; emits 9 reports and additive coverage only."""
from pathlib import Path
import json,gzip,re,collections
H=Path(__file__).resolve().parent;B=H.parent;R=H.parents[5]
D=['syscall number','register','argument','width','pointer','structure layout','address','length','unit','ownership','lifetime','error code','return value','state transition','configuration prerequisite']
chains=[]
def chain(i,title,refs,cells,issues,faults,dynamic,limits):
 values=cells.strip().split('\n');assert len(values)==15,(i,len(values))
 x={'id':i,'title':title,'review_status':'ReviewedStaticWithFindings','meaning':'审阅义务闭合；不表示实现正确或缺陷已修复','references':[{'key':a,'path':p,'lines':l} for a,p,l in refs],'dimensions':[{'name':k,'assessment':v} for k,v in zip(D,values)],'issue_ids':[f'CCR-F{n:04}' for n in issues],'failure_paths':faults,'dynamic_validation':dynamic,'limits':limits};chains.append(x)
chain('L01','程序加载 → 用户启动 → syscall/trap → AM/NEMU → return/exit',[
 ('L','nanos-lite/src/loader.c',[14,40,54,104,111,120,146,183,192]),('S','nanos-lite/src/syscall.c',[11,30,42,71,109,139]),('U','navy-apps/libs/libos/src/syscall.c',[46,69,74,91,104]),('C','navy-apps/libs/libos/src/crt0/crt0.c',[8,16]),('T','navy-apps/libs/libos/src/crt0/start.S',[1,10]),('A','abstract-machine/am/src/riscv/nemu/cte.c',[5,15,29,45]),('AS','abstract-machine/am/src/riscv/nemu/trap.S',[39,47,58,70,81]),('N','nemu/src/isa/riscv32/inst.c',[384,385]),('NI','nemu/src/isa/riscv32/system/intr.c',[29,61])],'''
U/S：共享syscall.h枚举exit0/yield1/open2/read3/write4/close7/lseek8/brk9/execve13/gettimeofday19；AM内部yield用a7=-1，非用户SYS_yield1。其余号不能等价认为已实现。
U→A/AS：RV64 a7=x17装号，a0/x10,a1/x11,a2/x12装3参，返回a0；ecall由N按当前priv产生8或11，A均+4后分发，mret恢复到下一条。NPC仅识别M态11，不能套用U态入口。
L→T/C：GPRx/a0指向argc槽；_start设置sp=a0再call_main，argv=args+1、envp=argv+argc+1。初始4程序以及exec字符串先拷到新栈，argv/env双NULL终止；未提供auxv，不能套完整Linux启动约定。
LP64：uintptr_t/intptr_t/long/ptr8，int4；L ELF64 Ehdr64/Phdr56，argc槽8但main argc为int。a0负返回保留64位；newlib低层隐式int问题F0077未因寄存器匹配消失。
L先读旧argv/env指针并拷字符串至新用户栈的PA，数组槽存对应VA；C收到用户VA，不是PA。无合法性/字符串上界校验F0061/F0073；非法指针不是可恢复EFAULT。
Context由公共arch/riscv.h与AS配对：32×8 GPR，mcause256/mstatus264/mepc272/np280，总288；pdir与x0槽重叠。argc/argvNULL/envNULL布局匹配，sp16字节对齐缺失F0060；layout.c交叉编译验证布局。
NEMU内核0x80000000身份映射，用户VME范围0x40000000–0x80000000，栈7fff8000–80000000，入口取ELF e_entry；旧nterm入口0x83000000是F0074。NPC启动flash30000000另有装载/能力断点。
PT_LOAD filesz/memsz为字节、phnum为项数、phentsize用于栈内Phdr读；未检查短头、phentsize>56、filesz>memsz、段溢出/重页F0057–59。32KiB栈没有argc/env字节总量校验。
ELF偏移/段/栈均byte，4096byte/page；syscall read/write为byte，gettimeofday另见L04。mepc推进4byte与当前无C配置一致；不把指令数当byte。
用户拥有argv源与调用buffer；loader分配物理页/页表、PCB拥有新Context；L复制后源可随exec失效。C environ借用新栈字符串；关闭固定fd不代表独立open对象释放。
启动Context位于PCB内核栈顶，trap frame须在切换期间活着；OS固定PCB不回收页有P6教学契约依据；AM通用unprotect回收仍F0030/CQ。首次用户trap的mscratch判源F0023及未初始化pdir槽F0024仍在返回链，正常探针通过不证明这些路径安全。
S exec预检文件不存在返回-ENOENT=-2，U转为-1并写errno；普通open缺失直接-1，没有一致errno传播F0076。ELF已存在但坏头直接panic；未实现syscall默认panic，不返回ENOSYS。
普通syscall S以long返回写Context.a0，AS恢复；成功exec以switch_boot_pcb/yield切到新Context，正常不回旧调用。main返回→本地newlib exit/cleanup→_exit→SYS_exit，_exit预期不返回而自旋兜底。
正常ELF加载→kstack Context→mret U→crt→ecall M→事件/syscall→mret U可达；SYS_exit忽略code并重载/bin/nterm，重置max_brk，非NEMU结束。缺失nterm时sys_exit忽略exec失败，可能回到_exit自旋；全机终止由ebreak教学ABI另判。
NEMU当前HAS_CTE/HAS_VME/FG_PROCESS、DEVICE和各IOE开启；user必须VME链接40000000。无VME naive分支需自己的入口/栈契约；NPC dummy ucontext=NULL/F0070、libam guest F0086/F0113均无当前成功全链，不因共享头而认作等价。
''',[23,24,30,57,58,59,60,61,70,73,74,76,77,86,113],
 ['不存在exec在替换地址空间前返回；本轮成功返回原调用，随后仍能brk/yield。','损坏ELF和缺盘分别触发loader魔数assert及BAD TRAP/rc1；不是错误码恢复。','任意用户指针/异常长度/非法调用号静态追到未校验解引用或panic，未在guest破坏性穷举。','exit是应用替换；OS固定PCB不回收页沿用P6教学边界，但AM通用unprotect语义仍CQ，不能扩大豁免。'],
 'TargetE2E-Pass（受控应用）：e2e-attempt5，8个业务marker+GOOD TRAP/rc0；faults含坏ELF/缺盘rc1和mtimer模式成功。',
 '普通UI/游戏非此fixture；当前历史ramdisk未运行；没有穷举嵌套中断/重复exec耗尽；NPC/libam全链NotRun。')
chain('L02','file API → libc/libos → syscall → nanos FS → ramdisk/device',[
 ('U','navy-apps/libs/libos/src/syscall.c',[74,78,82,86,108]),('R','navy-apps/libs/libc/src/reent/readr.c',[24,45]),('W','navy-apps/libs/libc/src/reent/writer.c',[24,45]),('S','nanos-lite/src/syscall.c',[47,51,55,59,63]),('F','nanos-lite/src/fs.c',[9,35,59,95,113,134,153]),('D','nanos-lite/src/disk.c',[17,34,42,60]),('A','abstract-machine/am/src/platform/nemu/ioe/disk.c',[1,28]),('N','nemu/src/device/disk.c',[27,44,64])],'''
open2/read3/write4/close7/lseek8：libos共享枚举与S case匹配。stdio→_read_r/_write_r→低层、公开read/write→syscalls wrapper另核；device没有新syscall号，仍read/write。
a7调用号；a0=fd/path，a1=buf/offset/flags，a2=len/whence/mode；返回a0。disk MMIO另用blkno/cnt/addrlo/addrhi/write/cmd寄存器，非把fd直接下发设备。
F fs_open收到pathname/flags/mode，但只按固定file_table查路径，flags/mode不建立新open状态；读写传fd/buffer/length。lseek接收signed long后F原型size_t，在当前GCC/LP64回写long恢复负值；非独立规范保证。
RV64 size_t/ssize_t/off_t/long/指针8，fd与whence4；F fp_offt long8；public reent低层缺prototype导致返回int扩展F0077。disk blkno/blkcnt int32，PA低高各32；NEMU paddr32限制见F0002/F0009。
用户buf VA→内核直接读写，disk使用512字节aligned8静态bounce而非把用户VA当DMA PA；AM写bounce身份映射PA进low/high。无有效用户指针检查F0073；device也直接写调用buffer。
Finfo=char*、size_t size/disk_offset、ReadFn/WriteFn，LP64五槽40byte；生成ramdisk.h前三项与NULL回调初始化对应，fp_offt独立数组。AM_DISK_BLKIO bool+padding/ptr8/两int，总24，N侧是寄存器序列而非结构memcpy。
F普通file_offset+disk_offset对应ramdisk字节区间；本轮108项连续且等于fsimg。D用pos/512和pos%512拆块，AM/NEMU控制a0000300..327；嵌入ramdisk为可写内存区，不是设备地址。
普通read/write clamp到剩余file_size且推进实际len；EOF返回0，零len正常0。F lseek无界导致size-offset下溢F0065；错误fd OOB F0064。D设备路径忽略块容量和底层完成结果F0075，不能仅用FS长度推导安全。
file/FS偏移和返回值都是byte；AM disk blkno/blkcnt是512byte块。最后不足块通过read-modify-write保留其他字节，镜像填充至512倍数；本轮padding324byte，无把count当byte的双端错配。
F固定表全局fd和fp_offt由内核拥有；同一文件重复open共用偏移，close重置。固定表教学语义已有P6契约来源，不能推广为完整POSIX每进程FD隔离；用户FILE缓冲与这个内核对象不同。
open重置offset；close不销毁file_table/host磁盘，设备fd为固定常驻项。exec不逐fd清理，NDL退出/重入状态见F0090。NEMU FILE在进程生命周期持有；宿主写错误不通过这些对象传上来。
缺失路径-1，坏fd不统一EBADF；errno全局/重入桥错F0076。host fseek/fread/fwrite返回未检查，AM void操作→D/FS正常len，形成中间失败吞掉F0009/F0075；缺盘读0最终loader panic。
R/W公开层返回_ssize_t但低层声明F0077可截断；正常_syscall a0和F byte count匹配。device callbacks返回byte数，events返回不含NUL、audio_read固定4和fb丢尾见L03/L05/L06；不得统一当成功的len。
open→offset0→短读推进→seek→EOF0→close归零静态匹配且target验证；无独立open表、write不扩展固定文件。底层失败没有原子回滚offset/数据的契约实现；坏seek先污染状态。
NEMU盘文件来自NAVY_HOME/build/ramdisk.img，非CONFIG_DISK_IMG_PATH任意指定；DEVICE/HAS_DISK、512字节块为前提。NPC KERNEL_EMBED_RAMDISK本有后备，但先io_read不支持的DISK_CONFIG就panic F0042；guest旧ramdisk.c缺失F0086。
''',[9,42,64,65,66,67,68,73,75,76,77,79,85,86,90],
 ['重复open/close共享偏移静态核实，未冒充每进程POSIX模型。','target：read4=ABCD，SEEK_END(-2)=5，read8=2/FG，零读/EOF=0，close0，missing open=-1。','宿主磁盘不存在实测禁用→read0→loader panic；宿主短I/O/容量越界仅静态闭合至F0009/F0075。'],
 'TargetE2E-Pass（libos低层文件API+FS+AM磁盘+NEMU文件）；公开stdio/reent包装为静态，不声称所有FILE操作运行。',
 '有效历史fsimg配对不等于生成工具链配对；没有NPC实际嵌入盘运行或宿主磁盘满测试。')
chain('L03','event → nanos device/FG → AM input → NEMU/NPC',[
 ('E','navy-apps/libs/libminiSDL/src/event.c',[52,67,89,146]),('N','navy-apps/libs/libndl/NDL.c',[23,98]),('D','nanos-lite/src/device.c',[13,31,44,54]),('P','nanos-lite/src/proc.c',[89,106]),('A','abstract-machine/am/src/platform/nemu/ioe/input.c',[1,7]),('K','nemu/src/device/keyboard.c',[25,52,67,85]),('NPC','abstract-machine/am/src/riscv/npc/input.c',[1,82,91])],'''
NDL read(evtdev,..)经SYS_read3/FS事件回调；AM_INPUT_KEYBRD=8。F1/F2/F3前台选择不额外syscall，内核消费按下事件。
用户a7=3、a0=fd3、a1=buffer、a2=len；AM inl读KBD a0000060，bit15为keydown，低15位为AM keycode。没有把SDL scancode值原样当AM编号。
K send_key(uint8_t scancode,bool)映射host键；AM解码后D输出kd/ku+空格+键名+换行；E以键名反查SDL枚举，N仅把非零read变true；无事件返回0。
AM bool1/int32键码、MMIO32；SDL sym uint8、类型uint8。82个非NONE键加NONE=83，AM/NEMU/miniSDL三个实际宏序列逐项相同（key-match.json），都可放入8位sym。
D直接向调用者buf写字符串并NUL结尾；E局部128byte，正常最大键名适配；一般调用者小buf/NULL受F0066/F0073。libam桥同128byte解析，不把AM结构指针当文本。
AM_INPUT_KEYBRD_T为8byte,keycode偏移4；SDL_KeyboardEvent2byte，SDL_Event24byte含user指针；两端并非同布局复制，通过文本转换；target layout断言证明本机RV64布局。
NEMU keyboard4byte寄存器a0000060与AM一致；NPC PS/2 base10011000字节流E0/F0解析独立，不可把NEMU值写到NPC寄存器。AM/OS只约定keycode enum。
事件字符串占strlen+1但return strlen，不含NUL；D忽略len，即len0也写F0066。NDL负read被当true F0090；E更严的newline/键范围不能修复内核提前越界。
MMIO读一个编码事件，文本read返回byte数，SDL_PollEvent返回事件数量0/1；三个单位不能混同。key-match为枚举值验证不是一次读传多事件证明。
NEMU环队列/AM NPC队列拥有事件副本；用户buf由调用者拥有；SDL队列和keystate为进程全局。F键按下被内核拥有并消费，应用不得期待收到同次按下。
NEMU出队发生在寄存器读回调；D即使len不足也先取走事件，不能重试恢复。F键按下被消费、释放仍可向应用发送；keystate按真实消费更新，未提供跨前台的自动状态重置保证。
无键为NONE/0；未映射host键忽略。NEMU队列满assert，NPC小队列满丢弃；没有统一可恢复overflow错误；无输入设备/AM未启用handler可能panic，F0045保留。
D非F键返回文本长度、FG按下返回0，N bool转换再E解析出事件；SDL推送坏sym导致keystate越界F0092，不能因物理键表合法而判全部入口合法。
keydown→enqueue→MMIO dequeue→D格式化→NDL read→SDL key-state/queue；FG事件先更新fg_pcb再return0，调度下次按fg选择。非FG配置仍用fg_pcb的F0069与这条配置依赖有关。
NEMU HAS_KEYBOARD/DEVICE、SDL事件轮询且NEMU_RUNNING；NPC需真实PS/2/NVBoard，WITH_SDL=0引脚保持高无键。当前FG_PROCESS开；libam guest另受F0113，不能作为下层替代成功证明。
''',[45,66,69,73,90,92,113],
 ['len0/短buf先写再返回，静态追到F0066；没有伪造对安全缓冲区的端到端负例。','F1/F2/F3按下被消费、释放转发已按双方顺序核；旧M1 harness仅历史参考。','负read、未知键与SDL_PushEvent不是同一种错误入口，分别追到NDL/SDL状态。'],
 'Static + target layout/key-table match；本轮未注入host真实键或NPC PS/2，完整事件链NotRun。',
 '不存在缺环境导致的静态Blocked；GUI/前台交互动态未测，fceux/oslab0应用内部仍缺源。')
chain('L04','time → nanos/AM timer → NEMU RTC/time/MTIMER',[
 ('U','navy-apps/libs/libos/src/syscall.c',[104]),('N','navy-apps/libs/libndl/NDL.c',[18,20]),('S','nanos-lite/src/syscall.c',[71,75]),('A','abstract-machine/am/src/platform/nemu/ioe/timer.c',[1,8]),('R','nemu/src/device/timer.c',[22,32]),('M','nemu/src/device/mtimer.c',[10,16,23,32]),('I','nemu/src/isa/riscv32/system/intr.c',[65,73]),('B','navy-apps/libs/libam/src/ioe.c',[37,39]),('NPC','abstract-machine/am/src/riscv/npc/timer.c',[1,20]),('DT','npc/verif/linux/dtb/dts/nemu.dts',[34])],'''
SYS_gettimeofday19两端一致；AM_TIMER_UPTIME=6；SDL/NDL无额外syscall。time CSR0xc01和MTIMER寄存器不是syscall号。
a7=19，a0=timeval*、a1=timezone*，内核只用tv，ret a0=0；AM先RTC high32再low32，R只在high偏移4刷新快照，顺序匹配，非两次自由运行低/高读。
S把AM uint64 us先放long，再tv_sec=us/1000000,tv_usec=us%1000000；timezone忽略。NDL gettimeofday全局tv→uint32 ticks；SDL用无符号ticks差值，B再乘1000回AM微秒。
RV64 timeval两个long64共16；uptime64，NDL/SDL32ms；正常us小于LONG_MAX转换准确。B已丢高位再拓宽F0117。NPC ld64读mtime；NEMU MMIO支持4/8访问，CPU word64/PA32分开。
内核直接写用户timeval两字段，没有NULL/EFAULT检查F0073；NDL全局timevar保留前次值且忽略失败F0090。AM uptime结构由宏栈上临时对象返回，无跨调用借用。
timeval sec偏移0/usec8；AM uptime8byte。MTIMER mtime/cmp各8byte，RTC两个32按小端重组；layout.c明确验证当前用户/AM类型，不套宿主time_t默认。
RTC a0000048..4f；NEMU mtime0200bff8/cmp02004000；CSR time与mtime同源，NEMU MMIO a000与NPC同址SDRAM不能混用。NPC time直接读取SoC mtime；J4明确把计拍数直接作为相对us，不宣称真实CPU频率为1MHz。
gettimeofday固定16byte不携带len；RTC高低各4、CLINT8byte。两平台AM timer_init目前均无重置起点动作；NEMU RTC使用自身host-relative get_time，NPC直接用mtime计拍，不假定两个平台同一epoch。
AM us；timeval sec+0..999999us；NDL/SDL floor(ms)32；DT timebase-frequency=1000000匹配NEMU us；samples间隔见L06。AM rtc calendar占位F0055不等同uptime坏。
时钟源由NEMU进程/设备拥有，mtime_offset由MTIMER写操作改变；调用者只拿数值。NDL timevar进程全局，SDL timer回调链另有F0093重入状态问题。
NEMU get_time起点为该进程首次采样；NPC init为空、直接读取mtime；B没有跨32ms回绕生命周期状态F0117；direct SDL模减只在定义的周期内有意义，不能直接判其32位回绕错误。
S返回0无后端失败通道；非法tv进入内存/异常路径，不ENOSYS/EFAULT。REF DEVICE=n time函数为0是既有能力限制，不当成动态时钟；RTC日历占位仍CQ。
TV正常返回0并写两个字段；ticks为uint32可回绕；libam转成uint64后仍在4294967296ms回0已复现。MTIP query返回highbit|7或INTR_EMPTY，与clock API值不混淆。
legacy仅消费cpu.INTR一次锁存；mtimer依mtime>=cmp保持电平直到重编程，不OR legacy；trap由arbiter检查mie/priv/mstatus后走AM timer事件再mret。mtimecmp初始UINT64_MAX，软件yield仍可调度。
当前NEMU timer legacy默认；Linux脚本显式mtimer/1MHz DT；NEMU REF无设备时间0。HAS_TIMER关而AM无条件访问不成功。target本轮legacy与mtimer运行同一nanos fixture，未编程cmp，不构成MTIP完整回归。
''',[23,24,47,55,73,90,93,117],
 ['gettimeofday指针和NDL失败保留F0073/F0090。','原libam函数host注入ffffffff→0，观测4294967295000us→0；明确非连续运行49.7天。','MTIMER/legacy仲裁静态读取当前双方，旧M1定向测试不冒充本轮。'],
 'Target gettimeofday return PASS；mtimer模式fixture PASS（无比较器编程）；libam wrap host seam复现。',
 '未本轮完整Linux/MTIP/WFI回归、真实NPC时基测量；RTC calendar与动态声画时间同步未验证。')
chain('L05','video → SDL/NDL → nanos → AM GPU → NEMU VGA',[
 ('S','navy-apps/libs/libminiSDL/src/video.c',[44,68,96,126]),('N','navy-apps/libs/libndl/NDL.c',[27,50,98]),('D','nanos-lite/src/device.c',[61,74,81]),('F','nanos-lite/src/fs.c',[35,113,134]),('A','abstract-machine/am/src/platform/nemu/ioe/gpu.c',[1,10,22]),('V','nemu/src/device/vga.c',[1,61,90]),('NPC','abstract-machine/am/src/riscv/npc/video.c',[1,10])],'''
open2/read3用于dispinfo，lseek8/write4用于fb；AM_GPU_CONFIG9/STATUS10/FBDRAW11。SDL/NDL没有专用视频syscall，也没有隐含ioctl。
a7各file号，a0=fb fd5/disp fd4，a1=byte offset或pixels，a2=SEEK_SET或byte len；AM寄存器VGACTL32宽度高16/高度低16，SYNC在+4，像素32bit写。
NDL把canvas中心+rect坐标变screen线性偏移；SDL_UpdateRect按surface pitch/pixel format组织行；OS按offset/4拆x/y和行内w。正常整行/多行参数语义匹配，负值/越界/自定义mask有F0091/F0098/F0114。
SDL_Rect坐标int16、尺寸uint16；SDL_Surface pitch uint16、w/h int32、pixels ptr64；NDL int32乘法→syscall size_t64可能溢出变巨长。AM像素uint32，x/y/w/h int32，buf地址64。
pixels始终由用户借出，内核/AM同步复制到FB；NEMU保存VRAM而非用户指针。SDL preallocated surface按flags决定释放；IMG/BMP freesrc独立F0104/F0106，不能跨层推断所有像素缓冲都由SDL拥有。
AM GPU_CONFIG16byte,width4/height8；FBDRAW32byte,pixels8/w16/h20/sync24，已目标编译。SDL_Surface与AM结构不同，NDL传裸packed32像素；无结构跨syscall memcpy。
NEMU VGACTL a0000100/+4，FB a1000000；800×600×4=1920000byte在2MiB AM映射内。NPC FB21000000、640×480，扫描显示、sync忽略；不是NEMU的同地址MMIO。
OS len/4取整丢非4倍尾字节，offset也/4；无frame边界检查F0068。NDL宽高乘4、stride=screen_w×4与OS一致，SDL若pitch/clip不匹配可越界；合法图元才能推导复制范围。
API几何是pixel，file seek/write是byte，NEMU纹理ARGB8888/内存32bit与默认mask0x00RRGGBB匹配；自定义mask F0098不能由depth32推导颜色一致。每行sync不是每像素sync。
屏幕配置和VRAM由设备拥有；SDL拥有自建surface，PREALLOC只借pixels；NDL持固定fd全局。nwm分支把3/4/5解释为IPC资源，须nwm host配套，不是当前nanos直接设备协议。
NDL_Init缓存尺寸/Canvas，Quit不复位所有fd/尺寸F0090；用户buffer仅在write期间有效。NEMU SDL texture长期存在，sync flag在device_update清零；AM指针不在宿主异步保存。
dispinfo短读返回可读字节、不保证NUL；NDL自行终止但未健壮处理read错误/缺字段F0090。fb非法fd/地址/尺寸可能assert/OOB，不返回统一EIO/EINVAL。中间write错误被NDL忽略。
合法fb_write返回done*4；NDL_DrawRect为void无法传回短写；SDL_UpdateRect同样void。GPU ready固定true不是显示已消费确认。NEMU读取同步标志清除不是syscall返回值。
实际AM先outl(sync,1)再复制像素F0041；NEMU每条指令后device_update有机会先显示旧/半帧。因此OS传sync1并非整帧完成屏障。NPC扫描无完成握手，正常静态颜色/地址匹配不补足原子帧语义。
NEMU HAS_VGA/VGA_SHOW_SCREEN、尺寸配置与AM MMIO固定值配套；关闭VGA而AM无条件init不闭合。NPC设备实现和NEMU不同；NWM_APP只在有对应服务/fd协商时适用，不能将当前nanos /proc/dispinfo当nwm控制管道。
''',[41,64,68,90,91,97,98,104,106,110,114],
 ['矩形负值/越屏、非4byte长度、read失败、短写沿上下层追到具体未检查点；未用正常帧证明边界。','sync先发后画的真实顺序保留F0041，不以NEMU偶尔正确刷新解除。','失败时buffer仍由原调用者释放；NDL无错误返回与FD残留均记录。'],
 'Static/target layout；本轮guest仅设备初始化与读配置可达，未绘制/GUI观察完整链。',
 'NEMU真实帧/NPC扫描/窗口管理器视觉验证NotRun；不能从图像资源SHA配对推出颜色正确。')
chain('L06','audio → SDL/NDL → nanos/device → AM audio → NEMU audio',[
 ('S','navy-apps/libs/libminiSDL/src/audio.c',[15,23,27,42,52]),('N','navy-apps/libs/libndl/NDL.c',[73,78,82,88,92]),('D','nanos-lite/src/device.c',[89,95,105,113]),('A','abstract-machine/am/src/platform/nemu/ioe/audio.c',[12,23,29,34]),('H','abstract-machine/am/include/amdev.h',[23,24,25,26]),('E','nemu/src/device/audio.c',[25,48,71,88,96]),('M','navy-apps/libs/libSDL_mixer/src/mixer.c',[7,231,256])],'''
open2/write4/read3/close7；fd6=/dev/sbctl、fd7=/dev/sb。AM_CONFIG14/CTRL15/STATUS16/PLAY17，未通过专用syscall。控设备写12byte，状态读4byte。
a7 file调用，a0 fd，a1配置/PCM/状态指针，a2 bytes；AM频率a0000200、声道+4、samples+8、容量+c、init+10、count+14，sbuf a1200000；各outl32与NEMU six-reg一致。
NDL int p[3]={freq,channels,samples}，D按3int重组AM；S callback len=frames×channels×bytes/sample，NDL查询free后裁剪。NEMU SDL spec采用S16SYS，U8输入链F0096实际不匹配。
freq/channels/samples在AM int32，miniSDL samples uint16/channels uint8，宿主SDL再次窄化；PCM短整型16，小端host S16SYS与RV64 LE配对。Area指针64，AM len转uint32与大size_t可能截断；当前合法64KiB内一致。
NDL传调用者PCM VA，D用Area[buf,buf+len)，AM同步拷入ring MMIO，NEMU回调只持sbuf。S在NDL_PlayAudio后free临时stream，对正常同步copy成立；失败/重入后callback userdata寿命F0094保留。
AM_CTRL12byte三个int无padding；STATUS4byte，CONFIG8byte bufsize偏移4，PLAY16byte Area；miniSDL spec32byte callback16/userdata24；宿主SDL spec独立重建，无直接结构拷贝跨ABI，layout.c验证target。
AM与NEMU ctl a0000200..217，ring a1200000..a120ffff；OS页表包含64KiB ring。NPC IOE没有AUDIO_CONFIG handler，OS init_fs无条件查询就panic F0042；libam无audio case，默认不填结构，不能称可播放。
count/free/len都是byte且容量65536；NDL控制len12匹配，但D其他len也返回len不应用；audio_read即len0/小buf仍写4返回4 F0067。AM len>capacity永久等待F0044；S只裁free不保证整sample/frame。
freq是Hz，samples是每声道frame数/回调，channels声道数；S interval=frames×1000/freq毫秒，PCM byte=frames×channels×2。mixer Vorbis解码返回每声道样本数，乘channel与sizeof(short)，固定点长帧风险F0102另记。
应用/SDL拥有callback与userdata及临时PCM，NDL仅拥有固定fd引用；AM wr_index、NEMU rd_index/count拥有ring推进。计数读改写跨模拟线程F0043非独立拥有；锁空实现不能保证安全。
NDL close只fs_close及置-1，未到AM/NEMU关设备、未清rd/wr/count；SDL_CloseAudio未停callback F0094。重复open更新配置但后端OpenAudio可能失败F0118，原设备与寄存器可不一致。
NEMU InitSubSystem非0或OpenAudio=-1没有上行错误；D返回len，S_OpenAudio0 F0118。NDL打开失败assert、Query忽略read结果F0090；不把不支持设备当free=0可安全退化。
ctrl正常write返回12，status read返回4且内容是空闲byte而非已排队count；PLAY返回len表示已复制并排队，不表示听到。S_OpenAudio总0不能作为后端已开证明；本轮故障桩证实错误仍被接受。
真实顺序AM_init读容量→写init=1(offset16)，之后CTRL依次freq/channels/samples(offset8)触发NEMU；初次确可开，F0010不能推导首次必败。生产/消费ring回绕及underrun余部未清F0011、count竞争F0043仍在。
NEMU HAS_AUDIO+DEVICE、宿主SDL音频后端为前提；FORMAT限定S16有效链，NPC和libam断点单列。host bridge采用同步MMIO/确定失败桩，不能覆盖线程竞争；真实声卡/音乐播放不在本轮动态证据内。
''',[10,11,42,43,44,67,90,94,95,96,100,101,102,103,115,118],
 ['两端原函数bridge：首次config会开音频；第二次OpenAudio=-1仍pause并接受4byte。','非法freq/channels、空指针、len>capacity、非frame倍数、underrun、close后callback分别追到未校验/等待/残留，旧缺陷不重复编号。','后端失败、资源释放和count推进没有闭合成可靠可恢复协议，审阅闭合不表示设备协议正确。'],
 'HostSeam-Reproduced：probes2/audio-run.log，实际AM/NEMU原函数+MMIO/SDL桩；target guest只初始化音频配置。',
 '真实host音频回调并发、声音质量和GUI应用NotRun；不能把SDL dummy初始化当真实播放PASS。')
chain('L07','exec/exit/yield/brk → process/memory → AM context/VME → NEMU',[
 ('U','navy-apps/libs/libos/src/syscall.c',[69,91,115]),('S','nanos-lite/src/syscall.c',[11,25,30,42,67]),('L','nanos-lite/src/loader.c',[104,111,117,129,188]),('M','nanos-lite/src/mm.c',[6,19,25,46]),('P','nanos-lite/src/proc.c',[89,106]),('A','abstract-machine/am/src/riscv/nemu/vme.c',[1,50,71,99]),('C','abstract-machine/am/src/riscv/nemu/cte.c',[5,45]),('N','nemu/src/isa/riscv32/system/mmu.c',[1,33,78,107]),('NPC','abstract-machine/am/src/platform/dummy/vme.c',[3,7,10,13,16])],'''
SYS_exit0/yield1/brk9/execve13与U/S一致；内核yield为a7=-1，转换EVENT_YIELD；timer调度是cause highbit7，不是SYS_yield。execvp先PATH选择再execve，溢出风险F0081/F0082仍独立。
a7号、a0 code/brk/path、a1 argv、a2 envp；a0返回或启动栈。S sys_yield内部再ecall，在内核产生嵌套trap；该trap需要保存正在执行syscall的Context再由schedule选择，不可只看最外层返回寄存器。
exec参数先复制后load避免旧地址覆盖，缺文件预检后才protect；brk参数是目标break地址，_sbrk参数是增量，两端U求newbreak→S mm_brk正确区分。exit code目前忽略而重载nterm是具体实现。
指针/break/pte/Context槽64，页号/flags从uintptr_t生成；_sbrk PTRDIFF/signed增量与mm_brk无符号地址仍需溢出检查F0089/F0063。目标AS页大小int4096，PTE8byte、512项表。
loader传新PA给map、VA给ucontext(entry)，Context.pdir指新root。传入argv/env仍来自旧当前地址空间，在__am_switch前可读；无copyin/失败回滚。page table高PA截断F0002不因低地址正常示例解除。
PCB union32KiB栈与cp/as/max_brk共享基址但元数据在底部；Context288放末尾，AddrSpace32包含pgsize/area/ptr。pdir alias x0保存槽，trap不初始化导致F0024；两结构不是NEMU CPU_state CSR布局。
AM kernel root覆盖PMEM及device段；protect复制kernel root，AS area40000000..80000000。SV39 satp mode8+root>>12，NEMUwalk三级并进行U/S/MPRV权限检查；AM map却统一RWXUAD、忽略prot F0029 CQ。
new_page按n×4096推进、pg_alloc n/PGSIZE无余数保护、heap界限未核F0032/F0062；brk上取整逐页只增长、不缩回；用户栈8页、无栈碰撞界限F0063，不能由128MiB PMEM推导分配永不耗尽。
brk单位byte address、_sbrk增量byte，new_page参数page数、pg_alloc参数byte；map参数单VA/PA页；ucontext返回Context指针。native/NPC时基或fd长度不混入此单位链。
PCB拥有root和Context引用，分配器全局拥有物理页；exec分配新页但无owner回收元数据，unprotect空F0030。文件固定全局对象并非exec时拥有的独立fd；不凭free API名字推导真实释放。
exec成功切换到新cp、max_brk清零重建；旧trap不得随后覆盖新cp。switch_boot_pcb让内核yield保存boot上下文，再调度新进程；多次成功exec/exit会积累页，OS不回收沿用P6教学边界、AM通用回收仍CQ，未扩充批准范围。
exec缺文件-ENOENT可返回原用户；已存在的坏ELF/失败分配没有rollback或ENOMEM路径。brk当前总0，新页越界不变成可处理错误；NPC vme_init=false被忽略、ucontext=NULL后解引用F0070。
普通yield/brk返回0，exec成功正常不返旧地址，exit不等于机器退出。_execve把-2转-1/errno2，但公开execve reent errno桥F0076另有问题；不能用低层探针证明公开errno完整。
schedule先存prev到current->cp，再按FG与background pcb3轮转；退出重载nterm，foreground PCB仍是原槽。AM切satp再恢复CSR/mret；mscratch来自交换后用户sp导致来源判定F0023，正常fixture并未解除嵌套/时序风险。
HAS_CTE/HAS_VME/FG组合为当前；无FG配置仍访问fg_pcb F0069。NPC已选dummy VME返回false/no-op/NULL且已保留F0031 CQ，不能宣称RV64就支持U态。guest软陷入全局Context/F0113及缺源包装F0086另列；不扩展RTL。
''',[2,23,24,29,30,31,32,57,58,59,61,62,63,69,70,73,76,81,82,86,89,113],
 ['missing exec前置检查不破坏原cp/as，本轮guest通过后继续运行；非法ELF不存在等价恢复。','brk新映射可达已测，但没有资源耗尽/收缩/stack collision成功承诺。','exit/exec旧资源、trap返回、调度状态分别读实际顺序；NPC false/null失败处理断点已关联而非全链Blocked。'],
 'TargetE2E-Pass：missing exec、sbrk32、SYS_yield返回、成功exec argv/env、main return→exit→nterm；legacy与mtimer两模式。',
 '未运行长时间泄漏/分配耗尽、NPC进程切换、libam递归路径；5项既有CQ保持未决。')
chain('L08','RV64 AM/NEMU/NPC REF及golden接口',[
 ('D','npc/csrc/util/difftest.cpp',[16,23,36,41,59,75]),('R','nemu/src/cpu/difftest/ref.c',[45,65,90,95,104]),('P','nemu/src/memory/paddr.c',[27,54,78]),('T','nemu/include/difftest-def.h',[22,31]),('S','npc/csrc/soctest.cpp',[75,120,164]),('C','nemu/configs/riscv64-ref_defconfig',[1,4,6]),('G','nemu/tools/spike-diff/difftest.cc',[39,70,85,101,126]),('DU','nemu/src/cpu/difftest/dut.c',[24,67,118]),('AM','abstract-machine/scripts/platform/npc.mk',[32,61,76])],'''
此层无syscall号；动态符号memcpy/regcpy/exec/raise_intr/init/ref_display是入口契约，方向DIFFTEST_TO_DUT=0/TO_REF=1、COPY_PC=0/COPY_REG=1双方一致；不能套用户a7。
D使用cpu_context[33]存32 GPR+PC；输入regcpy always复制33槽，输出COPY_REG只写前32、COPY_PC只写32槽。D先取旧PC→exec1→取新GPR，与退休PC/退休后GPR配对，不是PC差一拍缺陷。
memcpy(addr,buf,n,direction)；regcpy有NPC三参版本和Spike二参版本，D配R、NEMU DUT配G分别一致，不能交换.so。init NPC void(void)与R void(int port)不一致F0119；端口参数不是网络连接副作用。
host LP64要求unsigned long8、bool1、size_t8，33×8=264byte；当前RV64 cpu prefix兼容。D memcpy uint64地址但R paddr_t32，合法低32地址值可用，类型宽度仍不一致/无高位保证；F0002/F0014覆盖截断/边界风险。
buf是宿主缓冲指针，addr是guest物理地址，不能互换；R addr_to_soc只验起点然后for拷n字节F0014。D向R拷flash host数组，n=FLSAH_SIZE，与实际镜像payload长度不同，数组容量须16MiB。
CPU_state首部32word GPR+PC，后续CSR/priv不属于33字packet；R selectively输出时caller必须分两次填完整。NPC Context288仅AM trap结构，与264byte差分包不同；不能用memcpy(sizeof CPU_state)覆盖D buffer。
NPC FLASH_BASE30000000/16MiB，SRAM0f000000/8KiB，MROM20000000/4KiB，PSRAM80000000/实际4MiB，SDRAMa0000000/128MiB；REF PMEM80000000/128MiB覆盖但较DUT PSRAM宽，不能作为DUT容量oracle。DEVICE=n才注册SDRAM域。
n是byte、exec n是指令条数、regcopy没有len必须约定264；R int循环n>INT_MAX溢出/跨域F0014。boot脚本/AM VMA/LMA对应八linker的执行域，错误布局F0025–28/F0071–72未消失。
PC+4 skip假定已退休32bit非压缩指令；当前无C成立。SIM时间是仿真半周期计数，不是NEMU us；REF time=0无自主timer，因此不能用当前packet替代时间/CSR对拍。
D拥有dlopen句柄/临时packet，R拥有内存和CPU状态；memcpy双向是同步字节copy。AM loader/boot拥有DUT内存初始化，REF不会从FLASH自动生成SDRAM镜像；golden G只支持TO_REF内存方向。
D skip标志下一次退休清除，MMIO由DUT处理后同步GPR/pc+4；R init只printf、不重置CPU/内存，单次dlopen生命周期是前提。detach/attach NEMU只同步PMEM/33字，不能恢复设备/CSR全部状态。
dl开/符号缺失assert；ref无通用错误返回。NPC DIFF ABORT或SIM_END最终main仍return0，既有runner必须检查日志marker，不能凭exit0。R显式raise_intr丢PC F0116；当前D仅加载该导出未调用。
D difftest_step返回true表示mismatch，caller break；exec/regcopy/memcopy均void。NEMU DUT的isa_difftest_checkregs仅GPR无PC F0015，NPC D确实比较旧PC，不能把两个路径混同。
init→copy flash→copy GPR/pc→单步比较/skip；显式intr应转vector但R仅CSR/priv变化F0116，host原函数复现。G take_trap更新PC；NEMU DUT多镜像init只拷firmware F0016，不能从Linux native通过推golden同步。
当前npc/.npc_config DIFF=0，启用需匹配DEVICE=n RV64 GARRAY REF；native DEVICE=y有设备MMIO，不是SoC REF。Spike仅NEMU DUT golden、MAFDC能力超出当前DUT子集，不能把其支持当DUT已实现；未审核RTL或扩展S/CSR packet。
''',[2,14,15,16,23,25,26,27,28,71,72,116,119],
 ['直接原REF+trap注入highbit7观察PC仍旧、CSR已变，作为F0116证据；不冒充NPC当前自动IRQ。','缺.so/符号、内存跨界、错误初始payload、skip残留、DIFF退出码逐项核；历史M1负例日志仅历史。','八linker执行/加载/堆栈域与REF注册域配对；PSRAM范围较宽和设备域差异明确，未推断物理RTL实现。'],
 'HostSeam-Reproduced：REF中断函数；ABI/配置/skip静态。未本轮完整REF .so/NPC difftest或Spike全栈执行。',
 '历史M1 REF回归不是本次测试；当前DIFF=0、NPC无VME与CSR比较范围限制不自动解除；生产REF未覆盖/安装。')
chain('L09','build configuration → generated headers/linker/fsimg → executable',[
 ('N','nemu/Makefile',[1,20,40]),('NC','nemu/scripts/config.mk',[1,20]),('A','abstract-machine/Makefile',[1,90,130]),('NP','abstract-machine/scripts/platform/npc.mk',[12,32,61]),('O','nanos-lite/Makefile',[1,18,42]),('U','navy-apps/Makefile',[100,120,160,173,175]),('L','nanos-lite/src/loader.c',[40,45,54]),('B','npc/verif/linux/boot/Makefile',[1,18,27,40,48]),('RUN','npc/verif/linux/boot/run.py',[1,45,95]),('DT','npc/verif/linux/dtb/Makefile',[1,12,21]),('I','npc/verif/linux/initramfs/Makefile',[1,24])],'''
构建不执行syscall号，但nanos update把syscall.h软链接到Navy同表；两端20枚举/内核10case匹配，未知号仍panic。生成ramdisk.h是文件项，不含syscall编号。
RV64编译/汇编决定XLEN与a7/a0 ABI，Navy -march=rv64g默认LP64D、AM NEMU/NPC均共享isa/riscv.mk的rv64g；Linux firmware另用rv64ima_zicsr_zifencei/lp64，须分别读；不能拿ISA标签保证实际不含F/D/C。fixture实际工具/ELF与编译argv留档。
ISA/ARCH/VME/HAS_VME/BOOT_MODE/LDS/BOOT_S/HEAP_SIZE从不同Make入口传递；nanos update检测HAS_VME→Navy VME=1，但历史binary不会因配置文本改变自动重链；F0085递归吞错允许旧产物。
NEMU autoconf CONFIG_RV64/ISA64与auto.conf/config保持选定宏；数据/指针宽度按目标头目标编译。生成宏改变可影响库ABI，thin archive/ISA-only路径未编码全部VME/编译参数，来源Unknown不得写已匹配。
files.h与syscall.h链接目标按link text和resolved bytes分别核；thin .a引用对象路径，不能当自含静态库。fsimg symlink按目标内容打包，source身份仍按链接文字；30 BusyBox symlink不误报漂移。
ramdisk.h每项{name,size,offset,NULL,NULL}对Finfo初始化；ELF64 Ehdr64/Phdr56和PT_LOAD消费者匹配，但consumer不校验所有字段F0057。Context/device布局由layout.c本轮交叉编译，非仅两端各自编译通过。
Navy VME40000000/非VME83000000，NEMU OS80000000；NPC flash30000000→SRAM/PSRAM/SDRAM依LDS/BOOT_S。native Linuxfirmware80000000/kernel80200000/dtb82200000，DT memory80000000/128MiB；不可拿同一bin跨平台。
本轮实际ramdisk148376064byte、108连续extents、末尾padding324，512整倍数；当前镜像大于NPC16MiBflash F0071。PT_LOAD p_memsz包含BSS，raw bin/启动清BSS另核；NPC .ramdisk不进已选copy区间F0072。
linker地址和fs offsets是byte；配置MSIZE/HEAP_SIZE也是byte，内核页4096byte。DT timebase1MHz与MTIMER us、UART clock/divisor匹配当前平台；Linux initramfs压缩byte数不等于解压后内存占用。
构建拥有输出，nanos owns生成软链接而非副本；NEMU盘文件运行期可写，因此与原fsimg长期一致不是不变量。本轮只读比较在运行隔离输入前后均保护当前镜像；no install/clone/自动git。
普通构建增量/ISA-only库缓存可残留旧ABI；Navy recursive失败仍后续安装F0085。runner验证当前源码复制→对象→ELF→bin→controlled ramdisk→guest，本轮产物有完整hash，旧ELF来源仍Unknown而非追认。
失败传播：navy libs循环/fsimg前缀-吞失败F0085，AM辅助脚本F0051–52；当前Linux脚本显式check subprocess/timeout并清FIFO，但自动shell成功以输出marker判非进程0。安装/缺工具不在本轮执行。
make成功不等于guest成功；NEMU GOOD TRAP需code0，QUIT可exit0不当PASS；NPC mismatch也main0。P9 fixture要求全部业务marker+GOOD TRAP+rc0；坏ELF/缺盘rc1只算故障观察不是正常功能PASS。
配置生成→编译单元选择→链接地址→镜像布局→监视器load→执行必须同版；本轮source-check零未解释漂移且fsimg表匹配，仍保留旧nterm VME错配F0074。X03 Linux boot全流程静态核配置/LOAD/FIFO清理，不重跑历史M1。
六个已选profile保留，NEMU native与REF配置互斥；NPC xip当前、其余LDS模式仅接口审阅。Linux依既有外部OpenSBI/kernel/BusyBox资产，缺源fceux/oslab0仍P8 Partial；不安装不重新全仓审文件，P10差集复核未执行。
''',[5,16,25,26,27,28,51,52,57,71,72,74,85,86],
 ['当前.generated config、链接、fsimg三层分别核；整套历史binary与源码/配置对应关系Unknown，未用文件存在作为证明。','隔离直编避开Make副作用，只证明所列选源/参数构建和执行；不能代替全部递归recipe运行。','X03 console finally恢复termios/信号，run.py持有唯一FIFO及child清理；外部Linux源码未纳入全面审查，pyc只按来源/消费身份。'],
 'Current-source isolated build + two target mode runs + two target failures；108 fsimg extents/hash、target layout通过；生产构建/完整Linux启动NotRun。',
 '初始四次fixture构建失败原样保留（缺私有头/AM include/头路径污染/漏logo资源），修正仅证据脚本；attempt5完整成功。历史产物不重新认证。')
assert len(chains)==9
(H/'chains.json').write_text(json.dumps(chains,ensure_ascii=False,indent=2)+'\n')
for x in chains:
 text=f'# CCR-P9 {x["id"]} — {x["title"]}\n\n2026-10-17；{x["review_status"]}。{x["meaning"]}。输入身份见[endpoints](endpoints.json)、[source-check](source-check.json)，原P1端点与补充支撑逐项可追踪。\n\n| 代码键 | 当前源码/定位 |\n|---|---|\n'
 for q in x['references']:
  assert (R/q['path']).exists(),q
  text+=f'| {q["key"]} | `{q["path"]}:{",".join(map(str,q["lines"]))}` |\n'
 text+='\n| 必核维度 | 双方实际字段、闭合结论与故障限制 |\n|---|---|\n'
 for d in x['dimensions']:text+=f'| {d["name"]} | {d["assessment"].replace("|","/")} |\n'
 text+='\n故障路径：\n\n'+'\n'.join('- '+s for s in x['failure_paths'])+'\n\n本次动态：'+x['dynamic_validation']+'\n\n限制：'+x['limits']+'\n\n关联问题：'+', '.join(f'[{f}](../FINDINGS.md#{f.lower()})' for f in x['issue_ids'])+'。未自动关闭旧问题。\n'
 (H/(x['id']+'.md')).write_text(text)
