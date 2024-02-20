#include "verilated.h"
#include "verilated_dpi.h"
#include "verilated_vcd_c.h"
// #include "Vysyx_22040750.h"
#include "VysyxSoCFull.h"
#include "svdpi.h"
// #include "VysyxSoCFull__Dpi.h"
#define ANSI_FG_RED     "\33[1;31m"
#define ANSI_FG_GREEN   "\33[1;32m"
#define ANSI_NONE       "\33[0m"
#define ANSI_FMT(str, fmt) fmt str ANSI_NONE
extern "C" void flash_read(uint32_t addr, uint32_t *data) { assert(0); }
extern "C" void mrom_read(uint32_t addr, uint32_t *data) { *data = 0x00100073; }
static TOP_NAME* soc = NULL;
static uint64_t *cpu_gpr = NULL;
static uint32_t *wb_pc = NULL;
static bool finish = false;
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
    printf("%s at pc = 0x%08x, ret code=0x%lxh\n", ANSI_FMT("HIT BAD TRAP", ANSI_FG_RED), *wb_pc, cpu_gpr[10]);
  }
  else{
    printf("%s at pc = 0x%08x\n", ANSI_FMT("HIT GOOD TRAP", ANSI_FG_GREEN), *wb_pc);
  }
  //printf(" C: Im called fronm Scope :: %s \n\n ",svGetNameFromScope(svGetScope() ));
  //Vcpu_top::check();
  finish = true;
}
int main(int argc, char** argv){
    printf("hello ysyx!\n");
    Verilated::commandArgs(argc, argv);
    soc = new TOP_NAME;
    // waveform
    Verilated::traceEverOn(true);
    VerilatedVcdC* tfp = new VerilatedVcdC;
    soc->trace(tfp,99);
    tfp->open("soc.vcd");

    uint64_t sim_time = 0;
    soc->reset = 1;
    while(!finish && (sim_time < 1000)){
        // printf("time: %lu\n", sim_time);
        if(sim_time > 100){soc->reset = 0;}
        if(sim_time & 1){soc->clock = 1;}
        else{soc->clock = 0;}
        soc->eval();
        tfp->dump(sim_time);
        sim_time++;
    }
    soc->final();
    tfp->close();
    delete soc;
    printf("bye ysyx!\n");
    return 0;
}

