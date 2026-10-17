#!/usr/bin/env python3
"""Materialize CCR-P7 review decisions from frozen inputs; no production writes."""
from pathlib import Path
import collections, gzip, hashlib, json, re, shutil

ROOT=Path(__file__).resolve().parents[6]
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def lines(p,x): p.write_text(''.join(json.dumps(y,ensure_ascii=False)+'\n' for y in x))
rows=[json.loads(l) for l in gzip.open(HERE/'coverage.before.jsonl.gz','rt')]
old=json.loads((HERE/'findings.before.json').read_text())
assert len(old)==75
findings=[]
def issue(n,title,status,severity,locs,functions,contract,actual,reach,validation,fix,regression,limits,evidence):
    locations=[dict(path=p,lines=ls,sha256=sha(ROOT/p)) for p,ls in locs]
    f=dict(id=f'CCR-F{n:04}',title=title,severity=severity,status=status,phase='CCR-P7',
      locations=locations,functions=functions,expected_contract_and_basis=contract,
      actual_and_root_cause=actual,reachability_and_impact=reach,validation=validation,
      minimal_fix=fix,recommended_regression=regression,unconfirmed_assumptions_and_limits=limits,
      evidence=['p7/baseline.json',*evidence],conclusion=status,
      upstream_downstream_contracts='C-U01/U02/U03/U04按位置；application/libc/libos→nanos，详USER_RUNTIME.md和SYSCALL_ABI.md',
      existing_test_coverage='U13正常路径/输出示例见USER_RUNTIME.md；没有覆盖本触发条件的既有判定证据',
      missing_evidence='本轮无NEMU/NPC guest端到端回归；'+limits,
      severity_rationale=('导致有效输入的内存/返回/构建结果或运行时状态错误；影响限当前教学用户栈，未证明跨权限利用' if severity=='Medium' else '局部契约/防御/测试判定缺口，未观察普通RV64运行失败'),
      evidence_origin='本轮静态源码与指定隔离证据；不复用历史运行作为本轮测试')
    findings.append(f)

L='navy-apps/libs/libos/src/syscall.c'
C='navy-apps/libs/libc/'
issue(76,'libos错误返回没有遵守newlib低层errno接口','Confirmed','Medium',
 [(L,[74,78,83,94,102,110,113]),(C+'src/reent/openr.c',[42,49,50,51]),(C+'src/reent/execr.c',[48,55,56])],
 '_open/_read/_write/_lseek/_sbrk/_execve → _xxx_r',
 '本地reent wrapper明确要求低层全局errno；调用失败后应将原因交给请求的_reent。不是假定所有syscall均返回Linux -errno。',
 '多数libos wrapper直接返回-1且不设置低层errno；execve写宏errno对应默认_impure_ptr，绕开请求对象与低层全局errno。',
 'open不存在路径可留下旧错误；execve显式非默认_reent失败修改错误对象；stdio/应用错误诊断失真。',
 '隔离真实wrapper+reent，ecall替换为返回stub：open(-1)后高errno77、低0；exec默认2；独立对象99不变而默认2。修正probe自身_sbrk原型后exit0。',
 '统一内核错误语义与low errno存储；或提供完整REENTRANT_SYSCALLS_PROVIDED适配；避免同时维护互不相通错误槽。',
 '缺路径open/exec、seek失败、sbrk失败；默认和独立_reent，失败前设置非零哨兵。',
 '不要求本轮实现缺失POSIX能力；宿主stub没有验证真实内核错误码。', ['p7/supplement/errno-paths-fixed.log', 'p7/supplement/repair-results.json'])
issue(77,'newlib构建遗漏低层原型，64位read/write/lseek以隐式int调用','Confirmed','Low',
 [(C+'Makefile',[2,3]),(C+'include/sys/unistd.h',[262]),(C+'src/reent/readr.c',[49]),(C+'src/reent/writer.c',[49]),(C+'src/reent/lseekr.c',[49])],
 '_read_r/_write_r/_lseek_r与_COMPILING_NEWLIB',
 '低层声明必须与libos long/off_t64返回及size_t64参数一致；include/sys/unistd.h原型受_COMPILING_NEWLIB保护。',
 '默认编译未定义该宏，reent调用出现implicit-function-declaration；默认int返回与long64实现的C类型不兼容。',
 '当前构建所有上述调用均有声明缺口；更换优化/工具链可截断或拒绝编译。',
 'RV64编译诊断确认；host LP64生产reent+64位stub得到read3/write-2147483645/lseek5。当前RV64汇编没有sext.w且a0原样返回，未观察RV64实际截断。',
 '按newlib内部编译契约启用正确声明并消除warning；检查所有low syscall一致原型。',
 '返回值越过INT_MAX/UINT_MAX、-1；以implicit声明为错误编译并检查RV64结果。',
 '宿主截断不能外推成当前RV64已触发；_sbrk_r已有显式指针声明，不属于该例。', ['p7/width/results.json','p7/width/host-width.log','p7/width/readr.s'])
