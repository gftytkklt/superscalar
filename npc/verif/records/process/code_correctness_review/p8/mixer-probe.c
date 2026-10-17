#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include "mixer.c"
int main(void) {
  int16_t *pcm=calloc(65536*2,2),*out=calloc(65536*2,2);
  Chunk ch={.data=(uint8_t*)pcm,.len=65536*4,.freq=44100,.channels=2};
  Channel c={.chunk=&ch,.playing=1,.volume=128};
  mix_chunk(&c,out,65536);
  printf("65536 source frames: pos=%u playing=%d\n",c.pos,c.playing);
  assert(c.pos==0 && c.playing==1);free(pcm);free(out);return 0;
}
