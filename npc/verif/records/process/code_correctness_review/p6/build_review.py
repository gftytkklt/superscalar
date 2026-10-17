#!/usr/bin/env python3
"""Add only P6 responsibilities to frozen coverage; preserve original identities."""
from pathlib import Path
import json,gzip,hashlib,re,os,collections
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());B=H.parent
rows=[json.loads(s) for s in gzip.decompress((H/'coverage.before.jsonl.gz').read_bytes()).splitlines()]
issues=json.loads((H/'findings.json').read_text());files=[];branches=[]
keys=['normal','boundary_zero_empty_invalid','failure_state_return_cleanup','integer_alignment_lifetime','init_repeat','conditional_upstream_downstream']
spec={
'Makefile':['ARCH派生ISA，NPC独立加内嵌宏，SRCS全src；未执行解析/构建','HAS_NAVY空时touch空占位并非可启动OS；native体不属RV64','update递归make失败按make规则中止，后续ln是固定生成链接；F0074当前镜像配对不符','资源S通过touch强制更新，当前ramdisk148376064；F0071容量；未选任意覆盖参数','每次update重做navy ramdisk并刷新3链接；命令有自动Git等副作用故未运行','HAS_VME grep精确当前#define生效，两平台VME1；资源COPY F0072；OS/AM选源分别核'],
'include/common.h':['HAS_CTE/HAS_VME/FG_PROCESS生效并派生MULTITASK','注释要求恰一个stage；未强加任意宏组合支持','无stage会loader panic/无进程，多stage按elif优先且无compile-time校验，为配置前提','宏不持有状态；结构来自AM/klib公共头','include guard防递归，debug→common可终止','有效FG、其它保留stage分别审；测试KLOAD/NTERM/MULTIPROGRAM/TIME_SHARING调度F0069'],
'include/debug.h':['Log与panic/assert统一输出并halt1','cond只求值一次，assert不会因NDEBUG关闭','panic宏在halt noreturn契约下终止；不是syscall错误码','可变参格式风险承接klib P5，日志不改变OS对象所有权','guard与common递归保护，重定义assert明确','所有两平台共用；host halt stub退出90只作探针'],
'include/fs.h':['fd int、read/write/seek long，size_t len/offset；与定义逐项匹配','SEEK_SET enum仅未声明时定义；负offset转换F0065','没有统一errno承诺；ramdisk_read/write声明当前未使用，无链接调用','RV64 long/pointer8，fd4；device回调另size_t','头guard；无资源分配','navy off_t signed long→size_t路径核；主平台共用'],
'include/memory.h':['PGSIZE默认4096、PG_ALIGN与new_page/mm_brk声明一致','页回调整页输入前提有讲义和AM实际调用依据','返回指针未标NULL/失败；实际allocator无检查F0062','页对齐宏与PCB对齐共同作用','guard/default PGSIZE；init只调用一次','AM allocator以bytes调用pg_alloc，nanos以page数调用new_page，单位转换已核'],
'include/proc.h':['PCB union32KB，cp/as/max_brk在底部；函数声明与实现一致','栈到底会覆盖PCB字段，argc VLA风险F0061','max_brk注释明确不释放；未据此取消OOM检查','PCB页对齐，Context288在顶端；current/fg长期静态指针','5个静态PCB零初始化；ucontext重新使用该内核栈','AM Area和AddrSpace布局核；NPC五份容量F0071'],
'src/main.c':['mm→device→irq→fs→proc→yield次序；首次trap在proc建立之后','HAS_CTE off不yield；该选项与当前FG不组成有效运行场景','各init多数void/忽略能力bool，NPC失败F0070/F0042；最终panic显式不可达断言','logo资源自带尾NUL；无main局部指针被长期保存','只启动一次，无重入承诺','两个目标共用main；ct e初始化不能代替能力验收；未真实guest启动'],
'src/mm.c':['共享heap.start page-align，pg_alloc n/4096并清零，brk按峰值增长','零页仍可对齐推进；容量/乘法/round溢出F0062；brk区间F0063','分配无失败分支，brk总0；free_page panic，顺序不回收有讲义依据','GNU void*字节运算用于目标GNU11；无堆末端/地址有效性校验','init_mm不重置heap.start且vme_init回调更新；非可重入保证','NPC false被忽略F0070；NEMU allocator清零满足P4回调前提但不保证容量'],
'src/loader.c':['合法ELF非页对齐段拷文件+BSS、用户参数PA写VA保存及max_brk重置','ELF头/段/entry/溢出F0057/58，共页F0059，stack对齐/容量F0060/61','missing预检保持pcb；其它失败不回滚。固定sfs漏close不消耗动态fd；页不回收有依据','strlen转int、VLA、sp/USTACK_TO_PA算术；旧argv在loader前复制；当前satp仍旧，字符串生命周期可达','每次protect/newstack替换cp，内存单调耗尽F0062；非重入支持未承诺','LP64 Elf64有效；TEST_DUMMY/FILE早期配置需禁VME；navy _start/call_main核；NPC NULL ucontext'],
'src/proc.c':['FG4进程、boot current、前台与pcb3交替，按键选择0..2','其它保留stage fgNULL导致F0069；set_fg只被有效常量0..2调用','current->cp先存prev；fallback若cp空会改变current，正常FG全部cp有效','PCB静态 lifetime长；kernel context参数为常量，hello j极长运行int溢出未动态达到','init_proc一次；重入会累计分配且未释放，未承诺支持','irq TIMER/YIELD均可调度；真实AM切satp与mscratch存在F0023/24，host不代验'],
'src/irq.c':['SYSCALL→do_syscall→原context；YIELD/TIMER→schedule返回选定frame','只有MULTITASK或TEST_NTERM才分发调度事件','PAGEFAULT/ERROR/default panic；无copy故障恢复F0073','回调返回Context指针由PCB/当前栈拥有，不能返回栈局部临时对象','init_irq注册静态do_event一次，cte_init bool忽略，当前两实现返回true','NEMU U/M ecalls和timer vs NPC M-only/无VME，两个入口不能混称支持'],
'src/syscall.c':['a7/a0-a2→uintptr数组，10调用→long→a0；timeval微秒拆分','无效号panic；fd/指针/长度下传，F0064/73；off_t转换F0065','exec missing-ENOENT，普通open-1；exit reload失败会返回，当前目标存在；未知调用不承诺ENOSYS','有效用户VA由MPRV/旧satp访问；argv调用时复制；tv字段RV64各8','exec先替换当前PCB，再boot/yield防旧frame保存覆盖；不回收旧页','libos共享号、寄存器、负返回及_start/main/exit实际端点核；STRACE dormant表全'],
'src/syscall.h':['链接到libos唯一0..19枚举；OS使用10号','其余枚举不表示已实现','guard保护，多余syscall内核panic、用户端多数dummy','号传uintptr，返回intptr，二者64位；无独立重复头漂移','链接由update刷新；未改链接','仅核OS ABI；libos内部完整实现责任仍P7'],
'src/fs.c':['108普通+8设备；fd索引、共享offset、普通remain短读写、设备分派','坏fd F0064；负/越界seek F0065；零read仍先索引；open255截断无当前匹配别名','missing=-1；close0/reset无打开状态有讲义；malloc无失败检查继承F0037/62','off_t/size_t混合按GNU LP64分析；offset按实际返回递增；不存user buf','init_fs分配offset表清零并init disk/GPU/audio，只调用一次；复调泄漏未承诺','NPC CONFIG缺失在fallback前failF0042；fb特殊绕过sizeF0068；files表与image逐项核'],
'src/files.h':['全部108条Finfo生成初始化唯一连续，边界在image内','无重名、负值、越末端；48 ELF64只有nterm超用户域F0074','生成文件不是已验证编译配置；缺源/旧binary配对Unknown保持','常量size/offset为字节，RV64 size_t可表示；尾padding324不属文件','update指向navy/build/ramdisk.h；本轮不重生成','仅审生产消费边界和loader输入，不提前审navy app实现'],
'src/disk.c':['512字节bounce buffer、跨块read/RMW write；embed减法截断','设备offset+len/容量未检F0075；embed offset>=size/零/尾正常','AM void块接口无错误返回，函数总len；无盘无embed读0；NPCCONFIG先failF0042','blkbuf静态aligned8，恒等内核映射PA可DMA；用户buf仅memcpy，不跨返回保留','单hart陷阱MIE关闭，本路径不yield；重复init状态未完全重置，非承诺','NEMU设备真实同步，NPC嵌入分支受F0071/72阻断；不假设通用异步磁盘已支持'],
'src/device.c':['串口len字节、event格式、dispinfo文本、FB逐行、audio12/4/Area协议','event忽略lenF0066；audio短lenF0067；FB边界F0068；dispinfo允许忽略offset','未查device present；NPC CONFIG缺失F0042；audio非12返回len但不配置是域外限制','buf同步消费不持有；GPU像素4字节，time通过syscall；key合法常量受AM生产者约束','ioe_init一次；音频读bufsize缓存；重复init/真实并发未测','MULTIPROGRAM显式yield，FG键切只改指针；NDL必要调用边界核，P8主体未展开'],
'src/resources.S':['logo incbin后.byte0；NPC单独可写.ramdisk并导出start/end','当前148MB像超过容量F0071；tiny fixture也复制遗漏F0072','缺incbin输入应汇编失败，不运行update补源','链接符号作为连续地址范围；section aw不等于启动时自动搬运','Make触碰resources.S为更新依赖；无runtime初始化代码','KERNEL_EMBED仅NPC；NEMU通过AM设备而不是内嵌；6脚本孤儿节放置留证'],
'resources/logo.txt':['纯ASCII启动logo，resources.S追加NUL','作为printf%s单个参数，不把ASCII艺术视为格式串','无函数/资源回收语义','文本字节由链接纳入只读区，lifetime全程','只读一次启动打印','NEMU/NPC共用，资源hash固定'],
'README.md':['描述固定文件/页管理/双任务的原项目导航','列9syscall是历史简介；当前10个处理入口，未用陈旧数作分母','外链只作来源导航，不运行命令','无指针/状态对象，N/A','静态导航无需初始化','双平台现状以BUILD_PATHS与P6事实为准'],
'.gitignore':['规则允许源码/Make/README/logo，忽略产物和生成头','不以普通git status替代build/link哈希核对','无执行/清理动作','无运行时对象，N/A','无初始化','遵守原规则，不force add/改变跟踪策略'],
'src/.gitignore':['files.h/syscall.h生成链接忽略','链接目标单独hash固定','不代表缺失可免审','链接文本与resolved bytes分开','update生成，不在本轮执行','关联navy产物以OS消费端核'],
'.vscode/settings.json':['只设random/proc.h语言关联','JSON可解析，无运行代码','无错误传播/资源语义，N/A','无运行时状态，N/A','编辑器配置，N/A','不参与两平台构建，不以其推定编译选源']}
assets={x['path']:x for x in json.loads((H/'artifact-review.json').read_text())}
for r in rows:
 if r.get('review_scope')=='Excluded' or not ('CCR-P6' in r.get('effective_phase_responsibilities',{}) or r.get('effective_phase')=='CCR-P6'):continue
 path=r['path'];short=path.removeprefix('nanos-lite/');ids=[x['id'] for x in issues if any(l['path']==path for l in x['locations'])]
 if path.endswith('/device.c') or path.endswith('/disk.c'):ids+=['CCR-F0042']
 if r['row_kind']=='file':
  if short.startswith('build/'):
   a=assets[path];vals=['S03身份/生成消费核对；'+a.get('producer_consumer','readelf ELF64/RISC-V或原始镜像；历史构建身份'), '边界由对应源码/文件表审；本旧产物不作当前功能判据','失败日志仅原历史截面，未重跑；旧ramdisk.o无当前src对应，不混入当前SRCS','记录size/hash/ELF metadata或.d依赖；binary/source/config配对Unknown','不执行、不覆盖历史build；原始字节保留','依赖和目标文件名分别记NEMU/NPC；不能从对象存在推定平台启动通过'];depth='S03Artifact'
  else: vals=spec[short];depth='GeneratedInterface' if short in ['src/files.h','src/syscall.h'] else 'SourceOrConfiguration'
  rec={k:r[k] for k in ['row_id','module_id','path','source_sha256','inventory_id']};rec.update(dict(zip(keys,vals)));rec.update({'depth':depth,'issue_ids':sorted(set(ids)),'evidence':['OS_RUNTIME.md','p6/probe-results.json','p6/supplement-results.json','p6/ramdisk-review.json'],'review_status':'ReviewedStatic','dynamic_validation':'See named isolated probes; guest NotRun'})
  files.append(rec);r.update({k:rec[k] for k in keys});r['p6_review']=rec
 else:
  vals=spec[short];ln=r['line_range'][0];line=(R/path).read_text().splitlines()[ln-1].strip()
  if short=='Makefile':
   ev={11:'NEMU false / NPC true：仅NPC加KERNEL_EMBED_RAMDISK',14:'闭合NPC差异块',18:'两RV64目标false；native体Out of Scope',20:'两RV64进入，INC_PATH选本地newlib',22:'闭合平台include分支',27:'HAS_NAVY=1，空值分支inactive；保留占位行为审阅',30:'HAS_NAVY空才touch文件；当前不执行，空生成物不等于有效镜像',31:'当前HAS_NAVY=1有效臂',33:'目标syscall.h存在，缺失时make error；本轮未求值make',35:'闭合依赖缺源检查',41:'当前HAS_VME grep真→ISA=riscv64 VME=1',47:'闭合HAS_NAVY选择'}[ln]
  elif '__LP64__' in line:ev='RV64当前true：Elf64；32位体Out of Scope，仅保留结构导航'
  elif 'TEST_' in line or 'MULTIPROGRAM' in line or 'TIME_SHARING' in line:ev='当前FG及派生MULTITASK按表达式选择；各单选stage分支已逐体核，非FG调度F0069；不是任意宏组合支持'
  elif 'FG_PROCESS' in line:ev='当前FG_PROCESS true，按键消费/4进程分支；单选其它stage inactive'
  elif 'KERNEL_EMBED_RAMDISK' in line:ev='NEMU false / NPC true；NPC结构包含资源和fallback，但缺CONFIG使实际更早失败'
  elif 'HAS_VME' in line:ev='当前两目标宏true；NEMU有实现，NPC返回false不能因此视为VME成功；off臂静态核'
  elif 'HAS_CTE' in line:ev='当前true；off臂不注册/不yield且不适配FG调度，不宣称有效组合'
  elif 'STRACE' in line:ev='当前false；on臂日志名/参数/返回已静态核，格式支持沿P5'
  elif line.startswith('#ifndef'):ev='include guard首次进入/再次跳过；SEEK_SET/PGSIZE按公共头默认值；不是独立功能测试'
  elif 'ifdef assert' in line:ev='klib-macros已定义assert，此处undef后本地统一重定义'
  else:ev='结构导航else/endif：继承对应上层宏/平台分支，非独立场景；详见该文件六维结论'
  rec={k:r[k] for k in ['row_id','module_id','path','source_sha256','line_range']};rec.update({'source_line':line,'condition_evaluation':ev,'disposition':vals[5],'abi_lifetime':vals[3],'issue_ids':sorted(set(ids)),'review_status':'ReviewedStatic','evidence':['OS_RUNTIME.md','p6/file-review.jsonl']});branches.append(rec);r['p6_review']=rec
  for k,v in zip(keys,vals):r[k]=v
 r['review_status']='ReviewedStatic';r['dynamic_validation']='NotRun (guest); isolated evidence in p6/probe-results.json';r['issue_ids']=sorted(set(r.get('issue_ids',[])+ids));r['evidence_ids']=r.get('evidence_ids',[])+['CCR-E-P6-OS'];r['limits']=['P6职责静态已审；动态仅隔离host/compiler/link probes，非guest/硬件/全栈PASS；未来P7/P8/P9责任不前移']
