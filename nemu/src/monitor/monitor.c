/***************************************************************************************
* Copyright (c) 2014-2022 Zihao Yu, Nanjing University
*
* NEMU is licensed under Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*          http://license.coscl.org.cn/MulanPSL2
*
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
* EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
* MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
*
* See the Mulan PSL v2 for more details.
***************************************************************************************/

#include <isa.h>
#include <device/timer.h>
#include <device/serial.h>
#include <memory/paddr.h>

void init_rand();
void init_log(const char *log_file);
void init_mem();
void init_difftest(char *ref_so_file, long img_size, int port);
void init_device();
void init_sdb();
void init_disasm(const char *triple);
static void welcome() {
  Log("Trace: %s", MUXDEF(CONFIG_TRACE, ANSI_FMT("ON", ANSI_FG_GREEN), ANSI_FMT("OFF", ANSI_FG_RED)));
  IFDEF(CONFIG_TRACE, Log("If trace is enabled, a log file will be generated "
        "to record the trace. This may lead to a large log file. "
        "If it is not necessary, you can disable it in menuconfig"));
  Log("FTrace : %s", MUXDEF(CONFIG_FTRACE, ANSI_FMT("ON", ANSI_FG_GREEN), ANSI_FMT("OFF", ANSI_FG_RED)));
  Log("Build time: %s, %s", __TIME__, __DATE__);
  printf("Welcome to %s-NEMU!\n", ANSI_FMT(str(__GUEST_ISA__), ANSI_FG_YELLOW ANSI_BG_RED));
  printf("For help, type \"help\"\n");
  //Log("Exercise: Please remove me in the source code and compile NEMU again.");
  //assert(0);
}

#ifndef CONFIG_TARGET_AM
#include <getopt.h>

void sdb_set_batch_mode();

static char *log_file = NULL;
static char *diff_so_file = NULL;
static char *img_file = NULL;
static const char *kernel_file, *dtb_file;
static int difftest_port = 1234;
static int elf_num = 0;
static char **elf_file = NULL;

static long load_at(const char *file, paddr_t addr, uint64_t limit) {
  FILE *fp = fopen(file, "rb");
  if (!fp) { perror(file); exit(1); }
  if (fseek(fp, 0, SEEK_END)) { perror(file); exit(1); }
  long size = ftell(fp);
  if (size <= 0 || (uint64_t)size > limit || addr < CONFIG_MBASE ||
      (uint64_t)addr - CONFIG_MBASE + (uint64_t)size > CONFIG_MSIZE) {
    fprintf(stderr, "Image out of range or overlaps next image: %s\n", file); exit(1);
  }
  rewind(fp);
  if (fread(guest_to_host(addr), 1, size, fp) != (size_t)size) { perror(file); exit(1); }
  fclose(fp);
  Log("Loaded %s: %ld bytes at " FMT_PADDR, file, size, addr);
  return size;
}
static long load_img() {
  if (!!kernel_file != !!dtb_file || (kernel_file && !img_file)) {
    fprintf(stderr, "--kernel and --dtb require each other and a firmware IMAGE\n"); exit(1);
  }
  if (!img_file) {
    Log("No image is given. Use the default build-in image.");
    return 4096;
  }
  if (kernel_file) {
#if defined(CONFIG_RV64) && defined(CONFIG_DEVICE)
    if (CONFIG_MBASE != 0x80000000 || RESET_VECTOR != 0x80000000 || CONFIG_MSIZE <= 0x2200000) {
      fprintf(stderr, "Linux loader requires PMEM/reset at 0x80000000 and RAM beyond DTB\n"); exit(1);
    }
    long size = load_at(img_file, RESET_VECTOR, 0x200000);
    load_at(kernel_file, 0x80200000, 0x2000000);
    load_at(dtb_file, 0x82200000, CONFIG_MSIZE - 0x2200000);
    cpu.gpr[10] = 0;
    cpu.gpr[11] = 0x82200000;
    return size;
#else
    fprintf(stderr, "Multi-image boot requires native RV64 devices\n"); exit(1);
#endif
  }
  return load_at(img_file, RESET_VECTOR,
      CONFIG_MSIZE - ((uint64_t)RESET_VECTOR - CONFIG_MBASE));
}

