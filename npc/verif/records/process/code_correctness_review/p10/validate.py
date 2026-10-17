#!/usr/bin/env python3
"""Validate CCR-P10 evidence bookkeeping, never product correctness.

Read-only inputs/Git. Writes p10/validation.json. No project code, builds,
old validators, package installation or Git mutation is invoked.
"""
from pathlib import Path
import collections,gzip,hashlib,json,re,subprocess
P=Path(__file__).resolve().parent;B=P.parent;R=P.parents[5]
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*a):return subprocess.check_output(['git','--no-optional-locks','-C',str(R),*a]).decode()
checks=[]
def check(name,ok,detail=None):checks.append({'name':name,'pass':bool(ok),'detail':detail})
base=read(P/'baseline.json');before={}
for x in base['files']:
 raw=gzip.decompress((P/x['snapshot']).read_bytes());before[Path(x['path']).name]=raw.decode()
 check('frozen:'+x['path'],sha(raw)==x['sha256'])
oldcov=[json.loads(s) for s in before['coverage.jsonl'].splitlines()];cov=rows(B/'coverage.jsonl');final=rows(P/'final-coverage.jsonl');summary=read(P/'coverage-summary.json')
check('all_original_coverage_fields_preserved',oldcov==[{k:v for k,v in r.items() if k!='p10_review'} for r in cov])
check('stable_ids_and_order',len(cov)==40010 and len({x['row_id'] for x in cov})==40010 and [r['row_id'] for r in cov]==[r['row_id'] for r in final])
check('final_export_matches_root',[{k:v for k,v in x.items() if k not in ('row_id','row_kind','path','module_id','source_sha256')} for x in final]==[r['p10_review'] for r in cov])
files=[r for r in final if r['row_kind']=='file'];conditions=[r for r in final if r['row_kind']=='conditional_path']
counts=collections.Counter(x['final_status'] for x in files)
check('file_counts',len(files)==15240 and counts['Excluded']==2575 and counts['Unavailable']==2 and counts['ReviewedAtDeclaredDepth']+counts['BoundaryReviewed']==12663,dict(counts))
check('conditions_are_navigation_not_execution',collections.Counter(r['final_status'] for r in conditions)=={'ConditionNavigationReviewed':24656,'Excluded':114} and summary['functional_execution_coverage']=='Unknown / not measured')
waiver=read(P/'acceptance-waiver.json');missing=sorted(r['path'] for r in files if r['final_status']=='Unavailable')
check('missing_retained_not_fabricated',missing==sorted(waiver['paths']) and all(r['source_sha256'] is None for r in files if r['final_status']=='Unavailable'),missing)
check('latest_user_waiver_recorded',waiver['quote']=='缺源暂时不解决，如果没有缺源以外的问题，可以记录下来，并认为任务闭合' and waiver['acceptance_waived_missing_sources']==2 and waiver['p8_status'].startswith('Partial'))
check('no_unexplained_review_field_gap',all(r['final_status'] in ('Excluded','Unavailable') or r['phase_review_fields'] or r['module_id']=='X01' for r in final))
check('no_empty_final_reason_or_evidence',all(r['reason'] and r['evidence'] and r['depth'] for r in final))
check('X01_declared_boundary_only',len([r for r in files if r['module_id']=='X01'])==5 and all(r['depth']=='BuildSideEffectAndProvenance' for r in files if r['module_id']=='X01'))
calc=[]
for m in sorted({r['module_id'] for r in files}):
 rr=[r for r in files if r['module_id']==m];calc.append({'module_id':m,'identities':len(rr),'excluded':sum(r['final_status']=='Excluded' for r in rr),'reviewed_at_declared_depth':sum(r['final_status'] in ('ReviewedAtDeclaredDepth','BoundaryReviewed') for r in rr),'unavailable':sum(r['final_status']=='Unavailable' for r in rr)})
check('52_module_counts',len(calc)==52 and calc==summary['modules'])
check('coverage_summary_denominator',summary['retained_files']==12665 and summary['reviewed_at_declared_depth']==12663 and abs(summary['identity_obligation_percent']-12663/12665*100)<1e-10)
inv=rows(B/'inventory.jsonl');idx={x['path']:x for x in inv}
check('inventory_to_final_identity',set(idx)=={r['path'] for r in files} and all(r['source_sha256']==idx[r['path']]['source_sha256'] for r in files))
for section in ['## 4.','## 7.']:
 def get(t):return t.split(section,1)[1].split('\n## ',1)[0]
 now=(R/'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md').read_text()
 check('plan_scope_or_phase_requirements_unchanged:'+section,get(now)==get(before['CODE_CORRECTNESS_REVIEW_PLAN.md']))
