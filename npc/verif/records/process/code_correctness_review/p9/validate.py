#!/usr/bin/env python3
"""P9 Final Gate: interface completion and preservation, not product correctness."""
from pathlib import Path
import json,gzip,hashlib,subprocess,os,re,argparse,collections
P=Path(__file__).resolve().parent;B=P.parent;R=P.parents[5];checks=[]
def read(p):return json.loads(p.read_text())
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
def h(b):return hashlib.sha256(b).hexdigest()
def rows(p):return [json.loads(s) for s in p.read_text().splitlines()]
b=read(P/'baseline.json');old=[json.loads(s) for s in gzip.decompress((P/'coverage.jsonl.before.gz').read_bytes()).decode().splitlines()];new=rows(B/'coverage.jsonl');coverage=rows(P/'cross-layer-coverage.jsonl');ids={x['row_id'] for x in coverage}
check('stable 40010 ordered IDs',[r['row_id'] for r in old]==[r['row_id'] for r in new] and len(new)==40010)
unexpected=[]
for a,c in zip(old,new):
 d=dict(c);d.pop('p9_review',None)
 if a['row_id'] in ids and a['module_id']=='X03' and a.get('effective_phase')=='CCR-P9':d['review_status']=a['review_status']
 if d!=a:unexpected.append(a['row_id'])
check('no prior review/object changes outside P9 additive fields and X03 status',not unexpected,unexpected)
check('all 2082 scheduled obligations recorded',len([x for x in old if 'CCR-P9' in x.get('effective_phase_responsibilities',[])])==2082 and all(x['row_id'] in ids for x in old if 'CCR-P9' in x.get('effective_phase_responsibilities',[])))
check('2190 coverage increments: 1951 file / 239 condition',len(ids)==2190 and sum(x['row_kind']=='file' for x in coverage)==1951)
check('two missing source identities still Unavailable',sum(x['review_status']=='Unavailable' for x in new)==2 and all(x.get('p9_review') is None for x in new if x['review_status']=='Unavailable'))
f0=json.loads(gzip.decompress((P/'findings.json.before.gz').read_bytes()));f=read(B/'findings.json');nf=read(P/'findings.json');check('115 old findings unchanged, 4 stable new IDs',f[:115]==f0 and len(f)==119 and f[115:]==nf and [x['id'] for x in nf]==[f'CCR-F{i:04}' for i in range(116,120)])
check('new finding required evidence fields',all(all(x.get(k) for k in ['locations','expected_contract_and_basis','actual_and_root_cause','reachability_and_impact','validation','minimal_fix','recommended_regression','unconfirmed_assumptions_and_limits','evidence']) for x in nf))
sc=read(P/'source-check.json');drift=[]
for x in sc['checks']:
 p=R/x['path'];z=h(os.readlink(p).encode()) if p.is_symlink() else h(p.read_bytes())
 if z!=x['current_sha256'] or not x['matches']:drift.append(x['path'])
