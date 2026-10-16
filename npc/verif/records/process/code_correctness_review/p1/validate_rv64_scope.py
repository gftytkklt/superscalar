#!/usr/bin/env python3
"""Read-only source/metadata checks for the approved S06 scope amendment.

Writes only scope-s06/validation.json and manifest.json; no production tests.
"""
from pathlib import Path
import ast
import gzip
import hashlib
import itertools
import json
import os
import re
import subprocess

BASE=Path(__file__).resolve().parent.parent
if (BASE/'build_profiles.json').exists():
    import runpy
    runpy.run_path(str(Path(__file__).with_name('validate_final_gate.py')),run_name='__main__')
    raise SystemExit(0)
ROOT=BASE.parents[4];os.chdir(ROOT)
OUT=BASE/'p1/scope-s06'
def sha(path,link=False):
    if link:return hashlib.sha256(os.readlink(path).encode()).hexdigest()
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
checks={};details={}
def check(k,v):checks[k]=bool(v)
original=load(OUT/'original-manifest.json')
frozen_manifest=load(OUT/'original/p1/manifest.json')['artifact_sha256']
check('inventory_and_lexical_identity_evidence_unchanged',all(sha(BASE/p)==frozen_manifest[p] for p in ['inventory.jsonl','branches.jsonl','p1/baseline.json','p1/protected-sources.jsonl','p1/validation.json']))
h=hashlib.sha256()
with gzip.open(OUT/'original/coverage.jsonl.gz','rb') as f:
    for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
check('original_coverage_snapshot_exact',h.hexdigest()==original['coverage.jsonl'])
check('original_text_artifacts_retained',all(sha(OUT/'original'/p)==h for p,h in original.items() if p!='coverage.jsonl'))
cfg=load(BASE/'configs.json');oldcfg=load(OUT/'original/configs.json')
excluded={c['config_id'] for c in cfg if c['review_scope']=='Excluded'}
check('config_IDs_and_observed_selectors_unchanged',len(excluded)==29 and [(c['config_id'],c['status'],c['selectors']) for c in cfg]==[(c['config_id'],c['status'],c['selectors']) for c in oldcfg])
oldfile=gzip.open(OUT/'original/coverage.jsonl.gz','rt');newfile=(BASE/'coverage.jsonl').open()
ids=set();file_rows={};bad=[];count=0;excluded_count=0
for old,new in itertools.zip_longest(oldfile,newfile):
    if old is None or new is None:bad.append('row count changed');continue
    a=json.loads(old);b=json.loads(new);count+=1
    if b['row_id'] in ids:bad.append('duplicate ID')
    ids.add(b['row_id'])
    for key in ('row_id','row_kind','module_id','path','canonical_path','source_sha256','config','line_range','provenance'):
        if a[key]!=b[key]:bad.append((b['path'],key))
    if b['review_status'] not in ('Enumerated','Excluded') or b['issue_ids'] or b['dynamic_validation']!='NotRun':bad.append('false review')
    if set(b['review_config']) & excluded:bad.append('excluded config in current review domain')
    if b['review_status']=='Excluded':
        excluded_count+=1
        if b['effective_phase'] is not None or b['scope_approval']['current_receipt']!='SCOPE_RV64.md#s06-20261016':bad.append('unapproved exclusion')
        if b['review_config']:bad.append('excluded row still has current review obligations')
    if b['target_isa_constraint']['included']!=['RV64']:bad.append('scope not RV64')
    if b['row_kind']=='file':file_rows[b['path']]={'review_status':b['review_status'],'review_config':b['review_config']}
check('matrix_identity_preserved_and_scope_well_formed',not bad and count==40010 and len(file_rows)==15240 and excluded_count==818)
details['matrix_errors']=bad[:8]
keep=['nemu/src/isa/riscv32/inst.c','nemu/src/isa/riscv64','nemu/scripts/native.mk','nemu/tools/qemu-diff/src/isa.c','abstract-machine/scripts/spike.mk','abstract-machine/am/src/platform/dummy/cte.c','navy-apps/libs/libc/src/platform/setjmp/riscv.S','navy-apps/apps/nanos-lite-guest/Makefile']
drop=['nemu/src/isa/mips32/inst.c','nemu/src/isa/loongarch32r/inst.c','nemu/src/isa/x86','abstract-machine/scripts/riscv32-nemu.mk','abstract-machine/am/src/native/trm.c','navy-apps/libs/libos/src/native.cpp','navy-apps/libs/compiler-rt/repo']
check('RV64_shared_and_required_host_entries_retained',all(file_rows[p]['review_status']=='Enumerated' for p in keep))
check('nonRV64_dedicated_entries_excluded',all(file_rows[p]['review_status']=='Excluded' for p in drop))
contracts=load(BASE/'contracts.json');qs={q['question_id']:q for q in contracts['contract_questions']}
check('nonRV_contract_questions_retired_without_resolving_RV64_gaps',all(qs[q]['status']=='NotApplicable/ScopeExcluded' for q in ('CQ-003','CQ-004')) and all(q['status']=='ContractQuestion/Pending' for k,q in qs.items() if k not in ('CQ-003','CQ-004')))
hashbad=[]
for group in ('project_contracts','module_contracts'):
    for c in contracts[group]:
        for s in c.get('sources',[]):
            if s.get('source_sha256') and sha(s['path'])!=s['source_sha256']:hashbad.append(s['path'])