issue(78,'ecall内联汇编没有描述用户缓冲内存读写','Robustness','Low',[(L,[57,65])], '_syscall_',
 'GCC Extended Asm memory clobber契约：不可见的指针内存读写须由operands或memory描述。',
 '寄存器操作数只提供地址值，asm volatile没有memory clobber；read/gettimeofday输出和write输入内容不在编译器数据流中。',
 '普通系统调用路径可被内联/优化；可能错误缓存或重排调用前后缓冲访问。',
 '当前-O2同TU gettimeofday探针仍重新加载输出；弱hook逃逸可能保守化分析。本轮只证实声明遗漏，未复现误编译。',
 '为ecall添加准确内存约束，通常memory clobber；保留a0输入/输出关系。',
 'LTO/内联开关、无hook路径、read/gettimeofday输出与write输入可见性。',
 '不是当前编译器实测错误，也不是CPU内存栅栏需求。', ['p7/probes/visibility.s','SYSCALL_ABI.md'])
issue(79,'当前fwrite零元素大小路径发生除零','Confirmed','Medium',[(C+'src/stdio/fwrite.c',[144,147,166])], '_fwrite_r/fwrite',
 '本地fwrite公开接口允许size或count为0；没有传输完整元素时返回0，不能除零。',
 '_FVWRITE_IN_STREAMIO未启用，size=0使n=0，循环跳过但最终i/size。',
 'fwrite(buf,0,count,valid_stream)合法零长度请求可触发UB；与OS是否写入无关。',
 '生产fwrite编译链接最小外部FILE钩子；count0,size1退出0；size0 UBSan定位166行并按预期退出1。',
 '在状态/乘法/除法前处理size==0或count==0；保持零长度返回语义。',
 '两个维度分别为0和同时为0；普通短写/错误；两种_FVWRITE配置。',
 '仅当前默认分支确认；未把另一模板分支动态测为通过。', ['p7/probes/fwrite-size-zero.log','p7/probes/fwrite-count-zero.log','p7/fwrite-probe.c'])
issue(80,'calloc乘法溢出后向malloc提交过小尺寸','Confirmed','Medium',[(C+'src/stdlib/mallocr.h',[3197,3212])], '_calloc_r/calloc',
 'calloc分配n个elem_size元素，无法表示总长度必须失败；malloc只能检查已收到的尺寸。',
 'n*elem_size在size_t64域先回绕，未检查除法界限；后续malloc范围检查看不到原乘积。',
 '合法size_t参数(SIZE_MAX/2+2,2)请求变2；实际allocator若返回小块，调用者按原元素容量使用会越界。',
 '生产callocr.c/mallocr.h配stub allocator观测：正常3*8传24，溢出例传2。stub返回NULL，未演示真实堆破坏。',
 '乘前检查n!=0 && elem_size>SIZE_MAX/n，失败设置约定ENOMEM；再执行分配/清零。',
 '0、1、SIZE_MAX、刚好整除边界和超界；失败不改旧堆。',
 '没有证明具体应用已触发或可利用；不修复生产allocator。', ['p7/probes/calloc-overflow.log','p7/calloc-probe.c'])
issue(81,'execl系列固定argv数组未检查参数个数','Confirmed','Medium',
 [(C+'src/posix/execl.c',[27,33,34]),(C+'src/posix/execle.c',[23,29,30]),(C+'src/posix/execlp.c',[22,28,29])], 'execl/execle/execlp',
 '正确NULL终止的可变实参序列不能越过临时数组；超过实现容量应报告错误。',
 'argv[256]后do/while逐项写入，没有i<256限制；256个非NULL参数的结束NULL写argv[256]。',
 '从应用exec族可达；约2KiB指针表可小于OS32KiB栈，不能用内核栈限额豁免wrapper先发生的栈越界。',
 '逐语句静态索引/终止条件推导；未运行破坏宿主栈的probe。',
 '动态构造受限参数向量或在写前检查容量并按约定E2BIG失败。',
 '0/1/255/256/257个非NULL参数及execle末尾envp定位。',
 '不包括缺失NULL的调用者自身错误；OS参数容量另归F0061。', ['USER_RUNTIME.md'])
