#include <proc.h>
#include <fs.h>
#include <stdio.h>
#include <stdlib.h>
static int code,down=1;static size_t diskpos,disklen;static int draws;static uint64_t now=2000001;
Area heap; PCB *current,*fg_pcb;
void halt(int c){exit(c?90:0);}void putch(char c){}void yield(void){} void set_fg_pcb(int i){printf("fg=%d\n",i);}
void ioe_read(int reg,void *p){switch(reg){
 case AM_INPUT_KEYBRD:*(AM_INPUT_KEYBRD_T*)p=(AM_INPUT_KEYBRD_T){down,code};break;
 case AM_GPU_CONFIG:*(AM_GPU_CONFIG_T*)p=(AM_GPU_CONFIG_T){.present=true,.width=4,.height=3};break;
 case AM_AUDIO_CONFIG:*(AM_AUDIO_CONFIG_T*)p=(AM_AUDIO_CONFIG_T){.present=true,.bufsize=64};break;
 case AM_AUDIO_STATUS:*(AM_AUDIO_STATUS_T*)p=(AM_AUDIO_STATUS_T){.count=0};break;
 case AM_TIMER_UPTIME:*(AM_TIMER_UPTIME_T*)p=(AM_TIMER_UPTIME_T){.us=now};break;
 default:abort();}}
void ioe_write(int reg,void *p){if(reg==AM_GPU_FBDRAW){AM_GPU_FBDRAW_T *x=p;draws++;printf("draw x=%d y=%d w=%d h=%d\n",x->x,x->y,x->w,x->h);}}
bool ioe_init(void){return true;}void init_disk(void){}
size_t disk_read(void *b,size_t o,size_t n){diskpos=o;disklen=n;memset(b,0x42,n);return n;}
size_t disk_write(const void *b,size_t o,size_t n){diskpos=o;disklen=n;return n;}
int context_uload(PCB*p,const char*f,char*const a[],char*const e[]){return -2;}void switch_boot_pcb(void){}void naive_uload(PCB*p,const char*f){}int mm_brk(uintptr_t b){return 0;}
#include "nanos-lite/src/device.c"
#include "nanos-lite/src/fs.c"
#include "nanos-lite/src/syscall.c"
int main(int argc,char **argv){setbuf(stdout,NULL);init_fs();const char*s=argv[1];unsigned char b[64]={0};int fd=fs_open("//arc1.nsa",0,0);printf("fd=%d\n",fd);
 if(!strcmp(s,"fs")){printf("seek=%ld\n",fs_lseek(fd,295960,SEEK_SET));printf("read=%ld\n",fs_read(fd,b,16));printf("disk_pos=%zu disk_len=%zu eof=%ld\n",diskpos,disklen,fs_read(fd,b,1));int fd2=fs_open("arc1.nsa",0,0);printf("second_fd=%d reset=%ld\n",fd2,fs_lseek(fd,0,SEEK_CUR));fs_close(fd);printf("after_close_read=%ld (documented no-open-state)\n",fs_read(fd,b,1));}
 if(!strcmp(s,"bad-fd"))fs_read(-1,b,0);
 if(!strcmp(s,"seek")){printf("negative_seek=%ld\n",fs_lseek(fd,(size_t)-1,SEEK_SET));printf("read=%ld\n",fs_read(fd,b,1));printf("past_end_seek=%ld size=295964\n",fs_lseek(fd,295965,SEEK_SET));}
 if(!strcmp(s,"events")||!strcmp(s,"events-small")){code=AM_KEY_A;if(!strcmp(s,"events-small")){char *q=malloc(1);events_read(q,0,1);}else printf("n=%zu text=%s",events_read(b,0,64),b);}
 if(!strcmp(s,"audio-small")){char *q=malloc(1);audio_read(q,0,1);}
 if(!strcmp(s,"audio-zero")){int q=-1;size_t n=audio_read(&q,0,0);printf("len0 result=%zu wrote=%d\n",n,q);}
 if(!strcmp(s,"disp")){long n=fs_read(4,b,6);b[n]=0;printf("first=%s\n",b);n=fs_read(4,b,6);b[n]=0;printf("second=%s offset=%ld\n",b,fp_offt[4]);}
 if(!strcmp(s,"fb")){uint32_t pix[8]={0};printf("ret=%ld\n",fs_write(5,pix,sizeof(pix)));fs_lseek(5,48,SEEK_SET);printf("past_end_ret=%ld\n",fs_write(5,pix,4));}
 if(!strcmp(s,"abi")){Context c={0};c.GPR1=SYS_read;c.GPR2=fd;c.GPR3=(uintptr_t)b;c.GPR4=7;do_syscall(&c);printf("read_return=%lu bytes=%x offset=%ld\n",c.GPRx,b[0],fp_offt[fd]);struct timeval tv;c.GPR1=SYS_gettimeofday;c.GPR2=(uintptr_t)&tv;c.GPR3=0;do_syscall(&c);printf("time=%ld.%06ld return=%lu size=%zu\n",tv.tv_sec,tv.tv_usec,c.GPRx,sizeof(tv));c.GPR1=SYS_execve;do_syscall(&c);printf("exec_missing_signed=%ld\n",(long)c.GPRx);}
 return 0;}
