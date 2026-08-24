#include <proc.h>
#include <elf.h>
#include <fs.h>

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
  // naive version: ramdisk only consists of dummy
  size_t ramdisk_read(void *buf, size_t offset, size_t len);
  ramdisk_read(&ehdr, 0, sizeof(ehdr));
  assert(*(uint32_t*)&ehdr.e_ident == 0x464c457f);
  uint64_t phoff = ehdr.e_phoff;
  uint16_t phentsize = ehdr.e_phentsize;
  for (uint16_t i=0;i< ehdr.e_phnum; i++){
    ramdisk_read(&phdr, phoff, phentsize);
    if (phdr.p_type == PT_LOAD){
      size_t filesz = phdr.p_filesz;
      size_t vaddr = phdr.p_vaddr;
      size_t offset = phdr.p_offset;
      size_t memsz = phdr.p_memsz;
      ramdisk_read((void*)vaddr, offset, filesz);
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

void context_uload(PCB *pcb, const char *filename, char *const argv[], char *const envp[]) {
#ifdef HAS_VME
  protect(&pcb->as);
#endif
  Area kstack = {pcb->stack, pcb->stack + STACK_SIZE};

  // user stack: allocate a fresh 32KB region FIRST. Do not read argv/envp
  // after loader() runs: the new program may be loaded to the same address as
  // the calling process's static strings, overwriting them.
#ifdef HAS_VME
  // user stack lives at the end of the user virtual address space; the OS
  // writes the arguments into the *physical* pages (reachable through the
  // kernel identical mapping), which are mapped to the user stack region.
  uintptr_t ustack = (uintptr_t)pcb->as.area.end;   // 0x80000000
  uintptr_t ustack_lo = ustack - 8 * PGSIZE;        // 32KB
  void *ustack_pa = new_page(8);
  for (uintptr_t va = ustack_lo; va < ustack; va += PGSIZE) {
    map(&pcb->as, (void *)va, (void *)((uintptr_t)ustack_pa + (va - ustack_lo)),
        MMAP_READ | MMAP_WRITE);
  }
# define USTACK_TO_PA(v) ((void *)((uintptr_t)ustack_pa + ((uintptr_t)(v) - ustack_lo)))
#else
  uintptr_t ustack = (uintptr_t)new_page(8) + 8 * PGSIZE;
# define USTACK_TO_PA(v) ((void *)(v))
#endif

  // count argc/envc (read argv/envp BEFORE loader)
  int argc = 0;
  while (argv[argc] != NULL) argc ++;
  int envc = 0;
  while (envp[envc] != NULL) envc ++;

  // layout on user stack (grows downward from ustack), low -> high:
  //   argc, argv[], envp[], string area
  uintptr_t sp = ustack;

  // 1. string area: push argv strings then envp strings, RECORDING each
  //    string's address as it is placed (stack grows down, so later pushes
  //    land at lower addresses).
  uintptr_t argv_addr[argc + 1];
  for (int i = 0; i < argc; i ++) {
    int len = strlen(argv[i]) + 1;
    sp -= len;
    memcpy(USTACK_TO_PA(sp), argv[i], len);
    argv_addr[i] = sp;
  }
  argv_addr[argc] = 0;

  uintptr_t envp_addr[envc + 1];
  for (int e = 0; e < envc; e ++) {
    int len = strlen(envp[e]) + 1;
    sp -= len;
    memcpy(USTACK_TO_PA(sp), envp[e], len);
    envp_addr[e] = sp;
  }
  envp_addr[envc] = 0;

  // 2. envp[] pointer array (with NULL)
  sp -= (envc + 1) * sizeof(uintptr_t);
  memcpy(USTACK_TO_PA(sp), envp_addr, (envc + 1) * sizeof(uintptr_t));

  // 3. argv[] pointer array (with NULL)
  sp -= (argc + 1) * sizeof(uintptr_t);
  memcpy(USTACK_TO_PA(sp), argv_addr, (argc + 1) * sizeof(uintptr_t));

  // 4. argc
  sp -= sizeof(uintptr_t);
  *(uintptr_t *)USTACK_TO_PA(sp) = (uintptr_t)argc;

  // load the new program (may overwrite the calling process's static data)
  uintptr_t entry = loader(pcb, filename);
  Log("Jump to entry = %p", entry);

  Context *cp = ucontext(&pcb->as, kstack, (void *)entry);
  pcb->cp = cp;

  // GPRx points to argc; Navy _start sets sp from GPRx and passes it to call_main
  cp->GPRx = sp;

#undef USTACK_TO_PA
}

