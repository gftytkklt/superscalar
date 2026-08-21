#include <nterm.h>
#include <stdarg.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <SDL.h>

char handle_key(SDL_Event *ev);

static void sh_printf(const char *format, ...) {
  static char buf[256] = {};
  va_list ap;
  va_start(ap, format);
  int len = vsnprintf(buf, 256, format, ap);
  va_end(ap);
  term->write(buf, len);
}

static void sh_banner() {
  sh_printf("Built-in Shell in NTerm (NJU Terminal)\n\n");
  // PATH 环境变量：支持直接键入程序名（如 "menu"）而不必键入完整路径
  // overwrite=0：若已存在则不覆盖（兼容 Navy native 上已有的 PATH）
  setenv("PATH", "/bin", 0);
}

static void sh_prompt() {
  sh_printf("sh> ");
}

static void sh_handle_cmd(const char *cmd) {
  // 取命令的第一个词作为程序名（暂不支持参数传递）
  char prog[128];
  int n = 0;
  while (cmd[n] != '\0' && cmd[n] != ' ' && cmd[n] != '\n' && n < (int)sizeof(prog) - 1) {
    prog[n] = cmd[n];
    n ++;
  }
  prog[n] = '\0';
  if (n == 0) return;

  // execvp 按 PATH 搜索程序；exec 成功后不返回，失败返回 -1
  char *argv[] = {prog, NULL};
  execvp(prog, argv);
  sh_printf("exec %s: bad thing happen\n", prog);
}

void builtin_sh_run() {
  sh_banner();
  sh_prompt();

  while (1) {
    SDL_Event ev;
    if (SDL_PollEvent(&ev)) {
      if (ev.type == SDL_KEYUP || ev.type == SDL_KEYDOWN) {
        const char *res = term->keypress(handle_key(&ev));
        if (res) {
          sh_handle_cmd(res);
          sh_prompt();
        }
      }
    }
    refresh_terminal();
  }
}
