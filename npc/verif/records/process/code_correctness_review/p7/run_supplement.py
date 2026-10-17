#!/usr/bin/env python3
"""Additional isolated adapters and build-recipe tests. No real ecall or project make."""
from pathlib import Path
import json, os, re, shutil, subprocess, tempfile, hashlib
ROOT=Path(__file__).resolve().parents[6]; HERE=Path(__file__).resolve().parent
WORK=Path(tempfile.mkdtemp(prefix='ccr-p7-supp-work-')); OUT=Path(tempfile.mkdtemp(prefix='ccr-p7-supp-evidence-'))
records=[]; transformations=[]
def run(name,args,expected=0):
 p=subprocess.run(list(map(str,args)),cwd=WORK,env=dict(os.environ,CCACHE_DISABLE='1'),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
 (OUT/(name+'.log')).write_bytes(p.stdout);records.append(dict(name=name,argv=list(map(str,args)),cwd=str(WORK),exit=p.returncode,expected_exit=expected,log=name+'.log'))
 (OUT/'results.json').write_text(json.dumps(records,indent=2)+'\n');return p.returncode
for part in ['src','include']:shutil.copytree(ROOT/'navy-apps/libs/libc'/part,WORK/'libc'/part)
inc=WORK/'libc/include'
# Host adapter changes only the hardware-specific inline asm block, preserving wrappers.
source=(ROOT/'navy-apps/libs/libos/src/syscall.c').read_text()
a=source.index('  register intptr_t _gpr1');b=source.index('\n}',a)
source=source[:a]+'  return p7_ecall(type, a0, a1, a2);'+source[b:]
source='extern long p7_ecall(long,long,long,long);\n'+source
(WORK/'syscall.c').write_text(source);shutil.copy2(ROOT/'navy-apps/libs/libos/src/syscall.h',WORK/'syscall.h')
transformations.append('libos syscall.c: only register/asm/return block replaced by p7_ecall; rest byte text unchanged; no real OS call')
for n in ['openr','execr']:
 p=WORK/'libc/src/reent'/(n+'.c');p.write_text(re.sub(r'\berrno\b','p7_low_errno',p.read_text()))
transformations.append('reent openr/execr: identifier errno renamed p7_low_errno to separate non-TLS low-layer errno from host libc; high-level __errno separately renamed')
names=['_exit','_open','_write','_sbrk','_read','_close','_lseek','_gettimeofday','_execve','_fstat','_stat','_kill','_getpid','_fork','vfork','_link','_unlink','_wait','_times','pipe','dup','dup2','sleep','readlink','symlink','ioctl']
rename=['-D'+n+'=p7_'+n.lstrip('_') for n in names]+['-D__errno=p7_errno']
host=['/usr/bin/gcc','-std=gnu11','-O2','-D__riscv','-D__NAVY__','-fno-builtin','-ffunction-sections','-fdata-sections','-I'+str(inc),'-Wl,--gc-sections']
if run('errno-build',[*host,*rename,WORK/'syscall.c',WORK/'libc/src/reent/openr.c',WORK/'libc/src/reent/execr.c',HERE/'errno-probe.c','-o',WORK/'errno'])==0:run('errno-paths',[WORK/'errno'])
# Preserve exact headers and resolve only header symlinks; libam native branch stays off.
for p in (ROOT/'navy-apps/libs/libam/include').iterdir():
 (WORK/'aminc').mkdir(exist_ok=True);shutil.copy2(p,WORK/'aminc'/p.name,follow_symlinks=True)
shutil.copy2(ROOT/'navy-apps/libs/libam/src/cte.c',WORK/'cte.c')
shutil.copy2(ROOT/'navy-apps/libs/libam/src/trm.cpp',WORK/'trm.cpp')
run('libam-rv-cte',['/usr/bin/riscv64-linux-gnu-gcc','-O2','-march=rv64g','-I'+str(inc),'-I'+str(WORK/'aminc'),'-c',WORK/'cte.c','-o',WORK/'cte-rv.o'])
run('libam-rv-trm',['/usr/bin/riscv64-linux-gnu-g++','-O2','-march=rv64g','-fno-exceptions','-fno-rtti','-I'+str(inc),'-I'+str(WORK/'aminc'),'-c',WORK/'trm.cpp','-o',WORK/'trm-rv.o'])
run('libam-rv-ioe',['/usr/bin/riscv64-linux-gnu-gcc','-O2','-march=rv64g','-I'+str(inc),'-I'+str(WORK/'aminc'),'-I'+str(ROOT/'navy-apps/libs/libndl/include'),'-c',ROOT/'navy-apps/libs/libam/src/ioe.c','-o',WORK/'ioe-rv.o'])
# Host trm uses its existing non-RISC-V write branch; its output/halt functions are dead-stripped.
if run('libam-host-trm',['/usr/bin/g++','-O2','-fno-exceptions','-fno-rtti','-ffunction-sections','-fdata-sections','-I'+str(WORK/'aminc'),'-c',WORK/'trm.cpp','-o',WORK/'trm-host.o'])==0:
 if run('libam-host-build',['/usr/bin/gcc','-O2','-ffunction-sections','-fdata-sections','-I'+str(WORK/'aminc'),WORK/'cte.c',HERE/'libam-probe.c',WORK/'trm-host.o','-Wl,--gc-sections','-o',WORK/'libam'])==0:run('libam-host',[WORK/'libam'])
# Execute only two original loop recipes in an independent Makefile; fake submake does no work.
mk=(ROOT/'navy-apps/Makefile').read_text()
libs=mk.split('libs:\n',1)[1].split('\n\n',1)[0]
fsimg=mk.split('fsimg: $(addprefix apps/, $(APPS)) $(addprefix tests/, $(TESTS))\n',1)[1].split('\n\n',1)[0]
fake=WORK/'fake-make';fake.write_text('#!/bin/sh\ncase "$*" in *broken*) exit 7;; *) exit 0;; esac\n');fake.chmod(0o700)
(WORK/'Makefile').write_text('LIBS=broken good\nNAVY_HOME='+str(WORK)+'\nMAKE='+str(fake)+'\n.PHONY: libs fsimg broken good\nlibs:\n'+libs+'\nfsimg: broken good\n'+fsimg+'\nbroken good:\n\t@:\n')
run('libs-swallowed-failure',['make','-f',WORK/'Makefile','libs'])
run('fsimg-swallowed-failure',['make','-f',WORK/'Makefile','fsimg'])
(OUT/'transformations.json').write_text(json.dumps(transformations,indent=2)+'\n')
for p in [WORK/'syscall.c',WORK/'Makefile',fake]:shutil.copy2(p,OUT/p.name)
(OUT/'manifest.json').write_text(json.dumps({'work':str(WORK),'outputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in WORK.iterdir() if p.is_file()},'limitations':['Host only, mocked ecall and fake submake; no guest/production make','RV64 units compiled without executing them']},indent=2)+'\n')
print(OUT);print('unexpected',[(x['name'],x['exit']) for x in records if x['exit']!=x['expected_exit']])
