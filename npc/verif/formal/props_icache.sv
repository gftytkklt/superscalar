// ============================================================================
// Formal: icache 透明性（REF vs DUT）—— 讲义 B3「通过形式化验证测试icache」
//
// ⚠️ 尝试记录（非活跃：未配 icache.sby，measure 结果见 records/STAGE_B3_CACHE_PERF.md §3）。
//   实测：参数化最小实例(CACHE_SIZE=128B) + 下面这套 REF/DUT，z3 BMC 在 depth=6 即不可判定
//   （256bit 缓存行 + 128 项查找表被位爆破成巨大 SAT，base case 无法在 60s 内求出）；
//   控制层降级(datas 固定 0)同样不可判定；apt 老 boolector 与 yosys-smtbmc 协议不兼容。
//   原因与工程内已移除的 `dcache.sby` 相同：含大查找表 / 宽数据行的 cache，BMC 状态空间爆炸。
//   数据正确性改由仿真断言(axi_protocol_check/cache_bypass_check) + 定向微测试 + SoC difftest 覆盖。
//
// 设计（讲义 REF = 直接访存 / DUT = 经 icache 的等价性）：
//   REF  = 一个最简单的访存系统：把 32 位对齐的请求地址译成一条指令；
//   DUT  = ysyx_22040750_icachectrl（极小参数化实例 CACHE_SIZE=128B, BLOCK_SIZE=32B,
//          GROUP_NUM=2 -> 8 行, index=1bit）。
//   透明性属性：O_cpu_rvalid 时 O_cpu_inst 必须 == 直接从存储器译出的指令。
//   存储器建模为地址的**纯组合函数** mem(addr)（省去巨大 mem 状态）；AXI burst slave 返回
//   32B 行(4 拍 64-bit, 小端)；SRAM 数据阵列作为受控从端(和 sram_behav 同语义)。
// ============================================================================
module icache_transparency (
  input I_clk
);
  // ---- 参数化小实例（最小可判定规模）----
  // CACHE_SIZE=128B, BLOCK_SIZE=32B, GROUP_NUM=2 -> BLOCK_NUM=4, index=1bit, 每路 2 行
  localparam BLOCK_SIZE = 32, CACHE_SIZE = 128, GROUP_NUM = 2;
  localparam SD = CACHE_SIZE / BLOCK_SIZE / GROUP_NUM; // 每 way 行数 = 2
  localparam OFF_L = 5;                                 // $clog2(BLOCK_SIZE)

  // 可缓存窗口：PSRAM [BASE, BASE+256)。cacheable 区 = icache 的 mmio_flag 取反。
  // 窗口 256B = 8 个 32B 块 > cache 的 4 行 -> 必然发生替换/冲突缺失。
  localparam [31:0] BASE = 32'h80000000;

  // ---------------- DUT 端口 ----------------
  reg  [31:0] I_cpu_addr;
  reg         I_cpu_rd_req;
  wire        O_cpu_rd_ready;
  reg         I_cpu_fencei;
  reg         I_dcache_clean;
  wire [255:0] I_way0_rdata, I_way1_rdata;   // 由本 tb 的 SRAM 模型驱动
  wire [5:0]   O_sram_addr;
  wire [3:0]   O_sram_cen, O_sram_wen;       // cen/wen 低电平有效（同 sram_behav）
  wire [255:0] O_sram_wdata, O_sram_wmask;
  reg  [63:0]  I_mem_rdata;
  wire         I_mem_arready;
  wire         I_mem_rvalid, I_mem_rlast;
  wire [31:0]  O_mem_araddr;
  wire         O_mem_arvalid, O_mem_rready;
  wire [7:0]   O_mem_arlen;
  wire [2:0]   O_mem_arsize;
  wire [1:0]   O_mem_arburst;
  wire [31:0]  O_cpu_inst;
  wire         O_cpu_rvalid;

  ysyx_22040750_icachectrl #(
    .BLOCK_SIZE (BLOCK_SIZE),
    .CACHE_SIZE (CACHE_SIZE),
    .GROUP_NUM  (GROUP_NUM)
  ) dut (
    .I_clk(I_clk), .I_rst(I_rst),
    .I_cpu_addr(I_cpu_addr), .I_cpu_rd_req(I_cpu_rd_req),
    .O_cpu_rd_ready(O_cpu_rd_ready),
    .I_cpu_fencei(I_cpu_fencei), .I_dcache_clean(I_dcache_clean),
    .I_way0_rdata(I_way0_rdata), .I_way1_rdata(I_way1_rdata),
    .O_sram_addr(O_sram_addr), .O_sram_cen(O_sram_cen),
    .O_sram_wen(O_sram_wen), .O_sram_wdata(O_sram_wdata),
    .O_sram_wmask(O_sram_wmask),
    .I_mem_rdata(I_mem_rdata), .I_mem_arready(I_mem_arready),
    .I_mem_rvalid(I_mem_rvalid), .I_mem_rlast(I_mem_rlast),
    .O_mem_araddr(O_mem_araddr), .O_mem_arvalid(O_mem_arvalid),
    .O_mem_rready(O_mem_rready), .O_mem_arlen(O_mem_arlen),
    .O_mem_arsize(O_mem_arsize), .O_mem_arburst(O_mem_arburst),
    .O_cpu_inst(O_cpu_inst), .O_cpu_rvalid(O_cpu_rvalid)
  );

  // ---------------- 复位与自由输入 ----------------
  reg [3:0] rstst;
  wire I_rst;
  initial rstst = 4'd0;
  always @(posedge I_clk) if (rstst < 4'd15) rstst <= rstst + 4'd1;
  assign I_rst = (rstst < 4'd2);           // 复位 2 拍

  assign I_cpu_rd_req = ~I_rst;            // 持续请求（cache 按 rd_ready 串行处理）
  assign I_cpu_fencei  = 1'b0;             // fence.i 单独属性覆盖；此处关闭保持聚焦
  assign I_dcache_clean = 1'b1;            // 无真实 dcache：视为已干净
  assign I_mem_arready  = 1'b1;            // 主透明性证明：无背压，简化状态

  // ---------------- 存储器：纯组合函数 mem(addr) ----------------
  // 仅在 [BASE, BASE+256) 内有意义（已由 assume 保证）。用于 REF 与 burst slave。
  function automatic [31:0] mw(input [31:0] wordaddr);
    mw = 32'hA5A5A5A5 ^ wordaddr[10:0];
  endfunction

  // ---------------- 受控 burst 从端 ----------------
  // 收到 AR(arlen=3) -> 连续 4 拍 rvalid, 每拍 {mem(base+8i+4), mem(base+8i)}
  reg [2:0] bst; reg [31:0] line_base;
  always @(posedge I_clk) begin
    if (I_rst) begin bst <= 3'd0; line_base <= 32'd0; end
    else case (bst)
      3'd0: if (O_mem_arvalid && I_mem_arready) begin bst <= 3'd1; line_base <= O_mem_araddr; end
      3'd1, 3'd2, 3'd3, 3'd4: if (O_mem_rready) bst <= bst + 3'd1;
      3'd5: bst <= 3'd0;
      default: bst <= 3'd0;
    endcase
  end
  assign I_mem_rvalid = (bst >= 3'd1) && (bst <= 3'd4);
  assign I_mem_rlast  = (bst == 3'd4);
  assign I_mem_rdata  =
    (bst == 3'd1) ? {mw(line_base+4),    mw(line_base+0)}   :
    (bst == 3'd2) ? {mw(line_base+12),   mw(line_base+8)}   :
    (bst == 3'd3) ? {mw(line_base+20),   mw(line_base+16)}  :
    (bst == 3'd4) ? {mw(line_base+28),   mw(line_base+24)}  : 64'd0;

  // ---------------- ICache 的 SRAM 存储阵列模型 ----------------
  // 4 块 128bit SRAM，地址 O_sram_addr（index）共享；cen 低有效；wen=0 写 / wen=1 读。
  // 读结果寄存一拍（同 sram_behav），供 icachectrl 下一个周期（RD_HIT）采样。
  reg [127:0] s0[0:SD-1], s1[0:SD-1], s2[0:SD-1], s3[0:SD-1];
  reg [127:0] Q0, Q1, Q2, Q3;
  integer jj;
  initial for (jj = 0; jj < SD; jj = jj + 1) begin s0[jj] = 128'd0; s1[jj] = 128'd0; s2[jj] = 128'd0; s3[jj] = 128'd0; end
  always @(posedge I_clk) begin
    if (I_rst) begin Q0 <= 128'd0; Q1 <= 128'd0; Q2 <= 128'd0; Q3 <= 128'd0; end
    else begin
      if (!O_sram_cen[0]) begin if (!O_sram_wen[0]) s0[O_sram_addr] <= O_sram_wdata[127:0]; else Q0 <= s0[O_sram_addr]; end
      if (!O_sram_cen[1]) begin if (!O_sram_wen[1]) s1[O_sram_addr] <= O_sram_wdata[255:128]; else Q1 <= s1[O_sram_addr]; end
      if (!O_sram_cen[2]) begin if (!O_sram_wen[2]) s2[O_sram_addr] <= O_sram_wdata[127:0]; else Q2 <= s2[O_sram_addr]; end
      if (!O_sram_cen[3]) begin if (!O_sram_wen[3]) s3[O_sram_addr] <= O_sram_wdata[255:128]; else Q3 <= s3[O_sram_addr]; end
    end
  end
  assign I_way0_rdata = {Q1, Q0};
  assign I_way1_rdata = {Q3, Q2};

  // ---------------- 被服务地址队列（1 深，icache 单请求） ----------------
  reg qv; reg [31:0] qa;
  wire pc_handshake = I_cpu_rd_req && O_cpu_rd_ready;
  always @(posedge I_clk) begin
    if (I_rst) {qv, qa} <= 0;
    else begin
      if (O_cpu_rvalid) begin
        if (pc_handshake) qa <= I_cpu_addr;   // 消费旧 + 入队新
        else qv <= 0;
      end else if (pc_handshake) begin
        qv <= 1; qa <= I_cpu_addr;
      end
    end
  end

  // ---------------- 假设 ----------------
  always @* begin
    assume (I_cpu_addr >= BASE);
    assume (I_cpu_addr < BASE + 32'h100);
    assume (I_cpu_addr[1:0] == 2'b00);        // 字对齐
  end

  // ---------------- 断言 ----------------
  // [t1] 透明性：返回的指令 == 直接从存储器译出的指令
  always @* begin
    if (O_cpu_rvalid)
      assert (O_cpu_inst === mw(qa));
  end

  // [t2] cacheable 缺失读 = 32B burst；MMIO = 单拍（本 tb 全为 cacheable，故 arlen=3）
  always @(posedge I_clk) begin
    if (!I_rst && O_mem_arvalid && I_mem_arready) begin
      assert (O_mem_arlen == 8'd3);
      assert (O_mem_arsize == 3'd3);
    end
  end

  // [t3] ARVALID 保持到握手（AXI）
  reg arvalid_d, arready_d;
  always @(posedge I_clk) begin arvalid_d <= O_mem_arvalid; arready_d <= I_mem_arready; end
  always @(posedge I_clk) begin
    if (!I_rst && arvalid_d && !arready_d && !O_mem_arvalid)
      assert (0);
  end

  // cover：读路径可达
  always @(posedge I_clk) begin
    if (!I_rst && O_cpu_rvalid) cover (1'b1);
  end
endmodule
