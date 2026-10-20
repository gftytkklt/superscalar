#include <am.h>
#include <klib.h>
#include <klib-macros.h>
#include <rtthread.h>
#include <rthw.h>

static uint64_t tick_time_us;
static uint64_t tick_fraction;
static rt_ubase_t irq_from, irq_to;

typedef struct {
  void (*tentry)(void*);
  void *parameter;
  void (*texit)(void);
} context_args_t;

typedef struct{
  rt_ubase_t from;
  rt_ubase_t to;
  rt_ubase_t saved_user_data;
} cp_addr_t;

static Context* ev_handler(Event e, Context *c) {
  switch (e.event) {
    case EVENT_YIELD: {
      struct rt_thread *self = rt_thread_self();
      cp_addr_t *cp_addr = (cp_addr_t*) self->user_data;
      // restore user_data before the destination thread resumes
      self->user_data = cp_addr->saved_user_data;
      if(cp_addr->from != 0){
        *((Context**) cp_addr->from) = c;
      }
      c = *((Context**) cp_addr->to);
      break;
    }
    case EVENT_IRQ_TIMER: {
      rt_interrupt_enter();
      uint64_t now = io_read(AM_TIMER_UPTIME).us;
      uint64_t elapsed = now - tick_time_us;
      tick_time_us = now;
      // Preserve fractional ticks; an IRQ is a delivery opportunity, not a tick.
      uint64_t fraction = (elapsed % 1000000) * RT_TICK_PER_SECOND + tick_fraction;
      uint64_t ticks = (elapsed / 1000000) * RT_TICK_PER_SECOND + fraction / 1000000;
      tick_fraction = fraction % 1000000;
      while (ticks-- != 0) rt_tick_increase();
      rt_interrupt_leave();
      if (rt_interrupt_get_nest() == 0 && irq_from != 0) {
        *((Context **)irq_from) = c;
        c = *((Context **)irq_to);
        irq_from = irq_to = 0;
      }
      break;
    }
    default: printf("Unhandled event ID = %d\n", e.event); assert(0);
  }
  return c;
}

void wrapper_function(void *arg) {
  context_args_t *ctx_args = (context_args_t *)arg;
  ctx_args->tentry(ctx_args->parameter);
  ctx_args->texit();
}

void __am_cte_init() {
  tick_time_us = io_read(AM_TIMER_UPTIME).us;
  tick_fraction = 0;
  irq_from = irq_to = 0;
  cte_init(ev_handler);
}

void rt_hw_context_switch_to(rt_ubase_t to) {
  rt_ubase_t userdata = rt_thread_self()->user_data;
  cp_addr_t cp_addr = {
    .from = 0,
    .to = to,
    .saved_user_data = userdata
  };
  rt_thread_self()->user_data = (rt_ubase_t) &cp_addr;
  yield();
}

void rt_hw_context_switch(rt_ubase_t from, rt_ubase_t to) {
  rt_ubase_t userdata = rt_thread_self()->user_data;
  cp_addr_t cp_addr = {
    .from = from,
    .to = to,
    .saved_user_data = userdata
  };
  rt_thread_self()->user_data = (rt_ubase_t) &cp_addr;
  yield();
}

void rt_hw_context_switch_interrupt(rt_ubase_t from, rt_ubase_t to,
                                  rt_thread_t from_thread, rt_thread_t to_thread) {
  // Several catch-up ticks may schedule: save the interrupted thread only once.
  if (irq_from == 0) irq_from = from;
  irq_to = to;
}

rt_uint8_t *rt_hw_stack_init(void *tentry, void *parameter, rt_uint8_t *stack_addr, void *texit) {
  // stack_addr points to the top of the thread stack minus one word.
  // Recover the real top and align it.
  rt_uint8_t *top = (rt_uint8_t *)RT_ALIGN_DOWN((rt_ubase_t)(stack_addr + sizeof(rt_ubase_t)), 16);

  // Put the wrapper args on the thread's own stack (above the Context, so the
  // downward-growing stack never overwrites them). This avoids shared/heap
  // memory, which is exactly what the讲义 warns about.
  rt_uint8_t *args_addr = (rt_uint8_t *)RT_ALIGN_DOWN((rt_ubase_t)(top - sizeof(context_args_t)), 16);
  context_args_t *ctx_args = (context_args_t *)args_addr;
  ctx_args->tentry = tentry;
  ctx_args->parameter = parameter;
  ctx_args->texit = texit;

  // kcontext() only uses kstack.end: it places the Context at end - sizeof(Context).
  // After restore, sp = kstack.end = args_addr, so the args (located above sp)
  // remain valid throughout the wrapper's execution.
  Context *cp = kcontext((Area) { args_addr - sizeof(Context), args_addr }, wrapper_function, ctx_args);
  return (rt_uint8_t *) cp;
}
