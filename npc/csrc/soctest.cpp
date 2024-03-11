#include "verilated.h"
#include "verilated_dpi.h"
#include "verilated_vcd_c.h"
// #include "Vysyx_22040750.h"
#include "VysyxSoCFull.h"
#include "svdpi.h"
// #include "VysyxSoCFull__Dpi.h"
// #define CONFIG_WAVEFORM

#define ANSI_FG_RED     "\33[1;31m"
#define ANSI_FG_GREEN   "\33[1;32m"
#define ANSI_NONE       "\33[0m"
#define ANSI_FMT(str, fmt) fmt str ANSI_NONE
#define MROM_BASE 0x20000000
#define MROM_SIZE 0x1000
static TOP_NAME* soc = NULL;
static uint64_t *cpu_gpr = NULL;
static uint32_t *wb_pc = NULL;
static bool finish = false;
static uint8_t *mrom = NULL;
static char *img_path = NULL;
static uint64_t sim_time = 0;

extern "C" void flash_read(uint32_t addr, uint32_t *data) { assert(0); }
extern "C" void mrom_read(uint32_t addr, uint32_t *data) { 
  uint32_t index = (addr-MROM_BASE)&0xfffffffc;
  *data = *((uint32_t*)&mrom[index]);
  // *data = *((uint32_t*)&mrom[addr-MROM_BASE]);
  // printf("addr %x, mrom data = 0x%08x\n",addr, *data);
}
extern "C" void set_gpr_ptr(const svOpenArrayHandle r) {
  cpu_gpr = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
  //cpu_context->gpr = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
extern "C" void set_wb_pc_ptr(const svOpenArrayHandle r) {
  wb_pc = (uint32_t *)(((VerilatedDpiOpenVar*)r)->datap());
  //cpu_context->pc = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
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
void init_mrom(char *path){
  mrom = (uint8_t*)malloc(MROM_SIZE);
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
  long size = ftell(fp);
  if(size > MROM_SIZE){
    printf("size %ld of program is too large!\n", size);
    return;
  }
  printf("The image is %s, size = %ld\n", path, size);
  fseek(fp, 0, SEEK_SET);
  //int ret = fread(guest_to_host(RESET_VECTOR), size, 1, fp);
  int ret = fread(mrom, size, 1, fp);
  assert(ret == 1);
  fclose(fp);
}
int main(int argc, char** argv){
    printf("hello ysyx!\n");
    if(argc > 1){
      img_path = argv[1]; // hard encoding
    }
    init_mrom(img_path);
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
        // printf("time: %lu\n", sim_time);
        if(sim_time > 100){soc->reset = 0;}
        if(sim_time & 1){soc->clock = 1;}
        else{soc->clock = 0;}
        soc->eval();
        #ifdef CONFIG_WAVEFORM
        tfp->dump(sim_time);
        #endif
        sim_time++;
        // if(sim_time > 1000){break;}
    }
    soc->final();
    #ifdef CONFIG_WAVEFORM
    tfp->close();
    #endif
    delete soc;
    printf("bye ysyx!\n");
    return 0;
}

