#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <cassert>
#include <common.h>
#include <difftest.h>

const char *regs[] = {
  "$0", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
  "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
  "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
  "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"
};
static bool is_skip_ref = false;
static uint64_t cpu_context[33];
void (*nemu_difftest_memcpy)(uint64_t addr, void* buf, size_t n, bool direction) = NULL;
void (*nemu_difftest_regcpy)(void* dut, bool direction, bool iscpreg) = NULL;
void (*nemu_difftest_exec)(uint64_t n) = NULL;
void (*nemu_difftest_raise_intr)(uint64_t NO) = NULL;
void (*nemu_difftest_ref_display)() = NULL;

void init_difftest(char *ref_so_file, long img_size, uint8_t* mem, uint64_t *cpu_gpr){
    void *handle = dlopen(ref_so_file, RTLD_LAZY);
    if(!handle){
        printf("dlopen %s failed\n", ref_so_file);
        assert(0);
    }
    nemu_difftest_memcpy = (void (*)(uint64_t, void*, size_t, bool))dlsym(handle, "difftest_memcpy");
    assert(nemu_difftest_memcpy);
    nemu_difftest_regcpy = (void (*)(void*, bool, bool))dlsym(handle, "difftest_regcpy");
    assert(nemu_difftest_regcpy);
    nemu_difftest_exec = (void (*)(uint64_t))dlsym(handle, "difftest_exec");
    assert(nemu_difftest_exec);
    nemu_difftest_raise_intr = (void (*)(uint64_t))dlsym(handle, "difftest_raise_intr");
    assert(nemu_difftest_raise_intr);
    void(*nemu_difftest_init)(void) = (void (*)())dlsym(handle, "difftest_init");
    assert(nemu_difftest_init);
    void (*nemu_difftest_ref_display)(void) = (void (*)())dlsym(handle, "difftest_ref_display");
    assert(nemu_difftest_ref_display);
    // printf("difftest link end\n");
    nemu_difftest_init();
    nemu_difftest_memcpy(FLASH_BASE, mem, img_size, DIFFTEST_TO_REF);
    for(int i = 0;i<32;i++){
        cpu_context[i] = cpu_gpr[i];
    }
    cpu_context[32] = FLASH_BASE;
    nemu_difftest_regcpy(cpu_context, DIFFTEST_TO_REF, COPY_REG);
    printf("difftest init end\n");
}

void difftest_skip_ref(){
    is_skip_ref = true;
}

bool difftest_step(uint64_t pc, uint64_t* dut, uint64_t sim_time){
    // printf("step exec\n");
    uint64_t ref_data[33];
    bool error = false;
    if(is_skip_ref){
        // printf("%lu: skip exec at %lx\n", sim_time, pc);
        for(int i = 0;i<32;i++){
            cpu_context[i] = dut[i];
        }
        cpu_context[32] = pc+4;// skip to next instruction
        // always copy pc and reg to ref
        nemu_difftest_regcpy(cpu_context, DIFFTEST_TO_REF, COPY_REG);
        is_skip_ref = false;
        return false;
    }
    nemu_difftest_regcpy(ref_data, DIFFTEST_TO_DUT, COPY_PC);
    nemu_difftest_exec(1);
    nemu_difftest_regcpy(ref_data, DIFFTEST_TO_DUT, COPY_REG);
    //printf("ref exec\n");
    if(pc != ref_data[32]){printf("time: %ld, pc does not match! dut pc: %lx, ref pc: %lx\n",sim_time, pc, ref_data[32]);error = true;}
    // else{printf("time: %ld, pc: %lx\n",sim_time, pc);}
    for(int i=0;i<32;i++){
        if(dut[i] != ref_data[i]){printf("time: %ld, pc: %lx(dut), %lx(ref), reg %s does not match! ref: %lx, dut: %lx\n", sim_time, pc, ref_data[32], regs[i], ref_data[i], dut[i]);error = true;}
    }
    return error;
}