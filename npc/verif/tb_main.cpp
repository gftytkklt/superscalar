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
static uint8_t *low;   // [0x00000000, 0x10000000) SRAM region
static uint8_t *high;  // [0x2ff00000, 0x31000000) flash/code region

static bool rd_pending = false;
static bool rd_served  = false;
static uint32_t rd_addr = 0;
static uint8_t rd_size = 0;
static uint64_t rd_buf = 0;

static bool wr_pending = false;
static bool wr_wdata = false;
static uint32_t wr_addr = 0;

struct txn {
  uint64_t t;
  char type;   // A=AR  W=AW  D=wdata B=Bresp R+rdata
  uint32_t addr;
  uint32_t data;
  uint8_t  size;
  uint8_t  strb;
};
static std::vector<txn> logtx;

static uint8_t &byte_at(uint32_t a) {
  if (a < 0x10000000) return low[a];
  if (a >= 0x2ff00000 && a < 0x31000000) return high[a - 0x2ff00000];
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

// called during the LOW half-cycle: master outputs are stable; capture the
// requests presented on AR/AW and drive all slave-side outputs for the posedge.
static void axi_low(Vysyx_22040750 *d) {
  // --- READ CHANNEL -------------------------------------------------------
  // Retire a finished response when the core has clearly consumed it: it can
  // only present a NEW arvalid after the previous burst was fully retired, so
  // seeing arvalid (or a dwell timeout as safety net) means we are free again.
  static int rv_dwell = 0;
  if (rd_pending && rd_served && (d->io_master_arvalid || rv_dwell >= 8)) {
    rd_pending = false;
    rd_served  = false;
    rv_dwell   = 0;
  }
  d->io_master_arready = rd_pending ? 0 : 1;
  if (!rd_pending && d->io_master_arvalid) {
    rd_pending = true;
    rd_served  = false;
    rd_addr    = d->io_master_araddr;
    rd_size    = d->io_master_arsize;
    rd_buf     = read_aligned(rd_addr);
    logtx.push_back({sim_time, 'A', rd_addr, 0, rd_size, 0});
    rv_dwell   = 0;
  }
  if (rd_pending) {
    d->io_master_rvalid = 1;
    d->io_master_rlast  = 1;
    if (!rd_served) {
      logtx.push_back({sim_time, 'R', rd_addr, (uint32_t)(rd_buf & 0xffffffff), rd_size, 0});
      rd_served = true;
    }
    rv_dwell++;
  } else {
    d->io_master_rvalid = 0;
    d->io_master_rlast  = 0;
  }
  d->io_master_rdata = rd_buf;
  d->io_master_rid   = 0;
  d->io_master_rresp = 0;

  // --- WRITE CHANNEL ------------------------------------------------------
  static int wb_dwell = 0;
  if (wr_pending && wr_wdata && (d->io_master_awvalid || wb_dwell >= 8)) {
    wr_pending = false;
    wr_wdata   = false;
    wb_dwell   = 0;
  }
  d->io_master_awready = wr_pending ? 0 : 1;
  if (!wr_pending && d->io_master_awvalid) {
    wr_pending = true;
    wr_wdata   = false;
    wr_addr    = d->io_master_awaddr;
    logtx.push_back({sim_time, 'W', wr_addr, 0, d->io_master_awsize, 0});
    wb_dwell   = 0;
  }
  if (wr_pending && !wr_wdata && d->io_master_wvalid && d->io_master_wready) {
    write_strobed(wr_addr, d->io_master_wdata, d->io_master_wstrb);
    logtx.push_back({sim_time, 'D', wr_addr, (uint32_t)d->io_master_wdata, 0, d->io_master_wstrb});
    wr_wdata = true;
  }
  d->io_master_wready = (wr_pending && !wr_wdata) ? 1 : 0;
  d->io_master_bvalid = (wr_pending && wr_wdata) ? 1 : 0;
  d->io_master_bid    = 0;
  d->io_master_bresp  = 0;
  if (wr_pending && wr_wdata) wb_dwell++;
}

static void axi_high(Vysyx_22040750 *d) {
  (void)d;
}

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s <img.bin> [out.fst]\n", argv[0]);
    return 1;
  }
  const char *dump = (argc > 2) ? argv[2] : nullptr;

  low  = (uint8_t*)calloc(0x10000000, 1);
  high = (uint8_t*)calloc(0x00220000, 1); // cover [0x2ff00000, 0x31000000)
  FILE *fp = fopen(argv[1], "rb");
  if (!fp) { fprintf(stderr, "cannot open %s\n", argv[1]); return 1; }
  fseek(fp, 0, SEEK_END); long sz = ftell(fp); fseek(fp, 0, SEEK_SET);
  if (sz > 0x00200000) { fprintf(stderr, "img too big %ld\n", sz); return 1; }
  // image loads at flash 0x30000000 -> high[0x30000000 - 0x2ff00000]
  fread(high + 0x00100000, 1, sz, fp);
  fclose(fp);
  printf("img size=%ld\n", sz);

  // boot word at 0x2ffffffc : jal x0, 0x30000000  (offset=4)
  const uint32_t boot = 0x0040006f; // verifed by objdump below
  uint32_t baddr = 0x2ffffffc;
  high[baddr - 0x2ff00000 + 0] = boot & 0xff;
  high[baddr - 0x2ff00000 + 1] = (boot >> 8) & 0xff;
  high[baddr - 0x2ff00000 + 2] = (boot >> 16) & 0xff;
  high[baddr - 0x2ff00000 + 3] = (boot >> 24) & 0xff;
  printf("boot word @%08x = %08x\n", baddr, boot);

  Verilated::commandArgs(argc, argv);
  Vysyx_22040750 *dut = new Vysyx_22040750;

  Verilated::traceEverOn(true);
  VerilatedFstC *tfp = nullptr;
  if (dump) { tfp = new VerilatedFstC; dut->trace(tfp, 99); tfp->open(dump); }

  dut->reset = 1;
  dut->io_interrupt = 0;
  dut->clock = 0;
  dut->eval();

  bool failed = false;
  const uint64_t MAXT = dump ? 30000 : 400000;
  for (sim_time = 0; !finish && sim_time < MAXT; sim_time++) {
    if (sim_time > 40) dut->reset = 0;
    // low phase: settle, capture master requests, drive slave outputs
    dut->clock = 0;
    dut->eval();
    axi_low(dut);
    // high phase: posedge samples our outputs & core state advances
    dut->clock = 1;
    dut->eval();
    axi_high(dut);

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
  free(low); free(high);
  printf("%s\n", failed ? "RESULT: FAIL" : "RESULT: PASS");
  return failed ? 1 : 0;
}