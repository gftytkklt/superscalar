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

// The image stays open between validation and loading. The fixed ramdisk is
// unchanged during this single-core, non-yielding operation.
typedef struct {
  int fd;
  size_t size;
} ElfImage;

#ifdef HAS_VME
// Internal NEMU VME helpers; no change to the AM map() interface.
extern Area __am_user_area(void);
extern void *__am_lookup_page(AddrSpace *as, uintptr_t va);
#endif

static bool image_read(ElfImage *image, size_t offset, void *buf, size_t len) {
  if (offset > image->size || len > image->size - offset) return false;
#ifdef TEST_DUMMY
  size_t disk_read(void *buf, size_t offset, size_t len);
  return disk_read(buf, offset, len) == len;
#else
  return fs_lseek(image->fd, offset, SEEK_SET) == (long)offset &&
         fs_read(image->fd, buf, len) == (long)len;
#endif
}

static void image_close(ElfImage *image) {
#ifndef TEST_DUMMY
  fs_close(image->fd);
#endif
}

static bool read_phdr(ElfImage *image, const Elf_Ehdr *ehdr,
                      size_t i, Elf_Phdr *phdr) {
  return image_read(image, ehdr->e_phoff + i * sizeof(*phdr), phdr, sizeof(*phdr));
}

static bool validate_elf(ElfImage *image, Elf_Ehdr *ehdr) {
  if (!image_read(image, 0, ehdr, sizeof(*ehdr))) return false;
#ifdef __LP64__
  const int elf_class = ELFCLASS64;
#else
  const int elf_class = ELFCLASS32;
#endif
#if defined(__riscv)
  const int machine = EM_RISCV;
#elif defined(__x86_64__)
  const int machine = EM_X86_64;
#elif defined(__i386__)
  const int machine = EM_386;
#elif defined(__mips__)
  const int machine = EM_MIPS;
#else
  const int machine = EM_NONE;
  return false;
#endif
  if (memcmp(ehdr->e_ident, "\177ELF", 4) != 0 ||
      ehdr->e_ident[EI_CLASS] != elf_class ||
      ehdr->e_ident[EI_DATA] != ELFDATA2LSB ||
      ehdr->e_ident[EI_VERSION] != EV_CURRENT || ehdr->e_version != EV_CURRENT ||
      ehdr->e_machine != machine || ehdr->e_type != ET_EXEC ||
      ehdr->e_ehsize != sizeof(*ehdr) || ehdr->e_phentsize != sizeof(Elf_Phdr) ||
      ehdr->e_phnum == 0 || ehdr->e_phnum == PN_XNUM ||
      ehdr->e_phoff > image->size ||
      ehdr->e_phnum > (image->size - ehdr->e_phoff) / sizeof(Elf_Phdr)) return false;

#ifdef HAS_VME
  Area user = __am_user_area();
  uintptr_t lower = (uintptr_t)user.start;
  uintptr_t upper = (uintptr_t)user.end;
  if (upper < STACK_SIZE || lower >= upper - STACK_SIZE) return false;
  upper -= STACK_SIZE;
#endif
  // Current RISC-V targets use IALIGN=32 (no compressed instructions).
  if (machine == EM_RISCV && (ehdr->e_entry & 3)) return false;
  bool entry_ok = false;
  for (size_t i = 0; i < ehdr->e_phnum; i++) {
    Elf_Phdr phdr;
    if (!read_phdr(image, ehdr, i, &phdr)) return false;
    // This loader supports static executables, without an interpreter/relocator.
    if (phdr.p_type == PT_INTERP || phdr.p_type == PT_DYNAMIC) return false;
    if (phdr.p_type != PT_LOAD) continue;
    uintptr_t va = phdr.p_vaddr;
    if (phdr.p_filesz > phdr.p_memsz || phdr.p_offset > image->size ||
        phdr.p_filesz > image->size - phdr.p_offset ||
        phdr.p_memsz > UINTPTR_MAX - va ||
        ((va ^ phdr.p_offset) & (PGSIZE - 1)) != 0 ||
        (phdr.p_align > 1 && ((phdr.p_align & (phdr.p_align - 1)) != 0 ||
         ((va ^ phdr.p_offset) & (phdr.p_align - 1)) != 0))) return false;
    uintptr_t end = va + phdr.p_memsz;
    if (phdr.p_memsz && end > UINTPTR_MAX - (PGSIZE - 1)) return false;
#ifdef HAS_VME
    if (phdr.p_memsz && (va < lower || va >= upper || end > upper)) return false;
#endif
    // The entry must point to a file-backed instruction in an executable load.
    if ((phdr.p_flags & PF_X) && ehdr->e_entry >= va &&
        ehdr->e_entry - va < phdr.p_filesz) entry_ok = true;
    // Read all declared bytes before replacing the old PCB/address space.
    char scratch[256];
    for (size_t done = 0; done < phdr.p_filesz;) {
      size_t n = phdr.p_filesz - done;
      if (n > sizeof(scratch)) n = sizeof(scratch);
      if (!image_read(image, phdr.p_offset + done, scratch, n)) return false;
      done += n;
    }
  }
  return entry_ok;
}

