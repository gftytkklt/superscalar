
// #include <common.h>
#include <difftest.h>
#include <probe.h>
#include <memory.h>

// #define CONFIG_WAVEFORM
// #define CONFIG_WAVEFORM
// #define CONFIG_DIFFTEST

static TOP_NAME* soc = NULL;

bool finish = false;
uint64_t sim_time = 0;

static char *img_path = NULL;
static char *ref_so_file = NULL;

int main(int argc, char** argv){
    printf("hello ysyx!\n");
    if(argc > 1){
      img_path = argv[1]; // hard encoding
    }
    init_memory(img_path, FLASH);
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
    soc->eval(); // init probe ptr
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
    while(!finish){
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

