// ============================================================================
// Formal properties: dcachectrl 状态机可达性 (Bug1)
//
// 设计规范：对可缓存地址的内存读写应当进入 cache 命中/缺失路径
// （RD_HIT/RD_MISS/WR_HIT/WR_MISS 状态**可达**）。
// 当前 RTL 因 mmio_flag 恒真（dcachectrl:2014），这些状态对任何输入序列
// 都不可达 -> cover 将报 UNSAT/failed == 形式化证明 Bug1。
// 采用过程式 assert/cover（yosys -formal 直接支持）。
// ============================================================================
module dcache_cover (
  input I_clk, I_rst
);
  wire [31:0] I_cpu_addr;
  wire [63:0] I_cpu_data;
  wire [7:0]  I_cpu_wmask, I_cpu_rmask;
  wire        I_cpu_rd_req, I_cpu_wr_req, O_cpu_mem_ready;
  wire        I_cpu_fencei, O_dcache_clean;
  wire [255:0] I_way0_rdata, I_way1_rdata;
  wire [5:0]  O_sram_addr;
  wire [3:0]  O_sram_cen, O_sram_wen;
  wire [255:0] O_sram_wdata, O_sram_wmask;
  wire [63:0] I_mem_rdata;
  wire        I_mem_arready, I_mem_rvalid, I_mem_rlast;
  wire [31:0] O_mem_araddr;
  wire        O_mem_arvalid, O_mem_rready;
  wire [7:0]  O_mem_arlen;
  wire [2:0]  O_mem_arsize;
  wire [1:0]  O_mem_arburst;
  wire        I_mem_awready, I_mem_wready, I_mem_bvalid;
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
    .O_cpu_mem_ready(O_cpu_mem_ready),
    .I_cpu_fencei(I_cpu_fencei), .O_dcache_clean(O_dcache_clean),
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

  // --- 论断：请求拍上 mmio_flag 与命中互斥（当前实现令命中结构上不可达）
  always @(posedge I_clk) begin
    if (!I_rst && u.mmio_flag && (u.rd_hit || u.wr_hit))
      assert (0);
  end

  // --- 可达性 cover：修复 cache 后应可到；当前 buggy 版本全部不可达 -> FAIL
  always @(posedge I_clk) begin
    if (!I_rst) begin
      if (u.current_state == 16'h2)  cover (1'b1);  // RD_HIT
      if (u.current_state == 16'h4)  cover (1'b1);  // RD_MISS
      if (u.current_state == 16'h40) cover (1'b1);  // WR_HIT
      if (u.current_state == 16'h80) cover (1'b1);  // WR_MISS
    end
  end
endmodule