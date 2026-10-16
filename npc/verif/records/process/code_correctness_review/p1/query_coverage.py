#!/usr/bin/env python3
"""Read-only reverse lookup in CCR-P1's frozen coverage matrix."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--path', help='exact workspace-relative path')
parser.add_argument('--module', help='module ID such as N03')
parser.add_argument('--config', help='config ID such as CFG-NEMU-isa-riscv32e')
parser.add_argument('--branches', action='store_true', help='include condition navigation rows')
parser.add_argument('--profile', help='selected build profile ID, e.g. CCR-AM-NPC')
args = parser.parse_args()
if not any((args.path, args.module, args.config, args.profile)):
    parser.error('provide --path, --module, --config or --profile')
coverage = Path(__file__).resolve().parent.parent / 'coverage.jsonl'
count = 0
for line in coverage.open():
    row = json.loads(line)
    if not args.branches and row['row_kind'] != 'file':
        continue
    if args.path and row['path'] != args.path:
        continue
    if args.module and row['module_id'] != args.module:
        continue
    if args.config and args.config not in row['config']:
        continue
    if args.profile and args.profile not in row.get('review_profiles', []):
        continue
    keys = ('row_id','module_id','path','canonical_path','function_or_path','line_range',
            'source_sha256','hash_semantics','config','active_or_dormant',
            'expected_contract','contract_source','phase','phase_responsibilities',
            'review_status','source_status','scope_approval','condition_evaluation',
            'review_scope','scope_reason','review_config','excluded_config',
            'effective_phase','target_isa_constraint','scope_branch_selection',
            'effective_phase_responsibilities','review_profiles','build_profile_source')
    print(json.dumps({key:row[key] for key in keys if key in row},ensure_ascii=False,indent=2))
    count += 1
if not count:
    raise SystemExit('No matching frozen rows; this is not permission to omit a new file/config.')
