#!/usr/bin/env python3
from pathlib import Path
import json,gzip,hashlib,subprocess,re,collections,ast,os
ROOT=Path(__file__).resolve().parents[6];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
checks=[]
def check(name,ok,detail):checks.append(dict(name=name,passed=bool(ok),detail=detail))
def run(*args):return subprocess.check_output(args,cwd=ROOT,text=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}).strip()
baseline=json.loads((HERE/'baseline.json').read_text());before=[json.loads(x) for x in gzip.open(HERE/'coverage.before.jsonl.gz','rt')];after=[json.loads(x) for x in (BASE/'coverage.jsonl').read_text().splitlines()]
selected=lambda r:r.get('effective_phase')=='CCR-P8' or 'CCR-P8' in r.get('effective_phase_responsibilities',{})
check('baseline compressed hash',hashlib.sha256(gzip.decompress((HERE/'coverage.before.jsonl.gz').read_bytes())).hexdigest()==baseline['coverage_before_sha256'],'original P7 coverage bytes')
check('stable row identities',[r['row_id'] for r in before]==[r['row_id'] for r in after] and len({r['row_id'] for r in after})==len(after),len(after))
diff=[r['row_id'] for r,s in zip(before,after) if not selected(r) and r!=s]
check('non-P8 rows unchanged',not diff,dict(non_p8=sum(not selected(r) for r in before),diff=diff))
drift=[]; frozen=[]
for r in baseline['inputs']:
 p=ROOT/r['path'];exists=p.exists() or p.is_symlink();link=str(p.readlink()) if p.is_symlink() else None
 if (sha(p) if p.is_file() else None)!=r['sha256'] or (p.lstat().st_mode if exists else None)!=r['mode'] or link!=r['link']:drift.append(r['path'])
 old=next(x for x in before if x['row_id']==r['row_id'])
 identity=hashlib.sha256(link.encode()).hexdigest() if p.is_symlink() else (sha(p) if p.is_file() else None)
 if identity!=old.get('source_sha256'):frozen.append(r['path'])
check('6434 source/asset bytes-mode-link session identity',not drift,drift)
check('P1 identity at declared symlink-text semantics',not frozen,frozen)
fr=[json.loads(x) for x in (HERE/'file-review.jsonl').read_text().splitlines()];br=[json.loads(x) for x in (HERE/'branch-review.jsonl').read_text().splitlines()]
check('exact P8 file and condition denominator',{r['row_id'] for r in fr+br}=={r['row_id'] for r in before if selected(r)},dict(files=len(fr),conditions=len(br)))
check('prior per-phase reviews immutable',all(all(r.get(k)==s.get(k) for k in ['p2_review','p3_review','p4_review','p5_review','p6_review','p7_review']) for r,s in zip(before,after)),'shared responsibilities append-only')
old=json.loads((HERE/'findings.before.json').read_text());allf=json.loads((BASE/'findings.json').read_text());new=json.loads((HERE/'findings.json').read_text())
check('89 old finding objects unchanged',allf[:89]==old,'new IDs appended')
check('new IDs counts and classification',[r['id'] for r in new]==[f'CCR-F{x:04}' for x in range(90,116)] and len(allf)==115,dict(new=collections.Counter(r['status'] for r in new),cumulative=collections.Counter(r['status'] for r in allf)))
bad=[]
for r in new:
 for loc in r['locations']:
  p=ROOT/loc['path'];n=len(p.read_text(errors='replace').splitlines())
  if sha(p)!=loc['sha256'] or not all(0<i<=n for i in loc['lines']):bad.append(loc)
 for e in r['evidence']:
  if not (BASE/e).is_file():bad.append(e)
 for k in ['functions','expected_contract_and_basis','actual_and_root_cause','reachability_and_impact','validation','minimal_fix','recommended_regression','missing_evidence','existing_test_coverage','unconfirmed_assumptions_and_limits']:
  if not r.get(k):bad.append((r['id'],k))
check('new finding fields source hash/lines and evidence',not bad,bad)
ids={x['id'] for x in allf};check('coverage issue references',all(set(r.get('issue_ids',[]))<=ids for r in after),'all resolve')
unavailable=[r['path'] for r in fr if r['review_status']=='Unavailable'];check('missing sources retained not reviewed/excluded',set(unavailable)=={'fceux','navy-apps/apps/oslab0/repo'} and all(r['p8_review']['review_status']=='Unavailable' and r.get('review_scope')!='Excluded' for r in after if r['row_kind']=='file' and r['path'] in unavailable),unavailable)
logs=[];known=[]
for d in ['probes','probes-fixed','supplement','app-compile']:
 rs=json.loads((HERE/d/'results.json').read_text())
 for r in rs:
  logfile=HERE/r['log'] if d=='app-compile' else HERE/d/(r['name']+'.log')
  if not logfile.is_file():logs.append(str(logfile))
  if r['exit_code']!=r.get('expected_exit',0):known.append((d,r.get('name',r.get('path')),r['exit_code']))
