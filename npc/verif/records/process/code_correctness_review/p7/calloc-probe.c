/* Tests production callocr template's argument handling, not malloc internals. */
#include <stdlib.h>
#include <stdint.h>
#include <reent.h>
extern int printf(const char *, ...);
static struct _reent state;
struct _reent *_impure_ptr = &state;
static size_t seen;
void *_malloc_r(struct _reent *r, size_t n) { (void)r; seen = n; return NULL; }
int main(void) {
  _calloc_r(&state, 3, 8);
  if (seen != 24) return 2;
  _calloc_r(&state, (SIZE_MAX / 2) + 2, 2);
  printf("calloc request overflow: allocator received %lu bytes\n", (unsigned long)seen);
  return seen == 2 ? 0 : 3;
}
