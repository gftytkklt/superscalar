#!/usr/bin/env python3
"""Validate current P1 identities, selected scope and gate evidence, not correctness.

Read-only production access (hash/mode/link/Git); writes only final-closeout evidence.
No Makefile evaluation, compilation, simulation, install or inventory regeneration.
"""
from pathlib import Path
import ast
import argparse
import collections
import gzip
import hashlib
import itertools
import json
import os
import re
import subprocess
from finalize_p1_scope import EXCLUDED_CONFIGS, EXCLUDED_MODULES, RECEIPT

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[4]
OUT = BASE / 'p1/final-closeout'
os.chdir(ROOT)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pre-completion', action='store_true', help='Verify inputs before the completion state transition')
args = parser.parse_args()


def sha(path, link=False):
    if link:
        return hashlib.sha256(os.readlink(path).encode()).hexdigest()
    h = hashlib.sha256()
    with Path(path).open('rb') as src:
        for block in iter(lambda: src.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


checks = {}; details = {}


def check(name, passed, errors=None):
    checks[name] = bool(passed)
    if errors:
        details[name] = errors[:10]


archive = load(OUT / 'original-manifest.json')
bad = []
for path, saved in archive.items():
    data = (OUT / saved['archive']).read_bytes()
    if saved['archive'].endswith('.gz'):
        data = gzip.decompress(data)
    if hashlib.sha256(data).hexdigest() != saved['sha256']:
        bad.append(path)
check('pre_closeout_archive_intact', not bad, bad)
# Original S06 results are immutable; the new gate does not overwrite an old PASS.
old_evidence = ['p1/scope-s06/manifest.json', 'p1/scope-s06/validation.json', 'p1/scope-s06/result.json']
check('prior_scope_results_unchanged', all(sha(BASE / p) == archive[str((BASE / p).relative_to(ROOT))]['sha256'] for p in old_evidence))

inventory = {r['path']: r for r in map(json.loads, (BASE / 'inventory.jsonl').open())}
cfg = load(BASE / 'configs.json'); cfg_by_id = {c['config_id']: c for c in cfg}
old_cfg = load(OUT / archive[str((BASE / 'configs.json').relative_to(ROOT))]['archive'])
check('config_id_and_observed_state_preserved', len(cfg_by_id) == 187 and all(
    all(c.get(k) == cfg_by_id[c['config_id']].get(k) for k in ('status', 'selectors', 'source_sha256')) for c in old_cfg))
check('current_config_scope_consistent', {c['config_id'] for c in cfg if c['review_scope'] == 'Excluded'} == EXCLUDED_CONFIGS
      and all(c['effective_phase'] == [] and not c['review_profiles'] for c in cfg if c['review_scope'] == 'Excluded'))

profiles = load(BASE / 'build_profiles.json')
pids = {p['profile_id'] for p in profiles['profiles']}
expected_pids = {'CCR-NEMU-NATIVE', 'CCR-AM-NEMU', 'CCR-AM-NPC', 'CCR-NAVY-RV64', 'CCR-NEMU-SPIKE', 'CCR-NPC-NEMU-REF'}
check('selected_dual_platform_and_golden_profiles', pids == expected_pids and all(p['selected_for_review'] and p['review_status'] == 'Enumerated' and p['dynamic_validation'] == 'NotRun' for p in profiles['profiles']))
source_drift = [s['path'] for s in profiles['sources'] if sha(s['path']) != s['source_sha256']]
check('build_profile_evidence_hashes_match', not source_drift, source_drift)

rows = [json.loads(l) for l in (BASE / 'coverage.jsonl').open()]
old_path = OUT / archive[str((BASE / 'coverage.jsonl').relative_to(ROOT))]['archive']
bad = []; ids = set(); files = {}; counts = collections.Counter()
with gzip.open(old_path, 'rt') as old:
    for a, b in itertools.zip_longest(map(json.loads, old), rows):
        if a is None or b is None:
            bad.append('row count changed'); continue
        if b['row_id'] in ids:
            bad.append('duplicate ' + b['row_id'])
        ids.add(b['row_id'])
        for k in ('row_id', 'row_kind', 'module_id', 'path', 'canonical_path', 'source_sha256', 'config', 'line_range', 'provenance'):
            if a[k] != b[k]:
                bad.append((b['path'], k))
        counts[b['row_kind'] + ':' + b['review_status']] += 1
        if b['row_kind'] == 'file':
            if b['path'] in files:
                bad.append('duplicate file ' + b['path'])
            files[b['path']] = b
check('row_identity_and_historical_candidates_preserved', not bad and len(rows) == 40010, bad)
check('file_denominator_matches_inventory', files.keys() == inventory.keys() and len(files) == 15240 and all(
    r['source_sha256'] == inventory[p]['source_sha256'] and r['canonical_path'] == inventory[p]['canonical_path'] for p, r in files.items()))

bad = []
for r in rows:
    if r['review_status'] not in ('Excluded', 'Enumerated') or r['issue_ids'] or r['dynamic_validation'] != 'NotRun':
        bad.append((r['path'], 'false review'))
    if r['scope_approval']['current_receipt'] != RECEIPT:
        bad.append((r['path'], 'receipt'))
    if r['review_status'] == 'Excluded':
        if r['review_config'] or r['review_profiles'] or r['effective_phase'] is not None or r['effective_phase_responsibilities']:
            bad.append((r['path'], 'excluded obligation'))
    elif not r['review_config'] or set(r['review_config']) & EXCLUDED_CONFIGS or not r['review_profiles'] or not set(r['review_profiles']) <= pids or not r['effective_phase_responsibilities']:
        bad.append((r['path'], 'incomplete current obligation'))
    if r['target_isa_constraint']['included'] != ['RV64']:
        bad.append((r['path'], 'ISA'))
check('current_obligations_nonempty_and_exclusions_inert', not bad, bad)

# Independent frozen-path oracle: cover directories AND named outputs, including am_native.
target = r'(?:native|am_native|mips32(?:-nemu)?|loongarch32r(?:-nemu)?|riscv32e?(?:-(?:nemu|npc))?|x86(?:_64)?(?:-(?:nemu|qemu))?)'
legacy = [p for p, r in files.items() if p.startswith(('abstract-machine/', 'am-kernels/', 'nanos-lite/', 'navy-apps/', 'rt/bsp/abstract-machine/'))
          and (re.search(r'/build/' + target + r'/', p) or re.search(r'/build/[^/]+-' + target + r'(?:\.(?:a|elf|bin|txt|so|d|o))?$', p) or p == 'navy-apps/libs/libos/build/native.so')]
check('all_1775_other_target_artifacts_excluded', len(legacy) == 1775 and all(files[p]['review_status'] == 'Excluded' for p in legacy))
spike = [p for p in files if p.startswith('nemu/tools/spike-diff/')]
keep = ['nemu/src/isa/riscv32/inst.c', 'nemu/src/isa/riscv64', 'nemu/scripts/native.mk',
        'abstract-machine/am/src/platform/dummy/vme.c', 'abstract-machine/am/src/platform/dummy/mpe.c',
        'abstract-machine/scripts/riscv64-nemu.mk', 'abstract-machine/scripts/riscv64-npc.mk',
        'navy-apps/libs/libc/src/platform/setjmp/riscv.S', 'navy-apps/apps/nanos-lite-guest/Makefile']
check('RV64_shared_host_spike_golden_and_NPC_dummy_preserved', len(spike) == 2223 and all(files[p]['review_status'] == 'Enumerated' for p in keep + spike))
standalone = [p for p in files if p.startswith('abstract-machine/am/src/riscv/spike/') or p == 'abstract-machine/scripts/spike.mk' or p in {'abstract-machine/am/src/platform/dummy/' + x + '.c' for x in ('cte', 'ioe', 'trm')}]
check('standalone_AM_spike_and_unused_dummy_excluded', len(standalone) == 12 and all(files[p]['review_status'] == 'Excluded' for p in standalone))
check('NPC_dummy_config_not_NEMU_or_AM_spike', all(set(files['abstract-machine/am/src/platform/dummy/' + x + '.c']['review_config']) == {'CFG-AM-riscv64-npc', 'CFG-AM-dummy-runtime'} for x in ('vme', 'mpe')))
artifact_bad = []
for p, r in files.items():
    for arch, other in [('nemu', 'npc'), ('npc', 'nemu')]:
        if re.search(r'/build/(?:riscv64-' + arch + r'/|[^/]+-riscv64-' + arch + r'(?:\.|$))', p) and 'CFG-AM-riscv64-' + other in r['review_config']:
            artifact_bad.append(p)
check('RV64_producer_targets_do_not_inherit_other_platform', not artifact_bad, artifact_bad)
check('excluded_ISA_modules_have_no_review_obligation', all(r['review_status'] == 'Excluded' for r in files.values() if r['module_id'] in EXCLUDED_MODULES))
p2 = collections.Counter(r['module_id'] for r in files.values() if r['effective_phase'] == 'CCR-P2')
check('P2_NEMU_RV64_file_denominator_fixed', dict(p2) == {'N02': 8, 'N03': 10, 'N07': 5, 'N12': 6})

contracts = load(BASE / 'contracts.json')
qs = {q['question_id']: q for q in contracts['contract_questions']}
check('contract_questions_not_blanket_entry_blockers', all(qs[q]['status'] == 'NotApplicable/ScopeExcluded' for q in ('CQ-003', 'CQ-004')) and all(not q['p1_or_p2_entry_blocker'] for q in qs.values()))
cids = {c['contract_id'] for c in contracts['module_contracts']}
check('every_retained_row_has_contract_phase_and_profile', all(r['expected_contract'] in cids and r['contract_source'] and r['effective_phase'] and r['review_profiles'] for r in rows if r['review_status'] == 'Enumerated'))
contract_doc = (BASE / 'CONTRACTS.md').read_text()
check('current_contract_anchors_resolve', all('id="' + r['contract_source'].split('#')[1] + '"' in contract_doc for r in rows))
interfaces = load(BASE / 'interfaces_current.json')
check('current_interfaces_have_valid_retained_endpoints', len(interfaces['interfaces']) == 9 and all(
    link['review_status'] == 'Enumerated' and link['dynamic_validation'] == 'NotRun' and link['endpoints'] and all(
        e['path'] in files and files[e['path']]['review_status'] == 'Enumerated' and e['source_sha256'] == files[e['path']]['source_sha256'] for e in link['endpoints']) for link in interfaces['interfaces']))
source_drift = [s['path'] for group in ('project_contracts', 'module_contracts') for c in contracts[group] for s in c.get('sources', []) if s.get('source_sha256') and sha(s['path']) != s['source_sha256']]
check('current_contract_source_hashes_match', not source_drift, source_drift)

drift = []
for r in map(json.loads, (BASE / 'p1/protected-sources.jsonl').open()):
    p = Path(r['path'])
    try:
        if r['entry_type'] in ('missing_dependency', 'deleted_tracked'):
            if p.exists() or p.is_symlink():
                drift.append(str(p))
        elif sha(p, p.is_symlink()) != r['identity_sha256'] or oct(p.lstat().st_mode & 0o7777) != r['mode'] or (r.get('target_sha256') and sha(p) != r['target_sha256']):
            drift.append(str(p))
    except OSError:
        drift.append(str(p))
check('protected_sources_artifacts_modes_links_unchanged', not drift, drift)

def original(path):
    return (OUT / archive[path]['archive']).read_text()


state = Path('.agent/CURRENT_STATE.md').read_text(); queue = Path('.agent/TASK_QUEUE.md').read_text()
sb = lambda s: s[:s.index('<a id="ccr-execution-context"')] + s[s.index('## Completed（M0'):]
qb = lambda s: s[:s.index('<a id="ccr-queue"')] + s[s.index('### 主线一：'):]
check('M2_state_and_queue_unchanged', sb(state) == sb(original('.agent/CURRENT_STATE.md')) and qb(queue) == qb(original('.agent/TASK_QUEUE.md')))
check('previous_completion_snapshots_immutable', Path('.agent/CHANGELOG_AGENT.md').read_text().startswith(original('.agent/CHANGELOG_AGENT.md')))
if args.pre_completion:
    check('P1_reopened_P2_pending', 'CCR / CCR-P1 / Active（Reopened / In Progress' in state and 'CCR-P2 Pending（Planned，未开始）' in state)
else:
    check('P1_completed_P2_not_started_approval_separate', 'CCR / CCR-P1 / Completed' in state and 'P1结果确认/commit Pending' in state and 'CCR-P2 Next/Planned，未Start' in state)
check('HEAD_and_empty_index_unchanged', subprocess.check_output(['git', '--no-optional-locks', 'rev-parse', 'HEAD'], text=True).strip() == '47b6c78d9b91ae0a55ba248222a7cf306c2e174e' and not subprocess.check_output(['git', '--no-optional-locks', 'diff', '--cached', '--name-only']))
check('git_diff_check', subprocess.run(['git', '--no-optional-locks', 'diff', '--check'], capture_output=True).returncode == 0)
check('metadata_helper_syntax', all(ast.parse(p.read_text()) is not None for p in (BASE / 'p1').glob('*.py')))
check('current_profile_navigation', all('BUILD_PATHS.md' in (BASE / p).read_text() for p in ['SCOPE_RV64.md', 'COVERAGE.md', 'CONFIGURATIONS.md', 'CONTRACTS.md', 'P1_FINAL_GATE.md']))

result = {'date': '2026-10-17', 'phase': 'CCR-P1 reopened final gate', 'status': 'PASS' if all(checks.values()) else 'FAIL',
          'checks': checks, 'details': details, 'counts': dict(counts), 'P2_file_denominator': dict(p2),
          'limits': ['Structural scope/identity check only; no code correctness conclusion.', 'Physical/conditional navigation is not compiler reachability or dynamic coverage.', 'Historical binary/source/config pairing remains Unknown.'],
          'business_builds_or_tests': 0, 'production_edits': 0, 'installs': 0, 'commits': 0}
(OUT / ('precompletion-validation.json' if args.pre_completion else 'validation.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
if not args.pre_completion:
    paths = [BASE / p for p in ['coverage.jsonl', 'configs.json', 'contracts.json', 'build_profiles.json', 'BUILD_PATHS.md', 'interfaces_current.json', 'SCOPE_RV64.md', 'COVERAGE.md', 'CONTRACTS.md', 'CONFIGURATIONS.md', 'AVAILABILITY.md', 'INTERFACES.md', 'P1.md', 'P1_FINAL_GATE.md']] + list((BASE / 'p1').glob('*.py')) + [OUT / p for p in ['original-manifest.json', 'result.json', 'validation.json', 'independent-review.json']]
    (OUT / 'manifest.json').write_text(json.dumps({'date': '2026-10-17', 'artifact_sha256': {str(p.relative_to(BASE)): sha(p) for p in paths}, 'previous_evidence': 'original-manifest.json'}, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'checks': len(checks), 'failures': [k for k, v in checks.items() if not v], 'details': details, 'counts': dict(counts)}, ensure_ascii=False, indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