static int parse_args(int argc, char *argv[]) {
  const struct option table[] = {
    {"batch"    , no_argument      , NULL, 'b'},
    {"log"      , required_argument, NULL, 'l'},
    {"diff"     , required_argument, NULL, 'd'},
    {"port"     , required_argument, NULL, 'p'},
    {"help"     , no_argument      , NULL, 'h'},
    {"timer-source", required_argument, NULL, 256},
    {"serial-input", required_argument, NULL, 257},
    {"kernel", required_argument, NULL, 258},
    {"dtb", required_argument, NULL, 259},
    {0          , 0                , NULL,  0 },
  };
  int o;
  while ( (o = getopt_long(argc, argv, "-bhe:l:d:p:", table, NULL)) != -1) {
    switch (o) {
      case 'b': sdb_set_batch_mode(); break;
      case 256:
#if defined(CONFIG_RV64) && defined(CONFIG_DEVICE)
        nemu_timer_select(optarg); break;
#else
        fprintf(stderr, "--timer-source requires native RV64 devices\n"); exit(1);
#endif
      case 257:
#if defined(CONFIG_RV64) && defined(CONFIG_DEVICE) && defined(CONFIG_HAS_SERIAL)
        nemu_serial_input(optarg); break;
#else
        fprintf(stderr, "--serial-input requires native RV64 serial\n"); exit(1);
#endif
      case 258: kernel_file = optarg; break;
      case 259: dtb_file = optarg; break;
      case 'p': sscanf(optarg, "%d", &difftest_port); break;
      case 'l': log_file = optarg; break;
      case 'd': diff_so_file = optarg; break;
      case 'e': {
        char **tmp = (char **)realloc(elf_file, sizeof(char *) * (elf_num + 1));
        Assert(tmp, "realloc elf_file failed");
        elf_file = tmp;
        elf_file[elf_num] = optarg;
        elf_num++;
        break;
      }
      case 1: img_file = optarg; return 0;
      default:
        printf("Usage: %s [OPTION...] IMAGE [args]\n\n", argv[0]);
        printf("\t-b,--batch              run with batch mode\n");
        printf("\t-l,--log=FILE           output log to FILE\n");
        printf("\t-d,--diff=REF_SO        run DiffTest with reference REF_SO\n");
        printf("\t-p,--port=PORT          run DiffTest with port PORT\n");
        printf("\t-e,--elf=ELF_FILE_SRC	  run with elf file for ftrace\n");
        printf("\t--timer-source=legacy|mtimer  select timer input (default legacy)\n");
        printf("\t--serial-input=PATH      nonblocking file/FIFO RX\n");
        printf("\t--kernel=FILE --dtb=FILE multi-image RV64 boot\n");
        printf("\nOptions must precede IMAGE.\n");
        exit(0);
    }
  }
  return 0;
}

#ifdef CONFIG_FTRACE
#define BUF_SIZE 128
static int func_num = 32;
static int func_idx = 0;
typedef struct elf_func{
  char func_name[BUF_SIZE];
  unsigned long entry_addr;
  unsigned long func_size;
}func;
static func *func_pool = NULL;

#include <elf.h>
#include <limits.h>

static bool elf_range(uint64_t file_size, uint64_t offset, uint64_t size) {
  return offset <= file_size && size <= file_size - offset;
}

static bool elf_read(FILE *fp, uint64_t file_size, uint64_t offset, void *buf, size_t size) {
  return elf_range(file_size, offset, size) &&
    fseek(fp, (long)offset, SEEK_SET) == 0 &&
    fread(buf, 1, size, fp) == size && !ferror(fp);
}

