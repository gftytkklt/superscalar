#include <am.h>
#include <stdint.h>
extern int printf(const char *, ...);
intptr_t __am_cte_syscall(intptr_t,intptr_t,intptr_t,intptr_t);
static Context *echo(Event e, Context *c) { (void)e; c->GPRx=23; return c; }
int main(void) {
  intptr_t r=__am_cte_syscall(2,0x1234,0,0);
  printf("unregistered open: ret=%lx (input pathname), heap=%p..%p\n",(long)r,heap.start,heap.end);
  if(r!=0x1234 || heap.start!=0 || heap.end!=0) return 1;
  cte_init(echo);
  if(__am_cte_syscall(3,7,0,0)!=23) return 2;
  printf("registered handler return=23, Context bytes=%lu\n",(unsigned long)sizeof(Context));
  return 0;
}
