#include <NDL.h>
#include <sdl-video.h>
#include <assert.h>
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

void SDL_BlitSurface(SDL_Surface *src, SDL_Rect *srcrect, SDL_Surface *dst, SDL_Rect *dstrect) {
  assert(dst && src);
  assert(dst->format->BitsPerPixel == src->format->BitsPerPixel);

  int sx, sy, sw, sh;
  if (srcrect == NULL) { sx = 0; sy = 0; sw = src->w; sh = src->h; }
  else { sx = srcrect->x; sy = srcrect->y; sw = srcrect->w; sh = srcrect->h; }

  int dx = 0, dy = 0;
  if (dstrect != NULL) { dx = dstrect->x; dy = dstrect->y; }

  // clip against source bounds
  if (sx < 0) { sw += sx; dx -= sx; sx = 0; }
  if (sy < 0) { sh += sy; dy -= sy; sy = 0; }
  if (sx >= src->w || sy >= src->h || sw <= 0 || sh <= 0) { sw = sh = 0; }
  if (sx + sw > src->w) sw = src->w - sx;
  if (sy + sh > src->h) sh = src->h - sy;

  // clip against destination bounds
  if (dx < 0) { sw += dx; sx -= dx; dx = 0; }
  if (dy < 0) { sh += dy; sy -= dy; dy = 0; }
  if (dx >= dst->w || dy >= dst->h || sw <= 0 || sh <= 0) { sw = sh = 0; }
  if (dx + sw > dst->w) sw = dst->w - dx;
  if (dy + sh > dst->h) sh = dst->h - dy;

  if (dstrect != NULL) { dstrect->w = sw; dstrect->h = sh; }
  if (sw <= 0 || sh <= 0) return;
  int bpp = src->format->BytesPerPixel;
  int row_bytes = sw * bpp;
  for (int i = 0; i < sh; i ++) {
    uint8_t *sp = src->pixels + (sy + i) * src->pitch + sx * bpp;
    uint8_t *dp = dst->pixels + (dy + i) * dst->pitch + dx * bpp;
    memcpy(dp, sp, row_bytes);
  }
}

void SDL_FillRect(SDL_Surface *dst, SDL_Rect *dstrect, uint32_t color) {
  assert(dst);
  int dx = 0, dy = 0, dw = dst->w, dh = dst->h;
  if (dstrect != NULL) { dx = dstrect->x; dy = dstrect->y; dw = dstrect->w; dh = dstrect->h; }

  if (dx < 0) { dw += dx; dx = 0; }
  if (dy < 0) { dh += dy; dy = 0; }
  if (dx >= dst->w || dy >= dst->h || dw <= 0 || dh <= 0) return;
  if (dx + dw > dst->w) dw = dst->w - dx;
  if (dy + dh > dst->h) dh = dst->h - dy;

  int bpp = dst->format->BytesPerPixel;
  for (int i = 0; i < dh; i ++) {
    uint8_t *p = dst->pixels + (dy + i) * dst->pitch + dx * bpp;
    if (bpp == 4) {
      uint32_t *p32 = (uint32_t *)p;
      for (int j = 0; j < dw; j ++) p32[j] = color;
    } else {
      uint8_t c = color;
      for (int j = 0; j < dw; j ++) p[j] = c;
    }
  }
}

void SDL_UpdateRect(SDL_Surface *s, int x, int y, int w, int h) {
  if (s == NULL) return;

  if (x < 0) { w += x; x = 0; }
  if (y < 0) { h += y; y = 0; }
  if (w == 0) w = s->w - x;
  if (h == 0) h = s->h - y;
  if (x >= s->w || y >= s->h || w <= 0 || h <= 0) return;
  if (x + w > s->w) w = s->w - x;
  if (y + h > s->h) h = s->h - y;

  if (s->format->BitsPerPixel == 32) {
    // SDL1.2 display surfaces carry no alpha: force the alpha byte to 0xff
    // before handing pixels to NDL (whose framebuffer is opaque 0x00RRGGBB).
    // A grown-once scratch buffer avoids a per-frame malloc/free.
    static uint32_t *buf = NULL;
    static size_t cap = 0;
    size_t need = (size_t)w * h;
    if (need > cap) {
      free(buf);
      buf = malloc(need * sizeof(uint32_t));
      assert(buf);
      cap = need;
    }
    for (int i = 0; i < h; i ++) {
      uint32_t *src_row = (uint32_t *)s->pixels + (y + i) * (s->pitch / 4) + x;
      for (int j = 0; j < w; j ++) buf[i * w + j] = src_row[j] | 0xff000000u;
    }
    NDL_DrawRect(buf, x, y, w, h);
  } else {
    assert(s->format->BitsPerPixel == 8);
    assert(s->format->palette != NULL);
    SDL_Color *colors = s->format->palette->colors;
    uint32_t *buf = malloc(w * h * sizeof(uint32_t));
    assert(buf);
    for (int i = 0; i < h; i ++) {
      uint8_t *row = s->pixels + (y + i) * s->pitch + x;
      for (int j = 0; j < w; j ++) {
        SDL_Color c = colors[row[j]];
        buf[i * w + j] = (c.r << 16) | (c.g << 8) | c.b;
      }
    }
    NDL_DrawRect(buf, x, y, w, h);
    free(buf);
  }
}

