#include <proc.h>

#define MAX_NR_PROC 4

static PCB pcb[MAX_NR_PROC] __attribute__((used)) = {};
static PCB pcb_boot = {};
PCB *current = NULL;
PCB *fg_pcb = NULL; // the foreground process (owns the screen)

void switch_boot_pcb() {
  current = &pcb_boot;
}

void hello_fun(void *arg) {
  int j = 1;
  while (1) {
    Log("Hello World from Nanos-lite with arg '%p' for the %dth time!", (uintptr_t)arg, j);
    j ++;
    yield();
  }
}

void init_proc() {
  #ifdef TEST_DUMMY
  naive_uload(NULL, NULL);
  #elif defined(TEST_FILE)
  naive_uload(NULL, "/bin/nterm");
  #elif defined(TEST_NTERM)
  {
    char *const argv[] = {"/bin/nterm", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[0], "/bin/nterm", argv, envp);
  }
  switch_boot_pcb();
  #elif defined(TEST_KLOAD)
  context_kload(&pcb[0], hello_fun, (void *)0xdeadbeef);
  context_kload(&pcb[1], hello_fun, (void *)0xabcdef01);
  switch_boot_pcb();
  #elif defined(MULTIPROGRAM)
  context_kload(&pcb[0], hello_fun, (void *)0xdeadbeef);
  {
    char *const argv[] = {"/bin/pal", "--skip", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[1], "/bin/pal", argv, envp);
  }
  switch_boot_pcb();
  #elif defined(TIME_SHARING)
  {
    char *const argv[] = {"/bin/nterm", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[0], "/bin/nterm", argv, envp);
  }
  {
    char *const argv[] = {"/bin/hello", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[1], "/bin/hello", argv, envp);
  }
  switch_boot_pcb();
  #elif defined(FG_PROCESS)
  // PA4.5: load 3 foreground apps (pal / bird / nslider) + a background hello.
  // Only the foreground and hello are scheduled; F1/F2/F3 switch the foreground.
  {
    char *const argv[] = {"/bin/pal", "--skip", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[0], "/bin/pal", argv, envp);
  }
  {
    char *const argv[] = {"/bin/nterm", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[1], "/bin/nterm", argv, envp);
  }
  {
    char *const argv[] = {"/bin/nslider", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[2], "/bin/nslider", argv, envp);
  }
  {
    char *const argv[] = {"/bin/hello", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[3], "/bin/hello", argv, envp);
  }
  fg_pcb = &pcb[0]; // start with pal as the foreground
  switch_boot_pcb();
  #endif

  Log("Initializing processes...");

}

void context_kload(PCB *pcb, void (*entry)(void *), void *arg) {
  pcb->cp = kcontext((Area){(void *)pcb->stack, (void *)(pcb->stack + STACK_SIZE)}, entry, arg);
}

Context* schedule(Context *prev) {
  current->cp = prev;
  // PA4.5: alternate between the foreground process (fg_pcb, the screen owner)
  // and the background hello process (pcb[3]). Switching fg_pcb via F1/F2/F3
  // is handled automatically: if `current` is no longer the foreground, the
  // next schedule() jumps to the new foreground.
  current = (current == fg_pcb ? &pcb[3] : fg_pcb);
  // single-process case (e.g. TEST_NTERM): if the target PCB has no context,
  // stay on the current one instead of switching into a dead PCB.
  return (current->cp ? current->cp : prev);
}

void set_fg_pcb(int idx) {
  fg_pcb = &pcb[idx];
}
