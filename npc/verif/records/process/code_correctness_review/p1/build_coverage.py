#!/usr/bin/env python3
"""CCR-P1: join frozen identities/configs to explicit file and condition rows.

No build, source modification or semantic correctness judgement. Run from workspace.
Outputs are review records only. P1 rows remain Enumerated even for S01-S05 boundaries.
"""
import collections
import hashlib
import json
import re
from pathlib import Path

BASE = Path('npc/verif/records/process/code_correctness_review')
APPROVAL = 'CODE_CORRECTNESS_REVIEW_PLANNING.md#ccr-p0-approval-20261016'

def read_jsonl(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]

def module_for(path):
    p = path
    name = Path(p).name
    if p.startswith('nemu/'):
        q = p[5:]
        if q.startswith('src/isa/x86'): return 'N06'
        if name == 'filelist.mk' or name == 'Kconfig' or q in ('Makefile', '.config', '.config.old') or q.startswith(('configs/', 'scripts/')): return 'N01'
        if q.startswith(('build/', '.metals/', '.vscode/', 'include/config/', 'include/generated/', 'tools/kconfig/', 'tools/fixdep/', 'tools/spike-diff/repo/')) or q in ('LICENSE', 'README.md', '.gitignore', 'dtrace.txt', 'itrace.txt'): return 'N14'
        if q.startswith('src/isa/riscv'): return 'N03'
        if q.startswith('src/isa/mips32/'): return 'N04'
        if q.startswith('src/isa/loongarch32r/'): return 'N05'
        if q.startswith(('src/memory/', 'include/memory/')): return 'N07'
        if q.startswith(('src/cpu/difftest/', 'tools/spike-diff/', 'tools/qemu-diff/', 'tools/kvm-diff/')) or q in ('include/difftest-def.h', 'include/cpu/difftest.h', 'tools/difftest.mk'): return 'N11'
        if q.startswith(('src/monitor/',)): return 'N10'
        if q.startswith('src/device/'):
            return 'N09' if name in ('serial.c', 'timer.c', 'mtimer.c', 'keyboard.c', 'vga.c', 'audio.c', 'disk.c', 'sdcard.c', 'mmc.h') else 'N08'
        if q.startswith('include/device/'): return 'N08'
        if q.startswith(('tests/', 'resource/')): return 'N13'
        if q.startswith(('src/engine/', 'src/cpu/', 'include/cpu/')) or q in ('src/nemu-main.c', 'src/am-bin.S'): return 'N02'
        if q.startswith(('include/', 'src/utils/', 'tools/gen-expr/')): return 'N12'
        raise ValueError(('unmapped NEMU', p))
    if p.startswith('abstract-machine/'):
        q = p[len('abstract-machine/'):]
        if '/build/' in p or q in ('README', 'LICENSE', '.gitignore'): return 'A14'
        if q.startswith('klib/'): return 'A12'
        if q.startswith(('scripts/', 'tools/')) or q in ('Makefile', 'am/Makefile'): return 'A01'
        if q.startswith('am/include/') or q in ('am/src/riscv/riscv.h', 'am/src/mips/mips32.h', 'am/src/loongarch/loongarch32r.h', 'am/src/x86/x86.h'): return 'A02'
        if q.startswith('am/src/riscv/nemu/'): return 'A03'
        if q.startswith('am/src/riscv/npc/libgcc/'): return 'A06'
        if q.startswith('am/src/riscv/npc/'):
            return 'A05' if name in ('ioe.c', 'input.c', 'video.c', 'timer.c') else 'A04'
        if q.startswith('am/src/platform/nemu/'): return 'A07'
        if q.startswith('am/src/native/'): return 'A08'
        if re.match(r'am/src/(mips|loongarch|x86)/nemu/', q): return 'A09'
        if q.startswith('am/src/x86/qemu/'): return 'A10'
        if q.startswith(('am/src/riscv/spike/', 'am/src/platform/dummy/')): return 'A11'
        raise ValueError(('unmapped AM', p))
    if p.startswith('nanos-lite/'):
        if name in ('loader.c', 'mm.c'): return 'O02'
        if name in ('irq.c', 'proc.c'): return 'O03'
        if name in ('syscall.c', 'syscall.h'): return 'O04'
        if name in ('fs.c', 'disk.c', 'files.h', 'ramdisk.img'): return 'O05'
        if name in ('device.c', 'resources.S', 'logo.txt'): return 'O06'
        return 'O01'
    if p.startswith('navy-apps/'):
        q = p[10:]
        if q.startswith(('build/', 'fsimg/')) or '/build/' in q or '/resources/' in q or q in ('README.md', '.gitignore') or q.startswith('.vscode/'): return 'U14'
        if q == 'Makefile' or q.startswith('scripts/') or (name.startswith('Makefile') and '/repo/' not in p): return 'U01'
        libs = {'libos':'U02', 'libc':'U03', 'compiler-rt':'U03', 'libam':'U04', 'libndl':'U05', 'libminiSDL':'U06', 'libSDL_image':'U07', 'libSDL_mixer':'U07', 'libSDL_ttf':'U07', 'libbdf':'U07', 'libbmp':'U07', 'libvorbis':'U07', 'libfixedptc':'U08'}
        apps = {'nterm':'U09', 'menu':'U09', 'nwm':'U09', 'nplayer':'U09', 'nslider':'U09', 'nanos-lite-guest':'U10', 'am-kernels':'U11', 'fceux':'U11', 'oslab0':'U11', 'bird':'U12', 'busybox':'U12', 'lua':'U12', 'onscripter':'U12', 'pal':'U12'}
        parts = q.split('/')
        if parts[0] == 'libs' and parts[1] in libs: return libs[parts[1]]
        if parts[0] == 'apps' and parts[1] in apps: return apps[parts[1]]
        if parts[0] == 'tests': return 'U13'
        raise ValueError(('unmapped navy', p))
    if p.startswith(('am-kernels/', 'rt/bsp/abstract-machine/')): return 'A13'
    if p == 'fceux' or p.startswith('fceux/'): return 'U11'
    if p.startswith('fceux-am/'): return 'X04'
    if p.startswith(('npc/verif/linux/', 'npc/verif/tests/', 'npc/verif/scripts/')): return 'X03'
    if p.startswith(('npc/csrc/', 'npc/vsrc/', 'npc/ysyxSoC/')) or p in ('npc/.npc_config', '.npc_config', 'npc/Makefile'): return 'X02'
    if p.startswith('npc/verif/') or p.startswith('.agent/'): return 'X03'
    if '/' not in p or p.endswith(('/.gitignore', '/README.md', '/README')): return 'X01'
    raise ValueError(('unmapped support', p))

