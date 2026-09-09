// ============================================================================
// Standalone CPU-core testbench (Verilator) with an AXI4-slave memory model.
//
// 与 Verilog 分层事件队列 (stratified event queue) 的一致性说明：
//
//   每个仿真步执行两次 eval：
//     [1] posedge eval  (clock=1) -- 该时刻发生时钟沿：
//         - DUT 触发器"采样"的是我们在上一 tick 中驱动并从端已稳定的输入值，
//           与真实 Verilog 'flop 在 active 事件结束后取 NBA 前的值' 一致；
//         - 从端组合输出在 eval 内随输入结算，相当于 posedge 前的组合逻辑。
//     [2] settle eval   (clock=0) -- 无沿，状态不变，仅让组合逻辑结算；
//         之后 DUT 主端输出即为"当前拍 [t..t+1) 主端向从端呈现的值"。
//     [3] slave_tick() 在 settle 之后执行：
//         (a) 先用上一 tick 已提交的"从端寄存器状态"驱动组合输出
//             （供下一个 posedge 采样）；
//         (b) 再用本拍采样到的主端信号判定握手（AR/AW/W/B/R），
//             把结果"提交"进从端寄存器 -- 相当于从端触发器在该 posedge 的
//             NBA 更新，一拍之后才对外可见（rvalid/bvalid 晚一拍给出）。
//
//   因此本模型是"一拍响应、握手驱动"的从端：无 dwell 超时、无启发式退避，
//   复用与 RTL 相同的置位/保持(NBA)语义，避免同拍即回等非规范行为。
// ============================================================================
#include <cstdio>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <vector>
#include <string>
#include "verilated.h"
#include "verilated_fst_c.h"
#include "svdpi.h"
#include "Vysyx_22040750.h"

static bool finish = false;
static uint64_t sim_time = 0;

// ---- DPI-C stubs ---------------------------------------------------------
extern "C" void set_gpr_ptr(const svOpenArrayHandle) {}
extern "C" void set_diff_ptr(unsigned char) {}
extern "C" void set_mmio_ptr(unsigned char) {}
extern "C" void set_wb_pc_ptr(const svOpenArrayHandle) {}
extern "C" void set_wb_inst_ptr(const svOpenArrayHandle) {}
extern "C" void sim_end() { finish = true; }

// ---- AXI4 slave memory model --------------------------------------------
static uint8_t *low;    // [0x00000000, 0x10000000) SRAM region
static uint8_t *high;   // [0x2ff00000, 0x31000000) flash/code region
static uint8_t *pmem;   // [0x80000000, 0x88000000) 可缓存物理内存(PA3/仙剑段)

// ---- 从端寄存器（"触发器"，一拍一拍后提交并对外可见）--------------------
static bool  rd_serving = false;   // 当前正在向外回 R 数据（一拍后才给 rvalid）
static uint32_t rd_addr = 0;
static uint8_t  rd_size = 0;
static uint8_t  rd_beats = 1;      // 本突发总拍数 = arlen+1（1=单拍, 4=32B cacheline）
static uint8_t  rd_beat  = 0;      // 当前已回的第几拍(0..beats-1)
static bool  aw_hs = false;        // AW 已握手接受
static bool  wd_hs = false;        // W 全部拍已接收（最后一拍后置真）
static bool  wd_hs_d = false;      // wd_hs 的一拍延迟（NBA：接收后一拍才对外可查）
static uint8_t  wr_beats = 1;      // 本写突发总拍数 = awlen+1（1=单拍, 4=32B cacheline）
static uint8_t  wr_beat  = 0;      // 当前已接收的第几拍(0..beats-1)
static uint32_t wr_addr = 0;

struct txn {
  uint64_t t;
  char type;   // A=AR  R=R响应  W=AW  D=wdata  B=Bresp
  uint32_t addr;
  uint32_t data;
  uint8_t  size;
  uint8_t  strb;
};
static std::vector<txn> logtx;

static uint8_t &byte_at(uint32_t a) {
  if (a < 0x10000000) return low[a];
  if (a >= 0x2ff00000 && a < 0x31000000) return high[a - 0x2ff00000];
  if (a >= 0x80000000 && a < 0x88000000) return pmem[a - 0x80000000];
  return low[0];
}

