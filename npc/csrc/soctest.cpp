#include "verilated.h"
#include "verilated_dpi.h"
#include "verilated_vcd_c.h"
// #include "Vysyx_22040750.h"
#include "VysyxSoCFull.h"
#include "svdpi.h"
#include <common.h>
#include <difftest.h>
#include "VysyxSoCFull__Dpi.h"
// #define CONFIG_WAVEFORM
// #define CONFIG_WAVEFORM
#define CONFIG_DIFFTEST

static TOP_NAME* soc = NULL;
static uint64_t *cpu_gpr = NULL;
static uint32_t *wb_pc = NULL;
static uint32_t *wb_inst = NULL;
static bool diff_valid = false;
static bool mmio_op = false;
static bool finish = false;
static uint8_t *mrom = NULL;
static uint8_t *flash = NULL;
static char *img_path = NULL;
static char *ref_so_file = NULL;
static uint64_t sim_time = 0;

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
extern "C" void set_gpr_ptr(const svOpenArrayHandle r) {
  cpu_gpr = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
  //cpu_context->gpr = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
extern "C" void set_diff_ptr(const svBit value) {
  diff_valid = static_cast<bool>(value);
}
extern "C" void set_mmio_ptr(const svBit value) {
  mmio_op = static_cast<bool>(value);
}
extern "C" void set_wb_pc_ptr(const svOpenArrayHandle r) {
  wb_pc = (uint32_t *)(((VerilatedDpiOpenVar*)r)->datap());
  //cpu_context->pc = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
extern "C" void set_wb_inst_ptr(const svOpenArrayHandle r) {
  wb_inst = (uint32_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
extern "C" void sim_end(){
  //set_gpr_ptr(10);
  //printf("%ld\n", cpu_gpr[10]);
  if(cpu_gpr[10]){
    printf("%lu: %s at pc = 0x%08x, ret code=0x%lxh\n", sim_time, ANSI_FMT("HIT BAD TRAP", ANSI_FG_RED), *wb_pc, cpu_gpr[10]);
  }
  else{
    printf("%lu: %s at pc = 0x%08x\n", sim_time, ANSI_FMT("HIT GOOD TRAP", ANSI_FG_GREEN), *wb_pc);
  }
  //printf(" C: Im called fronm Scope :: %s \n\n ",svGetNameFromScope(svGetScope() ));
  //Vcpu_top::check();
  finish = true;
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
  // if(path == NULL){
  //   printf("no program provided\n");
  //   return;
  // }
  // FILE *fp = fopen(path, "rb");
  // if(fp == NULL){
  //   printf("cannot open %s\n", path);
  //   return;
  // }
  // fseek(fp, 0, SEEK_END);
  // long size = ftell(fp);
  // if(size > MROM_SIZE){
  //   printf("size %ld of program is too large!\n", size);
  //   return;
  // }
  // printf("The image is %s, size = %ld\n", path, size);
  // fseek(fp, 0, SEEK_SET);
  // //int ret = fread(guest_to_host(RESET_VECTOR), size, 1, fp);
  // int ret = fread(mrom, size, 1, fp);
  // assert(ret == 1);
  // fclose(fp);
}
void init_flash(char *path){
  flash = (uint8_t*)malloc(FLSAH_SIZE);
  load_proc(path, flash, FLSAH_SIZE);
}
int main(int argc, char** argv){
    printf("hello ysyx!\n");
    if(argc > 1){
      img_path = argv[1]; // hard encoding
    }
    init_flash(img_path);
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
    Verilated::commandArgs(argc, argv);
    soc = new TOP_NAME;
    // waveform
    #ifdef CONFIG_WAVEFORM
    Verilated::traceEverOn(true);
    VerilatedVcdC* tfp = new VerilatedVcdC;
    soc->trace(tfp,99);
    tfp->open("soc.vcd");
    #endif
    
    soc->reset = 1;
    while(!finish){
      if(sim_time == 1){
        #ifdef CONFIG_DIFFTEST
        printf("difftest: %s\n",ANSI_FMT("ON", ANSI_FG_GREEN));
        ref_so_file = argv[2];
        init_difftest(ref_so_file, FLSAH_SIZE, flash, cpu_gpr);
        #else
        printf("difftest: %s\n",ANSI_FMT("OFF", ANSI_FG_RED));
        #endif
        #ifdef CONFIG_WAVEFORM
        printf("waveform: %s\n",ANSI_FMT("ON", ANSI_FG_GREEN));
        #else
        printf("waveform: %s\n",ANSI_FMT("OFF", ANSI_FG_RED));
        #endif
      }
      // difftest_step(*wb_pc, cpu_gpr, sim_time);

        // printf("time: %lu\n", sim_time);
        if(sim_time > 20){soc->reset = 0;}
        if(sim_time & 1){soc->clock = 1;}
        else{soc->clock = 0;}
        // printf("before eval %d\n", *diff_valid);
        soc->eval();
        #ifdef CONFIG_WAVEFORM
        tfp->dump(sim_time);
        #endif
        #ifdef CONFIG_DIFFTEST
        // printf("wb_pc: %x\n", *wb_pc);
        // printf("%lu: after eval %d %x\n", sim_time, diff_valid, *wb_pc);
        if((diff_valid == true)&&(soc->clock == 1)){
          // printf("wb_pc: %x, inst: %08x, mmio: %d, valid: %d\n", *wb_pc, *wb_inst, mmio_op, diff_valid);
          // printf("in valid loop\n");
          if(mmio_op == true){
            // printf("mmio op\n");
            difftest_skip_ref();
          }
          // printf("wb_pc: %x\n", *wb_pc);
          if(difftest_step(*wb_pc, cpu_gpr, sim_time)){
            printf("%lu: %s at pc = 0x%08x\n", sim_time, ANSI_FMT("DIFF ABORT", ANSI_FG_RED), *wb_pc);
            break;
          }
        }
        #endif
        // difftest_step(*wb_pc, cpu_gpr, sim_time);
        sim_time++;
        // if(sim_time > 400){break;}
    }
    soc->final();
    #ifdef CONFIG_WAVEFORM
    tfp->close(); 
    #endif
    delete soc;
    printf("bye ysyx!\n");
    return 0;
}