issue(82,'execvp用无界PATH拼接写固定1024字节栈缓冲','Confirmed','Medium',
 [(C+'src/posix/execvp.c',[30,42,55,58,59]),(C+'include/dirent.h',[42])], 'execvp/strccpy',
 '搜索路径来自进程env；组件/file长度超限需失败或安全分配，不能越过本地数组。',
 'MAXNAMLEN=1024；strccpy/strcat均不接收容量，组件、斜杠和file总长没有验证。',
 'PATH组件达到1024或组合超过1023可在首次execv前栈越界；这些环境字符串仍可容纳于OS参数栈。',
 '静态长度推导；MAXNAMLEN当前头宏实值已核；未执行溢出。',
 '带溢出检查计算拼接总长并分配，或限长返回明确错误；保留PATH空组件规则。',
 '1023/1024边界、长file、空PATH/首尾冒号、含斜杠file、ENOENT与其他错误。',
 '空PATH语义额外记录，未另建重复问题。', ['USER_RUNTIME.md'])
issue(83,'setenv分配失败破坏environ所有权或丢失原向量','Confirmed','Medium',
 [(C+'src/stdlib/setenv_r.c',[93,95,103,104,105,116])], '_setenv_r',
 '初始environ为crt借用栈向量；只有成功创建堆向量后才能realloc；失败必须保留可用环境状态。',
 'alloced先置1再malloc，第一次失败后下一次realloc栈指针；另一分支直接environ=realloc，失败将原向量丢失为NULL。',
 '内存不足/注入分配失败后再次setenv即可非法realloc或后续遍历NULL；合法环境操作的失败路径。',
 '静态跟踪alloced/environ与crt赋值；未在真实OS制造OOM。',
 '新指针暂存、所有分配成功后原子提交状态；区分借用env字符串与自有向量生命周期。',
 '首次向量分配失败后重试、扩容realloc失败、字符串分配失败、既有值替换。',
 '当前mm_brk不可靠失败不等于这条失败契约不存在；实际OOM路径另受P6限制。', ['USER_RUNTIME.md'])
issue(84,'libam公开heap始终是NULL空区间','Confirmed','Medium',
 [('navy-apps/libs/libam/src/trm.cpp',[5])], 'Area heap / TRM初始化',
 'navy README声明libam提供TRM/IOE；AM heap需向调用者提供可用范围或明确能力，不能仅导出未初始化对象。',
 '全U04只有Area heap定义，没有赋初值/constructor/初始化赋值；BSS两端均NULL。',
 'AM程序使用heap做allocator/new_page等获得空地址范围；libc malloc的独立_sbrk链不能自动填充Area。',
 '实际trm.cpp与cte.c宿主隔离链接观测heap=[NULL,NULL]；RV64三个libam编译单元也独立编译成功。',
 '在已明确的用户堆预算内初始化Area并约定与libc allocator共享/独占，避免重叠所有权。',
 '首个heap访问前范围/对齐、与libc同时分配、耗尽/重复初始化。',
 '没有选择具体堆大小或擅自实现方案；CTE/VME占位是另一个能力边界。', ['p7/supplement/libam-host.log'])
issue(85,'递归libs/fsimg构建吞掉失败并允许使用旧产物','Confirmed','Medium',
 [('navy-apps/Makefile',[120,173,177,180])], 'libs/fsimg/ramdisk recipes',
 '失败依赖不得被报告成成功的构建/安装；ramdisk应由本轮成功的app产物组成。',
 'for循环没有失败即停，返回最后一次make状态；fsimg行前缀-进一步忽略最终失败。',
 '前项失败后末项成功外层返回0；fsimg任何项失败仍可继续ramdisk，残留旧文件被打包。',
 '仅提取两段recipe至隔离Makefile，fake-make broken=7/good=0；libs与fsimg外层均0。没有运行原make/clone/install。',
 '递归失败立即退出并让外层感知；成功集合单独发布；不要盲目删除用户旧产物。',
 '首/中/末子构建失败、缺工具、链接失败、旧fsimg存在与不存在。',
 '不能由此推断F0074历史nterm的具体生成原因；该旧镜像问题仍独立。', ['p7/supplement/libs-swallowed-failure.log','p7/supplement/fsimg-swallowed-failure.log','p7/run_supplement.py'])
