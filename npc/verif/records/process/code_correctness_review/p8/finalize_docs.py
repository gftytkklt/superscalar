#!/usr/bin/env python3
from pathlib import Path
import json,re,collections
ROOT=Path(__file__).resolve().parents[6];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
def write(p,s):p.write_text(s)
summary=json.loads((HERE/'review-summary.json').read_text());findings=json.loads((HERE/'findings.json').read_text())
body='''# CCR-P8 服务库、媒体与应用 OS 交互 / Final Gate

2026-10-17，独立CCR，总计划§7。**Partial（Final Gate未通过，已停止）；不是Completed。** 可用范围静态审阅和证据已交付；保留的fceux/oslab0缺源尚不能验收。P8未获提交授权，未提交；P9未Start，M2业务不变。没有生产代码修复。

## Project Resume / State Consistency Guard

读取根AGENTS/WORKFLOW_POLICY→CURRENT_STATE的CCR专节→TASK_QUEUE→working tree/HEAD，以及总计划§0/§4/§7、P0规划入口、P1–P7记录、coverage/CONTRACTS/INTERFACES/BUILD_PATHS和P6/P7证据导航。既有M2仍仅规划、P1未Start。上次P7 Completed但确认/commit Pending，由本轮用户“现在仅授权提交P7，执行CCR-P8”提供结果接受、P7提交和P8执行授权，不能扩展成P8提交/P9授权。

P7提交前150项manifest无漂移，21个可跟踪文件属于P7；提交 **679cc16** `docs(verif): record confirmed CCR-P7 review`，未push。首次.git索引只读导致命令未生效；同一已授权动作经沙箱权限提升完成，无自动审查拒绝。提交后普通working tree/index干净。原P7快照保留，确认/commit以P7追加回执为准。没有State Consistency Conflict。

P8开始时冻结6,434输入/13,629条件导航责任及原coverage/89问题；技术输入相对P1身份核对需遵守hash_semantics。30个BusyBox fsimg链接的source_sha是链接文本hash，alias_target_sha是目标内容hash，二者不同不是源漂移。本轮源/资源/mode/link不改；PAL两个既有删除的metadata以HEAD blob的docs路径定向补导航，未restore。

## 交付、范围和结果

| 模块 | 文件入口 | 本轮责任 |
|---|---:|---|
| U05 / U06 | 2 / 13 | 全部NDL、miniSDL源和公开API，file/event/timer/video/audio/state/fd/buffer及nanos对应 |
| U07 / U08 | 19 / 2 | 媒体包装/文件/对象/单位与调用侧fixedpt尺寸；纯codec/字体/数学算法按S01/S02排除 |
| U09 / U10 | 17 / 2 | 5个服务应用、嵌套guest新派发域/实际共享源消费，不按同名跳过 |
| U11 | 3 | am-kernels复用接入、fceux/oslab0缺源真实记录；MissingSource2，不计已审 |
| U12 | 4,681 | bird/pal/ons/Lua/BusyBox实际系统调用/适配、本地差异；算法/上游内部/产物边界逐文件留档 |
| U13 / U14 | 4 / 1,691 | 4个媒体/事件/时间测试oracle；P7资产生成消费身份复核，完整装载匹配仍P9 |

共6,434入口：137 ReviewedStatic（按接口深度），6,295 BoundaryReviewed（含资源/第三方/算法/历史metadata），2 Unavailable。13,629条件是逐行责任导航，不是执行覆盖率，不表示每个条件都运行或所有第三方函数全面审。原40,010个coverage稳定ID不增删，非P8行保持，已有p4–p7_review不覆盖。137/6295不得相加解释为6,432个自有实现均全面正确。

交付 [NDL/SDL服务表](SERVICE_RUNTIME.md)、[媒体封装表](MEDIA_RUNTIME.md)、[应用/测试调用清单](APP_OS_CALLS.md)、[逐文件边界](BOUNDARIES_P8.md)、[证据入口](p8/README.md)、[coverage](COVERAGE.md)、[问题](FINDINGS.md#ccr-p8-findings-20261017)。游戏逻辑、VM/脚本业务、纯编解码/字体栅格/OPL/数学内核明确排除；对应文件、混合文件保留的调用点和排除理由可查，不因“全量”扩大边界。

新增26项 **CCR-F0090–F0115：12 Confirmed / 14 Robustness**；累计115（83 Confirmed/27 Robustness/5 CQ；High13/Medium77/Low25），全部未修。关键实证：同格式surface转换换R/B、UpdateRect忽略mask、timer重入、close后audio callback、RWops负pos/键值/奇数字节混音越界、WAV padding和缺fmt、chunk16.16回绕；静态补链还确认音乐编码buffer泄漏、ONS字体/通道适配、guest软件hook递归。未增加或裁决CQ，没有批准教学简化，也没有选择生产修复方案。

## 本轮验证与明确限制

静态优先；已有四测试只审oracle和编译，不冒充运行。24条首组命令中12条RV64编译被ccache只读访问阻断，原日志保留；禁用缓存的24条重跑全部符合预期（包含两个sanitize预期退出1）。27条补充中window.cpp的mman/newlib头冲突保留为编译/能力限制，其余按预期；四测试日志名碰撞后由112组逐一唯一日志补齐。112个应用/测试单元RV64编译成功（PAL41、ONS32、Lua35、四测试各1），不是完整构建/链接。另有RWops focused两组4条命令，普通路径观察和ASan失败均保留，不抹去先前证据。

NDL/SDL/media共15个实现单元本轮RV64独立编译；host探针链接生产逻辑加明确NDL桩或调用mixer内部函数，不执行真实OS/MMIO/设备。所有GUI、键盘交互、声音质量/播放与真实NEMU/NPC全栈均 **ManualNotRun / TargetNotRun**。无安装/下载、原始make、镜像重建或应用启动；仅编译输出到新/tmp目录。

四个嵌套repo既有内容/mode/删除差异保持；未认证独立上游。当前rv64g编译成功不承诺NPC支持浮点/OS；NPC能力和旧binary配对问题沿P4–P7保留。所有问题建议均未实施。

## Final Gate / 下一动作

结构、差集、源码身份、hash/证据/日志/链接、M2不变和授权停点检查见 [validation](p8/validation.json)；交付哈希见 [manifest](p8/manifest.json)。**完整P8验收未通过：fceux与oslab0仍是计划保留的缺源实现，S05没有授权将其排除。** 已有可见包装已审，缺失内部不能标ReviewedStatic；没有用“环境限制”掩盖缺失源码。需提供对应实际源码并补身份/OS交互审阅，或用户明确调整这两项范围，之后仅续作P8；不要求重跑已有通过的局部探针。

状态保存为P8 Partial检查点，**不生成Phase Completion Snapshot**，不把P9设为可执行Next。`.agent`及多数报告/JSON/日志为忽略本地资料，普通P7 commit不是它们的备份；本轮未改跟踪规则、未force-add或上传。到此停止，不提交P8、不进入P9。
'''
write(BASE/'P8.md',body)
write(HERE/'README.md','''# CCR-P8 证据入口与复现

主记录：[P8](../P8.md)、[服务](../SERVICE_RUNTIME.md)、[媒体](../MEDIA_RUNTIME.md)、[应用](../APP_OS_CALLS.md)、[边界](../BOUNDARIES_P8.md)。Final Gate **Partial**：两项保留缺源，未标Completed；P8未提交，P9未Start。

| 文件 | 用途 |
|---|---|
| baseline.json / coverage.before.jsonl.gz / findings.before.json | HEAD679cc16、6,434输入的bytes/mode/link、原coverage和89问题 |
| provenance.json / *-local.diff | 四个嵌套repo当前HEAD/remote/status、tracked byte比较及既有差异；不是上游认证 |
| call-sites.json / app-call-sites.txt | 应用直接调用导航；参数/返回/所有权及间接wrapper解释在APP_OS_CALLS |
| file-review.jsonl / branch-review.jsonl / review-summary.json | 逐文件深度/边界/排除理由/问题，条件责任导航；Unavailable不算已审 |
| findings.json | 新26项完整字段、位置/hash、来源/上下游/回归与限制 |
| probes/ | 原24条；12个编译被ccache只读访问阻断，原样保留 |
| probes-fixed/ | 禁用cache后24条；12生产RV64单元编译、video/rw/timer/close、key与oddmix sanitizer、mixer wrap |
| supplement/ | 27条WAV和应用/media编译，window.cpp头冲突保留；测试同名日志首次碰撞，后112组补齐；两次RWops focused各2命令 |
| app-compile/ | 112单元唯一日志：PAL41/ONS32/Lua35/测试4，全部编译成功；非全产品链接/guest |
| validation.json / manifest.json | Final Gate结构检查与完整未通过原因、最终交付哈希；多数本地文件被git忽略 |

`run_probes.py`/`run_supplement.py`源码可复现隔离单元逻辑，均写新/tmp目录，未调用原Makefile/clone/install。原日志目录保持首次结果；再次执行会更新脚本指定证据目录，长期归档应先复制证据（无需为已通过项重跑）。`run_probes.py`新增rwoverflow分支供focused sanitizer使用；首次普通RWops probe查询tell会把内部负pos重新clamp，未证明安全；补充probe在下一次read前不seek，ASan证实base-1读取。两份结果都保留。

host使用系统libc和NDL受控桩，mixer-wrap/WAV harness直接include生产mixer.c并用gc-sections裁掉无关部分。目标编译使用现有/usr/bin/riscv64-linux-gnu-gcc/g++、本地newlib与Navy头，`CCACHE_DISABLE=1`，未执行目标文件。`app-compile`命令记录每个argv；无需网络/安装。没有保证/tmp二进制永久保存。

`build_review.py`仅从冻结coverage生成P8责任和问题；`finalize_docs.py`仅生成本阶段报告/索引/状态检查点，重跑前应先检查后续工作避免覆盖新阶段。源代码没有修复。缺源恢复后按Guard定向补查，不能用本轮记录代替缺失实现验收。
''')
# Append-only human findings; preserve all old prose and issue objects.
f=BASE/'FINDINGS.md';t=f.read_text();anchor='<a id="ccr-p8-findings-20261017"></a>'
if anchor in t:t=t[:t.index(anchor)]
current='当前状态（2026-10-17）：P8新增26项（12 Confirmed/14 Robustness）；累计115项（83 Confirmed/27 Robustness/5 CQ；High13/Medium77/Low25），均未修。[P8问题](#ccr-p8-findings-20261017) / [P8](P8.md) Final Gate Partial（两项缺源）；P7已确认提交679cc16；P8未提交，P9未开始。下方旧阶段正文保留历史截面。'
t=re.sub(r'当前状态（2026-10-17）：[^\n]*',current,t,count=1)
t+='\n\n'+anchor+'\n## CCR-P8 问题与证据（2026-10-17）\n\n26项新增，均未修；范围/深度见P8，完整字段在findings.json。\n\n'
for r in findings:
 t+='### '+r['id']+' — '+r['title']+'\n\n'
 t+='- 状态/等级：'+r['status']+' / '+r['severity']+'；路径：'+r['functions']+'\n'
 t+='- 位置：'+'；'.join('`'+l['path']+':'+str(l['lines'][0])+'`（SHA '+l['sha256']+'）' for l in r['locations'])+'\n'
 for name,key in [('契约','expected_contract_and_basis'),('根因','actual_and_root_cause'),('触发/影响','reachability_and_impact'),('本轮验证','validation'),('修复建议（未实施）','minimal_fix'),('回归','recommended_regression'),('限制','unconfirmed_assumptions_and_limits')]:t+='- '+name+'：'+r[key]+'\n'
 t+='- 证据：'+', '.join('['+e+']('+e+')' for e in r['evidence'])+'\n\n'
