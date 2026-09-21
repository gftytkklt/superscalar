// ============================================================================
// 指令缓存统计（P-C 数据分析平台）—— 非侵入式 bind 注入 icachectrl。
// 口径（与 dcache_stats 一致的"FSM/握手有边界计时"原则）：
//   miss 事件   : rd_miss（pc 握手拍且未命中，每请求恰 1 拍，不受 held-valid 污染）
//   缺失代价    : rd_miss 握手拍 → O_cpu_rvalid 交付拍的周期数（含 refill/MMIO 取指全程）
//   命中延迟    : rd_hit 握手拍 → O_cpu_rvalid 拍（通常 1~2）
//   区域        : 与 dcache_stats 相同的地址分区（.ld 决定落区）
// 用途：AMAT = hit_time + miss_rate × miss_penalty（icache 项）；
//       TMT(icache) = Σ 缺失代价。P-D（SDRAM AXI + delayer）后重跑即得对比。
// ============================================================================
module icache_stats (
  input I_clk,
  input I_rst,
  input [31:0] I_cpu_addr,
  input rd_hit, rd_miss,
  input O_cpu_rvalid
);
  localparam R_SRAM=0, R_PSRAM=1, R_FLASH=2, R_SDRAM=3, R_MMIO=4;
  reg [63:0] c_hit, c_miss;
  reg [63:0] mp_total[0:4], mp_n[0:4], mp_peak[0:4];   // miss penalty（按区域）
  reg [63:0] hl_total, hl_n, hl_peak;                  // hit latency
  reg mpend, hpend;
  reg [63:0] mt, ht;
  reg [2:0] mreg;
  integer i;

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
      for (i=0;i<5;i=i+1) begin mp_total[i]<=0; mp_n[i]<=0; mp_peak[i]<=0; end
      c_hit<=0; c_miss<=0; hl_total<=0; hl_n<=0; hl_peak<=0;
      mpend<=0; hpend<=0; mt<=0; ht<=0; mreg<=R_MMIO;
    end else begin
      // ---- miss penalty：rd_miss 握手 → O_cpu_rvalid ----
      if (rd_miss) begin
        c_miss  <= c_miss + 64'd1;
        mpend   <= 1'b1;
        mt      <= 64'd0;
        mreg    <= reg_of(I_cpu_addr);
      end else if (mpend) begin
        mt <= mt + 64'd1;
        if (O_cpu_rvalid) begin
          mp_total[mreg] <= mp_total[mreg] + mt + 64'd1;
          mp_n[mreg]     <= mp_n[mreg] + 64'd1;
          if (mt + 64'd1 > mp_peak[mreg]) mp_peak[mreg] <= mt + 64'd1;
          mpend <= 1'b0;
        end
      end
      // ---- hit latency：rd_hit 握手 → O_cpu_rvalid ----
      if (rd_hit) begin
        c_hit  <= c_hit + 64'd1;
        hpend  <= 1'b1;
        ht     <= 64'd0;
      end else if (hpend) begin
        ht <= ht + 64'd1;
        if (O_cpu_rvalid) begin
          hl_total <= hl_total + ht + 64'd1;
          hl_n     <= hl_n + 64'd1;
          if (ht + 64'd1 > hl_peak) hl_peak <= ht + 64'd1;
          hpend <= 1'b0;
        end
      end
    end
  end

  function [63:0] avg(input [63:0] t, input [63:0] n); begin avg = (n!=0)?(t/n):0; end endfunction
  final begin
    $display("ICACHE_MISS_PENALTY: psram(avg=%0d n=%0d peak=%0d) flash(avg=%0d n=%0d peak=%0d) sdram(avg=%0d n=%0d peak=%0d) sram_mmio(avg=%0d n=%0d) other_mmio(avg=%0d n=%0d)",
      avg(mp_total[R_PSRAM],mp_n[R_PSRAM]), mp_n[R_PSRAM], mp_peak[R_PSRAM],
      avg(mp_total[R_FLASH],mp_n[R_FLASH]), mp_n[R_FLASH], mp_peak[R_FLASH],
      avg(mp_total[R_SDRAM],mp_n[R_SDRAM]), mp_n[R_SDRAM], mp_peak[R_SDRAM],
      avg(mp_total[R_SRAM],mp_n[R_SRAM]),   mp_n[R_SRAM],
      avg(mp_total[R_MMIO],mp_n[R_MMIO]),   mp_n[R_MMIO]);
    $display("ICACHE_STAT: hit=%0d miss=%0d(%.2f%%) hit_lat(avg=%0d n=%0d peak=%0d) tmt_sum=%0d",
      c_hit, c_miss, ((c_hit+c_miss)!=0)?(100.0*c_miss/(c_hit+c_miss)):0.0,
      avg(hl_total,hl_n), hl_n, hl_peak,
      mp_total[R_PSRAM]+mp_total[R_FLASH]+mp_total[R_SDRAM]+mp_total[R_SRAM]+mp_total[R_MMIO]);
  end
endmodule

bind ysyx_22040750_icachectrl icache_stats u_icstat (
  .I_clk(I_clk),
  .I_rst(I_rst),
  .I_cpu_addr(I_cpu_addr),
  .rd_hit(rd_hit),
  .rd_miss(rd_miss),
  .O_cpu_rvalid(O_cpu_rvalid)
);
