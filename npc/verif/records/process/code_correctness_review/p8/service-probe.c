#include <SDL.h>
#include <NDL.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint32_t now;
static int cb_count, depth, peak, closed, queries, writes;
static uint32_t drawn;
int NDL_Init(uint32_t flags) { return 0; }
void NDL_Quit(void) { }
uint32_t NDL_GetTicks(void) { return now; }
void NDL_OpenCanvas(int *w,int *h) { if(!*w)*w=4; if(!*h)*h=4; }
void NDL_DrawRect(uint32_t *p,int x,int y,int w,int h) { drawn=*p; }
int NDL_PollEvent(char *p,int n) { return 0; }
void NDL_OpenAudio(int f,int c,int s) {closed=0;}
void NDL_CloseAudio(void) {closed=1;}
int NDL_QueryAudio(void) { if(closed)queries++; return 4096; }
int NDL_PlayAudio(void *p,int n) { if(closed)writes++; return n; }
static void audio_cb(void *u,uint8_t *p,int n) {cb_count++;memset(p,0,n);}
static uint32_t timer_cb(uint32_t interval,void *p) {
  depth++; if(depth>peak)peak=depth; cb_count++;
  if(depth<3) SDL_GetTicks();
  depth--; return 0;
}
int main(int argc,char **argv) {
  assert(argc==2);
  if(!strcmp(argv[1],"video")) {
    SDL_Surface *s=SDL_CreateRGBSurface(0,1,1,32,DEFAULT_RMASK,DEFAULT_GMASK,DEFAULT_BMASK,DEFAULT_AMASK);
    *(uint32_t*)s->pixels=0x00112233;
    SDL_Surface *d=SDL_ConvertSurface(s,s->format,0);
    printf("identity convert: %08x -> %08x\n",*(uint32_t*)s->pixels,*(uint32_t*)d->pixels);
    assert(*(uint32_t*)d->pixels==0x00332211);
    SDL_Surface *a=SDL_CreateRGBSurface(0,1,1,32,0xff,0xff00,0xff0000,0xff000000);
    *(uint32_t*)a->pixels=0x00332211; SDL_UpdateRect(a,0,0,0,0);
    printf("ABGR update raw=%08x expected red/blue-mapped ff112233\n",drawn);
    assert(drawn==0xff332211);SDL_FreeSurface(a);SDL_FreeSurface(d);SDL_FreeSurface(s);
  } else if(!strcmp(argv[1],"rw")) {
    char data[]="abcde",dst[16]={0}; SDL_RWops *r=SDL_RWFromMem(data,5);
    size_t n=SDL_RWread(r,dst,2,3);printf("partial: items=%zu pos=%lld\n",n,(long long)SDL_RWtell(r));
    assert(n==2 && SDL_RWtell(r)==5);
    SDL_RWseek(r,0,RW_SEEK_SET);n=SDL_RWread(r,dst,(size_t)1<<63,2);
    printf("overflow: items=%zu pos=%lld\n",n,(long long)SDL_RWtell(r));
    assert(n==0 && SDL_RWtell(r)==0);SDL_RWclose(r);
  } else if(!strcmp(argv[1],"timer")) {
    SDL_AddTimer(1,timer_cb,NULL);now=2;SDL_GetTicks();
    printf("one due timer: callbacks=%d nested-depth=%d\n",cb_count,peak);assert(cb_count==3 && peak==3);
  } else if(!strcmp(argv[1],"close")) {
    SDL_AudioSpec s={.freq=1000,.format=AUDIO_S16,.channels=2,.samples=1,.callback=audio_cb};
    SDL_OpenAudio(&s,NULL);SDL_PauseAudio(0);now=2;SDL_GetTicks();SDL_CloseAudio();now=4;SDL_GetTicks();
    printf("after close: callbacks=%d invalid-queries=%d invalid-writes=%d\n",cb_count,queries,writes);
    assert(cb_count==2 && queries==1 && writes==1);
  } else if(!strcmp(argv[1],"keys")) {
    SDL_Event e={0}; e.type=SDL_KEYDOWN;e.key.keysym.sym=255;SDL_PushEvent(&e);
  } else if(!strcmp(argv[1],"oddmix")) {
    uint8_t *s=malloc(1),*d=malloc(1);*s=*d=0;SDL_MixAudio(d,s,1,128);free(s);free(d);
  } else if(!strcmp(argv[1],"rwoverflow")) {
    char data[]="abcde",dst[8]={0};SDL_RWops *r=SDL_RWFromMem(data,5);
    SDL_RWread(r,dst,(size_t)-1,1);
    SDL_RWread(r,dst,1,1); /* negative internal position is used before a seek can clamp it */
    SDL_RWclose(r);
  }
  return 0;
}
