#!/usr/bin/env python3
"""Direct compilers only; no make, install, original build writes or guest run."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
OUT=Path(tempfile.mkdtemp(prefix='ccr-p5-'))
RESULT=[]
COPIED=[]
def cp(src,dst=None):
    src=ROOT/src; dst=OUT/(dst or str(src.relative_to(ROOT)))
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    COPIED.append({'source':str(src.relative_to(ROOT)),'copy':str(dst),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
    return dst
def run(name,argv,expect=0):
    try:
        p=subprocess.run(list(map(str,argv)),cwd=OUT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30,env={**os.environ,'CCACHE_DISABLE':'1','ASAN_OPTIONS':'detect_leaks=0:detect_stack_use_after_return=1','UBSAN_OPTIONS':'halt_on_error=1'})
        rc,txt=p.returncode,p.stdout
    except subprocess.TimeoutExpired as e:rc,txt=124,str(e)
    (HERE/(name+'.log')).write_text(txt)
    RESULT.append({'name':name,'argv':list(map(str,argv)),'cwd':str(OUT),'exit':rc,'expected_exit':expect,'expected_exit_match': rc==expect,'log':name+'.log'})
    return rc

for p in (ROOT/'abstract-machine/am/include').rglob('*.h'):cp(str(p.relative_to(ROOT)))
for p in (ROOT/'abstract-machine/klib').rglob('*'):
    if p.is_file() and '/build/' not in str(p):cp(str(p.relative_to(ROOT)))
inc=['-I'+str(OUT/'abstract-machine/am/include'),'-I'+str(OUT/'abstract-machine/klib/include'),'-DARCH_H="arch/riscv.h"']
common=['-O2','-std=gnu11','-fno-builtin','-funsigned-char',*inc]
names='strlen strcpy strncpy strcat strcmp strncmp memset memmove memcpy memcmp rand srand abs atoi malloc free printf sprintf snprintf vsprintf vsnprintf'.split()
rename=['-D'+n+'=ccr_'+n for n in names]
san=['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-no-pie']
run('host-version',['gcc','--version']);run('rv-version',['riscv64-linux-gnu-gcc','--version'])
for stem in ['string','stdio','stdlib','int64']:
    run('host-'+stem,['gcc',*common,*san,*rename,'-c',OUT/f'abstract-machine/klib/src/{stem}.c','-o',OUT/(stem+'.o')])
cp(str((HERE/'klib-probe.c').relative_to(ROOT)),'klib-probe.c')
run('host-link',['gcc',*common,*san,OUT/'klib-probe.c',*[OUT/(n+'.o') for n in ['string','stdio','stdlib','int64']],'-o',OUT/'klib-probe'])
for scenario,expect in [('strncpy-pad',0),('strncpy-bound',1),('format',0),('format-negative',1),('format-octal',1),('atoi',0),('malloc',0),('memory',0),('move-zero',1),('int64',0),('int64-min',1)]:run(scenario,[OUT/'klib-probe',scenario],expect)

rv=['riscv64-linux-gnu-gcc','-O2','-std=gnu11','-fno-builtin','-fno-stack-protector','-march=rv64g','-mcmodel=medany','-mstrict-align',*inc]
rvsrc=[p for p in (ROOT/'abstract-machine/am/src/platform/nemu/ioe').glob('*.c')]+[ROOT/f'abstract-machine/am/src/riscv/npc/{n}.c' for n in ['ioe','input','video','timer']]+[p for p in (ROOT/'abstract-machine/am/src/riscv/npc/libgcc').glob('*') if p.suffix in ['.c','.S']]+list((ROOT/'abstract-machine/klib/src').glob('*.c'))
for p in (ROOT/'abstract-machine/am/src/riscv/npc/libgcc').glob('*.h'):cp(str(p.relative_to(ROOT)))
for p in [ROOT/'abstract-machine/am/src/platform/nemu/include/nemu.h',ROOT/'abstract-machine/am/src/riscv/riscv.h']:cp(str(p.relative_to(ROOT)))
for n,p in enumerate(rvsrc):
    dst=cp(str(p.relative_to(ROOT)));obj=OUT/f'rv-{n}-{p.stem}.o'
    run(f'rv-{n}-{p.stem}',[*rv,'-Wall','-Werror','-D__riscv=1','-DISA_H="riscv/riscv.h"','-I'+str(OUT/'abstract-machine/am/src'),'-I'+str(OUT/'abstract-machine/am/src/platform/nemu/include'),'-c',dst,'-o',obj])
    if p.stem in ['cpp','timer','ashldi3','multi3','div','muldi3']:run(f'disasm-{n}-{p.stem}',['riscv64-linux-gnu-objdump','-dr',obj])

mock=OUT/'mock';mock.mkdir()
(mock/'nemu.h').write_text('''#include <stdint.h>
#define AUDIO_ADDR 0xa0000200UL
#define AUDIO_SBUF_ADDR 0xa1200000UL
#define DISK_ADDR 0xa0000300UL
#define RTC_ADDR 0xa0000048UL
#define VGACTL_ADDR 0xa0000100UL
#define FB_ADDR 0xa1000000UL
#define KBD_ADDR 0xa0000060UL
uint32_t mock_inl(uintptr_t); uint16_t mock_inw(uintptr_t);
void mock_outl(uintptr_t,uint32_t); void mock_outb(uintptr_t,uint8_t);
#define inl mock_inl
#define inw mock_inw
#define outl mock_outl
#define outb mock_outb
''')
cp(str((HERE/'device-probe.c').relative_to(ROOT)),'device-probe.c')
devsrc=[OUT/('abstract-machine/am/src/platform/nemu/ioe/'+n+'.c') for n in ['gpu','audio','disk','timer','input','ioe']]
run('device-link',['gcc',*common,'-I'+str(mock),OUT/'device-probe.c',*devsrc,'-o',OUT/'device-probe'])
for s,e in [('gpu',0),('timer',0),('input',0),('disk',0),('audio',0),('audio-oversize',42),('ioe',0)]:run('device-'+s,[OUT/'device-probe',s],e)

res={'phase':'CCR-P5','date':'2026-10-17','out':str(OUT),'commands':RESULT,'copied':COPIED,'environment':{'CCACHE_DISABLE':'1','ASAN_OPTIONS':'detect_leaks=0:detect_stack_use_after_return=1','UBSAN_OPTIONS':'halt_on_error=1'},'output_hashes':{str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()},'limit':'LP64 host with unsigned plain char; real source under renamed klib exports or MMIO-only header substitution. Cross compile is not guest/hardware execution.'}
(HERE/'probe-results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'out':str(OUT),'commands':len(RESULT),'unexpected':[r for r in RESULT if not r['expected_exit_match']]},ensure_ascii=False,indent=2))