issue(86,'nanos-lite-guest包装引用已不存在的ramdisk.c','Confirmed','Medium',
 [('navy-apps/apps/nanos-lite-guest/Makefile',[9,10])], 'SRCS/VPATH',
 '当前声明的wrapper应能解析每个源前置条件；复用nanos源需与实际文件名/装载方式相符。',
 'SRCS仍包含ramdisk.c，app目录及VPATH的nanos-lite/src均不存在；当前nanos为disk.c/resources.S路径。',
 '干净RV64 wrapper构建找不到该.o的源前置条件；旧产物存在不能证明清洁构建有效。',
 '只读核对源存在性和规则，未执行有副作用的make。guest业务源码仍归P8。',
 '按guest实际ramdisk后端更新源清单及stub边界后隔离验证，避免重复资源符号。',
 '无build目录的wrapper构建；生成ramdisk与stub/嵌入源互斥。',
 '不声称补一个文件即可解决所有guest编译/运行问题。', ['USER_RUNTIME.md'])
issue(87,'exec相关示例失败后仍返回成功状态','Robustness','Low',
 [('navy-apps/tests/exec-test/main.c',[12,13]),('navy-apps/tests/execvp-test/main.c',[10,11,12]),('navy-apps/tests/busybox-test/main.c',[9,10,11])], 'main测试oracle',
 '测试欲证明exec成功时，返回路径应报告失败；exec成功不会返回原main。',
 '调用失败后落到return0，部分仅printf错误；自动状态判定可把失败视为成功。',
 '文件缺失或exec错误时触发；旧脚本若只观察退出码漏报。',
 '三个main源码静态核对；未执行guest测试。',
 '失败路径明确非零/断言，并按OS退出实现选择可观测oracle。',
 '缺目标、坏PATH、成功exec后目标程序专用标记；测试runner验证两者不同。',
 'OS sys_exit重启nterm并非宿主退出码，自动oracle还需P9端到端定义。', ['USER_RUNTIME.md'])
issue(88,'open connector无条件读取未必提供的mode可变实参','Confirmed','Low',
 [(C+'src/syscalls/sysopen.c',[18,19]),(C+'src/posix/opendir.c',[89])], 'open',
 '当前API及本地opendir/getut等调用允许open(path,O_RDONLY)；读取不存在的va_arg不满足C可变参数契约。',
 '不判断flags就va_arg(ap,int)并传_open_r，二参调用读取不存在的第三参。',
 '普通只读打开及opendir/getut本地调用可达；当前内核忽略mode通常掩盖值错误，但不能消除C契约缺陷。',
 '静态匹配二参调用与sysopen无条件读取；未宣称观察到RV64崩溃。',
 '仅在需要创建mode的flags下提取，其他情况传确定默认值；保留mode_t提升约定。',
 '二参O_RDONLY、三参O_CREAT、不同优化/寄存器哨兵。',
 '未强加完整POSIX文件创建后端；这里只处理现有调用接口。', ['USER_RUNTIME.md'])
issue(89,'用户_sbrk在地址计算前没有溢出与下界检查','Robustness','Low',[(L,[83,84,87])], '_sbrk',
 '增量到绝对break的转换须可表示且保留合法堆边界，失败应不改program_break。',
 '(intptr_t)program_break+increment可能先发生有符号溢出；缩减没有end下界检查。',
 '极值增量或过量缩减来自sbrk API/allocator时可算出错误地址，再交给当前始终成功的mm_brk。',
 '正常+16/-8与stub失败不改break已探针核对；极值仅静态推导，未在guest执行。',
 '先在无溢出的地址域核对上下界，成功后提交break；与OS容量策略一致。',
 '0、±小值、INTPTR_MIN/MAX、end以下、内核拒绝时状态。',
 '内核堆越界根因仍F0063；GNU void*算术本身未作为缺陷。', ['p7/supplement/errno-paths-fixed.log'])

