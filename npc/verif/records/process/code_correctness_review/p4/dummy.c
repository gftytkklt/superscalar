#include <am.h>
#include <stdio.h>
static int called;
static void entry(void){called++;}
int main(void){int v=7; int old=atomic_xchg(&v,11); AddrSpace as={.pgsize=123,.ptr=(void*)456}; Area st={0};
 printf("mpe_init=%d called=%d cpus=%d cpu=%d old=%d value=%d\n",mpe_init(entry),called,cpu_count(),cpu_current(),old,v);
 printf("vme_init=%d ",vme_init(0,0));protect(&as);map(&as,0,0,0);unprotect(&as);printf("pgsize=%d ptr=%p ucontext=%p\n",as.pgsize,as.ptr,(void*)ucontext(&as,st,0));return 0;}
