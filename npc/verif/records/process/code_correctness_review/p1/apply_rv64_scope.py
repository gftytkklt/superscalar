#!/usr/bin/env python3
"""Apply user-approved S06 to CCR metadata only; never modify production inputs.

Preserves row/config IDs and identity hashes. Non-RV64 implementation obligations
are excluded; mixed files retain RV64/shared obligations without C preprocessing.
"""
from pathlib import Path
import collections
import json
import re

BASE=Path(__file__).resolve().parent.parent
RECEIPT='SCOPE_RV64.md#s06-20261016'
NON_NEMU=['riscv32','riscv32e','mips32','loongarch32r','x86']
NON_AM=['loongarch32r-nemu','mips32-nemu','native','riscv32-nemu','riscv32e-nemu','riscv32e-npc','x86-nemu','x86-qemu','x86_64-qemu']
NON_NAVY=['am_native','loongarch32r','mips32','native','riscv32','riscv32e','x86']
EXCLUDED_CONFIGS=({f'CFG-NEMU-isa-{x}' for x in NON_NEMU}
 | {f'CFG-NEMU-defconfig-{x}-am_defconfig' for x in ('mips32','riscv32')}
 | {f'CFG-AM-{x}' for x in NON_AM}
 | {f'CFG-NAVY-{x}' for x in NON_NAVY}
 | {'CFG-NAVY-option-compiler-rt-32bit','CFG-NAVY-option-native-preload',
    'CFG-MISSING-compiler-rt','CFG-AM-option-smp','CFG-AM-option-__NATIVE_USE_KLIB__',
    'CFG-NEMU-symbol-DIFFTEST_REF_KVM'})
VALUE_CONSTRAINTS={'CFG-NEMU-symbol-RV64':'y','CFG-NEMU-symbol-RVE':'n',
 'CFG-NEMU-symbol-ISA_riscv':'y','CFG-NEMU-symbol-ISA_x86':'n',
 'CFG-NEMU-symbol-ISA_mips32':'n','CFG-NEMU-symbol-ISA_loongarch32r':'n',
 'CFG-NEMU-symbol-ISA':'riscv64','CFG-NEMU-symbol-ISA64':'y'}
EXCLUDED_MODULES={'N04','N05','N06','A08','A09','A10'}

def exclusion_reason(path,module):
    # The physical riscv32 directory is shared by RV64. This override is essential.
    if path.startswith('nemu/src/isa/riscv32/') or path=='nemu/src/isa/riscv64':return None
    if module in EXCLUDED_MODULES:return 'module contains only a non-RV64 target implementation'
    if path.startswith('nemu/tools/kvm-diff/'):return 'KVM x86 guest adapter; not the NEMU host/native output form'
    if path.startswith('nemu/src/isa/') and any('/'+x+'/' in path+'/' for x in ('mips32','loongarch32r','x86')):return 'non-RV64 ISA-specific source/build declaration'
    if path in [f'nemu/configs/{x}-am_defconfig' for x in ('mips32','riscv32')]:return 'non-RV64 defconfig'
    if path.startswith('abstract-machine/am/src/') and any(path.startswith('abstract-machine/am/src/'+x+'/') for x in ('mips','loongarch','x86','native')):return 'non-RV64 AM target port'
    if path in [f'abstract-machine/am/include/arch/{x}.h' for x in ('loongarch32r-nemu','mips32-nemu','native','x86-nemu','x86-qemu','x86_64-qemu')]:return 'non-RV64 AM Context/ABI declaration'
    if path in [f'abstract-machine/scripts/{x}.mk' for x in NON_AM] or path in [f'abstract-machine/scripts/isa/{x}.mk' for x in ('loongarch32r','mips32','x86','x86_64')] or path=='abstract-machine/scripts/platform/qemu.mk':return 'non-RV64 AM build port'
    if path in [f'navy-apps/scripts/{x}.mk' for x in NON_NAVY] or path=='navy-apps/libs/libos/src/native.cpp':return 'non-RV64 Navy target build/runtime'
    if path in [f'navy-apps/libs/libc/src/platform/setjmp/{x}.S' for x in ('amd64','mips32','x86')]:return 'non-RV64 target-specific setjmp assembly'
    if path.startswith('navy-apps/libs/compiler-rt/'):return 'current Navy caller selects compiler-rt only for excluded 32-bit target ISAs'
    if path.startswith('am-kernels/tests/riscv-tests/isa/rv32') or path.startswith('am-kernels/tests/riscv-tests/benchmarks/common/syscalls32'):return 'explicit RV32-only test input'
    return None

