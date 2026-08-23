#include <common.h>
#include <fs.h>
#include <proc.h>
#include "syscall.h"
#include <sys/time.h>
#include <time.h>

// 展示批处理系统：程序退出后再次运行的程序
#define BATCH_INIT_PROG "/bin/nterm"

int sys_execve(const char *fname, char * const argv[], char *const envp[]) {
  // load the new program into the current process, then abandon the current
  // execution flow: switch to the boot PCB (never scheduled) and yield, so the
  // next schedule() resumes the newly loaded program.
  context_uload(current, fname, argv, envp);
  switch_boot_pcb();
  yield();
  return 0;
}

void sys_exit(uintptr_t code) {
  // 不再直接 halt 整个系统，而是重新运行批处理系统的初始程序
  char *const argv[] = {BATCH_INIT_PROG, NULL};
  char *const envp[] = {NULL};
  sys_execve(BATCH_INIT_PROG, argv, envp);
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
  return fs_write(fd, buf, count);
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

int sys_gettimeofday(struct timeval *tv, struct timezone *tz){
  long us = io_read(AM_TIMER_UPTIME).us;
  tv->tv_sec = us / 1000000;
  tv->tv_usec = us % 1000000;
  return 0;
}

#ifdef STRACE
// 系统调用号 -> 名字的映射（供 strace 使用）
static const char *syscall_names[] = {
  [SYS_exit]         = "exit",
  [SYS_yield]        = "yield",
  [SYS_open]         = "open",
  [SYS_read]         = "read",
  [SYS_write]        = "write",
  [SYS_kill]         = "kill",
  [SYS_getpid]       = "getpid",
  [SYS_close]        = "close",
  [SYS_lseek]        = "lseek",
  [SYS_brk]          = "brk",
  [SYS_fstat]        = "fstat",
  [SYS_time]         = "time",
  [SYS_signal]       = "signal",
  [SYS_execve]       = "execve",
  [SYS_fork]         = "fork",
  [SYS_link]         = "link",
  [SYS_unlink]       = "unlink",
  [SYS_wait]         = "wait",
  [SYS_times]        = "times",
  [SYS_gettimeofday] = "gettimeofday",
};

static const char *syscall_name(int id) {
  if (id >= 0 && id < (int)LENGTH(syscall_names)) return syscall_names[id];
  return "???";
}
#endif

void do_syscall(Context *c) {
  uintptr_t a[4];
  a[0] = c->GPR1;
  a[1] = c->GPR2;
  a[2] = c->GPR3;
  a[3] = c->GPR4;

#ifdef STRACE
  Log("syscall %s(%ld, %ld, %ld)", syscall_name(a[0]), a[1], a[2], a[3]);
#endif

  long ret = 0;
  switch (a[0]) {
    case SYS_exit: sys_exit(a[1]);break;   // noreturn，不会执行到下方的返回值设置与打印
    case SYS_yield: ret = sys_yield();break;
    case SYS_open: ret = sys_open((const char *)a[1], (int)a[2], (int) a[3]);break;
    case SYS_read: ret = sys_read((int)a[1],(void*)a[2],(size_t)a[3]);break;
    case SYS_write: ret = sys_write((int)a[1],(void*)a[2],(size_t)a[3]);break;
    case SYS_close: ret = sys_close((int)a[1]);break;
    case SYS_lseek: ret = sys_lseek((int)a[1],(long)a[2],(int)a[3]);break;
    case SYS_brk: ret = sys_brk((void*)a[1]);break;
    case SYS_gettimeofday: ret = sys_gettimeofday((struct timeval *)a[1], (struct timezone *)a[2]);break;
    case SYS_execve: sys_execve((const char *)a[1], (char * const *)a[2], (char *const *)a[3]);break;  // 成功时不返回
    default: panic("Unhandled syscall ID = %d", a[0]);
  }
  c->GPRx = ret;

#ifdef STRACE
  Log("syscall %s -> %ld", syscall_name(a[0]), ret);
#endif
}
