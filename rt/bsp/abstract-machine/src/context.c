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
} cp_addr_t;

static Context* ev_handler(Event e, Context *c) {
  switch (e.event) {
    case EVENT_YIELD: 
      cp_addr_t *cp_addr = (cp_addr_t*) rt_thread_self()->user_data;
      if(cp_addr->from != 0){
      // if(1){
        *((Context**) cp_addr->from) = c;
      }
      c = *((Context**) cp_addr->to);
      break;
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
    .to = to
  };
  rt_thread_self()->user_data = (rt_ubase_t) &cp_addr;
  yield();
  rt_thread_self()->user_data = userdata;
}

void rt_hw_context_switch(rt_ubase_t from, rt_ubase_t to) {
  rt_ubase_t userdata = rt_thread_self()->user_data;
  cp_addr_t cp_addr = {
    .from = from,
    .to = to
  };
  rt_thread_self()->user_data = (rt_ubase_t) &cp_addr;
  yield();
  rt_thread_self()->user_data = userdata;
}

void rt_hw_context_switch_interrupt(void *context, rt_ubase_t from, rt_ubase_t to, struct rt_thread *to_thread) {
  assert(0);
}

rt_uint8_t *rt_hw_stack_init(void *tentry, void *parameter, rt_uint8_t *stack_addr, void *texit) {
  // stack_addr = (rt_uint8_t*)((uintptr_t)stack_addr & ~(sizeof(uintptr_t) - 1));
  // rt_uint8_t* stk = stack_addr+sizeof(rt_ubase_t);
  // stk = (rt_uint8_t*)RT_ALIGN_DOWN((rt_ubase_t)stk, sizeof(uintptr_t));
  // rt_uint8_t* stk = (rt_uint8_t*)((uintptr_t)stack_addr & ~(sizeof(uintptr_t) - 1));
  // Context *cp = kcontext((Area) {stk-0x8000, stk}, tentry, (void*) parameter);
  // cp->gpr[1] = (uintptr_t)texit;
  // printf("cp: %p, tentry: %p, texit: %p, para: %p, stack: %p, stk: %p\n", cp, tentry, texit, parameter, stack_addr, stk);
  // return (rt_uint8_t *) cp;
  
  /* this version can run in native, but failed in nemu */
  // set parameter wrapper
  context_args_t *ctx_args = (context_args_t*) rt_malloc(sizeof(context_args_t));
  ctx_args->tentry = tentry;
  ctx_args->parameter = parameter;
  ctx_args->texit = texit;
  // set context parameter
  rt_uint8_t* stk = stack_addr+sizeof(rt_ubase_t);
  stk = (rt_uint8_t*)RT_ALIGN_DOWN((rt_ubase_t)stk, sizeof(uintptr_t));
  Context *cp = kcontext((Area) {stk-0x8000, stk}, wrapper_function, (void*) ctx_args);
  printf("cp: %p, tentry: %p, texit: %p, para: %p, stack: %p\n", cp, tentry, texit, parameter, stack_addr);
  return (rt_uint8_t *) cp;
}