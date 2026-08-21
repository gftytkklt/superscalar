#include <am.h>
#include <klib-macros.h>
#include <string.h>

// =====================================================================
// libam CTE: 在 Navy 运行时上模拟自陷(trap)与上下文切换
//
// 设计思路
//   用户程序无法获得真实硬件自陷，因此 CTE 必须借助宿主机制模拟：
//   - native (Linux, glibc): 用 sigaction 捕获 guest 的 trap 指令
//     (SIGILL/SIGSYS) 与定时器 (SIGALRM)，用 ucontext 读取/恢复寄存器，
//     把"陷入"投递给 guest 注册的 CTE handler。
//   - 其它 ISA (Nanos-lite/NEMU 宿主，无信号): 退化为软件自陷 ——
//     yield/syscall 直接调用 __am_irq_handle()，不做真实 trap。
//
// Context 布局与 AM riscv 一致:
//   gpr[32], mcause, mstatus, mepc, np
//   GPR1=gpr[17](a7), GPR2=gpr[10](a0), GPR3=gpr[11], GPR4=gpr[12], GPRx=gpr[10]
//
// 说明：完整的多进程调度需要按 guest 进程保存/恢复 ucontext_t，
//   __am_switch_to() 是该扩展点，当前仅提供软件自陷路径的占位实现。
// =====================================================================

static Context *(*cte_handler)(Event ev, Context *ctx) = NULL;
static bool irq_enabled = true;

// 软件自陷下的"当前上下文"（不做真实寄存器保存）
static Context current_ctx;

static void __am_switch_to(Context *next);

static Context *__am_irq_handle(Event ev, Context *ctx) {
  Context *next = ctx;
  if (cte_handler != NULL) next = cte_handler(ev, ctx);
  return next;
}

// ---------- 软件化系统调用（最后一环） ----------
// guest 的 libos _syscall_ 通过弱符号钩子(__am_cte_syscall)转到这里，
// 以"函数调用"模拟陷入：把系统调用投递给 guest 注册的 CTE handler。
// 系统调用号/参数通过 GPR1..GPR4 传递，返回值经 GPRx 取回。
intptr_t __am_cte_syscall(intptr_t type, intptr_t a0, intptr_t a1, intptr_t a2) {
  current_ctx.GPR1 = type;
  current_ctx.GPR2 = a0;
  current_ctx.GPR3 = a1;
  current_ctx.GPR4 = a2;
  Event ev = { .event = EVENT_SYSCALL, .cause = type, .ref = (uintptr_t)&current_ctx };
  Context *next = cte_handler != NULL ? cte_handler(ev, &current_ctx) : &current_ctx;
  return next != NULL ? next->GPRx : 0;
}

void yield(void) {
  Context *next = __am_irq_handle((Event) { .event = EVENT_YIELD }, &current_ctx);
  if (next != NULL) __am_switch_to(next);
}

// ---------- 中断开关（软件屏蔽位） ----------
bool ienabled(void) {
  return irq_enabled;
}

void iset(bool enable) {
  irq_enabled = enable;
}

// ---------- 新建内核上下文 ----------
// 在 kstack 顶端预留一个 Context，返回其指针。
// 当 __am_switch_to() 切换到它时，"恢复"这个 Context 就会跳转到 entry(arg)。
Context *kcontext(Area kstack, void (*entry)(void *), void *arg) {
  uintptr_t *sp = (uintptr_t *)(void *)kstack.end - 1;
  Context *ctx = (Context *)(void *)sp - 1;
  memset(ctx, 0, sizeof(*ctx));
  ctx->gpr[2]  = (uintptr_t)ctx;   // sp 指向该 Context 自身
  ctx->gpr[10] = (uintptr_t)arg;   // a0 = arg
  ctx->mepc = (uintptr_t)entry;    // 首次被切换时执行 entry
  ctx->np   = (uintptr_t)entry;
  return ctx;
}

// VME 相关；libam 未实现 VME，直接 panic
Context *ucontext(AddrSpace *as, Area kstack, void *entry) {
  (void)as; (void)kstack; (void)entry;
  panic("libam: ucontext requires VME, which is not implemented");
  return NULL;
}

// =====================================================================
// native 实现：信号捕获真实 trap + ucontext 保存/恢复 + setitimer 定时
// =====================================================================
#ifdef __ISA_NATIVE__

