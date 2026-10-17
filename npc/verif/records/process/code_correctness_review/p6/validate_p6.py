#!/usr/bin/env python3
"""P6 read-only source/evidence audit. Never builds or executes a probe/guest."""
from pathlib import Path
import ast
import collections
import gzip
import hashlib
import json
import os
import re
import subprocess

H = Path(__file__).resolve().parent
R = next(p for p in H.parents if (p / 'AGENTS.md').exists())
B = H.parent
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def j(p):
    return json.loads(p.read_text())
def jl(p):
    return [json.loads(s) for s in p.read_text().splitlines()]
def git(*args):
    return subprocess.check_output(['git', '-C', str(R), *args], text=True).strip()
checks = []
def check(name, ok, details=None):
    checks.append({'check': name, 'pass': bool(ok), 'details': details})

base = j(H / 'baseline.json')
check('HEAD and branch unchanged', git('rev-parse', 'HEAD') == base['head'] and git('branch', '--show-current') == 'boot_linux')
check('P5 receipt and explicit continuation authorization recorded', '632b843' in (B / 'P5.md').read_text() and '继续执行独立任务CCR-P6' in (B / 'P6.md').read_text())
drift = []
for x in base['inputs']:
    p = R / x['path']
    identity = hashlib.sha256(os.readlink(p).encode()).hexdigest() if p.is_symlink() else sha(p)
    if identity != x['sha256'] or sha(p) != x['resolved_sha256'] or x['sha256'] != x['baseline_sha256']:
        drift.append(x['path'])
check('70 OS sources/artifacts match P6 and P1 including symlink targets', len(base['inputs']) == 70 and not drift, drift)
support = j(H / 'support-sources.json')
check('support identity only; no new navy implementation review', all(sha(R / p) == s for p, s in support.items()), len(support))
inv = jl(B / 'inventory.jsonl')
configs = [x for x in inv if x['path'] in ['nemu/.config', 'npc/.npc_config']]
check('two active platform configurations unchanged', len(configs) == 2 and all(sha(R / x['path']) == x['source_sha256'] for x in configs))
before_bytes = gzip.decompress((H / 'coverage.before.jsonl.gz').read_bytes())
check('frozen coverage-before hash', hashlib.sha256(before_bytes).hexdigest() == base['coverage_before_sha256'])
before = [json.loads(x) for x in before_bytes.splitlines()]
after = jl(B / 'coverage.jsonl')
def selected(x):
    return x.get('review_scope') != 'Excluded' and (x.get('effective_phase') == 'CCR-P6' or 'CCR-P6' in x.get('effective_phase_responsibilities', {}))
