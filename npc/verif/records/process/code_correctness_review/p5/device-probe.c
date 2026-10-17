#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <am.h>
#include <nemu.h>
static uint32_t regs[64], samples[16];
static unsigned reads, writes, sync_before, fb_writes;
uint32_t mock_inl(uintptr_t a) {
  if(a==AUDIO_ADDR+12)return 8;
  if(a==AUDIO_ADDR+20) { if(++reads>30) { puts("audio capacity wait exceeds 30 reads; len=9 capacity=8 count=0"); exit(42); } return regs[5]; }
  if(a==RTC_ADDR+4) { regs[16]=2; regs[17]=5; return regs[17]; }
  if(a==RTC_ADDR)return regs[16];
  if(a==KBD_ADDR)return 0x8000|AM_KEY_A;
  return regs[(a-DISK_ADDR)/4];
}
uint16_t mock_inw(uintptr_t a) {return a==VGACTL_ADDR+2 ? 4 : 3;}
void mock_outl(uintptr_t a,uint32_t v) {
  if(a==VGACTL_ADDR+4)sync_before=fb_writes+1;
  if(a>=FB_ADDR && a<FB_ADDR+128) {samples[(a-FB_ADDR)/4]=v; fb_writes++;}
  if(a>=AUDIO_ADDR && a<AUDIO_ADDR+24)regs[(a-AUDIO_ADDR)/4]=v;
  printf("outl 0x%lx=0x%x\n",(unsigned long)a,v); writes++;
}
void mock_outb(uintptr_t a,uint8_t v) {printf("outb 0x%lx=0x%x\n",(unsigned long)a,v);writes++;}
void putch(char c) { (void)c; }
void halt(int n) { exit(n+60); }
void __am_gpu_init(void), __am_audio_init(void);
void __am_gpu_config(AM_GPU_CONFIG_T *),__am_gpu_fbdraw(AM_GPU_FBDRAW_T *);
void __am_timer_uptime(AM_TIMER_UPTIME_T *), __am_input_keybrd(AM_INPUT_KEYBRD_T *);
void __am_audio_ctrl(AM_AUDIO_CTRL_T *),__am_audio_play(AM_AUDIO_PLAY_T *);
void __am_disk_blkio(AM_DISK_BLKIO_T *);
int main(int argc,char **argv) {
  if(argc!=2)return 2;
  if(!strcmp(argv[1],"gpu")) {
    __am_gpu_init(); AM_GPU_CONFIG_T cfg;__am_gpu_config(&cfg);
    uint32_t p[2]={0xaabbcc,0x112233}; AM_GPU_FBDRAW_T d={0,0,p,2,1,true}; __am_gpu_fbdraw(&d);
    printf("dimensions=%d/%d bytes=%d sync_event_fb_count_plus1=%u expected=3 after-2-writes\n",cfg.width,cfg.height,cfg.vmemsz,sync_before);
  } else if(!strcmp(argv[1],"timer")) {
    AM_TIMER_UPTIME_T t;__am_timer_uptime(&t);printf("latched_us=%llu expected=%llu\n",(unsigned long long)t.us,(5ULL<<32)|2);
  } else if(!strcmp(argv[1],"input")) {
    AM_INPUT_KEYBRD_T k;__am_input_keybrd(&k);printf("keycode=%d down=%d expected=%d/1\n",k.keycode,k.keydown,AM_KEY_A);
  } else if(!strcmp(argv[1],"disk")) {
    AM_DISK_BLKIO_T d={false,(void*)0x123456789abcdef0ULL,7,2};__am_disk_blkio(&d);
  } else if(!strcmp(argv[1],"audio") || !strcmp(argv[1],"audio-oversize")) {
    __am_audio_init();AM_AUDIO_CTRL_T c={8000,1,1024};__am_audio_ctrl(&c);
    char b[9]="abcdefgh";AM_AUDIO_PLAY_T a={{b,b+(!strcmp(argv[1],"audio")?5:9)}};__am_audio_play(&a);
    if(!strcmp(argv[1],"audio")) {a.buf.end=b+5; regs[5]=0;__am_audio_play(&a);printf("final-count=%u writes=%u\n",regs[5],writes);}
  } else if(!strcmp(argv[1],"ioe")) {
    printf("ioe_init=%d\n",ioe_init()); AM_UART_CONFIG_T c;ioe_read(AM_UART_CONFIG,&c);printf("uart_present=%d\n",c.present);
  } else return 2;
  return 0;
}