#include <signal.h>
#include <ucontext.h>
#include <sys/ucontext.h>
#include <sys/time.h>
#include <unistd.h>

#if defined(__x86_64__)
// x86_64 Linux 上 ucontext 的 gregs 下标（glibc <sys/ucontext.h> 未直接暴露 REG_* 时）
enum {
  _REG_RDI = 8, _REG_RSI = 9, _REG_RDX = 12, _REG_RAX = 13,
  _REG_RCX = 14, _REG_RIP = 16,
};
// guest(_syscall_ 按 ARGS_ARRAY 用 rdi/rsi/rdx/rcx/rax) 的寄存器映射：
//   GPR1(a7) <- rdi, GPR2(a0) <- rsi, GPR3(a1) <- rdx, GPR4(a2) <- rcx,
//   GPRx(a0) -> rax
static void ctx_from_uc(Context *c, ucontext_t *uc) {
  gregset_t *g = &uc->uc_mcontext.gregs;
  memset(c, 0, sizeof(*c));
  c->gpr[17] = (*g)[_REG_RDI];
  c->gpr[10] = (*g)[_REG_RSI];
  c->gpr[11] = (*g)[_REG_RDX];
  c->gpr[12] = (*g)[_REG_RCX];
  c->mepc = (*g)[_REG_RIP];
  c->np   = (*g)[_REG_RIP];
}

static void ctx_to_uc(Context *c, ucontext_t *uc) {
  gregset_t *g = &uc->uc_mcontext.gregs;
  (*g)[_REG_RAX] = c->gpr[10];            // 系统调用返回值
  (*g)[_REG_RIP] = c->np ? c->np : c->mepc;
}
#else
#error "libam CTE native 寄存器映射未实现"
#endif

static void trap_signal_handler(int sig, siginfo_t *info, void *uc_void) {
  (void)info;
  ucontext_t *uc = (ucontext_t *)uc_void;
  Context ctx;
  Event ev = { .cause = sig, .ref = 0 };

  ctx_from_uc(&ctx, uc);
  if (sig == SIGALRM) {
    ev.event = irq_enabled ? EVENT_IRQ_TIMER : EVENT_NULL;
  } else {
    // 捕获到的 trap 指令（如 guest 的 ecall 在 x86 宿主上是非法指令）
    ev.event = EVENT_SYSCALL;
  }

  Context *next = &ctx;
  if (ev.event != EVENT_NULL && cte_handler != NULL) {
    next = cte_handler(ev, &ctx);
    if (next == NULL) next = &ctx;
  }
  ctx_to_uc(next, uc);
}

static void __am_switch_to(Context *next) {
  // 扩展点：需为每个 guest 进程维护一个 ucontext_t（栈、入口），
  // 用 swapcontext 在此处完成进程切换。当前为占位实现。
  (void)next;
}

bool cte_init(Context *(*handler)(Event ev, Context *ctx)) {
  cte_handler = handler;

  struct sigaction sa;
  memset(&sa, 0, sizeof(sa));
  sa.sa_sigaction = trap_signal_handler;
  sa.sa_flags = SA_SIGINFO;
  sigemptyset(&sa.sa_mask);
  sigaction(SIGILL, &sa, NULL);   // guest 自陷指令
  sigaction(SIGSYS, &sa, NULL);
  sigaction(SIGALRM, &sa, NULL);  // 定时器

  struct itimerval it;
  memset(&it, 0, sizeof(it));
  it.it_interval.tv_usec = 10000; // 10ms 定时
  it.it_value = it.it_interval;
  setitimer(ITIMER_REAL, &it, NULL);
  return true;
}

// =====================================================================
// 其它 ISA（Nanos-lite/NEMU 宿主，无信号机制）：软件自陷
// =====================================================================
#else

static void __am_switch_to(Context *next) {
  // 软件自陷模式下，guest 通过函数调用进入 handler；
  // 若 handler 返回了不同 Context，说明发生了"调度"，此处可挂接
  // setjmp/longjmp 或手工寄存器切换。当前实现仅接受"不切换"的约定。
  (void)next;
}

bool cte_init(Context *(*handler)(Event ev, Context *ctx)) {
  cte_handler = handler;
  return true;
}

#endif