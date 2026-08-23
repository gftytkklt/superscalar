#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main() {
  printf("busybox-test: exec busybox cat num\n");
  char *const argv1[] = {"/bin/busybox", "cat", "/share/files/num", NULL};
  char *const envp[] = {NULL};
  execve("/bin/busybox", argv1, envp);
  printf("exec busybox failed\n");
  return 0;
}