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
#include <cpu/cpu.h>
#include <difftest-def.h>
#include <memory/paddr.h>

// __EXPORT void difftest_memcpy(paddr_t addr, void *buf, size_t n, bool direction) {
//   assert(0);
// }

// __EXPORT void difftest_regcpy(void *dut, bool direction) {
//   assert(0);
// }

// __EXPORT void difftest_exec(uint64_t n) {
//   assert(0);
// }

// __EXPORT void difftest_raise_intr(word_t NO) {
//   assert(0);
// }

// __EXPORT void difftest_init(int port) {
//   void init_mem();
//   init_mem();
//   /* Perform ISA dependent initialization. */
//   init_isa();
// }

uint64_t cur_pc;
__EXPORT void difftest_memcpy(uint64_t addr, void *buf, size_t n, bool direction) {
  if (n == 0) return;
  // NPC passes a 64-bit address even when this REF uses a narrower paddr_t.
  uint8_t* addr_pt = addr <= (paddr_t)-1 ? addr_to_soc_range((paddr_t)addr, n) : NULL;
  if (addr_pt == NULL) {
    panic("difftest_memcpy range out of bounds: addr=0x%016" PRIx64 ", n=%zu", addr, n);
    return;
  }
  uint8_t* tmp = (uint8_t*) buf; // addr pt of npc
  if(direction == DIFFTEST_TO_DUT){
    for (size_t i=0;i<n;i++){
      tmp[i] = addr_pt[i];
    }
    //tmp[32] = cpu.pc;
  }
  else{
    for (size_t i=0;i<n;i++){
      addr_pt[i] = tmp[i];
    }
    //cpu.pc = tmp[32];
  }
}
// here, *dut must be dut reg
// TODO: add pc cp, set pc to correct value
__EXPORT void difftest_regcpy(void *dut, bool direction, bool iscpreg) {
  //assert(0);
  unsigned long* tmp = (unsigned long*) dut;
  if(direction == DIFFTEST_TO_DUT){
    if(iscpreg){
      for (int i=0;i<32;i++){
        tmp[i] = cpu.gpr[i];
      }
    }
    else{
      tmp[32] = cpu.pc;
    }
  }
  else{
    //printf("dut to ref\n");
    for (int i=0;i<32;i++){
      
      cpu.gpr[i] = tmp[i];
      //printf("%d: %lx\n",i, cpu.gpr[i]);
    }
    //cpu.pc = pc;
    //printf("end\n");
    cpu.pc = tmp[32];
  }
}

__EXPORT void difftest_exec(uint64_t n) {
  //assert(0);
  cpu_exec(n);
}

__EXPORT void difftest_raise_intr(word_t NO) {
  //assert(0);
  isa_raise_intr(NO, cpu.pc);
}

__EXPORT void difftest_ref_display() {
  isa_reg_display();
}
// I think this init function is not necessary?
__EXPORT void difftest_init(int port) {
  printf("init difftest at port %d\n", port);
  // void init_mem();
  // init_mem();
  // /* Perform ISA dependent initialization. */
  // init_isa();
}