static int image_open(ElfImage *image, Elf_Ehdr *ehdr, const char *filename) {
#ifdef TEST_DUMMY
  size_t disk_size(void);
  image->fd = -1;
  image->size = disk_size();
#else
  image->fd = fs_open(filename, 0, 0);
  if (image->fd < 0) return -ENOENT;
  long size = fs_filesz(image->fd);
  if (size < 0) { image_close(image); return -ENOEXEC; }
  image->size = size;
#endif
  if (validate_elf(image, ehdr)) return 0;
  image_close(image);
  return -ENOEXEC;
}

static uintptr_t load_elf(PCB *pcb, ElfImage *image, const Elf_Ehdr *ehdr) {
  for (size_t i = 0; i < ehdr->e_phnum; i++) {
    Elf_Phdr phdr;
    panic_on(!read_phdr(image, ehdr, i, &phdr), "ELF changed after validation");
    if (phdr.p_type != PT_LOAD || phdr.p_memsz == 0) continue;
    uintptr_t vaddr = phdr.p_vaddr, end = vaddr + phdr.p_memsz;
    uintptr_t file_end = vaddr + phdr.p_filesz;
#ifdef HAS_VME
    for (uintptr_t va = ROUNDDOWN(vaddr, PGSIZE); va < ROUNDUP(end, PGSIZE); va += PGSIZE) {
      void *pa = __am_lookup_page(&pcb->as, va);
      if (pa == NULL) {
        pa = new_page(1);
        panic_on(pa == NULL, "Out of physical pages loading ELF");
        memset(pa, 0, PGSIZE);
        map(&pcb->as, (void *)va, pa, MMAP_READ | MMAP_WRITE);
      }
      uintptr_t f0 = (va > vaddr ? va : vaddr);
      uintptr_t f1 = (va + PGSIZE < file_end ? va + PGSIZE : file_end);
      if (f1 > f0) {
        panic_on(!image_read(image, phdr.p_offset + (f0 - vaddr),
                            (char *)pa + (f0 - va), f1 - f0), "ELF changed after validation");
      }
      uintptr_t z0 = (file_end > va ? file_end : va);
      uintptr_t z1 = (end < va + PGSIZE ? end : va + PGSIZE);
      if (z1 > z0) memset((char *)pa + (z0 - va), 0, z1 - z0);
    }
    uintptr_t brk = ROUNDUP(end, PGSIZE);
    if (brk > pcb->max_brk) pcb->max_brk = brk;
    if (end > pcb->brk_start) pcb->brk_start = end;
#else
    panic_on(!image_read(image, phdr.p_offset, (void *)vaddr, phdr.p_filesz),
             "ELF changed after validation");
    memset((void *)file_end, 0, end - file_end);
#endif
  }
  image_close(image);
  return ehdr->e_entry;
}

void naive_uload(PCB *pcb, const char *filename) {
  Log("Open %s", filename);
  ElfImage image;
  Elf_Ehdr ehdr;
  int status = image_open(&image, &ehdr, filename);
  panic_on(status < 0, "Invalid executable");
  uintptr_t entry = load_elf(pcb, &image, &ehdr);
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
  ElfImage image;
  Elf_Ehdr ehdr;
  int status = image_open(&image, &ehdr, filename);
  if (status < 0) return status;
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
  uintptr_t entry = load_elf(pcb, &image, &ehdr);
  Log("Jump to entry = %p", entry);

  Context *cp = ucontext(&pcb->as, kstack, (void *)entry);
  pcb->cp = cp;

  // GPRx points to argc; Navy _start sets sp from GPRx and passes it to call_main
  cp->GPRx = initial_sp;

#undef USTACK_TO_PA
  return 0;
}

