#!/usr/bin/env python3
"""CCR-P10 read-only input/evidence audit; writes only p10/*-audit.json.

This is a bookkeeping/evidence check, not a program correctness test.
Does not run project code, make, old validators, guest, network or git mutations.
"""
from pathlib import Path
import ast
import collections
import hashlib
import json
import os
import stat
import subprocess

P = Path(__file__).resolve().parent
B = P.parent
R = P.parents[5]
def sha(b): return hashlib.sha256(b).hexdigest()
def read(p): return json.loads(p.read_text())
def rows(p): return [json.loads(s) for s in p.read_text().splitlines()]
def write(n, v): (P/n).write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n')
def git(p, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(p), *args])

inv = rows(B/'inventory.jsonl')
cov = rows(B/'coverage.jsonl')
files = [r for r in cov if r['row_kind']=='file']
identity = []
for x in inv:
    p = R/x['path']
    h = sha(os.readlink(p).encode()) if p.is_symlink() else sha(p.read_bytes()) if p.is_file() else None
    mode = oct(stat.S_IMODE(p.lstat().st_mode)) if p.exists() or p.is_symlink() else None
    identity.append({'path':x['path'], 'entry_type':x['entry_type'],
                     'is_git_metadata':x['is_git_metadata'], 'old_sha256':x['source_sha256'],
                     'sha256':h, 'old_mode':x.get('mode'), 'mode':mode,
                     'match':h==x['source_sha256'] and mode==x.get('mode'),
                     'resolved_sha256':sha(p.read_bytes()) if p.is_symlink() and p.is_file() else None})
protected = rows(B/'p1/protected-sources.jsonl')
by_path = {x['path']:x for x in identity}
protection_errors = []
for x in protected:
    c = by_path[x['path']]
    if c['sha256']!=x['identity_sha256'] or c['mode']!=x['mode'] or c['resolved_sha256']!=x.get('target_sha256'):
        protection_errors.append(x['path'])

# Re-enumerate precisely the P1 navigation scope, not the whole workspace.
tree = ast.parse((B/'p1/inventory_capture.py').read_text())
names = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('TARGETS','SUPPORT_DIRS','SUPPORT_FILES','MISSING'):
        names[node.targets[0].id] = eval(compile(ast.Expression(node.value), '<P1 literal scope>', 'eval'), {'__builtins__':{}}, {})
current = set(names['SUPPORT_FILES']) | set(names['MISSING'])
for root in names['TARGETS']+names['SUPPORT_DIRS']:
    p = R/root
    if not p.exists() or p.is_symlink() or not p.is_dir():
        current.add(root); continue
    for d, dirs, fs in os.walk(p, followlinks=False):
        for n in list(dirs):
            q = Path(d)/n
            if q.is_symlink(): current.add(str(q.relative_to(R))); dirs.remove(n)
        current.update(str((Path(d)/n).relative_to(R)) for n in fs)
old_paths = {x['path'] for x in inv}
deleted = {x['path'] for x in inv if x['entry_type']=='deleted_tracked'}
repos = []
for name,x in read(B/'p1/repositories.json').items():
    if name=='.': continue
    head=git(R/name,'rev-parse','HEAD').decode().strip()
    diff=sha(git(R/name,'diff','--no-ext-diff','--no-textconv','HEAD','--binary'))
    status=sha(git(R/name,'status','--short','--untracked-files=all'))
    repos.append({'path':name,'head':head,'head_match':head==x['head'],
                  'diff_sha256':diff,'diff_match':diff==x['diff_binary_sha256'],
                  'status_sha256':status,'p1_status_sha256':x['status_sha256'],
                  'status_match':status==x['status_sha256']})
write('identity-audit.json', {'input_count':len(inv), 'checks':identity,
     'protected_count':len(protected),'protection_errors':protection_errors,
     'added_paths':sorted(current-old_paths),'removed_paths':sorted(old_paths-current-deleted),
     'p1_deleted_paths':sorted(deleted), 'nested_repositories':repos})

