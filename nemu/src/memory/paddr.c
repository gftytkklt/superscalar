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

#include <memory/host.h>
#include <memory/paddr.h>
#include <device/mmio.h>
#include <isa.h>

// 存储介质统一建模（2026-08-31 阶段 H）：
//   每种存储介质 = {名称, 地址空间(base,size), 内存指针(mem), 读写函数钩子(read/write)}。
//   抽象的读写只与地址和长度有关：paddr_read/paddr_write 按地址命中注册区间后，
//   调用对应介质的读写钩子（目前各介质均为 host_read/host_write 直接数组访存，
//   未来如需对某种介质特殊处理（如只读 flash、带时序的 SDRAM），只需改该介质的钩子）。
typedef struct {
  const char *name;
  paddr_t base;
  size_t size;
  uint8_t *mem;
  word_t (*read )(uint8_t *mem, paddr_t offset, int len);
  void   (*write)(uint8_t *mem, paddr_t offset, int len, word_t data);
} MemRegion;

static word_t mem_read(uint8_t *mem, paddr_t offset, int len) {
  return host_read(mem + offset, len);
}
static void mem_write(uint8_t *mem, paddr_t offset, int len, word_t data) {
  host_write(mem + offset, len, data);
}

#if   defined(CONFIG_PMEM_MALLOC)
static uint8_t *pmem = NULL;
#else // CONFIG_PMEM_GARRAY
static uint8_t pmem[CONFIG_MSIZE] PG_ALIGN = {};
#endif
static uint8_t flash[CONFIG_FLASHSIZE] PG_ALIGN = {};
static uint8_t sram[CONFIG_SRAMSIZE] PG_ALIGN = {};
static uint8_t mrom[CONFIG_MROMSIZE] PG_ALIGN = {};
// SDRAM 区 [0xa0000000, 0xa1000000) 与 NEMU 设备 MMIO（serial/rtc/keyboard/vga 等，默认也在
// 0xa0000000 区）重叠。编译策略：仅当 DEVICE 关闭（difftest ref）时把 SDRAM 作为内存区注册；
// DEVICE 开启（native 解释器模式）时该地址由 mmio_read/write 按外设处理，SDRAM 内存区不编译。
#ifndef CONFIG_DEVICE
static uint8_t sdram[CONFIG_SDRAMSIZE] PG_ALIGN = {};
#endif

// 注册的存储空间（按地址查找，顺序无关）。pmem 的 mem 直接引用 pmem：
// CONFIG_PMEM_GARRAY 时为静态数组地址（编译期可用，difftest 流不调用 init_mem 也有效）；
// CONFIG_PMEM_MALLOC 时为指针变量（init_mem 里 malloc 后赋值）。
static MemRegion mem_regions[] = {
  { "pmem",  CONFIG_MBASE,       CONFIG_MSIZE,       pmem,  mem_read, mem_write },
  { "flash", CONFIG_FLASHBASE,   CONFIG_FLASHSIZE,   flash, mem_read, mem_write },
  { "sram",  CONFIG_SRAMBASE,    CONFIG_SRAMSIZE,    sram,  mem_read, mem_write },
  { "mrom",  CONFIG_MROMBASE,    CONFIG_MROMSIZE,    mrom,  mem_read, mem_write },
#ifndef CONFIG_DEVICE
  { "sdram", CONFIG_SDRAMBASE,   CONFIG_SDRAMSIZE,   sdram, mem_read, mem_write },
#endif
};
#define NR_MEM_REGIONS (sizeof(mem_regions) / sizeof(mem_regions[0]))

static MemRegion* find_mem_region(paddr_t addr) {
  for (int i = 0; i < NR_MEM_REGIONS; i++) {
    MemRegion *r = &mem_regions[i];
    if (addr - r->base < r->size) return r;
  }
  return NULL;
}

uint8_t* guest_to_host(paddr_t paddr) { return pmem + paddr - CONFIG_MBASE; }
paddr_t host_to_guest(uint8_t *haddr) { return haddr - pmem + CONFIG_MBASE; }
uint8_t* addr_to_soc(paddr_t addr) {
  MemRegion *r = find_mem_region(addr);
  return r ? r->mem + (addr - r->base) : NULL;
}

static void out_of_bound(paddr_t addr) {
  panic("address = " FMT_PADDR " is out of bound of pmem [" FMT_PADDR ", " FMT_PADDR "] at pc = " FMT_WORD,
      addr, PMEM_LEFT, PMEM_RIGHT, cpu.pc);
}

void init_mem() {
#if   defined(CONFIG_PMEM_MALLOC)
  pmem = malloc(CONFIG_MSIZE);
  assert(pmem);
#endif
  mem_regions[0].mem = pmem;   // pmem 指针（malloc 或静态数组）运行时确定
#ifdef CONFIG_MEM_RANDOM
  uint32_t *p = (uint32_t *)pmem;
  int i;
  for (i = 0; i < (int) (CONFIG_MSIZE / sizeof(p[0])); i ++) {
    p[i] = rand();
  }
#endif
  Log("physical memory area [" FMT_PADDR ", " FMT_PADDR "]", PMEM_LEFT, PMEM_RIGHT);
  Log("flash memory area [" FMT_PADDR ", " FMT_PADDR "]", CONFIG_FLASHBASE, CONFIG_FLASHBASE + CONFIG_FLASHSIZE - 1);
  Log("sram memory area [" FMT_PADDR ", " FMT_PADDR "]", CONFIG_SRAMBASE, CONFIG_SRAMBASE + CONFIG_SRAMSIZE - 1);
  Log("mrom memory area [" FMT_PADDR ", " FMT_PADDR "]", CONFIG_MROMBASE, CONFIG_MROMBASE + CONFIG_MROMSIZE - 1);
#ifndef CONFIG_DEVICE
  Log("sdram memory area [" FMT_PADDR ", " FMT_PADDR "]", CONFIG_SDRAMBASE, CONFIG_SDRAMBASE + CONFIG_SDRAMSIZE - 1);
#endif
}

word_t paddr_read(paddr_t addr, int len) {
  MemRegion *r = find_mem_region(addr);
  if (r != NULL) {
    word_t result = r->read(r->mem, addr - r->base, len);
    IFDEF(CONFIG_MTRACE, Log("Get data 0x%lx from addr "FMT_PADDR"", result, addr));
    return result;
  }
  IFDEF(CONFIG_DEVICE, return mmio_read(addr, len));
  out_of_bound(addr);
  return 0;
}

void paddr_write(paddr_t addr, int len, word_t data) {
  MemRegion *r = find_mem_region(addr);
  if (r != NULL) {
    r->write(r->mem, addr - r->base, len, data);
    IFDEF(CONFIG_MTRACE, Log("Write data 0x%lx to addr "FMT_PADDR"", data, addr));
    return;
  }
  IFDEF(CONFIG_DEVICE, mmio_write(addr, len, data); return);
  out_of_bound(addr);
}