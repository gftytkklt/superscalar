#include <am.h>
#include <stdlib.h>
#include <unistd.h>

Area heap;

// 宿主直写：绕过 guest 自身的 libos/libc 系统调用链，直接对宿主发真实陷入。
// 对 guest 内核而言这就是它的"串口寄存器"；对普通应用而言是无缓冲的逐字符输出。
static void __am_host_write(int fd, const void *buf, size_t len) {
#ifdef __riscv
  // SYS_write = 4（Nanos-lite 系统调用号，见 libos/src/syscall.h）
  register long a7 asm("a7") = 4;
  register long a0 asm("a0") = fd;
  register long a1 asm("a1") = (long)buf;
  register long a2 asm("a2") = len;
  asm volatile("ecall" : "+r"(a0) : "r"(a1), "r"(a2), "r"(a7) : "memory");
#else
  write(1, buf, len);
#endif
}

void putch(char ch) {
  __am_host_write(1, &ch, 1);
}

void halt(int code) {
  exit(code);

  // should not reach here
  while (1);
}