// APIs below are already implemented.

static inline int maskToShift(uint32_t mask) {
  switch (mask) {
    case 0x000000ff: return 0;
    case 0x0000ff00: return 8;
    case 0x00ff0000: return 16;
    case 0xff000000: return 24;
    case 0x00000000: return 24; // hack
    default: assert(0);
  }
}

SDL_Surface* SDL_CreateRGBSurface(uint32_t flags, int width, int height, int depth,
    uint32_t Rmask, uint32_t Gmask, uint32_t Bmask, uint32_t Amask) {
  assert(depth == 8 || depth == 32);
  SDL_Surface *s = malloc(sizeof(SDL_Surface));
  assert(s);
  s->flags = flags;
  s->format = malloc(sizeof(SDL_PixelFormat));
  assert(s->format);
  if (depth == 8) {
    s->format->palette = malloc(sizeof(SDL_Palette));
    assert(s->format->palette);
    s->format->palette->colors = malloc(sizeof(SDL_Color) * 256);
    assert(s->format->palette->colors);
    memset(s->format->palette->colors, 0, sizeof(SDL_Color) * 256);
    s->format->palette->ncolors = 256;
  } else {
    s->format->palette = NULL;
    s->format->Rmask = Rmask; s->format->Rshift = maskToShift(Rmask); s->format->Rloss = 0;
    s->format->Gmask = Gmask; s->format->Gshift = maskToShift(Gmask); s->format->Gloss = 0;
    s->format->Bmask = Bmask; s->format->Bshift = maskToShift(Bmask); s->format->Bloss = 0;
    s->format->Amask = Amask; s->format->Ashift = maskToShift(Amask); s->format->Aloss = 0;
  }

  s->format->BitsPerPixel = depth;
  s->format->BytesPerPixel = depth / 8;

  s->w = width;
  s->h = height;
  s->pitch = width * depth / 8;
  assert(s->pitch == width * s->format->BytesPerPixel);

  if (!(flags & SDL_PREALLOC)) {
    s->pixels = malloc(s->pitch * height);
    assert(s->pixels);
  }

  return s;
}

SDL_Surface* SDL_CreateRGBSurfaceFrom(void *pixels, int width, int height, int depth,
    int pitch, uint32_t Rmask, uint32_t Gmask, uint32_t Bmask, uint32_t Amask) {
  SDL_Surface *s = SDL_CreateRGBSurface(SDL_PREALLOC, width, height, depth,
      Rmask, Gmask, Bmask, Amask);
  assert(pitch == s->pitch);
  s->pixels = pixels;
  return s;
}

void SDL_FreeSurface(SDL_Surface *s) {
  if (s != NULL) {
    if (s->format != NULL) {
      if (s->format->palette != NULL) {
        if (s->format->palette->colors != NULL) free(s->format->palette->colors);
        free(s->format->palette);
      }
      free(s->format);
    }
    if (s->pixels != NULL && !(s->flags & SDL_PREALLOC)) free(s->pixels);
    free(s);
  }
}

SDL_Surface* SDL_SetVideoMode(int width, int height, int bpp, uint32_t flags) {
  if (flags & SDL_HWSURFACE) NDL_OpenCanvas(&width, &height);
  return SDL_CreateRGBSurface(flags, width, height, bpp,
      DEFAULT_RMASK, DEFAULT_GMASK, DEFAULT_BMASK, DEFAULT_AMASK);
}

