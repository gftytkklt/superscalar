#!/usr/bin/env python3
"""Materialize P10 adjudication without rewriting original phase fields.

Uses the frozen P10 baseline and explicit review notes in RECONCILIATION.md.
This script assembles records; it does not independently review source code.
"""
from pathlib import Path
import collections
import gzip
import hashlib
import json

P=Path(__file__).resolve().parent; B=P.parent
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def jsonl(p,v):p.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in v))
base=read(P/'baseline.json')
def original(name):
    f=next(x for x in base['files'] if x['path'].endswith('/'+name))
    return gzip.decompress((P/f['snapshot']).read_bytes()).decode()
cov=[json.loads(l) for l in original('coverage.jsonl').splitlines()]
final=[]
for r in cov:
    phase=r.get('effective_phase')
    reviews={k:v for k,v in r.items() if k.startswith('p') and k.endswith('_review')}
    evidence=[f'P{p}.md' for p in range(2,10) if f'p{p}_review' in reviews]
    if r['review_status']=='Excluded':
        status='Excluded'; evidence=['SCOPE_RV64.md', 'p3/source-evidence.json','p5/scope-correction.json','p7/scope-correction.json']
        depth='UserApprovedOutOfScope';reason=r.get('scope_reason','S06批准范围排除，保留身份，不计已审')
    elif r['review_status']=='Unavailable':
        status='Unavailable';depth='MissingSource';reason='S05保留缺源；P10用户批准暂缓并豁免本次闭合验收，未批准排除或认定已审';evidence=['P8.md#p8-waiver-20261017','P10.md#p10-user-waiver-20261017']
    elif r['module_id']=='X01':
        status='BoundaryReviewed';depth='BuildSideEffectAndProvenance';reason='P0/P1已有副作用证据，P10逐入口核对并补最终映射';evidence=['../CODE_CORRECTNESS_REVIEW_PLANNING.md','P1.md','p10/RECONCILIATION.md']
    elif r['row_kind']=='conditional_path':
        status='ConditionNavigationReviewed';depth='DeclaredFileDepthOnly';reason='条件选择/对应阶段责任记录；不是动态分支覆盖'
        if r.get('p2_review',{}).get('p2_disposition')=='ReviewedBoundary':
            evidence+=['P3.md','p10/RECONCILIATION.md'];reason='P2控制边界与P3回调实现配对，P10定向核对交接'
        if r.get('p2_review',{}).get('p2_disposition')=='NotApplicableRV64':
            reason='RV64选择已核；非RV实现体按S06排除，不当作已审实现'
    else:
        status='ReviewedAtDeclaredDepth';reason='主审/共享责任按各阶段深度解释，问题未修、动态限制独立'
        rv=reviews.get((phase or '').replace('CCR-P','p')+'_review',{})
        depth=rv.get('review_depth',rv.get('depth',rv.get('disposition',r.get('classification','SeePhaseEvidence'))))
    item={'row_id':r['row_id'],'row_kind':r['row_kind'],'path':r['path'],'module_id':r['module_id'],
          'source_sha256':r['source_sha256'],'original_review_status':r['review_status'],
          'final_status':status,'depth':depth,'reason':reason,
          'primary_phase':phase,'responsibilities':r.get('effective_phase_responsibilities',{}),
          'evidence':sorted(set(evidence)),'phase_review_fields':list(reviews),
          'issue_ids':sorted(set(r.get('issue_ids',[]))|{i for v in reviews.values() for i in v.get('issue_ids',[])})}
    r['p10_review']={k:v for k,v in item.items() if k not in ('row_id','row_kind','path','module_id','source_sha256')}
    final.append(item)
jsonl(B/'coverage.jsonl',cov);jsonl(P/'final-coverage.jsonl',final)
modules=[]
for m in sorted({r['module_id'] for r in final}):
    rr=[r for r in final if r['module_id']==m and r['row_kind']=='file']
    modules.append({'module_id':m,'identities':len(rr),'excluded':sum(x['final_status']=='Excluded' for x in rr),
                    'reviewed_at_declared_depth':sum(x['final_status'] in ('ReviewedAtDeclaredDepth','BoundaryReviewed') for x in rr),
                    'unavailable':sum(x['final_status']=='Unavailable' for x in rr)})
write(P/'coverage-summary.json',{'stable_rows':40010,'files':15240,'retained_files':12665,'excluded_files':2575,
    'reviewed_at_declared_depth':12663,'unavailable_files':2,'identity_obligation_percent':12663/12665*100,
    'retained_condition_navigation':24656,'excluded_condition_navigation':114,
    'condition_navigation_records':24656,'functional_execution_coverage':'Unknown / not measured',
    'modules':modules,'corrections':{'X01_file_ledger':5,'P2_condition_handoffs':16,'P2_nonRV_selection':7,'P8_condition_ledger':13629}})

