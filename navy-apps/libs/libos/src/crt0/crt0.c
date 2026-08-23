#include <stdint.h>
#include <stdlib.h>
#include <assert.h>

int main(int argc, char *argv[], char *envp[]);
extern char **environ;
void __libc_init_array(void);
void call_main(uintptr_t *args) {
  int argc = (int)args[0];
  char **argv = (char **)(args + 1);
  char **envp = (char **)(argv + argc + 1);
  environ = envp;
  // 遍历 .init_array，执行 C++ 全局对象构造函数（如 RIX 解码器 Adplug 的全局对象）
  __libc_init_array();
  exit(main(argc, argv, envp));
  assert(0);
}
