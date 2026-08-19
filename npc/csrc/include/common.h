#ifndef COMMON_H
#define COMMON_H
#include "verilated.h"
#include "verilated_dpi.h"
#include "verilated_vcd_c.h"
// #include "Vysyx_22040750.h"
#include "VysyxSoCFull.h"
#include "svdpi.h"
#include "VysyxSoCFull__Dpi.h"
#define ANSI_FG_RED     "\33[1;31m"
#define ANSI_FG_GREEN   "\33[1;32m"
#define ANSI_NONE       "\33[0m"
#define ANSI_FMT(str, fmt) fmt str ANSI_NONE
#define MROM_BASE 0x20000000
#define MROM_SIZE 0x1000
#define FLASH_BASE 0x30000000
#define FLSAH_SIZE 0x1000000

extern bool finish;
extern uint64_t sim_time;

#endif