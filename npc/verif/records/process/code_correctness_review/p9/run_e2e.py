#!/usr/bin/env python3
"""Fresh-source bounded CCR-P9 guest probe. No make/git/network; output only /tmp and new evidence."""
from pathlib import Path
import argparse, subprocess, tempfile, shutil, os, json, hashlib, resource
ROOT=Path(__file__).resolve().parents[6]; HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
OUT=a.output.resolve();OUT.mkdir(parents=True,exist_ok=False)
W=Path(tempfile.mkdtemp(prefix='ccr-p9-e2e-'));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
R={'date':'2026-10-17','work':str(W),'commands':[],'sources':{},'scope':'controlled payload/files at four existing FG paths; original nanos config/implementation, AM, NEMU; no GUI/real sound claim','fixture_substitutions':['generated files.h and isolated ramdisk contents','application payload','user __assert_func failure sink'],'make':False,'production_edits':False}
R['runner_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def save(): (OUT/'results.json').write_text(json.dumps(R,ensure_ascii=False,indent=2)+'\n')
def run(label,cmd,timeout=60,env=None,required=True):
 try:
  q=subprocess.run([str(x) for x in cmd],cwd=W,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);rc=q.returncode;out=q.stdout
 except subprocess.TimeoutExpired as e: rc='TIMEOUT';out=(e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else e.stdout or ''
 (OUT/(label+'.log')).write_text(out)
 R['commands'].append({'label':label,'argv':[str(x) for x in cmd],'cwd':str(W),'returncode':rc,'log':label+'.log','timeout_seconds':timeout});save()
 print(label,rc,flush=True)
 if required and rc!=0: raise RuntimeError(label+' failed; inspect '+str(OUT/(label+'.log')))
 return rc,out
def copytree(src):
 shutil.copytree(ROOT/src,W/src,ignore=shutil.ignore_patterns('.git','build','__pycache__'))
 for x in (W/src).rglob('*'):
  if x.is_file():
   z=ROOT/x.relative_to(W);R['sources'][str(z.relative_to(ROOT))]=hashlib.sha256(z.read_bytes()).hexdigest()
for s in ['nemu/include','nemu/src','abstract-machine/am/include','abstract-machine/am/src','abstract-machine/klib','nanos-lite/include','nanos-lite/src','nanos-lite/resources','navy-apps/libs/libc/include','navy-apps/libs/libos/src']:
 copytree(s)
# files.h was dereferenced above; source identity retained before fixture replacement.
for s in ['abstract-machine/scripts/linker.ld','navy-apps/libs/libc/Makefile']:
 t=W/s;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/s,t);R['sources'][s]=hashlib.sha256((ROOT/s).read_bytes()).hexdigest()
for tool in ['gcc','riscv64-linux-gnu-gcc','riscv64-linux-gnu-ld']:
 run('version-'+tool,['/usr/bin/'+tool,'--version'])
ns=['src/nemu-main.c']
for d in ['cpu','monitor','utils','memory','engine/interpreter','isa/riscv32','device/io']:
 ns += [str(x.relative_to(W/'nemu')) for x in (W/'nemu/src'/d).rglob('*.c')]
ns += ['src/device/'+x+'.c' for x in ['device','alarm','intr','serial','timer','mtimer','keyboard','vga','audio','disk']]
run('nemu-build',['/usr/bin/gcc','-O2','-g','-Wall','-Werror','-D__GUEST_ISA__=riscv64','-Inemu/include','-Inemu/src/isa/riscv32/include',*[str(Path('nemu')/s) for s in ns],'-lreadline','-ldl','-lSDL2','-o','nemu-current'],timeout=60)
CC='/usr/bin/riscv64-linux-gnu-gcc';LD='/usr/bin/riscv64-linux-gnu-ld'
flags=['-O2','-g','-std=gnu11','-march=rv64g','-mcmodel=medany','-fno-pic','-static','-fno-builtin','-fno-stack-protector','-fno-asynchronous-unwind-tables','-ffunction-sections','-fdata-sections','-U_FORTIFY_SOURCE']
uflags=flags+['-D__NAVY__','-DHAVE_INITFINI_ARRAY','-DNO_FLOATING_POINT','-Inavy-apps/libs/libc/include']
libsrc=['misc/init.c','reent/impure.c','reent/reent.c','stdlib/exit.c','stdlib/__call_atexit.c','stdlib/environ.c','errno/errno.c','string/strlen.c','string/strcmp.c','string/memcmp.c']
for h in (ROOT/'navy-apps/libs/libc/src').rglob('*.h'):
 src=h.relative_to(ROOT);t=W/src;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(h,t);R['sources'][str(src)]=hashlib.sha256(h.read_bytes()).hexdigest()
user=[W/'navy-apps/libs/libos/src/crt0/start.S',W/'navy-apps/libs/libos/src/crt0/crt0.c',W/'navy-apps/libs/libos/src/syscall.c']
for s in libsrc:
 src='navy-apps/libs/libc/src/'+s;t=W/src;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/src,t);R['sources'][src]=hashlib.sha256((ROOT/src).read_bytes()).hexdigest();user.append(t)