def phase_for(module, path):
    if module in ('N02', 'N03', 'N04', 'N05', 'N07'): return 'CCR-P2'
    if module == 'N12': return 'CCR-P2' if '/include/' in path or path.endswith('/state.c') else 'CCR-P3'
    if module.startswith('N'): return 'CCR-P3'
    if module in ('A01', 'A03', 'A04', 'A09'): return 'CCR-P4'
    if module == 'A02': return 'CCR-P5' if path.endswith('/amdev.h') else 'CCR-P4'
    if module in ('A07', 'A08', 'A10', 'A11'):
        return 'CCR-P5' if '/ioe/' in path or Path(path).name in ('ioe.c', 'timer.c', 'htif.c', 'htif.h') else 'CCR-P4'
    if module == 'A14': return 'CCR-P4'
    if module.startswith('A'): return 'CCR-P5'
    if module.startswith('O'): return 'CCR-P6'
    if module in ('U01','U02','U03','U04','U14'): return 'CCR-P7'
    if module == 'U13': return 'CCR-P8' if any('/'+n+'/' in path for n in ('audiotest','bmp-test','event-test','timer-test')) else 'CCR-P7'
    if module.startswith('U'): return 'CCR-P8'
    return {'X01':'CCR-P1','X02':'CCR-P3','X03':'CCR-P9','X04':'CCR-P5'}[module]

