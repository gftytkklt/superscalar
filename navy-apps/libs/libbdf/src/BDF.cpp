#include <BDF.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <errno.h>
#include <limits.h>

static bool fields(const char *p, int *values, int count, int base = 10) {
  for (int i = 0; i < count; i ++) {
    char *end;
    errno = 0;
    long value = strtol(p, &end, base);
    if (end == p || errno == ERANGE || value < INT_MIN || value > INT_MAX) return false;
    values[i] = (int)value;
    p = end;
  }
  while (*p == ' ' || *p == '\t') p ++;
  return *p == '\0';
}

void BDF_Font::create(uint32_t ch, int *bbx, uint32_t *bitmap, int count) {
  delete [] font[ch];
  font[ch] = new uint32_t[h];
  for (int y = 0; y < h; y ++) {
    uint32_t row = 0;
    for (int x = 0; x < w; x ++) {
      int64_t x1 = (int64_t)x - bbx[2];
      int64_t y1 = (int64_t)y - ((int64_t)h - bbx[1] - bbx[3]) - h1;
      if (x1 >= 0 && x1 < 32 && y1 >= 0 && y1 < count) {
        if ((bitmap[y1] >> x1) & 1u) row |= UINT32_C(1) << x;
      }
    }
    font[ch][y] = row;
  }
}

BDF_Font::BDF_Font(const char *fname) : w1(0), h1(0), name(NULL), w(0), h(0) {
  memset(font, 0, sizeof(font));
  if (fname == NULL) return;
  FILE *fp = fopen(fname, "r");
  if (!fp) return;

  char buf[256], cmd[32];
  bool started = false, bounds = false, glyph = false, bbx = false;
  bool in_bitmap = false, ended = false, ok = true;
  uint32_t bm[32];
  int ch = 0, bm_idx = 0, bm_bbx[4] = {};

  while (fgets(buf, sizeof(buf), fp)) {
    size_t len = strlen(buf);
    if (len == sizeof(buf) - 1 && buf[len - 1] != '\n') { ok = false; break; }
    while (len && (buf[len - 1] == '\n' || buf[len - 1] == '\r')) buf[--len] = '\0';
    const char *p = buf;
    while (*p == ' ' || *p == '\t') p ++;
    size_t n = strcspn(p, " \t");
    if (n >= sizeof(cmd)) { ok = false; break; }
    memcpy(cmd, p, n); cmd[n] = '\0'; p += n;
    while (*p == ' ' || *p == '\t') p ++;

    if (in_bitmap && strcmp(cmd, "ENDCHAR") != 0) {
      size_t digits = (bm_bbx[0] + 7) / 8 * 2;
      if (bm_idx >= bm_bbx[1] || bm_idx >= 32 || len != digits) { ok = false; break; }
      uint32_t row = 0;
      for (size_t i = 0; i < digits; i ++) {
        char c = buf[i];
        int value = c >= '0' && c <= '9' ? c - '0' :
                    c >= 'A' && c <= 'F' ? c - 'A' + 10 :
                    c >= 'a' && c <= 'f' ? c - 'a' + 10 : -1;
        if (value < 0) { ok = false; break; }
        for (int bit = 0; bit < 4; bit ++)
          if ((value >> (3 - bit)) & 1) row |= UINT32_C(1) << (i * 4 + bit);
      }
      if (!ok) break;
      bm[bm_idx ++] = row;
    } else if (strcmp(cmd, "STARTFONT") == 0) {
      if (started) { ok = false; break; }
      started = true;
    } else if (strcmp(cmd, "FONTBOUNDINGBOX") == 0) {
      int box[4];
      if (!started || bounds || glyph || !fields(p, box, 4) ||
          box[0] <= 0 || box[0] > 32 || box[1] <= 0 || box[1] > 32) { ok = false; break; }
      w = box[0]; h = box[1]; w1 = box[2]; h1 = box[3]; bounds = true;
    } else if (strcmp(cmd, "STARTCHAR") == 0) {
      if (!bounds || glyph || !fields(p, &ch, 1, 16) || ch < 0) { ok = false; break; }
      glyph = true; bbx = false;
    } else if (strcmp(cmd, "BBX") == 0) {
      if (!glyph || bbx || !fields(p, bm_bbx, 4) ||
          bm_bbx[0] < 0 || bm_bbx[0] > 32 || bm_bbx[1] < 0 || bm_bbx[1] > 32) { ok = false; break; }
      bbx = true;
    } else if (strcmp(cmd, "BITMAP") == 0) {
      if (!glyph || !bbx) { ok = false; break; }
      in_bitmap = true; bm_idx = 0;
    } else if (strcmp(cmd, "ENDCHAR") == 0) {
      if (!glyph || !in_bitmap || bm_idx != bm_bbx[1]) { ok = false; break; }
      if (ch < 256) create(ch, bm_bbx, bm, bm_idx);
      in_bitmap = false; glyph = false;
    } else if (strcmp(cmd, "ENDFONT") == 0) {
      if (!bounds || glyph) { ok = false; break; }
      ended = true; break;
    }
  }

  if (ferror(fp)) ok = false;
  fclose(fp);
  if (!ok || !ended) {
    for (uint32_t *&pixels: font) { delete [] pixels; pixels = NULL; }
    w = h = w1 = h1 = 0;
  }
}

BDF_Font::~BDF_Font() {
  for (uint32_t *pixels: font) {
    delete [] pixels;
  }
}