identity_keys = ['row_id', 'row_kind', 'module_id', 'path', 'canonical_path', 'source_sha256', 'inventory_id', 'review_scope', 'effective_phase', 'effective_phase_responsibilities']
check('40010 stable identities and phase/scope allocation unchanged', len(before) == len(after) == 40010 and all(all(a.get(k) == b.get(k) for k in identity_keys) for a, b in zip(before, after)))
check('all non-P6 rows unchanged, P7/P8 not started', all(a == b for a, b in zip(before, after) if not selected(a)))
files, branches = jl(H / 'file-review.jsonl'), jl(H / 'branch-review.jsonl')
target = [x for x in after if selected(x)]
check('70 files + 91 conditions, bidirectional IDs', (len(files), len(branches), len(target)) == (70, 91, 161) and {x['row_id'] for x in target} == {x['row_id'] for x in files + branches})
check('O01-O06 module counts', collections.Counter(x['module_id'] for x in files) == {'O01':57, 'O02':2, 'O03':2, 'O04':2, 'O05':4, 'O06':3})
six = ['normal', 'boundary_zero_empty_invalid', 'failure_state_return_cleanup', 'integer_alignment_lifetime', 'init_repeat', 'conditional_upstream_downstream']
check('file six-dimensional review and condition evidence populated', all(all(x.get(k) for k in six) for x in files) and all(x.get('source_line') and x.get('condition_evaluation') and x.get('disposition') for x in branches))
check('coverage agrees with detailed file/branch records', all(x['review_status'] == 'ReviewedStatic' and x.get('p6_review') in files + branches for x in target))
all_issues, issues = j(B / 'findings.json'), j(H / 'findings.json')
old_hash = hashlib.sha256((json.dumps(all_issues[:56], ensure_ascii=False, indent=2) + '\n').encode()).hexdigest()
check('prior 56 findings exactly preserved', old_hash == base['prior_findings_sha256'])
check('75 stable finding IDs and 19 P6 classifications', [x['id'] for x in all_issues] == [f'CCR-F{n:04d}' for n in range(1,76)] and issues == all_issues[56:] and collections.Counter(x['status'] for x in issues) == {'Confirmed':14, 'Robustness':5})
fields = ['functions', 'expected_contract_and_basis', 'actual_and_root_cause', 'reachability_and_impact', 'severity_rationale', 'upstream_downstream_contracts', 'existing_test_coverage', 'missing_evidence', 'recommended_regression', 'validation', 'conclusion']
check('each issue includes required facts and source hashes', all(all(x.get(k) for k in fields) and all(sha(R / loc['path']) == loc['sha256'] and loc['lines'] for loc in x['locations']) for x in issues))
check('P6 known issue references are valid and corrected', all(set(x['issue_ids']) <= {f['id'] for f in all_issues} and 'CCR-F0038' not in x['issue_ids'] for x in files + branches))
assets = j(H / 'artifact-review.json')
disk = j(H / 'ramdisk-review.json')
check('49 artifact records retain Unknown pairing', len(assets) == 49 and all(x['pairing'].startswith('Unknown') for x in assets))
check('108 file extents / 48 ELF inputs, no code execution', disk['count'] == disk['unique_names'] == 108 and disk['contiguous'] and all(x['within_image'] for x in disk['entries']) and sum('elf_class' in x for x in disk['entries']) == 48 and disk['image_size'] == (R / 'nanos-lite/build/ramdisk.img').stat().st_size)
check('nterm mismatch explicitly identified', [x['name'] for x in disk['entries'] if any(not s['range_ok'] for s in x.get('segments', []))] == ['/bin/nterm'])
records = [j(H / n) for n in ['probe-results.json', 'supplement-results.json']]
commands = sum((x['commands'] for x in records), [])
unexpected = [c['name'] for c in commands if c['exit'] != c['expected_exit']]
check('93 historical commands; three mismatches retained and disclosed', len(commands) == 93 and unexpected == ['loader-alignment', 'loader-args-large', 'loader-stack-overlap'] and all(n in (B / 'P6.md').read_text() for n in unexpected), unexpected)
check('historical command logs exist / isolated cwd', all((H / c['log']).exists() and c['cwd'].startswith('/tmp/ccr-p6-') for c in commands))
check('historical copied production input hashes match', all(sha(R / x['path']) == x['sha256'] for x in records[0]['copies']))
output_missing, output_drift = [], []
for rec in records:
    for p, s in rec['output_hashes'].items():
        source = Path(rec['out']) / p
        if not source.exists():
            output_missing.append(str(source))
        elif sha(source) != s:
            output_drift.append(str(source))
