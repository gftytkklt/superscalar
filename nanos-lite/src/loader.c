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
  #elif defined(TEST_FILE)
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
      fs_lseek(fd, offset, SEEK_SET);
      // naive version
      #ifndef HAS_VME
      fs_read(fd, (void *)vaddr, filesz);
      memset((void *)(vaddr + filesz), 0, (memsz-filesz));
      #endif
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