static uint64_t read_aligned(uint32_t a) {
  uint32_t base = a & ~7u;
  uint64_t v = 0;
  for (int i = 0; i < 8; i++) v |= ((uint64_t)byte_at(base + i)) << (8 * i);
  return v;
}
static void write_strobed(uint32_t a, uint64_t d, uint8_t strb) {
  uint32_t base = a & ~7u;
  for (int i = 0; i < 8; i++)
    if (strb & (1 << i)) byte_at(base + i) = (d >> (8 * i)) & 0xff;
}

// (a) 用"上一拍已提交的从端寄存器状态"驱动组合输出（下个 posedge 采样）。
//     组合逻辑此时就绪，等价于 Verilog 中 comb 块在 active 事件内的结算。
static void slave_comb(Vysyx_22040750 *d) {
  d->io_master_arready = rd_serving ? 0 : 1;
  d->io_master_rvalid  = rd_serving ? 1 : 0;
  d->io_master_rlast   = rd_serving && (rd_beat == rd_beats - 1) ? 1 : 0;
  d->io_master_rdata   = rd_serving ? read_aligned(rd_addr + rd_beat * 8) : 0;
  d->io_master_rid     = 0;
  d->io_master_rresp   = 0;

  d->io_master_awready = aw_hs ? 0 : 1;
  d->io_master_wready  = (aw_hs && !wd_hs) ? 1 : 0;
  d->io_master_bvalid  = (aw_hs && wd_hs_d) ? 1 : 0;
  d->io_master_bid     = 0;
  d->io_master_bresp   = 0;
}

// (b) 用本拍主端呈现的信号判定握手并"提交"从端寄存器（模拟该拍 posedge 的 NBA）：
//     提交结果从下一个 tick 起驱动输出 —— 即一拍后才对外可见。
static void slave_commit(Vysyx_22040750 *d) {
  // ---- 读通道（支持 burst：arpack burst 拍数按 arlen+1）----
  if (rd_serving) {
    // R 数据在飞：本拍 posedge 若 rvalid&&rready 完成一拍
    if (d->io_master_rready) {
      logtx.push_back({sim_time, 'R',
                       rd_addr + rd_beat * 8,
                       (uint32_t)(read_aligned(rd_addr + rd_beat * 8) & 0xffffffff),
                       rd_size, 0});
      if (rd_beat == rd_beats - 1) {
        rd_serving = false;   // 最后一拍已回，退避
        rd_beat = 0;
      } else {
        rd_beat++;
      }
    }
  } else if (d->io_master_arvalid) {
    // AR 握手（arready 本拍为 1）：提交 -> 下一拍开始回 R
    rd_serving = true;
    rd_addr    = d->io_master_araddr;
    rd_size    = d->io_master_arsize;
    rd_beats   = d->io_master_arlen + 1;   // 单拍 arlen=0 => 1 beat；cacheline arlen=3 => 4 beat
    rd_beat    = 0;
    logtx.push_back({sim_time, 'A', rd_addr, 0, rd_size, d->io_master_arlen});
  }
  // ---- 写通道（支持 burst：wdata 按 awlen+1 拍接收，全收后才回 B）----
  if (!aw_hs && d->io_master_awvalid) {
    aw_hs = true;                 // AW 握手（awready 本拍为 1）
    wd_hs = false;
    wr_addr  = d->io_master_awaddr;
    wr_beats = d->io_master_awlen + 1;   // 单拍 awlen=0 => 1 beat；cacheline awlen=3 => 4 beat
    wr_beat  = 0;
    logtx.push_back({sim_time, 'W', wr_addr, 0, d->io_master_awsize, d->io_master_awlen});
  }
  if (aw_hs && !wd_hs && d->io_master_wvalid && d->io_master_wready) {
    write_strobed(wr_addr + wr_beat * 8, d->io_master_wdata, d->io_master_wstrb);
    logtx.push_back({sim_time, 'D', wr_addr + wr_beat * 8,
                     (uint32_t)d->io_master_wdata, 0, d->io_master_wstrb});
    if (wr_beat == wr_beats - 1) wd_hs = true;   // 最后一拍：全部接收，可回 B
    else wr_beat++;
  }
  if (aw_hs && wd_hs_d && d->io_master_bready) {
    // bvalid 上一拍已对外置 1，本拍 posedge 完成 B 握手后退避
    logtx.push_back({sim_time, 'B', wr_addr, 0, 0, 0});
    aw_hs = false;
    wd_hs = false;
    wd_hs_d = false;
  }
  wd_hs_d = wd_hs;   // 一拍传递：wdata 接收后下一拍才可给 bvalid
}

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s <img.bin> [out.fst]\n", argv[0]);
    return 1;
  }
  const char *dump = (argc > 2) ? argv[2] : nullptr;

  low  = (uint8_t*)calloc(0x10000000, 1);
  high = (uint8_t*)calloc(0x00220000, 1); // cover [0x2ff00000, 0x31000000)
  pmem = (uint8_t*)calloc(0x08000000, 1); // cover [0x80000000, 0x88000000)
  FILE *fp = fopen(argv[1], "rb");
  if (!fp) { fprintf(stderr, "cannot open %s\n", argv[1]); return 1; }
  fseek(fp, 0, SEEK_END); long sz = ftell(fp); fseek(fp, 0, SEEK_SET);
  if (sz > 0x00200000) { fprintf(stderr, "img too big %ld\n", sz); return 1; }