void SDL_SoftStretch(SDL_Surface *src, SDL_Rect *srcrect, SDL_Surface *dst, SDL_Rect *dstrect) {
  assert(src && dst);
  assert(dst->format->BitsPerPixel == src->format->BitsPerPixel);
  assert(dst->format->BitsPerPixel == 8);

  int sx = (srcrect == NULL ? 0 : srcrect->x);
  int sy = (srcrect == NULL ? 0 : srcrect->y);
  int sw = (srcrect == NULL ? src->w : srcrect->w);
  int sh = (srcrect == NULL ? src->h : srcrect->h);

  int dx = (dstrect == NULL ? 0 : dstrect->x);
  int dy = (dstrect == NULL ? 0 : dstrect->y);
  int dw = (dstrect == NULL ? dst->w : dstrect->w);
  int dh = (dstrect == NULL ? dst->h : dstrect->h);

  if (dw == sw && dh == sh) {
    SDL_Rect rect;
    rect.x = sx; rect.y = sy; rect.w = sw; rect.h = sh;
    SDL_BlitSurface(src, &rect, dst, dstrect);
    return;
  }

  for (int j = 0; j < dh; j ++) {
    int sy0 = sy + (j * sh) / dh;
    uint8_t *sp = src->pixels + sy0 * src->pitch;
    uint8_t *dp = dst->pixels + (dy + j) * dst->pitch + dx;
    for (int i = 0; i < dw; i ++) {
      int sx0 = sx + (i * sw) / dw;
      dp[i] = sp[sx0];
    }
  }
}

void SDL_SetPalette(SDL_Surface *s, int flags, SDL_Color *colors, int firstcolor, int ncolors) {
  assert(s);
  assert(s->format);
  assert(s->format->palette);
  assert(firstcolor == 0);

  s->format->palette->ncolors = ncolors;
  memcpy(s->format->palette->colors, colors, sizeof(SDL_Color) * ncolors);

  if(s->flags & SDL_HWSURFACE) {
    assert(ncolors == 256);
    for (int i = 0; i < ncolors; i ++) {
      uint8_t r = colors[i].r;
      uint8_t g = colors[i].g;
      uint8_t b = colors[i].b;
    }
    SDL_UpdateRect(s, 0, 0, 0, 0);
  }
}

static void ConvertPixelsARGB_ABGR(void *dst, void *src, int len) {
  int i;
  uint8_t (*pdst)[4] = dst;
  uint8_t (*psrc)[4] = src;
  union {
    uint8_t val8[4];
    uint32_t val32;
  } tmp;
  int first = len & ~0xf;
  for (i = 0; i < first; i += 16) {
#define macro(i) \
    tmp.val32 = *((uint32_t *)psrc[i]); \
    *((uint32_t *)pdst[i]) = tmp.val32; \
    pdst[i][0] = tmp.val8[2]; \
    pdst[i][2] = tmp.val8[0];

    macro(i + 0); macro(i + 1); macro(i + 2); macro(i + 3);
    macro(i + 4); macro(i + 5); macro(i + 6); macro(i + 7);
    macro(i + 8); macro(i + 9); macro(i +10); macro(i +11);
    macro(i +12); macro(i +13); macro(i +14); macro(i +15);
  }

  for (; i < len; i ++) {
    macro(i);
  }
}

SDL_Surface *SDL_ConvertSurface(SDL_Surface *src, SDL_PixelFormat *fmt, uint32_t flags) {
  assert(src->format->BitsPerPixel == 32);
  assert(src->w * src->format->BytesPerPixel == src->pitch);
  assert(src->format->BitsPerPixel == fmt->BitsPerPixel);

  SDL_Surface* ret = SDL_CreateRGBSurface(flags, src->w, src->h, fmt->BitsPerPixel,
    fmt->Rmask, fmt->Gmask, fmt->Bmask, fmt->Amask);

  assert(fmt->Gmask == src->format->Gmask);
  assert(fmt->Amask == 0 || src->format->Amask == 0 || (fmt->Amask == src->format->Amask));
  ConvertPixelsARGB_ABGR(ret->pixels, src->pixels, src->w * src->h);

  return ret;
}

uint32_t SDL_MapRGBA(SDL_PixelFormat *fmt, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
  assert(fmt->BytesPerPixel == 4);
  uint32_t p = (r << fmt->Rshift) | (g << fmt->Gshift) | (b << fmt->Bshift);
  if (fmt->Amask) p |= (a << fmt->Ashift);
  return p;
}

int SDL_LockSurface(SDL_Surface *s) {
  return 0;
}

void SDL_UnlockSurface(SDL_Surface *s) {
}