# Concrete supplements to formerly generic P3-P6 regression recommendations.
reg={
9:'五内存域首/尾、跨末端、64位高地址、块数乘法溢出；短fread/fwrite、seek失败；拒绝后host/guest哨兵不变。',
10:'分开测试单写init、实际AM init→freq→channels→samples序列、重开；检查SDL打开次数和参数，不把首次正常开启判失败。',
11:'count=0/1/len-1/len、ring wrap；回调输出预填非零哨兵，检查所有欠载字节为0。',
12:'NULL/空串、31/32/33 token、31/32字节token、长数字；检查失败标志和数组哨兵。',
13:'32个watchpoint后第33个、空串/127/128/129字节表达式及字母n；检查池状态和求值文本一致。',
14:'每个REF内存域双向copy首/尾、跨区、0与大于INT_MAX长度；边界失败不触及host哨兵。',
15:'只改REF PC、只改GPR、二者相同；验证PC-only mismatch必报，逐项记录skip/CSR未比字段。',
16:'firmware/kernel/DTB三段不同字节哨兵；核初次执行前双方地址/长度/hash，缺任一段必须拒绝或报差异。',
17:'以选定QEMU真实target description核GPR/PC位置；PC与FPR0放不同哨兵，高地址传输和短GDB包检查。',
18:'CPU结构和PMEM每个截断点、读取错误、错误格式；失败后原活CPU/内存逐字节不变。',
19:'固定seed产生指定数量有效非空样例；编译器失败/0有效样例必须非零，逐样例比独立期望。',
20:'每种寄存器read/write、SDCMD重复读、传输方向、EOF/短I/O；只允许规定方向推进状态。',
21:'无SYMTAB、entsize0、超界shoff、短节/索引、正常ELF；失败不得除零或使用未完成数据。',
22:'PMEM剩余容量−1/等于/+1、RESET_VECTOR边界与空镜像；超限在任何复制前拒绝。',
23:'M态yield/计时/嵌套trap、U态返回及更改sp后的下一trap；检查MPP/np/mscratch和活栈哨兵。',
24:'trap slot预填0/非零垃圾、两个地址空间交替及syscall内yield；核每次satp保存/恢复。',
25:'data与BSS对齐1/2/8/64，各NPC链接模式；真实启动前预填BSS哨兵并验证完整清零范围。',
26:'SRAM静态区/SSBL恰在栈底、越一字节和7KiB例；link断言及运行栈水位分别验证。',
27:'text/rodata/data不同对齐及空节；逐节LMA→VMA字节比较，再执行常量读取。',
28:'HEAP_SIZE为0、恰容量、容量+1及地址加法溢出；错误配置不得发布超界Area。',
29:'用户先裁决权限/撤映射/故障子集；再测R/W/X/NONE、U/S/MPRV、unmap和故障事件/tval。',
30:'先裁决共享页表和所有权；重复protect/map/unprotect，核自有页回收、共享页不误释放。',
31:'先裁决NPC扩展能力；false不得作为初始化成功，NULL context/atomic路径要拒绝或实现真实契约。',
32:'脏页/NULL分配器、每级分配失败，根页清零和失败后AddrSpace未发布。',
33:'非NUL终止的n字节源、短串padding、n0/1/边界，检查返回dst及源/目的哨兵。',
34:'d/i/u/x/X后接u/X/普通字符；检查转换符和后继文本互不污染。',
35:'int32/long64 MIN/MAX、unsigned最高位、void*、符号与补零；独立期望字符串。',
36:'ULONG_MAX的2/8/10/16进制，截断sink与size0，内部数字buffer使用sanitizer。',
37:'分配1后分配8/16、剩余容量±1、SIZE_MAX、失败不推进cursor；检查目标对齐。',
38:'空白六类、可选±、尾文本、空串；仅测试可表示范围，不强加溢出未定行为。',
39:'MIN/1、MIN%1、±1/0边界按ABI、普通向量；GCC/Clang及UBSan分开解释。',
40:'局部static重复调用只初始化一次，guard首字节、失败/重入边界与析构能力单列。',
41:'在sync和每个像素写之间强制device_update；显示内容必须来自完成写入，0×0 sync-only保留。',
42:'缺设备所有CONFIG返回能力信息；present UART的TX/RX；OS init_fs检查不支持设备路径。',
43:'在count读和提交间强制callback消费；同时核生产/消费总量、wrap、欠载，不以同步MMIO桩代替并发。',
44:'len0/capacity−1/capacity/capacity+1、非法Area；验证有界拒绝或分片进展，不挂死。',
45:'reg−1/127/128、RD/WR反向与合法结构；错误无越界间接跳转。',
46:'原MIE0/1、两层disable/enable逆序恢复、调度调用；实际RT头签名编译与目标中断观测。',
47:'按声明tick频率统计AM timer→RT tick；超时/软件timer/抢占，禁止将60Hz直接当100Hz。',
48:'第一次成功、缩小后成功、全部失败；Area长度等于实际成功请求、无NULL发布。',
49:'创建后延迟启动、调用者栈销毁、create/start失败、重复启动；核参数自有复制和清理。',
50:'注册失败、无UART_RX的平台、预置命令耗尽；返回码与能力检查不被静态串口输出掩盖。',
51:'make/nm/objcopy在首/中/末失败；预置旧对象；不得发布成功mk/C或使用陈旧产物。',
52:'纯PASS、纯FAIL、预期负例、混合、空结果、管道失败；退出和有效样例数双重检查。',
53:'GPU无加速/无显示、磁盘absent/blksz0；仅运行支持子测试并显式列SKIP。',
54:'先裁决free/arena/reset生命周期；按选定契约重复分配释放、容量和双owner场景。',
55:'先裁决has_rtc含义；不支持/固定占位/真实历法各按能力声明验证，与uptime测试分开。',
56:'n0、同址、两向重叠和大块；O(1)栈预算，GNU零长扩展与诊断边界分开。',
57:'ELF magic/class/data/machine/type、短Ehdr/Phdr、entsize55/56/57/128及ph表溢出；失败保留原进程。',
58:'filesz>memsz、VA/offset回绕、用户上下界/栈/共享内核页；完整预检后才提交映射。',
59:'两个合法PT_LOAD同页但字节不重叠、顺序互换/跨页/BSS；保持前段字节且头全部合法。',
60:'argv/env长度与数量遍历16种余数；检查argc槽8对齐、首次C入口sp16对齐及内容不变。',
61:'参数总量32KiB边界、长字符串/多参数、空argv/env；失败不产生越界VLA或部分地址空间。',
62:'页数0/1、恰末端/越一页、乘法/ROUNDUP溢出；失败不移动全局游标并向上层传播。',
63:'brk堆下界/栈底/用户上界、ROUNDUP溢出和页分配失败；失败原break/页表不变。',
64:'fd−1/filenum−1/filenum、零长度、关闭后固定fd语义；所有入口和offset哨兵。',
65:'SET/CUR/END的负/0/文件末端/越界/溢出、invalid whence；失败不改变offset。',
66:'len0/1/完整事件长度/长度+NUL、最大键名/非法键码、前台F键；哨兵及消费重试语义。',
67:'len0/1/3/4/5、未对齐buffer；不得写超len，返回与实际字节一致。',
68:'FB首/末像素、offset等于size、跨屏末端、非4倍、跨行及零宽；返回实际写入。',
69:'所有保留stage/FG配置的首轮schedule、fallback/空PCB；current和frame始终有效。',
70:'真实dummy vme_init=false后禁止后续protect/ucontext解引用；有能力平台正常启动对照。',
71:'按用户选定NPC布局建立完整PCB/ramdisk预算和link断言；不得默改BOOT_MODE/裁镜像。',
72:'空/8字节/跨页ramdisk，在各保留NPC模式核LMA/VMA和实际复制范围。',
73:'先裁决用户指针失败策略；NULL/末页/未映射/跨界/长度溢出；观察copyin/out或受控错误。',
74:'每个启动ELF的所有PT_LOAD和entry满足VME用户域；hash绑定fs表/ramdisk，原nterm错配应拒绝。',
75:'块末端/越界、offset+len溢出、跨块RMW、后端短I/O；先冻结错误传播协议再验证。'
}
fs=json.loads(original('findings.json')); fa={x['id']:x for x in read(P/'findings-audit.json')['checks']}
host=set(range(1,5))|{6,7,10,11,24,29,30,31,33,34,35,36,37,38,39,41,42,44,46,48,49,54,56}|set(range(57,70))|{70,75,76,77,79,80,84,89,92,93,94,95,97,98,99,100,101,102,116,117,118}
host.discard(11) # P9 proved reachability, not an underrun runtime reproduction.
build={5,23,25,26,27,28,40,46,60,71,72,77,78,110}
tool={51,52,85}
for f in fs:
    n=int(f['id'][-4:]); kinds=['StaticSource']
    if n in host:kinds.append('CCRHostProbe')
    if n in build:kinds.append('CCRCompileLinkOrDisassembly')
    if n in tool:kinds.append('CCRIsolatedFakeToolObservation')
    if n==74:kinds.append('CurrentArtifactMetadata')
    note='保留原分类/严重度；生产问题未修。动态执行范围仅见原validation；静态可独立支持Confirmed，不将NotRun写成已验证。'
    supplemental=[]
    if n in (10,11):
        note='P9已确认实际AM init→CTRL/samples可首次打开；F0010仅触发偏移问题，F0011欠载清零问题无需先修F0010才可达。原历史猜测不作为当前限制。'
        supplemental=['p9/L06.md','p9/probes2/results.json','p9/probes2/audio-run.log']
    if n==77:note='Confirmed仅原型/C类型不一致；host截断已观测，当前RV64无截断观测，不扩大影响。'
    if n==78:note='Robustness：缺memory约束；当前探针仍重新加载输出，未复现误编译。'
    if f['status']=='ContractQuestion':note='未决；没有批准教学简化，不升级Confirmed/ApprovedGap，不选择实现契约。'
    f['final_review']={'phase':'CCR-P10','date':'2026-10-17','adjudication':'Retained','canonical_root_id':f['id'],
        'duplicate_of':None,'evidence_classes':kinds,'original_object_sha256':fa[f['id']]['original_object_sha256'],
        'evidence_audit':'p10/findings-audit.json','dedup_basis':'p10/RECONCILIATION.md',
        'supplemental_evidence':supplemental,'note':note,
        'regression':reg.get(n,f['recommended_regression']), 'p10_dynamic_execution':'NotRun; metadata/static evidence audit only'}
