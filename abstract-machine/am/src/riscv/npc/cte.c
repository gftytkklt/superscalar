#include <am.h>
#include <riscv/riscv.h>
#include <klib.h>

static Context* (*user_handler)(Event, Context*) = NULL;

Context* __am_irq_handle(Context *c) {
  if (user_handler) {
    Event ev = {0};
    switch (c->mcause) {
      case 0x0b: c->mepc += 4;ev.event = (c->gpr[17] == -1) ? EVENT_YIELD : EVENT_SYSCALL; break;
      case 0x8000000000000007: ev.event = EVENT_IRQ_TIMER; break;
      default: ev.event = EVENT_ERROR; break;
    }

    c = user_handler(ev, c);
    assert(c != NULL);
  }

  return c;
}

extern void __am_asm_trap(void);

bool cte_init(Context*(*handler)(Event, Context*)) {
  // initialize exception entry
  asm volatile("csrw mtvec, %0" : : "r"(__am_asm_trap));

  // register event handler
  user_handler = handler;

  return true;
}

Context *kcontext(Area kstack, void (*entry)(void *), void *arg) {
  Context *cp = (Context*)kstack.end - 1;
  // printf("kstack end addr:%p, cp addr:%p\n",kstack.end,cp);
  cp->mstatus = 0xa00001880;
  cp->mepc = (uintptr_t)entry;
  //printf("kernel entry: %lx\n",cp->mepc);
  cp->gpr[10] = (uintptr_t)arg;
  //cp->gpr[2] = (uintptr_t)cp;
  cp->gpr[2] = (uintptr_t)kstack.end;// sp should be end or end - CONTEXT_SIZE?
  cp->np = 0;
  cp->pdir = NULL;
  return cp;
}

void yield() {
#ifdef __riscv_e
  asm volatile("li a5, -1; ecall");
#else
  asm volatile("li a7, -1; ecall");
#endif
}

bool ienabled() {
  unsigned long mstatus;
  asm volatile ("csrr %0, mstatus" : "=r" (mstatus));
  return (mstatus & (1UL << 3)) != 0;
}

void iset(bool enable) {
  if(enable){
    asm volatile ("csrrs zero, mstatus, %0" :: "rK" (1 << 3));
  }
  else{
    asm volatile ("csrrc zero, mstatus, %0" :: "rK" (1 << 3));
  }
}