def kind_for(item, module):
    p = item['path']; name = Path(p).name
    if item['entry_type'] in ('missing_dependency','deleted_tracked'): return 'missing_source_or_dependency'
    if '/.git/' in p or p.endswith('/.git'): return 'git_metadata'
    if item['entry_type'] == 'directory_alias': return 'directory_alias'
    if item['entry_type'].startswith('symlink'): return 'symlink_binding'
    if '/build/' in p or '/__pycache__/' in p or '/include/generated/' in p or '/include/config/' in p or name.endswith(('.o','.a','.so','.d','.pyc','.log','.elf','.bin','.img','.db','.mv.db')): return 'generated_or_build_artifact'
    if '/fsimg/' in p or '/.vscode/' in p or '/.metals/' in p or name.endswith(('.png','.jpg','.bmp','.wav','.ogg','.mp3','.ttf','.bdf','.nes','.nsa','.gif','.pal','.dat')): return 'resource_or_editor_data'
    if item.get('text_encoding') is None and item.get('size_bytes',0): return 'binary_asset_provenance_pending'
    if name in ('LICENSE','COPYING','README','README.md') or name.endswith(('.md','.rst','.txt','.tex')): return 'documentation_or_resource'
    if '/platform/dummy/' in p: return 'placeholder_port'
    if module in ('U03','U07','U08','U12') or '/repo/' in p or '/tools/kconfig/' in p or '/tools/fixdep/' in p or module == 'A06': return 'upstream_or_mixed_source'
    if name.startswith(('Makefile','Kconfig','SConstruct','SConscript')) or name.endswith(('.mk','.ld','.sh','.py','defconfig')) or name in ('.config','.config.old','.npc_config','.gitignore'): return 'build_configuration_or_tool'
    return 'implementation_or_header'

def configs_for(path, module, configs):
    ids = [c['config_id'] for c in configs]
    am_arch = ['CFG-AM-'+a for a in ('loongarch32r-nemu','mips32-nemu','riscv32-nemu','riscv32e-nemu','riscv64-nemu','riscv32e-npc','riscv64-npc','x86-nemu','x86-qemu','x86_64-qemu','native','spike')]
    # Sets are symbolic applicability domains, NOT a claim that all cross-products build.
    if module.startswith('N'):
        if path == 'nemu/src/isa/riscv64': prefix = ['CFG-NEMU-isa-riscv64']
        elif '/isa/riscv' in path: prefix = ['CFG-NEMU-isa-riscv64','CFG-NEMU-isa-riscv32','CFG-NEMU-isa-riscv32e']
        elif '/isa/mips32/' in path: prefix = ['CFG-NEMU-isa-mips32']
        elif '/isa/loongarch32r/' in path: prefix = ['CFG-NEMU-isa-loongarch32r']
        elif '/isa/x86' in path: prefix = ['CFG-NEMU-isa-x86']
        else: prefix = [i for i in ids if i.startswith('CFG-NEMU-isa-')]
        if path == 'nemu/.config' or path.startswith(('nemu/include/generated/','nemu/include/config/')): prefix = ['CFG-NEMU-current']
    elif module.startswith('A'):
        prefix = am_arch
        if '/riscv/npc/' in path: prefix = [i for i in prefix if i.endswith('-npc')]
        elif '/riscv/nemu/' in path: prefix = [i for i in prefix if 'riscv' in i and i.endswith('-nemu')]
        elif '/platform/nemu/' in path: prefix = [i for i in prefix if i.endswith('-nemu')]
        elif '/native/' in path: prefix = ['CFG-AM-native']
        elif '/x86/qemu/' in path: prefix = ['CFG-AM-x86-qemu','CFG-AM-x86_64-qemu']
        elif '/x86/nemu/' in path: prefix = ['CFG-AM-x86-nemu']
        elif '/mips/nemu/' in path: prefix = ['CFG-AM-mips32-nemu']
        elif '/loongarch/nemu/' in path: prefix = ['CFG-AM-loongarch32r-nemu']
        elif '/riscv/spike/' in path: prefix = ['CFG-AM-spike']
        elif '/am/include/arch/riscv.h' in path or path.endswith('/riscv/riscv.h'): prefix = [i for i in am_arch if 'riscv' in i or i.endswith('-spike')]
        elif '/am/include/arch/' in path and 'CFG-AM-'+Path(path).stem in ids: prefix = ['CFG-AM-'+Path(path).stem]
        elif path.endswith('/mips/mips32.h'): prefix = ['CFG-AM-mips32-nemu']
        elif path.endswith('/loongarch/loongarch32r.h'): prefix = ['CFG-AM-loongarch32r-nemu']
        elif path.endswith('/x86/x86.h'): prefix = [i for i in am_arch if '-x86' in i]
        elif '/scripts/platform/' in path: prefix = [i for i in am_arch if i.endswith('-'+Path(path).stem)]
        elif '/scripts/isa/' in path:
            stem=Path(path).stem
            prefix = [i for i in am_arch if ('riscv' in i or i.endswith('-spike'))] if stem=='riscv' else ['CFG-AM-x86_64-qemu'] if stem=='x86_64' else ['CFG-AM-x86-nemu','CFG-AM-x86-qemu'] if stem=='x86' else [i for i in am_arch if i=='CFG-AM-'+stem+'-nemu']
        elif Path(path).name.endswith('.mk') and 'CFG-AM-'+Path(path).stem in ids: prefix = ['CFG-AM-'+Path(path).stem]
    elif module.startswith('O'): prefix = [i for i in ids if i.startswith('CFG-NANOS-')] + am_arch
    elif module.startswith('U'):
        prefix = [i for i in ids if i.startswith('CFG-NAVY-')]
        if path.startswith('navy-apps/scripts/'):
            if path.endswith('/riscv/common.mk'): prefix=['CFG-NAVY-riscv32','CFG-NAVY-riscv32e','CFG-NAVY-riscv64']
            elif 'CFG-NAVY-'+Path(path).stem in ids: prefix=['CFG-NAVY-'+Path(path).stem]
    elif module == 'X02': prefix = [i for i in ids if i.startswith('CFG-NEMU-defconfig-riscv64-ref') or i in ('CFG-AM-riscv64-npc','CFG-AM-riscv32e-npc')]
    elif module == 'X03': prefix = [i for i in ids if i in ('CFG-NEMU-current','CFG-NEMU-isa-riscv64','CFG-NEMU-target-native-elf','CFG-NEMU-runtime-linux-kernel-dtb','CFG-NEMU-timer-mtimer','CFG-SUPPORT-LINUX-native')]
    elif module == 'X01': prefix = ids
    else: prefix = am_arch
    direct = [c['config_id'] for c in configs if path in c.get('source_paths', [])]
    return sorted(set(i for i in prefix+direct if i in ids))