check('1951 source/asset identities no unexplained drift',len(sc['checks'])==1951 and not drift and not sc['unindexed'],drift)
actual=read(P/'e2e-attempt5/results.json');changed=[s for s,v in actual['sources'].items() if h((R/s).read_bytes())!=v];check('all isolated build input bytes still current',not changed,changed)
chains=read(P/'chains.json');dims=['syscall number','register','argument','width','pointer','structure layout','address','length','unit','ownership','lifetime','error code','return value','state transition','configuration prerequisite']
check('L01–L09 all 15 dimensions and failure/dynamic limits',len(chains)==9 and [x['id'] for x in chains]==[f'L{i:02}' for i in range(1,10)] and all([d['name'] for d in x['dimensions']]==dims and all(d['assessment'] for d in x['dimensions']) and x['failure_paths'] and x['dynamic_validation'] and x['limits'] for x in chains))
refs=[r for c in chains for r in c['references']];badrefs=[r for r in refs if not (R/r['path']).exists() or max(r['lines'])>len((R/r['path']).read_text().splitlines())];check('reference paths/line positions valid',not badrefs,badrefs)
i0=json.loads(gzip.decompress((P/'interfaces_current.json.before.gz').read_bytes()));i=read(B/'interfaces_current.json');check('original 121 endpoint identities preserved',all(a['endpoints']==c['endpoints'] and a['excluded_historical_endpoints']==c['excluded_historical_endpoints'] for a,c in zip(i0['interfaces'],i['interfaces'])) and i['retained_unique_endpoint_paths']==121)
check('INTERFACES data consume exact P9 facts',all(c['contract_dimensions']=={d['name']:d['assessment'] for d in ch['dimensions']} for c,ch in zip(i['interfaces'],chains)))
fs=read(P/'fsimg-match.json');check('108 current table extents match fsimg/ramdisk',fs['count']==108 and fs['padding']==324 and fs['image_size']==148376064 and all(x['matches'] and x['complete'] and x['contiguous'] for x in fs['entries']))
check('target layout compilation PASS',read(P/'layout-result.json')['returncode']==0)
check('82 actual key enumerators match',read(P/'key-match.json')['equal'] and read(P/'key-match.json')['non_none_count']==82)
check('actual target markers + code0 + GOOD TRAP',actual['e2e_success'] and all(actual['observations'].values()) and actual['commands'][-1]['returncode']==0)
fr=read(P/'faults/results.json')['cases'];check('bad ELF / missing disk fail, mtimer fixture succeeds',all(x['returncode']==1 and x['bad_trap'] and not x['user_started'] for x in fr[:2]) and fr[2]['returncode']==0 and fr[2]['good_trap'] and fr[2]['exit_reloaded'])
pr=read(P/'probes2/results.json');check('3 host seam probes compiled/executed with expected observations',len(pr['commands'])==6 and all(x['returncode']==0 for x in pr['commands']))
for n in range(1,5):check(f'failed build attempt {n} preserved',read(P/f'e2e-attempt{n}/results.json')['commands'][-1]['returncode']!=0)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();check('only prior P8 commit, no P9 commit',head==b['head'])
check('git index unchanged',subprocess.run(['git','diff','--cached','--quiet'],cwd=R).returncode==0)
check('git whitespace',subprocess.run(['git','diff','--check'],cwd=R,stdout=subprocess.PIPE).returncode==0)
state=(R/'.agent/CURRENT_STATE.md').read_text();m2=state.split('## Active Execution Context',1)[1].split('## Current Milestone / Phase / Next Entry',1)[0];check('M2 active context unchanged',m2==b['m2_context'])
history=(R/'.agent/CHANGELOG_AGENT.md').read_bytes();check('immutable history prefix retained',h(history[:b['history_prefix_size']])==b['history_prefix_sha256'])
check('P8 Partial and explicit waiver retained','CCR-P8 | Partial' in (R/'.agent/TASK_QUEUE.md').read_text() and '同意，先提交再执行，那两个缺源暂不解决' in state)
final=(B/'P9.md').exists()
if final:
 check('P9 Completed distinct from approval/commit and P10 not started','CCR / CCR-P9 / Completed' in state and 'Working tree contains uncommitted Phase changes' in state and '| CCR-P10 | Next（Planned，未Start）' in (R/'.agent/TASK_QUEUE.md').read_text())
 docs=[B/'P9.md',B/'CROSS_LAYER_P9.md',P/'README.md',P/'END_TO_END.md']+list(P.glob('L??.md'))
 bad=[]
 for d in docs:
  for t in re.findall(r'\]\(([^)]+)\)',d.read_text()):
   if '://' not in t and not t.startswith('#'):
    q=(d.parent/t.split('#')[0]);
    if not q.exists():bad.append((str(d.relative_to(R)),t))
 check('new evidence navigation resolves',not bad,bad)
 check('unique Phase Completion snapshot',history.count(b'id="snapshot-ccr-p9-20261017"')==1)
res={'phase':'CCR-P9','date':'2026-10-17','gate':'PASS' if all(x['pass'] for x in checks) else 'FAIL','meaning':'P9 interface review deliverables only; known implementation defects/CQ/NotRun retained; not P10/full CCR completion','checks':checks,'passed':sum(x['pass'] for x in checks),'total':len(checks),'final_state_checked':final}
(P/('validation.json' if final else 'pre-gate.json')).write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(res['gate'],res['passed'],'/',len(checks));print(json.dumps([x for x in checks if not x['pass']],ensure_ascii=False,indent=2))
raise SystemExit(0 if res['gate']=='PASS' else 1)