for n,x in [('file-review.jsonl',files),('branch-review.jsonl',branches)]: (H/n).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
(B/'coverage.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
# Supporting interface/source identity does not change U/A coverage responsibilities.
support=['navy-apps/README.md','navy-apps/libs/libos/src/syscall.c','navy-apps/libs/libos/src/syscall.h','navy-apps/libs/libos/src/crt0/start.S','navy-apps/libs/libos/src/crt0/crt0.c','navy-apps/libs/libndl/NDL.c','navy-apps/libs/libc/include/sys/_types.h','navy-apps/libs/libc/include/sys/types.h','navy-apps/libs/libc/include/sys/_timeval.h','navy-apps/libs/libc/include/elf.h','abstract-machine/am/include/am.h','abstract-machine/am/include/amdev.h','abstract-machine/am/include/arch/riscv.h','abstract-machine/am/src/riscv/nemu/vme.c','abstract-machine/am/src/riscv/nemu/cte.c','abstract-machine/am/src/riscv/nemu/trap.S','abstract-machine/am/src/platform/dummy/vme.c','abstract-machine/am/src/riscv/npc/ioe.c','abstract-machine/am/src/riscv/npc/trm.c','abstract-machine/am/src/riscv/npc/ssbl.c','abstract-machine/am/src/platform/nemu/ioe/disk.c','abstract-machine/am/src/platform/nemu/ioe/audio.c']+['abstract-machine/scripts/'+s+'.ld' for s in ['linker-soc','linker-sram','linker-psram','linker-psram-ssbl','linker-sdram','linker-sdram-heap']]
(H/'support-sources.json').write_text(json.dumps({p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in support},indent=2)+'\n')
print('files',len(files),'conditions',len(branches),'modules',collections.Counter(x['module_id'] for x in files))