static bool load_elf_funcs(const char *path) {
  FILE *fp = fopen(path, "rb");
  Elf64_Shdr *sections = NULL;
  char *strings = NULL;
  const char *error = "cannot open file";
  bool ok = false;
  if (fp == NULL) goto out;
  error = "cannot read file size";
  if (fseek(fp, 0, SEEK_END) != 0) goto out;
  long file_end = ftell(fp);
  if (file_end < 0) goto out;
  uint64_t file_size = file_end;
  Elf64_Ehdr header;
  error = "invalid or unsupported ELF64 header";
  if (!elf_read(fp, file_size, 0, &header, sizeof(header)) ||
      memcmp(header.e_ident, ELFMAG, SELFMAG) != 0 ||
      header.e_ident[EI_CLASS] != ELFCLASS64 ||
      header.e_ident[EI_DATA] != ELFDATA2LSB ||
      header.e_ident[EI_VERSION] != EV_CURRENT || header.e_version != EV_CURRENT ||
      header.e_ehsize != sizeof(header) || header.e_shentsize != sizeof(Elf64_Shdr) ||
      header.e_shnum == 0 || header.e_shnum >= SHN_LORESERVE ||
      header.e_shstrndx >= header.e_shnum) goto out;

  size_t section_bytes = (size_t)header.e_shnum * sizeof(*sections);
  error = "invalid section table";
  if (!elf_range(file_size, header.e_shoff, section_bytes)) goto out;
  sections = malloc(section_bytes);
  if (sections == NULL || !elf_read(fp, file_size, header.e_shoff, sections, section_bytes)) goto out;
  if (sections[0].sh_type != SHT_NULL ||
      (header.e_shstrndx != SHN_UNDEF && sections[header.e_shstrndx].sh_type != SHT_STRTAB)) goto out;
  int sym_index = -1;
  for (int i = 1; i < header.e_shnum; i++) {
    Elf64_Shdr *sh = &sections[i];
    if (sh->sh_type != SHT_NULL && sh->sh_type != SHT_NOBITS &&
        !elf_range(file_size, sh->sh_offset, sh->sh_size)) goto out;
    if (sh->sh_type == SHT_SYMTAB) sym_index = i;
  }
  error = "missing or invalid symbol table";
  if (sym_index < 0) goto out;
  Elf64_Shdr *symtab = &sections[sym_index];
  if (symtab->sh_entsize != sizeof(Elf64_Sym) ||
      symtab->sh_size % sizeof(Elf64_Sym) != 0 || symtab->sh_size == 0 ||
      symtab->sh_link >= header.e_shnum) goto out;
  Elf64_Shdr *strtab = &sections[symtab->sh_link];
  error = "invalid symbol string table";
  if (strtab->sh_type != SHT_STRTAB || strtab->sh_size == 0 ||
      (uint64_t)(size_t)strtab->sh_size != strtab->sh_size) goto out;
  strings = malloc((size_t)strtab->sh_size);
  if (strings == NULL || !elf_read(fp, file_size, strtab->sh_offset, strings, strtab->sh_size) ||
      strings[0] != '\0' || strings[strtab->sh_size - 1] != '\0') goto out;

  error = "invalid symbol or function range";
  uint64_t sym_count = symtab->sh_size / sizeof(Elf64_Sym);
  for (uint64_t i = 0; i < sym_count; i++) {
    Elf64_Sym sym;
    if (!elf_read(fp, file_size, symtab->sh_offset + i * sizeof(sym), &sym, sizeof(sym)) ||
        sym.st_name >= strtab->sh_size || sym.st_shndx == SHN_XINDEX ||
        (sym.st_shndx < SHN_LORESERVE && sym.st_shndx >= header.e_shnum)) goto out;
    char *name = strings + sym.st_name;
    char *end = memchr(name, '\0', strtab->sh_size - sym.st_name);
    if (end == NULL) goto out;
    // Preserve the existing GLOBAL/FUNC filter; undefined symbols have no entry.
    if (sym.st_info != ELF64_ST_INFO(STB_GLOBAL, STT_FUNC) || sym.st_shndx == SHN_UNDEF) continue;
    if (sym.st_value > ULONG_MAX || sym.st_size > ULONG_MAX - sym.st_value) goto out;
    if (func_idx == func_num) {
      error = "function table allocation failed";
      if (func_num > INT_MAX - 32 || (size_t)(func_num + 32) > SIZE_MAX / sizeof(func)) goto out;
      func *tmp = realloc(func_pool, (size_t)(func_num + 32) * sizeof(func));
      if (tmp == NULL) goto out;
      func_pool = tmp;
      func_num += 32;
      error = "invalid symbol or function range";
    }
    func record = {};
    size_t name_len = end - name;
    if (name_len >= sizeof(record.func_name)) name_len = sizeof(record.func_name) - 1;
    memcpy(record.func_name, name, name_len);
    record.entry_addr = sym.st_value;
    record.func_size = sym.st_size;
    func_pool[func_idx++] = record;
  }
  ok = true;
out:
  free(strings);
  free(sections);
  if (fp != NULL && fclose(fp) != 0) { ok = false; error = "file close failed"; }
  if (!ok) fprintf(stderr, "FTRACE: rejected ELF '%s': %s\n", path, error);
  return ok;
}

static void init_elf() {
  func_pool = malloc((size_t)func_num * sizeof(func));
  Assert(func_pool, "malloc func_pool failed");
  for (int i = 0; i < elf_num; i++) {
    Log("elf file %d: %s", i, elf_file[i]);
    if (!load_elf_funcs(elf_file[i])) {
      free(func_pool);
      func_pool = NULL;
      func_idx = 0;
      exit(EXIT_FAILURE);
    }
  }
}
static int func_depth = 0;
#define MAX_CALL_DEPTH 64
static int call_stack[MAX_CALL_DEPTH];   // 保存被调函数的 func_idx，用于真实调用栈匹配
static int call_top = 0;

// 返回 func_pool 中入口地址 == addr 的函数下标，找不到返回 -1
static int find_func_by_entry(unsigned long addr) {
  for (int i = 0; i < func_idx; i ++) {
    if (func_pool[i].entry_addr == addr) return i;
  }
  return -1;
}

