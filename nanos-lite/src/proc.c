#include <proc.h>

#define MAX_NR_PROC 4

static PCB pcb[MAX_NR_PROC] __attribute__((used)) = {};
static PCB pcb_boot = {};
PCB *current = NULL;

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
  #elif defined(TEST_KLOAD)
  context_kload(&pcb[0], hello_fun, (void *)0xdeadbeef);
  context_kload(&pcb[1], hello_fun, (void *)0xabcdef01);
  switch_boot_pcb();
  #elif defined(MULTIPROGRAM) || defined(TIME_SHARING)
  context_kload(&pcb[0], hello_fun, (void *)0xdeadbeef);
  {
    char *const argv[] = {"/bin/pal", "--skip", NULL};
    char *const envp[] = {NULL};
    context_uload(&pcb[1], "/bin/pal", argv, envp);
  }
  switch_boot_pcb();
  #endif

  Log("Initializing processes...");

}

void context_kload(PCB *pcb, void (*entry)(void *), void *arg) {
  pcb->cp = kcontext((Area){(void *)pcb->stack, (void *)(pcb->stack + STACK_SIZE)}, entry, arg);
}

Context* schedule(Context *prev) {
  current->cp = prev;
  current = (current == &pcb[0] ? &pcb[1] : &pcb[0]);
  return current->cp;
}
