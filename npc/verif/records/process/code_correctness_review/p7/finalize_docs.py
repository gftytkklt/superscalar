#!/usr/bin/env python3
"""P7 navigation and lifecycle completion, only after the review is assembled."""
from pathlib import Path
import hashlib,json,re,shutil,collections
ROOT=Path(__file__).resolve().parents[6];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
assert '<a id="snapshot-ccr-p7-20261017"></a>' not in (ROOT/'.agent/CHANGELOG_AGENT.md').read_text(), 'Completion already exists; do not rerun'
def write(p,s): p.write_text(s if s.endswith('\n') else s+'\n')
def append_once(p,marker,s):
 t=p.read_text();t=t.split(marker)[0].rstrip();write(p,t+'\n\n'+marker+'\n'+s)
def dump(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2))
summary=json.loads((HERE/'review-summary.json').read_text())
assert summary['retained_files']==2624 and summary['new_findings']==14
for rel,prefix in [('README.md','npc/verif/records/'),('npc/README.md','verif/records/'),('npc/verif/README.md','records/'),('npc/verif/records/README.md','')]:
 p=ROOT/rel;base=prefix+'process/code_correctness_review/'
 new=f'独立CCR：[P7审阅/Final Gate]({base}P7.md) Completed；2624保留文件入口、8322条件导航，65个native资产按S06排除；新增11 Confirmed/3 Robustness，累计89项未修。[用户运行时]({base}USER_RUNTIME.md)、[syscall/ABI]({base}SYSCALL_ABI.md)、[第三方边界]({base}THIRD_PARTY_P7.md)、[问题]({base}FINDINGS.md)、[证据]({base}p7/README.md)、[覆盖]({base}COVERAGE.md)。P6已确认/提交`bdc02a3`；P7结果确认/commit Pending，P8未开始；生产源码与M2未改。'
 write(p,re.sub(r'^独立CCR：.*$',new,p.read_text(),flags=re.M))