#ifdef NPC_PMEM_BOOT
  // 主存模式：映像直接装入可缓存区 0x80000000（PC 复位也到 0x80000000）
  fread(pmem, 1, sz, fp);
  fclose(fp);
  printf("PMEM-boot: img size=%ld loaded @0x80000000\n", sz);
#else
  // image loads at flash 0x30000000 -> high[0x30000000 - 0x2ff00000]
  fread(high + 0x00100000, 1, sz, fp);
  fclose(fp);
  printf("img size=%ld\n", sz);

  // boot word at 0x2ffffffc : jal x0, 0x30000000  (offset=4)
  const uint32_t boot = 0x0040006f; // verified vs assembler
  uint32_t baddr = 0x2ffffffc;
  high[baddr - 0x2ff00000 + 0] = boot & 0xff;
  high[baddr - 0x2ff00000 + 1] = (boot >> 8) & 0xff;
  high[baddr - 0x2ff00000 + 2] = (boot >> 16) & 0xff;
  high[baddr - 0x2ff00000 + 3] = (boot >> 24) & 0xff;
  printf("boot word @%08x = %08x\n", baddr, boot);
#endif

  Verilated::commandArgs(argc, argv);
  Vysyx_22040750 *dut = new Vysyx_22040750;

  Verilated::traceEverOn(true);
  VerilatedFstC *tfp = nullptr;
  if (dump) { tfp = new VerilatedFstC; dut->trace(tfp, 99); tfp->open(dump); }

  dut->reset = 1;
  dut->io_interrupt = 0;
  dut->clock = 0;
  dut->eval();
  slave_comb(dut);   // 让从端在首个 posedge 之前已给出初始组合输出

  bool failed = false;
  const uint64_t MAXT = dump ? 30000 : 400000;
  for (sim_time = 0; !finish && sim_time < MAXT; sim_time++) {
    if (sim_time > 40) dut->reset = 0;   // 同步复位：沿前撤销，posedge 采样为 0

    dut->clock = 1; dut->eval();          // posedge：DUT 采样上一 tick 驱动的从端输出
    dut->clock = 0; dut->eval();          // settle：主端输出 = 当前拍 [t..t+1) 值
    slave_comb(dut);                      // 用"当前从端寄存器态"驱动本拍从端输出
    slave_commit(dut);                    // 判定本拍握手并把结果提交进从端寄存器（下一拍生效）

    if (tfp) tfp->dump(sim_time * 2);
    if (Verilated::gotError()) failed = true;   // 记录断言失败但不中止，收集全部
  }
  printf("sim ended at t=%llu finish=%d\n", (unsigned long long)sim_time, finish);
  if (tfp) tfp->close();

  // ---- dump SRAM results
  puts("==== SRAM 0x0f000000 dump (u64) ====");
  for (int i = 0; i < 48; i++) {
    uint64_t v = 0;
    for (int b = 0; b < 8; b++) v |= ((uint64_t)low[0x0f000000 + i * 8 + b]) << (8 * b);
    printf("0x0f000000+%3d : 0x%016llx\n", i * 8, (unsigned long long)v);
  }
  puts("==== AXI txn log ===");
  for (auto &x : logtx)
    printf("t=%-8llu  %c  addr=0x%08x size=%u strb=0x%02x data=0x%08x\n",
           (unsigned long long)x.t, x.type, x.addr, x.size, x.strb, x.data);

  delete dut;
  free(low); free(high); free(pmem);
  printf("%s\n", failed ? "RESULT: FAIL" : "RESULT: PASS");
  return failed ? 1 : 0;
}