write(f,t)
# Current navigation, retaining historical sections.
nav='独立CCR：[P8审阅/Final Gate]({p}P8.md) **Partial**；6,434文件入口/13,629条件导航，2项缺源未审；新增12 Confirmed/14 Robustness，累计115项未修。[NDL/SDL]({p}SERVICE_RUNTIME.md)、[媒体]({p}MEDIA_RUNTIME.md)、[应用调用]({p}APP_OS_CALLS.md)、[逐文件边界]({p}BOUNDARIES_P8.md)、[证据]({p}p8/README.md)、[覆盖]({p}COVERAGE.md)。P7已确认/提交`679cc16`；P8未提交、不标Completed，P9未开始；生产源码与M2未改。'
for name,prefix in [('README.md','npc/verif/records/process/code_correctness_review/'),('npc/README.md','verif/records/process/code_correctness_review/'),('npc/verif/README.md','records/process/code_correctness_review/'),('npc/verif/records/README.md','process/code_correctness_review/')]:
 f=ROOT/name;write(f,re.sub(r'^独立CCR：.*$',lambda m:nav.format(p=prefix),f.read_text(),count=1,flags=re.M))
f=ROOT/'npc/verif/records/process/README.md';t=f.read_text();t=t.replace('P7确认/commit Pending；P8未开始','P7已确认/提交679cc16；当前见P8行')
line='| [code_correctness_review/P8.md](code_correctness_review/P8.md) | PROCESS | CCR-P8 [NDL/SDL](code_correctness_review/SERVICE_RUNTIME.md)、[媒体](code_correctness_review/MEDIA_RUNTIME.md)、[应用调用](code_correctness_review/APP_OS_CALLS.md)、[逐文件边界](code_correctness_review/BOUNDARIES_P8.md)、[证据](code_correctness_review/p8/README.md) | ⏸ Partial / Final Gate未通过；2项保留缺源；26新问题累计115；P8未提交，P9未开始 |'
if '| [code_correctness_review/P8.md]' not in t:t=t.replace(next(l for l in t.splitlines() if l.startswith('| [code_correctness_review/P7.md]')),next(l for l in t.splitlines() if l.startswith('| [code_correctness_review/P7.md]'))+'\n'+line)
write(f,t)
f=BASE/'COVERAGE.md';t=f.read_text();t=re.sub(r'^当前阶段：.*$',lambda m:'当前阶段：[P8](P8.md) Final Gate Partial；P7已确认/提交679cc16，P8未提交，P9未开始。6,434入口=137接口静态/6,295边界/2缺源；13,629条件仅导航。详[服务](SERVICE_RUNTIME.md)、[媒体](MEDIA_RUNTIME.md)、[应用](APP_OS_CALLS.md)、[边界](BOUNDARIES_P8.md)、[证据](p8/README.md)。',t,count=1,flags=re.M)
if '## P8责任与未闭合范围' not in t:t+='\n## P8责任与未闭合范围\n\nP8覆盖原20,063责任行，文件6,434/条件13,629；原ID、P1分母、非P8行及旧p4–p7_review保持。逐文件新增p8_review；Depth按p8/review-summary.json解释，算法/第三方/资源BoundaryReviewed不算全部实现审阅。fceux/oslab0两项Unavailable仍保留有效P8义务，不能用S02/S05标Excluded。完整静态验收未通过，P8 Partial；P9不是可启动Next。26项新问题F0090–F0115，累计115未修。\n'
write(f,t)
for name in ['CONTRACTS.md','INTERFACES.md']:
 f=BASE/name;t=f.read_text()
 if 'id="p8-local-review-20261017"' not in t:t+='\n\n<a id="p8-local-review-20261017"></a>\n## P8局部核定（2026-10-17）\n\n[服务参数/单位/错误/state](SERVICE_RUNTIME.md)、[media所有权/格式](MEDIA_RUNTIME.md)、[调用与nanos消费](APP_OS_CALLS.md)补充U05–U14及L03–L06消费侧证据；未把L01–L09或interfaces_current标Completed。S01/S02算法边界逐文件可追溯；fceux/oslab0保留缺源，P8 Final Gate Partial。SDL1.2/RIFF官方语义只用于相关既有接口，未选定全面SDL/POSIX兼容契约；CQ保持。\n'
 write(f,t)
