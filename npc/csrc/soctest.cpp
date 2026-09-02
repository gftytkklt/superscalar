
// #include <common.h>
#include <cstdlib>
#include <cstdio>
#include <difftest.h>
#include <probe.h>
#include <memory.h>

// #define CONFIG_WAVEFORM
// #define CONFIG_DIFFTEST

#ifdef CONFIG_NVBOARD
#include <nvboard.h>
void nvboard_bind_all_pins(TOP_NAME* top);   // 由 auto_pin_bind.cpp 生成
#endif

static TOP_NAME* soc = NULL;

bool finish = false;
uint64_t sim_time = 0;

static char *img_path = NULL;
static char *ref_so_file = NULL;

// 波形输出路径/降频，供调试仿真用。
//   编译期 WAVE=1 只决定二进制是否带 trace 支持（CONFIG_WAVEFORM）。
//   运行期必须 WAVE_ON=1 才真正 dump（否则即使带 trace 支持也不写 VCD，避免
//   长仿真/回归时 build/soc.vcd 持续膨胀爆盘）。
//   WAVE_FILE: 波形文件路径（默认 build/soc.vcd，落在 npc/build/，不进工作区根目录）。
//   WAVE_DIV : 每 N 个 posedge 帧 dump 一次（默认 1=全量）。长仿真看波形建议调大。
static bool wave_enabled_flag = false;
static const char* wave_file() {
  const char* f = getenv("WAVE_FILE");
  return f ? f : "build/soc.vcd";
}
static unsigned wave_div() {
  const char* d = getenv("WAVE_DIV");
  return (d && atoi(d) > 0) ? (unsigned)atoi(d) : 1u;
}

int main(int argc, char** argv){
    printf("hello ysyx!\n");
    if(argc > 1){
      img_path = argv[1]; // hard encoding
    }
    init_memory(img_path, FLASH);
    Verilated::commandArgs(argc, argv);
    // 运行期波形开关：仅 WAVE_ON=1 时 dump（无论二进制是否带 trace 支持）。
    const char* won = getenv("WAVE_ON");
    wave_enabled_flag = (won && strcmp(won, "1") == 0);
    soc = new TOP_NAME;
    #ifdef CONFIG_NVBOARD
    // NVBoard（阶段 J0）：绑定外部引脚 + 初始化窗口（SDL）。
    nvboard_bind_all_pins(soc);
    nvboard_init();
    #endif
    // waveform
    #ifdef CONFIG_WAVEFORM
    VerilatedVcdC* tfp = NULL;
    if (wave_enabled_flag) {
      Verilated::traceEverOn(true);
      tfp = new VerilatedVcdC;
      soc->trace(tfp,99);
      tfp->open(wave_file());
      printf("waveform: %s -> %s (dump div=%u)\n", ANSI_FMT("ON", ANSI_FG_GREEN), wave_file(), wave_div());
    } else {
      printf("waveform: %s (build has trace support, but WAVE_ON!=1)\n", ANSI_FMT("OFF", ANSI_FG_RED));
    }
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
        #ifdef CONFIG_NVBOARD
        // NVBoard 每全周期调用一次（主循环是半周期 eval）：UART 采样按全周期计，
        // divisor 才与 16550 位周期（16×dl clk）对齐。内部再自适应限帧 ~60fps。
        if (posedge_phase) nvboard_update();
        #else
        // 无 NVBoard 时外设输入空闲拉高，避免误触发：
        //   - UART RX：16550 接收器把悬空/0 当起始位误收；
        //   - PS/2：ps2_clk/ps2_data 悬空/0 会（ps2_clk 上升沿）被解码器当起始位误采。
        soc->externalPins_uart_rx = 1;
        soc->externalPins_ps2_clk = 1;
        soc->externalPins_ps2_data = 1;
        #endif
        soc->eval();
        #ifdef CONFIG_WAVEFORM
        // 波形窗口：WAVE_START/WAVE_END 限制 dump 区间（用于只抓卡死前后的一小段逐拍波形）。
        // 默认全量（div 控制降频）。
        {
          static unsigned wstart = (getenv("WAVE_START") ? (unsigned)strtoul(getenv("WAVE_START"),NULL,10) : 0u);
          static unsigned wend   = (getenv("WAVE_END")   ? (unsigned)strtoul(getenv("WAVE_END"),NULL,10)   : 0xffffffffu);
          if (wave_enabled_flag && posedge_phase &&
              (sim_time >= (uint64_t)wstart) && (sim_time <= (uint64_t)wend) &&
              ((sim_time >> 1) % wave_div() == 0)) tfp->dump(sim_time);
        }
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
        // SIM_END: 提前终止（调试用，避免卡死无限跑）
        {
          static unsigned long s_end = (getenv("SIM_END") ? strtoul(getenv("SIM_END"),NULL,10) : 0ul);
          if (s_end && sim_time >= s_end) { printf("[SIM] t=%lu reach SIM_END\n", sim_time); fflush(stdout); break; }
        }
    }
    soc->final();
    #ifdef CONFIG_NVBOARD
    nvboard_quit();
    #endif
    #ifdef CONFIG_WAVEFORM
    if (wave_enabled_flag) {
      tfp->close();
      printf("waveform closed: %s\n", wave_file());
    }
    #endif
    delete soc;
    printf("bye ysyx!\n");
    return 0;
}

