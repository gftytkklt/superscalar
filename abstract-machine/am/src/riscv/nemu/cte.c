#include <am.h>
#include <riscv/riscv.h>
#include <klib.h>
#define CONTEXT_SIZE 288
static Context* (*user_handler)(Event, Context*) = NULL;

Context* __am_irq_handle(Context *c) {
  uintptr_t ksp = 0;
  // record the current address space into the context
  __am_get_cur_as(c);

  if (user_handler) {
    Event ev = {0};
    // Determine the next privilege (np): trap.S swapped mscratch into sp, so
    // mscratch now holds the original sp. It is non-zero for a user trap and
    // 0 for a kernel trap (kernel threads never have mscratch armed).
    asm volatile("csrr %0, mscratch" : "=r"(ksp));
    c->np = (ksp == 0) ? KERNEL_MODE : USER_MODE;
    ksp = 0;
    asm volatile("csrw mscratch, %0" : : "r"(ksp)); // support re-entry of CTE

    switch (c->mcause) {
      case 0x0b: case 0x8: c->mepc += 4;ev.event = (c->gpr[17] == -1) ? EVENT_YIELD : EVENT_SYSCALL; break;
      case 0x8000000000000007: ev.event = EVENT_IRQ_TIMER; break;
      default: ev.event = EVENT_ERROR; break;
    }

    c = user_handler(ev, c);
    assert(c != NULL);
  }

  // switch to the address space of the process to be resumed
  __am_switch(c);

  // Before returning to a user context, arm mscratch with that context's kernel
  // stack top, so the next user trap can switch to the kernel stack.
  if (c->np == USER_MODE) {
    ksp = (uintptr_t)c + CONTEXT_SIZE;
    asm volatile("csrw mscratch, %0" : : "r"(ksp));
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
  cp->mstatus = 0xa00001880;
  cp->mepc = (uintptr_t)entry;
  cp->gpr[10] = (uintptr_t)arg;
  cp->gpr[2] = (uintptr_t)kstack.end; // kernel thread starts on the top of its kernel stack
  cp->np = KERNEL_MODE;
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
  // return false;
}

void iset(bool enable) {
  if(enable){
    // printf("enable intr\n");
    asm volatile ("csrrs zero, mstatus, %0" :: "rK" (1 << 3));
  }
  else{
    // printf("disable intr\n");
    asm volatile ("csrrc zero, mstatus, %0" :: "rK" (1 << 3));
  }
}
