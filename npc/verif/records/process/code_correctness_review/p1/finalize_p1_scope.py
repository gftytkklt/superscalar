#!/usr/bin/env python3
"""Apply the approved RV64 dual-platform scope to CCR metadata only.

Keeps physical identities and historical candidate config IDs. Does not evaluate
Makefiles, rebuild inventories, inspect implementation correctness or run guests.
"""
from pathlib import Path
import collections
import hashlib
import json
import re
from apply_rv64_scope import (EXCLUDED_CONFIGS as S06_EXCLUDED, EXCLUDED_MODULES,
                              NON_AM, NON_NAVY, VALUE_CONSTRAINTS, exclusion_reason)

BASE = Path(__file__).resolve().parent.parent
ROOT = BASE.parents[4]
OUT = BASE / 'p1/final-closeout'
RECEIPT = 'SCOPE_RV64.md#s06-clarification-20261017'
EXCLUDED_CONFIGS = S06_EXCLUDED | {'CFG-AM-spike', 'CFG-AM-spike-linker'}
TARGETS = sorted(set(NON_AM + NON_NAVY + ['x86_64']), key=len, reverse=True)
BUILD_ROOTS = ('abstract-machine/', 'am-kernels/', 'nanos-lite/',
               'navy-apps/', 'rt/bsp/abstract-machine/')
TARGET_RE = '|'.join(re.escape(t) for t in TARGETS)
OLD_DIR = re.compile(r'/build/(' + TARGET_RE + r')/')
OLD_NAMED = re.compile(r'/build/[^/]+-(' + TARGET_RE + r')(?:\.(?:a|elf|bin|txt|so|d|o))?$')
SPIKE_AM = 'abstract-machine/am/src/riscv/spike/'
DUMMY = 'abstract-machine/am/src/platform/dummy/'
PROFILES = {'nemu': 'CCR-AM-NEMU', 'npc': 'CCR-AM-NPC'}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def old_target_artifact(path):
    return (path.startswith(BUILD_ROOTS) and
            (OLD_DIR.search(path) or OLD_NAMED.search(path) or
             path == 'navy-apps/libs/libos/build/native.so'))


def current_exclusion(path, module):
    if old_target_artifact(path):
        return 'S06: non-RV64 target build artifact; retain S03 historical identity only'
    if path.startswith(SPIKE_AM) or path == 'abstract-machine/scripts/spike.mk':
        return '2026-10-17: standalone AM Spike target is not either selected AM/OS platform; NEMU Spike golden integration is separate'
    if path in {DUMMY + x + '.c' for x in ('cte', 'ioe', 'trm')}:
        return '2026-10-17: this dummy API is not selected by riscv64-nemu or riscv64-npc; NPC dummy VME/MPE remain in scope'
    return exclusion_reason(path, module)


def profiles_for(path, module, configs):
    if path.startswith('nemu/tools/spike-diff/'):
        return ['CCR-NEMU-SPIKE']
    if path.startswith('nemu/'):
        return ['CCR-NEMU-NATIVE', 'CCR-NEMU-SPIKE', 'CCR-NPC-NEMU-REF']
    if path.startswith('navy-apps/') or module.startswith('U'):
        return ['CCR-NAVY-RV64']
    if path in {DUMMY + 'vme.c', DUMMY + 'mpe.c'}:
        return ['CCR-AM-NPC']
    if module.startswith('A') or module.startswith('O') or path.startswith(BUILD_ROOTS):
        selected = [p for arch, p in PROFILES.items() if 'CFG-AM-riscv64-' + arch in configs]
        return selected or ['CCR-AM-NEMU', 'CCR-AM-NPC']
    if module == 'X02':
        return ['CCR-NPC-NEMU-REF', 'CCR-AM-NPC']
    if module == 'X03':
        return ['CCR-NEMU-NATIVE']
    return ['CCR-AM-NEMU', 'CCR-AM-NPC', 'CCR-NEMU-NATIVE']


