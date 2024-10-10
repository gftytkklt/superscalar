#include <memory.h>
uint8_t *mrom = NULL;
uint8_t *flash = NULL;

// addr begin from 0
void flash_read(int32_t addr, int32_t *data) { 
  // printf("flash addr: %x\n", addr);
  // uint32_t index = (addr-FLASH_BASE)&0xfffffffc;
  uint32_t index = addr;
  // printf("addr = %x, index = %x\n", addr, index);
  // *data = *((uint32_t*)&flash[index]); 
  *data = ((uint32_t)flash[index]) |
          ((uint32_t)flash[index + 1] << 8) |
          ((uint32_t)flash[index + 2] << 16) |
          ((uint32_t)flash[index + 3] << 24);
}
void mrom_read(int32_t addr, int32_t *data) {
  // printf("mrom addr: %x\n", addr);
  uint32_t index = (addr-MROM_BASE)&0xfffffffc;
  *data = *((uint32_t*)&mrom[index]);
}

void load_proc(char *path, void *dest, uint64_t capacity){
  if(path == NULL){
    printf("no program provided\n");
    return;
  }
  FILE *fp = fopen(path, "rb");
  if(fp == NULL){
    printf("cannot open %s\n", path);
    return;
  }
  fseek(fp, 0, SEEK_END);
  uint64_t size = ftell(fp);
  if(size > capacity){
    printf("size %ld of program is too large!\n", size);
    return;
  }
  printf("The image is %s, size = %ld\n", path, size);
  fseek(fp, 0, SEEK_SET);
  //int ret = fread(guest_to_host(RESET_VECTOR), size, 1, fp);
  int ret = fread(dest, size, 1, fp);
  assert(ret == 1);
  fclose(fp);
}
void init_mrom(char *path){
  mrom = (uint8_t*)malloc(MROM_SIZE);
  load_proc(path, mrom, MROM_SIZE);
}
void init_flash(char *path){
  flash = (uint8_t*)malloc(FLSAH_SIZE);
  load_proc(path, flash, FLSAH_SIZE);
}

void init_memory(char *path, int type){
  if(type == FLASH){
    init_flash(path);
  }
  else if(type == MROM){
    init_mrom(path);
  }
  else{
    printf("unknown memory type\n");
  }
}

// some deprecated functions
    // init_mrom(img_path);
    // uint32_t data = 0;
    // printf("flash ref data: \n");
    // for(uint32_t addr = 0; addr < 0 + 0x100; addr += 4){
    //   flash_read(addr, &data);
    //   printf("addr: %x, data: 0x%08x\n", addr, data);
    // }
    // printf("flash ref data end\n");
    // return 0;
    // test data
    // uint32_t start = 0x200000f9;
    // uint32_t end = 0x20000219;
    // uint32_t data;
    // for(uint32_t i = start; i<end; i = i+4){
    //   mrom_read(i, &data);
    //   printf("addr %x, data %x\n", i, data);
    // }
    // return 0;
    // test end