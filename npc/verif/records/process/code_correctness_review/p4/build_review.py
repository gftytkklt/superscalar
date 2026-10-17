#!/usr/bin/env python3
"""Materialize reviewed CCR-P4 findings and per-file/condition coverage."""
import gzip,hashlib,json,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[6];CCR=ROOT/'npc/verif/records/process/code_correctness_review';OUT=CCR/'p4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def loc(path,lines):return {'path':'abstract-machine/'+path,'lines':lines,'sha256':sha(ROOT/'abstract-machine'/path)}
def issue(n,title,severity,status,locations,basis,actual,reach,validation,fix,limits):
 return dict(id=f'CCR-F{n:04d}',title=title,severity=severity,status=status,phase='CCR-P4',locations=[loc(p,l) for p,l in locations],expected_contract_and_basis=basis,actual_and_root_cause=actual,reachability_and_impact=reach,validation=validation,minimal_fix=fix,recommended_regression='在隔离副本中按该触发条件与正常对照复验；回归既有RV64双平台路径，契约问题先裁决再实施。',unconfirmed_assumptions_and_limits=limits,evidence=['P4.md','p4/file-review.jsonl','p4/probe-results.json','p4/supplement-results.json','p4/vme-results.json'])
ISSUES=[
issue(23,'NEMU用交换后的mscratch误判内核trap来源','High','Confirmed', [('am/src/riscv/nemu/trap.S',[45,47,50,57,80]),('am/src/riscv/nemu/cte.c',[14,18,20,37,39])],
 '本地trap入口约定：内核执行时mscratch=0，用户执行时为内核栈顶；必须保持当前内核栈和正确生命周期。Priv-v1.12 MPP记录实际前态。',
 'csrrw后mscratch在两种来源下均是原sp，正常为非零。C仍把非零当USER_MODE，返回同一内核context时错误装入旧栈顶。',
 '内核yield/时钟trap，handler返回原context后继续调用函数改变sp；下一trap在旧sp处分配frame，可能覆盖活动调用栈。嵌套内核trap也会被误判；并非只有U态可达。',
 '源码逐指令推导；RV64原trap/cte编译与反汇编确认csrrw、sp保存和C判定；未执行guest嵌套调度。',
 '按保存的mstatus.MPP或交换前的显式标记分类；内核返回清mscratch，用户返回设置独立有效kstack顶；初始化入口显式建立该不变量。',
 '错误np本身不会改mret的MPP；风险是后续栈选择，不能写作第一次trap就错误进入U态。'),
issue(24,'NEMU从未初始化的trap slot推断pdir内核线程标记','Medium','Confirmed',[('am/include/arch/riscv.h',[11,14]),('am/src/riscv/nemu/trap.S',[15,34,50,63]),('am/src/riscv/nemu/vme.c',[59,69])],
 'CTE/VME切换必须保存当前执行流地址空间；kcontext的NULL标记只对该已初始化Context有效，不能代表任意新trap frame。',
 'pdir覆盖gpr[0]，汇编不写slot0；__am_get_cur_as先读slot0，为零就跳过satp快照。新内核trap frame不一定等于原kcontext/ucontext对象，字节内容决定是否保存地址空间。',
 'VME开启时用户A syscall中的内核代码再次yield，新的frame slot0恰为0；切到B后返回该frame会因NULL不恢复A的satp。独立内核线程无用户地址需求时可能被掩盖。',
 'vme-host-observation：mock satp=0x81234000，零slot保留NULL，非零slot保存0x81234000；仅两个CSR表达式被替换。汇编确认slot0无写入。',
 '在每次trap上确定性保存地址空间；单独维护线程类型/地址空间继承策略，勿用未初始化栈字节推断。',
 '正常首次ucontext的固定frame可保留原pdir，不声称每次用户trap必败；多进程场景仍需P6/P9集成验证。'),
issue(25,'NPC BSS起点只对齐符号，漏清真实BSS前缀','Medium','Confirmed',[('scripts/linker-soc.ld',[34,39]),('scripts/linker-sram.ld',[42,47]),('scripts/linker-sdram-heap.ld',[31,36]),('am/src/riscv/npc/trm.c',[55,58]),('am/src/riscv/npc/boot_sram.c',[49,50])],
 'TRM进入main前静态零初始化对象必须为0；链接边界必须覆盖实际.bss。',
 '_bss_start=ALIGN(8)仅给符号赋值，未推进位置计数器；低对齐输入.bss可能从该符号之前开始，甚至_bss_start>_bss_end。',
 'xip/sram/sdram-heap，1字节.data加1字节.bss的合法输入即可；loader只清符号范围，不会初始化该字节。原始.bin含零也不会由NPC flash装载自动清SRAM。',
 '隔离GNU ld 2.42链接：xip test_bss=0xf000001，start=0xf000008，end=0xf000002；sram同样差7字节。无硬件执行。',
 '在输出节起点设置ALIGN或先执行 . = ALIGN(8)，再定义_bss_start；对原始低对齐符号和实际清零范围做断言。',
 '其他NPC脚本存在同形式，但当前.data尾部已ALIGN(8)，本probe未复现漏清，不能一律称所有模式失败。'),
issue(26,'NPC链接允许静态区占用固定栈地址','High','Confirmed',[('scripts/linker-soc.ld',[34,46]),('scripts/linker-sram.ld',[42,51]),('scripts/linker-sdram-heap.ld',[31,41]),('scripts/linker-psram-ssbl.ld',[26,34,101]),('scripts/platform/npc.mk',[65,66])],
 '启动所用栈与代码/data/BSS必须不重叠，不能仅检查整个8KiB SRAM的总大小。',
 '栈顶固定0xf001800，但没有保留栈输出段或检查静态区/SSBL末端；MEMORY只限制到0xf002000。',
 'xip/sram/sdram-heap静态BSS约7KiB仍能链接，覆盖栈顶；启动C函数或清零会破坏栈。SSBL增大时也有同一未保留栈预算的风险。',
 '三模式stack-overlap链接均退出0，BSS end分别0xf001c01/0xf001c19/0xf001c01，大于sp=0xf001800；仍小于8KiB容量。',
 '明确栈底/栈顶和最小预算，在脚本以ASSERT或专用region检查static/SSBL与stack分离。',
 '最小fixture并未运行C loader；实际损坏的地址及指令依目标栈用量，当前默认小程序不必触发。'),
issue(27,'NPC搬运假定text与rodata的LMA/VMA间距相同','Medium','Confirmed',[('am/src/riscv/npc/boot_sram.c',[38,43]),('am/src/riscv/npc/ssbl.c',[30,34]),('scripts/linker-sram.ld',[23,39]),('scripts/linker-psram.ld',[25,36]),('scripts/linker-psram-ssbl.ld',[40,51]),('scripts/linker-sdram.ld',[25,36]),('scripts/linker-sdram-rt.ld',[26,37])],
 '启动搬运须将每个ALLOC初始化节的LMA内容放到该节VMA，包含不同对齐引入的空隙。',
 'boot_sram/SSBL按_sdata-_text_vma将text+rodata整体搬运；各输出节AT>flash并未约束相对LMA/VMA偏移恒定，高对齐rodata会产生不同间隙。',
 'sram/psram/psram-ssbl/sdram/sdram-rt接受高对齐常量时，复制完成后的常量在错误位置，还可能从有效镜像末尾之外读取。xip不使用该整体搬运。',
 'aligned.S链接五模式；psram .text VMA0x80000000/LMA0x30000138，.rodata VMA0x80000040/LMA0x30000158，相对偏移0x40与0x20。源码复制会把常量放到0x80000020。',
 '按节分别提供LMA/VMA/size并搬运，或由链接脚本保证且ASSERT整个搬运区的地址差一致。',
 '本次只运行链接与反汇编，未跑硬件；不能将特定高对齐反例扩写为所有现有镜像损坏。'),
issue(28,'可调heap边界未限制到实际内存容量','Low','Robustness',[('scripts/linker-soc.ld',[50,51]),('scripts/linker-sram.ld',[55,56]),('scripts/linker-sdram.ld',[75,77]),('scripts/linker-sdram-heap.ld',[43,44]),('scripts/platform/npc.mk',[63,67])],
 'heap声明的Area应对应可用内存；用户可覆盖HEAP_SIZE，错误配置应拒绝或有明确容量前置。',
 '只定义_heap_end=start+size，没有分配受MEMORY检验的节或范围ASSERT；xip/sram的PSRAM甚至未声明为MEMORY区域。',
 '显式HEAP_SIZE=0x10000000链接成功，xip暴露256MiB堆而PSRAM只有4MiB；SDRAM变体也越过128MiB。默认0x8000未由此失败。',
 '三个oversize-heap探针link退出0，符号范围见probe-results；未访问越界硬件。',
 '验证非负大小/加法溢出并按对应内存region限制heap end，保留命令行覆盖。',
 '配置健壮性问题，不是默认堆已越界；NEMU linker无PMEM容量ASSERT同类预算限制仅记录。'),
issue(29,'NEMU VME权限与撤映射语义尚无统一契约','Medium','ContractQuestion',[('am/include/am.h',[10,12,65]),('am/src/riscv/nemu/vme.c',[37,92,96]),('am/src/riscv/nemu/cte.c',[22,25])],
 '本地MMAP_*明确含no access/read/write；AM规约§6与ics2024§4.3在权限/撤映射教学子集上不同。用户本轮允许保留CQ完成P4，不批准简化。',
 '所有leaf强制V/R/W/X/U/A/D，prot不作AM位到PTE位的转换；内核恒等映射也U可访问；pa=NULL/prot=NONE仍得到有效leaf。page fault归EVENT_ERROR且不提供mtval。',
 'NEMU vme_init返回true后map/protect/ucontext可达；若要求保护/撤映射则无法满足。不能由NPC dummy或旧教学实践推广为已批准豁免。',
 'CSR替换host观察：READ leaf flags=0xdf，NULL/NONE leaf=0xdf；未执行目标页访问。',
 '先明确AM子集；若要求保护，分开内核/用户权限，翻译MMAP位并实现撤映射/故障事件；同时审trap中的MPRV。',
 '不是Confirmed安全漏洞或ApprovedGap；实际nanos调用者留P6，批准来源仅授权CQ留档。'),
issue(30,'NEMU unprotect不回收页表的生命周期契约待定','Low','ContractQuestion',[('am/src/riscv/nemu/vme.c',[29,47,57,86,90])],
 '公开API有protect/unprotect及pgfree；AM规约描述销毁，ics2024允许顺序分配不回收。用户只批准保留CQ。',
 'protect分配根，map分配中间表，unprotect空实现且pgfree_usr从未调用；共享内核页表与用户页表的所有权未区分。',
 '成功初始化后重复protect/unprotect会持续分配；是否必须支持回收尚待既有教学子集裁决。',
 'host探针对已分配表unprotect后free_calls=0；无完整OS生命周期运行。',
 '明确调用者生命周期及共享页表所有权，再实现回收或显式文档化受限子集。',
 '不把教学文档自动当本项目批准；也不强加完整Linux VM生命周期。'),
issue(31,'NPC选入dummy VME/MPE，当前双平台栈能力未闭合','Medium','ContractQuestion',[('scripts/platform/npc.mk',[46,59]),('am/src/platform/dummy/vme.c',[3,18]),('am/src/platform/dummy/mpe.c',[3,17]),('am/src/riscv/npc/vme.c',[3,18]),('am/src/riscv/npc/mpe.c',[3,17])],
 '本轮双平台含当前HAS_VME配置；初始化返回false表示此实现没有成功提供该扩展，不能当正确性PASS；用户允许能力限制/CQ留档，不批准简化。',
 '实际选dummy而非同名npc文件；vme_init/mpe_init false，protect/unprotect/map无操作，ucontext NULL，atomic_xchg恒0且不写内存；cpu_count/current为1/0。',
 '符号在riscv64-npc可链接/可调用，但无成功初始化后的VME/MPE路径。若调用者继续调用则得到无效能力；P1当前OS配置使用HAS_VME的接线风险需P6判定，P4不宣称OS已崩溃。',
 'host链接未修改dummy文件：mpe_init=0且entry未调，cpus=1/current=0；交换7→11返回0并保留7；VME false，AddrSpace不变，ucontext NULL。',
 '先决定平台扩展支持范围；调用者应检查失败并限制不可用路径，或另行实现所需能力。单hart并不使假atomic exchange变为正确实现。',
 '不能将失败后的误用直接认作受支持路径的Confirmed缺陷；未找到ApprovedGap来源；不要求扩展NPC RTL。'),
issue(32,'NEMU VME根页初始化与分配失败依赖未声明前置','Low','Robustness',[('am/src/riscv/nemu/vme.c',[27,37,48,53,85,88])],
 '页表walk前根页必须是有效初始化表；pgalloc签名不声明零填充与永不失败。',
 'kas.ptr=pgalloc后未清零也未检查NULL；map只给新建中间页清零；protect分配失败直接memcpy。脏根PTE若V位为1会被当指针遍历。',
 '非零/复用页或分配失败回调可触发；若调用者保证首轮零页且永不失败则掩盖。本轮不审P6分配器，不推定当前OS已触发。',
 '静态数据流确认；host探针只提供零页正常allocator，没有运行故障注入。',
 '根页确定性清零并检查所有分配结果，或显式约定并检验回调前置；失败后不发布有效AddrSpace。',
 '健壮性风险，不把回调未明语义裁决为新项目承诺。')]

