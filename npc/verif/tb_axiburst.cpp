// ============================================================================
// Standalone directed testbench for ysyx_22040750_axiburst2xxx (S1a: 读路径).
//
// Mock slave 行为镜像 SoC AXI4ToAPB 桥:
//   - 读: AR 握手后下一拍 rvalid 单拍返回, rdata=Fill(2,prdata), rlast=1。
//   - 写: (S1b 用例) 此处从端不支持写。
//
// 读用例:
//   T1  burst 读 cacheline (arlen=3,size=3) -> 4 x 64-bit R beats
//   T3  MMIO 8B 读 (arlen=0,size=3)          -> 1 x 64-bit R beat  {hi,lo}
//   T5  MMIO 4B 读 (arlen=0,size=2)          -> 1 x 64-bit R beat  Fill(2)
// ============================================================================
#include <cstdio>
#include <cstdint>
#include <cstring>
#include "verilated.h"
#include "Vysyx_22040750_axiburst2xxx.h"

static uint8_t mem[0x100000];

// ---- mock slave state (单拍读 + 单拍写) ----
static bool rd_serving = false;
static uint32_t rd_addr;
static bool wr_serving = false;   // B pending

static void slave_comb(Vysyx_22040750_axiburst2xxx *d) {
  d->I_s_arready = rd_serving ? 0 : 1;
  d->I_s_rvalid  = rd_serving ? 1 : 0;
  d->I_s_rlast   = rd_serving ? 1 : 0;
  if (rd_serving) {
    uint32_t idx = rd_addr - 0x80000000;   // mem 覆盖 [0x80000000, +1MB)
    uint32_t w = (uint32_t)mem[idx] | ((uint32_t)mem[idx+1]<<8) |
                 ((uint32_t)mem[idx+2]<<16) | ((uint32_t)mem[idx+3]<<24);
    d->I_s_rdata   = ((uint64_t)w << 32) | w;   // Fill(2, prdata)
  } else {
    d->I_s_rdata = 0;
  }
  d->I_s_awready = wr_serving ? 0 : 1;
  d->I_s_wready  = wr_serving ? 0 : 1;
  d->I_s_bvalid  = wr_serving ? 1 : 0;
}

static void slave_commit(Vysyx_22040750_axiburst2xxx *d) {
  if (rd_serving) {
    if (d->O_s_rready) rd_serving = false;
  } else if (d->O_s_arvalid && d->I_s_arready) {
    rd_serving = true;
    rd_addr = d->O_s_araddr;
  }
  if (wr_serving) {
    if (d->O_s_bready) wr_serving = false;
  } else if (d->O_s_awvalid && d->O_s_wvalid && d->I_s_awready && d->I_s_wready) {
    wr_serving = true;
    uint32_t a = d->O_s_awaddr - 0x80000000;
    // mirror AXI4ToAPB: pwdata/pstrb from half selected by addr[2]
    uint32_t pwdata = (d->O_s_awaddr & 4) ? (uint32_t)(d->O_s_wdata >> 32) : (uint32_t)d->O_s_wdata;
    uint8_t  pstrb  = (d->O_s_awaddr & 4) ? (uint8_t)(d->O_s_wstrb >> 4) : (uint8_t)d->O_s_wstrb;
    for (int i = 0; i < 4; i++)
      if (pstrb & (1 << i)) mem[a + i] = (pwdata >> (8 * i)) & 0xff;
  }
}

static void step(Vysyx_22040750_axiburst2xxx *d, uint64_t &t) {
  d->I_clk = 1; d->eval();
  d->I_clk = 0; d->eval();
  slave_comb(d);
  slave_commit(d);
  t++;
}

static int failures = 0;
static void CHECK(bool ok, const char *msg, uint64_t t) {
  if (!ok) { failures++; printf("  [FAIL] t=%llu %s\n", (unsigned long long)t, msg); }
}

static void init_mem(uint32_t base, const uint8_t *data, int n) {
  memcpy(mem + base, data, n);
}