p=ROOT/'npc/verif/records/process/README.md';t=p.read_text()
t=re.sub(r'(\| \[code_correctness_review/P6.md\].*?\| ✅ Completed；).*',lambda m:m[1]+'70文件/91条件，19新问题；累计75；已确认/提交bdc02a3；历史P6证据 |',t)
row='| [code_correctness_review/P7.md](code_correctness_review/P7.md) | PROCESS | CCR-P7 RV64启动/libos/libc/ABI/构建；[运行时](code_correctness_review/USER_RUNTIME.md)、[ABI](code_correctness_review/SYSCALL_ABI.md)、[第三方](code_correctness_review/THIRD_PARTY_P7.md)、[证据](code_correctness_review/p7/README.md) | ✅ Completed；2624保留文件/8322条件导航，65项S06排除，14新问题，累计89；P7确认/commit Pending；P8未开始 |'
if 'code_correctness_review/P7.md' not in t:t=re.sub(r'(^\| \[code_correctness_review/P6.md\].*$)',r'\1\n'+row,t,flags=re.M)
write(p,t)
p=ROOT/'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md';t=p.read_text()
t=re.sub(r'^> 最新执行状态.*$', '> 最新执行状态（2026-10-17）：P6已确认/提交`bdc02a3`；[CCR-P7](../records/process/code_correctness_review/P7.md)审阅/Final Gate Completed。2624保留文件入口/8322条件导航、65个native产物S06更正排除；新增14项，累计89未修。P7结果确认/commit Pending，P8未开始；生产源码/M2不变。§7阶段范围不变。',t,flags=re.M)
t=re.sub(r'^版本：.*$', '版本：v0.3（S06仅RV64+双平台/Spike角色澄清），2026-10-17。整体计划及S01–S06已批准；P0–P6已确认/提交，回执见各阶段记录。P7执行由本轮用户明确授权，现Completed，结果确认/commit Pending。P0提交47b6c78、P1提交0d65d72、P2提交9918989、P3提交1d76133、P4提交a419cea、P5提交632b843、P6提交bdc02a3；不推定P8授权。',t,flags=re.M)
t=re.sub(r'^- P0–P5已完成.*$', '- P0–P6已完成/确认/提交；本轮用户授权提交P6并执行CCR-P7，现P7审阅/Final Gate Completed，结果确认与commit Pending；P8–P10未开始。',t,flags=re.M)
write(p,t)
p=BASE/'COVERAGE.md';t=p.read_text()
t=re.sub(r'^当前阶段：.*$', '当前阶段：[P7/Final Gate](P7.md)、[用户运行时](USER_RUNTIME.md)、[ABI表](SYSCALL_ABI.md)、[第三方边界](THIRD_PARTY_P7.md)、[证据](p7/README.md)。P6已确认/提交bdc02a3；P7 Completed，结果确认/commit Pending，P8未开始。',t,flags=re.M)
append='''
## P7当前分母与深度（2026-10-17）

稳定身份仍15240文件/24770条件=40010行。原P7 2689文件/8322条件，65个native产物按S06更正排除，P7保留2624文件入口。全局当前文件12664保留/2576排除，条件24656保留/114排除。原ID和非P7行不变；U14模块表按更正后更新。

RuntimeInterface122、ABIInterface18、LocalAdaptation56、BuildInterface40、TestOracle7、ThirdPartyBoundary662、ProvenanceBoundary28、AssetIdentity1691，另Excluded65。`BoundaryReviewed`表示本轮用户批准的第三方/资产边界核对，不能作为实现算法全面审计。8322条件是导航及责任判定，不是功能路径运行数，包含第三方宏和不启用能力；具体深度及原文见[p7/branch-review](p7/branch-review.jsonl)。

U01=40、U02=4、U03=872、U04=10、U13=7、U14=1691保留；[逐文件](p7/file-review.jsonl)、[范围更正](p7/scope-correction.json)、[统计](p7/review-summary.json)。14新问题，累计89（71 Confirmed/13 Robustness/5 CQ），未修。动态只限定向探针；P8/P9责任保留，所有其他阶段行未改。
'''
write(p,t)
append_once(p,'<a id="ccr-p7-coverage-20261017"></a>',append)
rows=[json.loads(l) for l in (BASE/'coverage.jsonl').open()]
u14=collections.Counter(r['review_scope']=='Excluded' for r in rows if r['module_id']=='U14' and r['row_kind']=='file')
t=p.read_text();t=re.sub(r'^(\| U14 \|) \d+ \| \d+ \|',lambda m:f'{m[1]} {u14[False]} | {u14[True]} |',t,flags=re.M);write(p,t)
p=BASE/'FINDINGS.md';t=p.read_text();t=re.sub(r'^当前状态（2026-10-17）：.*$', '当前状态（2026-10-17）：P7新增14项（11 Confirmed/3 Robustness）；累计89项（71 Confirmed/13 Robustness/5 ContractQuestion；High13/Medium54/Low22），均未修。见[P7问题](#ccr-p7-findings-20261017)及[P7审阅](P7.md)。P6已确认/提交bdc02a3；P7确认/commit Pending，P8未开始；下方各阶段正文保留历史截面。',t,flags=re.M);write(p,t)
for file,body in {
 'CONTRACTS.md':'''## P7契约补充

C-U01选源/链接/失败传播，C-U02 crt/argv/env/syscall，C-U03 reent/errno/stdio/allocator/本地移植，C-U04 TRM/IOE/软件CTE，相关U13 oracle/U14资产已按[USER_RUNTIME](USER_RUNTIME.md)核对。[SYSCALL_ABI](SYSCALL_ABI.md)列20号/10case、寄存器/参数/返回、结构和所有权；[THIRD_PARTY_P7](THIRD_PARTY_P7.md)列来源/71历史差异/19目录边界。

CQ-006仍不以完整POSIX作为教学OS承诺；本文以已有调用者、newlib wrapper和RV64 ABI识别具体不一致。stub与缺后端明确记录，不擅自批准其为完整功能。GCC13.3 asm与psABI v1.0官方正文可用；newlib网页非冻结版本，精确契约以本地3.3移植源码为准。OpenGroup在线函数页读取403/C标准PDF读取超时不作为已读依据，CQ-014不伪装全消除。

P7新增F0076–F0089；P6 F0060/61/62/63/65/70–74沿用。F0029–31等旧CQ未裁决；P8 NDL事件有效性、时间回绕和P9跨层运行仍保留。新确认仅限本轮用户明确授权，不由测试推定。
''',
 'BUILD_PATHS.md':'''## P7用户构建补充

本轮静态核对全部40个U01入口：`ISA=riscv64`→riscv64.mk/common.mk→rv64g/medany/no-pic、__NAVY__、C++最小运行时→crt入口_start/libos/libc/libgcc及archive group；VME非空（包括0）链接0x40000000，空为0x83000000。libs phony会令链接重跑，不能将flags缓存风险写成“VME切换一定不重链”。libc编译宏与低调用声明缺口F0077，递归失败传递F0085，guest源清单F0086。

未运行原始make或make -n，避免解析期clone/仓库/产物副作用。现有工具用于/tmp隔离43+3生产单元及3份width汇编，不是完整产品重建。850 libc tracked字节相对HEAD一致不证明独立上游身份。

108个ramdisk extents与fsimg匹配；历史nterm非VME问题F0074保留。onscripter/repo/build中33 native ELF及32配套.d按S06排除；外层build/riscv64路径仍保留。见[p7/asset-review](p7/asset-review.json)、[scope-correction](p7/scope-correction.json)。两平台共用用户ABI不等于NPC具备VME/足够内存；fceux/oslab0缺源保持，不拉取。P8/P9未开始。
''',
 'INTERFACES.md':'''## P7用户侧补链（L01/L02/L03/L04/L07/L09）

[USER_RUNTIME](USER_RUNTIME.md)建立application→libc connector→reent→libos→ecall→nanos分派；[SYSCALL_ABI](SYSCALL_ABI.md)逐号/寄存器/宽度/结构/errno对应。栈a0与sp、argc/argv/env借用直到exec、timeval写入、FILE/buffer/heap ownership、低层返回及失败状态均有记录。软件__am_cte_syscall弱hook是条件链，只有成员实际链接才存在；无真实寄存器切换、静态Context非重入，putch直接ecall例外明确。

相关P6生产者证据复用而不重记测试；F0060栈对齐、F0061容量、F0063 brk、F0065 seek、F0070–74能力/指针/镜像断点未修。P7本地新增errno/width/stdio/allocator/exec/env/build问题见F0076–89。

libam→NDL只审调用侧约定：NUL终止且格式有效的事件、ticks单位/回绕、canvas/rect参数、GPU sync含义；NDL/SDL/应用实现为P8，完整跨层验证为P9。本次静态补链不把L01–L09标记Completed，也不改原interfaces_current.json的未来责任。
'''}.items():append_once(BASE/file,'<a id="ccr-p7-supplement-20261017"></a>',body)

