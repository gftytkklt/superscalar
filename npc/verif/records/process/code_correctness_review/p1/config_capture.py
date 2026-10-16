import os,re,json,hashlib,shutil,subprocess,collections
from pathlib import Path
R=Path('/home/gftyt/ysyx-workbench'); os.chdir(R)
O=R/'npc/verif/records/process/code_correctness_review'; (O/'p1').mkdir(exist_ok=True)
def sha(p):
 return hashlib.sha256(Path(p).read_bytes()).hexdigest() if Path(p).is_file() else None
def out(p,x): (O/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def phase(p):
 if p.startswith('nemu/'):
  return 'CCR-P2' if any(x in p for x in ['/isa/riscv','/isa/mips','/isa/loongarch','/memory/','/engine/interpreter/']) or p.endswith(('cpu-exec.c','include/cpu/decode.h','include/cpu/ifetch.h')) else 'CCR-P3'
 if p.startswith('abstract-machine/'):
  return 'CCR-P5' if any(x in p for x in ['/klib/','/ioe/','/libgcc/']) or Path(p).name in ('ioe.c','input.c','video.c','audio.c','gpu.c','timer.c','disk.c') else 'CCR-P4'
 if p.startswith('nanos-lite/'): return 'CCR-P6'
 if p.startswith('navy-apps/'):
  return 'CCR-P7' if any(x in p for x in ['/libs/libc/','/libs/libos/','/libs/libam/','/libs/compiler-rt/','/scripts/']) or p=='navy-apps/Makefile' else 'CCR-P8'
 if p.startswith(('am-kernels/','rt/bsp/abstract-machine/','fceux-am/')): return 'CCR-P5'
 return 'CCR-P9'
configs=[]
def add(id,c,status,selectors,paths,ph,limits=None,**kw):
 configs.append(dict(config_id=id,component=c,status=status,selectors=selectors,source_paths=paths,source_sha256={p:sha(p) for p in paths if Path(p).is_file()},limits=limits or ['本阶段仅枚举；未构建、未测试；可运行性不由配置身份推定'],phase=ph,review_status='Enumerated',dynamic_validation='NotRun',**kw))
current={}
for line in Path('nemu/.config').read_text().splitlines():
 m=re.match(r'CONFIG_(\w+)=(.*)',line)
 if m: current[m[1]]=m[2]
 m=re.match(r'# CONFIG_(\w+) is not set',line)
 if m: current[m[1]]='n'
add('CFG-NEMU-current','NEMU','active',current,['nemu/.config','nemu/include/config/auto.conf','nemu/include/generated/autoconf.h'],['CCR-P2','CCR-P3'],['active 仅表示持久配置；不代表现存二进制与源码/生成头匹配；命令行 override 未求值'])
for isa in ['riscv64','riscv32','riscv32e','mips32','loongarch32r','x86']:
 add('CFG-NEMU-isa-'+isa,'NEMU','active' if isa=='riscv64' else 'unavailable' if isa=='x86' else 'dormant',{'GUEST_ISA':isa if isa!='riscv32e' else 'riscv32','RV64':isa=='riscv64','RVE':isa=='riscv32e'},['nemu/Kconfig','nemu/src/isa/riscv32/Kconfig','nemu/src/isa/filelist.mk'],['CCR-P2','CCR-P3'],['x86 源码目录缺失，包装/声明仍审；S05'] if isa=='x86' else ['所有 ISA 分支均保留；RV64 与 RV32 为目录别名，RVE 条件单列；实现/占位分界待正式阶段逐路径判定'])
ks=[]
for p in ['nemu/Kconfig','nemu/src/isa/riscv32/Kconfig','nemu/src/memory/Kconfig','nemu/src/device/Kconfig']:
 lines=Path(p).read_text().splitlines(); starts=[(i,m[1]) for i,l in enumerate(lines) if (m:=re.match(r'\s*(?:menu)?config\s+(\w+)',l))]
 for n,(i,sym) in enumerate(starts):
  end=starts[n+1][0] if n+1<len(starts) else len(lines)
  block=lines[i:end]; val=current.get(sym,'not-emitted')
  typ=next((m[1] for l in block if (m:=re.match(r'\s*(bool|tristate|string|hex|int)\b',l))), 'Unknown')
  ks.append(sym)
  add('CFG-NEMU-symbol-'+sym,'NEMU','active' if val not in ('n','not-emitted') else 'dormant',{'CONFIG_'+sym:val,'domain':('y/n' if typ in ('bool','tristate') else typ)},[p],['CCR-P2','CCR-P3'],['未进行 Kconfig 求值；not-emitted 表示当前.config未输出，不等同永久不可达；正反分支均保留'],line_range=[i+1,end],kconfig_type=typ,declaration='\n'.join(block),alternatives='all declared/default/depends/select conditions, including disabled branch')
for p in sorted(Path('nemu/configs').glob('*defconfig')):
 add('CFG-NEMU-defconfig-'+p.name,'NEMU','dormant',{'defconfig':p.name},[str(p)],['CCR-P2','CCR-P3'],['未执行defconfig；不能覆盖当前.config；TARGET_AM 的 DON’T CHOOSE 为源码标签，批准/可用程度待契约核实'])
for mode in ['native-elf','shared-ref','am']:
 add('CFG-NEMU-target-'+mode,'NEMU','active' if mode=='native-elf' else 'dormant',{'target':mode},['nemu/Kconfig','nemu/Makefile','nemu/scripts/native.mk','nemu/scripts/build.mk'],['CCR-P3'],['AM target 标为 DON’T CHOOSE；保留源码静态审阅，运行支持契约Pending'] if mode=='am' else None)
for mode in ['legacy','mtimer']:
 add('CFG-NEMU-timer-'+mode,'NEMU','dormant',{'--timer-source':mode},['nemu/src/monitor/monitor.c','nemu/src/device/mtimer.c'],['CCR-P3','CCR-P9'],['当前运行参数Unknown；legacy源码默认，Linux历史入口选择mtimer；本次不运行'])
for mode in ['image','linux-kernel-dtb','serial-file-fifo','difftest-cli']:
 add('CFG-NEMU-runtime-'+mode,'NEMU','dormant',{'runtime_profile':mode},['nemu/src/monitor/monitor.c'],['CCR-P3','CCR-P9'],['参数可用性依赖RV64/DEVICE/SERIAL/DIFFTEST等；命令行范围只登记，不执行'])
archs=sorted(p.stem for p in Path('abstract-machine/scripts').glob('*.mk'))
for arch in archs:
 p='abstract-machine/scripts/'+arch+'.mk'; txt=Path(p).read_text()
 extra=[str(q) for q in Path('abstract-machine/scripts/isa').glob('*.mk') if 'scripts/isa/'+q.name in txt]+[str(q) for q in Path('abstract-machine/scripts/platform').glob('*.mk') if 'scripts/platform/'+q.name in txt]
 limits=['AM无持久当前ARCH；dormant表示本轮未选中，历史build不是active证明；工具/运行平台见AVAILABILITY']
 if arch=='x86-nemu': limits+=['AM端口源码保留；NEMU x86实现缺失，端到端运行 unavailable']
 if 'npc' in arch: limits+=['平台脚本选择dummy VME/MPE；riscv/npc独立vme/mpe现有文件仍在范围，是否未来启用Pending']
 add('CFG-AM-'+arch,'AM','unavailable' if arch=='x86-nemu' else 'dormant',{'ARCH':arch,'declarations':txt.strip().splitlines()},[p]+extra,['CCR-P4','CCR-P5'],limits)
link_modes={'linker':'generic-NEMU','linker-soc':'xip','linker-sram':'sram','linker-psram':'psram','linker-psram-ssbl':'psram-ssbl','linker-sdram':'sdram','linker-sdram-heap':'sdram-heap','linker-sdram-rt':'explicit-LDS-for-RT'}
for p in sorted(Path('abstract-machine/scripts').glob('*.ld')):
 add('CFG-AM-linker-'+p.stem,'AM','active' if p.stem=='linker-soc' else 'dormant',{'LDS':str(p),'BOOT_MODE':link_modes.get(p.stem,'explicit-LDS')},[str(p),'abstract-machine/scripts/platform/npc.mk','npc/.npc_config'],['CCR-P4','CCR-P9'],['active仅是.npc_config的xip默认映射；LDS/BOOT_S命令行可覆盖；sdram-rt为独立显式入口，不添加不存在的BOOT_MODE'])
add('CFG-AM-spike-linker','AM','dormant',{'LDS':'am/src/riscv/spike/linker.ld'},['abstract-machine/am/src/riscv/spike/linker.ld','abstract-machine/scripts/spike.mk'],['CCR-P4'])
add('CFG-AM-dummy-runtime','AM','placeholder',{'apis':['cte','vme','mpe','ioe']},[str(p) for p in sorted(Path('abstract-machine/am/src/platform/dummy').glob('*.c'))],['CCR-P4','CCR-P5'],['dummy身份由目录/API静态识别；占位不代表已获批准简化或正确性通过'])
for sel in ['__NATIVE_USE_KLIB__','mainargs','HEAP_SIZE','WITH_SDL','BOOT_S','LDS','smp']:
 add('CFG-AM-option-'+sel,'AM','dormant',{'option':sel,'domain':'defined/undefined or caller-supplied value'},['abstract-machine/Makefile','abstract-machine/scripts/platform/npc.mk','abstract-machine/scripts/platform/qemu.mk','abstract-machine/klib/src/stdlib.c'],['CCR-P4','CCR-P5','CCR-P9'],['参数domain按源码枚举；未进行兼容性笛卡尔积、编译器预定义宏求值或批准新组合'])
features=['HAS_CTE','HAS_VME','TEST_DUMMY','TEST_FILE','TEST_KLOAD','TEST_NTERM','MULTIPROGRAM','TIME_SHARING','FG_PROCESS','MULTITASK','STRACE','KERNEL_EMBED_RAMDISK','HAS_NAVY']
for feature in features:
 for on in [True,False]:
  known=feature in ['HAS_CTE','HAS_VME','FG_PROCESS','MULTITASK','HAS_NAVY']
  state='active' if on==known else 'dormant'
  if feature=='KERNEL_EMBED_RAMDISK': state='dormant'
  add(f'CFG-NANOS-{feature}-'+('on' if on else 'off'),'nanos-lite',state,{feature:'defined/nonempty' if on else 'undefined/empty'},['nanos-lite/include/common.h','nanos-lite/Makefile'],['CCR-P6','CCR-P9'],['各开关为因子；TEST_*/MULTIPROGRAM/TIME_SHARING/FG_PROCESS注释要求互斥，MULTITASK派生，不能理解为任意组合合法；实际ARCH/命令行Unknown'])
for isa in sorted(p.stem for p in Path('navy-apps/scripts').glob('*.mk')):
 p='navy-apps/scripts/'+isa+'.mk'; extra=['navy-apps/scripts/riscv/common.mk'] if isa.startswith('riscv') else []
 add('CFG-NAVY-'+isa,'navy-apps','unavailable' if isa in ('mips32','loongarch32r','riscv32','riscv32e','x86') else 'dormant',{'ISA':isa,'declarations':Path(p).read_text().strip().splitlines()},[p,'navy-apps/Makefile']+extra,['CCR-P7','CCR-P8','CCR-P9'],['ISA无持久当前值；8脚本全保留；32位构建依赖compiler-rt/repo缺源，所以本机默认构建unavailable，现有源码仍审'] if isa in ('mips32','loongarch32r','riscv32','riscv32e','x86') else ['ISA无持久当前值；实际链接/运行配置Unknown；native经libos native.so，am_native使用AM宿主布局'])
for mode in ['on','off']:
 add('CFG-NAVY-VME-'+mode,'navy-apps','dormant',{'VME':'nonempty' if mode=='on' else 'empty'},['navy-apps/scripts/riscv/common.mk','navy-apps/scripts/x86.mk','navy-apps/scripts/mips32.mk','navy-apps/scripts/loongarch32r.mk','navy-apps/scripts/am_native.mk'],['CCR-P7','CCR-P9'],['Make $(if $(VME),...) 按非空选择；不能把VME=0自动当off；有VME地址0x40000000，无VME RV/MIPS/LA=0x83000000，x86/am_native=0x03000000'])
for feat in ['NO_FLOATING_POINT','HAVE_INITFINI_ARRAY','__NAVY__','native-preload','compiler-rt-32bit','busybox-config']:
 add('CFG-NAVY-option-'+feat,'navy-apps','unavailable' if feat=='compiler-rt-32bit' else 'dormant',{'feature':feat},['navy-apps/Makefile','navy-apps/libs/libc/Makefile','navy-apps/libs/libos/Makefile','navy-apps/apps/busybox/config/nanos-lite.config'],['CCR-P7','CCR-P8'],['第三方宏分支完整保留在branches.jsonl；不因当前Make默认宏而排除其他自有实现'])
for dep,p in [('compiler-rt','navy-apps/libs/compiler-rt/repo'),('oslab0','navy-apps/apps/oslab0/repo'),('fceux','fceux')]:
 add('CFG-MISSING-'+dep,'support','unavailable',{'required_path':p},[p],['CCR-P7' if dep=='compiler-rt' else 'CCR-P8'],['缺源；恢复需用户提供准确版本/路径或明确范围调整；不clone，不以fceux-am替代fceux'])
add('CFG-SUPPORT-AM-callers','support','dormant',{'scope':'A13 / X04 runtime integration only'},['rt/bsp/abstract-machine/Makefile','rt/bsp/abstract-machine/Kconfig','rt/bsp/abstract-machine/.config','am-kernels/tests/am-tests/Makefile'],['CCR-P5'],['仅AM接入/构建/测试oracle；不扩为完整RT/算法审阅；Kconfig及测试宏分支见branches'])
add('CFG-SUPPORT-LINUX-native','support','dormant',{'ARCH':'riscv64-nemu','ISA':'rv64ima_zicsr_zifencei','ABI':'lp64'},['npc/verif/linux/boot/Makefile','npc/verif/linux/dtb/targets/nemu.mk','npc/verif/linux/initramfs/Makefile'],['CCR-P3','CCR-P9'],['历史M1资产仅作契约与测试入口，不重验业务Milestone'])
def mask_c_comments(text):
 result=[]; i=0; state='code'
 while i<len(text):
  c=text[i]; n=text[i+1] if i+1<len(text) else ''
  if state=='code':
   if c=='/' and n=='*': result.extend('  '); i+=2; state='block'; continue
   if c=='/' and n=='/': result.extend('  '); i+=2; state='line'; continue
   if c=='"': state='string'
   elif c=="'": state='char'
   result.append(c)
  elif state=='block':
   if c=='*' and n=='/': result.extend('  '); i+=2; state='code'; continue
   result.append('\n' if c=='\n' else ' ')
  elif state=='line':
   result.append('\n' if c=='\n' else ' ')
   if c=='\n': state='code'
  else:
   result.append(c)
   if c=='\\' and n: result.append(n); i+=2; continue
   if (state=='string' and c=='"') or (state=='char' and c=="'"): state='code'
  i+=1
 return ''.join(result)

# Full lexical condition inventory, not preprocessor or correctness analysis.
roots=['nemu','abstract-machine','nanos-lite','navy-apps','am-kernels','rt/bsp/abstract-machine']
files=[]
for root in roots:
 for d,dirs,names in os.walk(root,followlinks=False):
  dirs[:]=[x for x in dirs if x not in ('.git','build','.metals','.vscode') and not Path(d,x).is_symlink()]
  for name in names:
   p=Path(d,name)
   if p.is_symlink(): continue
   if p.suffix.lower() in ('.c','.h','.cc','.cpp','.cxx','.hpp','.s','.inc','.mk','.ld','.sh','.py') or p.name in ('Makefile','Kconfig','Config.in'):
    files.append(p)
# include selected support inputs, no broad NPC scan
for p in ['Makefile','init.sh','npc/.npc_config']:
 files.append(Path(p))
for d in ['npc/verif/linux/boot','npc/verif/linux/dtb','npc/verif/linux/initramfs']:
 files.extend(p for p in Path(d).rglob('*') if p.is_file() and not p.is_symlink() and p.suffix in ('.py','.sh','.mk','.dts','.dtsi'))
rows=[]; config_refs=set(); unbalanced=[]; scanned=[]
for p in sorted(set(files)):
 try:
  data=p.read_bytes()
  if b'\0' in data: continue
  text=data.decode('utf-8',errors='replace')
 except OSError: continue
 path=str(p); digest=hashlib.sha256(data).hexdigest(); lines=text.splitlines(); stack=[]; scanned.append({'path':path,'sha256':digest,'line_count':len(lines)})
 ismake=p.suffix=='.mk' or p.name=='Makefile'; isk=p.name in ('Kconfig','Config.in')
 # Preserve line identity while masking C comments; shell/Python comments are not preprocessor directives.
 iscode=p.suffix.lower() in ('.c','.h','.cc','.cpp','.cxx','.hpp','.s','.inc')
 masked=mask_c_comments(text) if iscode else text
 masked_lines=masked.splitlines()
 for i,raw in enumerate(lines,1):
  l=masked_lines[i-1] if i<=len(masked_lines) else raw
  m=re.match(r'^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)',l)
  kind=None; token=None
  if m and iscode: kind='preprocessor'; token=m[1]
  elif ismake and (m:=re.match(r'^\s*(ifeq|ifneq|ifdef|ifndef|else|endif)\b(.*)',l)): kind='make'; token=m[1]
  elif isk and (re.match(r'^(if |endif\b)',l) or re.match(r'^\s*(depends on |select |imply |default .*\bif\b|visible if )',l)): kind='kconfig'; token=l.strip().split()[0]
  elif re.search(r'\b(IFDEF|IFNDEF|MUXDEF|MUXNDEF|IFONE|MUXONE)\s*\(',l): kind='macro-selector'; token='selector'
  elif ismake and ('$(if ' in l or re.search(r'\$\(CONFIG_\w+\)',l)): kind='make-selector'; token='selector'
  if path.startswith('nemu/') and not any(x in path for x in ['/tools/kconfig/','/tools/spike-diff/repo/']): config_refs.update(re.findall(r'\bCONFIG_(\w+)\b',l))
  if not kind: continue
  rid='BR-'+hashlib.sha256(f'{path}:{i}:{kind}'.encode()).hexdigest()[:16]
  open_=token in ('if','ifdef','ifndef','ifeq','ifneq'); close=token=='endif'
  groups=list(stack)
  if open_: stack.append(rid)
  if close:
   if stack: stack.pop()
   else: unbalanced.append({'path':path,'line':i,'issue':'lexical close without opener; parser is not authoritative'})
  syms=re.findall(r'\bCONFIG_(\w+)\b',l)
  ids=['CFG-NEMU-symbol-'+s for s in syms if s in ks]
  if not ids:
   if path.startswith('nemu/'): ids=['CFG-NEMU-isa-'+x for x in ['riscv64','riscv32','riscv32e','mips32','loongarch32r','x86']]
   elif path.startswith('abstract-machine/'): ids=['CFG-AM-'+a for a in archs]
   elif path.startswith('nanos-lite/'): ids=['CFG-NANOS-'+x+'-'+v for x in features for v in ['on','off'] if re.search(r'\b'+x+r'\b',l)] or ['CFG-NANOS-HAS_CTE-on','CFG-NANOS-HAS_CTE-off','CFG-NANOS-HAS_VME-on','CFG-NANOS-HAS_VME-off']
   elif path.startswith('navy-apps/'): ids=['CFG-NAVY-'+x.stem for x in sorted(Path('navy-apps/scripts').glob('*.mk'))]
   else: ids=['CFG-SUPPORT-AM-callers'] if path.startswith(('am-kernels/','rt/')) else ['CFG-SUPPORT-LINUX-native']
  rows.append({'branch_id':rid,'path':path,'canonical_path':str(p.resolve().relative_to(R)),'line_range':[i,i],'source_sha256':digest,'kind':kind,'directive':token,'condition':raw.strip(),'parent_conditions':groups,'config_ids':ids,'phase':phase(path),'review_status':'Enumerated','active_or_dormant':'Unknown: unevaluated lexical condition; all arms retained','limits':['条件指令导航；含头文件guard/第三方宏；非可达性证明；运行时条件和多行宏完整语义留所属正式阶段']})
 if stack: unbalanced.append({'path':path,'open_groups':stack,'issue':'lexical group left open; source may contain embedded/template syntax'})
extras=sorted(config_refs-set(ks))
for s in extras:
 add('CFG-NEMU-symbol-'+s,'NEMU','dormant',{'CONFIG_'+s:'not declared in traversed project Kconfig'},['nemu/Kconfig'],['CCR-P2','CCR-P3'],['源码残留/外部预定义/历史符号候选；未自定意义或删除；正式阶段核对其生产者/可达性'],declaration_status='Unknown / no declaration found')
# Associate extra symbols where encountered.
for row in rows:
 for s in extras:
  if re.search(r'\bCONFIG_'+re.escape(s)+r'\b',row['condition']) and 'CFG-NEMU-symbol-'+s not in row['config_ids']: row['config_ids'].append('CFG-NEMU-symbol-'+s)
for r in configs:
 r['status_semantics']='active=持久配置/派生选择可见；dormant=本轮未选中或选择Unknown；unavailable=指定依赖缺源；placeholder=明确dummy入口；均非正确性结论'
 r['source_availability']='missing dependency; existing source retained' if r['status']=='unavailable' else 'see inventory; no exclusion inferred'
 if r['config_id']=='CFG-AM-dummy-runtime' and (O/'p1/placeholder-candidates.jsonl').exists():
  ph=[json.loads(l) for l in (O/'p1/placeholder-candidates.jsonl').read_text().splitlines()]
  r['placeholder_evidence']=[{'path':x['path'],'line_range':x['line_range'],'placeholder_id':x['placeholder_id']} for x in ph if '/platform/dummy/' in x['path']]
configs.sort(key=lambda x:x['config_id']); out(Path('configs.json'),configs)
(O/'branches.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
out(Path('p1/branch-enumeration.json'),{'date':'2026-10-16','method':'Static lexical scan only; no make/preprocessor/toolchain invoked','roots':roots,'exclude_directories':['.git','build','.metals','.vscode'],'extensions':['.c','.h','.cc','.cpp','.cxx','.hpp','.s','.inc','.mk','.ld','.sh','.py','Makefile','Kconfig','Config.in'],'symlinks':'not followed; canonical source enumerated once; file aliases are in inventory/coverage','scanned_files':scanned,'branch_rows':len(rows),'counts':dict(collections.Counter(r['kind'] for r in rows)),'nemu_kconfig_symbol_count':len(ks),'nemu_symbols_without_declaration':extras,'lexical_balance_notices':unbalanced,'limits':['每个源码文件coverage仍保留；没有条件指令的文件并非无路径','这是P1配置分支入口，不取代P2–P8逐函数/运行时路径审阅','条件合法组合由原Kconfig/source契约约束；不声称笛卡尔积全可构建']})
# Existing probe evidence is reused during metadata-only regeneration.
import sys
if (O/'p1/environment.json').exists() and '--reprobe' not in sys.argv:
 print(json.dumps({'configs':len(configs),'branches':len(rows),'scanned_files':len(scanned),'kconfig_symbols':len(ks),'extra_symbols':extras,'lexical_notices':len(unbalanced),'environment':'reused; no probes repeated'},ensure_ascii=False)); sys.exit(0)
# Safe availability discovery: explicit executables, no project command execution.
tools=['python3','bash','git','rg','gcc','g++','clang','clang++','ld','ar','nm','readelf','objdump','objcopy','make','pkg-config','sdl2-config','llvm-config-18','llvm-config','gdb','riscv64-linux-gnu-gcc','riscv64-linux-gnu-objcopy','riscv64-linux-gnu-readelf','riscv64-unknown-elf-gcc','mips-linux-gnu-gcc','loongarch32r-linux-gnusf-gcc','x86_64-linux-gnu-gcc','qemu-system-i386','qemu-system-x86_64','qemu-system-riscv64','spike','verilator','dtc','scons','timeout','gzip','cpio','bison','flex','valgrind','cppcheck']
probes=[]
for name in tools:
 executable=shutil.which(name); row={'tool':name,'path':executable,'status':'present' if executable else 'unavailable','probe':'PATH lookup via shutil.which (command -v equivalent)'}
 if executable:
  flag='-v' if name=='dtc' else '--version'
  try:
   r=subprocess.run([executable,flag],capture_output=True,text=True,timeout=5)
   row.update(argv=[executable,flag],exit_code=r.returncode,version_output='\n'.join((r.stdout+r.stderr).splitlines()[:4]))
  except Exception as e: row['version_error']=type(e).__name__+': '+str(e)
 probes.append(row)
packages=[]
if shutil.which('pkg-config'):
 for package in ['sdl2','readline','zlib','libffi']:
  r=subprocess.run(['pkg-config','--modversion',package],capture_output=True,text=True,timeout=5)
  packages.append({'package':package,'argv':['pkg-config','--modversion',package],'exit_code':r.returncode,'version_or_error':r.stdout.strip() if r.returncode==0 else r.stderr.strip()})
assets=['nemu/build/riscv64-nemu-interpreter','nemu/build/riscv64-nemu-interpreter-so','npc/build/ysyxSoCFull','navy-apps/build/ramdisk.img','navy-apps/build/ramdisk.h','navy-apps/libs/compiler-rt/repo','navy-apps/apps/oslab0/repo','fceux','fceux-am','nemu/src/isa/x86','nemu/tools/spike-diff/repo','am-kernels/tests/riscv-tests','/home/gftyt/linux-m0/opensbi','/home/gftyt/linux-m0/busybox-1.36.1/busybox','/home/gftyt/linux-m0/linux-6.1.188/usr/gen_init_cpio','npc/verif/build/linux-kernel/nemu-src/Makefile']
asset_rows=[]
for s in assets:
 p=Path(s); asset_rows.append({'path':s,'exists':p.exists(),'kind':'directory' if p.is_dir() else 'file' if p.is_file() else 'missing','sha256':sha(p),'execution':'NotRun','limits':'existence is not compatibility/current build evidence'})
env={k:os.environ.get(k,'UNSET') for k in ['NEMU_HOME','AM_HOME','NAVY_HOME','NPC_HOME','ARCH','ISA','DISPLAY','WAYLAND_DISPLAY']}
out(Path('p1/environment.json'),{'date':'2026-10-16','phase':'CCR-P1','cwd':str(R),'probe_policy':'只读PATH/版本/pkg-config/文件存在与哈希；无项目make调用（仅GNU Make --version）、构建、模拟器、测试脚本或安装','tools':probes,'pkg_config':packages,'environment_selectors':env,'assets':asset_rows,'business_builds':0,'business_tests':0,'installs':0,'limitations':['宿主GUI/音频/硬件/进程环境未验证','工具存在不证明支持全部march/mabi/32位链接；未编译探针','隔离副本及各脚本副作用仍须实际验证阶段重新审核']})
print(json.dumps({'configs':len(configs),'branches':len(rows),'scanned_files':len(scanned),'kconfig_symbols':len(ks),'extra_symbols':extras,'lexical_notices':len(unbalanced),'tools_present':[p['tool'] for p in probes if p['status']=='present'],'tools_unavailable':[p['tool'] for p in probes if p['status']=='unavailable']},ensure_ascii=False))