# Specific whole-file reviews. The six dimensions are separate and backed by P4.md.
NOTES={
'Makefile':('ARCH/ISA/platform→am/klib archive→ELF/bin；C gnu11/C++17；make解析mkdir和编译器fallback已读。','非法ARCH/缺源/缺工具显式error或fallback；不执行原树make。','image依赖每次重链接，但ARCH同名对象不跟踪flags/BOOT_MODE/MAINARGS变化；历史参数绑定Unknown。'),
'am/Makefile':('AM_SRCS加src前缀，公共规则递归archive，include目录为am/src。','仅选平台列表编译；不遍历未选npc vme/mpe作为当前实现。','继承父ARCH/变量；无独立运行期清理。'),
'am/include/am.h':('Area/AddrSpace/Event/CTE/VME/MPE签名与Context引用已核；IOE结构留P5。','失败bool与NULL、空Area/无效栈需调用方前置；F29–32。','C++ extern C只包函数声明；地址/长度uintptr_t/void*为64位。'),
'am/include/arch/riscv.h':('RV64 NR_REGS32；pdir与gpr0共用；288字节布局通过静态断言。','RVE分支仅排除导航；新frame slot0无初始化关联F24。','offset16/256/264/272/280与汇编一致；结构align8，合法调用栈须16字节对齐。'),
'am/src/riscv/riscv.h':('RV64 MSTATUS_SXL/UXL常量与MODE枚举；PTE位；MMIO内联声明仅接口。','非RV64分支不审；IOE访问行为留P5。','寄存器/地址uintptr_t；MSTATUS bit19/18/7/3在32位int范围内。'),
'am/src/platform/nemu/include/nemu.h':('RV64 ebreak/a0、PMEM128MiB、NEMU_PADDR_SPACE和PTE/PGSIZE。','设备常量不等于IOE已审；实际PMEM配置匹配当前128MiB；其他ISA分支排除。','恒等映射含PMEM/FB/audio/MMIO；M1 MTIMER地址未在此表，当前AM用legacy timer，扩展路径留P9。'),
'am/src/platform/nemu/trm.c':('heap从_heap_start到PMEM_END；_trm_init→main(mainargs)→halt；putch端口边界。','main返回进入ebreak后死循环；BSS由objcopy物化，非本C清零。','MAINARGS构建参数无自动对象失效，重建责任见构建表；repeat _trm_init无重置承诺。'),
'am/src/platform/nemu/mpe.c':('单hart entry一次运行，返回panic；cpu_count/current=1/0；atomic_exchange int32。','单核仍采用原子操作；无多核扩展承诺，entry不能返回。','C atomic默认seq_cst；需要A，当前NEMU支持；同文件不归NPC构建。'),
'am/src/riscv/nemu/start.S':('entry/_start清s0、设sp、jal _trm_init；ELF入口与bin起点一致。','无显式BSS循环；NEMU bin含BSS零内容；jal超距应由ld报错。','sp按linker4KiB对齐；gp/tp无初始化，仅当前无TLS/无gp重定位契约，不声称任意TLS可运行。'),
'am/src/riscv/nemu/trap.S':('mscratch换栈、保存30个普通GPR与原sp/CSR、C返回Context*、恢复/mret。','F23/F24；无FP/fcsr保存；支持整数上下文，非完整LP64D执行环境。','frame288保持16对齐；mepc承担返回PC，ra独立保存；MPRV使数据访问按MPP权限，关联F29。'),
'am/src/riscv/nemu/cte.c':('cte_init设mtvec/MTIE；ecall U/M分别yield/syscall，timer保留PC；handler可换Context。','F23；NULL handler并未建立np/mscratch安全性，合法CTE使用应提供handler；pagefault→ERROR关联F29。','kcontext栈尾建帧、a0/PC/SP/MPP/np初始化；未定义entry返回trampoline；iset只改MIE，不改MPIE。'),
'am/src/riscv/nemu/vme.c':('Sv39三级表、satp mode8/ASID0、用户区0x40000000–0x80000000、protect复制内核根。','F24/F29/F30/F32；对齐/合法VA/heap内PA为前置；不承诺超页输入表与多ASID。','get_satp移12对ASID0有效；中间PPN mask36低于Sv39完整44位但当前低物理内存不触发；无TLB目标无需额外sfence才能观察变更。'),
'am/src/riscv/npc/start.S':('xip/sdram-heap入口设栈后jal _trm_init。','与搬运型BOOT_S不可任意混搭；重复初始化不承诺。','栈0xf001800对齐16；BSS/data由TRM loader。'),
'am/src/riscv/npc/start_sram.S':('entry设SRAM栈、call _boot_loader，意外返回自旋。','适用sram/psram/sdram/rt，链接缺符号会报错。','无硬件初始化时序验证；la/call由RV64 medany编译。'),
'am/src/riscv/npc/start_fsbl.S':('entry设SRAM栈，call _fsbl_loader；返回自旋。','仅二级psram-ssbl默认选入。','FSBL/SSBL共用SRAM栈，需不与SSBL重叠。'),
'am/src/riscv/npc/boot_sram.c':('flash内自包含copy_bytes、搬text/rodata/data、清BSS、缓存域fence.i、跳TRM。','零长度不拷；不同模8地址一直按byte拷，尾部不越界；F25/F26/F27。','对齐8时ld/sd，长度long LP64；section归属经反汇编/链接；fence硬件效果未测。'),
'am/src/riscv/npc/fsbl.c':('flash FSBL按_ssbl_size把SSBL搬SRAM，跳_ssbl_entry。','size0跳过复制；符号取地址表示ABS size，编译/符号表核对。','copy不依赖klib/data；SRAM公开契约非缓存；无硬件运行。'),
'am/src/riscv/npc/ssbl.c':('SRAM SSBL按两段搬PSRAM主程序、清BSS、fence.i后跳TRM。','F27，零长copy跳过；无镜像完整性校验契约。','SSBL不能依赖未搬主程序，反汇编未见klib调用；栈与SSBL共享区域预算F26。'),
'am/src/riscv/npc/trm.c':('UART配置→loader data memcpy/BSS清零→main→halt；heap来自脚本。','F25/F26；调用memcpy的实现留P5，启动契约要求该函数搬运前不依赖尚未初始化全局。','UART宏54/1与构建关联；重复loader会重置静态数据，非运行期API；MMIO时序留硬件/P5。'),
'am/src/riscv/npc/cte.c':('M-ecall与timer分类；handler返回Context，kcontext设置PC/a0，iset读写MIE。','U ecall与pagefault→ERROR，当前无成功VME；无需把不支持U返回当正常能力。','不设置mie，与NEMU不同；NPC公开机器级中断行为未动态验证，不能套NEMU门控作确定错误。'),
'am/src/riscv/npc/trap.S':('保存x1,x3–31及3CSR，sp由frame+288隐式恢复，使用返回Context指针。','未保存gpr2；不能任意改其字段重定向SP，当前kcontext/内核trap的frame+size成立。','x0/pdir/np不由asm保存；无user-kstack换栈/FP；整数内核CTE范围，切换不同frame恢复对应栈。'),
'am/src/platform/dummy/vme.c':('NPC实际选入：init false；protect/unprotect/map空；ucontext NULL。','F31；无成功初始化路径，不把空操作算作VME正确。','无分配/所有权变更；重复调用仍失败；恢复支持需另行契约/实现。'),
'am/src/platform/dummy/mpe.c':('NPC实际选入：init false且entry不执行；cpu_count/current=1/0；交换无操作。','F31；atomic_xchg观察旧值0/地址不变，单hart不能证明原子交换已实现。','无成功MPE生命周期；硬件不具A也不能据此隐含批准dummy。'),
'am/src/riscv/npc/vme.c':('未选入的同名占位，字节与dummy/vme一致。','F31；不作为实际NPC运行路径或VME已实现证据。','静态API行为同dummy；build脚本明确排除该文件选源。'),
'am/src/riscv/npc/mpe.c':('未选入的同名占位，字节与dummy/mpe一致。','F31；不能因该文件存在或cpu_count1判断能力。','静态API行为同dummy；当前符号来自platform/dummy。'),
'scripts/isa/riscv.mk':('rv64g/medany/strict-align/fno-pic，elf64lriscv；ARCH_H覆盖为riscv.h。','实际GCC默认lp64d已测；无显式mabi，整数Context不保存FP；不声称支持FP。','-march是允许指令集而非执行覆盖；P5/P7核具体运行时与第三方ABI。'),
'scripts/riscv64-nemu.mk':('共用RV64+NEMU平台，并选nemu start/cte/trap/vme。','有效ISA_H=riscv/riscv.h；无其他ISA路径纳入。','配置作用于当前ARCH；本次直接等效编译，未运行make。'),
'scripts/riscv64-npc.mk':('共用RV64+NPC平台选源。','不隐式选npc/vme.c或mpe.c。','宏/ABI与NEMU同源，启动与链接按平台区别。'),
'scripts/platform/nemu.mk':('NEMU TRM/MPE/IOE清单，链接0x80000000、entry0，objcopy含BSS。','run/gdb转发有生产副作用；本轮不运行；IOE只审选源不审语义。','MAINARGS/flags变化不自动使既有.o过期；产物配对需干净输出，旧archive Unknown。'),
'scripts/platform/npc.mk':('当前xip，六BOOT_MODE及LDS/BOOT_S命令行覆盖；UART54/1，heap默认32KiB。','F31/F28；非法模式落xip分支；显式错配LDS/BOOT_S非支持组合，需调用方约束。','BOOT_S变化改archive成员但同名对象CFLAGS变化无依赖；不混用旧参数产物。'),
'scripts/linker.ld':('NEMU text/data PT_LOAD，bin物化BSS；stack从BSS后对齐4KiB再留32KiB，heap随后。','无MEMORY/heap上界ASSERT；过大程序可超过PMEM，当前fixture小；.data.*与.sdata由ld orphan放置，样本不穷举。','_start=0x80000000；ELF PT_LOAD与bin对照；C/gp/TLS通用性未承诺。'),
'scripts/linker-soc.ld':('flash XIP，data LMAflash→SRAM，BSS SRAM，heapPSRAM，固定SRAM栈。','F25/F26/F28；mrom未使用；flash/SRAM已定义容量。','8字节data/rodata，BSS起点问题；默认模式，链接探针有复现。'),
'scripts/linker-sram.ld':('flash bootloader，主程序SRAM，heapPSRAM。','F25/F26/F27/F28；主程序必须给固定栈留空间。','text/rodata/data分节AT>flash；整体搬运对齐假设不成立。'),
'scripts/linker-psram.ld':('flash bootloader，主程序PSRAM，SRAM栈，堆到0x80400000。','F27；RT KEEP表仅链接保持，不审RT运行时；data尾ALIGN8使本probe BSS完整。','堆从页对齐BSS尾；HEAP_SIZE不使用；容量由MEMORY限制静态段。'),
'scripts/linker-psram-ssbl.ld':('FSBL flash→SSBL SRAM→主程序PSRAM；堆到PSRAM顶。','F26/F27；额外am-apps/RT表仅布局职责，不审P5接入。','_ssbl_size为ABS；BSS尾表可额外对齐；主程序与SSBL分离。'),
'scripts/linker-sdram.ld':('flash bootloader→主程序SDRAM，heap从BSS后页对齐+HEAP_SIZE。','F27/F28；MEMORY128MiB只限制静态段不限制heap符号。','RT表KEEP而data尾对齐8；SRAM只用栈。'),
'scripts/linker-sdram-heap.ld':('flash XIP，data/BSS SRAM，heap从SDRAM基址起。','F25/F26/F28；注释16MB与MEMORY128MiB不一致，地址范围以公开配置/实际MEMORY为准。','旧注释mmio skip不作当前REF支持证明；P3/P9负责REF。'),
'scripts/linker-sdram-rt.ld':('显式LDS变体：SDRAM程序/堆至0xa8000000，SRAM栈。','F27；RT表/am-apps数据BSS仅检查链接布局，语义留P5。','需匹配start_sram.S；不是BOOT_MODE额外自动选项。'),
'.gitignore':('build/与默认忽略规则，源码扩展名白名单。','不改跟踪规则；ignored证据不随普通commit备份。','无运行期对象/初始化职责。'),
'README':('AM五种抽象的导航说明，不代表每平台支持全部扩展。','不以顶层宣传覆盖dummy失败。','无运行期对象/初始化职责。'),
'LICENSE':('MIT授权及来源边界登记。','免责声明不免除本次审阅义务。','不做上游无关历史审计；无运行期对象。'),
 'tools/logisim-img.py':('工具读取4字节分拆inst和4字节lane；当前两平台脚本未调用。','尾部不足4字节会索引失败、无参数直接报错，但不是已选双平台启动链，不扩大为工具修复。','只判选入/生产消费关系；输出在输入相邻目录，本次未执行。')}

