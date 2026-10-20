#define SDL_malloc  malloc
#define SDL_free    free
#define SDL_realloc realloc

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <limits.h>

#define SDL_STBIMAGE_IMPLEMENTATION
#include "SDL_stbimage.h"

SDL_Surface* IMG_Load_RW(SDL_RWops *src, int freesrc) {
  SDL_Surface *surface = NULL;
  /* The memory decoder supports a complete buffer at position zero only. */
  if (src != NULL && src->type == RW_TYPE_MEM && src->seek != NULL &&
      src->mem.base != NULL && src->mem.size > 0 && src->mem.size <= INT_MAX &&
      SDL_RWtell(src) == 0) {
    surface = STBIMG_LoadFromMemory(src->mem.base, (int)src->mem.size);
  }
  /* Closing a memory RWops releases its wrapper, not the borrowed buffer. */
  if (src != NULL && freesrc && src->close != NULL) SDL_RWclose(src);
  return surface;
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
  static const uint8_t png_magic[8] = {0x89, 'P', 'N', 'G', 0x0d, 0x0a, 0x1a, 0x0a};
  uint8_t buf[8];
  int64_t pos = SDL_RWtell(src);
  if (SDL_RWseek(src, 0, RW_SEEK_SET) != 0) return 0;
  int ok = (SDL_RWread(src, buf, 1, 8) == 8) && (memcmp(buf, png_magic, 8) == 0);
  SDL_RWseek(src, pos, RW_SEEK_SET); // restore the position
  return ok;
}

SDL_Surface* IMG_LoadJPG_RW(SDL_RWops *src) {
  return IMG_Load_RW(src, 0);
}

char *IMG_GetError() {
  return "Navy does not support IMG_GetError()";
}
