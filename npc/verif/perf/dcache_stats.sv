// ============================================================================
// 数据缓存统计（复核 + 正确版访存延迟）—— 非侵入式 bind 注入 dcachectrl。
//
// 目的：评估缓存收益。dcache = write-back + write-allocate。
// 由于 O_cpu_rvalid/O_cpu_bvalid 可被保持多拍、且连续命中在 RD_HIT 中无请求边界，
// **无法**按"请求->valid 响应"逐请求计时（会漏计/放大）。因此改为测量**有明确边界**的量：
//   [1] 命中/缺失计数：rd_hit/rd_miss、wr_hit/wr_miss（每次请求 1 拍，可靠）。
//   [2] **缺失代价(miss penalty)**：从缺失被发现(rd_miss/wr_miss 拍)到 cache 恢复就绪
//       (O_cpu_mem_ready=1) 的周期数（dcache 停供时长 = CPU 等待该访问的代价）。
//   [3] **MMIO 延迟**（非缓存区，如 SRAM）：MMIO 请求开始到 cache 恢复就绪的周期数。
//   [4] 命中延迟：连续命中时 cache 保持就绪、每请求约 1 拍（此处记录 rd_hit/wr_hit 时确实就绪）。
// 区域分类用于区分 SRAM(不缓存) vs PSRAM/flash(可缓存)。
// ============================================================================
module dcache_stats (
  input I_clk, I_rst,
  input I_cpu_rd_req, I_cpu_wr_req,
  input [31:0] I_cpu_addr,
  input O_cpu_mem_ready,
  input O_cpu_rvalid, O_cpu_bvalid,
  input rd_hit, rd_miss, wr_hit, wr_miss, // dcachectrl 内部（每次请求 1 拍）
  input wr_wb, rd_wb,                     // dcachectrl 内部状态拍
  input mmio_process                      // dcachectrl 内部（1=当前 MMIO 请求）
);
  localparam R_SRAM=0, R_PSRAM=1, R_FLASH=2, R_SDRAM=3, R_MMIO=4;
  reg [63:0] c_rd_hit, c_rd_miss, c_wr_hit, c_wr_miss, c_wr_wb, c_rd_wb;

  // 缺失代价（读/写分开）
  reg [63:0] rdmp_total, rdmp_n, rdmp_peak; reg rdmp_pend; reg [63:0] rdmp_t;
  reg [63:0] wrmp_total, wrmp_n, wrmp_peak; reg wrmp_pend; reg [63:0] wrmp_t;
  // MMIO 延迟（非缓存区）
  reg [63:0] mmio_total, mmio_n, mmio_peak; reg mmio_pend; reg [63:0] mmio_t; reg [2:0] mmio_reg;

  function [2:0] reg_of(input [31:0] x);
    begin
      if ((x>=32'h80000000) && (x<32'h80400000)) reg_of = R_PSRAM;
      else if ((x>=32'h30000000) && (x<32'h40000000)) reg_of = R_FLASH;
      else if ((x>=32'ha0000000) && (x<32'ha8000000)) reg_of = R_SDRAM;
      else if ((x>=32'h0f000000) && (x<32'h0f002000)) reg_of = R_SRAM;
      else reg_of = R_MMIO;
    end
  endfunction

  always @(posedge I_clk) begin
    if (I_rst) begin
      c_rd_hit<=0; c_rd_miss<=0; c_wr_hit<=0; c_wr_miss<=0; c_wr_wb<=0; c_rd_wb<=0;
      rdmp_total<=0; rdmp_n<=0; rdmp_peak<=0; rdmp_pend<=0; rdmp_t<=0;
      wrmp_total<=0; wrmp_n<=0; wrmp_peak<=0; wrmp_pend<=0; wrmp_t<=0;
      mmio_total<=0; mmio_n<=0; mmio_peak<=0; mmio_pend<=0; mmio_t<=0; mmio_reg<=R_MMIO;
    end else begin
      if (rd_hit)  c_rd_hit  <= c_rd_hit  + 64'd1;
      if (rd_miss) c_rd_miss <= c_rd_miss + 64'd1;
      if (wr_hit)  c_wr_hit  <= c_wr_hit  + 64'd1;
      if (wr_miss) c_wr_miss <= c_wr_miss + 64'd1;
      if (wr_wb)   c_wr_wb   <= c_wr_wb   + 64'd1;
      if (rd_wb)   c_rd_wb   <= c_rd_wb   + 64'd1;

      // ---- 读缺失代价：rd_miss(1拍) -> cache 恢复就绪 ----
      if (rd_miss && !rdmp_pend) begin rdmp_pend<=1; rdmp_t<=1; end
      else if (rdmp_pend) rdmp_t <= rdmp_t + 64'd1;
      if (rdmp_pend && O_cpu_mem_ready && !rd_miss) begin
        rdmp_total <= rdmp_total + rdmp_t; rdmp_n <= rdmp_n + 64'd1;
        if (rdmp_t > rdmp_peak) rdmp_peak <= rdmp_t;
        rdmp_pend <= 0;
      end

      // ---- 写缺失代价：wr_miss(1拍) -> cache 恢复就绪 ----
      if (wr_miss && !wrmp_pend) begin wrmp_pend<=1; wrmp_t<=1; end
      else if (wrmp_pend) wrmp_t <= wrmp_t + 64'd1;
      if (wrmp_pend && O_cpu_mem_ready && !wr_miss) begin
        wrmp_total <= wrmp_total + wrmp_t; wrmp_n <= wrmp_n + 64'd1;
        if (wrmp_t > wrmp_peak) wrmp_peak <= wrmp_t;
        wrmp_pend <= 0;
      end

      // ---- MMIO（非缓存区）延迟：请求开始 -> cache 恢复就绪 ----
      // mmio 请求开始 = mmio_process 由 0->1 且 CPU 有请求
      if (!mmio_process && (I_cpu_rd_req || I_cpu_wr_req) && O_cpu_mem_ready) begin
        mmio_pend <= 1; mmio_t <= 1; mmio_reg <= reg_of(I_cpu_addr);
      end else if (mmio_pend) begin
        mmio_t <= mmio_t + 64'd1;
        if (O_cpu_mem_ready && !mmio_process) begin
          mmio_total <= mmio_total + mmio_t; mmio_n <= mmio_n + 64'd1;
          if (mmio_t > mmio_peak) mmio_peak <= mmio_t;
          mmio_pend <= 0;
        end
      end
    end
  end

  string rn;
  final begin
    $display("DCACHE_MP: rd_miss_penalty(avg=%0d n=%0d peak=%0d)  wr_miss_penalty(avg=%0d n=%0d peak=%0d)",
      (rdmp_n!=0)?(rdmp_total/rdmp_n):0, rdmp_n, rdmp_peak,
      (wrmp_n!=0)?(wrmp_total/wrmp_n):0, wrmp_n, wrmp_peak);
    $display("DCACHE_MMIO: sram_mmio_lat(avg=%0d n=%0d peak=%0d)  [其他 mmio 已并入总数] total_mmio(avg=%0d n=%0d peak=%0d)",
      (mmio_n!=0 && mmio_reg==R_SRAM)?(mmio_total/mmio_n):0, mmio_n, mmio_peak,
      (mmio_n!=0)?(mmio_total/mmio_n):0, mmio_n, mmio_peak);
    $display("DCACHE_STAT: rd_hit=%0d rd_miss=%0d(%.2f%%) wr_hit=%0d wr_miss=%0d(%.2f%%) rd_wb_cyc=%0d wr_wb_cyc=%0d",
      c_rd_hit, c_rd_miss, ((c_rd_hit+c_rd_miss)!=0)?(100.0*c_rd_miss/(c_rd_hit+c_rd_miss)):0.0,
      c_wr_hit, c_wr_miss, ((c_wr_hit+c_wr_miss)!=0)?(100.0*c_wr_miss/(c_wr_hit+c_wr_miss)):0.0,
      c_rd_wb, c_wr_wb);
  end
endmodule

bind ysyx_22040750_dcachectrl dcache_stats u_dcstat (
  .I_clk(I_clk), .I_rst(I_rst),
  .I_cpu_rd_req(I_cpu_rd_req), .I_cpu_wr_req(I_cpu_wr_req),
  .I_cpu_addr(I_cpu_addr), .O_cpu_mem_ready(O_cpu_mem_ready),
  .O_cpu_rvalid(O_cpu_rvalid), .O_cpu_bvalid(O_cpu_bvalid),
  .rd_hit(rd_hit), .rd_miss(rd_miss), .wr_hit(wr_hit), .wr_miss(wr_miss),
  .wr_wb(wr_wb), .rd_wb(rd_wb),
  .mmio_process(mmio_process)
);
