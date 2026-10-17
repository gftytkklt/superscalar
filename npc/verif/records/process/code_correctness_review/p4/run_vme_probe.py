#!/usr/bin/env python3
"""Host observation of actual AM VME C with only satp CSR accesses substituted."""
import hashlib,json,pathlib,re,subprocess,tempfile
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[5]
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=pathlib.Path);args=parser.parse_args()
if args.output:P=args.output.resolve()
P.mkdir(parents=True,exist_ok=True)
if (P/'vme-results.json').exists():raise SystemExit('Refusing to overwrite VME evidence')
w=pathlib.Path(tempfile.mkdtemp(prefix='ccr-p4-vme-')); commands=[]
src=ROOT/'abstract-machine/am/src/riscv/nemu/vme.c';text=src.read_text()
text=text.replace('asm volatile("csrw satp, %0" : : "r"(mode | ((uintptr_t)pdir >> 12)));','mock_satp = mode | ((uintptr_t)pdir >> 12);')
text=text.replace('asm volatile("csrr %0, satp" : "=r"(satp));','satp = mock_satp;')
assert 'asm volatile' not in text
(w/'vme.c').write_text('static unsigned long mock_satp;\n'+text)
probe='''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vme.c"
char _pmem_start;
void halt(int code){exit(code);}
static int frees;
static void *alloc_page(int n){void *p=aligned_alloc(4096,n); if(!p) abort();memset(p,0,n);return p;}
static void release_page(void *p){frees++;free(p);}
int main(void){
 pgalloc_usr=alloc_page;pgfree_usr=release_page;vme_enable=1;
 mock_satp=(8ul<<60)|(0x81234000ul>>12);
 Context c={0};__am_get_cur_as(&c);printf("zero_frame_pdir=%p expected_snapshot=0x81234000\\n",c.pdir);
 c.pdir=(void*)1;__am_get_cur_as(&c);printf("nonzero_frame_pdir=%p\\n",c.pdir);
 AddrSpace as={.ptr=alloc_page(4096)};map(&as,(void*)0x40000000,(void*)0x83000000,MMAP_READ);
 PTE *root=as.ptr,*mid=(void*)((root[1]>>10)<<12),*leaf=(void*)((mid[0]>>10)<<12);
 printf("read_only_leaf_flags=0x%lx\\n",leaf[0]&1023);
 map(&as,(void*)0x40000000,NULL,MMAP_NONE);printf("null_none_leaf=0x%lx\\n",leaf[0]);
 unprotect(&as);printf("unprotect_free_calls=%d ptr=%p\\n",frees,as.ptr);
 return 0;
}
'''
(w/'probe.c').write_text(probe);(P/'vme-probe.c').write_text(probe)
# Use original headers read-only; no writes to original source or build directories.
args=['/usr/bin/gcc','-std=gnu11','-O2','-D__riscv_xlen=64','-D__riscv=1','-DARCH_H="arch/riscv.h"','-DISA_H="riscv/riscv.h"']
args += ['-I'+str(ROOT/'abstract-machine'/d) for d in ['am/include','am/src','am/src/platform/nemu/include','klib/include']]
args += ['probe.c','-o','probe']
for name,argv in [('vme-host-compile',args),('vme-host-observation',[str(w/'probe')])]:
 p=subprocess.run(argv,cwd=w,text=True,capture_output=True,timeout=30);(P/(name+'.log')).write_text(p.stdout+p.stderr)
 commands.append({'argv':argv,'cwd':str(w),'exit_code':p.returncode,'log':name+'.log'});assert p.returncode==0
(P/'vme-results.json').write_text(json.dumps({'date':'2026-10-17','source':str(src.relative_to(ROOT)),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'transformed_sha256':hashlib.sha256((w/'vme.c').read_bytes()).hexdigest(),'workdir':str(w),'commands':commands,'limits':'Only two CSR access expressions replaced by mock_satp; static internal allocator/enabled state set by harness. Host LP64, no RV64 MMU/trap execution. Mapping permission/unmap/free outputs are observations, not automatically adjudicated against conflicting teaching contracts.'},indent=2)+'\n')
print((P/'vme-host-observation.log').read_text())
if __name__=='__main__':pass
