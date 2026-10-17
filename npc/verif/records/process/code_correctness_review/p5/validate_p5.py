#!/usr/bin/env python3
"""CCR-P5 Final Gate: scoped evidence/lifecycle checks, not a product PASS."""
from pathlib import Path
import ast,collections,gzip,hashlib,json,os,re,subprocess
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());B=H.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):return json.loads(p.read_text())
def jl(p):return [json.loads(s) for s in p.read_text().splitlines()]
checks=[]
def check(n,ok,detail=None):checks.append({'check':n,'pass_':bool(ok),'details':detail})
before=[json.loads(x) for x in gzip.decompress((H/'coverage.before.jsonl.gz').read_bytes()).decode().splitlines()]
after=jl(B/'coverage.jsonl');baseline=j(H/'baseline.json')
def selected(r):return r.get('review_scope')!='Excluded' and ('CCR-P5' in r.get('effective_phase_responsibilities',{}) or r.get('effective_phase')=='CCR-P5')
check('baseline HEAD and explicit P5 authorization',baseline['head']=='a419cea8333a84a0037dcd7ee221b0cee495b74f' and 'only CCR-P5' in baseline['authorization'] and baseline['drift']==[])
excluded='am-kernels/tests/riscv-tests/debug/bin/RTOSDemo32.axf'
check('all 40010 original identities retained / only approved S06 scope correction',len(before)==len(after)==40010 and all(all(a.get(k)==b.get(k) for k in ['row_id','row_kind','module_id','path','canonical_path','source_sha256','inventory_id']) and (a['path']==excluded or all(a.get(k)==b.get(k) for k in ['effective_phase','effective_phase_responsibilities','review_scope','review_config'])) for a,b in zip(before,after)))
check('non-P5 rows exactly unchanged',all(a==b for a,b in zip(before,after) if not selected(a)))
check('prior P4 responsibility records preserved',all(a.get('p4_review')==b.get('p4_review') for a,b in zip(before,after)))
check('coverage before SHA matches baseline',hashlib.sha256(gzip.decompress((H/'coverage.before.jsonl.gz').read_bytes())).hexdigest()==baseline['coverage_before_sha256'])
files=jl(H/'file-review.jsonl');branches=jl(H/'branch-review.jsonl');ids={x['row_id'] for x in before if selected(x)};rows=[x for x in after if x['row_id'] in ids]
check('P5 fixed 2537 original entries = 2536 reviewed + 1 approved S06 exclusion / 1213 conditions',(len(files),len(branches),len(rows))==(2537,1213,3750) and all(r['review_status']==('Excluded' if r['path']==excluded else 'ReviewedStatic') for r in rows))
correction=j(H/'scope-correction.json');check('S06 excluded RV32 binary not claimed reviewed',correction['after']['review_scope']=='Excluded' and not correction['after']['review_config'] and not correction['after']['review_profiles'] and not correction['after']['effective_phase_responsibilities'] and next(x for x in files if x['path']==excluded)['review_status']=='Excluded')
check('bidirectional file/condition row-id traceability',{r['row_id'] for r in files+branches}=={r['row_id'] for r in rows} and len({r['row_id'] for r in files+branches})==3750)
six=['normal','boundary_zero_empty_invalid','failure_state_return_cleanup','integer_alignment_lifetime','init_repeat','conditional_upstream_downstream']
check('per-file six dimensions populated with explicit depth',all(r.get('depth') and all(r.get(k) and not r[k].startswith('Pending') for k in six) for r in files))
check('every condition has source and disposition',all(x.get('source_line') and x.get('condition_evaluation') and x.get('disposition') and x.get('abi_lifetime') for x in branches))
drift=[]
for x in baseline['inputs']:
 p=R/x['path'];s=hashlib.sha256(os.readlink(p).encode()).hexdigest() if p.is_symlink() else sha(p) if p.is_file() else None
 if s!=x['sha256']:drift.append(x['path'])
check('all P5 source/artifact bytes unchanged',not drift,{'checked':len(baseline['inputs']),'drift':drift})
drift=[];count=0
for x in jl(B/'inventory.jsonl'):
 if not (x['path'].startswith('abstract-machine/') or x['path'] in ['nemu/.config','npc/.npc_config']) or not x.get('source_sha256'):continue
 p=R/x['path'];s=hashlib.sha256(os.readlink(p).encode()).hexdigest() if p.is_symlink() else sha(p) if p.is_file() else None;count+=1
 if s!=x['source_sha256']:drift.append(x['path'])