// 发起一笔读, 收集返回的 64-bit beats; 返回完成与否。
// 主端请求保持到 arready（同 tb_main.cpp 的"请求保持到 ready"模型）：
// 在 step 前观察 arready（上一拍 settle 后的组合值），判定本轮 posedge 是否握手。
static bool do_read(Vysyx_22040750_axiburst2xxx *d, uint64_t &t,
                    uint32_t addr, uint8_t len, uint8_t size,
                    uint64_t *out, int *nbeats) {
  int nb = 0;
  bool ar_done = false;
  for (int cyc = 0; cyc < 1000; cyc++) {
    d->I_m_araddr = addr; d->I_m_arlen = len; d->I_m_arsize = size; d->I_m_arburst = (len?1:0);
    d->I_m_arvalid = ar_done ? 0 : 1;
    d->I_m_rready = 1;
    d->I_m_awvalid = 0; d->I_m_wvalid = 0; d->I_m_wdata = 0; d->I_m_wstrb = 0; d->I_m_wlast = 0;
    d->I_m_bready = 1;
    if (!ar_done && d->I_m_arvalid && d->O_m_arready) ar_done = true;
    step(d, t);
    if (ar_done && d->O_m_rvalid && d->I_m_rready) {
      out[nb++] = d->O_m_rdata;
      if (d->O_m_rlast) { *nbeats = nb; return true; }
      if (nb >= 16) return false;
    }
  }
  return false;
}

// 发起一笔写 (AW + W beats), 直到收到 bvalid; 返回完成与否。
static bool do_write(Vysyx_22040750_axiburst2xxx *d, uint64_t &t,
                     uint32_t addr, uint8_t len, uint8_t size,
                     const uint64_t *wd, const uint8_t *wstrb) {
  int beats = len + 1;
  int wb = 0;
  bool aw_done = false, bdone = false;
  for (int cyc = 0; cyc < 2000; cyc++) {
    d->I_m_awaddr = addr; d->I_m_awlen = len; d->I_m_awsize = size; d->I_m_awburst = (len?1:0);
    d->I_m_awvalid = aw_done ? 0 : 1;
    if (aw_done && wb < beats) {
      d->I_m_wvalid = 1;
      d->I_m_wdata = wd[wb];
      d->I_m_wstrb = wstrb[wb];
      d->I_m_wlast  = (wb == beats - 1);
    } else {
      d->I_m_wvalid = 0; d->I_m_wdata = 0; d->I_m_wstrb = 0; d->I_m_wlast = 0;
    }
    d->I_m_arvalid = 0; d->I_m_rready = 1;
    d->I_m_bready = 1;
    if (!aw_done && d->I_m_awvalid && d->O_m_awready) aw_done = true;
    if (aw_done && wb < beats && d->I_m_wvalid && d->O_m_wready) wb++;
    step(d, t);
    if (d->O_m_bvalid && d->I_m_bready) { bdone = true; }
    if (bdone) return true;
  }
  return false;
}

