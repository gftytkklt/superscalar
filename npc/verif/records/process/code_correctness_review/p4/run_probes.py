#!/usr/bin/env python3
"""CCR-P4 isolated compiler/linker probes. No project make, guest, install or Git hook."""
import hashlib, json, os, pathlib, shutil, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[6]
OUT=ROOT/'npc/verif/records/process/code_correctness_review/p4'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 global OUT
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=pathlib.Path)
 args=parser.parse_args()
 if args.output: OUT=args.output.resolve()
 OUT.mkdir(parents=True,exist_ok=True)
 if (OUT/'probe-results.json').exists(): raise SystemExit('Refusing to overwrite evidence; use --output NEW_DIRECTORY')
 w=pathlib.Path(tempfile.mkdtemp(prefix='ccr-p4-')); logs=[]
 env=os.environ.copy();env.update({'CCACHE_DISABLE':'1','AM_HOME':str(w/'am'),'NPC_HOME':str(w/'npc'),'NEMU_HOME':str(w/'nemu')})
 def run(args,name,ok=True):
  r=subprocess.run(list(map(str,args)),cwd=w,env=env,text=True,capture_output=True,timeout=30)
  log=r.stdout+r.stderr;(OUT/(name+'.log')).write_text(log)
  logs.append({'name':name,'argv':list(map(str,args)),'cwd':str(w),'exit_code':r.returncode,'log':name+'.log'})
  if ok and r.returncode: raise RuntimeError(name+': '+log)
  return log
 sources={}
 for d in ['am/include','am/src/riscv','am/src/platform/nemu','am/src/platform/dummy','klib/include','scripts']:
  # Only files, no build/Git metadata; unused ISA source is copied as compiler include support, not reviewed.
  src=ROOT/'abstract-machine'/d;dst=w/'am'/d;shutil.copytree(src,dst,symlinks=False)
  for p in src.rglob('*'):
   if p.is_file():sources[str(p.relative_to(ROOT))]=sha(p)
 cc='/usr/bin/riscv64-linux-gnu-gcc';ld='/usr/bin/riscv64-linux-gnu-ld';obj='/usr/bin/riscv64-linux-gnu-objdump';re='/usr/bin/riscv64-linux-gnu-readelf'
 flags=['-march=rv64g','-mcmodel=medany','-mstrict-align','-fno-pic','-O2','-fno-builtin','-fno-stack-protector','-fno-asynchronous-unwind-tables','-ffunction-sections','-fdata-sections','-DARCH_H="arch/riscv.h"','-DISA_H="riscv/riscv.h"']
 inc=['-I'+str(w/'am'/d) for d in ['am/include','am/src','am/src/platform/nemu/include','klib/include']]
 run([cc,'--version'],'compiler-version');run([ld,'--version'],'linker-version')
 run([cc,*flags,'-Q','--help=target'],'compiler-target')
 layout='''#include <am.h>
_Static_assert(sizeof(uintptr_t)==8,"RV64 word");
_Static_assert(sizeof(Context)==288,"frame");
_Static_assert(offsetof(Context,pdir)==0,"pdir/x0");
_Static_assert(offsetof(Context,gpr[2])==16,"sp");
_Static_assert(offsetof(Context,mcause)==256,"cause");
_Static_assert(offsetof(Context,mstatus)==264,"status");
_Static_assert(offsetof(Context,mepc)==272,"epc");
_Static_assert(offsetof(Context,np)==280,"np");
_Static_assert(sizeof(Context)%16==0,"alignment preservation");
const unsigned long layout[]={sizeof(Context),_Alignof(Context),offsetof(Context,gpr[2]),offsetof(Context,mcause),offsetof(Context,mstatus),offsetof(Context,mepc),offsetof(Context,np)};
'''
 (w/'layout.c').write_text(layout);(OUT/'layout.c').write_text(layout)
 run([cc,*flags,*inc,'-c','layout.c','-o','layout.o'],'layout-compile')
 run([re,'-h','-A','layout.o'],'layout-elf')
 names={}
 for f in ['nemu/start.S','nemu/trap.S','nemu/cte.c','nemu/vme.c','npc/start.S','npc/start_sram.S','npc/start_fsbl.S','npc/trap.S','npc/cte.c','npc/boot_sram.c','npc/fsbl.c','npc/ssbl.c','npc/trm.c','npc/vme.c','npc/mpe.c']:
  out=f.replace('/','-').replace('.','-')+'.o';names[f]=out
  run([cc,*flags,*inc,'-Wno-main','-c',w/'am/am/src/riscv'/f,'-o',out],'compile-'+out)
  if f.endswith('trap.S') or f.endswith('cte.c') or f in ['npc/boot_sram.c','npc/fsbl.c','npc/ssbl.c']:
   run([obj,'-dr',out],'disasm-'+out)
 fixture='''.section .text._trm_init,"ax"
.global _trm_init
_trm_init:
 la a0, test_bss
 la a1, test_data
 ret
.section .data,"aw"
.global test_data
test_data: .byte 7
.section .bss,"aw",@nobits
.global test_bss
test_bss: .space 1
'''
 (w/'fixture.S').write_text(fixture);(OUT/'fixture.S').write_text(fixture)
 run([cc,*flags,'-c','fixture.S','-o','fixture.o'],'fixture-compile')
 results=[]
 variants=[('nemu','linker.ld','nemu/start.S'),('xip','linker-soc.ld','npc/start.S'),('sram','linker-sram.ld','npc/start_sram.S'),('psram','linker-psram.ld','npc/start_sram.S'),('psram-ssbl','linker-psram-ssbl.ld','npc/start_fsbl.S'),('sdram','linker-sdram.ld','npc/start_sram.S'),('sdram-heap','linker-sdram-heap.ld','npc/start.S'),('sdram-rt','linker-sdram-rt.ld','npc/start_sram.S')]
 for mode,script,start in variants:
  def link(tag,fixtureobj,heap='0x8000'):
   args=[ld,'-melf64lriscv','--gc-sections','-e','_start','-T',w/'am/scripts'/script,'--defsym=_pmem_start='+('0x80000000' if mode=='nemu' else '0x30000000'),'--defsym=_entry_offset=0','--defsym=_sram_start=0x0f000000','--defsym=_stack_offt=0x1800','--defsym=_heap_size='+heap,'-o',tag+'.elf',names[start],fixtureobj]
   if mode in ['sram','psram','sdram','sdram-rt']:args += [names['npc/boot_sram.c']]
   if mode=='psram-ssbl':args += [names['npc/fsbl.c'],names['npc/ssbl.c']]
   run(args,tag+'-link');s=run([re,'-h','-SW','-lW','-sW',tag+'.elf'],tag+'-elf')
   sy={}
   for line in s.splitlines():
    fields=line.split()
    if len(fields)==8 and fields[0].endswith(':'):
     try:sy[fields[-1]]=int(fields[1],16)
     except ValueError:pass
   run(['/usr/bin/riscv64-linux-gnu-objcopy','-S','--set-section-flags','.bss=alloc,contents','-O','binary',tag+'.elf',tag+'.bin'],tag+'-objcopy')
   results.append({'name':tag,'script':script,'symbols':sy,'elf_sha256':sha(w/(tag+'.elf')),'bin_sha256':sha(w/(tag+'.bin')),'bin_size':(w/(tag+'.bin')).stat().st_size})
  link(mode,'fixture.o')
  if mode in ['xip','sram','sdram-heap']:
   (w/'large.S').write_text(fixture.replace('.space 1','.space 7168'))
   run([cc,*flags,'-c','large.S','-o','large.o'],mode+'-large-compile');link(mode+'-stack-overlap','large.o')
  if mode in ['xip','sdram','sdram-heap']:link(mode+'-oversize-heap','fixture.o','0x10000000')
 # Actual selected dummy functions, unmodified, linked to a host observation harness.
 dummy='''#include <am.h>
#include <stdio.h>
static int called;
static void entry(void){called++;}
int main(void){int v=7; int old=atomic_xchg(&v,11); AddrSpace as={.pgsize=123,.ptr=(void*)456}; Area st={0};
 printf("mpe_init=%d called=%d cpus=%d cpu=%d old=%d value=%d\\n",mpe_init(entry),called,cpu_count(),cpu_current(),old,v);
 printf("vme_init=%d ",vme_init(0,0));protect(&as);map(&as,0,0,0);unprotect(&as);printf("pgsize=%d ptr=%p ucontext=%p\\n",as.pgsize,as.ptr,(void*)ucontext(&as,st,0));return 0;}
'''
 (w/'dummy.c').write_text(dummy);(OUT/'dummy.c').write_text(dummy)
 run(['/usr/bin/gcc','-O2',*inc,'-DARCH_H="arch/riscv.h"','dummy.c',w/'am/am/src/platform/dummy/mpe.c',w/'am/am/src/platform/dummy/vme.c','-o','dummy'],'dummy-compile')
 run([w/'dummy'],'dummy-observation')
 record={'date':'2026-10-17','phase':'CCR-P4','workdir':str(w),'environment_overrides':{k:env[k] for k in ['CCACHE_DISABLE','AM_HOME','NPC_HOME','NEMU_HOME']},'sources':sources,'commands':logs,'link_results':results,'limits':'Compiler/linker and host dummy observations only; fixture _trm_init is not real runtime; no RV64 guest/NPC hardware execution; no project make or production writes.'}
 (OUT/'probe-results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'workdir':str(w),'commands':len(logs),'links':len(results),'result':'recorded'}))
if __name__=='__main__':main()
