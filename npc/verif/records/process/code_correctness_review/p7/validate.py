#!/usr/bin/env python3
"""CCR-P7 Final Gate: read production, validate records, write only gate evidence."""
from pathlib import Path
import ast,collections,gzip,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[6];HERE=Path(__file__).resolve().parent;BASE=HERE.parent
checks=[]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def check(name,ok,detail):
 checks.append(dict(name=name,pass_=bool(ok),detail=detail))
def read(p):return json.loads(p.read_text())
def cmd(*args):return subprocess.check_output(args,cwd=ROOT,text=True).strip()
baseline=read(HERE/'baseline.json')
drift=[]
for i in baseline['inputs']:
 p=ROOT/i['path'];h=hashlib.sha256(str(p.readlink()).encode()).hexdigest() if p.is_symlink() else sha(p)
 target=sha(p) if p.is_symlink() and p.is_file() else None
 if h!=i['sha256'] or target!=i['target_sha256'] or oct(p.lstat().st_mode&0o777)!=i['mode']:drift.append(i['path'])
check('P7 frozen source/asset hash-mode-link identity',not drift,dict(count=len(baseline['inputs']),drift=drift))
drift=[]
for s in read(HERE/'support-sources.json'):
 p=ROOT/s['path']
 if sha(p)!=s['sha256'] or oct(p.lstat().st_mode&0o777)!=s['mode'] or (str(p.readlink()) if p.is_symlink() else None)!=s['link']:drift.append(s['path'])
check('support source identity',not drift,drift)
before=[json.loads(l) for l in gzip.open(HERE/'coverage.before.jsonl.gz','rt')]
after=[json.loads(l) for l in (BASE/'coverage.jsonl').open()]
check('coverage baseline compressed content hash',hashlib.sha256(gzip.decompress((HERE/'coverage.before.jsonl.gz').read_bytes())).hexdigest()==baseline['coverage_before_sha256'],'baseline equality')
bmap={r['row_id']:r for r in before};amap={r['row_id']:r for r in after}
check('stable coverage IDs',len(amap)==len(after)==40010 and bmap.keys()==amap.keys(),'no add/delete/duplicate')
original=[r for r in before if r.get('effective_phase')=='CCR-P7'];ids={r['row_id'] for r in original}
nonp7=[i for i in bmap if i not in ids and bmap[i]!=amap[i]]
check('non-P7 rows unchanged',not nonp7,dict(non_p7_count=len(before)-len(ids),diff=nonp7))
excluded=[r for r in original if amap[r['row_id']]['review_scope']=='Excluded']
check('S06 corrections limited to 65 frozen native assets',len(excluded)==65 and all('/onscripter/repo/build/' in r['path'] for r in excluded),len(excluded))
check('P7 row closure at declared depth',all(amap[i]['review_status'] in ['ReviewedStatic','BoundaryReviewed','Excluded'] and amap[i].get('p7_review',{}).get('evidence') for i in ids),dict(files=2689,conditions=8322,scope='review_depth controls meaning; not algorithm/guest PASS'))
allissues=read(BASE/'findings.json');old=read(HERE/'findings.before.json');new=read(HERE/'findings.json')
check('old 75 findings immutable',allissues[:75]==old,'append-only issue objects')
check('new issue IDs/status/count',allissues[75:]==new and [f['id'] for f in new]==[f'CCR-F{n:04}' for n in range(76,90)] and collections.Counter(f['status'] for f in new)=={'Confirmed':11,'Robustness':3},len(allissues))
errors=[]
for f in new:
 for l in f['locations']:
  p=ROOT/l['path'];n=len(p.read_text().splitlines())
  if sha(p)!=l['sha256'] or not all(1<=x<=n for x in l['lines']):errors.append([f['id'],l['path']])
 for e in f['evidence']:
  if not (BASE/e).exists():errors.append([f['id'],e])
 for k in ['expected_contract_and_basis','actual_and_root_cause','reachability_and_impact','validation','minimal_fix','recommended_regression','unconfirmed_assumptions_and_limits','functions','severity_rationale','missing_evidence']:
  if not f.get(k):errors.append([f['id'],k])
check('finding location hashes, evidence and fields',not errors,errors)
all_ids={f['id'] for f in allissues}
check('coverage issue references',all(set(amap[i]['issue_ids'])<=all_ids for i in ids),'all IDs resolve')
for name,kind in [('file-review.jsonl','file'),('branch-review.jsonl','conditional_path')]:
 rs=[json.loads(l) for l in (HERE/name).open()];expected={r['row_id'] for r in original if r['row_kind']==kind}
 check(name+' exact denominator',len(rs)==len(expected) and {r['row_id'] for r in rs}==expected,len(rs))
res=[];unexpected=[];logdrift=[]
for folder in ['probes','supplement','width']:
 for r in read(HERE/folder/'results.json'):
  log=HERE/folder/Path(r['log']).name
  res.append((folder,r['name'],r['exit']))
  if not log.is_file() or ('log_sha256' in r and sha(log)!=r['log_sha256']):logdrift.append(r['name'])
  if r['exit']!=r['expected_exit']:unexpected.append((folder,r['name'],r['exit']))