p=ROOT/'npc/verif/docs/PROJECT_OVERVIEW.md';t=p.read_text();t=t.replace('P6审阅Completed、结果确认/commit Pending，P7未开始，见文末P6节','P6已确认/提交bdc02a3；P7 Completed、结果确认/commit Pending，P8未开始，见文末P7节').replace('### 2026-10-17 CCR-P6当前交付','### 2026-10-17 CCR-P6历史交付（当时停点）');write(p,t)
append_once(p,'<a id="ccr-p7-current-20261017"></a>','''### 2026-10-17 CCR-P7当前交付

[P7/Final Gate](../records/process/code_correctness_review/P7.md) Completed；2624保留文件/8322条件导航，65个native资产S06更正排除；14新问题（11 Confirmed/3 Robustness），累计89未修。[运行时](../records/process/code_correctness_review/USER_RUNTIME.md)、[ABI](../records/process/code_correctness_review/SYSCALL_ABI.md)、[第三方](../records/process/code_correctness_review/THIRD_PARTY_P7.md)、[证据](../records/process/code_correctness_review/p7/README.md)。P6已确认/提交bdc02a3；P7结果确认/commit Pending，P8未开始。仅隔离编译/宿主探针，无生产修复/guest/依赖下载；M2不变。
''')

p=ROOT/'.agent/CURRENT_STATE.md';t=p.read_text();start=t.index('| Task / Phase / Status | CCR /');end=t.index('\n## Completed（M0',start)
t=t[:start]+'''| Task / Phase / Status | CCR / CCR-P7 / Completed（Final Gate PASS） |
| Current Objective | U01–U04及相关U13/U14的RV64用户运行时审阅已交付；等待结果确认/commit |
| Last Completed Action | P6按授权提交bdc02a3；P7源码/ABI/第三方边界与定向验证、coverage/问题留档及Final Gate完成 |
| Current Working Files | P7.md、USER_RUNTIME/SYSCALL_ABI/THIRD_PARTY_P7、p7证据、coverage/问题/契约/构建/接口补充、计划与五README/索引 |
| Remaining Work | 本阶段无待执行审阅步骤；89问题未修；第三方无关算法按用户指令仅边界核对；P8/P9/P10未执行 |
| Next Phase / Next Action | CCR-P8 Next（Planned，未Start）；先用户确认P7并commit，再有P8授权 |
| Blocked By | 阶段执行无阻塞；下一阶段门槛为P7确认/commit/P8授权 |
| Approval / Commit | P6已确认/提交bdc02a3；P7执行授权来自用户“现在授权提交P6，执行CCR-P7”；P7结果确认Pending、未commit |
| Known Risks | 累计89未修（71 Confirmed/13 Robustness/5 CQ）；NPC能力/镜像问题保留；无guest或完整重建；来源与历史产物配对限制见P7 |
| Repository / Processes | boot_linux HEAD bdc02a3204d551bb7c46cf652c2a4ee365827d2f；Working tree contains uncommitted Phase changes；无本轮运行中编译/guest |

Guard：Session明确授权解释旧P6 Pending/P7未授权状态，无State Consistency Conflict。P7开始前保存2689输入/11011行责任；本轮65个native资产按已批准S06更正排除，原ID与非P7行保持。M2业务Active Execution Context不变。P6提交回执见[P6](../npc/verif/records/process/code_correctness_review/P6.md#ccr-p6-approval-commit-20261017)；本轮[P7](../npc/verif/records/process/code_correctness_review/P7.md)、[完成快照](CHANGELOG_AGENT.md#snapshot-ccr-p7-20261017)。P7审阅完成、用户结果确认、commit、P8执行授权分别记录；到此停止。
''' +t[end:];write(p,t)
p=ROOT/'.agent/TASK_QUEUE.md';t=p.read_text();t=re.sub(r'^\| CCR-P7 \|.*$', '| CCR-P7 | Completed（Final Gate PASS） | 本轮授权执行；结果确认/commit Pending | [P7](../npc/verif/records/process/code_correctness_review/P7.md)、[快照](CHANGELOG_AGENT.md#snapshot-ccr-p7-20261017)；14新问题，累计89未修 |',t,flags=re.M)
t=t.replace('| CCR-P8–P10 | Planned，未Start | 各前阶段确认/commit及对应执行授权 | 服务/应用→跨层→最终闭合，计划§7 |','| CCR-P8 | Next（Planned，未Start） | P7结果确认/commit及P8执行授权 | 服务库/应用OS交互余项，计划§7；未授权执行 |\n| CCR-P9–P10 | Planned，未Start | 各前阶段确认/commit及对应执行授权 | 跨层→最终闭合，计划§7 |')
t=t.replace('本轮用户已确认P4并授权提交，P5授权仅来自本轮明确指令；F0029–31按用户回复保留CQ，消费端P6/P9待处理。','本轮用户已确认并授权提交P6、执行P7；P7 Completed，P8未开始；F0029–31按既有用户回复保留CQ，P6消费端证据保留、P9待闭合。');write(p,t)
p=ROOT/'.agent/CHANGELOG_AGENT.md'
marker='<a id="snapshot-ccr-p7-20261017"></a>'
assert marker not in p.read_text(), 'Do not rewrite an existing completion snapshot'
with p.open('a') as f:f.write('''

<a id="snapshot-ccr-p7-20261017"></a>
## Phase Completion Snapshot — CCR-P7（2026-10-17）

- Milestone / Phase：独立CCR / CCR-P7，Completed（Final Gate PASS）；不占用或推进M2/M2-P1。
- Goal：计划§7 U01–U04及相关U13/U14，RV64 crt/libos/libc/syscall/ABI/构建与双平台OS对应；本地适配必审、第三方无关算法不全面审。
- Completed Changes：用户运行时/20号syscall/结构/所有权/错误矩阵、第三方71历史差异与19目录边界、2689原文件入口→2624保留/65 native排除、8322条件导航；14新问题F0076–89，累计89未修。
- Modified Files：P7.md、USER_RUNTIME.md、SYSCALL_ABI.md、THIRD_PARTY_P7.md、p7/证据与脚本；coverage/COVERAGE、findings/FINDINGS、CONTRACTS/BUILD_PATHS/INTERFACES补充；整体计划/PROJECT_OVERVIEW、五README导航；CURRENT_STATE/TASK_QUEUE/DOCUMENT_INDEX。没有生产源码修改。
- Debug / Technical Findings：低errno与reent槽不同、低原型缺失；零size fwrite除零/calloc乘积回绕；exec/env缓冲与所有权；libam heap空；构建失败吞掉。当前RV64未观察返回截断或memory-clobber误编译，不把host现象外推。
- Tests / Validation：本轮56主命令（43 RV64生产单元）、10补充（3 RV64 libam）、5宽度命令；补充中fixture缺原型导致一次失败，2条focused repair后通过，原日志保留。108镜像extent匹配。Final Gate身份/差集/链接/状态检查见p7/validation.json；P6提交前143manifest/70输入为前置复核，不当作本轮OS重测。
- Problems Solved：完成审阅覆盖、逐项记录、来源/错误/ABI交界留证；只解决审阅与证据问题，未修14项或既有75项生产缺陷。
- Remaining Risks：无guest/完整产品重建；libc来源未独立上游比对，历史产物配对Unknown；NPC VME/资源/nterm断点保持；P4/P6 CQ未批准简化；P8/P9边界未闭合。
- Confirmation Source：用户本轮“现在授权提交P6，执行CCR-P7”；Final Gate后停止、不进入P8。P7结果确认Pending，执行授权不等于结果批准。
- HEAD / Commit State：boot_linux bdc02a3204d551bb7c46cf652c2a4ee365827d2f；P6已确认提交；P7 Working tree contains uncommitted Phase changes，未push；.agent/多数报告证据被忽略，未force-add/改规则。
- Next Entry / Gate：CCR-P8 Next/Planned，未Start；P7用户确认+commit+P8执行授权后才可进入。
- Recovery Materials：[P7](../npc/verif/records/process/code_correctness_review/P7.md)、[证据](../npc/verif/records/process/code_correctness_review/p7/README.md)、p7/baseline.json、validation.json、manifest.json；冷启动携带本地忽略资料，/tmp产物可按脚本重建。
- Next Step：停止，等待P7结果确认/commit；不自动修复、不进入P8。
''')
p=ROOT/'.agent/DOCUMENT_INDEX.md';t=p.read_text().replace('## 2026-10-17 CCR-P6当前导航','## 2026-10-17 CCR-P6历史导航（当时停点）');write(p,t)
append_once(p,'<a id="ccr-p7-navigation-20261017"></a>','''## CCR-P7当前导航

[P7/Final Gate](../npc/verif/records/process/code_correctness_review/P7.md)、[用户运行时](../npc/verif/records/process/code_correctness_review/USER_RUNTIME.md)、[syscall/ABI表](../npc/verif/records/process/code_correctness_review/SYSCALL_ABI.md)、[第三方边界](../npc/verif/records/process/code_correctness_review/THIRD_PARTY_P7.md)、[p7证据](../npc/verif/records/process/code_correctness_review/p7/README.md)。2624保留文件/8322条件导航、65 native排除、14新问题；P6已确认提交bdc02a3，P7 Completed但确认/commit Pending，P8未开始。仅隔离编译/宿主探针，不代表完整产品或guest通过。
''')