# Evidence names must refer to the frozen logs, not invented test names.
for f in findings:
    for e in f['evidence']:
        assert (BASE/e).exists(), (f['id'],e)
dump(HERE/'findings.json',findings)
dump(BASE/'findings.json',old+findings)

native=[r for r in rows if r.get('effective_phase')=='CCR-P7' and '/onscripter/repo/build/' in r['path']]
assert len(native)==65 and all(r['row_kind']=='file' for r in native)
asset={a['path']:a for a in json.loads((HERE/'asset-review.json').read_text())}
for r in native:
    a=asset[r['path']]
    if a['kind']=='ELF': assert a['machine']==62
    else:
        assert r['path'].endswith('.d') and asset[r['path'][:-2]+'.o']['machine']==62
        dep_target=a['dependency_text'].split(':',1)[0].replace('//','/')
        assert dep_target=='build/'+r['path'].split('/repo/build/',1)[1][:-2]+'.o'
dump(HERE/'scope-correction.json',dict(authority='已批准S06：Navy-native及非RV64目标产物Excluded；不是新增范围决定',
 basis='33 ELF EM_X86_64 + 32配套.d目标一一匹配，部分含宿主SDL头；repo/Makefile使用gcc/g++，与Navy外层build/riscv64目录不同',
 before=[{k:r.get(k) for k in ['row_id','path','source_sha256','review_scope','effective_phase','review_profiles','review_config','effective_phase_responsibilities']} for r in native]))

provenance=json.loads((HERE/'libc-provenance.json').read_text())
changed={C+x.split('\t')[-1] for x in provenance['history_changed_paths'] if not x.startswith('D\t')}
runtime_dirs={'syscalls','reent','errno','platform'}
runtime_names={
 'misc/init.c','misc/fini.c','misc/lock.c','misc/__dprintf.c',
 'stdio/stdio.c','stdio/makebuf.c','stdio/refill.c','stdio/wsetup.c','stdio/fflush.c','stdio/fread.c','stdio/fwrite.c','stdio/fopen.c','stdio/fclose.c','stdio/fseek.c','stdio/fseeko.c','stdio/findfp.c','stdio/fvwrite.c','stdio/local.h',
 'stdlib/malloc.c','stdlib/calloc.c','stdlib/realloc.c','stdlib/free.c','stdlib/environ.c','stdlib/getenv.c','stdlib/getenv_r.c','stdlib/setenv.c','stdlib/setenv_r.c','stdlib/putenv.c','stdlib/putenv_r.c','stdlib/envlock.c','stdlib/exit.c','stdlib/atexit.c','stdlib/on_exit.c','stdlib/cxa_atexit.c','stdlib/__atexit.c','stdlib/__call_atexit.c','stdlib/abort.c',
 'posix/opendir.c','posix/readdir.c','posix/readdir_r.c','posix/closedir.c','posix/telldir.c','posix/scandir.c','posix/glob.c','posix/creat.c','posix/popen.c',
 'unix/pread.c','unix/pwrite.c','unix/getcwd.c','unix/getlogin.c','unix/getpass.c','unix/getpwent.c','unix/getut.c','unix/ttyname.c','unix/ttyname_r.c',
 'time/time.c','time/clock.c','time/tzset_r.c','signal/raise.c','signal/signal.c','signal/psignal.c','ssp/chk_fail.c','ssp/stack_protector.c'}
abi_headers={'unistd.h','reent.h','errno.h','stdio.h','stdlib.h','sys/unistd.h','sys/_types.h','sys/types.h','sys/_stdint.h','sys/_timeval.h','sys/time.h','sys/_timespec.h','sys/stat.h','sys/reent.h','sys/lock.h','newlib.h','machine/setjmp.h','machine/_default_types.h','sys/config.h','_syslist.h','sys/dirent.h','sys/termios.h','sys/utmp.h'}
dir_notes={
 'argz':'分配/字符串向量依赖；非OS算法边界','ctype':'字符分类表，无OS glue','errno':'errno宏与_reent错误槽对应',
 'locale':'默认配置/分配/locale能力边界','math':'本地assert stubs，不支持FP',
 'misc':'初始化/锁/写入接入；其他工具算法边界','platform':'本地RV64寄存器和C++接入',
 'posix':'exec/目录/进程后端边界；regex/glob算法不全面审','reent':'低调用返回/errno/_reent生命周期',
 'search':'容器/比较/分配依赖；算法不全面审','signal':'本地handler或kill/getpid后端；无内核信号',
 'ssp':'默认关闭；失败write/abort接口','stdio':'FILE/字节I/O及模板选入；格式算法边界',
 'stdlib':'堆/env/退出/进程接口；其他算法边界','string':'字符串API及本地include；算法不全面审',
 'syscalls':'public→reent connector','time':'gettimeofday/times/TZ接口；日历算法边界',
 'unix':'文件/终端/账号依赖；无完整OS后端'}