check('current_contract_source_hashes_match',not hashbad)
drift=[]
for line in (BASE/'p1/protected-sources.jsonl').open():
    r=json.loads(line);p=Path(r['path'])
    if r['entry_type'] in ('missing_dependency','deleted_tracked'):
        if p.exists() or p.is_symlink():drift.append(str(p))
        continue
    try:
        if sha(p,p.is_symlink())!=r['identity_sha256'] or oct(p.lstat().st_mode&0o7777)!=r['mode']:drift.append(str(p))
        if r.get('target_sha256') and sha(p)!=r['target_sha256']:drift.append(str(p)+' target')
    except OSError:drift.append(str(p))
check('protected_sources_artifacts_modes_links_unchanged',not drift);details['drift']=drift[:8]
old=load(OUT/'original-text.json');state=Path('.agent/CURRENT_STATE.md').read_text();queue=Path('.agent/TASK_QUEUE.md').read_text()
state_business=lambda s:s[:s.index('<a id="ccr-execution-context"')]+s[s.index('## Completed（M0'):]
queue_business=lambda s:s[:s.index('<a id="ccr-queue"')]+s[s.index('### 主线一：'):]
check('M2_state_and_queue_unchanged',state_business(state)==state_business(old['.agent/CURRENT_STATE.md']) and queue_business(queue)==queue_business(old['.agent/TASK_QUEUE.md']))
check('original_completion_snapshot_immutable',Path('.agent/CHANGELOG_AGENT.md').read_text().startswith(old['.agent/CHANGELOG_AGENT.md']))
check('P1_supplement_completed_without_P2_or_commit_approval','CCR / CCR-P1 / Completed' in state and 'S06' in state and 'P1结果确认/commit Pending' in state and 'P2 Next/Planned，未Start' in state)
check('HEAD_and_empty_index_unchanged',subprocess.check_output(['git','--no-optional-locks','rev-parse','HEAD'],text=True).strip()=='47b6c78d9b91ae0a55ba248222a7cf306c2e174e' and not subprocess.check_output(['git','--no-optional-locks','diff','--cached','--name-only']))
check('git_diff_check',subprocess.run(['git','--no-optional-locks','diff','--check'],capture_output=True).returncode==0)
check('metadata_helper_syntax',all(ast.parse(p.read_text()) is not None for p in (BASE/'p1').glob('*.py')))
check('scope_receipt_linked_from_current_entry_docs',all('SCOPE_RV64.md' in (BASE/p).read_text() for p in ['P1.md','COVERAGE.md','CONTRACTS.md','CONFIGURATIONS.md','INTERFACES.md','AVAILABILITY.md']))
result={'date':'2026-10-16','phase':'CCR-P1 supplemental completion','scope':'S06','status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,'details':details,'business_builds_or_tests':0,'production_edits':0,'installs':0,'commits':0,'limits':['Scope metadata validation only, no correctness verdict.','Mixed conditional arms are constrained to RV64, not evaluated by a preprocessor.']}
(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
paths=[BASE/p for p in ['SCOPE_RV64.md','coverage.jsonl','configs.json','contracts.json','P1.md','COVERAGE.md','CONTRACTS.md','CONFIGURATIONS.md','INTERFACES.md','AVAILABILITY.md']]+list((BASE/'p1').glob('*.py'))+[OUT/'result.json',OUT/'validation.json',OUT/'original-manifest.json']
(OUT/'manifest.json').write_text(json.dumps({'date':'2026-10-16','scope':'S06','artifact_sha256':{p.relative_to(BASE).as_posix():sha(p) for p in paths},'original_scope_manifest':'original/p1/manifest.json'},indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'failures':[k for k,v in checks.items() if not v],'details':details},ensure_ascii=False,indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
