#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,subprocess,tempfile,os,shutil
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists())
T=Path(tempfile.mkdtemp(prefix='ccr-p5-final-'));commands=[]
def run(n,a,e=0,env=None):
 p=subprocess.run(list(map(str,a)),cwd=T,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30,env={**os.environ,'CCACHE_DISABLE':'1',**(env or {})})
 (H/(n+'.log')).write_text(p.stdout);commands.append({'name':n,'argv':list(map(str,a)),'cwd':str(T),'exit':p.returncode,'expected_exit':e,'match':p.returncode==e,'env_overrides':env,'log':n+'.log'})
base=Path(json.loads((H/'probe-results.json').read_text())['out'])
inc=['-I'+str(base/'abstract-machine/am/include'),'-I'+str(base/'abstract-machine/klib/include'),'-DARCH_H="arch/riscv.h"']
(T/'layout.c').write_text('''#include <am.h>
#include <stddef.h>
#define S(t,n) _Static_assert(sizeof(t)==n,#t)
#define O(t,m,n) _Static_assert(offsetof(t,m)==n,#t "." #m)
S(Area,16);S(AM_UART_RX_T,1);S(AM_TIMER_CONFIG_T,2);S(AM_TIMER_RTC_T,24);S(AM_TIMER_UPTIME_T,8);
S(AM_INPUT_KEYBRD_T,8);O(AM_INPUT_KEYBRD_T,keycode,4);
S(AM_GPU_CONFIG_T,16);O(AM_GPU_CONFIG_T,width,4);S(AM_GPU_FBDRAW_T,32);O(AM_GPU_FBDRAW_T,pixels,8);O(AM_GPU_FBDRAW_T,sync,24);
S(AM_AUDIO_CONFIG_T,8);S(AM_AUDIO_CTRL_T,12);S(AM_AUDIO_STATUS_T,4);S(AM_AUDIO_PLAY_T,16);
S(AM_DISK_CONFIG_T,12);S(AM_DISK_STATUS_T,1);S(AM_DISK_BLKIO_T,24);O(AM_DISK_BLKIO_T,buf,8);O(AM_DISK_BLKIO_T,blkno,16);
S(struct gpu_texturedesc,8);S(struct gpu_canvas,26);O(struct gpu_canvas,sibling,14);O(struct gpu_canvas,texture,18);
''')
run('ioe-layout',['riscv64-linux-gnu-gcc','-std=gnu11','-march=rv64g',*inc,'-c',T/'layout.c','-o',T/'layout.o'])
(T/'guard.cc').write_text('extern int make(); int &f(){static int n=make();return n;}')
run('cpp-guard-compile',['riscv64-linux-gnu-g++','-O2','-std=c++17','-march=rv64g','-ffreestanding','-fno-rtti','-fno-exceptions','-c',T/'guard.cc','-o',T/'guard.o'])
run('cpp-guard-disasm',['riscv64-linux-gnu-objdump','-dr',T/'guard.o'])
run('cpp-stub-disasm',['riscv64-linux-gnu-objdump','-dr',next(base.glob('rv-*-cpp.o'))])
rtincs=[l.split('CFLAGS += ')[1] for l in (R/'rt/bsp/abstract-machine/files.mk').read_text().splitlines() if l.startswith('CFLAGS += -I/') ]
run('interrupt-real-declarations',['gcc','-O2','-std=gnu11','-fno-builtin','-DARCH_H="arch/riscv.h"','-I'+str(R/'rt/include'),'-I'+str(R/'rt/bsp/abstract-machine'),'-I'+str(R/'rt/bsp/abstract-machine/include'),*inc,*rtincs,'-include',R/'rt/include/rthw.h','-c',R/'rt/bsp/abstract-machine/src/interrupt.c','-o',T/'bad-irq.o'],1)
for key,line in [('fail','[dummy] ***FAIL***\n'),('pass','[dummy] PASS\n')]:
 (T/'.result').write_text(line)
 run('cpu-oracle-'+key,['sh','-c','grep -q "FAIL" .result | grep -v "wrong\\]"; FAIL=$?; rm .result; test $FAIL -ne 0'])

# Exercise only the integration generator's status propagation with fake tools/objects.
am=T/'mock-work/abstract-machine';kern=am.parent/'am-kernels';arch='riscv64-npc'
for n in ['am','klib']:
 p=am/n/'build';p.mkdir(parents=True);(p/f'{n}-{arch}.a').write_bytes(b'mock archive; fake nm below\n')
for n in ['kernels/hello','benchmarks/microbench','kernels/typing-game','kernels/snake']:
 p=kern/n/'build'/arch;p.mkdir(parents=True);(p/'stale.o').write_bytes(b'stale mock object')
bin=T/'mock-bin';bin.mkdir()
for n,body in [('make','exit 7'),('riscv64-linux-gnu-nm','echo putch'),('riscv64-linux-gnu-objcopy','exit 0')]:
 p=bin/n;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o700)
(T/'build'/arch).mkdir(parents=True)
run('generator-failed-make',['python3',R/'rt/bsp/abstract-machine/integrate-am-apps.py','ARCH='+arch,'CROSS_COMPILE=riscv64-linux-gnu-'],0,{'AM_HOME':str(am),'PATH':str(bin)+':'+os.environ['PATH']})
(H/'generator-failed-make-output.mk').write_bytes((T/'build'/arch/'am-apps.mk').read_bytes())
result={'date':'2026-10-17','phase':'CCR-P5','out':str(T),'commands':commands,'generator_fixture':'Four make calls return 7, stale mock .o files already exist, nm/objcopy are explicitly fake; this tests status propagation, not compilation.','output_hashes':{str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*') if p.is_file()}}
(H/'final-probe-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'out':str(T),'commands':len(commands),'unexpected':[c for c in commands if not c['match']]},ensure_ascii=False))
