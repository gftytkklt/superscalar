#include <am.h>
#include <stdio.h>
#include "nemu/src/device/audio.c"
#include "abstract-machine/am/src/platform/nemu/ioe/audio.c"
static io_callback_t cb;
static unsigned opens,pauses;static int fail_open;
uint8_t *new_space(int n){return calloc(1,n);}
void add_mmio_map(const char *n,paddr_t a,void *p,uint32_t len,io_callback_t f){if(f)cb=f;}
uint32_t inl(uintptr_t a){return audio_base[(a-AUDIO_ADDR)/4];}
void outl(uintptr_t a,uint32_t v){uint32_t off=a-AUDIO_ADDR;audio_base[off/4]=v;cb(off,4,true);}
void outb(uintptr_t a,uint8_t v){sbuf[a-AUDIO_SBUF_ADDR]=v;}
int SDL_InitSubSystem(Uint32 flags){return 0;}
int SDL_OpenAudio(SDL_AudioSpec *want,SDL_AudioSpec *have){opens++;printf("open=%u hz=%d channels=%u frames=%u fmt=%x result=%d\n",opens,want->freq,want->channels,want->samples,want->format,fail_open?-1:0);return fail_open?-1:0;}
void SDL_PauseAudio(int on){pauses++;}
int main(void){
 init_audio();__am_audio_init();printf("after_am_init opens=%u init=%u capacity=%u\n",opens,audio_base[4],bufsize);
 AM_AUDIO_CTRL_T cfg={44100,2,512};__am_audio_ctrl(&cfg);
 if(opens!=1||pauses!=1)return 1;
 fail_open=1;cfg.freq=22050;__am_audio_ctrl(&cfg);
 char data[4]={1,2,3,4};AM_AUDIO_PLAY_T play={{data,data+4}};__am_audio_play(&play);AM_AUDIO_STATUS_T st;__am_audio_status(&st);
 printf("failed_reopen pauses=%u count=%d reg_freq=%u queued=%d,%d,%d,%d\n",pauses,st.count,audio_base[0],sbuf[0],sbuf[1],sbuf[2],sbuf[3]);
 return !(opens==2&&pauses==2&&st.count==4&&audio_base[0]==22050);
}