arch=B/'p1/final-closeout/original/npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md'
check('S01_S05_match_P1_archive',now.split('## 4.',1)[1].split('\n## ',1)[0]==arch.read_text().split('## 4.',1)[1].split('\n## ',1)[0])
findings=read(B/'findings.json');oldfind=json.loads(before['findings.json']);ids={f['id'] for f in findings};audit=read(P/'findings-audit.json')
check('119_original_findings_preserved',[{k:v for k,v in f.items() if k!='final_review'} for f in findings]==oldfind and len(findings)==119)
check('stable_finding_numbering',audit['ordered_ids_valid'] and [f['id'] for f in findings]==[f'CCR-F{i:04}' for i in range(1,120)])
check('severity_classification',collections.Counter(f['severity'] for f in findings)=={'High':13,'Medium':79,'Low':27} and collections.Counter(f['status'] for f in findings)=={'Confirmed':86,'Robustness':28,'ContractQuestion':5})
check('all_evidence_location_and_fields_valid',all(not f['missing_fields'] and all(x['sha256_match'] and x['lines_valid'] for x in f['locations']) and all(e['exists'] for e in f['evidence']) for f in audit['checks']))
check('final_original_object_hash',all(f['final_review']['original_object_sha256']==a['original_object_sha256'] for f,a in zip(findings,audit['checks'])))
check('final_issue_links_not_dangling',all(set(r['issue_ids'])<=ids for r in final))
check('regression_and_repair_all119',set(read(P/'repair-priority.json'))==ids and all(f['final_review']['regression'] for f in findings))
check('CQ_not_decided',set(f['id'] for f in findings if f['status']=='ContractQuestion')=={'CCR-F0029','CCR-F0030','CCR-F0031','CCR-F0054','CCR-F0055'} and all(f['final_review']['duplicate_of'] is None for f in findings))
inter=read(B/'interfaces_current.json');oldinter=json.loads(before['interfaces_current.json']);stripped={k:v for k,v in inter.items() if k!='p10_summary'};stripped['interfaces']=[{k:v for k,v in x.items() if k!='p10_final'} for x in inter['interfaces']]
check('original_interface_identity_preserved',stripped==oldinter)
chains=read(B/'p9/chains.json')
check('nine_actual_interfaces_135_fields',[c['id'] for c in chains]==[f'L{i:02}' for i in range(1,10)] and all(len(c['dimensions'])==15 and c['failure_paths'] and c['references'] and c['issue_ids'] and c['dynamic_validation'] for c in chains))
check('interface_evidence_links',all((B/x['p10_final']['evidence']).is_file() for x in inter['interfaces']) and all(set(c['issue_ids'])<=ids for c in chains))
check('endpoint_source_identities',all(e['path'] in idx and e['source_sha256']==idx[e['path']]['source_sha256'] for x in inter['interfaces'] for e in x['endpoints']))
check('missing_not_overridden_by_interfaces',inter['p10_summary']['all_retained_sources_reviewed'] is False and inter['p10_summary']['ccr_review_closed_with_user_waiver'] is True)
contracts=read(B/'contracts.json');check('original_contracts_preserved',{k:v for k,v in contracts.items() if k!='p10_final'}==json.loads(before['contracts.json']))
ia=read(P/'identity-audit.json')
check('source_protection',ia['input_count']==15240 and ia['protected_count']==14971 and not ia['protection_errors'] and not ia['added_paths'] and not ia['removed_paths'] and all(x['match'] for x in ia['checks'] if not x['is_git_metadata']))
check('nested_repos_unchanged',len(ia['nested_repositories'])==10 and all(x['head_match'] and x['diff_match'] and x['status_match'] for x in ia['nested_repositories']))
ma=read(P/'manifest-audit.json');known_local={'p1/build_coverage.py','p1/query_coverage.py','p1/validate_p1.py','p1/validate_rv64_scope.py','p1/apply_rv64_scope.py','p4/README.md','p8/README.md'}
unexplained=[]
for m in ma:
 for x in m['checks']:
  if not x['current_sha256']:unexplained.append(x['path']+':missing')
  rel=x['path'].removeprefix(str(B.relative_to(R))+'/')
  if not x['match'] and re.match(r'p\d+/',rel) and rel not in known_local:unexplained.append(x['path']+':phase evidence changed')
