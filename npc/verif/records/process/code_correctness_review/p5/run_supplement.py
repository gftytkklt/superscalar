#!/usr/bin/env python3
"""NPC MMIO substitutions and BSP boundary probes; not a full RTOS test."""
from pathlib import Path
import json,subprocess,os,hashlib,shutil,tempfile
H=Path(__file__).resolve().parent
R=next(p for p in H.parents if (p/'AGENTS.md').exists())
T=Path(tempfile.mkdtemp(prefix='ccr-p5-bsp-')); cmds=[]; copies=[]
def cp(s,d):
    p=R/s;q=T/d;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    copies.append({'path':s,'copy':str(q),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return q
def run(n,a,e=0):
    try:
        p=subprocess.run(list(map(str,a)),cwd=T,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20,env={**os.environ,'CCACHE_DISABLE':'1','ASAN_OPTIONS':'detect_leaks=0:detect_stack_use_after_return=1'})
        rc,s=p.returncode,p.stdout
    except subprocess.TimeoutExpired as x:rc,s=124,str(x)
    (H/(n+'.log')).write_text(s);cmds.append({'name':n,'argv':list(map(str,a)),'cwd':str(T),'exit':rc,'expected_exit':e,'match':rc==e,'log':n+'.log'})
for p in (R/'abstract-machine/am/include').rglob('*.h'):cp(str(p.relative_to(R)),'include/'+str(p.relative_to(R/'abstract-machine/am/include')))
for p in (R/'abstract-machine/klib/include').glob('*.h'):cp(str(p.relative_to(R)),'include/'+p.name)
common=['gcc','-O2','-std=gnu11','-fno-builtin','-funsigned-char','-DARCH_H="arch/riscv.h"','-I'+str(T/'include')]
for n in ['ioe','input','video']:cp('abstract-machine/am/src/riscv/npc/'+n+'.c',n+'.c')
(T/'npc-probe.c').write_text('''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <am.h>
static uint8_t fifo[200];static int count,pos;
uint32_t ps2_data(void){return fifo[pos++];}
uint32_t ps2_status(void){return pos<count;}
void putch(char c){(void)c;} void halt(int c){exit(60+c);}
void __am_timer_init(void){} void __am_timer_rtc(AM_TIMER_RTC_T *p){(void)p;} void __am_timer_uptime(AM_TIMER_UPTIME_T *p){p->us=0;}
void __am_input_keybrd(AM_INPUT_KEYBRD_T *);
void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *);
int main(int ac,char **av){if(ac!=2)return 2;setvbuf(stdout,NULL,_IONBF,0);ioe_init();
if(!strcmp(av[1],"input")) { uint8_t b[]={0x1c,0xf0,0x1c,0xe0,0x74,0xe0,0xf0,0x74,0x77};memcpy(fifo,b,sizeof b);count=sizeof b;
for(int i=0;i<5;i++){AM_INPUT_KEYBRD_T k;__am_input_keybrd(&k);printf("key=%d down=%d\\n",k.keycode,k.keydown);} }
else if(!strcmp(av[1],"split-prefix")){ fifo[0]=0xe0;count=1;AM_INPUT_KEYBRD_T k;__am_input_keybrd(&k);printf("prefix-only=%d\\n",k.keycode);fifo[count++]=0x74;__am_input_keybrd(&k);printf("continued=%d expected=%d\\n",k.keycode,AM_KEY_RIGHT);}
else if(!strcmp(av[1],"queue")){for(int i=0;i<20;i++)fifo[count++]=0x1c;int events=0;for(int i=0;i<21;i++){AM_INPUT_KEYBRD_T k;__am_input_keybrd(&k);events+=(k.keycode!=0);}printf("fifo20 produced=%d queue-capacity=15\\n",events);}
else if(!strcmp(av[1],"audio-config")){AM_AUDIO_CONFIG_T c;ioe_read(AM_AUDIO_CONFIG,&c);}
else if(!strcmp(av[1],"disk-config")){AM_DISK_CONFIG_T c;ioe_read(AM_DISK_CONFIG,&c);}
else if(!strcmp(av[1],"uart-tx")){AM_UART_CONFIG_T c;ioe_read(AM_UART_CONFIG,&c);printf("present=%d then TX\\n",c.present);AM_UART_TX_T v={'A'};ioe_write(AM_UART_TX,&v);}
else if(!strcmp(av[1],"uart-rx")){unsigned char *m=mmap((void*)0x10000000,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);if(m==MAP_FAILED)return 3;AM_UART_RX_T c;m[5]=0;ioe_read(AM_UART_RX,&c);printf("empty=%u\\n",(unsigned char)c.data);m[5]=1;m[0]='A';ioe_read(AM_UART_RX,&c);printf("read=%c\\n",c.data);}
else if(!strcmp(av[1],"video")){uint32_t *m=mmap((void*)0x21000000,640*480*4+4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0);if(m==MAP_FAILED)return 3;uint32_t v[2]={1,2};AM_GPU_FBDRAW_T c={639,0,v,2,1,0};__am_gpu_fbdraw(&c);printf("row0-last=%u row1-first=%u (crossing rectangle not clipped)\\n",m[639],m[640]);c=(AM_GPU_FBDRAW_T){0,0,NULL,0,0,1};__am_gpu_fbdraw(&c);}
return 0;}
''')
s=(T/'input.c').read_text().replace('(*(volatile uint32_t *)(PS2_BASE + 0x0L))','ps2_data()').replace('(*(volatile uint32_t *)(PS2_BASE + 0x4L))','ps2_status()')
(T/'input-mock.c').write_text('uint32_t ps2_data(void); uint32_t ps2_status(void);\n'.replace('uint32_t','#include <stdint.h>\nuint32_t',1)+s)
run('npc-link',[*common,T/'npc-probe.c',T/'ioe.c',T/'input-mock.c',T/'video.c','-o',T/'npc'])
for n,e in [('input',0),('split-prefix',0),('queue',0),('audio-config',61),('disk-config',61),('uart-tx',61),('uart-rx',0),('video',0)]:run('npc-'+n,[T/'npc',n],e)

# BSP fixtures use the public AM structs, with a deliberately tiny RT boundary stub.
(T/'include/rtthread.h').write_text('''#ifndef CCR_RT_STUB_H
#define CCR_RT_STUB_H
#include <stdint.h>
#include <stddef.h>
typedef uintptr_t rt_ubase_t; typedef intptr_t rt_base_t; typedef uint8_t rt_uint8_t;
typedef struct rt_thread {rt_ubase_t user_data;} *rt_thread_t;
#define RT_ALIGN_DOWN(n,a) ((n)&~((a)-1))
#define RT_USING_HEAP 1
#define RT_NULL NULL
#define INIT_ENV_EXPORT(x)
#define MSH_CMD_EXPORT(a,b)
void *rt_malloc(size_t);void rt_system_heap_init(void*,void*);void rt_kprintf(const char*,...);
struct rt_thread *rt_thread_self(void);
void rt_thread_exit(void);
rt_thread_t rt_thread_create(const char*,void(*)(void*),void*,unsigned,int,int);
int rt_thread_startup(rt_thread_t);
#endif
''')
for n in ['context','init','interrupt']:cp('rt/bsp/abstract-machine/src/'+n+'.c','bsp-'+n+'.c')
(T/'bsp-probe.c').write_text('''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <am.h>
#include <rtthread.h>
static int en,fail;static struct rt_thread thr={1234};static Context *(*cb)(Event,Context*);static Context oldc,newc,*target=&newc,*saved;
static Context *got;static void *gotarg;static Area gotstack;
Area heap={(void*)0x80000000,(void*)0x88000000};extern Area am_apps_heap;
asm(".globl __am_apps_data_start,__am_apps_data_end,__am_apps_bss_start,__am_apps_bss_end\\n.set __am_apps_data_start,0x1000\\n.set __am_apps_data_end,0x1000\\n.set __am_apps_bss_start,0x1000\\n.set __am_apps_bss_end,0x1000");
void putch(char c){(void)c;}void halt(int n){exit(60+n);}void iset(bool v){en=v;}bool ienabled(void){return en;}
bool cte_init(Context *(*f)(Event,Context*)){cb=f;return true;}bool ioe_init(void){return true;}int entry(void){return 0;}
struct rt_thread *rt_thread_self(void){return &thr;}void rt_system_heap_init(void*a,void*b){(void)a;(void)b;}
void rt_kprintf(const char*f,...){(void)f;}int rt_hw_uart_init(void){return 0;}void *rt_malloc(size_t n){(void)n;return fail?NULL:(void*)0x82000000;}
Context *kcontext(Area a,void(*f)(void*),void *p){(void)f;gotstack=a;gotarg=p;return got=(Context*)((char*)a.end-sizeof(Context));}
void yield(void){Event e={.event=EVENT_YIELD};Context *c=cb(e,&oldc);printf("selected-target=%d\\n",c==target);}
void rt_hw_context_switch(rt_ubase_t,rt_ubase_t);void __am_cte_init(void);void rt_hw_board_init(void);rt_uint8_t *rt_hw_stack_init(void*,void*,rt_uint8_t*,void*);
extern void rt_hw_interrupt_enable(rt_base_t);extern rt_base_t rt_hw_interrupt_disable(void);
static void f(void *x){(void)x;}
int main(int ac,char**av){if(ac!=2)return 2;
if(!strcmp(av[1],"interrupt")){en=0;rt_hw_interrupt_disable();rt_hw_interrupt_enable(0);printf("restore-disabled mie=%d expected=0\\n",en);}
else if(!strcmp(av[1],"heap")||!strcmp(av[1],"heap-fail")){fail=!strcmp(av[1],"heap-fail");rt_hw_board_init();printf("app-heap-start=%p bytes=%lu requested=%u\\n",am_apps_heap.start,(uintptr_t)am_apps_heap.end-(uintptr_t)am_apps_heap.start,0x2000000);}
else if(!strcmp(av[1],"context")){__am_cte_init();rt_hw_context_switch((rt_ubase_t)&saved,(rt_ubase_t)&target);printf("saved=%d user-data=%lu expected=1/1234\\n",saved==&oldc,thr.user_data);_Alignas(16) unsigned char stack[1024];void *c=rt_hw_stack_init(f,(void*)77,stack+sizeof stack-sizeof(rt_ubase_t),f);printf("frame-align=%lu end-align=%lu arg-in-stack=%d frame-in-stack=%d\\n",(uintptr_t)c%16,(uintptr_t)gotstack.end%16,(char*)gotarg>=(char*)stack&&(char*)gotarg<(char*)stack+1024,(char*)c>=(char*)stack);}
return 0;}
''')
run('bsp-init-compile',[*common,'-Dmain=bsp_main','-c',T/'bsp-init.c','-o',T/'init.o'])
run('bsp-link',[*common,'-no-pie',T/'bsp-probe.c',T/'bsp-context.c',T/'bsp-interrupt.c',T/'init.o','-o',T/'bsp'])
for n in ['interrupt','heap','heap-fail','context']:run('bsp-'+n,[T/'bsp',n])

# Extract the exact generated wrapper template without executing the integration script.
text=(R/'rt/bsp/abstract-machine/integrate-am-apps.py').read_text()
start=text.index('am_app_c_fp.write("""#include')+len('am_app_c_fp.write("""')
template=text[start:text.index('""")',start)]
(T/'wrapper.c').write_text(template)
(T/'wrapper-probe.c').write_text('''#include <stdio.h>
#include <stdlib.h>
#include <am.h>
#include <rtthread.h>
Area heap,am_apps_heap,am_apps_data,am_apps_bss;uint8_t *am_apps_data_content;
static void (*deferred)(void*);static void *argument;static struct rt_thread thr;
rt_thread_t rt_thread_create(const char*n,void(*f)(void*),void*p,unsigned s,int pr,int t){(void)n;(void)s;(void)pr;(void)t;deferred=f;argument=p;return &thr;}
int rt_thread_startup(rt_thread_t p){(void)p;return 0;}void rt_thread_exit(void){}void halt(int n){exit(60+n);}
#include "wrapper.c"
static void app(const char *p){printf("app=[%s]\\n",p);}
__attribute__((noinline)) static void launch(void){char *a[]={"app","hello"};am_app_start_wrapper("app",app,2,a);}
int main(void){static char b[1];am_apps_data=(Area){b,b};am_apps_bss=(Area){b,b};am_apps_data_content=b;launch();deferred(argument);return 0;}
''')
run('wrapper-link',[*common,'-O1','-fsanitize=address','-fno-omit-frame-pointer','-no-pie',T/'wrapper-probe.c','-o',T/'wrapper'])
run('wrapper-lifetime',[T/'wrapper'],1)

# Compile against the real RT public declaration to expose the interrupt ABI mismatch.
cp('rt/include/rthw.h','real-rthw.h')
run('bsp-interrupt-contract',[*common,'-I'+str(R/'rt/include'),'-I'+str(R/'rt/bsp/abstract-machine'),'-I'+str(R/'rt/bsp/abstract-machine/include'),'-include',R/'rt/include/rthw.h','-c',T/'bsp-interrupt.c','-o',T/'irq-contract.o'],1)
result={'phase':'CCR-P5','date':'2026-10-17','out':str(T),'commands':cmds,'copies':copies,'substitutions':{'NPC input':'Only PS2_DATA/PS2_STATUS expressions replaced by scripted FIFO functions; original copy retained.','NPC video/UART':'private anonymous mmap at fixed MMIO addresses; no hardware access','BSP':'small RT boundary stub; exact C sources; wrapper template extracted without executing generator','limit':'No scheduling/interrupt/hardware/whole RTOS execution'},'hashes':{str(p.relative_to(T)):hashlib.sha256(p.read_bytes()).hexdigest() for p in T.rglob('*') if p.is_file()}}
(H/'supplement-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'out':str(T),'commands':len(cmds),'unexpected':[x for x in cmds if not x['match']]},ensure_ascii=False,indent=2))
