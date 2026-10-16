#!/usr/bin/env python3
"""CCR-P1 integrated record/identity verification, not a production test.

Reads source bytes and Git state; writes only p1/validation.json and manifest.json.
No project Makefile evaluation, compilation, application execution or installation.
"""
import ast
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

# S06 is an explicitly approved scope change. Preserve the original P1 validator
# and its evidence snapshot; current validation uses the supplemental boundary.
if (Path(__file__).resolve().parent.parent/'build_profiles.json').exists():
    import runpy
    runpy.run_path(str(Path(__file__).with_name('validate_final_gate.py')),run_name='__main__')
    raise SystemExit(0)
if (Path(__file__).resolve().parent.parent/'SCOPE_RV64.md').exists():
    import runpy
    runpy.run_path(str(Path(__file__).with_name('validate_rv64_scope.py')),run_name='__main__')
    raise SystemExit(0)

BASE=Path(__file__).resolve().parent.parent
ROOT=BASE.parents[4]
os.chdir(ROOT)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def rows(path):
    with path.open() as f:
        for line in f:
            if line.strip(): yield json.loads(line)

checks={};errors=[]
def check(name,value):
    checks[name]=bool(value)
    if not value: errors.append(name)

inv={r['path']:r for r in rows(BASE/'inventory.jsonl')}
cfg=json.loads((BASE/'configs.json').read_text());cfgids={r['config_id'] for r in cfg}
contracts=json.loads((BASE/'contracts.json').read_text())
contractids={c['contract_id'] for c in contracts['module_contracts']}
branches={b['branch_id']:b for b in rows(BASE/'branches.jsonl')}
required=set('row_id module_id path canonical_path function_or_path line_range source_sha256 provenance config active_or_dormant expected_contract contract_source review_status evidence_ids issue_ids limits phase scope_approval normal boundary_zero_empty_invalid failure_state_return_cleanup integer_alignment_lifetime init_repeat conditional_upstream_downstream phase_responsibilities'.split())
seen=set();files={};branchrefs=[];usedcfg=set();modules=set();bad=[];total=0
for r in rows(BASE/'coverage.jsonl'):
    total+=1
    if required-set(r) or r['row_id'] in seen: bad.append(('schema/id',r.get('row_id')))
    seen.add(r['row_id']);usedcfg.update(r['config']);modules.add(r['module_id'])
    i=inv.get(r['path'])
    if not i or r['source_sha256']!=i['source_sha256'] or r['canonical_path']!=i['canonical_path']:bad.append(('identity',r['path']))
    if r['expected_contract'] not in contractids or set(r['config'])-cfgids:bad.append(('reference',r['path']))
    if r['review_status']!='Enumerated' or r['dynamic_validation']!='NotRun' or r['issue_ids']:bad.append(('false-review',r['path']))
    if r['row_kind']=='file':
        if r['path'] in files:bad.append(('duplicate-file',r['path']))
        files[r['path']]={k:r[k] for k in ('row_id','module_id','config','phase')}
    else:
        bid=r['branch_refs'][0];branchrefs.append(bid);b=branches.get(bid)
        if not b or r['line_range']!=b['line_range'] or r['source_sha256']!=b['source_sha256']:bad.append(('branch',bid))
        if not r.get('condition_evaluation','').startswith('Unknown'):bad.append(('condition-status',bid))
check('coverage_schema_identity_reference_status',not bad)
check('inventory_to_file_rows_exact',set(inv)==set(files) and len(inv)==15240)
check('branch_to_condition_rows_exact',collections.Counter(branchrefs)==collections.Counter(branches.keys()))
check('all_52_modules_and_187_configs_reachable',len(modules)==52 and usedcfg==cfgids and len(cfgids)==187)
check('only_P1_records_not_formal_review',total==40010)

actual=set()
for root in ('nemu','abstract-machine','nanos-lite','navy-apps'):
    for directory,dirs,names in os.walk(root,followlinks=False):
        for name in names:actual.add((Path(directory)/name).as_posix())
        for name in dirs[:]:
            p=Path(directory)/name
            if p.is_symlink():actual.add(p.as_posix());dirs.remove(name)
frozen={p for p,i in inv.items() if p.split('/')[0] in ('nemu','abstract-machine','nanos-lite','navy-apps') and i['entry_type'] not in ('missing_dependency','deleted_tracked')}
check('four_target_actual_path_set_unchanged',actual==frozen)
drift=[]
for r in rows(BASE/'p1/protected-sources.jsonl'):
    p=Path(r['path'])
    if r['entry_type'] in ('missing_dependency','deleted_tracked'):
        if p.exists() or p.is_symlink():drift.append(r['path'])
        continue
    try:
        h=hashlib.sha256(os.readlink(p).encode()).hexdigest() if p.is_symlink() else sha(p)
        if h!=r['identity_sha256'] or oct(p.lstat().st_mode&0o7777)!=r['mode']:drift.append(r['path'])
        if r.get('target_sha256') and sha(p)!=r['target_sha256']:drift.append(r['path']+' target')
    except OSError:drift.append(r['path'])