def apply():
    assert (BASE / 'build_profiles.json').is_file(), 'Freeze selected build profiles first'
    configs = json.loads((BASE / 'configs.json').read_text())
    assert EXCLUDED_CONFIGS <= {c['config_id'] for c in configs}
    selected = {'CFG-NEMU-current', 'CFG-NEMU-isa-riscv64', 'CFG-NEMU-target-native-elf',
                'CFG-AM-riscv64-nemu', 'CFG-AM-riscv64-npc', 'CFG-NAVY-riscv64'}
    for c in configs:
        cid = c['config_id']; excluded = cid in EXCLUDED_CONFIGS
        c.update(scope_approval=RECEIPT,
                 review_scope='Excluded' if excluded else 'RV64OrRequiredSupport',
                 review_status='Excluded' if excluded else 'Enumerated',
                 review_selection='out_of_scope' if excluded else
                     ('selected_for_review' if cid in selected else 'conditional_factor_or_support'),
                 effective_phase=[] if excluded else c['phase'])
        c['scope_reason'] = ('Non-RV64 or standalone AM Spike target; identity retained only' if excluded else
                            'Selected RV64 NEMU/NPC software stack or its conditional implementation/support')
        c['selection_evidence'] = RECEIPT + '; BUILD_PATHS.md / build_profiles.json'
        c['current_source_paths'] = [p for p in c['source_paths'] if not current_exclusion(p, '')]
        if cid == 'CFG-AM-riscv64-nemu':
            c['review_profiles'] = ['CCR-AM-NEMU']
        elif cid == 'CFG-AM-riscv64-npc' or cid == 'CFG-AM-dummy-runtime':
            c['review_profiles'] = ['CCR-AM-NPC']
        elif cid.startswith('CFG-AM-') or cid.startswith('CFG-NANOS-'):
            c['review_profiles'] = ['CCR-AM-NEMU', 'CCR-AM-NPC']
        elif cid.startswith('CFG-NAVY-') or cid.startswith('CFG-MISSING-'):
            c['review_profiles'] = ['CCR-NAVY-RV64']
        else:
            c['review_profiles'] = ['CCR-NEMU-NATIVE', 'CCR-NEMU-SPIKE', 'CCR-NPC-NEMU-REF']
        if excluded:
            c['review_profiles'] = []
        c['observed_state_note'] = 'status/selectors retain frozen observations; review selection is not proof of current binary or successful execution'
        if cid in VALUE_CONSTRAINTS:
            c['review_value_constraint'] = VALUE_CONSTRAINTS[cid]
    dump(BASE / 'configs.json', configs)

    counts = collections.Counter(); excluded_files = []; corrected_artifacts = []
    module_counts = collections.defaultdict(collections.Counter)
    temp = BASE / 'coverage.closeout.tmp'
    with (BASE / 'coverage.jsonl').open() as src, temp.open('w') as dst:
        for line in src:
            r = json.loads(line); path = r['path']; module = r['module_id']
            reason = current_exclusion(path, module); excluded = reason is not None
            rc = [] if excluded else [c for c in r['config'] if c not in EXCLUDED_CONFIGS]
            # Artifact target selection follows the producing target, not a shared source's candidate domain.
            for arch in ('nemu', 'npc'):
                if re.search(r'/build/(?:riscv64-' + arch + r'/|[^/]+-riscv64-' + arch + r'(?:\.|$))', path):
                    rc = [c for c in rc if not c.startswith('CFG-AM-riscv64-') or c == 'CFG-AM-riscv64-' + arch]
            if path in {DUMMY + 'vme.c', DUMMY + 'mpe.c'}:
                rc = [c for c in rc if not c.startswith('CFG-AM-riscv64-') or c == 'CFG-AM-riscv64-npc']
            assert excluded or rc, ('Included row has no current config', path)
            r.update(review_config=rc,
                     excluded_config=[c for c in r['config'] if c in EXCLUDED_CONFIGS],
                     review_scope='Excluded' if excluded else 'RV64OrRequiredSupport',
                     review_status='Excluded' if excluded else 'Enumerated',
                     effective_phase=None if excluded else r['phase'],
                     scope_reason=reason or 'Selected RV64 NEMU/NPC software/OS interaction or required host/REF support; S01-S05 depth retained',
                     phase_role='historical owner only; no current review obligation' if excluded else 'current RV64 owner',
                     review_profiles=[] if excluded else profiles_for(path, module, rc),
                     build_profile_source='BUILD_PATHS.md / build_profiles.json',
                     profile_relation='static applicability to selected review scenarios; not preprocessing or proof of binary provenance')
            r['contract_source'] = 'CONTRACTS.md#current-' + r['expected_contract'].lower()
            r['effective_phase_responsibilities'] = {} if excluded else dict(r['phase_responsibilities'])
            if path in {DUMMY + 'vme.c', DUMMY + 'mpe.c'}:
                r['effective_phase_responsibilities'] = {'CCR-P4': 'NPC selected dummy VME/MPE API contract and OS interaction; no automatic teaching waiver'}
            r['scope_approval']['current_receipt'] = RECEIPT
            r['scope_approval']['current_depth'] = 'Historical identity only; outside current review denominator' if excluded else 'S01-S05 intersected with selected RV64 NEMU/NPC stack and golden/REF interfaces'
            if 'S06' not in r['scope_approval']['boundaries']:
                r['scope_approval']['boundaries'].append('S06')
            r['target_isa_constraint'] = {'included': ['RV64'], 'excluded': 'all other target ISAs',
                'CONFIG_RV64': True, 'CONFIG_RVE': False, '__riscv_xlen': 64,
                'native_semantics': 'NEMU host/native retained; AM-native/Navy-native target implementations excluded'}
            if r['row_kind'] == 'conditional_path':
                r['scope_branch_selection'] = 'Not evaluated: only RV64/shared arms in selected profiles; lexical conditions/else/endif are navigation, not reviewed paths'
            if r['row_kind'] == 'file':
                module_counts[module][r['review_status']] += 1
                if excluded:
                    excluded_files.append({'row_id': r['row_id'], 'path': path, 'reason': reason})
                if old_target_artifact(path):
                    corrected_artifacts.append(path)
            counts[r['row_kind'] + ':' + r['review_status']] += 1
            dst.write(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n')
    temp.replace(BASE / 'coverage.jsonl')

    contracts = json.loads((BASE / 'contracts.json').read_text())
    for c in contracts['module_contracts']:
        excluded = set(c['modules']) <= EXCLUDED_MODULES
        c.update(scope_approval=RECEIPT, review_scope='Excluded' if excluded else 'RV64OrRequiredSupport',
                 review_status='Excluded' if excluded else 'Enumerated',
                 effective_phase=[] if excluded else c['phase'])
        c['current_scope'] = 'Outside approved RV64 scope; historical source entry only' if excluded else 'RV64 NEMU/NPC software stack and necessary host/OS interfaces; S01-S05 depth. Historical scope text is filtered by coverage.review_config/review_profiles.'
        c['current_source_paths'] = [p for p in c['source_paths'] if not current_exclusion(p, c['modules'][0])]
        if c['contract_id'] == 'C-A11':
            c['current_scope'] = 'Only NPC-selected dummy VME/MPE API and OS interactions; standalone AM Spike and unused dummy APIs excluded. No correctness or approved teaching-gap inference.'
            c['effective_phase'] = ['CCR-P4']
        if c['contract_id'] in ('C-N11', 'C-N14'):
            c['current_scope'] += ' Spike is NEMU DUT golden model: version/provenance/local changes/adapter/ABI under S01; no core modification authorized.'
    for c in contracts['official_contracts']:
        c['scope_approval'] = RECEIPT
        excluded = c['contract_id'] in {'C-OFFICIAL-MIPS', 'C-OFFICIAL-LA32R', 'C-OFFICIAL-X86'}
        c['review_scope'] = 'Excluded' if excluded else 'RV64OrRequiredSupport'
        if excluded:
            c['status'] = 'NotApplicable/ScopeExcluded'
    for c in contracts['contract_questions']:
        c['scope_approval'] = RECEIPT
        c['p1_or_p2_entry_blocker'] = False
        c['gate_reason'] = 'Resolve before a conclusion depending on unsettled semantics; no blanket entry veto and no new interpretation approved here'
        if c['question_id'] in ('CQ-003', 'CQ-004'):
            c['status'] = 'NotApplicable/ScopeExcluded'
        if c['question_id'] == 'CQ-010':
            c['current_scope_note'] = 'Spike golden core follows S01; provenance/local differences and actual interface preserved, no automatic pristine-upstream assertion. fceux/oslab0 OS wrappers follow S02/S05 in P8; not P2 blockers. 32-bit compiler-rt excluded.'
    contracts['current_scope_approval'] = RECEIPT
    for c in contracts['project_contracts']:
        if c['contract_id'] == 'C-PROJ-CCR':
            c['version'] = 'v0.3: S06 RV64 plus 2026-10-17 dual-platform/Spike role clarification'
            c['scope'] = 'RV64 NEMU重点；AM/OS=NEMU+NPC；Spike=NEMU DUT golden；S01-S05不变'
            for s in c['sources']:
                if s['path'] == 'npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md':
                    data = (ROOT / s['path']).read_bytes()
                    s.setdefault('pre_closeout_source_sha256', s['source_sha256'])
                    s['source_sha256'] = hashlib.sha256(data).hexdigest()
                    s['line_count'] = len(data.splitlines())
                    s['refresh_reason'] = '2026-10-17 approved dual-platform scope; previous plan archived in p1/final-closeout/original'
    dump(BASE / 'contracts.json', contracts)
    result = {'date': '2026-10-17', 'receipt': RECEIPT, 'coverage_counts': dict(counts),
        'module_file_counts': dict(module_counts), 'excluded_configs': sorted(EXCLUDED_CONFIGS),
        'retained_config_count': len(configs) - len(EXCLUDED_CONFIGS),
        'corrected_other_target_artifact_count': len(corrected_artifacts),
        'corrected_other_target_artifacts': corrected_artifacts, 'excluded_files': excluded_files,
        'reviewed_rows': 0, 'confirmed_findings': 0, 'production_edits': 0}
    dump(OUT / 'result.json', result)
    print(json.dumps({k: result[k] for k in ('coverage_counts', 'retained_config_count',
        'corrected_other_target_artifact_count', 'reviewed_rows', 'production_edits')}, ensure_ascii=False))


if __name__ == '__main__':
    apply()
