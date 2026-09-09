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
  // 把命令行按空白切分成 argv[]，支持参数传递
  char cmd_buf[128];
  strncpy(cmd_buf, cmd, sizeof(cmd_buf) - 1);
  cmd_buf[sizeof(cmd_buf) - 1] = '\0';

  char *argv[16];
  int argc = 0;
  char *p = cmd_buf;
  while (*p && argc < (int)(sizeof(argv)/sizeof(argv[0])) - 1) {
    while (*p == ' ' || *p == '\t' || *p == '\n') p ++;   // skip whitespace
    if (*p == '\0') break;
    argv[argc ++] = p;
    while (*p && *p != ' ' && *p != '\t' && *p != '\n') p ++;
    if (*p) *p ++ = '\0';
  }
  argv[argc] = NULL;
  if (argc == 0) return;

  // execvp 按 PATH 搜索程序；exec 成功后不返回，失败返回 -1
  execvp(argv[0], argv);
  sh_printf("exec %s: bad thing happen\n", argv[0]);
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
