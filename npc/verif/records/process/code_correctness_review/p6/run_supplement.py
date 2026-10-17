#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,tempfile,os,hashlib,shutil
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());O=Path(tempfile.mkdtemp(prefix='ccr-p6-supp-'));cmds=[]
def run(n,a,e=0):
 p=subprocess.run(list(map(str,a)),cwd=O,env={**os.environ,'CCACHE_DISABLE':'1','ASAN_OPTIONS':'detect_leaks=0','UBSAN_OPTIONS':'halt_on_error=1'},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=30);(H/(n+'.log')).write_text(p.stdout);cmds.append({'name':n,'argv':list(map(str,a)),'cwd':str(O),'exit':p.returncode,'expected_exit':e,'log':n+'.log'});return p.returncode
base=Path(json.loads((H/'probe-results.json').read_text())['out'])
shutil.copytree(base/'nanos-lite',O/'nanos-lite');shutil.copytree(base/'abstract-machine',O/'abstract-machine')
s=(H/'loader-probe.c').read_text().replace('"/bin/pal","--skip"','"/bin/nterm","--skip"');(O/'loader-probe.c').write_text(s)
flags=['-std=gnu11','-O1','-g','-fno-builtin','-funsigned-char','-DARCH_H="arch/riscv.h"',*[ '-I'+str(O/p) for p in ['.','nanos-lite/include','abstract-machine/am/include','abstract-machine/klib/include']]]
run('loader-misaligned-build',['gcc',*flags,'-fsanitize=address,undefined','-fno-sanitize-recover=all','-no-pie',O/'loader-probe.c','-o',O/'loader'])
run('loader-misaligned',[O/'loader','alignment'],1)
# Original resources.S; tiny fixture isolates placement independently of known capacity overflow.
(O/'resources').mkdir();(O/'build').mkdir();shutil.copy2(R/'nanos-lite/resources/logo.txt',O/'resources/logo.txt');(O/'build/ramdisk.img').write_bytes(b'12345678');(O/'start.S').write_text('.section entry,"ax"\n.globl _start\n_start: j _start\n.section .data\n.word 0x12345678\n')
run('resource-compile',['riscv64-linux-gnu-gcc','-march=rv64g','-DKERNEL_EMBED_RAMDISK','-c',R/'nanos-lite/src/resources.S','-o',O/'resources.o'])
run('layout-start',['riscv64-linux-gnu-gcc','-march=rv64g','-c',O/'start.S','-o',O/'start.o'])
for name in ['linker-soc','linker-psram','linker-psram-ssbl','linker-sdram','linker-sdram-heap','linker-sram']:
 rc=run(name+'-link',['riscv64-linux-gnu-ld','-m','elf64lriscv','-T',R/f'abstract-machine/scripts/{name}.ld','--defsym=_sram_start=0xf000000','--defsym=_stack_offt=0x2000','--defsym=_heap_size=0x8000',O/'start.o',O/'resources.o','-o',O/(name+'.elf')])
 if not rc:run(name+'-sections',['riscv64-linux-gnu-objdump','-h',O/(name+'.elf')]);run(name+'-symbols',['riscv64-linux-gnu-nm','-n',O/(name+'.elf')])
res={'phase':'CCR-P6','date':'2026-10-17','out':str(O),'commands':cmds,'output_hashes':{str(p.relative_to(O)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.rglob('*') if p.is_file()},'limits':'Modified harness arguments only; original resources.S with 8-byte isolated ramdisk; links test orphan placement, not real kernel capacity or execution.'}
(H/'supplement-results.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({'out':str(O),'commands':len(cmds),'unexpected':[x for x in cmds if x['exit']!=x['expected_exit']]},indent=2))
