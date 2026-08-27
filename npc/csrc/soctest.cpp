
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
        // 半周期驱动：每个 sim_time 一次 eval。
        //   odd : clock=1 -> eval 内发生 posedge + 组合结算；
        //   even: clock=0 -> eval 仅组合结算（无沿，触发器保持）。
        // 事件队列对应关系：
        //   - 触发器在 posedge 取"沿前已稳定"的输入（reset/从端请求），符合 NBA 语义；
        //   - 组合信号（diff_valid/wb_pc 等，由 always@(*) 结算）在 eval 后即本拍
        //     posedge 之后的 retire 信息，故 difftest 只在 posedge 拍采样并与参考
        //     模型的"单指令推进"一一对应。
        bool posedge_phase = (sim_time & 1) != 0;

        // sync reset (always@(posedge) if(rst))：在 posedge 拍、clock 0->1 前撤销，
        // 保证该拍上升沿采样到已撤销值；even 拍不写，消除相位歧义。
        if (posedge_phase && (sim_time > 20)) { soc->reset = 0; }

        soc->clock = posedge_phase;
        soc->eval();
        #ifdef CONFIG_WAVEFORM
        if (posedge_phase) tfp->dump(sim_time);   // 仅 posedge 帧（信息不丢，去半拍冗余）
        #endif
        #ifdef CONFIG_DIFFTEST
        // printf("wb_pc: %x\n", *wb_pc);
        // printf("%lu: after eval %d %x\n", sim_time, diff_valid, *wb_pc);
        if(diff_valid && posedge_phase){
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