file_reviews=[]; branch_reviews=[]
issue_by_path=collections.defaultdict(list)
for f in findings:
    for l in f['locations']: issue_by_path[l['path']].append(f['id'])
def classify(r):
    p=r['path']; m=r['module_id']
    if m=='U14': return 'AssetIdentity','S03：格式、身份、生成/消费；历史源码/flags配对Unknown'
    if m=='U01': return 'BuildInterface','选源/递归/参数/链接/安装/ramdisk责任；应用实现P8未开始'
    if m=='U02': return 'RuntimeInterface','启动/syscall全体实现；RV64栈/寄存器/返回/errno，其他ISA分支不扩审'
    if m=='U04': return 'RuntimeInterface','TRM/IOE/软件CTE全部本地实现；NDL调用侧前置条件，P8/P9双端待闭合'
    if m=='U13': return 'TestOracle','触发接口/正常与失败oracle；本轮未运行guest测试'
    assert m=='U03'
    if '/.git/' in p or p.endswith(('.md','.gitignore')): return 'ProvenanceBoundary','本地repo/import/声明身份；不审git内部或宣称原版未改'
    if p in changed: return 'LocalAdaptation','import→HEAD本地差异、宏/模板/ABI与OS依赖；无关算法不全面审'
    if p.startswith(C+'src/'):
        rel=p[len(C+'src/'):]; d=rel.split('/')[0]
        return ('RuntimeInterface' if d in runtime_dirs or rel in runtime_names else 'ThirdPartyBoundary',dir_notes[d])
    if p.startswith(C+'include/') and p[len(C+'include/'):] in abi_headers: return 'ABIInterface','本地编译宏/类型声明/结构布局/调用宽度；未实现API仅能力边界'
    return 'ThirdPartyBoundary','第三方头/文档的配置与调用边界；非完整API或算法审计'

