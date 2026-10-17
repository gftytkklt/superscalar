#!/usr/bin/env python3
"""Isolated CCR-P7 evidence. No project make, network, installation or guest.
Re-run creates new /tmp directories; never overwrites frozen evidence.
"""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
OUT = Path(tempfile.mkdtemp(prefix='ccr-p7-evidence-'))
WORK = Path(tempfile.mkdtemp(prefix='ccr-p7-work-'))
env = dict(os.environ, CCACHE_DISABLE='1')
records = []
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(name, argv, expected=0):
    r = subprocess.run(list(map(str, argv)), cwd=WORK, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)
    log = OUT / (name + '.log')
    log.write_bytes(r.stdout)
    records.append(dict(name=name, argv=list(map(str, argv)), cwd=str(WORK),
                        env_overrides={'CCACHE_DISABLE':'1'}, exit=r.returncode,
                        expected_exit=expected, log=str(log), log_sha256=sha(log)))
    (OUT/'results.json').write_text(json.dumps(records, indent=2)+'\n')
    return r.returncode

for component in ['libc', 'libos']:
    src = ROOT/'navy-apps/libs'/component
    for folder in ['src', 'include']:
        if (src/folder).exists(): shutil.copytree(src/folder, WORK/component/folder)
inc = WORK/'libc/include'
flags = ['-O2','-fno-builtin','-fno-stack-protector','-fno-asynchronous-unwind-tables',
         '-fno-pic','-march=rv64g','-mcmodel=medany','-D__NAVY__','-D__ISA_RISCV64__',
         '-U_FORTIFY_SOURCE','-I'+str(inc)]
gcc='/usr/bin/riscv64-linux-gnu-gcc'
run('rv-version',[gcc,'--version'])
run('host-version',['/usr/bin/gcc','--version'])
run('rv-abi',[gcc,*flags,'-std=gnu11','-S',HERE/'abi-probe.c','-o',WORK/'abi.s'])
run('rv-macros',[gcc,*flags,'-dM','-E',HERE/'abi-probe.c'])
units = ['libos/src/syscall.c','libos/src/crt0/crt0.c','libos/src/crt0/start.S']
units += ['libc/src/'+s for s in [
 'platform/cpp.cpp','platform/setjmp/riscv.S','misc/init.c','misc/fini.c',
 'syscalls/sysopen.c','syscalls/sysread.c','syscalls/syswrite.c','syscalls/syslseek.c',
 'syscalls/sysexecve.c','reent/openr.c','reent/readr.c','reent/writer.c','reent/execr.c',
 'reent/sbrkr.c','errno/errno.c','stdlib/mallocr.c','stdlib/callocr.c','stdlib/freer.c',
 'stdlib/reallocr.c','stdlib/setenv_r.c','stdlib/getenv_r.c','stdlib/exit.c',
 'stdlib/__atexit.c','stdlib/__call_atexit.c','stdio/fwrite.c','stdio/fread.c',
 'stdio/fflush.c','stdio/fopen.c','stdio/fclose.c','stdio/findfp.c','stdio/fseeko.c',
 'stdio/stdio.c','stdio/makebuf.c','stdio/vfprintf.c','stdio/vfscanf.c',
 'posix/execv.c','posix/execvp.c','posix/execl.c','posix/execle.c','posix/execlp.c']]
for i,u in enumerate(units):
    cxx=u.endswith('.cpp'); cc='/usr/bin/riscv64-linux-gnu-g++' if cxx else gcc
    extra=['-DNO_FLOATING_POINT','-DHAVE_INITFINI_ARRAY'] if u.startswith('libc/') else []
    extra += ['-std=c++17','-ffreestanding','-fno-rtti','-fno-exceptions'] if cxx else ([] if u.endswith('.S') else ['-std=gnu11'])
    run('unit-'+str(i),[cc,*flags,*extra,'-c',WORK/u,'-o',WORK/(str(i)+'.o')])
run('rv-libos-disasm',['riscv64-linux-gnu-objdump','-dr',WORK/'0.o'])
run('rv-start-disasm',['riscv64-linux-gnu-objdump','-dr',WORK/'2.o'])
run('rv-setjmp-disasm',['riscv64-linux-gnu-objdump','-dr',WORK/'4.o'])
# Same translation unit inlining probe: original syscall source unmodified.
probe = WORK/'libos/src/visibility.c'
probe.write_text('#include "syscall.c"\nlong probe(void) { struct timeval t={123,456}; _gettimeofday(&t, 0); return t.tv_sec; }\n')
run('rv-memory-visibility',[gcc,*flags,'-std=gnu11','-S',probe,'-o',WORK/'visibility.s'])
host=['/usr/bin/gcc','-O2','-std=gnu11','-D__riscv','-fno-builtin','-ffunction-sections',
      '-fdata-sections','-I'+str(inc),'-Wl,--gc-sections']
renames=['-Dfwrite=p7_fwrite','-D_fwrite_r=p7_fwrite_r']
if run('fwrite-build',[*host,*renames,'-fsanitize=undefined','-fno-sanitize-recover=all',
                      WORK/'libc/src/stdio/fwrite.c',HERE/'fwrite-probe.c','-o',WORK/'fwrite'])==0:
    run('fwrite-count-zero',[WORK/'fwrite'])
    run('fwrite-size-zero',[WORK/'fwrite','zero'],1)
if run('calloc-build',[*host,WORK/'libc/src/stdlib/callocr.c',HERE/'calloc-probe.c',
                      '-o',WORK/'calloc'])==0:
    run('calloc-overflow',[WORK/'calloc'])
for f in ['abi.s','visibility.s']:
    if (WORK/f).exists(): shutil.copy2(WORK/f,OUT/f)
sources={str(p.relative_to(ROOT)):sha(p) for p in ROOT.joinpath('navy-apps/libs/libc').rglob('*')
         if p.is_file() and any(z in p.parts for z in ['src','include']) and 'build' not in p.parts}
sources.update({str(p.relative_to(ROOT)):sha(p) for p in ROOT.joinpath('navy-apps/libs/libos/src').rglob('*') if p.is_file()})
(OUT/'manifest.json').write_text(json.dumps(dict(work=str(WORK),source_hashes=sources,
    outputs={str(p):sha(p) for p in WORK.iterdir() if p.is_file()},
    limitations=['No guest execution','Host probes use LP64/newlib headers and external stubs','Only selected units compiled; not a complete product build']),indent=2)+'\n')
print(OUT)
print('commands',len(records),'unexpected',[(x['name'],x['exit']) for x in records if x['exit']!=x['expected_exit']])
