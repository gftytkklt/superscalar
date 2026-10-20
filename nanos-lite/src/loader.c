#include <proc.h>
#include <elf.h>
#include <fs.h>
#include <errno.h>

#ifdef __LP64__
# define Elf_Ehdr Elf64_Ehdr
# define Elf_Phdr Elf64_Phdr
#else
# define Elf_Ehdr Elf32_Ehdr
# define Elf_Phdr Elf32_Phdr
#endif

static uintptr_t loader(PCB *pcb, const char *filename) {
  #ifdef TEST_DUMMY
  Elf_Ehdr ehdr = {};
  Elf_Phdr phdr = {};
  // naive version: the disk image's first file is dummy
  size_t disk_read(void *buf, size_t offset, size_t len);
  disk_read(&ehdr, 0, sizeof(ehdr));
  assert(*(uint32_t*)&ehdr.e_ident == 0x464c457f);
  uint64_t phoff = ehdr.e_phoff;
  uint16_t phentsize = ehdr.e_phentsize;
  for (uint16_t i=0;i< ehdr.e_phnum; i++){
    disk_read(&phdr, phoff, phentsize);
    if (phdr.p_type == PT_LOAD){
      size_t filesz = phdr.p_filesz;
      size_t vaddr = phdr.p_vaddr;
      size_t offset = phdr.p_offset;
      size_t memsz = phdr.p_memsz;
      disk_read((void*)vaddr, offset, filesz);
      memset((void*)vaddr + filesz, 0, memsz-filesz);
    }
    phoff += phentsize;
  }
  return ehdr.e_entry;
  #elif defined(TEST_FILE) || defined(TEST_NTERM) || defined(MULTIPROGRAM) || defined(TIME_SHARING) || defined(FG_PROCESS)
  Elf_Ehdr ehdr = {};
  Elf_Phdr phdr = {};
  int fd = fs_open(filename, 0, 0);
  if(fd<0){return -1;}
  fs_read(fd, &ehdr, 64);
  assert(*(uint32_t*)&ehdr.e_ident == 0x464c457f);
  uint64_t phoff = ehdr.e_phoff;
  uint16_t phentsize = ehdr.e_phentsize;
  for (uint16_t i=0;i< ehdr.e_phnum; i++){
    fs_lseek(fd, phoff, SEEK_SET);
    fs_read(fd, &phdr, phentsize);
    if (phdr.p_type == PT_LOAD){
      size_t filesz = phdr.p_filesz;
      size_t vaddr = phdr.p_vaddr;
      size_t offset = phdr.p_offset;
      size_t memsz = phdr.p_memsz;
      #ifdef HAS_VME
      // load the segment page by page: allocate a physical page, map it to the
      // segment's virtual page, then copy the file content into the physical page
      uintptr_t page_start = ROUNDDOWN(vaddr, PGSIZE);
      for (uintptr_t va = page_start;
           va < ROUNDUP(vaddr + memsz, PGSIZE); va += PGSIZE) {
        void *pa = new_page(1);
        panic_on(pa == NULL, "Out of physical pages loading ELF");
        map(&pcb->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);

        // copy the file part of this page (if any). Note the segment may start
        // mid-page, so the file offset must be computed from the virtual address.
        if (va < vaddr + filesz) {
          uintptr_t fstart = (va > vaddr) ? va : vaddr;   // first vaddr in page that has file data
          size_t n = (vaddr + filesz - fstart < PGSIZE - (fstart - va)) ?
                     (vaddr + filesz - fstart) : (PGSIZE - (fstart - va));
          if (n > 0) {
            fs_lseek(fd, offset + (fstart - vaddr), SEEK_SET);
            fs_read(fd, (char *)pa + (fstart - va), n);
          }
        }

        // zero the bss part of this page (if any)
        uintptr_t z0 = (vaddr + filesz > va) ? (vaddr + filesz) : va;
        uintptr_t z1 = (vaddr + memsz < va + PGSIZE) ? (vaddr + memsz) : (va + PGSIZE);
        if (z1 > z0) memset((char *)pa + (z0 - va), 0, z1 - z0);
      }
      // record the peak program break (page-aligned) for mm_brk()
      uintptr_t brk = ROUNDUP(vaddr + memsz, PGSIZE);
      if (brk > pcb->max_brk) pcb->max_brk = brk;
      if (vaddr + memsz > pcb->brk_start) pcb->brk_start = vaddr + memsz;
      #else
      fs_lseek(fd, offset, SEEK_SET);
      fs_read(fd, (void *)vaddr, filesz);
      memset((void *)(vaddr + filesz), 0, (memsz-filesz));
      #endif
    }
    phoff += phentsize;
  }
  return ehdr.e_entry;
  #else
  panic("No test macro defined for loader");
  #endif
}

void naive_uload(PCB *pcb, const char *filename) {
  Log("Open %s", filename);
  uintptr_t entry = loader(pcb, filename);
  Log("Jump to entry = %p", entry);
  ((void(*)())entry) ();
}