selected=[r for r in rows if r.get('effective_phase')=='CCR-P7']
native_ids={r['row_id'] for r in native}
check_keys=['normal','boundary_zero_empty_invalid','failure_state_return_cleanup','integer_alignment_lifetime','init_repeat','conditional_upstream_downstream']
for r in selected:
    p=r['path']; depth,note=classify(r); isfile=r['row_kind']=='file'
    issues=issue_by_path[p][:]
    if p.endswith('libos/src/crt0/start.S'): issues+=['CCR-F0060']
    if r['row_id'] in native_ids:
        depth='Excluded';note='S06已批准范围更正：Navy-native x86_64产物/对应依赖；不计RV64已审'
        r.update(review_scope='Excluded',review_status='Excluded',effective_phase=None,review_profiles=[],review_config=[],effective_phase_responsibilities={},scope_reason=note)
    else:
        r['review_status']='ReviewedStatic' if depth not in {'ThirdPartyBoundary','ProvenanceBoundary','AssetIdentity'} else 'BoundaryReviewed'
    evidence=['USER_RUNTIME.md','SYSCALL_ABI.md','THIRD_PARTY_P7.md','p7/baseline.json']
    if depth=='AssetIdentity' or depth=='Excluded': evidence+=['p7/asset-review.json','p7/fsimg-match.json']
    if r['module_id']=='U03': evidence+=['p7/libc-provenance.json']
    if depth=='Excluded': evidence+=['p7/scope-correction.json']
    report=dict(row_id=r['row_id'],path=p,module_id=r['module_id'],source_sha256=r['source_sha256'],
        line_range=r.get('line_range'),function_or_path=r['function_or_path'],review_depth=depth,
        conclusion=note,issue_ids=issues,evidence=evidence,dynamic='NotRun per-row; targeted probe applicability in findings, not whole-file PASS')
    if not isfile:
        b=r.get('line_range') or [1,1]
        source=(ROOT/p).read_text(errors='replace').splitlines()
        report['source_condition']='\n'.join(source[max(0,b[0]-1):min(len(source),b[-1])])[:3000]
        report['condition_disposition']=('S01 boundary only; unrelated third-party macro combinations not evaluated/compiled' if depth=='ThirdPartyBoundary' else
          '按RV64非E、__NAVY__、默认newlib宏与OS接口核条件责任；native/other ISA及未支持功能仅记录边界；非全配置运行证明')
        branch_reviews.append(report)
    else:file_reviews.append(report)
    r['p7_review']=report
    r['evidence_ids']=list(dict.fromkeys(r.get('evidence_ids',[])+['CCR-E-P7-review']))
    r['issue_ids']=list(dict.fromkeys(r.get('issue_ids',[])+issues))
    r['dynamic_validation']='NotRun (whole row); targeted evidence in p7 findings'
    for k in check_keys:
        r[k]=('NotApplicable: S06 Excluded' if depth=='Excluded' else f'{depth}: {note}; '+
              {'normal':'正常链及支持能力见USER_RUNTIME对应行',
               'boundary_zero_empty_invalid':'零/空/无效参数检查及未实现边界见矩阵；不声称第三方算法全审',
               'failure_state_return_cleanup':'错误/清理/副作用与ownership见矩阵和关联问题',
               'integer_alignment_lifetime':'标量/结构/栈/借用及所有权见SYSCALL_ABI；无关算法边界保留',
               'init_repeat':'初始化/重入/重复使用能力与限制见USER_RUNTIME',
               'conditional_upstream_downstream':'application/libc/libos→nanos；P8/P9责任仍未完成'}[k])
    r['limits']=['P7逐行按review_depth解释；BoundaryReviewed不是实现算法全审或动态通过',
      '没有guest/完整重建；历史产物源码/flags配对Unknown；第三方来源未独立与上游tarball比较',
      '用户本轮禁止无关libc全面审计和自动下载；P8/P9未开始']
lines(HERE/'file-review.jsonl',file_reviews)
lines(HERE/'branch-review.jsonl',branch_reviews)
lines(BASE/'coverage.jsonl',rows)
dump(HERE/'review-summary.json',dict(original_rows=len(selected),original_files=len(file_reviews),
   conditions=len(branch_reviews),excluded_files=len(native),retained_files=len(file_reviews)-len(native),
   file_depths=dict(collections.Counter(r['review_depth'] for r in file_reviews)),
   condition_depths=dict(collections.Counter(r['review_depth'] for r in branch_reviews)),
   new_findings=len(findings),new_status=dict(collections.Counter(f['status'] for f in findings)),
   cumulative_findings=len(old+findings),cumulative_status=dict(collections.Counter(f['status'] for f in old+findings)),
   cumulative_severity=dict(collections.Counter(f['severity'] for f in old+findings))))

# Append-only issue details: reruns replace this new phase's generated tail only.
fp=BASE/'FINDINGS.md'; txt=fp.read_text(); marker='<a id="ccr-p7-findings-20261017"></a>'
txt=txt.split(marker)[0].rstrip()+'\n\n'+marker+'\n## CCR-P7（2026-10-17）\n\n新增14项：11 Confirmed、3 Robustness，均未修；完整字段见findings.json。\n'
for f in findings:
    txt+=f'\n<a id="{f["id"].lower()}"></a>\n### {f["id"]} — {f["title"]}\n\n'
    txt+=f'- 状态/等级：{f["status"]} / {f["severity"]}；函数：{f["functions"]}\n'
    txt+='- 位置：'+'；'.join(f'`{l["path"]}:{l["lines"][0]}`（SHA {l["sha256"]}）' for l in f['locations'])+'\n'
    for key,label in [('expected_contract_and_basis','契约'),('actual_and_root_cause','根因'),('reachability_and_impact','触发/影响'),('validation','本轮验证'),('minimal_fix','最小修复建议（未实施）'),('recommended_regression','建议回归'),('unconfirmed_assumptions_and_limits','限制')]:txt+=f'- {label}：{f[key]}\n'
    txt+='- 证据：'+', '.join(f'[{e}]({e})' for e in f['evidence'])+'\n'
fp.write_text(txt)
print((HERE/'review-summary.json').read_text())
