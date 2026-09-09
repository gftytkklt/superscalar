#include <sdl-file.h>
#include <stdlib.h>
#include <string.h>

/* ---- file-backed RWops: operate on a FILE* ---- */

static int64_t file_size(SDL_RWops *f) {
  long cur = ftell(f->fp);
  fseek(f->fp, 0, RW_SEEK_END);
  long size = ftell(f->fp);
  fseek(f->fp, cur, RW_SEEK_SET);
  return size;
}

static int64_t file_seek(SDL_RWops *f, int64_t offset, int whence) {
  fseek(f->fp, (long)offset, whence);
  return ftell(f->fp);
}

static size_t file_read(SDL_RWops *f, void *buf, size_t size, size_t nmemb) {
  return fread(buf, size, nmemb, f->fp);
}

static size_t file_write(SDL_RWops *f, const void *buf, size_t size, size_t nmemb) {
  return fwrite(buf, size, nmemb, f->fp);
}

static int file_close(SDL_RWops *f) {
  fclose(f->fp);
  free(f);
  return 0;
}

/* ---- memory-backed RWops: read/write directly on mem.base ----
 * The position is stored in a wrapper so that mem.base/mem.size stay usable
 * by consumers that access the buffer directly (e.g. IMG_Load_RW). */

typedef struct {
  SDL_RWops rw;
  ssize_t pos;
} MemRW;

static int64_t mem_size(SDL_RWops *f) {
  return f->mem.size;
}

static int64_t mem_seek(SDL_RWops *f, int64_t offset, int whence) {
  ssize_t pos = ((MemRW *)f)->pos;
  switch (whence) {
    case RW_SEEK_SET: pos = offset; break;
    case RW_SEEK_CUR: pos += offset; break;
    case RW_SEEK_END: pos = f->mem.size + offset; break;
  }
  if (pos < 0) pos = 0;
  if (pos > f->mem.size) pos = f->mem.size;
  ((MemRW *)f)->pos = pos;
  return pos;
}

static size_t mem_read(SDL_RWops *f, void *buf, size_t size, size_t nmemb) {
  ssize_t pos = ((MemRW *)f)->pos;
  ssize_t avail = (pos < f->mem.size) ? (f->mem.size - pos) : 0;
  ssize_t need = size * nmemb;
  ssize_t n = (need < avail) ? need : avail;
  if (n > 0) memcpy(buf, (char *)f->mem.base + pos, n);
  ((MemRW *)f)->pos = pos + n;
  return (size > 0) ? (n / size) : 0;
}

static size_t mem_write(SDL_RWops *f, const void *buf, size_t size, size_t nmemb) {
  ssize_t pos = ((MemRW *)f)->pos;
  ssize_t avail = (pos < f->mem.size) ? (f->mem.size - pos) : 0;
  ssize_t need = size * nmemb;
  ssize_t n = (need < avail) ? need : avail;
  if (n > 0) memcpy((char *)f->mem.base + pos, buf, n);
  ((MemRW *)f)->pos = pos + n;
  return (size > 0) ? (n / size) : 0;
}

static int mem_close(SDL_RWops *f) {
  free((MemRW *)f);
  return 0;
}

/* ---- constructors ---- */

SDL_RWops* SDL_RWFromFile(const char *filename, const char *mode) {
  FILE *fp = fopen(filename, mode);
  if (fp == NULL) return NULL;
  SDL_RWops *rw = malloc(sizeof(SDL_RWops));
  if (rw == NULL) { fclose(fp); return NULL; }
  *rw = (SDL_RWops) {
    .size = file_size, .seek = file_seek,
    .read = file_read, .write = file_write, .close = file_close,
    .type = RW_TYPE_FILE, .fp = fp,
  };
  return rw;
}

SDL_RWops* SDL_RWFromMem(void *mem, int size) {
  MemRW *m = malloc(sizeof(MemRW));
  if (m == NULL) return NULL;
  m->pos = 0;
  m->rw = (SDL_RWops) {
    .size = mem_size, .seek = mem_seek,
    .read = mem_read, .write = mem_write, .close = mem_close,
    .type = RW_TYPE_MEM,
    .mem = { .base = mem, .size = size },
  };
  return &m->rw;
}