manifests=[]
for rel in ['p1/manifest.json','p1/scope-s06/manifest.json','p1/final-closeout/manifest.json','p2/manifest.json']+[f'p{i}/manifest.json' for i in range(4,10)]:
    obj=read(B/rel)
    data=obj.get('files',obj.get('artifact_sha256',obj))
    if isinstance(data,list): pairs=[(a['path'],a['sha256']) for a in data]
    else: pairs=[(k,v if isinstance(v,str) else v.get('sha256')) for k,v in data.items() if isinstance(v,(dict,str))]
    checks=[]
    for name,h in pairs:
        if not h or len(h)!=64: continue
        q=R/name if name.startswith(('.agent/','npc/','README')) else B/name
        if not q.exists() and (B/Path(rel).parent/name).exists():q=B/Path(rel).parent/name
        now=sha(q.read_bytes()) if q.is_file() else None
        checks.append({'path':str(q.relative_to(R)),'sha256':h,'current_sha256':now,'match':now==h})
    manifests.append({'manifest':rel,'checks':checks,'count':len(checks),'mismatches':[x for x in checks if not x['match']]})
write('manifest-audit.json',manifests)

findings=read(B/'findings.json'); findings_audit=[]
for f in findings:
    locations=[]
    for x in f['locations']:
        p=R/x['path'];h=sha(p.read_bytes()) if p.is_file() else None
        lines=x.get('lines',[])
        locations.append({'path':x['path'],'lines':lines,'sha256_match':h==x['sha256'],
                          'lines_valid':bool(lines) and min(lines)>0 and max(lines)<=len(p.read_bytes().splitlines()) if p.is_file() else False})
    ev=[]
    for name in f['evidence']:
        q=B/name.split('#')[0]
        ev.append({'reference':name,'exists':q.exists(),'sha256':sha(q.read_bytes()) if q.is_file() else None})
    required=['id','title','severity','status','phase','locations','actual_and_root_cause','validation','minimal_fix','recommended_regression','unconfirmed_assumptions_and_limits','evidence']
    missing=[k for k in required if not f.get(k)]
    if not (f.get('expected_and_basis') or f.get('expected_contract_and_basis')):missing.append('expected_contract')
    if not (f.get('reachable_path_and_trigger') or f.get('reachability_and_impact')):missing.append('reachability')
    findings_audit.append({'id':f['id'],'severity':f['severity'],'status':f['status'],
                           'original_object_sha256':sha(json.dumps({k:v for k,v in f.items() if k!='final_review'},ensure_ascii=False,sort_keys=True).encode()),
                           'missing_fields':missing,'locations':locations,'evidence':ev})
write('findings-audit.json', {'count':len(findings), 'ordered_ids_valid':[f['id'] for f in findings]==[f'CCR-F{i:04}' for i in range(1,120)],
    'severity':dict(collections.Counter(f['severity'] for f in findings)),
    'status':dict(collections.Counter(f['status'] for f in findings)), 'checks':findings_audit})

summary={'inventory':len(inv),'coverage':len(cov),'ordered_unique_ids':len({r['row_id'] for r in cov})==len(cov),
         'inventory_coverage_path_difference':sorted({r['path'] for r in files}^{x['path'] for x in inv}),
         'status':{k:dict(collections.Counter(r['review_status'] for r in cov if r['row_kind']==k)) for k in ['file','conditional_path']},
         'unavailable':[r['path'] for r in files if r['review_status']=='Unavailable'],
         'no_phase_review':[r['row_id'] for r in cov if r['review_status']!='Excluded' and not any(k.startswith('p') and k.endswith('_review') and k!='p10_review' for k in r)],
         'input_sources_sha256':{n:sha((B/n).read_bytes()) for n in ['inventory.jsonl','coverage.jsonl','findings.json','interfaces_current.json']}}
write('coverage-audit.json',summary)
print(json.dumps({'identity_count':len(inv),'protected_count':len(protected),'protection_errors':protection_errors,
 'added':sorted(current-old_paths),'removed':sorted(old_paths-current-deleted),
 'source_drift_nonmetadata':[x['path'] for x in identity if not x['match'] and not x['is_git_metadata']],
 'nested_head_diff_status_errors':[x['path'] for x in repos if not x['head_match'] or not x['diff_match'] or not x['status_match']],
 'manifest_checks':sum(x['count'] for x in manifests),
 'phase_local_manifest_mismatch':[x['path'] for m in manifests for x in m['mismatches'] if ('/'+m['manifest'].split('/')[0]+'/') in x['path']],
 'finding_field_errors':[x['id'] for x in findings_audit if x['missing_fields']],
 'finding_location_errors':[(x['id'],a['path']) for x in findings_audit for a in x['locations'] if not a['sha256_match'] or not a['lines_valid']],
 'finding_evidence_errors':[(x['id'],a['reference']) for x in findings_audit for a in x['evidence'] if not a['exists']],
 'status':summary['status'],'no_phase_review_count':len(summary['no_phase_review'])},ensure_ascii=False,indent=2))