check('historical_manifests_classified',len(ma)==10 and sum(x['count'] for x in ma)==1202 and not unexplained,unexplained)
# Preserve the business state outside the independent CCR section.
for n,a,z in [('CURRENT_STATE.md','## 独立审阅执行上下文','\n## Completed'),('TASK_QUEUE.md','### 独立任务 CCR','\n### 主线一')]:
 def outside(t):i=t.index(a);j=t.index(z,i);return (t[:i]+t[j:]).strip()
 check('business_context_unchanged:'+n,outside((R/'.agent'/n).read_text())==outside(before[n]))
log=(R/'.agent/CHANGELOG_AGENT.md').read_text()
check('prior_snapshots_immutable',log.startswith(before['CHANGELOG_AGENT.md'].rstrip()))
check('single_P10_completion_snapshot',log.count('<a id="snapshot-ccr-p10-20261017"></a>')==1)
state=(R/'.agent/CURRENT_STATE.md').read_text();queue=(R/'.agent/TASK_QUEUE.md').read_text()
check('completion_commit_waiver_separate','CCR / CCR-P10 / Completed' in state and 'Working tree contains uncommitted Phase changes' in state and '| CCR-P8 | Partial' in queue and '| CCR-P10 | Completed' in queue)
check('P9_only_commit',git('rev-parse','HEAD').strip()==base['p9_commit'] and git('diff','--cached','--name-only').strip()=='')
allowed={'README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md'}
changed=set(git('diff','--name-only','HEAD').splitlines());check('tracked_diff_documentation_only',changed<=allowed,sorted(changed))
check('diff_whitespace',subprocess.run(['git','-C',str(R),'diff','--check'],capture_output=True).returncode==0)
# Check local links in new/updated deliverables; old historic embeds retain old semantics.
docs=['FINAL_REPORT.md','FINAL_FINDINGS.md','LIMITATIONS_AND_DECISIONS.md','EVIDENCE_INDEX.md','REPAIR_AND_REGRESSION.md','P10.md','p10/README.md','p10/RECONCILIATION.md']
errors=[];refs=set()
for n in docs:
 p=B/n
 for raw in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  q=raw.split('#')[0]
  if not q or '://' in q:continue
  target=(p.parent/q).resolve();refs.add(str(target.relative_to(R)) if target.is_relative_to(R) else str(target))
  # This invocation emits validation.json after all checks; it need not preexist.
  if target!=P/'validation.json' and not target.is_file():errors.append({'source':n,'target':raw})
check('final_document_links',not errors,errors)
check('user_waiver_anchor_exists','<a id="p10-user-waiver-20261017"></a>' in (B/'P10.md').read_text())
# Verify auditable evidence hashes still match after producing final docs.
ev_errors=[]
for f in audit['checks']:
 for e in f['evidence']:
  p=B/e['reference'].split('#')[0]
  if not p.is_file() or sha(p.read_bytes())!=e['sha256']:ev_errors.append((f['id'],e['reference']))
check('finding_evidence_no_post_audit_drift',not ev_errors,ev_errors)
report={'phase':'CCR-P10','date':'2026-10-17','purpose':'Record/evidence validation; not product correctness','checks':checks,'passed':sum(c['pass'] for c in checks),'failed':sum(not c['pass'] for c in checks),'result':'PASS' if all(c['pass'] for c in checks) else 'FAIL','ccr_acceptance':'ClosedWithExplicitUserMissingSourceWaiver' if all(c['pass'] for c in checks) else 'NotPassed','all_retained_source_reviewed':False,'unreviewed_missing_sources':missing,'unresolved_findings':119,'p10_new_product_dynamic_runs':0,'local_document_references':sorted(refs),'head':git('rev-parse','HEAD').strip(),'p10_committed':False}
(P/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('checks','local_document_references')},ensure_ascii=False,indent=2))
for c in checks:
 if not c['pass']:print('FAIL',c['name'],json.dumps(c['detail'],ensure_ascii=False))
raise SystemExit(0 if report['result']=='PASS' else 1)
