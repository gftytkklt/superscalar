#include <reent.h>
#include <stdint.h>
#include <sys/types.h>
extern int printf(const char *, ...);
int p7_low_errno;
long _read(int fd, void *p, size_t n) { (void)fd; (void)p; (void)n; return 0x100000003L; }
long _write(int fd, const void *p, size_t n) { (void)fd; (void)p; (void)n; return 0x80000003L; }
long _lseek(int fd, long off, int w) { (void)fd; (void)off; (void)w; return 0x100000005L; }
int main(void) {
  struct _reent r={0};
  long a=_read_r(&r,0,0,0), b=_write_r(&r,0,0,0), c=_lseek_r(&r,0,0,0);
  printf("mock 64bit syscall returns: read=%ld write=%ld lseek=%ld\n",a,b,c);
  return !(a==3 && b==-2147483645L && c==5);
}
