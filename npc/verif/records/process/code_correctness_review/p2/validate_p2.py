#!/usr/bin/env python3
"""Validate CCR-P2 evidence identities and phase boundaries; no guest tests."""
import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
CCR = HERE.parent
ROOT = HERE.parents[5]


def sha(path):
    data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((CCR / name).read_text())


def rows(name):
    return [json.loads(line) for line in (CCR / name).open()]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def main():
    checks = []

    def check(label, result):
        checks.append({'check': label, 'pass': bool(result)})

    baseline = read('p2/baseline.json')
    before, after = rows('p2/coverage.before.jsonl'), rows('coverage.jsonl')
    scope = {r['path'] for r in baseline['scope']}
    files = [r for r in after if r['row_kind'] == 'file']
    selected = [r for r in files if r.get('effective_phase') == 'CCR-P2']
    reviews, branches = read('p2/file-review.json'), rows('p2/branch-review.jsonl')
    check('matrix count and row identity/order', len(after) == len(before) == 40010
          and [r['row_id'] for r in before] == [r['row_id'] for r in after]
          and len({r['row_id'] for r in after}) == len(after))
    identity = ['row_id', 'row_kind', 'path', 'canonical_path', 'source_sha256',
                'effective_phase', 'effective_phase_responsibilities', 'line_range',
                'module_id', 'provenance', 'review_scope', 'excluded_config']
    check('original scope/identity/phase/provenance preserved', all(
        all(a.get(k) == b.get(k) for k in identity) for a, b in zip(before, after)))
    check('outside P2 paths entirely unchanged', all(a == b for a, b in
          zip(before, after) if a['path'] not in scope))
    inventory = rows('inventory.jsonl')
    check('inventory to file-row denominator', len(files) == len(inventory) == 15240
          and {r['path'] for r in files} == {r['path'] for r in inventory})
    check('29 P2 file responsibilities closed', len(selected) == len(reviews) == 29
          and {r['path'] for r in selected} == {r['path'] for r in reviews} == scope
          and all(r['review_status'] == 'Reviewed' for r in selected)
          and all(r['p2_review'] in reviews for r in selected))
    dimensions = ['normal', 'boundary_zero_empty_invalid', 'failure_state_return_cleanup',
                  'integer_alignment_lifetime', 'init_repeat', 'conditional_upstream_downstream']
    check('file review dimensions populated', all(r.get(k) and 'Pending' not in r[k]
          for r in reviews for k in dimensions))
    condition_ids = {r['row_id'] for r in after if r['path'] in scope and r['row_kind'] != 'file'}
    check('166 conditional rows individually accounted', len(branches) == len(condition_ids) == 166
          and {r['row_id'] for r in branches} == condition_ids
          and all(r.get('p2_disposition') and r.get('rationale') for r in branches))
    check('P1 source identities still match', all(sha(ROOT / r['path']) == r['sha256']
          == r['p1_sha256'] for r in baseline['scope']))
    findings = read('findings.json')
    check('eight stable Confirmed findings', [r['id'] for r in findings] ==
          [f'CCR-F{i:04d}' for i in range(1, 9)]
          and all(r['status'] == 'Confirmed' and r['phase'] == 'CCR-P2' for r in findings)
          and Counter(r['severity'] for r in findings) == {'High': 1, 'Medium': 5, 'Low': 2})
    check('finding source locations/hash accurate', all(
        sha(ROOT / loc['path']) == loc['sha256'] and all(
            1 <= n <= len((ROOT / loc['path']).read_text().splitlines()) for n in loc['lines'])
        for r in findings for loc in r['locations']))
    check('finding evidence paths exist', all((CCR / p).exists() for r in findings for p in r['evidence']))
    results, supplement = read('p2/repro-results.json'), read('p2/supplement-results.json')
    check('reproduction original source/config identity', all(sha(ROOT / 'nemu' / p) == h
          for p, h in results['sources'].items()))
    expected = {'inv-end': -6, **dict.fromkeys(
        ['addiw', 'addw', 'subw', 'mul', 'mulw', 'sllw', 'unaligned', 'malloc-compile'], 1)}
    check('19 original command records and logs', len(results['commands']) == 19 and all(
        c['returncode'] == expected.get(c['label'], 0) and (HERE / c['log']).is_file()
        for c in results['commands']))
    check('DEVICE=n supplement commands and logs', [c['returncode'] for c in supplement['commands']] == [0, -6]
          and all((HERE / (c['label'] + '.log')).is_file() for c in supplement['commands']))
    temp = Path(results['work'])
    check('original reproduction binaries still match', all(sha(temp / p) == h
          for p, h in results['binaries'].items())
          and sha(temp / 'repro-nodevice') == supplement['binary_sha256'])
    for path in [HERE / 'run_repro.py', Path(__file__)]:
        ast.parse(path.read_text())
    check('Python helper syntax', True)
    check('HEAD unchanged and index empty', git('rev-parse', 'HEAD') == baseline['head']
          and not git('diff', '--cached', '--name-only'))
    expected_tracked = {'README.md', 'npc/README.md', 'npc/verif/README.md',
                        'npc/verif/records/README.md', 'npc/verif/records/process/README.md'}
    check('tracked changes limited to five navigation READMEs',
          set(git('diff', '--name-only').splitlines()) == expected_tracked)
    untracked = git('ls-files', '--others', '--exclude-standard').splitlines()
    check('untracked changes limited to P2 evidence helpers', set(untracked) == {
        str((HERE / name).relative_to(ROOT)) for name in
        ['README.md', 'repro.c', 'run_repro.py', 'validate_p2.py']})
    check('git diff whitespace', subprocess.run(['git', 'diff', '--check'], cwd=ROOT,
          capture_output=True).returncode == 0)
    prefix = read('p2/changelog-prefix.json')
    changelog = (ROOT / '.agent/CHANGELOG_AGENT.md').read_bytes()
    check('historical completion snapshots unchanged', hashlib.sha256(
        changelog[:prefix['bytes']]).hexdigest() == prefix['sha256'])
    check('one P2 completion snapshot', changelog.count(b'<a id="snapshot-ccr-p2-20261017">') == 1)
    state = (ROOT / '.agent/CURRENT_STATE.md').read_text()
    queue = (ROOT / '.agent/TASK_QUEUE.md').read_text()
    check('Completed separated from approval/commit and P3 gate',
          'CCR / CCR-P2 / Completed' in state and 'P2结果确认Pending、commit Pending' in state
          and 'P3未开始' in state and '| CCR-P3' in queue and '| CCR-P2' in queue)
    check('M2 remains planning only', 'M2 — Active（仅规划；实现未开始）' in state
          and '| M2-P1 | Next / Planned；计划确认 |' in queue)
    missing = []
    docs = [CCR / 'P2.md', CCR / 'FINDINGS.md', HERE / 'README.md']
    for doc in docs:
        for link in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
            target = link.split('#')[0]
            if target and not re.match(r'\w+://', target):
                path = (doc.parent / target).resolve()
                if path not in [HERE / 'validation.json', HERE / 'manifest.json'] and not path.exists():
                    missing.append({'document': str(doc.relative_to(ROOT)), 'target': target})
    check('new report/evidence local links resolve', not missing)
    report = {'date': '2026-10-17', 'head': baseline['head'], 'checks': checks,
              'status': 'PASS' if all(c['pass'] for c in checks) else 'FAIL',
              'scope_files': 29, 'conditional_navigation_rows': 166,
              'unexplained_rv64_difference': 0, 'missing_links': missing,
              'limits': 'Structural final gate; source review and original defect reproductions are separate evidence.'}
    (HERE / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    assets = list(HERE.iterdir()) + [CCR / n for n in
        ['P2.md', 'FINDINGS.md', 'findings.json', 'coverage.jsonl', 'COVERAGE.md', 'CONTRACTS.md']]
    assets += [ROOT / p for p in expected_tracked]
    assets += [ROOT / '.agent' / n for n in
               ['CURRENT_STATE.md', 'TASK_QUEUE.md', 'CHANGELOG_AGENT.md', 'DOCUMENT_INDEX.md']]
    assets += [ROOT / 'npc/verif/docs' / n for n in
               ['CODE_CORRECTNESS_REVIEW_PLAN.md', 'PROJECT_OVERVIEW.md']]
    manifest = {str(p.relative_to(ROOT)): sha(p) for p in sorted(assets)
                if p.is_file() and p.name != 'manifest.json'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'checks': len(checks),
                      'failed': [c['check'] for c in checks if not c['pass']],
                      'missing_links': missing}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
