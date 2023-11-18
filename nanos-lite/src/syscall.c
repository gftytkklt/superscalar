#include <common.h>
#include "syscall.h"

void sys_exit(uintptr_t code){
  #ifdef TEST_DUMMY
  halt(code);
  #endif
}

int sys_yield(){
  yield();
  return 0;
}

int sys_brk(void *addr){
  #ifdef TEST_DUMMY
    return 0;
  #endif
}

long sys_write(int fd, void *buf, size_t count){
  #ifdef TEST_DUMMY
    if(fd == 1 || fd == 2){
      size_t i = 0;
      char *tmp = (char*) buf;
      while((i < count) && (tmp[i] != '\0')){
        putch(tmp[i]);
        i++;
      }
      return i;
    }
    else{
      return -1;
    }
  #endif
}

void do_syscall(Context *c) {
  uintptr_t a[4];
  a[0] = c->GPR1;
  a[1] = c->GPR2;
  a[2] = c->GPR3;
  a[3] = c->GPR4;

  switch (a[0]) {
    case SYS_exit: sys_exit(a[1]);break;
    case SYS_yield: c->GPRx = sys_yield();break;
    case SYS_write: c->GPRx = sys_write((int)a[1],(void*)a[2],(size_t)a[3]);break;
    case SYS_brk: c->GPRx = sys_brk((void*)a[1]);break;
    default: panic("Unhandled syscall ID = %d", a[0]);
  }
}