check('protected_source_artifact_link_bytes_and_modes_unchanged',not drift)

sourcebad=[]
for c in cfg+contracts['project_contracts']+contracts['module_contracts']:
    for p,h in c.get('source_sha256',{}).items():
        if sha(p)!=h:sourcebad.append(p)
    for source in c.get('sources',[]):
        if source.get('source_sha256') and sha(source['path'])!=source['source_sha256']:sourcebad.append(source['path'])
check('config_and_contract_local_source_hashes_match',not sourcebad)
old=json.loads((BASE/'p1/pre-p1-documents.json').read_text())
plan=Path('npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md').read_text()
scope_rows=lambda s:[l for l in s.splitlines() if re.match(r'\| (?:[NAOUXLS]\d\d|CCR-P\d)',l)]
check('approved_module_scope_phase_interface_rows_unchanged',scope_rows(plan)==scope_rows(old['npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md']))
state=Path('.agent/CURRENT_STATE.md').read_text();queue=Path('.agent/TASK_QUEUE.md').read_text()
strip_state=lambda s:s[:s.index('<a id="ccr-execution-context"')]+s[s.index('## Completed（M0'):]
strip_queue=lambda s:s[:s.index('<a id="ccr-queue"')]+s[s.index('### 主线一：'):]
check('M2_business_state_and_queue_unchanged',strip_state(state)==strip_state(old['.agent/CURRENT_STATE.md']) and strip_queue(queue)==strip_queue(old['.agent/TASK_QUEUE.md']))
check('prior_changelog_snapshot_immutable',Path('.agent/CHANGELOG_AGENT.md').read_text().startswith(old['.agent/CHANGELOG_AGENT.md']))
readmes=['README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md']
nonccr=lambda s:[l for l in s.splitlines() if not re.search(r'CCR|CODE_CORRECTNESS|code_correctness',l)]
check('preexisting_M2_README_content_preserved',all(nonccr(Path(p).read_text())==nonccr(old[p]) and Path(p).read_text().endswith('\n')==old[p].endswith('\n') for p in readmes))
check('P1_completed_approval_commit_pending_P2_not_started','CCR / CCR-P1 / Completed' in state and 'P1结果确认/commit Pending' in state and 'P2 Next/Planned，未Start' in state)
head=subprocess.check_output(['git','--no-optional-locks','rev-parse','HEAD'],text=True).strip()
check('HEAD_unchanged_no_commit',head=='47b6c78d9b91ae0a55ba248222a7cf306c2e174e')
check('Git_index_empty',not subprocess.check_output(['git','--no-optional-locks','diff','--cached','--name-only']))
check('git_diff_check',subprocess.run(['git','--no-optional-locks','diff','--check'],capture_output=True).returncode==0)
check('all_evidence_python_scripts_parse',all(ast.parse(p.read_text()) is not None for p in (BASE/'p1').glob('*.py')))
for name in ('inventory-validation.json','config-validation.json','coverage-review.json'):
    d=json.loads((BASE/'p1'/name).read_text());check(name+'_PASS',d.get('status','').startswith('PASS') or d.get('final_validation',{}).get('status')=='PASS')

# Check new/updated Markdown links relative to their actual documents, excluding web links.
docpaths=list(BASE.glob('*.md'))+[Path(p) for p in old if p.endswith('.md') and 'CHANGELOG' not in p]
linkbad=[]
for p in docpaths:
    urls=collections.Counter(re.findall(r'\]\(([^)]+)\)',p.read_text()))
    if not p.is_absolute() and str(p) in old:
        urls-=collections.Counter(re.findall(r'\]\(([^)]+)\)',old[str(p)]))
    for url in urls:
        if re.match(r'^(https?://|mailto:)',url):continue
        target=url.split('#')[0]
        if target and not (p.parent/target).exists():linkbad.append((str(p),url))
check('updated_document_local_links_resolve',not linkbad)
result={'date':'2026-10-16','task':'CCR-P1','status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors,'details':{'schema_errors':bad[:10],'drift':drift[:10],'source_hash_errors':sourcebad[:10],'link_errors':linkbad[:20]},'counts':{'inventory':len(inv),'coverage':total,'conditions':len(branches),'configs':len(cfgids),'modules':len(modules)},'business_tests':0,'production_builds':0,'production_edits':0,'installs':0,'commits':0,'limitations':['Metadata validation only; no code correctness verdict.','External official source bodies were not downloaded/frozen as bytes; applicability is Pending.','Git metadata identity can change independently; source protection is checked separately.']}
(BASE/'p1/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
manifest={p.relative_to(BASE).as_posix():sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='manifest.json' and '__pycache__' not in str(p)}
(BASE/'p1/manifest.json').write_text(json.dumps({'date':'2026-10-16','task':'CCR-P1','artifact_sha256':manifest,'manifest_self_hash':'not included'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'errors':errors,'details':result['details'],'counts':result['counts']},ensure_ascii=False,indent=2))
raise SystemExit(1 if errors else 0)