repair=read(HERE/'supplement/repair-results.json')
check('probe logs / explicit fixture repair',not logdrift and unexpected==[('supplement','errno-paths',4)] and len(repair)==2 and all(r['exit']==r['expected_exit']==0 and (HERE/'supplement'/r['log']).is_file() for r in repair),dict(original_commands=len(res),unexpected_preserved=unexpected,repair_commands=2))
fs=read(HERE/'fsimg-match.json')
check('ramdisk/fsimg extents',fs['file_count']==108 and all(x['contiguous'] and x['complete'] and x['image_sha256']==x['fsimg_sha256'] for x in fs['extents']),dict(entries=fs['file_count'],padding=fs['padding']))
prov=read(HERE/'libc-provenance.json')
check('libc HEAD identity and declared provenance',len(prov['tracked'])==850 and all(x['byte_match'] for x in prov['tracked']) and cmd('git','-C','navy-apps/libs/libc','rev-parse','HEAD')==prov['head'],'850 byte matches; no independent upstream authentication')
docfiles=[BASE/n for n in ['P7.md','USER_RUNTIME.md','SYSCALL_ABI.md','THIRD_PARTY_P7.md']]+[HERE/'README.md']
badlinks=[]
for p in docfiles:
 for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('http:','https:','#')):continue
  path=target.split('#',1)[0]
  if not (p.parent/path).exists() and path not in ['p7/validation.json','p7/manifest.json','../P7.md']:badlinks.append([str(p.relative_to(ROOT)),target])
check('new report local links',not badlinks,badlinks)
bad=[]
for p in HERE.glob('*.py'):
 try:ast.parse(p.read_text())
 except SyntaxError as e:bad.append([p.name,str(e)])
check('helper Python syntax',not bad,bad)
head=cmd('git','rev-parse','HEAD');staged=cmd('git','diff','--cached','--name-only');changed=cmd('git','diff','--name-only').splitlines();untracked=cmd('git','ls-files','--others','--exclude-standard').splitlines()
allowed={'README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md'}
check('HEAD / tracked production unchanged / no P7 commit',head==baseline['head'] and not staged and set(changed)<=allowed and all(p.startswith('npc/verif/records/process/code_correctness_review/p7/') for p in untracked),dict(head=head,tracked_changes=changed,staged=staged,untracked_count=len(untracked)))
ws=subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True,text=True)
check('git whitespace',ws.returncode==0,ws.stdout+ws.stderr)
state=(ROOT/'.agent/CURRENT_STATE.md').read_text();prev=(HERE/'CURRENT_STATE.md.before').read_text()
start='## 独立审阅执行上下文';end='## Completed（M0'
check('M2 state untouched',state.split(start)[0]==prev.split(start)[0] and state.split(end,1)[1]==prev.split(end,1)[1],'only dedicated CCR section changed')
queue=(ROOT/'.agent/TASK_QUEUE.md').read_text();prevq=(HERE/'TASK_QUEUE.md.before').read_text()
check('M2 queue untouched',queue.split('### 独立任务 CCR')[0]==prevq.split('### 独立任务 CCR')[0] and queue.split('### 主线一',1)[1]==prevq.split('### 主线一',1)[1],'only dedicated CCR queue changed')
changelog=(ROOT/'.agent/CHANGELOG_AGENT.md').read_text();previous=(HERE/'CHANGELOG_AGENT.md.before').read_text()
check('completion history append-only',changelog.startswith(previous) and changelog.count('<a id="snapshot-ccr-p7-20261017"></a>')==1,'P6 receipt and old snapshots retained')
check('completion / approval / commit / next gate separate',
 'CCR / CCR-P7 / Completed' in state and '结果确认Pending、未commit' in state and 'CCR-P8 Next（Planned，未Start）' in state and 'Working tree contains uncommitted Phase changes' in state and '| CCR-P8 | Next（Planned，未Start）' in queue,
 'P7 Completed; result acceptance and commit Pending; P8 not started')
for p in [ROOT/'README.md',ROOT/'npc/README.md',ROOT/'npc/verif/README.md',ROOT/'npc/verif/records/README.md',ROOT/'npc/verif/records/process/README.md']:
 check('navigation '+str(p.relative_to(ROOT)),'P7.md' in p.read_text() and 'P8未开始' in p.read_text(),'current P7 links')
result=dict(phase='CCR-P7',date='2026-10-17',head=head,final_gate='PASS' if all(c['pass_'] for c in checks) else 'FAIL',checks=checks,limitations=['Static review at declared depth; no full unrelated third-party algorithm audit','Targeted host/compile probes only; no guest/full product build','No production fixes; P7 acceptance/commit pending; stop before P8'])
(HERE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(result['final_gate'],len(checks),'checks')
for c in checks:
 if not c['pass_']:print(c)
if result['final_gate']!='PASS':raise SystemExit(1)
files=list(HERE.rglob('*'))+[BASE/n for n in ['P7.md','USER_RUNTIME.md','SYSCALL_ABI.md','THIRD_PARTY_P7.md','coverage.jsonl','COVERAGE.md','findings.json','FINDINGS.md','CONTRACTS.md','BUILD_PATHS.md','INTERFACES.md']]
files += [ROOT/p for p in ['npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md','npc/verif/docs/PROJECT_OVERVIEW.md',*sorted(allowed),'.agent/CURRENT_STATE.md','.agent/TASK_QUEUE.md','.agent/CHANGELOG_AGENT.md','.agent/DOCUMENT_INDEX.md']]
files=sorted(set(p for p in files if p.is_file() and p!=HERE/'manifest.json' and '__pycache__' not in p.parts))
manifest=dict(phase='CCR-P7',head=head,excludes='manifest self hash only; no temporary binaries promised',files=[dict(path=str(p.relative_to(ROOT)),size=p.stat().st_size,sha256=sha(p)) for p in files])
(HERE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('manifest',len(files),'files; sources unchanged, P8 not started')
