#include <SDL.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "mixer.c"
int main(int argc,char **argv) {
  assert(argc==3);
  if(argv[1][0]=='s') {
    SDL_AudioSpec spec={0}; uint8_t *buf=NULL; uint32_t len=0;
    SDL_AudioSpec *r=SDL_LoadWAV(argv[2],&spec,&buf,&len);
    printf("SDL WAV accepted=%d channels=%d rate=%d bytes=%u\n",r!=NULL,spec.channels,spec.freq,len);free(buf);
    assert(r==NULL);
  } else {
    SDL_RWops *r=SDL_RWFromFile(argv[2],"rb");Chunk *c=parse_wav(r);SDL_RWclose(r);
    printf("mixer WAV accepted=%d channels=%d rate=%u\n",c!=NULL,c?c->channels:-1,c?c->freq:0);
    if(argv[1][0]=='m')assert(c==NULL);
    else assert(c && c->channels==0 && c->freq==0);
    if(c){free(c->data);free(c);}
  }
}
