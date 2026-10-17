#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
#include <reent.h>
#include <sys/types.h>
extern int printf(const char *, ...);
static struct _reent state;
struct _reent *_impure_ptr = &state;
int p7_low_errno;
int *p7_errno(void) { return &state._errno; }
char end;
extern void *program_break;
extern void *p7_sbrk(intptr_t);
static intptr_t result, last[4];
intptr_t p7_ecall(intptr_t n, intptr_t a, intptr_t b, intptr_t c) {
  last[0]=n; last[1]=a; last[2]=b; last[3]=c;
  return result;
}
int main(void) {
  state._errno=77; result=-1;
  int o=_open_r(&state,"missing",0,0);
  printf("open ret=%d high_errno=%d low_errno=%d\n",o,state._errno,p7_low_errno);
  if(o!=-1 || state._errno!=77 || p7_low_errno!=0) return 1;
  result=-2; state._errno=77;
  int e=_execve_r(&state,"missing",NULL,NULL);
  printf("exec default reent ret=%d high_errno=%d low_errno=%d\n",e,state._errno,p7_low_errno);
  if(e!=-1 || state._errno!=2) return 2;
  struct _reent separate={0}; separate._errno=99;
  e=_execve_r(&separate,"missing",NULL,NULL);
  printf("exec separate reent ret=%d requested_errno=%d global_errno=%d\n",e,separate._errno,state._errno);
  if(e!=-1 || separate._errno!=99) return 3;
  result=0; program_break=(void *)0x40010000;
  void *a=p7_sbrk(16); void *b=p7_sbrk(-8);
  printf("sbrk normal old=%p then=%p current=%p\n",a,b,program_break);
  if(a!=(void *)0x40010000 || b!=(void *)0x40010010 || program_break!=(void *)0x40010008) return 4;
  result=-1; a=p7_sbrk(16);
  printf("sbrk failure=%p current=%p\n",a,program_break);
  if(a!=(void *)-1 || program_break!=(void *)0x40010008) return 5;
  return 0;
}