# Only supporting inputs used by this review, not a new repository scan.
support=['nanos-lite/src/'+x for x in ['syscall.c','syscall.h','fs.c','loader.c','mm.c','proc.c','irq.c','disk.c','resources.S']]
support+=['nanos-lite/include/'+x for x in ['common.h','proc.h','memory.h','fs.h']]
support+=['abstract-machine/am/include/am.h','abstract-machine/am/include/amdev.h','abstract-machine/am/include/arch/riscv.h','abstract-machine/klib/include/klib-macros.h','navy-apps/libs/libndl/include/NDL.h','navy-apps/apps/onscripter/repo/Makefile']
sources=[]
for rel in support:
 p=ROOT/rel;sources.append(dict(path=rel,link=str(p.readlink()) if p.is_symlink() else None,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mode=oct(p.lstat().st_mode&0o777)))
dump(HERE/'support-sources.json',sources)
shutil.copyfile('/tmp/ccr-p7-os-calls.txt',HERE/'os-call-sites.txt')
dump(HERE/'checklist.json',dict(phase='CCR-P7',items={
 x:dict(status='Reviewed within documented depth',evidence=e) for x,e in {
 'crt/startup/argv/env/stack':['USER_RUNTIME.md','SYSCALL_ABI.md'],
 'syscall wrapper/number/argument passing/return/errno':['SYSCALL_ABI.md','p7/findings.json'],
 'libc adaptation/third-party local changes':['THIRD_PARTY_P7.md','p7/libc-provenance.json'],
 'malloc/heap/stdio/file/process APIs':['USER_RUNTIME.md','p7/findings.json'],
 'register/width/pointer/size_t/ssize_t/int/long':['SYSCALL_ABI.md','p7/probes/abi.s','p7/width/results.json'],
 'structure/alignment/ownership/lifetime':['SYSCALL_ABI.md','USER_RUNTIME.md'],
 'RV64 build/link/two-platform OS':['BUILD_PATHS.md','USER_RUNTIME.md','p7/asset-review.json'],
 'coverage/findings/evidence/stop':['COVERAGE.md','P7.md','p7/review-summary.json']}.items()},
 limits=['No guest/full build','No unrelated full libc audit','No download/install','P8 not started']))
print('Navigation, support evidence, checklist, lifecycle snapshot written; run validate.py before delivery.')
