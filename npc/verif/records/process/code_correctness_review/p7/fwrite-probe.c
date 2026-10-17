/* Host LP64 probe using the actual newlib FILE and reent definitions.
 * Only external stream initialization/flush hooks are stubs. */
#include <stdio.h>
#include <reent.h>
static struct _reent state;
struct _reent *_impure_ptr = &state;
void __sinit(struct _reent *p) { p->__sdidinit = 1; }
int __swsetup_r(struct _reent *p, FILE *f) { (void)p; (void)f; return 0; }
int __swbuf_r(struct _reent *p, int c, FILE *f) { (void)p; (void)f; return c; }
int main(int argc, char **argv) {
  (void)argv;
  FILE f = {0};
  f._flags = __SWR | __SNBF;
  state.__sdidinit = 1;
  size_t size = argc == 1 ? 1 : 0;
  size_t count = argc == 1 ? 0 : 1;
  return p7_fwrite("x", size, count, &f) != 0;
}
