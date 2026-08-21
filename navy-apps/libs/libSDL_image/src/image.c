#define SDL_malloc  malloc
#define SDL_free    free
#define SDL_realloc realloc

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

#define SDL_STBIMAGE_IMPLEMENTATION
#include "SDL_stbimage.h"

SDL_Surface* IMG_Load_RW(SDL_RWops *src, int freesrc) {
  assert(src->type == RW_TYPE_MEM);
  assert(freesrc == 0);
  return STBIMG_LoadFromMemory(src->mem.base, src->mem.size);
}

SDL_Surface* IMG_Load(const char *filename) {
  FILE *fp = fopen(filename, "r");
  if (fp == NULL) return NULL;
  fseek(fp, 0, SEEK_END);
  long size = ftell(fp);
  fseek(fp, 0, SEEK_SET);
  void *buf = malloc(size);
  assert(buf);
  size_t n = fread(buf, 1, size, fp);
  fclose(fp);
  SDL_Surface *s = (n == (size_t)size) ? STBIMG_LoadFromMemory(buf, size) : NULL;
  free(buf);
  return s;
}

int IMG_isPNG(SDL_RWops *src) {
  return 0;
}

SDL_Surface* IMG_LoadJPG_RW(SDL_RWops *src) {
  return IMG_Load_RW(src, 0);
}

char *IMG_GetError() {
  return "Navy does not support IMG_GetError()";
}