def handoffs(module, path):
    table={
        'N01': {'CCR-P2':'消费ISA/位宽/内存选择契约；不重复P3构建审阅','CCR-P3':'配置求值、生成及构建副作用','CCR-P9':'配置到实际产物L09'},
        'N02': {'CCR-P2':'执行状态/PC/译码入口','CCR-P3':'native/AM装载补链','CCR-P9':'L01/L07/L09双端'},
        'N03': {'CCR-P2':'ISA/异常/特权/翻译主体','CCR-P3':'difftest调用/传输补链','CCR-P9':'L01/L07/L08'},
        'N04': {'CCR-P2':'未启用ISA实现及占位承诺','CCR-P3':'difftest接入补链'},
        'N05': {'CCR-P2':'未启用ISA实现及占位承诺','CCR-P3':'difftest接入补链'},
        'N12': {'CCR-P2':'公共类型/位宽/执行状态','CCR-P3':'日志/时间/反汇编/表达式工具'},
        'N13': {'CCR-P2':'作为ISA验证输入，执行前必须审核所需oracle','CCR-P3':'测试/资源/集成驱动正式审阅'},
        'A02': {'CCR-P4':'Context及C/汇编ABI、TRM/CTE/VME/MPE','CCR-P5':'IOE与公共运行时API','CCR-P9':'跨层结构/字段'},
        'A07': {'CCR-P4':'TRM/MPE及平台地址声明','CCR-P5':'IOE分发表及各设备','CCR-P9':'NEMU设备双端'},
        'A08': {'CCR-P4':'host启动/context/VME/MPE','CCR-P5':'host IOE及资源生命周期'},
        'A10': {'CCR-P4':'QEMU启动/分页/上下文/SMP','CCR-P5':'QEMU设备IOE'},
        'A11': {'CCR-P4':'Spike启动/HTIF声明及dummy context边界','CCR-P5':'HTIF/时钟/IOE与dummy API承诺'},
        'A14': {'CCR-P4':'启动/链接产物与配置来源','CCR-P5':'运行时/klib产物ABI来源','CCR-P9':'实际装载匹配'},
        'U14': {'CCR-P7':'fsimg/ramdisk/生成表生产及构建来源','CCR-P8':'资源格式/尺寸与服务/应用消费','CCR-P9':'文件表/镜像/链接一致性'},
        'X01': {'CCR-P1':'初始化/提交/生成副作用及身份导航','CCR-P3':'仅随N01/N11审实际构建接入调用链'},
        'X02': {'CCR-P3':'REF加载/方向/内存注册契约','CCR-P4':'AM-NPC启动/设备/链接布局接口','CCR-P9':'L08实际双方配对'},
        'X03': {'CCR-P3':'仅NEMU平台配置及验证基础设施入口','CCR-P9':'Linux native及跨层验证输入；不审外部OS内部'},
    }
    return table.get(module,{phase_for(module,path):'按C-'+module+'及批准模块目标审本行范围'})

