#include <proc.h>
#include <stdio.h>
#include <stdlib.h>
Area heap;static PCB pcb;PCB *current=&pcb,*fg_pcb;static int nmap;static uintptr_t last;
void halt(int c){exit(90);}void putch(char c){}
bool vme_init(void*(*a)(int),void(*f)(void*)){printf("vme_init=false\n");return false;}
void map(AddrSpace*a,void*v,void*p,int prot){nmap++;last=(uintptr_t)v;}
#include "nanos-lite/src/mm.c"
int main(int argc,char**argv){setbuf(stdout,NULL);heap=(Area){(void*)0x1003,(void*)0x3000};const char*s=argv[1];
 if(!strcmp(s,"pages")){void*p=new_page(2);printf("allocated=%p end=%p limit=%p exceeded=%d\n",p,heap.start,heap.end,heap.start>heap.end);}
 if(!strcmp(s,"wrap")){void*p=new_page(SIZE_MAX/4096+1);printf("wrapped_allocation=%p cursor=%p\n",p,heap.start);}
 if(!strcmp(s,"brk")){pcb.max_brk=0x7fffe000;int r=mm_brk(0x80001000);printf("return=%d maps=%d last=%lx max=%lx stack_start=7fff8000 user_end=80000000\n",r,nmap,last,pcb.max_brk);}
 if(!strcmp(s,"vme")){init_mm();printf("continued_after_false=1\n");}
 return 0;}
