/* CCR-P9 controlled payload. Production crt0, libos and selected newlib units
 * remain unmodified. Only __assert_func below is a fixture failure sink. */
#include <stdint.h>
#include <stddef.h>
#include <sys/time.h>
#include <errno.h>
#include <string.h>
#include <stdlib.h>
extern intptr_t _syscall_(intptr_t, intptr_t, intptr_t, intptr_t);
extern int _open(const char *, int, unsigned int);
extern long _read(int, void *, size_t);
extern long _write(int, void *, size_t);
extern long _lseek(int, long, int);
extern int _close(int);
extern int _execve(const char *, char *const [], char *const []);
extern int _gettimeofday(struct timeval *, struct timezone *);
extern void *_sbrk(intptr_t);
static void say(const char *s) { _write(1, (void *)s, strlen(s)); }
static void stop(int n) { asm volatile("mv a0,%0; ebreak"::"r"((intptr_t)n)); for (;;) {} }
void __assert_func(const char *f, int l, const char *fn, const char *e) {
  (void)f;(void)l;(void)fn;(void)e;say("P9_ASSERT_FAILURE\n");stop(99);
}
#define REQUIRE(c) do { if (!(c)) { say("P9_CHECK_FAILURE " #c "\n");stop(98); } } while (0)
int main(int argc, char **argv, char **envp) {
  REQUIRE(argc > 0 && argv[argc] == 0 && envp != 0);
  if (!strcmp(argv[0], "P9_EXEC")) {
    REQUIRE(argc == 1 && envp[0] && !strcmp(envp[0], "P9=ok") && !envp[1]);
    say("P9_EXEC_NEW_CONTEXT\n");
    return 0; /* actual crt0 -> newlib exit -> _exit -> nanos reload nterm */
  }
  if (!strcmp(argv[0], "/bin/nterm")) {
    say("P9_EXIT_RELOADED_NTERM\n");stop(0); /* explicit harness success terminator */
  }
  if (strcmp(argv[0], "/bin/pal")) {
    for (;;) _syscall_(1,0,0,0); /* background fixture yields */
  }
  say("P9_USER_START\n");
  int fd = _open("/data/check",0,0); REQUIRE(fd >= 8);
  char b[8] = {0};
  REQUIRE(_read(fd,b,4) == 4 && !memcmp(b,"ABCD",4));
  REQUIRE(_lseek(fd,-2,2) == 5);
  REQUIRE(_read(fd,b,8) == 2 && !memcmp(b,"FG",2));
  REQUIRE(_read(fd,b,0) == 0 && _read(fd,b,1) == 0);
  REQUIRE(_close(fd) == 0 && _open("/missing",0,0) == -1);
  say("P9_FILE_EOF_SEEK_CLOSE\n");
  struct timeval tv={0}; REQUIRE(_gettimeofday(&tv,0)==0 && tv.tv_sec>=0 && tv.tv_usec>=0 && tv.tv_usec<1000000);
  say("P9_TIME_RETURN\n");
  char *args[] = {"P9_EXEC",0}; char *env[] = {"P9=ok",0};
  REQUIRE(_execve("/missing",args,env)==-1 && errno==2);
  say("P9_EXEC_MISSING_RETURN\n");
  REQUIRE(_sbrk(32)!=(void *)-1);
  say("P9_BRK_RETURN\n");
  say("P9_BEFORE_YIELD\n");_syscall_(1,0,0,0);say("P9_AFTER_YIELD\n");
  say("P9_BEFORE_EXEC\n");_execve("/bin/nslider",args,env);
  say("P9_EXEC_UNEXPECTED_RETURN\n");stop(97);
  return 97;
}
