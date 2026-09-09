#ifndef PROBE_H
#define PROBE_H
#include <common.h>
extern "C" void set_gpr_ptr(const svOpenArrayHandle r);
extern "C" void set_diff_ptr(const svBit value);
extern "C" void set_mmio_ptr(const svBit value);
extern "C" void set_wb_pc_ptr(const svOpenArrayHandle r);
extern "C" void set_wb_inst_ptr(const svOpenArrayHandle r);
extern "C" void sim_end();

extern uint64_t *cpu_gpr;
extern uint32_t *wb_pc;
extern uint32_t *wb_inst;
extern bool diff_valid;
extern bool mmio_op;

#endif