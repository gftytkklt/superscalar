#include <proc.h>
#include <elf.h>

#ifdef __LP64__
# define Elf_Ehdr Elf64_Ehdr
# define Elf_Phdr Elf64_Phdr
#else
# define Elf_Ehdr Elf32_Ehdr
# define Elf_Phdr Elf32_Phdr
#endif

static uintptr_t loader(PCB *pcb, const char *filename) {
  Elf_Ehdr ehdr = {};
  Elf_Phdr phdr = {};
  // naive version: ramdisk only consists of dummy
  #ifdef TEST_DUMMY
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
  #endif
}

void naive_uload(PCB *pcb, const char *filename) {
  uintptr_t entry = loader(pcb, filename);
  Log("Jump to entry = %p", entry);
  ((void(*)())entry) ();
}

