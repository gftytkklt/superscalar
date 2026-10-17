#include <proc.h>
#include <stdio.h>
#include <stdlib.h>
static Context contexts[4];static int count;
void halt(int c){exit(90);}void yield(void){}void putch(char c){}
int context_uload(PCB*p,const char*f,char*const a[],char*const e[]){p->cp=&contexts[count++];printf("load=%s\n",f);return 0;}
Context*kcontext(Area s,void(*e)(void*),void*a){return &contexts[count++];}
void naive_uload(PCB*p,const char*f){}
#include "nanos-lite/src/proc.c"
int main(void){setbuf(stdout,NULL);init_proc();Context prev={0};Context *a=schedule(&prev);printf("first=%td\n",a-contexts);Context *b=schedule(a);printf("second=%td\n",b-contexts);set_fg_pcb(2);Context*c=schedule(b);printf("switch_fg=%td\n",c-contexts);return 0;}
