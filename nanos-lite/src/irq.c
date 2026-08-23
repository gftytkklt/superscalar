#include <common.h>
void do_syscall(Context *c);
#if defined(MULTITASK) || defined(TEST_NTERM)
Context* schedule(Context *prev);
#endif
static Context* do_event(Event e, Context* c) {
  switch (e.event) {
#if defined(MULTITASK) || defined(TEST_NTERM)
    case EVENT_YIELD: return schedule(c);
#endif
    case EVENT_SYSCALL: do_syscall(c); break;
    case EVENT_IRQ_TIMER: return c;
    default: panic("Unhandled event ID = %d", e.event);
  }

  return c;
}

void init_irq(void) {
  Log("Initializing interrupt/exception handler...");
  cte_init(do_event);
}