def main():
    inv = read_jsonl(BASE/'inventory.jsonl')
    configs = json.loads((BASE/'configs.json').read_text())
    statuses = {c['config_id']:c['status'] for c in configs}
    branch_file = BASE/'branches.jsonl'
    branches = read_jsonl(branch_file) if branch_file.exists() else []
    bypath = collections.defaultdict(list)
    for b in branches: bypath[b['path']].append(b)
    placeholders=collections.defaultdict(list)
    if (BASE/'p1/placeholder-candidates.jsonl').exists():
        for marker in read_jsonl(BASE/'p1/placeholder-candidates.jsonl'): placeholders[marker['path']].append(marker)
    rows=[]; modules=collections.Counter(); kinds=collections.Counter()
    for item in inv:
        p=item['path']; m=module_for(p); kind=kind_for(item,m); cfg=configs_for(p,m,configs)
        if not cfg: raise ValueError(('no config domain',p))
        scope=['v0.1-full-file-enumeration']
        depth='全部自有实现/头/构建路径；后续阶段逐函数核对，P1仅枚举'
        if kind in ('git_metadata','generated_or_build_artifact','resource_or_editor_data','documentation_or_resource','directory_alias','symlink_binding','binary_asset_provenance_pending'):
            scope+=['S03'];depth='身份/来源/生成或消费链、参数/哈希与相关ABI；不逐行审机器码/资源/元数据'
        elif kind == 'upstream_or_mixed_source':
            scope+=['S01'];depth='来源、本地相关修改、构建/ABI/适配及运行时关联闭包；未证明无关的内容保持待核，不整库排除'
        if m in ('U07','U08','U12','A13','X04'):
            scope+=['S02'];depth+='；业务算法边界在所属阶段按S02核实，不预先排除未读函数'
        if m.startswith('X') or p.startswith('rt/'):
            scope+=['S04'];depth+='；仅直接接口/接入/验证契约，不展开完整外部OS/RTL'
        if kind=='missing_source_or_dependency': scope+=['S05'];depth='保留缺源身份及恢复条件；不得计入静态已审'
        limits=['P1仅身份/范围枚举；未执行正确性审阅或动态验证','配置集合是候选适用域；条件表达式见branches.jsonl，合法组合/实际编译选入待所属阶段核对']
        if kind=='upstream_or_mixed_source': limits.append('本地差异见inventory provenance；HEAD相同不等于上游无改；不以来源不明作排除依据')
        if kind=='placeholder_port': limits.append('dummy命名仅标识占位端口；教学豁免/具体行为仍须契约证据')
        if kind=='missing_source_or_dependency': limits.append('源码/目标缺失；相关静态/动态结论Blocked，S05不豁免最终覆盖')
        base={'row_id':'CCR-R-'+hashlib.sha256(('file\0'+p).encode()).hexdigest()[:20], 'row_kind':'file', 'module_id':m,'path':p,'canonical_path':item['canonical_path'], 'function_or_path':p, 'line_range':[1,item.get('line_count')] if item.get('line_count') else None, 'source_sha256':item.get('source_sha256'), 'provenance':item['provenance'], 'config':cfg,'active_or_dormant':{i:statuses[i] for i in cfg},'expected_contract':'C-'+m,'contract_source':'CONTRACTS.md#c-'+m.lower(), 'review_status':'Enumerated','dynamic_validation':'NotRun','normal':'Pending: 所属阶段核对','boundary_zero_empty_invalid':'Pending: 所属阶段核对','failure_state_return_cleanup':'Pending: 所属阶段核对','integer_alignment_lifetime':'Pending: 所属阶段核对','init_repeat':'Pending: 所属阶段核对','conditional_upstream_downstream':'Pending: 分支与双端入口已枚举，语义未核','evidence_ids':['CCR-E-P1-inventory'],'issue_ids':[],'limits':limits,'phase':phase_for(m,p),'scope_approval':{'receipt':APPROVAL,'boundaries':scope,'depth':depth},'classification':kind,'branch_refs':[b.get('branch_id',b.get('row_id')) for b in bypath[p]],'source_status':'unavailable' if kind=='missing_source_or_dependency' else 'present','alias_target_sha256':item.get('target_sha256')}
        base['provenance']={**base['provenance'],**{k:item.get(k) for k in ('git_repo','git_head','git_tracked','git_ignored','git_status','head_blob','source_matches_head')}}
        base['hash_semantics']=item.get('hash_semantics','missing: no file bytes')
        base['inventory_id']=item['inventory_id']
        base['placeholder_candidates']=placeholders[p]
        base['enumeration_phase']='CCR-P1'
        base['phase_responsibilities']=handoffs(m,p)
        base['closure_phase']='CCR-P10: 仅总差集/版本漂移/证据复核，不重复主体审阅'
        base['related_module_ids']=[k for prefix,k in [('nemu/src/isa/riscv','N03'),('nemu/src/isa/mips32','N04'),('nemu/src/isa/loongarch32r','N05')] if m=='N01' and p.startswith(prefix)]
        base['config_relation']='workspace-global support domain; not a build selection' if m=='X01' else 'symbolic applicability domain refined by path; direct declaration factors included; condition evaluation Pending'
        if 'S03' in scope:
            family = 'G-GIT' if kind=='git_metadata' else 'G-NEMU' if p.startswith('nemu/') else 'G-AM' if p.startswith('abstract-machine/') else 'G-NANOS' if p.startswith('nanos-lite/') else 'G-NAVY' if p.startswith('navy-apps/') else 'G-RT' if p.startswith('rt/') else 'G-AMK' if p.startswith('am-kernels/') else 'G-SUPPORT'
            base['generation_or_binding']={'entry':family,'source':'GENERATORS.md#'+family.lower(),'actual_generation_command':'Unknown: existing artifact not regenerated in P1','binding_target':item.get('link_target'),'coherence_status':'Pending: identity pinned; producer/config/consumer equivalence is not established'}
        if kind in ('git_metadata','generated_or_build_artifact','resource_or_editor_data','documentation_or_resource','directory_alias','binary_asset_provenance_pending'):
            for key in ('normal','boundary_zero_empty_invalid','failure_state_return_cleanup','integer_alignment_lifetime','init_repeat'):
                base[key]='N/A: 此行登记非实现资产；相关生成器/接口另有源码行；来源/消费链待所属阶段核对'
        rows.append(base);modules[m]+=1;kinds[kind]+=1
    file_rows={r['path']:r for r in rows}
    outside=[]
    for b in branches:
        if b['path'] not in file_rows: outside.append(b['path']);continue
        r=dict(file_rows[b['path']]); bid=b.get('branch_id',b.get('row_id'))
        r['row_id']='CCR-R-'+hashlib.sha256(('branch\0'+str(bid)).encode()).hexdigest()[:20]
        r['row_kind']='conditional_path';r['parent_row_id']=file_rows[b['path']]['row_id'];r['branch_refs']=[bid]
        r['line_range']=b['line_range']
        variant_ids={'CFG-NAVY-'+s for s in ('am_native','loongarch32r','mips32','native','riscv32','riscv32e','riscv64','x86')} | {'CFG-AM-'+s for s in ('loongarch32r-nemu','mips32-nemu','riscv32-nemu','riscv32e-nemu','riscv64-nemu','riscv32e-npc','riscv64-npc','x86-nemu','x86-qemu','x86_64-qemu','native','spike')} | {c['config_id'] for c in configs if c['config_id'].startswith('CFG-NEMU-isa-')}
        r['lexical_candidate_config_ids']=b.get('config_ids',[])
        r['condition_factor_ids']=[i for i in b.get('config_ids',[]) if i not in variant_ids]
        r['config']=sorted(set(r['config']+r['condition_factor_ids']))
        r['active_or_dormant']={i:statuses[i] for i in r['config']}
        r['function_or_path']=b.get('condition',b.get('directive',str(bid)))
        r['condition_evaluation']=b['active_or_dormant']
        r['parent_conditions']=b.get('parent_conditions',[])
        r['branch_kind']=b['kind']
        r['evidence_ids']=['CCR-E-P1-inventory','CCR-E-P1-branches']
        rows.append(r)
    with (BASE/'coverage.jsonl').open('w') as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
    stats={'file_rows':len(inv),'conditional_rows':len(rows)-len(inv),'total_rows':len(rows),'modules':dict(sorted(modules.items())),'classification':dict(kinds),'branches_outside_inventory':sorted(set(outside)),'reviewed_rows':0,'confirmed_findings':0,'exclusions':0}
    (BASE/'p1/coverage-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(stats,ensure_ascii=False,indent=2))
    if (BASE/'SCOPE_RV64.md').exists():
        from apply_rv64_scope import apply
        apply()

if __name__=='__main__': main()