shutil.copy2(HERE/'e2e-user.c',W/'e2e-user.c');user.append(W/'e2e-user.c')
uobjs=[]
for i,s in enumerate(user):
 obj=W/f'user-{i}.o';run(f'user-compile-{i}',[CC,*uflags,'-c',s,'-o',obj]);uobjs.append(obj)
run('user-link',[LD,'--no-relax','-Ttext-segment','0x40000000','-e','_start','--gc-sections',*uobjs,'-o','user.elf'],required=False)
if not (W/'user.elf').exists(): raise RuntimeError('user link; preserve attempts')
run('user-elf',['/usr/bin/riscv64-linux-gnu-readelf','-hlW','user.elf'])
data=(W/'user.elf').read_bytes();names=['/bin/pal','/bin/nterm','/bin/nslider','/bin/hello'];image=b'';table=[]
for name in names:
 table.append('{"%s", %d, %d, NULL, NULL},'%(name,len(data),len(image)));image+=data
image+=b'\0'*((-len(image))%512);table.append('{"/data/check", 7, %d, NULL, NULL},'%len(image));image+=b'ABCDEFG';image+=b'\0'*((-len(image))%512)
(W/'navy-runtime/build').mkdir(parents=True);(W/'navy-runtime/build/ramdisk.img').write_bytes(image);(W/'nanos-lite/src/files.h').write_text('\n'.join(table)+'\n')
R['controlled_files']=table
ks=[x for x in (W/'nanos-lite/src').glob('*.c')]+[W/'nanos-lite/src/resources.S']
am=['riscv/nemu/start.S','riscv/nemu/cte.c','riscv/nemu/trap.S','riscv/nemu/vme.c','platform/nemu/trm.c','platform/nemu/mpe.c']+['platform/nemu/ioe/'+s+'.c' for s in ['ioe','timer','input','gpu','audio','disk']]
ks += [W/'abstract-machine/am/src'/s for s in am]+list((W/'abstract-machine/klib/src').glob('*.c'))
kflags=flags+['-mstrict-align','-D__ISA_RISCV64__','-D__ARCH_RISCV64_NEMU','-D__PLATFORM_NEMU','-DARCH_H="arch/riscv.h"','-DISA_H="riscv/riscv.h"','-DMAINARGS=""','-Inanos-lite/include','-Iabstract-machine/am/include','-Iabstract-machine/klib/include','-Iabstract-machine/am/src','-Iabstract-machine/am/src/platform/nemu/include']
kobjs=[]
for i,s in enumerate(ks):
 extra=['-Inavy-apps/libs/libc/include','-Wa,-I'+str(W/'nanos-lite')] if 'nanos-lite' in str(s) else []
 obj=W/f'kernel-{i}.o';run(f'kernel-compile-{i}',[CC,*kflags,*extra,'-c',s,'-o',obj]);kobjs.append(obj)
run('kernel-link',[LD,'-melf64lriscv','-T','abstract-machine/scripts/linker.ld','--defsym=_pmem_start=0x80000000','--defsym=_entry_offset=0','--gc-sections','-e','_start',*kobjs,'-o','kernel.elf'])
run('kernel-bin',['/usr/bin/riscv64-linux-gnu-objcopy','-S','--set-section-flags','.bss=alloc,contents','-O','binary','kernel.elf','kernel.bin'])
env=dict(os.environ,CCACHE_DISABLE='1',SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NAVY_HOME=str(W/'navy-runtime'))
R['runtime_env']={k:env[k] for k in ['CCACHE_DISABLE','SDL_VIDEODRIVER','SDL_AUDIODRIVER','NAVY_HOME']}
rc,out=run('guest',[W/'nemu-current','-b','--timer-source=legacy',W/'kernel.bin'],timeout=20,env=env,required=False)
R['observations']={s:s in out for s in ['P9_USER_START','P9_FILE_EOF_SEEK_CLOSE','P9_TIME_RETURN','P9_EXEC_MISSING_RETURN','P9_BRK_RETURN','P9_AFTER_YIELD','P9_EXEC_NEW_CONTEXT','P9_EXIT_RELOADED_NTERM','HIT GOOD TRAP']}
R['e2e_success']=rc==0 and all(R['observations'].values())
R['artifacts']={str(x.relative_to(W)):{'size':x.stat().st_size,'sha256':hashlib.sha256(x.read_bytes()).hexdigest()} for x in [W/'nemu-current',W/'kernel.elf',W/'kernel.bin',W/'user.elf',W/'navy-runtime/build/ramdisk.img']}
save();print(json.dumps(R['observations']),flush=True)
