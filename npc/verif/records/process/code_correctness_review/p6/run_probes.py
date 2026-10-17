#!/usr/bin/env python3
"""Isolated direct compiler probes; no project make or original build writes."""
from pathlib import Path
import os,json,hashlib,shutil,subprocess,tempfile
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());O=Path(tempfile.mkdtemp(prefix='ccr-p6-')); cmds=[];copies=[]
def cp(p):
 s=R/p;d=O/p;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d);copies.append({'path':p,'sha256':hashlib.sha256(s.read_bytes()).hexdigest()});return d
for p in list((R/'nanos-lite/include').glob('*.h'))+list((R/'nanos-lite/src').glob('*'))+list((R/'abstract-machine/am/include').rglob('*.h'))+list((R/'abstract-machine/klib/include').glob('*.h')):
 if p.is_file() and p.suffix in ['.h','.c','.S']:cp(str(p.relative_to(R)))
cp('abstract-machine/am/src/riscv/npc/ioe.c')
for p in H.glob('*-probe.c'):shutil.copy2(p,O/p.name)
env={**os.environ,'CCACHE_DISABLE':'1','ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'}
def run(n,args,expected=0):
 p=subprocess.run(list(map(str,args)),cwd=O,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
 (H/(n+'.log')).write_text(p.stdout);cmds.append({'name':n,'argv':list(map(str,args)),'cwd':str(O),'exit':p.returncode,'expected_exit':expected,'log':n+'.log'});return p.returncode
inc=['-I'+str(O),'-I'+str(O/'nanos-lite/include'),'-I'+str(O/'abstract-machine/am/include'),'-I'+str(O/'abstract-machine/klib/include'),'-DARCH_H="arch/riscv.h"']
flags=['-std=gnu11','-O1','-g','-fno-builtin','-funsigned-char',*inc]
san=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-no-pie']
run('host-version',['gcc','--version']);run('rv-version',['riscv64-linux-gnu-gcc','--version'])
cases={'loader':[('valid',0),('phentsize',1),('short',0),('wrong-type',0),('overflow',0),('filesz',0),('kernel',0),('shared',0),('alignment',0),('args-large',0),('missing',0),('stack-overlap',0)],'fs-device':[('fs',0),('bad-fd',1),('seek',0),('events',0),('events-small',1),('audio-small',1),('audio-zero',0),('disp',0),('fb',0),('abi',0)],'mm':[('pages',0),('wrap',0),('brk',0),('vme',0)],'disk':[('normal',0),('range',42),('embed',0)],'schedule':[('',0)],'npc':[('',90)]}
for kind,scenarios in cases.items():
 extra=['-DKERNEL_EMBED_RAMDISK'] if kind in ['disk','npc'] else []
 rc=run(kind+'-build',['gcc',*flags,*san,*extra,O/(kind+'-probe.c'),'-o',O/kind])
 if rc:continue
 for s,e in scenarios:run(kind+'-'+(s or 'run'),[O/kind,s],e)
# Observe alignment and overlap output beyond UBSan's first misaligned store.
run('loader-observe-build',['gcc',*flags,'-no-pie',O/'loader-probe.c','-o',O/'loader-observe'])
for s in ['alignment','stack-overlap']:run('loader-observe-'+s,[O/'loader-observe',s])
# Legal retained stage selectors, edit only isolated common.h copies.
common=O/'nanos-lite/include/common.h';orig=common.read_text()
for stage in ['TEST_NTERM','TEST_KLOAD','MULTIPROGRAM','TIME_SHARING']:
 common.write_text(orig.replace('#define FG_PROCESS',f'#define {stage}'))
 if run('schedule-'+stage+'-build',['gcc',*flags,*san,O/'schedule-probe.c','-o',O/('schedule-'+stage)])==0:run('schedule-'+stage,[O/('schedule-'+stage),''],1)
common.write_text(orig)
# RV64 compile actual production units and ABI declarations using local newlib headers.
rv=['riscv64-linux-gnu-gcc','-O2','-std=gnu11','-Wall','-Werror','-fno-builtin','-fno-stack-protector','-march=rv64g','-mcmodel=medany','-mstrict-align','-fno-pic',*inc,'-I'+str(R/'navy-apps/libs/libc/include')]
for platform in ['nemu','npc']:
 for src in ['main','mm','loader','irq','proc','syscall','fs','disk','device']:
  extra=['-DKERNEL_EMBED_RAMDISK'] if platform=='npc' else []
  run('rv-'+platform+'-'+src,[*rv,*extra,'-c',O/f'nanos-lite/src/{src}.c','-o',O/f'{platform}-{src}.o'])
abi=O/'abi.c';abi.write_text('''#include <common.h>\n#include <sys/types.h>\n#include <sys/time.h>\n#include <elf.h>\n_Static_assert(sizeof(void*)==8,"pointer");\n_Static_assert(sizeof(off_t)==8,"off_t");\n_Static_assert(sizeof(struct timeval)==16,"timeval");\n_Static_assert(offsetof(struct timeval,tv_usec)==8,"usec");\n_Static_assert(sizeof(Elf64_Ehdr)==64 && sizeof(Elf64_Phdr)==56,"ELF");\n_Static_assert(sizeof(Context)==288,"Context");\n''')
run('rv-abi',[*rv,'-c',abi,'-o',O/'abi.o'])
run('rv-proc-size',['riscv64-linux-gnu-size','-A',O/'npc-proc.o'])
run('rv-npc-layout',['riscv64-linux-gnu-ld','-m','elf64lriscv','-T',R/'abstract-machine/scripts/linker-soc.ld','--defsym=_sram_start=0x0f000000','--defsym=_stack_offt=0x2000','--defsym=_heap_size=0x8000','--unresolved-symbols=ignore-all',O/'npc-proc.o','-o',O/'npc-layout.elf'],1)
res={'phase':'CCR-P6','date':'2026-10-17','out':str(O),'commands':cmds,'copies':copies,'environment':{k:env[k] for k in ['CCACHE_DISABLE','ASAN_OPTIONS','UBSAN_OPTIONS']},'output_hashes':{str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file()},'limit':'Host LP64 real OS source with stub FS/AM boundaries; direct RV64 compile is not guest execution. No production make, install or source edits.'}
(H/'probe-results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'out':str(O),'commands':len(cmds),'unexpected':[c for c in cmds if c['exit']!=c['expected_exit']]},indent=2))
