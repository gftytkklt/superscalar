#include <SDL_bmp.h>
#include <BMP.h>
#include <stdlib.h>
#include <stdint.h>

SDL_Surface* SDL_LoadBMP(const char *filename) {
  int w, h;
  void *pixels = BMP_Load(filename, &w, &h);
  if (pixels == NULL) return NULL;
  // SDL stores pitch in uint16_t; reject widths the surface cannot represent.
  if (w <= 0 || h <= 0 || w > (int)(UINT16_MAX / sizeof(uint32_t))) { free(pixels); return NULL; }
  SDL_Surface *s = SDL_CreateRGBSurfaceFrom(pixels, w, h, 32, w * sizeof(uint32_t),
      DEFAULT_RMASK, DEFAULT_GMASK, DEFAULT_BMASK, DEFAULT_AMASK);
  if (s == NULL) { free(pixels); return NULL; }
  s->flags &= ~SDL_PREALLOC;
  return s;
}