def main():
 if (OUT/'source-evidence.json').exists():raise SystemExit('Frozen P4 result exists; do not regenerate over reviewed evidence')
 (OUT/'findings.json').write_text(json.dumps(ISSUES,ensure_ascii=False,indent=2)+'\n')
 old=json.loads((CCR/'findings.json').read_text());old=[x for x in old if x.get('phase')!='CCR-P4'];assert len(old)==22
 (CCR/'findings.json').write_text(json.dumps(old+ISSUES,ensure_ascii=False,indent=2)+'\n')
 bypath=collections.defaultdict(list)
 for i in ISSUES:
  for l in i['locations']:bypath[l['path']].append(i['id'])
 prior=[json.loads(l) for l in gzip.open(OUT/'coverage.before.jsonl.gz','rt')];files=[];branches=[];out=[]
 for row in prior:
  if row.get('effective_phase')!='CCR-P4' or row['review_status']=='Excluded':out.append(row);continue
  path=row['path'];p=ROOT/path;assert sha(p)==row['source_sha256']
  generated=row['classification']=='generated_or_build_artifact'
  if generated: notes=('S03: archive/object头及依赖路径逐件取证，见artifact-review.json；声明生成链来自共用Makefile/平台脚本。','历史源码/config/flags精确配对Unknown；不把旧.o/.a当本次功能验证。','P4仅启动/ABI/来源；IOE/klib运行时内容保留P5，未逐条重审机器码。')
  else:notes=NOTES[path.removeprefix('abstract-machine/')]
  disposition='S03ArtifactBoundary' if generated else 'ReviewedStatic'
  row['review_status']='ReviewedStatic'
  row['p4_review']={'disposition':disposition,'responsibility':'P4 startup/link/context/VME/MPE only','paths_reviewed':notes[0],'boundary_failure':notes[1],'abi_lifetime_config':notes[2],'source_sha256':sha(p),'evidence':'P4.md / p4/probe-results.json / p4/file-review.jsonl','dynamic_validation':'No RV64 guest/hardware execution; compiler/linker/host probes separately recorded','scope_limit':'P5 IOE/klib/runtime, P6 OS and other ISA semantics not reviewed'}
  row['issue_ids']=sorted(set(row.get('issue_ids',[])+bypath[path]));row['evidence_ids']=sorted(set(row.get('evidence_ids',[])+['CCR-E-P4-static','CCR-E-P4-probes']))
  row['normal']=notes[0];row['boundary_zero_empty_invalid']=notes[1];row['failure_state_return_cleanup']=notes[1]+' '+notes[2]
  row['integer_alignment_lifetime']=notes[2];row['init_repeat']='一次启动/扩展初始化；初始化失败不得视为能力可用。'+notes[1]
  row['conditional_upstream_downstream']=notes[2]+' P4.md双平台对照；后续责任字段保留。'
  row['limits']=list(dict.fromkeys(row.get('limits',[])+['P4责任已审；旧P1 Pending文字为历史；P5/P6/P9责任仍按各自阶段，未运行RV64 guest或硬件。']))
  if row['row_kind']=='file':
   files.append({'row_id':row['row_id'],'module_id':row['module_id'],'path':path,'line_range':row['line_range'],'source_sha256':sha(p),'issue_ids':row['issue_ids'],**row['p4_review']})
  else:
   condition=row['function_or_path'];evaluation='结构指令/guard，不作为独立功能测试。'
   if 'riscv_e' in condition:evaluation='RV64非E：defined(__riscv_e)=false；仅32-GPR/a7有效臂审阅，RVE体排除。'
   elif '__riscv_xlen' in condition:evaluation='__riscv_xlen=64；LOAD/STORE=ld/sd，XLEN8，RV64 status宽度有效。'
   elif '__cplusplus' in condition:evaluation='C关闭、C++开启extern C；声明链接性核对，未执行C++运行时。'
   elif '__ISA_' in condition or '__ARCH_X86' in condition or condition=='#elif':evaluation='该非RV64臂不审；RV64 nemu_trap取__riscv分支，DEVICE_BASE取非x86臂。'
   elif '__riscv)' in condition:evaluation='RV64有效分支：a0/ebreak。'
   elif 'BOOT_MODE' in condition:evaluation='当前xip；sram/psram/psram-ssbl/sdram/sdram-heap为保留变体，八脚本probe覆盖合法搭配。'
   elif 'WITH_SDL' in condition:evaluation='当前0→UART_DIVISOR54，1/y→1；时序与IOE不在本次运行验证。'
   elif 'MAINARGS' in condition:evaluation='make定义时使用其字符串，否则空串；同名对象不跟踪宏改变。'
   elif 'UART_DIVISOR' in condition:evaluation='平台宏优先，未定义回退54；P5/硬件实效未测。'
   elif condition.startswith('ifeq'):evaluation='构建默认目标/检查/fallback分支已静态核；不运行原Makefile；有效ARCH两平台，工具可用。'
   row['p4_review']['condition_evaluation']=evaluation
   branches.append({'row_id':row['row_id'],'path':path,'line_range':row['line_range'],'condition':condition,'evaluation':evaluation,'file_review':path,'evidence':'P4.md / p4/file-review.jsonl'})
  out.append(row)
 assert len(files)==120 and len(branches)==78
 for name,rows in [('file-review.jsonl',files),('branch-review.jsonl',branches)]:
  (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
 (CCR/'coverage.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in out))
 report={'date':'2026-10-17','phase':'CCR-P4','head':'1d76133','files':len(files),'conditional_rows':len(branches),'generated_boundary_files':78,'source_navigation_files':42,'source_identity_drift':[],'coverage_after_sha256':sha(CCR/'coverage.jsonl'),'coverage_before_sha256':hashlib.sha256(gzip.decompress((OUT/'coverage.before.jsonl.gz').read_bytes())).hexdigest(),'issue_status_counts':dict(collections.Counter(x['status'] for x in ISSUES)),'issue_severity_counts':dict(collections.Counter(x['severity'] for x in ISSUES)),'module_file_counts':dict(collections.Counter(x['module_id'] for x in files)),'authorization':'用户仅授权P4；2026-10-17补充允许保留ContractQuestion/能力限制完成，不批准教学简化。'}
 (OUT/'source-evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 # Append-only P4 findings section; preserve previous phase records verbatim.
 f=CCR/'FINDINGS.md';s=f.read_text();marker='\n<a id="ccr-p4-findings-20261017"></a>'
 assert marker not in s
 s+=marker+'\n## CCR-P4 — 双平台启动、链接、Context（2026-10-17）\n\n新增CCR-F0023–F0032：5 Confirmed、2 Robustness、3 ContractQuestion；严重度H2/M5/L3。累计32项，其中27 Confirmed。用户明确允许CQ和能力限制留档完成P4，不批准简化；没有修复代码。\n'
 for i in ISSUES:
  s+=f"\n### {i['id']} — {i['title']}\n\n- **{i['severity']} / {i['status']} / CCR-P4**\n"
  s+='- 位置：'+'；'.join(f"`{l['path']}:{','.join(map(str,l['lines']))}` SHA256 `{l['sha256']}`" for l in i['locations'])+'\n'
  for key,label in [('expected_contract_and_basis','预期/依据'),('actual_and_root_cause','实际/根因'),('reachability_and_impact','可达性/影响'),('validation','本次证据'),('minimal_fix','最小建议'),('recommended_regression','回归'),('unconfirmed_assumptions_and_limits','限制')]:s+=f'- {label}：{i[key]}\n'
 f.write_text(s)
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
