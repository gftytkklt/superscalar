#!/usr/bin/env python3
"""CCR-P4 Final Gate: identity, scoped coverage, probe observations and lifecycle only."""
import ast,collections,gzip,hashlib,json,os,pathlib,re,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[6];CCR=ROOT/'npc/verif/records/process/code_correctness_review';OUT=CCR/'p4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readj(p):return json.loads(p.read_text())
def jl(p):return [json.loads(l) for l in p.open()]
def main():
 checks=[]
 def check(name,condition,details=None):checks.append(dict(check=name,pass_=bool(condition),details=details))
 before=[json.loads(l) for l in gzip.open(OUT/'coverage.before.jsonl.gz','rt')];after=jl(CCR/'coverage.jsonl');source=readj(OUT/'source-evidence.json');base=readj(OUT/'baseline.json')
 selected=lambda x:x.get('effective_phase')=='CCR-P4' and x['review_status']!='Excluded'
 check('P1 stable matrix row identities',len(before)==len(after)==40010 and all(all(a.get(k)==b.get(k) for k in ['row_id','row_kind','path','module_id','source_sha256','effective_phase','effective_phase_responsibilities']) for a,b in zip(before,after)))
 check('non-P4 rows exactly unchanged',all(a==b for a,b in zip(before,after) if not selected(a)))
 rows=[r for r in after if selected(r)];files=[r for r in rows if r['row_kind']=='file'];branches=[r for r in rows if r['row_kind']=='conditional_path']
 check('P4 denominator and no hidden exclusions',(len(files),len(branches))==(120,78) and all(r['review_status']=='ReviewedStatic' for r in rows))
 check('per-file and per-condition traceability',{x['row_id'] for x in jl(OUT/'file-review.jsonl')}=={x['row_id'] for x in files} and {x['row_id'] for x in jl(OUT/'branch-review.jsonl')}=={x['row_id'] for x in branches})
 check('six dimensions populated with P4 disposition',all(all(r.get(k) and not r[k].startswith('Pending') for k in ['normal','boundary_zero_empty_invalid','failure_state_return_cleanup','integer_alignment_lifetime','init_repeat','conditional_upstream_downstream']) and r.get('p4_review',{}).get('scope_limit') for r in rows))
 check('all P4 source/artifact bytes unchanged',all(sha(ROOT/r['path'])==r['source_sha256'] for r in files))
 inv=jl(CCR/'inventory.jsonl');protected=[];drift=[]
 for r in inv:
  p=r.get('path','')
  if not (p.startswith('abstract-machine/') or p in ['npc/.npc_config','nemu/.config']):continue
  if r.get('source_sha256') is None:continue
  f=ROOT/p
  actual=hashlib.sha256(os.readlink(f).encode()).hexdigest() if f.is_symlink() else sha(f) if f.is_file() else None
  protected.append(p)
  if actual!=r['source_sha256']:drift.append(p)
 check('AM all-identity and two config protection',not drift and len(protected)>120,{'checked':len(protected),'drift':drift})
 check('original and updated coverage digests',hashlib.sha256(gzip.decompress((OUT/'coverage.before.jsonl.gz').read_bytes())).hexdigest()==source['coverage_before_sha256'] and sha(CCR/'coverage.jsonl')==source['coverage_after_sha256'])
 artifacts=readj(OUT/'artifact-review.json');check('S03 78 artifact metadata records',len(artifacts)==78 and all('dependency_text' in a or a.get('exit_code')==0 for a in artifacts))
 issues=readj(CCR/'findings.json');p4=readj(OUT/'findings.json');p3=readj(CCR/'p3/findings.json')
 check('stable finding sequence and previous P3 entries unchanged',[x['id'] for x in issues]==[f'CCR-F{i:04d}' for i in range(1,33)] and issues[8:22]==p3 and issues[22:]==p4)
 check('finding classifications',collections.Counter(i['status'] for i in p4)=={'Confirmed':5,'Robustness':2,'ContractQuestion':3} and collections.Counter(i['severity'] for i in p4)=={'High':2,'Medium':5,'Low':3})
 check('finding source hashes and locations',all(sha(ROOT/l['path'])==l['sha256'] and all(1<=n<=len((ROOT/l['path']).read_text().splitlines()) for n in l['lines']) for i in p4 for l in i['locations']))
 probes=readj(OUT/'probe-results.json');supp=readj(OUT/'supplement-results.json');vme=readj(OUT/'vme-results.json');gnu=readj(OUT/'gnu11-results.json')
 cmds=probes['commands']+supp['commands']+vme['commands']+gnu['commands']
 check('103 successful probe commands, isolated cwd',len(cmds)==103 and all(c['exit_code']==0 and c['cwd'].startswith('/tmp/ccr-p4-') and c['argv'][0] not in ['make','git','sudo','pip','apt'] for c in cmds))
 check('GNU11 project dialect confirmed',len(gnu['commands'])==10 and all(c['same_object_bytes'] for c in gnu['commands']))
 check('original probe copied source hashes unchanged',all(sha(ROOT/p)==h for p,h in probes['sources'].items()))
 link={x['name']:x for x in probes['link_results']}
 check('BSS prefix counterexamples observed',all(link[m]['symbols']['test_bss']<link[m]['symbols']['_bss_start'] and link[m]['symbols']['_bss_start']>link[m]['symbols']['_bss_end'] for m in ['xip','sram','sdram-heap']))
 check('stack collision counterexamples observed',all(link[m+'-stack-overlap']['symbols']['_bss_end']>link[m+'-stack-overlap']['symbols']['_stack_pointer'] for m in ['xip','sram','sdram-heap']))
 check('oversize heap counterexamples observed',link['xip-oversize-heap']['symbols']['_heap_end']>0x80400000 and link['sdram-oversize-heap']['symbols']['_heap_end']>0xa8000000 and link['sdram-heap-oversize-heap']['symbols']['_heap_end']>0xa8000000)
 offsets=[]
 for mode in ['sram','psram','psram-ssbl','sdram','sdram-rt']:
  seg={}
  for line in (OUT/(mode+'-aligned-sections.log')).read_text().splitlines():
   a=line.split()
   if len(a)>=6 and a[1] in ['.text','.rodata']:seg[a[1]]=[int(a[k],16) for k in [3,4]]
  offsets.append((seg['.rodata'][0]-seg['.text'][0],seg['.rodata'][1]-seg['.text'][1]))
 check('five LMA/VMA alignment counterexamples observed',all(a!=b for a,b in offsets),offsets)
 check('host observations recorded without hardware PASS','old=0 value=7' in (OUT/'dummy-observation.log').read_text() and 'zero_frame_pdir=(nil)' in (OUT/'vme-host-observation.log').read_text() and 'read_only_leaf_flags=0xdf' in (OUT/'vme-host-observation.log').read_text())
 check('first harness link failure preserved','undefined reference to' in (OUT/'vme-host-compile-attempt1.log').read_text())
 check('ABI metadata and compile-time assertions','double-float ABI' in (OUT/'layout-elf.log').read_text() and '16-bytes' in (OUT/'layout-elf.log').read_text() and 'sizeof(Context)==288' in (OUT/'layout.c').read_text())
 for py in OUT.glob('*.py'):ast.parse(py.read_text(),filename=str(py))
 check('evidence helpers syntax',True)
 current=(ROOT/'.agent/CURRENT_STATE.md').read_text();old=(OUT/'CURRENT_STATE.md.before').read_text();anchor='<a id="ccr-execution-context"></a>';tail='\n## Completed（M0'
 check('M2 current state unchanged',current.split(anchor)[0]==old.split(anchor)[0] and current[current.index(tail):]==old[old.index(tail):])
 queue=(ROOT/'.agent/TASK_QUEUE.md').read_text();oldq=(OUT/'TASK_QUEUE.md.before').read_text();mark='<a id="ccr-queue"></a>';tailq='### 主线一：'
 check('business task queue unchanged',queue.split(mark)[0]==oldq.split(mark)[0] and queue[queue.index(tailq):]==oldq[oldq.index(tailq):])
 history=(ROOT/'.agent/CHANGELOG_AGENT.md').read_bytes();check('immutable previous completion snapshots',history.startswith((OUT/'CHANGELOG_AGENT.md.before').read_bytes()) and history.count(b'id="snapshot-ccr-p4-20261017"')==1)
 check('Completed vs approval/commit and P5 gate','CCR / CCR-P4 / Completed' in current and 'P4结果确认/commit Pending' in current and 'CCR-P5 | Next/Planned，未Start' in queue and '不批准简化' in current)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();staged=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT,text=True).strip()
 check('HEAD preserved and no staged/commit changes',head==base['head'] and not staged)
 tracked=set(subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines());allowed={'README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md'}
 check('tracked production untouched',tracked==allowed,sorted(tracked))
 check('git diff whitespace',subprocess.run(['git','diff','--check'],cwd=ROOT,capture_output=True).returncode==0)
 docs=[CCR/'P4.md',OUT/'README.md'];bad=[]
 for doc in docs:
  for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
   if '://' in target or target.startswith('#'):continue
   path=target.split('#')[0]
   if path=='p4/validation.json':continue
   if path and not (doc.parent/path).exists():bad.append([str(doc),target])
 check('P4 evidence links resolve',not bad,bad)
 result={'date':'2026-10-17','phase':'CCR-P4','status':'PASS' if all(x['pass_'] for x in checks) else 'FAIL','head':head,'checks':checks,'counts':{'files':120,'conditional_rows':78,'artifacts':78,'new_findings':10,'all_findings':32,'successful_probe_commands':len(cmds),'prior_harness_link_failures':1,'link_probes':19},'production_edits':0,'installs':0,'commits':0,'guest_runs':0,'hardware_runs':0,'limits':'Review/structural gate only; known confirmed defects remain, CQ preserved by explicit user instruction; host CSR substitutions and linker fixtures do not prove guest/hardware behavior.'}
 (OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 manifest={str(p.relative_to(CCR)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='manifest.json'}
 for name in ['P4.md','coverage.jsonl','FINDINGS.md','findings.json','CONTRACTS.md','BUILD_PATHS.md','INTERFACES.md']:manifest[name]=sha(CCR/name)
 (OUT/'manifest.json').write_text(json.dumps({'date':'2026-10-17','phase':'CCR-P4','files':manifest},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[x for x in checks if not x['pass_']]},ensure_ascii=False))
 if result['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