int main(int argc, char **argv) {
  Verilated::commandArgs(argc, argv);
  Vysyx_22040750_axiburst2xxx *d = new Vysyx_22040750_axiburst2xxx;
  uint64_t t = 0;

  d->I_rst = 1; d->I_clk = 0; d->eval();
  for (int i = 0; i < 5; i++) step(d, t);
  d->I_rst = 0;
  for (int i = 0; i < 2; i++) step(d, t);

  // ================= T1: read cacheline burst =================
  {
    uint8_t data[32];
    for (int i = 0; i < 32; i++) data[i] = (uint8_t)(0xA0 + i);
    init_mem(0x20, data, 32);
    uint64_t out[8]; int nb = 0;
    bool ok = do_read(d, t, 0x80000020, 3, 3, out, &nb);
    CHECK(ok, "T1 read burst completes", t);
    CHECK(nb == 4, "T1 returns 4 beats", t);
    uint64_t expect[4];
    for (int b = 0; b < 4; b++) {
      expect[b] = 0;
      for (int i = 0; i < 8; i++) expect[b] |= ((uint64_t)data[b*8+i]) << (8*i);
    }
    for (int b = 0; b < 4; b++) {
      char msg[64]; snprintf(msg, sizeof msg, "T1 beat%d data", b);
      CHECK(out[b] == expect[b], msg, t);
    }
  }

  // ================= T3: read MMIO 8B =================
  {
    uint8_t data[8] = {0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88};
    init_mem(0x60, data, 8);
    uint64_t out[8]; int nb = 0;
    bool ok = do_read(d, t, 0x80000060, 0, 3, out, &nb);
    CHECK(ok, "T3 read 8B completes", t);
    CHECK(nb == 1, "T3 returns 1 beat", t);
    CHECK(out[0] == 0x8877665544332211ULL, "T3 8B data", t);
  }

  // ================= T5: read MMIO 4B =================
  {
    uint8_t data[8] = {0xde,0xad,0xbe,0xef, 0,0,0,0};
    init_mem(0x80, data, 8);
    uint64_t out[8]; int nb = 0;
    bool ok = do_read(d, t, 0x80000080, 0, 2, out, &nb);
    CHECK(ok, "T5 read 4B completes", t);
    CHECK(nb == 1, "T5 returns 1 beat", t);
    CHECK(out[0] == 0xefbeaddeefbeaddeULL, "T5 4B Fill(2) data", t);
  }

  // ================= T2: write cacheline burst =================
  {
    uint64_t wd[4]; uint8_t ws[4];
    for (int b = 0; b < 4; b++) {
      wd[b] = 0; ws[b] = 0xff;
      for (int i = 0; i < 8; i++) wd[b] |= ((uint64_t)(0x40 + b*8 + i)) << (8*i);
    }
    memset(mem + 0x40, 0, 32);
    bool ok = do_write(d, t, 0x80000040, 3, 3, wd, ws);
    CHECK(ok, "T2 write burst completes", t);
    for (int i = 0; i < 32; i++) {
      char msg[64]; snprintf(msg, sizeof msg, "T2 mem[%d]", i);
      CHECK(mem[0x40 + i] == (uint8_t)(0x40 + i), msg, t);
    }
  }

  // ================= T4: write MMIO 8B =================
  {
    uint64_t wd[1] = {0x8877665544332211ULL}; uint8_t ws[1] = {0xff};
    memset(mem + 0x70, 0, 8);
    bool ok = do_write(d, t, 0x80000070, 0, 3, wd, ws);
    CHECK(ok, "T4 write 8B completes", t);
    uint8_t exp[8] = {0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88};
    for (int i = 0; i < 8; i++) {
      char msg[64]; snprintf(msg, sizeof msg, "T4 mem[%d]", i);
      CHECK(mem[0x70+i] == exp[i], msg, t);
    }
  }

  // ================= T6: write MMIO 4B @addr+4 (high half) =================
  {
    uint64_t wd[1] = {0x1122334411223344ULL}; uint8_t ws[1] = {0xf0};
    memset(mem + 0x90, 0, 8);
    bool ok = do_write(d, t, 0x80000094, 0, 2, wd, ws);
    CHECK(ok, "T6 write 4B@+4 completes", t);
    uint8_t exp[4] = {0x44,0x33,0x22,0x11};
    for (int i = 0; i < 4; i++) {
      char msg[64]; snprintf(msg, sizeof msg, "T6 mem[%d]", i);
      CHECK(mem[0x94+i] == exp[i], msg, t);
    }
    CHECK(mem[0x90]==0 && mem[0x91]==0 && mem[0x92]==0 && mem[0x93]==0, "T6 low half untouched", t);
  }

  // ================= T7: write MMIO 2B (strb=0x03, low half) =================
  {
    uint64_t wd[1] = {0x0000abcd0000abcdULL}; uint8_t ws[1] = {0x03};
    memset(mem + 0xa0, 0, 8);
    bool ok = do_write(d, t, 0x800000a0, 0, 1, wd, ws);
    CHECK(ok, "T7 write 2B completes", t);
    CHECK(mem[0xa0]==0xcd && mem[0xa1]==0xab, "T7 2B data", t);
    CHECK(mem[0xa2]==0 && mem[0xa3]==0, "T7 2B mask respected", t);
  }

  d->final();
  delete d;

  printf("RESULT: %s (%d failures)\n", failures ? "FAIL" : "PASS", failures);
  return failures ? 1 : 0;
}