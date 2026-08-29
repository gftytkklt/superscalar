// ============================================================================
// Formal: dcache AXI 读通道状态机 (S1.5 解耦后)
//
// 目标：验证 dcache 对可缓存区(PSRAM)读请求的 AXI 语义：
//   [a1] ARVALID 保持到 ARREADY 握手（AXI 规范，对任意从端背压成立）
//   [a2] 从端返回 4 拍 burst 后，cache 最终回 O_cpu_rvalid（读完成）
// 从端模型（受控）：
//   - arready 自由（free input，测背压）
//   - rvalid 在 AR 握手后连续 4 拍，rlast 第 4 拍
// 驱动：复位后对 0x80000000 发一次读请求（tag 初始全 0 -> 必 miss -> RD_MISS）
// ============================================================================
module dcache_axi (
  input I_clk, I_rst
);
  reg [31:0] I_cpu_addr;
  reg [63:0] I_cpu_data;
  reg [7:0]  I_cpu_wmask, I_cpu_rmask;
  reg        I_cpu_rd_req, I_cpu_wr_req, I_cpu_fencei;
  wire       O_cpu_mem_ready, O_dcache_clean;
  reg  [255:0] I_way0_rdata, I_way1_rdata;
  wire [5:0]  O_sram_addr;
  wire [3:0]  O_sram_cen, O_sram_wen;
  wire [255:0] O_sram_wdata, O_sram_wmask;
  reg  [63:0] I_mem_rdata;
  wire        I_mem_arready;
  wire        I_mem_rvalid, I_mem_rlast;
  wire [31:0] O_mem_araddr;
  wire        O_mem_arvalid, O_mem_rready;
  wire [7:0]  O_mem_arlen;
  wire [2:0]  O_mem_arsize;
  wire [1:0]  O_mem_arburst;
  reg  I_mem_awready, I_mem_wready, I_mem_bvalid;
  wire [63:0] O_mem_wdata;
  wire [31:0] O_mem_awaddr;
  wire        O_mem_awvalid, O_mem_wvalid, O_mem_bready, O_mem_wlast;
  wire [7:0]  O_mem_awlen, O_mem_wstrb;
  wire [2:0]  O_mem_awsize;
  wire [1:0]  O_mem_awburst;
  wire [63:0] O_cpu_data;
  wire        O_cpu_rvalid, O_cpu_bvalid;

  ysyx_22040750_dcachectrl u (
    .I_clk(I_clk), .I_rst(I_rst),
    .I_cpu_addr(I_cpu_addr), .I_cpu_data(I_cpu_data),
    .I_cpu_wmask(I_cpu_wmask), .I_cpu_rmask(I_cpu_rmask),
    .I_cpu_rd_req(I_cpu_rd_req), .I_cpu_wr_req(I_cpu_wr_req),
    .O_cpu_mem_ready(O_cpu_mem_ready), .I_cpu_fencei(I_cpu_fencei),
    .O_dcache_clean(O_dcache_clean),
    .I_way0_rdata(I_way0_rdata), .I_way1_rdata(I_way1_rdata),
    .O_sram_addr(O_sram_addr), .O_sram_cen(O_sram_cen),
    .O_sram_wen(O_sram_wen), .O_sram_wdata(O_sram_wdata),
    .O_sram_wmask(O_sram_wmask),
    .I_mem_rdata(I_mem_rdata), .I_mem_arready(I_mem_arready),
    .I_mem_rvalid(I_mem_rvalid), .I_mem_rlast(I_mem_rlast),
    .O_mem_araddr(O_mem_araddr), .O_mem_arvalid(O_mem_arvalid),
    .O_mem_rready(O_mem_rready), .O_mem_arlen(O_mem_arlen),
    .O_mem_arsize(O_mem_arsize), .O_mem_arburst(O_mem_arburst),
    .I_mem_awready(I_mem_awready), .I_mem_wready(I_mem_wready),
    .I_mem_bvalid(I_mem_bvalid),
    .O_mem_wdata(O_mem_wdata), .O_mem_awaddr(O_mem_awaddr),
    .O_mem_awvalid(O_mem_awvalid), .O_mem_wvalid(O_mem_wvalid),
    .O_mem_bready(O_mem_bready), .O_mem_wlast(O_mem_wlast),
    .O_mem_awlen(O_mem_awlen), .O_mem_awsize(O_mem_awsize),
    .O_mem_awburst(O_mem_awburst), .O_mem_wstrb(O_mem_wstrb),
    .O_cpu_data(O_cpu_data), .O_cpu_rvalid(O_cpu_rvalid),
    .O_cpu_bvalid(O_cpu_bvalid)
  );

  // ---- 驱动: 复位后发一次可缓存区读请求 (0x80000000) ----
  reg [3:0] st;
  initial st = 4'd0;
  always @(posedge I_clk) if (st < 4'd9) st <= st + 4'd1;
  always @* begin
    I_cpu_rd_req = (st == 4'd1);
    I_cpu_wr_req = 1'b0;
    I_cpu_addr   = 32'h80000000;
    I_cpu_data   = 64'd0;
    I_cpu_wmask  = 8'd0;
    I_cpu_rmask  = 8'hff;
    I_cpu_fencei = 1'b0;
    I_way0_rdata = 256'd0;
    I_way1_rdata = 256'd0;
    I_mem_awready = 1'b0;
    I_mem_wready  = 1'b0;
    I_mem_bvalid  = 1'b0;
  end

  // ---- 受控从端: arready 自由; AR 握手后连续 4 拍返回 rdata, rlast 第 4 拍 ----
  reg [2:0] rstate;
  always @(posedge I_clk) begin
    if (I_rst) rstate <= 3'd0;
    else case (rstate)
      3'd0: if (O_mem_arvalid && I_mem_arready) rstate <= 3'd1;
      3'd1: if (O_mem_rready)                   rstate <= 3'd2;
      3'd2: if (O_mem_rready)                   rstate <= 3'd3;
      3'd3: if (O_mem_rready)                   rstate <= 3'd4;
      3'd4: if (O_mem_rready)                   rstate <= 3'd0;
      default: rstate <= 3'd0;
    endcase
  end
  assign I_mem_rvalid = (rstate != 3'd0);
  assign I_mem_rlast  = (rstate == 3'd4);
  // rdata: 每拍值 = rstate 对应 (仅 rvalid 时被 cache 采样)
  reg [63:0] rdata_out;
  always @(posedge I_clk) begin
    if (I_rst) rdata_out <= 64'd0;
    else case (rstate)
      3'd0: rdata_out <= 64'h0101010101010101;
      3'd1: rdata_out <= 64'h0202020202020202;
      3'd2: rdata_out <= 64'h0303030303030303;
      3'd3: rdata_out <= 64'h0404040404040404;
      3'd4: rdata_out <= 64'h0505050505050505;
      default: rdata_out <= 64'd0;
    endcase
  end
  assign I_mem_rdata = rdata_out;

  // ---- 断言 (process 风格, yosys -formal 兼容) ----
  // [a1] ARVALID 保持到握手: 若上拍 arvalid 且未握手(arready=0), 本拍 arvalid 必须保持
  reg arvalid_d, arready_d;
  always @(posedge I_clk) begin
    arvalid_d <= O_mem_arvalid;
    arready_d <= I_mem_arready;
  end
  always @(posedge I_clk) begin
    if (!I_rst && arvalid_d && !arready_d && !O_mem_arvalid)
      assert (0);   // AXI: ARVALID dropped before handshake
  end

  // [a2] burst 完成后 cache 应在宽限期内回 O_cpu_rvalid（读完成）
  reg [2:0] gcnt;
  always @(posedge I_clk) begin
    if (I_rst) gcnt <= 3'd0;
    else if (I_mem_rvalid && I_mem_rlast) gcnt <= 3'd4;
    else if (gcnt != 3'd0 && O_cpu_rvalid) gcnt <= 3'd0;
    else if (gcnt != 3'd0) gcnt <= gcnt - 3'd1;
  end
  always @(posedge I_clk) begin
    if (!I_rst && gcnt == 3'd1 && !O_cpu_rvalid)
      assert (0);   // burst 结束 4 拍内必须回读数据
  end

  // [a3] 可缓存区 miss 读必须是 32B burst (arlen=3)
  always @(posedge I_clk) begin
    if (!I_rst && O_mem_arvalid && I_mem_arready)
      if (O_mem_arlen != 8'd3)
        assert (0);
  end

  // cover: 读路径可达
  always @(posedge I_clk) begin
    if (!I_rst && O_cpu_rvalid) cover (1'b1);
  end
endmodule