#include <common.h>
#include <fs.h>
#include "syscall.h"

void sys_exit(uintptr_t code) {
  halt(code);
}

int sys_yield() {
  yield();
  return 0;
}

int sys_open(const char *pathname, int flags, int mode) {
  return fs_open(pathname, flags, mode);
}

long sys_read(int fd, void *buf, size_t len){
  return fs_read(fd, buf, len);
}

long sys_write(int fd, void *buf, size_t count) {
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
  #elif defined(TEST_FILE)
    return fs_write(fd, buf, count);
  #endif
}

int sys_close(int fd){
  return fs_close(fd);
}

long sys_lseek(int fd, size_t offset, int whence){
  return fs_lseek(fd, offset, whence);
}

int sys_brk(void *addr) {
  return 0;
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
    case SYS_open: c->GPRx = sys_open((const char *)a[1], (int)a[2], (int) a[3]);break;
    case SYS_read: c->GPRx = sys_read((int)a[1],(void*)a[2],(size_t)a[3]);break;
    case SYS_write: c->GPRx = sys_write((int)a[1],(void*)a[2],(size_t)a[3]);break;
    case SYS_close: c->GPRx = sys_close((int)a[1]);break;
    case SYS_lseek: c->GPRx = sys_lseek((int)a[1],(long)a[2],(int)a[3]);break;
    case SYS_brk: c->GPRx = sys_brk((void*)a[1]);break;
    default: panic("Unhandled syscall ID = %d", a[0]);
  }
}