// Charge every pointer and terminating string byte before changing the process.
static int count_args(char *const vec[], size_t *count, size_t *used) {
  *count = 0;
  while (vec != NULL && vec[*count] != NULL) {
    if (*used > STACK_SIZE - sizeof(uintptr_t)) return -E2BIG;
    size_t available = STACK_SIZE - *used - sizeof(uintptr_t);
    size_t len = 0;
    while (len < available && vec[*count][len] != '\0') len++;
    if (len == available) return -E2BIG;
    *used += sizeof(uintptr_t) + len + 1;
    (*count)++;
  }
  return 0;
}

int context_uload(PCB *pcb, const char *filename, char *const argv[], char *const envp[]) {
  size_t argc, envc;
  size_t used = 3 * sizeof(uintptr_t);  // argc and the two NULL pointers
  if (count_args(argv, &argc, &used) < 0 ||
      count_args(envp, &envc, &used) < 0) return -E2BIG;
  // The page-aligned stack top and STACK_SIZE are multiples of 16.
  // Rounding a validated used <= STACK_SIZE up to 16 still fits the stack.
  // Reject a missing executable before replacing the caller's address space
  // or context. fs_open() uses a fixed file table; the loader opens it again.
  int fd = fs_open(filename, 0, 0);
  if (fd < 0) return -ENOENT;
  fs_close(fd);
#ifdef HAS_VME
  protect(&pcb->as);
#endif
  // Reset the program break: the loader re-derives it from the new ELF's
  // segments. A stale value from the previous program would make mm_brk()
  // skip mapping (brk <= max_brk) and the new program would run on unmapped
  // heap pages (exec-after-exit reload path).
  pcb->max_brk = 0;
  pcb->brk_start = 0;
  Area kstack = {pcb->stack, pcb->stack + STACK_SIZE};

  // user stack: allocate a fresh 32KB region FIRST. Do not read argv/envp
  // after loader() runs: the new program may be loaded to the same address as
  // the calling process's static strings, overwriting them.
#ifdef HAS_VME
  // user stack lives at the end of the user virtual address space; the OS
  // writes the arguments into the *physical* pages (reachable through the
  // kernel identical mapping), which are mapped to the user stack region.
  uintptr_t ustack = (uintptr_t)pcb->as.area.end;   // 0x80000000
  uintptr_t ustack_lo = ustack - STACK_SIZE;
  void *ustack_pa = new_page(STACK_SIZE / PGSIZE);
  panic_on(ustack_pa == NULL, "Out of physical pages for user stack");
  for (uintptr_t va = ustack_lo; va < ustack; va += PGSIZE) {
    map(&pcb->as, (void *)va, (void *)((uintptr_t)ustack_pa + (va - ustack_lo)),
        MMAP_READ | MMAP_WRITE);
  }
# define USTACK_TO_PA(v) ((void *)((uintptr_t)ustack_pa + ((uintptr_t)(v) - ustack_lo)))
#else
  void *ustack_pa = new_page(STACK_SIZE / PGSIZE);
  panic_on(ustack_pa == NULL, "Out of physical pages for user stack");
  uintptr_t ustack = (uintptr_t)ustack_pa + STACK_SIZE;
# define USTACK_TO_PA(v) ((void *)(v))
#endif

  // layout on user stack (grows downward from ustack), low -> high:
  //   argc, argv[], envp[], string area
  uintptr_t initial_sp = ROUNDDOWN(ustack - used, 16);
  uintptr_t *table = USTACK_TO_PA(initial_sp);
  uintptr_t *argv_addr = table + 1;
  uintptr_t *envp_addr = argv_addr + argc + 1;
  table[0] = argc;
  uintptr_t sp = ustack;

  // Copy into the new user stack and fill its pointer tables directly.
  // All source strings were bounded above and remain live until loader().
  for (size_t i = 0; i < argc; i ++) {
    size_t len = strlen(argv[i]) + 1;
    sp -= len;
    memcpy(USTACK_TO_PA(sp), argv[i], len);
    argv_addr[i] = sp;
  }
  argv_addr[argc] = 0;

  for (size_t e = 0; e < envc; e ++) {
    size_t len = strlen(envp[e]) + 1;
    sp -= len;
    memcpy(USTACK_TO_PA(sp), envp[e], len);
    envp_addr[e] = sp;
  }
  envp_addr[envc] = 0;

  // load the new program (may overwrite the calling process's static data)
  uintptr_t entry = loader(pcb, filename);
  assert(entry != (uintptr_t)-1); // preflight found this file in the fixed table
  Log("Jump to entry = %p", entry);

  Context *cp = ucontext(&pcb->as, kstack, (void *)entry);
  pcb->cp = cp;

  // GPRx points to argc; Navy _start sets sp from GPRx and passes it to call_main
  cp->GPRx = initial_sp;

#undef USTACK_TO_PA
  return 0;
}

