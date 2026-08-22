#include <am.h>
#include <klib.h>
#include <rtthread.h>

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
    case EVENT_IRQ_TIMER: break;
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

void rt_hw_context_switch_interrupt(void *context, rt_ubase_t from, rt_ubase_t to, struct rt_thread *to_thread) {
  assert(0);
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