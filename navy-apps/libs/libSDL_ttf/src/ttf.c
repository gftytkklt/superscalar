#include <SDL_ttf.h>
#include <fixedptc.h>
#include <assert.h>
#include <limits.h>

#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"

int TTF_Init() {
  return 0;
}

TTF_Font* TTF_OpenFont(const char *file, int ptsize) {
  SDL_RWops *f = SDL_RWFromFile(file, "rb");
  if (f == NULL) return NULL;
  TTF_Font *font = TTF_OpenFontRW(f, 0, ptsize);
  SDL_RWclose(f);
  return font;
}

static uint32_t font_be32(const uint8_t *p) {
  return (uint32_t)p[0] << 24 | (uint32_t)p[1] << 16 | (uint32_t)p[2] << 8 | p[3];
}

/* Check the outer directory before calling stb. This is not a validator for
 * arbitrary untrusted font tables; the bundled stb parser has that limitation. */
static int font_offset(const uint8_t *buf, size_t size) {
  if (size < 12) return -1;
  if (font_be32(buf) == 0x74746366) { // TTC
    if (size < 16) return -1;
    uint32_t count = font_be32(buf + 8), off = font_be32(buf + 12);
    if (count == 0 || count > (size - 12) / 4 || off > size - 12 || off > INT_MAX) return -1;
  }
  int off = stbtt_GetFontOffsetForIndex(buf, 0);
  if (off < 0 || (size_t)off > size - 12) return -1;
  size_t count = (unsigned)buf[off + 4] << 8 | buf[off + 5];
  if (count > (size - off - 12) / 16) return -1;
  for (size_t i = 0; i < count; i++) {
    const uint8_t *table = buf + off + 12 + i * 16;
    uint32_t start = font_be32(table + 8), len = font_be32(table + 12);
    if (start > size || len > size - start) return -1;
  }
  return off;
}

TTF_Font *TTF_OpenFontRW(SDL_RWops *src, int freesrc, int ptsize) {
  uint8_t *buf = NULL;
  stbtt_fontinfo *finfo = NULL;
  TTF_Font *font = NULL;
  if (src == NULL || ptsize <= 0) goto fail;
  int64_t pos = SDL_RWtell(src), end = SDL_RWsize(src);
  if (pos < 0 || end < pos || end - pos < 12 || end - pos > INT_MAX) goto fail;
  size_t size = (size_t)(end - pos);
  buf = malloc(size);
  if (buf == NULL || SDL_RWread(src, buf, 1, size) != size) goto fail;
  int off = font_offset(buf, size);
  if (off < 0) goto fail;
  finfo = malloc(sizeof(*finfo));
  if (finfo == NULL || !stbtt_InitFont(finfo, buf, off)) goto fail;
  font = malloc(sizeof(*font));
  if (font == NULL) goto fail;
  *font = (TTF_Font){ .finfo = finfo, .file = { buf, size }, .ptsize = ptsize,
                      .src = freesrc ? src : NULL };

  // pre-computed data
  fixedpt pixel = fixedpt_muli(fixedpt_rconst(1.333333), ptsize);
  font->factor = stbtt_ScaleForPixelHeight(finfo, pixel);
  stbtt_GetFontVMetrics(finfo, &font->ascent, &font->descent, NULL);
  font->height = fixedpt_toint(fixedpt_muli(font->factor, font->ascent - font->descent));
  font->ascent = fixedpt_toint(fixedpt_muli(font->factor, font->ascent));
  font->descent = fixedpt_toint(fixedpt_muli(font->factor, font->descent));

  return font;

fail:
  free(font);
  free(finfo);
  free(buf);
  if (freesrc && src != NULL) SDL_RWclose(src);
  return NULL;
}

void TTF_CloseFont(TTF_Font *font) {
  if (font == NULL) return;
  free(font->finfo);
  free(font->file.buf);
  if (font->src != NULL) SDL_RWclose(font->src);
  free(font);
}

int TTF_GlyphMetrics(TTF_Font *font, Uint16 ch, int *minx, int *maxx, int *miny, int *maxy, int *advance) {
  stbtt_fontinfo *finfo = font->finfo;
  int glyphIndex = stbtt_FindGlyphIndex(finfo, ch);
  if (glyphIndex == 0) return -1;
  int ret = stbtt_GetGlyphBox(finfo, glyphIndex, minx, miny, maxx, maxy);
  if (ret == 0) return -1;
  if (minx) *minx = fixedpt_toint(fixedpt_muli(font->factor, *minx));
  if (miny) *miny = fixedpt_toint(fixedpt_muli(font->factor, *miny));
  if (maxx) *maxx = fixedpt_toint(fixedpt_muli(font->factor, *maxx));
  if (maxy) *maxy = fixedpt_toint(fixedpt_muli(font->factor, *maxy));
  assert(advance == NULL); // not implemented
  return 0;
}

int TTF_FontAscent(TTF_Font *font) {
  return font->ascent;
}

int TTF_FontHeight(TTF_Font *font) {
  return font->height;
}

static struct {
  SDL_Color fg, bg;
  SDL_Color palette[256];
} palCache = {};

SDL_Surface *TTF_RenderGlyph_Shaded(TTF_Font *font, Uint16 ch, SDL_Color fg, SDL_Color bg) {
  stbtt_fontinfo *finfo = font->finfo;
  int glyphIndex = stbtt_FindGlyphIndex(finfo, ch);
  if (glyphIndex == 0) return NULL;
  int w, h;
  uint8_t *pixels = stbtt_GetGlyphBitmap(finfo, 0, font->factor, glyphIndex, &w, &h, NULL, NULL);

  SDL_Surface *s = SDL_CreateRGBSurfaceFrom(pixels, w, h, 8, w, 0, 0, 0, 0);
  s->flags &= ~SDL_PREALLOC;
  if (!(fg.val == palCache.fg.val && bg.val == palCache.bg.val)) {
    // cache miss
    int rdiff = fg.r - bg.r;
    int gdiff = fg.g - bg.g;
    int bdiff = fg.b - bg.b;
    int adiff = fg.a - bg.a;
    for (int i = 0; i < 256; i ++) {
      palCache.palette[i].r = bg.r + (i*rdiff) / 255;
      palCache.palette[i].g = bg.g + (i*gdiff) / 255;
      palCache.palette[i].b = bg.b + (i*bdiff) / 255;
      palCache.palette[i].a = bg.a + (i*adiff) / 255;
    }
    palCache.palette[0].a = bg.a;
    palCache.fg.val = fg.val;
    palCache.bg.val = bg.val;
  }
  memcpy(s->format->palette->colors, palCache.palette, sizeof(palCache.palette));
  return s;
}
