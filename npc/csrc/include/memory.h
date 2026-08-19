#ifndef MEMORY_H
#define MEMORY_H

#include <common.h>
enum { FLASH, MROM };
extern "C" void flash_read(int32_t addr, int32_t *data);
extern "C" void mrom_read(int32_t addr, int32_t *data);
void init_memory(char *path, int type);
extern uint8_t *mrom;
extern uint8_t *flash;
void load_proc(char *path, void *dest, uint64_t capacity);
#endif