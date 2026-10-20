#include <stdio.h> 
#include <stdint.h> 
#include <stdlib.h>
#include <assert.h>
#include <limits.h>

struct BitmapHeader {
  uint16_t type;
  uint32_t filesize;
  uint32_t resv_1;
  uint32_t offset;
  uint32_t ih_size;
  uint32_t width;
  uint32_t height;
  uint16_t planes;
  uint16_t bitcount; // 1, 4, 8, or 24
  uint32_t compression;
  uint32_t sizeimg;
  uint32_t xres, yres;
  uint32_t clrused, clrimportant;
} __attribute__((packed));

void* BMP_Load(const char *filename, int *width, int *height) {
  if (!filename) return NULL;
  FILE *fp = fopen(filename, "rb");
  if (!fp) return NULL;

  struct BitmapHeader hdr;
  uint32_t *pixels = NULL;
  assert(sizeof(hdr) == 54);
  if (fread(&hdr, sizeof(hdr), 1, fp) != 1) goto fail;

  if (hdr.type != 0x4d42 || hdr.planes != 1 || hdr.ih_size < 40 ||
      hdr.ih_size > UINT32_MAX - 14 || hdr.offset < 14 + hdr.ih_size ||
      hdr.bitcount != 24 || hdr.compression != 0 ||
      hdr.width == 0 || hdr.width > INT_MAX ||
      hdr.height == 0 || hdr.height > INT_MAX) goto fail;
  int w = hdr.width;
  int h = hdr.height;
  if ((size_t)w > SIZE_MAX / sizeof(uint32_t) / (size_t)h ||
      (size_t)w > (SIZE_MAX - 3) / 3) goto fail;
  size_t line_off = ((size_t)w * 3 + 3) & ~(size_t)3;
  uint64_t offset = hdr.offset;
  if (offset > LONG_MAX ||
      (uint64_t)h > ((uint64_t)LONG_MAX - offset) / line_off) goto fail;
  long data_end = offset + (uint64_t)h * line_off;
  if (fseek(fp, 0, SEEK_END) != 0) goto fail;
  long file_size = ftell(fp);
  if (file_size < data_end) goto fail;
  pixels = malloc((size_t)w * h * sizeof(uint32_t));
  if (!pixels) goto fail;

  for (int i = 0; i < h; i ++) {
    long row_off = offset + (uint64_t)(h - 1 - i) * line_off;
    uint32_t *row = pixels + (size_t)w * i;
    if (fseek(fp, row_off, SEEK_SET) != 0 ||
        fread(row, 3, w, fp) != (size_t)w) goto fail;
    for (int j = w - 1; j >= 0; j --) {
      uint8_t *src = (uint8_t *)row + (size_t)3 * j;
      uint8_t b = src[0], g = src[1], r = src[2];
      row[j] = (r << 16) | (g << 8) | b;
    }
  }

  if (fclose(fp) != 0) {
    free(pixels);
    return NULL;
  }
  if (width) *width = w;
  if (height) *height = h;
  return pixels;

fail:
  free(pixels);
  fclose(fp);
  return NULL;
}
