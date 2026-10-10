// Actual nanos-lite scheduling/event code; stub only loader, AM, and syscalls.
#include <proc.h>
#include <stdlib.h>
#include <stdio.h>
static Context contexts[4], boot_context;
static PCB *loaded[4];
static int load_count, key;
static Context *(*handler)(Event, Context *);
void init_proc(void);
void init_irq(void);
size_t events_read(void *, size_t, size_t);
int context_uload(PCB *pcb, const char *file, char *const argv[], char *const envp[]) {
  loaded[load_count] = pcb;
  pcb->cp = &contexts[load_count++];
  return 0;
}
bool cte_init(Context *(*h)(Event, Context *)) { handler = h; return true; }
void ioe_read(int reg, void *buf) {
  if (reg != AM_INPUT_KEYBRD) abort();
  *(AM_INPUT_KEYBRD_T *)buf = (AM_INPUT_KEYBRD_T){ .keydown = true, .keycode = key };
  key = AM_KEY_NONE;
}
void do_syscall(Context *c) { abort(); }
void halt(int code) { exit(code ? code : 1); }
static Context *event(int id, Context *ctx) { return handler((Event){.event = id}, ctx); }
#define CHECK(x) do { if (!(x)) abort(); } while (0)
int main(void) {
  init_proc(); init_irq(); CHECK(load_count == 4);
  Context *ctx = event(EVENT_YIELD, &boot_context);
  CHECK(current == loaded[0] && ctx == &contexts[0]);
  ctx = event(EVENT_IRQ_TIMER, ctx); CHECK(current == loaded[3]);
  ctx = event(EVENT_IRQ_TIMER, ctx); CHECK(current == loaded[0]);
  int keys[] = {AM_KEY_F2, AM_KEY_F3, AM_KEY_F1};
  int targets[] = {1, 2, 0};
  for (int i = 0; i < 3; i++) {
    PCB *before = current;
    key = keys[i]; char buf[64];
    CHECK(events_read(buf, 0, sizeof(buf)) == 0);
    CHECK(current == before && fg_pcb == loaded[targets[i]]);
    ctx = event(EVENT_IRQ_TIMER, ctx); CHECK(current == fg_pcb);
    ctx = event(EVENT_IRQ_TIMER, ctx); CHECK(current == loaded[3]);
    ctx = event(EVENT_IRQ_TIMER, ctx); CHECK(current == fg_pcb);
  }
  puts("nanos-lite actual IRQ/events/scheduler: FG/hello + F2/F3/F1 PASS");
}
