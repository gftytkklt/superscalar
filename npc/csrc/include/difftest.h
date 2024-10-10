#ifndef DIFFTEST_H
#define DIFFTEST_H
#include <common.h>
void init_difftest(char *ref_so_file, long img_size, uint8_t* mem, uint64_t *cpu_gpr);
void difftest_skip_ref();
/* return true if error occurs */
bool difftest_step(uint64_t pc, uint64_t* dut, uint64_t sim_time);

enum { DIFFTEST_TO_DUT, DIFFTEST_TO_REF };
enum { COPY_PC, COPY_REG };

#endif