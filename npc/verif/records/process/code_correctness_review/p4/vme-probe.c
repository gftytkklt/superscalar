#include <stdio.h>
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
 Context c={0};__am_get_cur_as(&c);printf("zero_frame_pdir=%p expected_snapshot=0x81234000\n",c.pdir);
 c.pdir=(void*)1;__am_get_cur_as(&c);printf("nonzero_frame_pdir=%p\n",c.pdir);
 AddrSpace as={.ptr=alloc_page(4096)};map(&as,(void*)0x40000000,(void*)0x83000000,MMAP_READ);
 PTE *root=as.ptr,*mid=(void*)((root[1]>>10)<<12),*leaf=(void*)((mid[0]>>10)<<12);
 printf("read_only_leaf_flags=0x%lx\n",leaf[0]&1023);
 map(&as,(void*)0x40000000,NULL,MMAP_NONE);printf("null_none_leaf=0x%lx\n",leaf[0]);
 unprotect(&as);printf("unprotect_free_calls=%d ptr=%p\n",frees,as.ptr);
 return 0;
}