// 返回 func_pool 中 addr 落在 [entry, entry+size) 的函数下标，找不到返回 -1
static int find_func_by_addr(unsigned long addr) {
  for (int i = 0; i < func_idx; i ++) {
    if (addr >= func_pool[i].entry_addr &&
        addr <  func_pool[i].entry_addr + func_pool[i].func_size) return i;
  }
  return -1;
}

void print_ftrace(unsigned long pc, unsigned long dnpc, unsigned inst) {
  // ebreak：单独处理（调试断点，不算函数调用）
  if (inst == 0x00100073) {
    printf("%lx:%*sebreak\n", pc, func_depth, " ");
    return;
  }

  unsigned opcode = BITS(inst, 6, 0);
  unsigned rd = BITS(inst, 11, 7);
  unsigned rs1 = BITS(inst, 19, 15);

  if (opcode == 0x6f) {           // jal
    if (rd != 0) {                // rd!=0 保存返回地址 => 函数调用
      int i = find_func_by_entry(dnpc);
      if (i >= 0) {
        printf("%lx:%*scall [%s@0x%lx]\n", pc, func_depth, " ",
               func_pool[i].func_name, func_pool[i].entry_addr);
        if (call_top < MAX_CALL_DEPTH) call_stack[call_top ++] = i;
        func_depth = call_top;
      }
    }
    // rd == 0 的 jal 是无返回跳转（goto），不算调用，不记录
  }
  else if (opcode == 0x67) {      // jalr
    if (rd == 0 && rs1 == 1) {    // ret: jalr x0, imm(x1)
      int i = find_func_by_addr(pc);
      if (i >= 0) {
        printf("%lx:%*sret [%s]\n", pc, func_depth, " ",
               func_pool[i].func_name);
      }
      if (call_top > 0) call_top --;
      func_depth = call_top;
    }
    else if (rd != 0) {           // 间接调用（如函数指针）
      int i = find_func_by_entry(dnpc);
      if (i >= 0) {
        printf("%lx:%*scall [%s@0x%lx]\n", pc, func_depth, " ",
               func_pool[i].func_name, func_pool[i].entry_addr);
        if (call_top < MAX_CALL_DEPTH) call_stack[call_top ++] = i;
        func_depth = call_top;
      }
    }
    // rd==0 且 rs1!=1 的 jalr：无返回跳转，不记录
  }
  // 其它指令（分支、普通指令）不参与 call/ret 判定
}
#endif

void init_monitor(int argc, char *argv[]) {
  /* Perform some global initialization. */

  /* Parse arguments. */
  parse_args(argc, argv);

  /* Set random seed. */
  init_rand();

  /* Open the log file. */
  init_log(log_file);

  /* Initialize memory. */
  init_mem();

  /* Initialize devices. */
  IFDEF(CONFIG_DEVICE, init_device());

  /* Initialize elf*/
  IFDEF(CONFIG_FTRACE, init_elf());

  /* Perform ISA dependent initialization. */
  init_isa();

  /* Load the image to memory. This will overwrite the built-in image. */
  long img_size = load_img();

  /* Initialize differential testing. */
  init_difftest(diff_so_file, img_size, difftest_port);

  /* Initialize the simple debugger. */
  init_sdb();

#ifndef CONFIG_ISA_loongarch32r
  IFDEF(CONFIG_ITRACE, init_disasm(
    MUXDEF(CONFIG_ISA_x86,     "i686",
    MUXDEF(CONFIG_ISA_mips32,  "mipsel",
    MUXDEF(CONFIG_ISA_riscv,
      MUXDEF(CONFIG_RV64,      "riscv64",
                               "riscv32"),
                               "bad"))) "-pc-linux-gnu"
  ));
#endif

  /* Display welcome message. */
  welcome();
}
#else // CONFIG_TARGET_AM
#include <limits.h>

static long load_img() {
  extern char bin_start, bin_end;
  uintptr_t start = (uintptr_t)&bin_start, end = (uintptr_t)&bin_end;
  Assert(end >= start, "Invalid embedded image symbol order");
  uintptr_t size = end - start;
  Assert(size <= SIZE_MAX && size <= LONG_MAX, "Embedded image size is not representable");

  uint64_t offset = CONFIG_PC_RESET_OFFSET;
  Assert(offset < (uint64_t)CONFIG_MSIZE &&
      offset <= (uint64_t)(paddr_t)-1 - PMEM_LEFT,
      "Embedded image reset vector is outside PMEM");
  Assert(size <= (uint64_t)CONFIG_MSIZE - offset,
      "Embedded image exceeds remaining PMEM");

  Log("img size = %ld", (long)size);
  memcpy(guest_to_host(RESET_VECTOR), &bin_start, size);
  return (long)size;
}

void am_init_monitor() {
  init_rand();
  init_mem();
  init_isa();
  load_img();
  IFDEF(CONFIG_DEVICE, init_device());
  welcome();
}
#endif