check('all AM identities and two active configs unchanged',not drift and count==295,{'checked':count,'drift':drift})
prov=j(H/'source-provenance.json');check('support source hashes match reviewed locations',all(sha(R/p)==s for p,s in prov['support_sources'].items()))
check('preexisting nested Git states retained',all(subprocess.check_output(['git','-C',str(R/p),'rev-parse','HEAD'],text=True).strip()==v['head'] and subprocess.check_output(['git','-C',str(R/p),'status','--short'],text=True)==v['status'] for p,v in prov['repositories'].items()))
assets=j(H/'artifact-review.json');check('S03 per-asset metadata not runtime PASS',len(assets)==1551 and all(x.get('type') and x.get('producer_consumer') and x.get('pairing','').startswith('Unknown') for x in assets))
generated=[x for x in files if x['depth']=='S03GeneratedInterface'];check('generated source interfaces still reviewed',len(generated)==3 and any(x['path'].endswith('build/am-apps.c') and 'CCR-F0049' in x['issue_ids'] for x in generated))
issues=j(B/'findings.json');new=j(H/'findings.json')
prior_sha=hashlib.sha256((json.dumps(issues[:32],ensure_ascii=False,indent=2)+'\n').encode()).hexdigest()
check('old 32 findings exactly preserved',prior_sha==j(B/'p4/manifest.json')['files']['findings.json'])
check('stable finding IDs and classification',[x['id'] for x in issues]==[f'CCR-F{n:04d}' for n in range(1,57)] and issues[32:]==new and collections.Counter(x['status'] for x in new)=={'Confirmed':19,'Robustness':3,'ContractQuestion':2} and collections.Counter(x['severity'] for x in new)=={'High':2,'Medium':12,'Low':10})
fields=['expected_contract_and_basis','actual_and_root_cause','reachability_and_impact','validation','minimal_fix','recommended_regression','unconfirmed_assumptions_and_limits','evidence']
check('finding contracts/impact/limits and locations',all(all(x.get(k) for k in fields) and all(sha(R/l['path'])==l['sha256'] and l['lines'] and all(1<=n<=len((R/l['path']).read_text(errors='replace').splitlines()) for n in l['lines']) for l in x['locations']) for x in new))
records=[j(H/n) for n in ['probe-results.json','supplement-results.json','final-probe-results.json']];cmds=sum((x['commands'] for x in records),[])
check('79 final commands match expected outcomes',len(cmds)==79 and all(c['exit']==c['expected_exit'] for c in cmds),collections.Counter(c['expected_exit'] for c in cmds))
check('all command outputs isolated and no direct install/git/make',all(c['cwd'].startswith('/tmp/ccr-p5-') and c['argv'][0] not in ['make','git','sudo','pip','apt','scons'] and not (Path(c['cwd'])/'.git').exists() for c in cmds))
check('copied original sources unchanged',all(sha(R/x['source'])==x['sha256'] for x in records[0]['copied']) and all(sha(R/x['path'])==x['sha256'] for x in records[1]['copies']))
check('recorded binary/fixture output hashes still match',all(sha(Path(rec['out'])/p)==s for rec,key in [(records[0],'output_hashes'),(records[1],'hashes'),(records[2],'output_hashes')] for p,s in rec[key].items()))
check('20 RV64 production compilation units',len([c for c in records[0]['commands'] if c['name'].startswith('rv-') and c['name']!='rv-version'])==20)
def log(n):return (H/(n+'.log')).read_text()
check('strncpy bounded-source and padding counterexamples','stack-buffer-overflow' in log('strncpy-bound') and '61 00 5a 5a 5a' in log('strncpy-pad'))
check('formatter safe controls and internal overflow','actual=[ab]' in log('format') and 'actual=[ffffffff80000000]' in log('format') and 'size0=4 expected=4' in log('format') and 'runtime error' in log('format-negative') and 'runtime error' in log('format-octal'))
check('malloc and signed helper counterexamples','alignment8=1 cursor=89 capacity=64' in log('malloc') and 'signed integer overflow' in log('int64-min') and '10000 vectors' in log('int64'))
check('NEMU MMIO controls and GPU/oversize observations','sync_event_fb_count_plus1=1' in log('device-gpu') and 'latched_us=21474836482 expected=21474836482' in log('device-timer') and 'outl 0xa0000308=0x9abcdef0' in log('device-disk') and 'outl 0xa000030c=0x12345678' in log('device-disk') and 'len=9 capacity=8 count=0' in log('device-audio-oversize'))
check('NPC normal/split/queue/UART and capability failure evidence','continued=76 expected=76' in log('npc-split-prefix') and 'produced=15' in log('npc-queue') and 'empty=255' in log('npc-uart-rx') and 'present=1 then TX' in log('npc-uart-tx'))
check('BSP context controls and interrupt/heap/lifetime counterexamples','frame-align=0 end-align=0' in log('bsp-context') and 'saved=1 user-data=1234' in log('bsp-context') and 'restore-disabled mie=1 expected=0' in log('bsp-interrupt') and 'bytes=16777216 requested=33554432' in log('bsp-heap') and 'stack-use-after-return' in log('wrapper-lifetime'))
check('real RT declarations expose exact signature mismatch','number of arguments' in log('interrupt-real-declarations') and 'conflicting types for' in log('interrupt-real-declarations') and 'fatal error' not in log('interrupt-real-declarations'))
check('C++ guard ABI and source/fixture failures preserved','<__cxa_guard_acquire>' in log('cpp-stub-disasm') and 'R_RISCV_CALL_PLT\t__cxa_guard_acquire' in log('cpp-guard-disasm') and 'ccache: error' in (H/'attempt1-host-string.log').read_text() and 'undefined reference' in (H/'attempt1-bsp-link.log').read_text())
check('script oracle and failed make counterexamples',any(c['name']=='cpu-oracle-fail' and c['exit']==0 for c in records[2]['commands']) and 'stale.o' in (H/'generator-failed-make-output.mk').read_text() and (H/'generator-failed-make.log').exists())
for p in H.glob('*.py'):ast.parse(p.read_text())
check('all evidence Python scripts parse',True)
cs=(R/'.agent/CURRENT_STATE.md').read_text();oldcs=(H/'CURRENT_STATE.md.before').read_text();tq=(R/'.agent/TASK_QUEUE.md').read_text();oldtq=(H/'TASK_QUEUE.md.before').read_text();ch=(R/'.agent/CHANGELOG_AGENT.md').read_text();oldch=(H/'CHANGELOG_AGENT.md.before').read_text()
check('M2 active context and prior business state unchanged',cs[:cs.index('## 独立审阅执行上下文')]==oldcs[:oldcs.index('## 独立审阅执行上下文')] and cs[cs.index('\n## Completed'):]==oldcs[oldcs.index('\n## Completed'):])
check('business task queue unchanged',tq[:tq.index('### 独立任务 CCR')]==oldtq[:oldtq.index('### 独立任务 CCR')] and tq[tq.index('### 主线一'):]==oldtq[oldtq.index('### 主线一'):])
check('immutable earlier snapshots and one new completion',ch.startswith(oldch) and ch.count('<a id="snapshot-ccr-p5-20261017">')==1)
check('completion distinct from approval and commit / P6 not started','CCR / CCR-P5 / Completed' in cs and 'P5结果确认/commit Pending' in cs and 'uncommitted CCR-P5' in cs and '| CCR-P6 | Next/Planned，未Start |' in tq and 'P6明确授权均Pending' in tq and not (B/'P6.md').exists())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();stage=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R,text=True)
check('HEAD preserved and index empty / no commit',head==baseline['head'] and not stage)
changed=subprocess.check_output(['git','diff','--name-only'],cwd=R,text=True).splitlines()
allowed=['README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md']
check('tracked edits limited to five navigation READMEs',sorted(changed)==sorted(allowed),changed)
check('Git whitespace',subprocess.run(['git','diff','--check'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).returncode==0)
docs=[B/'P5.md',B/'AM_RUNTIME.md',H/'README.md',B/'COVERAGE.md',B/'FINDINGS.md']
bad=[]
for p in docs:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if re.match(r'https?://',target) or target.startswith('#'):continue
  target=target.split('#')[0];f=p.parent/target
  if f in [H/'validation.json',H/'manifest.json']:continue
  if not f.exists():bad.append((str(p),target))
check('P5 report links resolve',not bad,bad)
check('live navigation and API records updated',all('P5' in (R/p).read_text() and '56' in (R/p).read_text() for p in allowed) and j(B/'contracts.json')['p5_review']['record']=='AM_RUNTIME.md' and j(B/'build_profiles.json')['p5_runtime_sources']['npc_local_libgcc_selected'] is False)
result={'phase':'CCR-P5','date':'2026-10-17','head':head,'status':'PASS' if all(x['pass_'] for x in checks) else 'FAIL','checks':checks,'counts':{'files':2537,'conditions':1213,'S03_assets':1551,'new_findings':24,'all_findings':56,'final_probe_commands':79,'cross_compiled_production_units':20},'production_edits':0,'installs':0,'commits':0,'guest_runs':0,'hardware_runs':0,'approval':'P5 result approval and commit Pending; P6 unauthorized / not started','limits':'Static review at declared S01/S02/S03 depths plus isolated host/compiler/script evidence; known defects and CQs retained, no target/hardware/whole RTOS PASS.'}
(H/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
paths=[p for p in H.rglob('*') if p.is_file() and p.name not in ['manifest.json','validation.json']]
paths += [B/n for n in ['P5.md','AM_RUNTIME.md','coverage.jsonl','COVERAGE.md','FINDINGS.md','findings.json','CONTRACTS.md','contracts.json','INTERFACES.md','interfaces_current.json','BUILD_PATHS.md','build_profiles.json']]
paths += [R/p for p in allowed]+[R/'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md',R/'npc/verif/docs/PROJECT_OVERVIEW.md']+[R/'.agent'/n for n in ['CURRENT_STATE.md','TASK_QUEUE.md','CHANGELOG_AGENT.md','DOCUMENT_INDEX.md']]
manifest={'phase':'CCR-P5','date':'2026-10-17','root':str(R),'files':{str(p.relative_to(R)):sha(p) for p in paths},'exclusions':'manifest.json/validation.json excluded to avoid circular digests; prior P0-P4 assets not rewritten'}
(H/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'failed':[x for x in checks if not x['pass_']],'manifest_files':len(paths)},ensure_ascii=False,indent=2))
raise SystemExit(0 if result['status']=='PASS' else 1)