check('all archived command logs exist',not logs,logs)
check('original environment failures and NWM compile restriction explicit',len(known)==13 and all(d=='probes' and n.startswith('rv64-') or (d=='supplement' and n=='rv64-nwm-window') for d,n,_ in known),known)
fixed=json.loads((HERE/'probes-fixed/results.json').read_text());check('24 fixed commands meet expectations',all(r['matched'] for r in fixed),len(fixed))
apps=json.loads((HERE/'app-compile/results.json').read_text());check('112 app/test units unique logs and successful compile',len(apps)==112 and len({r['log'] for r in apps})==112 and all(r['exit_code']==0 for r in apps),collections.Counter(r['path'].split('/')[2] for r in apps))
check('RWops focused sanitizer outcome',json.loads((HERE/'supplement/rwoverflow-bounds-results.json').read_text())[1]['exit_code']==1,'expectation1; failed before base on second read, no guest')
support=[]
for path in sorted({l['path'] for f in new for l in f['locations']}|{'nanos-lite/src/fs.c','nanos-lite/src/device.c','nanos-lite/src/syscall.c','nanos-lite/include/common.h','navy-apps/libs/libvorbis/src/stb_vorbis.c','navy-apps/apps/onscripter/Makefile','navy-apps/apps/onscripter/repo/Makefile'}):
 p=ROOT/path;support.append(dict(path=path,sha256=sha(p)))
dump(HERE/'support-sources.json',support)
sourcefile={r['path']:r for r in before if r['row_kind']=='file'}
check('support sources agree frozen inventory',all(s['path'] in sourcefile and sourcefile[s['path']].get('source_sha256')==s['sha256'] for s in support),'current source hash agrees P1 file bytes; no widening')
changed=run('git','diff','--name-only').splitlines();allowed=['README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md']
check('tracked production unchanged/index empty/only P7 committed',set(changed)<=set(allowed) and not run('git','diff','--cached','--name-only') and run('git','rev-parse','HEAD')==baseline['head'],dict(head=baseline['head'],changed=changed))
check('git diff whitespace',not run('git','diff','--check'),'no whitespace errors')
prefix=lambda t:t.split('<a id="ccr-execution-context"></a>')[0]
check('M2 Active Execution Context unchanged',prefix((ROOT/'.agent/CURRENT_STATE.md').read_text())==prefix((HERE/'CURRENT_STATE.md.before').read_text()),'CCR dedicated section only')
m2=lambda t:t[t.index('<a id="m2-phases"></a>'):t.index('## Planned Tasks')]
check('M2 phase queue unchanged',m2((ROOT/'.agent/TASK_QUEUE.md').read_text())==m2((HERE/'TASK_QUEUE.md.before').read_text()),'business phases unchanged')
check('old history not rewritten',(ROOT/'.agent/CHANGELOG_AGENT.md').read_text().startswith((HERE/'CHANGELOG_AGENT.md.before').read_text()),'P7 receipt/checkpoint appended')
state=(ROOT/'.agent/CURRENT_STATE.md').read_text();hist=(ROOT/'.agent/CHANGELOG_AGENT.md').read_text();queue=(ROOT/'.agent/TASK_QUEUE.md').read_text()
check('Partial distinct from Completed/no premature P9',all(x in state for x in ['CCR / CCR-P8 / Partial','P8未获提交授权/未commit/未Completed','Working tree contains uncommitted Phase changes']) and '## Phase Completion Snapshot — CCR-P8' not in hist and '| CCR-P8 | Partial' in queue,'P8 incomplete, P9 not started; no completion snapshot')
newdocs=[BASE/x for x in ['P8.md','SERVICE_RUNTIME.md','MEDIA_RUNTIME.md','APP_OS_CALLS.md','BOUNDARIES_P8.md']]+[HERE/'README.md'];broken=[]
for doc in newdocs:
 for link in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
  if re.match(r'\w+://',link) or link.startswith('#'):continue
  path=link.split('#')[0]
  if path and not (doc.parent/path).exists():broken.append(dict(doc=str(doc.relative_to(ROOT)),link=link))
check('new report links',not broken,broken)
syntax=[]
for p in HERE.glob('*.py'):
 try:ast.parse(p.read_text())
 except SyntaxError as e:syntax.append((p.name,str(e)))
check('evidence script syntax',not syntax,syntax)
structural=all(c['passed'] for c in checks)
dump(HERE/'validation.json',dict(phase='CCR-P8',date='2026-10-17',head=baseline['head'],structural_checks='PASS' if structural else 'FAIL',final_gate='PARTIAL' if structural else 'NOT PASSED',phase_status='Partial — not Completed',missing_retained_sources=unavailable,checks=checks,manual_validation='GUI/audio/keyboard/guest/NPC hardware NotRun',stop='Do not commit P8; do not start P9'))
paths=set(newdocs+[BASE/'coverage.jsonl',BASE/'COVERAGE.md',BASE/'FINDINGS.md',BASE/'findings.json',BASE/'CONTRACTS.md',BASE/'INTERFACES.md',BASE/'P7.md',ROOT/'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md',ROOT/'npc/verif/docs/PROJECT_OVERVIEW.md',*[ROOT/x for x in allowed],*[ROOT/'.agent'/x for x in ['CURRENT_STATE.md','TASK_QUEUE.md','CHANGELOG_AGENT.md','DOCUMENT_INDEX.md']]])
paths.update(p for p in HERE.rglob('*') if p.is_file() and p.name!='manifest.json' and '__pycache__' not in p.parts)
dump(HERE/'manifest.json',dict(phase='CCR-P8',head=baseline['head'],phase_status='Partial; not Completed',excludes='self hash; no /tmp binaries promised',files=[dict(path=str(p.relative_to(ROOT)),size=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)]))
print(json.dumps(dict(structural='PASS' if structural else 'FAIL',final_gate='PARTIAL',failed=[r for r in checks if not r['passed']],manifest_count=len(paths)),ensure_ascii=False,indent=2))
raise SystemExit(0 if structural else 1)
