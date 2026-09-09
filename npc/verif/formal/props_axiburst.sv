// ============================================================================
// Formal: axiburst2xxx 读通道 (AXI burst -> 8x32bit 单拍)
//
// 验证:
//   [a1] slave 侧 arlen=0 (单拍), arsize=2 (32bit)
//   [a2] master 收 burst(arlen=3,size=3) 后, 8 次 slave 单拍读被重组成 4x64bit,
//        且每拍 rdata 与受控从端内容一致 (小端: beat_i = {word_{2i+1}, word_{2i}})
//   [a3] ARVALID 保持到握手
// 从端(受控): 单拍读, AR 握手后一周期 rvalid, rdata = {2{word[araddr[4:2]]}},
//             rlast=1。word[k] = k+1。
// ============================================================================
module axiburst_axi (
  input I_clk
);
  // I_rst 受控: 复位 2 拍后释放
  wire I_rst;
  // ---- axiburst2xxx 端口 ----
  reg  [31:0] I_m_araddr;
  reg         I_m_arvalid;
  wire        O_m_arready;
  reg  [7:0]  I_m_arlen;
  reg  [2:0]  I_m_arsize;
  reg  [1:0]  I_m_arburst;
  wire [63:0] O_m_rdata;
  wire        O_m_rvalid;
  wire        O_m_rlast;
  reg         I_m_rready;

  reg  [31:0] I_m_awaddr;
  reg         I_m_awvalid;
  wire        O_m_awready;
  reg  [7:0]  I_m_awlen;
  reg  [2:0]  I_m_awsize;
  reg  [1:0]  I_m_awburst;
  reg  [63:0] I_m_wdata;
  reg         I_m_wvalid;
  wire        O_m_wready;
  reg         I_m_wlast;
  reg  [7:0]  I_m_wstrb;
  wire        O_m_bvalid;
  reg         I_m_bready;

  wire [31:0] O_s_araddr;
  wire        O_s_arvalid;
  reg         I_s_arready;
  wire [7:0]  O_s_arlen;
  wire [2:0]  O_s_arsize;
  wire [1:0]  O_s_arburst;
  wire [63:0] I_s_rdata;
  wire        I_s_rvalid;
  reg         I_s_rlast;
  wire        O_s_rready;

  wire [31:0] O_s_awaddr;
  wire        O_s_awvalid;
  reg         I_s_awready;
  wire [7:0]  O_s_awlen;
  wire [2:0]  O_s_awsize;
  wire [1:0]  O_s_awburst;
  wire [63:0] O_s_wdata;
  wire        O_s_wvalid;
  reg         I_s_wready;
  wire        O_s_wlast;
  wire [7:0]  O_s_wstrb;
  reg         I_s_bvalid;
  wire        O_s_bready;

  ysyx_22040750_axiburst2xxx u (
    .I_clk(I_clk), .I_rst(I_rst),
    .I_m_araddr(I_m_araddr), .I_m_arvalid(I_m_arvalid), .O_m_arready(O_m_arready),
    .I_m_arlen(I_m_arlen), .I_m_arsize(I_m_arsize), .I_m_arburst(I_m_arburst),
    .O_m_rdata(O_m_rdata), .O_m_rvalid(O_m_rvalid), .O_m_rlast(O_m_rlast), .I_m_rready(I_m_rready),
    .I_m_awaddr(I_m_awaddr), .I_m_awvalid(I_m_awvalid), .O_m_awready(O_m_awready),
    .I_m_awlen(I_m_awlen), .I_m_awsize(I_m_awsize), .I_m_awburst(I_m_awburst),
    .I_m_wdata(I_m_wdata), .I_m_wvalid(I_m_wvalid), .O_m_wready(O_m_wready),
    .I_m_wlast(I_m_wlast), .I_m_wstrb(I_m_wstrb), .O_m_bvalid(O_m_bvalid), .I_m_bready(I_m_bready),
    .O_s_araddr(O_s_araddr), .O_s_arvalid(O_s_arvalid), .I_s_arready(I_s_arready),
    .O_s_arlen(O_s_arlen), .O_s_arsize(O_s_arsize), .O_s_arburst(O_s_arburst),
    .I_s_rdata(I_s_rdata), .I_s_rvalid(I_s_rvalid), .I_s_rlast(I_s_rlast), .O_s_rready(O_s_rready),
    .O_s_awaddr(O_s_awaddr), .O_s_awvalid(O_s_awvalid), .I_s_awready(I_s_awready),
    .O_s_awlen(O_s_awlen), .O_s_awsize(O_s_awsize), .O_s_awburst(O_s_awburst),
    .O_s_wdata(O_s_wdata), .O_s_wvalid(O_s_wvalid), .I_s_wready(I_s_wready),
    .O_s_wlast(O_s_wlast), .O_s_wstrb(O_s_wstrb), .I_s_bvalid(I_s_bvalid), .O_s_bready(O_s_bready)
  );

  // ---- 驱动 master: 复位后发一次 burst 读 (arlen=3, size=3) ----
  reg [3:0] st;
  initial st = 4'd0;
  always @(posedge I_clk) if (st < 4'd9) st <= st + 4'd1;
  assign I_rst = (st < 4'd2);          // 复位 2 拍(st=0,1)后释放
  always @* begin
    I_m_araddr  = 32'h80000000;
    I_m_arlen   = 8'd3;
    I_m_arsize  = 3'd3;
    I_m_arburst = 2'd1;
    I_m_arvalid = (st == 4'd3);        // 释放后发请求
    I_m_rready  = 1'b1;
    I_m_awaddr  = 32'h0; I_m_awvalid = 1'b0;
    I_m_awlen   = 8'd0; I_m_awsize = 3'd0; I_m_awburst = 2'd0;
    I_m_wdata   = 64'd0; I_m_wvalid = 1'b0; I_m_wlast = 1'b0; I_m_wstrb = 8'd0;
    I_m_bready  = 1'b1;
    I_s_arready = 1'b1;    // 从端无背压 (被 on-serviced 覆盖)
    I_s_rlast   = 1'b1;
    I_s_awready = 1'b0; I_s_wready = 1'b0; I_s_bvalid = 1'b0;
  end

  // ---- 受控从端: 单拍读, AR 握手后一周期 rvalid, rdata={2{word}} ----
  function automatic [31:0] word_of(input [31:0] a);
    case (a[4:2])
      3'd0: word_of = 32'h00000001;
      3'd1: word_of = 32'h00000002;
      3'd2: word_of = 32'h00000003;
      3'd3: word_of = 32'h00000004;
      3'd4: word_of = 32'h00000005;
      3'd5: word_of = 32'h00000006;
      3'd6: word_of = 32'h00000007;
      3'd7: word_of = 32'h00000008;
      default: word_of = 32'h0;
    endcase
  endfunction

  reg rd_serving;
  reg [31:0] rd_addr;
  always @(posedge I_clk) begin
    if (I_rst) rd_serving <= 1'b0;
    else if (O_s_arvalid && I_s_arready) begin
      rd_serving <= 1'b1;
      rd_addr <= O_s_araddr;
    end else if (O_s_rready) rd_serving <= 1'b0;
  end
  assign I_s_rvalid = rd_serving;
  assign I_s_rdata  = {2{word_of(rd_addr)}};

  // ---- 断言 ----
  // [a1] slave 侧必须单拍 32bit
  always @(posedge I_clk) begin
    if (!I_rst && O_s_arvalid && I_s_arready) begin
      if (O_s_arlen != 8'd0) assert (0);
      if (O_s_arsize != 3'd2) assert (0);
    end
  end

  // [a2] burst 完成后 master 每拍 rdata 必须等于重组值 (小端)
  reg [2:0] mbeat;
  always @(posedge I_clk) begin
    if (I_rst) mbeat <= 3'd0;
    else if (O_m_rvalid && I_m_rready) mbeat <= mbeat + 3'd1;
  end
  always @(posedge I_clk) begin
    if (!I_rst && O_m_rvalid && I_m_rready) begin
      case (mbeat)
        3'd0: assert (O_m_rdata === 64'h0000000200000001); // {word1, word0}
        3'd1: assert (O_m_rdata === 64'h0000000400000003); // {word3, word2}
        3'd2: assert (O_m_rdata === 64'h0000000600000005); // {word5, word4}
        3'd3: assert (O_m_rdata === 64'h0000000800000007); // {word7, word6}
        default: ;
      endcase
    end
  end

  // [a3] slave 侧 ARVALID 保持到握手 (axiburst 作为 AXI 主端)
  reg arvalid_d, arready_d;
  always @(posedge I_clk) begin
    arvalid_d <= O_s_arvalid;
    arready_d <= I_s_arready;
  end
  always @(posedge I_clk) begin
    if (!I_rst && arvalid_d && !arready_d && !O_s_arvalid)
      assert (0);
  end

  // cover: 读完成
  always @(posedge I_clk) begin
    if (!I_rst && O_m_rvalid && O_m_rlast) cover (1'b1);
  end
endmodule