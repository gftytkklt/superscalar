#include <probe.h>

uint64_t *cpu_gpr = NULL;
uint32_t *wb_pc = NULL;
uint32_t *wb_inst = NULL;
bool diff_valid = false;
bool mmio_op = false;

void set_gpr_ptr(const svOpenArrayHandle r) {
  cpu_gpr = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
  //cpu_context->gpr = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
void set_diff_ptr(const svBit value) {
  diff_valid = static_cast<bool>(value);
}
void set_mmio_ptr(const svBit value) {
  mmio_op = static_cast<bool>(value);
}
void set_wb_pc_ptr(const svOpenArrayHandle r) {
  wb_pc = (uint32_t *)(((VerilatedDpiOpenVar*)r)->datap());
  //cpu_context->pc = (uint64_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
void set_wb_inst_ptr(const svOpenArrayHandle r) {
  wb_inst = (uint32_t *)(((VerilatedDpiOpenVar*)r)->datap());
}
void sim_end(){
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