def apply():
    if (BASE/'build_profiles.json').exists():
        from finalize_p1_scope import apply as closeout
        return closeout()
    configs=json.loads((BASE/'configs.json').read_text())
    known={c['config_id'] for c in configs}
    assert EXCLUDED_CONFIGS <= known,EXCLUDED_CONFIGS-known
    for c in configs:
        c['scope_approval']=RECEIPT
        c['review_scope']='Excluded' if c['config_id'] in EXCLUDED_CONFIGS else 'RV64OrRequiredSupport'
        c['scope_reason']='S06: non-RV64 target implementation/target-only dependency' if c['review_scope']=='Excluded' else 'S06: RV64 and its required shared code, build, host and interface support only'
        if c['config_id'] in VALUE_CONSTRAINTS:c['review_value_constraint']=VALUE_CONSTRAINTS[c['config_id']]
        c['review_status']='Excluded' if c['review_scope']=='Excluded' else 'Enumerated'
    (BASE/'configs.json').write_text(json.dumps(configs,ensure_ascii=False,indent=2)+'\n')

    counts=collections.Counter();excluded_paths=[];out=BASE/'coverage.s06.tmp'
    with (BASE/'coverage.jsonl').open() as src,out.open('w') as dst:
        for line in src:
            r=json.loads(line);reason=exclusion_reason(r['path'],r['module_id']);excluded=reason is not None
            r['review_config']=[] if excluded else [c for c in r['config'] if c not in EXCLUDED_CONFIGS]
            r['excluded_config']=[c for c in r['config'] if c in EXCLUDED_CONFIGS]
            r['review_scope']='Excluded' if excluded else 'RV64OrRequiredSupport'
            r['review_status']='Excluded' if excluded else 'Enumerated'
            r['scope_reason']=reason or 'Review RV64 and required shared/host behavior only; all other target ISA arms are waived by S06'
            r['effective_phase']=None if excluded else r['phase']
            r['scope_approval']['current_receipt']=RECEIPT
            if 'S06' not in r['scope_approval']['boundaries']:r['scope_approval']['boundaries'].append('S06')
            r['scope_approval']['current_depth']='Identity retained only; no correctness obligation for this non-RV64 implementation' if excluded else 'Original S01-S05 depth intersected with RV64 plus necessary shared/host/interface support'
            r['target_isa_constraint']={'included':['RV64'],'excluded':'all other target ISAs','CONFIG_RV64':True,'CONFIG_RVE':False,'__riscv_xlen':64,'native_semantics':'NEMU host/native retained; AM-native/Navy-native guest implementation excluded'}
            if r['row_kind']=='conditional_path':
                r['scope_branch_selection']='Not evaluated: review only RV64/shared arms; non-RV64 arms excluded. Conditional/MUX/else navigation is not a preprocessing result.'
            r['phase_role']='historical owner only; no current review phase under S06' if excluded else 'current owner under RV64 scope'
            counts[(r['row_kind'],r['review_scope'])]+=1
            if excluded and r['row_kind']=='file':excluded_paths.append({'row_id':r['row_id'],'path':r['path'],'module_id':r['module_id'],'reason':reason})
            dst.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    out.replace(BASE/'coverage.jsonl')

    contracts=json.loads((BASE/'contracts.json').read_text())
    for c in contracts['module_contracts']:
        excluded=bool(set(c['modules'])<=EXCLUDED_MODULES)
        c['review_scope']='Excluded' if excluded else 'RV64OrRequiredSupport'
        c['scope_approval']=RECEIPT
        c['current_scope']='S06 excludes this target implementation; identity/old contract entry retained' if excluded else c['scope']+'；S06仅RV64及必要共享/宿主/接口部分，其他ISA子项不再审阅'
        if excluded:c['status']='ExcludedByScope';c['review_status']='Excluded'
    for c in contracts['official_contracts']:
        excluded=c['contract_id'] in {'C-OFFICIAL-MIPS','C-OFFICIAL-LA32R','C-OFFICIAL-X86'}
        c['review_scope']='Excluded' if excluded else 'RV64OrRequiredSupport'
        c['scope_approval']=RECEIPT
        if excluded:c['status']='NotApplicable/ScopeExcluded'
    for c in contracts['contract_questions']:
        q=c['question_id'];c['scope_approval']=RECEIPT
        if q in ('CQ-003','CQ-004'):
            c['status']='NotApplicable/ScopeExcluded';c['resolution']='S06 explicitly excludes MIPS/LoongArch implementation obligations; no ISA version decision needed for this CCR.'
        else:
            c['current_scope_note']={
                'CQ-001':'Only RV64/shared course and approved simplifications; non-RV64 teaching ports excluded.',
                'CQ-002':'RV64 ISA/privileged/EEI/LP64 remain Pending; RV32/RVE/ILP32E obligations excluded.',
                'CQ-005':'Guest x86/x86_64/AM-native contracts and missing NEMU x86 are excluded; only ABI/tool dependencies actually required by RV64 host validation remain Pending.',
                'CQ-010':'compiler-rt is selected only by excluded 32-bit Navy targets and is not an RV64 blocker; fceux/oslab0 and relevant source provenance remain Pending.',
                'CQ-014':'MIPS/LA32R document access is no longer a blocker; required ELF/POSIX and other RV64 sources remain Pending.'
            }.get(q,'Only RV64 plus its necessary shared/host/interface support; unresolved non-ISA obligations remain Pending.')
    contracts['current_scope_approval']=RECEIPT
    (BASE/'contracts.json').write_text(json.dumps(contracts,ensure_ascii=False,indent=2)+'\n')
    stats={'scope_id':'S06','date':'2026-10-16','receipt':RECEIPT,'coverage_counts':{k+':'+v:n for (k,v),n in sorted(counts.items())},'excluded_configs':sorted(EXCLUDED_CONFIGS),'retained_config_count':len(configs)-len(EXCLUDED_CONFIGS),'excluded_modules':sorted(EXCLUDED_MODULES),'excluded_file_rows':excluded_paths,'active_contract_questions':12,'out_of_scope_contract_questions':['CQ-003','CQ-004'],'reviewed_rows':0,'confirmed_findings':0,'source_changes':0,'scope_model':'Physical identity and lexical branches retained. Scope is a projection to RV64; no claim of compiler branch evaluation or legal combination proof.'}
    (BASE/'p1/scope-s06/result.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in stats.items() if k not in ('excluded_file_rows','excluded_configs')},ensure_ascii=False,indent=2))

if __name__=='__main__':apply()