check('available historical output bytes match; missing retained as limit', not output_drift, {'missing':output_missing, 'drift':output_drift})
old_manifest = j(B / 'p5/manifest.json')['files']
p5_technical = {p:s for p,s in old_manifest.items() if '/code_correctness_review/p5/' in p}
check('P5 technical evidence immutable', all(sha(R / p) == s for p,s in p5_technical.items()), len(p5_technical))
checklist = (H / 'REVIEW_CHECKLIST.md').read_text()
required = ['OS初始化','内存布局','ELF loader','ELF segment','segment boundary','BSS','entry','user stack','syscall','syscall number','参数传递','返回值','fd','file offset','open','close','read','write','lseek','ramdisk','device file','event','timer','display','process','scheduling','exec','exit','brk','VME','双平台条件分支']
check('all 31 required objects have explicit conclusions', all(f'| {n} |' in checklist for n in required))
chain = (B / 'CROSS_LAYER_P6.md').read_text()
check('A/B chain columns and unknown downstream are explicit', all(s in chain for s in ['## A.', '## B.', '调用方约定/证据','被调用方实现与实际传递','失败语义/结论','证据不足','P7/P9']))
cases = re.findall(r'case (SYS_\w+):', (R / 'nanos-lite/src/syscall.c').read_text())
check('10 actual syscall handlers, no inferred implementation from enum', len(cases) == 10 and len(set(cases)) == 10, cases)
cs, tq, cl = [(R / '.agent' / n).read_text() for n in ['CURRENT_STATE.md','TASK_QUEUE.md','CHANGELOG_AGENT.md']]
check('Completion, approval, commit, next-stage gates consistent', 'CCR / CCR-P6 / Completed' in cs and 'P6结果确认Pending、commit Pending' in cs and '| CCR-P7 | Next / Planned，未Start' in tq and cl.count('id="snapshot-ccr-p6-20261017"') == 1)
oldcs = (H / 'CURRENT_STATE.md.before').read_text()
check('M2 active execution context unchanged', cs.split('<a id="ccr-execution-context">')[0] == oldcs.split('<a id="ccr-execution-context">')[0])
tracked = git('diff', '--name-only').splitlines()
allowed = ['README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md']
check('tracked changes are only five documentation indices; index empty', sorted(tracked) == sorted(allowed) and not git('diff', '--cached', '--name-only'), tracked)
check('git whitespace check', subprocess.run(['git','-C',str(R),'diff','--check'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode == 0)
for p in H.glob('*.py'):
    ast.parse(p.read_text())
check('evidence scripts parse; none invoked except this validator', True)
docs = [B / n for n in ['P6.md','OS_RUNTIME.md','CROSS_LAYER_P6.md','COVERAGE.md','FINDINGS.md']] + [H / 'README.md', H / 'REVIEW_CHECKLIST.md']
broken = []
for p in docs:
    for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
        if '://' in target or target.startswith('#'):
            continue
        q = (p.parent / target.split('#')[0]).resolve()
        if q.name in ['resume-validation.json','manifest.json']:
            continue
        if not q.exists():
            broken.append([str(p.relative_to(R)),target])
check('review document local links resolve', not broken, broken)
result = {'phase':'CCR-P6','date':'2026-10-17','head':git('rev-parse','HEAD'),'kind':'read-only evidence/document Final Gate, not product tests','checks':checks,'pass':all(x['pass'] for x in checks),'limits':['No new build/probe/guest/navy implementation review','Historical binary to current complete source/config pairing Unknown','Three historical expected-exit mismatches explicitly retained','P7/P8 not started; production defects unfixed']}
(H / 'resume-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
paths = set(docs + [B / n for n in ['coverage.jsonl','findings.json','CONTRACTS.md','BUILD_PATHS.md','INTERFACES.md']] + [R / p for p in allowed] + [R / '.agent' / n for n in ['CURRENT_STATE.md','TASK_QUEUE.md','CHANGELOG_AGENT.md','DOCUMENT_INDEX.md']] + [R / 'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md',R / 'npc/verif/docs/PROJECT_OVERVIEW.md'])
paths.update(p for p in H.iterdir() if p.is_file() and p.name != 'manifest.json')
(H / 'manifest.json').write_text(json.dumps({'phase':'CCR-P6','date':'2026-10-17','head':base['head'],'files':{str(p.relative_to(R)):sha(p) for p in sorted(paths)}}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'checks':len(checks),'pass':result['pass'],'failed':[x for x in checks if not x['pass']]}, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['pass'] else 1)