write(B/'findings.json',fs)
out=['# CCR 最终问题清单','', '2026-10-17；119项均未修。Critical 0 / High 13 / Medium 79 / Low 27；86 Confirmed / 28 Robustness / 5 ContractQuestion / 0 ApprovedGap。', '',
     '编号稳定，按严重度排列；原条目保留于findings.json，final_review补充当前限定和具体回归。P10没有新生产动态实验。[根因对账](p10/RECONCILIATION.md)、[逐项证据核验](p10/findings-audit.json)、[修复及回归顺序](REPAIR_AND_REGRESSION.md)。','',
     '| ID | 等级 | 分类 | 问题 |','|---|---|---|---|']
ordered=sorted(fs,key=lambda f:({'Critical':0,'High':1,'Medium':2,'Low':3}[f['severity']],f['id']))
for f in ordered:out.append(f'| [{f["id"]}](#{f["id"].lower()}) | {f["severity"]} | {f["status"]} | {f["title"]} |')
for f in ordered:
    out+=['',f'<a id="{f["id"].lower()}"></a>',f'## {f["id"]} — {f["title"]}','',f'**{f["severity"]} / {f["status"]} / 未修复**；来源 {f["phase"]}。', '',
          '受影响路径：'+'；'.join('`'+x['path']+':'+','.join(map(str,x['lines']))+'`（SHA256 `'+x['sha256']+'`）' for x in f['locations']), '',
          '预期/依据：'+f.get('expected_contract_and_basis',f.get('expected_and_basis','')), '',
          '实际/根因：'+f['actual_and_root_cause'], '',
          '可达/影响：'+f.get('reachability_and_impact',f.get('reachable_path_and_trigger','')+' '+f.get('impact','')), '',
          '验证（原CCR阶段，本次P10仅复核）：'+f['validation'], '',
          '证据：'+'、'.join(f'[{e}]({e})' for e in f['evidence']+f['final_review']['supplemental_evidence']), '',
          '最小修复建议（未实施）：'+f['minimal_fix'], '',
          '回归建议：'+f['final_review']['regression'], '',
          '限制：'+f['unconfirmed_assumptions_and_limits'], '',
          'P10裁定：'+f['final_review']['note']]
(B/'FINAL_FINDINGS.md').write_text('\n'.join(out)+'\n')

interfaces=json.loads(original('interfaces_current.json'))
for x in interfaces['interfaces']:
    x['p10_final']={'review':'已闭合（P9规定的接口审阅字段）','implementation':'存在问题',
        'dynamic':'部分闭合；各子路径NotRun/无法验证按P9逐链证据保留',
        'evidence':f'p9/{x["interface_id"]}.md',
        'p8_missing_sources':'仍未审；不能由通用接口配对推定缺源应用已审'}
interfaces['p10_summary']={'review_fields':135,'chains_with_findings':9,'functionally_all_pass':False,
                         'ccr_review_closed_with_user_waiver':True,'all_retained_sources_reviewed':False,
                         'reason':'P10用户批准暂缓两缺源并允许其余审阅验收通过后闭合；缺源仍未审',
                         'authorization':'P10.md#p10-user-waiver-20261017','report':'FINAL_REPORT.md'}
write(B/'interfaces_current.json',interfaces)
print('P10 final matrices and 119 finding adjudications materialized; originals preserved as fields and baseline snapshots.')