f=ROOT/'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md';t=f.read_text();t=re.sub(r'^> 最新执行状态.*$',lambda m:'> 最新执行状态（2026-10-17）：P7已确认/提交`679cc16`；[CCR-P8](../records/process/code_correctness_review/P8.md) Final Gate Partial：可用服务/媒体/应用OS接口审阅交付，2项保留缺源未审。26新问题，累计115未修；P8不标Completed/未提交，P9未开始；§7范围及M2不变。',t,count=1,flags=re.M)
t=t.replace('P7执行由本轮用户明确授权，现Completed，结果确认/commit Pending。','P7已确认/提交679cc16；本轮用户明确授权执行P8，现Final Gate Partial，P9未开始。').replace('不推定P8授权。','不推定P9授权。').replace('- P0–P6已完成/确认/提交；本轮用户授权提交P6并执行CCR-P7，现P7审阅/Final Gate Completed，结果确认与commit Pending；P8–P10未开始。','- P0–P7已完成/确认/提交；本轮用户授权仅提交P7并执行P8；现P8 Final Gate Partial（2项保留缺源），不可标Completed；P9/P10未开始。')
write(f,t)
f=ROOT/'npc/verif/docs/PROJECT_OVERVIEW.md';t=f.read_text().replace('### 2026-10-17 CCR-P7当前交付','### 2026-10-17 CCR-P7历史交付（当时停点）')
if '### 2026-10-17 CCR-P8当前交付' not in t:t+='\n\n### 2026-10-17 CCR-P8当前交付\n\n[P8](../records/process/code_correctness_review/P8.md) Final Gate Partial；P7已确认/提交679cc16；6,434入口/13,629条件导航，26新问题、累计115未修，fceux/oslab0两项保留缺源未审。[服务](../records/process/code_correctness_review/SERVICE_RUNTIME.md)、[媒体](../records/process/code_correctness_review/MEDIA_RUNTIME.md)、[应用](../records/process/code_correctness_review/APP_OS_CALLS.md)、[边界](../records/process/code_correctness_review/BOUNDARIES_P8.md)、[证据](../records/process/code_correctness_review/p8/README.md)。P8未Completed/未提交，P9未开始，生产源码/M2不变。\n'
write(f,t)
# Semantic checkpoint only: incomplete phase must not receive a completion snapshot.
f=ROOT/'.agent/CURRENT_STATE.md';t=f.read_text();a=t.index('| Task / Phase / Status | CCR /');z=t.index('\n## Completed（M0',a)
t=t[:a]+'''| Task / Phase / Status | CCR / CCR-P8 / Partial（Final Gate未通过，已停） |
| Current Objective | 补齐保留缺源后闭合U05–U14余项；可用RV64服务/媒体/应用OS交互已留档 |
| Last Completed Action | P7已按授权提交679cc16；P8可用范围审阅/局部验证、coverage与问题/边界/索引检查点交付 |
| Current Working Files | P8.md、SERVICE_RUNTIME/MEDIA_RUNTIME/APP_OS_CALLS/BOUNDARIES_P8、p8证据、coverage/findings、导航与本地状态 |
| Next Action | 提供fceux/oslab0对应源码并补身份/OS交互审阅，或用户明确调整该两项范围；仅续作P8，P9未Start |
| Blocked By | fceux、navy-apps/apps/oslab0/repo缺源，按S05保留且未审；无安装授权/没有擅自下载 |
| Approval / Commit | P7本轮用户确认并提交679cc16；P8执行授权来自“现在仅授权提交P7，执行CCR-P8”；P8未获提交授权/未commit/未Completed |
| Known Risks | 115未修（83 Confirmed/27 Robustness/5 CQ）；GUI/声音/guest未观察；NPC能力、旧产物配对与第三方来源限制保留 |
| Repository / Processes | boot_linux HEAD679cc16；Working tree contains uncommitted Phase changes；无运行中构建/guest |

Guard：最新明确授权解释旧P7 Pending/P8 Next状态，无冲突；30个链接hash差异来自symlink-text与target bytes不同语义，非漂移。P8不满足完整验收，不生成Completion快照；保存Partial检查点。业务M2上下文未改，P9/P10未开始。恢复入口：[P8](../npc/verif/records/process/code_correctness_review/P8.md)、[证据](../npc/verif/records/process/code_correctness_review/p8/README.md)、[队列](TASK_QUEUE.md#ccr-queue)。
'''+t[z:];write(f,t)
f=ROOT/'.agent/TASK_QUEUE.md';t=f.read_text().replace('用户2026-10-17本轮授权提交P6并执行P7','用户2026-10-17本轮仅授权提交P7并执行P8')
t=t.replace('| CCR-P8 | Active（In Progress） | P7已确认/提交679cc16；本轮用户明确授权执行P8 | U05–U14余项；仅OS交互；Final Gate停、不进入P9 |','| CCR-P8 | Partial（Final Gate未通过，已停） | P7确认/commit已满足679cc16；P8未Completed/未提交 | 2项保留缺源须补源/明确范围调整后仅续作P8；[P8](../npc/verif/records/process/code_correctness_review/P8.md)，26新问题累计115；不进入P9 |')
t=t.replace('本轮用户已确认并授权提交P6、执行P7；P7 Completed，P8未开始','本轮用户已确认并仅授权提交P7、执行P8；P7提交679cc16，P8 Partial，P9未开始')
write(f,t)
f=ROOT/'.agent/CHANGELOG_AGENT.md';t=f.read_text();anchor='<a id="checkpoint-ccr-p8-partial-20261017"></a>'
if anchor not in t:t+='\n\n'+anchor+'''\n## Phase Checkpoint — CCR-P8 Partial（2026-10-17；非Completion）

- Goal / Authorization：独立CCR，总计划§7 U05–U14余项，仅RV64服务/应用/测试OS交互；用户仅授权提交P7并执行P8，Final Gate停、不进入P9。
- Results / Files：P8、SERVICE_RUNTIME、MEDIA_RUNTIME、APP_OS_CALLS、BOUNDARIES_P8及p8证据；coverage 6434文件/13629条件，137接口静态、6295边界、2缺源；F0090–F0115新增26（12 Confirmed/14 Robustness），累计115未修。导航/状态同步，生产源码零修复。
- Validation：24条首组保留12次ccache环境失败，24修正命令符合预期；27补充保留NWM头冲突和4测试日志碰撞说明；112个应用/测试RV64单元编译成功，未链接/运行；RWops补充两组4命令保留；host定向复现与全部GUI/声音/target NotRun分开。结构Final Gate见p8/validation.json，完整验收Partial。
- Blocker / Remaining Work：fceux、oslab0源码缺失，S05并未排除其审阅义务；需补对应源/身份并审OS交互，或用户明确调整范围。已有局部结果不从头重做，原快照不覆盖。
- Technical Findings：timer重入/audio关闭、surface格式、RWops长度、WAV/framing、mixer位置/所有权、ONS缓存/通道、guest派发域；无新长期架构裁决，DECISIONS不变。
- HEAD / Commit：boot_linux679cc16，P7已确认提交/未push；P8 Working tree contains uncommitted Phase changes，未获提交授权。忽略资料仅本地，commit不是备份。
- Gate / Recovery：P8未Completed，未生成Phase Completion Snapshot；P9 Pending未Start。恢复P8.md、p8/baseline/validation/manifest和file-review；不推进M2。
'''
write(f,t)
f=ROOT/'.agent/DOCUMENT_INDEX.md';t=f.read_text().replace('## CCR-P7当前导航','## CCR-P7历史导航（当时停点）')
if '## CCR-P8当前导航' not in t:t+='\n\n## CCR-P8当前导航\n\n[P8/Partial Final Gate](../npc/verif/records/process/code_correctness_review/P8.md)、[NDL/SDL](../npc/verif/records/process/code_correctness_review/SERVICE_RUNTIME.md)、[媒体](../npc/verif/records/process/code_correctness_review/MEDIA_RUNTIME.md)、[应用调用](../npc/verif/records/process/code_correctness_review/APP_OS_CALLS.md)、[逐文件边界](../npc/verif/records/process/code_correctness_review/BOUNDARIES_P8.md)、[证据](../npc/verif/records/process/code_correctness_review/p8/README.md)。P7已确认/提交679cc16，P8 Partial未Completed/未提交，P9未开始；26新问题累计115未修，2项保留缺源不能伪装已审。\n'
write(f,t)
print('P8 Partial documents/state checkpoint updated; no completion, no commit, no P9.')
