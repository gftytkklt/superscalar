#include <am.h>
#include <klib.h>
#include <rtthread.h>
extern Area am_apps_heap, am_apps_data, am_apps_bss;
extern uint8_t * am_apps_data_content;
static void am_app_start_thread(void *args) {
  void (*fn)(const char *mainargs) = ((void **)args)[0];
  const char *mainargs = ((void **)args)[1];
  fn(mainargs);
}
static void am_app_start_wrapper(const char *app_name, void *app_main, int argc, char *argv[]) {
  memcpy(am_apps_data.start, am_apps_data_content, am_apps_data.end - am_apps_data.start);
  memset(am_apps_bss.start, 0, am_apps_bss.end - am_apps_bss.start);
  heap = am_apps_heap;
  void *args[2] = { app_main, (argc >= 2 ? argv[1] : "") };
  rt_thread_t tid = rt_thread_create(app_name, am_app_start_thread, args, 0x4000, 0, 20);
  rt_thread_startup(tid);
}
bool __dummy_ioe_init() { return true; }
bool __dummy_cte_init(Context *(*handler)(Event ev, Context *ctx)) { return true; }
bool __dummy_vme_init(void *(*pgalloc)(int), void (*pgfree)(void *)) { return true; }
bool __dummy_mpe_init(void (*entry)()) { return true; }
void __rt_am_halt(int code) {
  void rt_thread_exit(void);
  rt_thread_exit();
}
extern int __am_hello_main(const char *);
static void am_hello(int argc, char *argv[]) {
  am_app_start_wrapper("hello", __am_hello_main, argc, argv);
}
MSH_CMD_EXPORT(am_hello, AM hello);
extern int __am_microbench_main(const char *);
static void am_microbench(int argc, char *argv[]) {
  am_app_start_wrapper("microbench", __am_microbench_main, argc, argv);
}
MSH_CMD_EXPORT(am_microbench, AM microbench);
extern int __am_typing_game_main(const char *);
static void am_typing_game(int argc, char *argv[]) {
  am_app_start_wrapper("typing_game", __am_typing_game_main, argc, argv);
}
MSH_CMD_EXPORT(am_typing_game, AM typing_game);
