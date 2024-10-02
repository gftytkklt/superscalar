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

#if   defined(CONFIG_PMEM_MALLOC)
static uint8_t *pmem = NULL;
#else // CONFIG_PMEM_GARRAY
static uint8_t pmem[CONFIG_MSIZE] PG_ALIGN = {};
static uint8_t flash[CONFIG_FLASHSIZE] PG_ALIGN = {};
static uint8_t sram[CONFIG_SRAMSIZE] PG_ALIGN = {};
static uint8_t mrom[CONFIG_MROMSIZE] PG_ALIGN = {};
#endif

uint8_t* guest_to_host(paddr_t paddr) { return pmem + paddr - CONFIG_MBASE; }
paddr_t host_to_guest(uint8_t *haddr) { return haddr - pmem + CONFIG_MBASE; }
uint8_t* addr_to_soc(paddr_t addr) {
  if(in_pmem(addr)) return pmem + addr - CONFIG_MBASE;
  if(in_flash(addr)) return flash + addr - CONFIG_FLASHBASE;
  if(in_sram(addr)) return sram + addr - CONFIG_SRAMBASE;
  if(in_mrom(addr)) return mrom + addr - CONFIG_MROMBASE;
  return NULL;
}

// static word_t pmem_read(paddr_t addr, int len) {
//   word_t ret = host_read(guest_to_host(addr), len);
//   return ret;
// }

// static void pmem_write(paddr_t addr, int len, word_t data) {
//   host_write(guest_to_host(addr), len, data);
// }

static void out_of_bound(paddr_t addr) {
  panic("address = " FMT_PADDR " is out of bound of pmem [" FMT_PADDR ", " FMT_PADDR "] at pc = " FMT_WORD,
      addr, PMEM_LEFT, PMEM_RIGHT, cpu.pc);
}

void init_mem() {
  // itrace = fopen("itrace.txt","w");
  // dtrace = fopen("dtrace.txt","w");
#if   defined(CONFIG_PMEM_MALLOC)
  pmem = malloc(CONFIG_MSIZE);
  assert(pmem);
#endif
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
}

word_t paddr_read(paddr_t addr, int len) {
  // word_t result = 0;
  //if (likely(in_pmem(addr))) return pmem_read(addr, len);
  //IFDEF(CONFIG_DEVICE, return mmio_read(addr, len));
  // bool invaddr = true;
  paddr_t base = 0;
  uint8_t *mem = NULL;
  if (likely(in_pmem(addr))) {
    // word_t result = pmem_read(addr, len);
    // if ((addr >= (unsigned long)0x80006400) && (addr < (unsigned long)0x80006500))
    // IFDEF(CONFIG_MTRACE, Log("Get data 0x%lx from addr "FMT_PADDR"", result, addr));
    // return result;
    base = CONFIG_MBASE;
    mem = pmem;
  }
  else if(likely(in_flash(addr))) {
    // panic("Flash memory read is not implemented");
    base = CONFIG_FLASHBASE;
    mem = flash;
  }
  else if(likely(in_sram(addr))) {
    // panic("SRAM memory read is not implemented");
    base = CONFIG_SRAMBASE;
    mem = sram;
  }
  else if(likely(in_mrom(addr))) {
    // panic("MROM memory read is not implemented");
    base = CONFIG_MROMBASE;
    mem = mrom;
  }
  if(mem != NULL) {
    word_t result = host_read(mem + addr - base, len);
    IFDEF(CONFIG_MTRACE, Log("Get data 0x%lx from addr "FMT_PADDR"", result, addr));
    return result;
  }
  IFDEF(CONFIG_DEVICE, return mmio_read(addr, len));
  out_of_bound(addr);
  
  // return result;
  return 0;
}

void paddr_write(paddr_t addr, int len, word_t data) {
  // if ((addr >= (unsigned long)0x80006400) && (addr < (unsigned long)0x80006500))
  // IFDEF(CONFIG_MTRACE, Log("Write data 0x%lx to addr "FMT_PADDR"", data, addr));
  // if (likely(in_pmem(addr))) { pmem_write(addr, len, data); return; }

  paddr_t base = 0;
  uint8_t *mem = NULL;
  if (likely(in_pmem(addr))) {
    // pmem_write(addr, len, data);
    // IFDEF(CONFIG_MTRACE, Log("Write data 0x%lx to addr "FMT_PADDR"", data, addr));
    base = CONFIG_MBASE;
    mem = pmem;
  }
  else if(likely(in_flash(addr))) {
    // panic("Flash memory write is not implemented");
    base = CONFIG_FLASHBASE;
    mem = flash;
  }
  else if(likely(in_sram(addr))) {
    // panic("SRAM memory write is not implemented");
    base = CONFIG_SRAMBASE;
    mem = sram;
  }
  else if(likely(in_mrom(addr))) {
    // panic("MROM memory write is not implemented");
    base = CONFIG_MROMBASE;
    mem = mrom;
  }
  if(mem != NULL) {
    host_write(mem + addr - base, len, data);
    IFDEF(CONFIG_MTRACE, Log("Write data 0x%lx to addr "FMT_PADDR"", data, addr));
    return;
  }

  IFDEF(CONFIG_DEVICE, mmio_write(addr, len, data); return);
  out_of_bound(addr);
}
