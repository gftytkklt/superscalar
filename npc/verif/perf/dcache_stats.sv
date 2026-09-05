// ============================================================================
// 数据缓存统计（按存储区域拆分的访存延迟）—— 非侵入式 bind 注入 dcachectrl。
// 目的：为 cachesim 提供**按区域参数化**的访存/缺失/MMIO 延迟。
// 区域（= SoC 存储地址区间，由 .ld 决定访问落到哪）：
//   PSRAM [0x80000000,0x80400000) 可缓存堆区
//   flash [0x30000000,0x40000000) 可缓存 .text/.rodata
//   SDRAM [0xa0000000,0xa8000000) 可缓存
//   SRAM  [0x0f000000,0x0f002000) **故意非缓存**（RTL 合并为 MMIO 单拍）
//   其它 = 外设/空洞 MMIO
// 记录（都按区域拆分）：
//   rd_miss_penalty[region]  : cacheable 读缺失的 refill 代价（缺失被发现->cache 就绪）
//   wr_miss_penalty[region]  : cacheable 写缺失的 refill 代价（不含脏块回写）
//   wr_wb[region]            : 写缺失时额外脏块回写代价（WR_WB 状态周期，已含在 wr_miss_penalty 内）
//   mmio_lat[region]         : 非缓存区(MMIO) 直接访存延迟
//   hit_miss 计数
// ============================================================================
module dcache_stats (
  input I_clk, I_rst,
  input I_cpu_rd_req, I_cpu_wr_req,
  input [31:0] I_cpu_addr,
  input O_cpu_mem_ready,
  input O_cpu_rvalid, O_cpu_bvalid,
  input rd_hit, rd_miss, wr_hit, wr_miss,
  input wr_wb, rd_wb,
  input mmio_process
);
  localparam R_SRAM=0, R_PSRAM=1, R_FLASH=2, R_SDRAM=3, R_MMIO=4;
  reg [63:0] c_rd_hit, c_rd_miss, c_wr_hit, c_wr_miss, c_rd_wb_cyc, c_wr_wb_cyc;

  reg [63:0] rmp_total[0:4], rmp_n[0:4], rmp_peak[0:4];
  reg [63:0] wmp_total[0:4], wmp_n[0:4], wmp_peak[0:4];
  reg [63:0] mmio_total[0:4], mmio_n[0:4], mmio_peak[0:4];
  reg [63:0] wrmp_wb_total[0:4], wrmp_wb_n[0:4];   // 写缺失脏回写代价（WR_WB 状态占用）
  reg rmp_pend, wmp_pend, mmio_pend;
  reg [63:0] rmp_t, wmp_t, mmio_t;
  reg [2:0] rmp_reg, wmp_reg, mmio_reg;
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
      for (i=0;i<5;i=i+1) begin
        rmp_total[i]<=0; rmp_n[i]<=0; rmp_peak[i]<=0;
        wmp_total[i]<=0; wmp_n[i]<=0; wmp_peak[i]<=0;
        mmio_total[i]<=0; mmio_n[i]<=0; mmio_peak[i]<=0;
        wrmp_wb_total[i]<=0; wrmp_wb_n[i]<=0;
      end
      c_rd_hit<=0; c_rd_miss<=0; c_wr_hit<=0; c_wr_miss<=0; c_rd_wb_cyc<=0; c_wr_wb_cyc<=0;
      rmp_pend<=0; wmp_pend<=0; mmio_pend<=0; rmp_t<=0; wmp_t<=0; mmio_t<=0;
      rmp_reg<=R_MMIO; wmp_reg<=R_MMIO; mmio_reg<=R_MMIO;
    end else begin
      if (rd_hit)  c_rd_hit  <= c_rd_hit  + 64'd1;
      if (rd_miss) c_rd_miss <= c_rd_miss + 64'd1;
      if (wr_hit)  c_wr_hit  <= c_wr_hit  + 64'd1;
      if (wr_miss) c_wr_miss <= c_wr_miss + 64'd1;
      if (rd_wb)   c_rd_wb_cyc <= c_rd_wb_cyc + 64'd1;
      if (wr_wb)   c_wr_wb_cyc <= c_wr_wb_cyc + 64'd1;

      // --- 读缺失代价（按区域）---
      if (rd_miss && !rmp_pend) begin rmp_pend<=1; rmp_t<=1; rmp_reg<=reg_of(I_cpu_addr); end
      else if (rmp_pend) rmp_t <= rmp_t + 64'd1;
      if (rmp_pend && O_cpu_mem_ready && !rd_miss) begin
        rmp_total[rmp_reg] <= rmp_total[rmp_reg] + rmp_t;
        rmp_n[rmp_reg]     <= rmp_n[rmp_reg] + 64'd1;
        if (rmp_t > rmp_peak[rmp_reg]) rmp_peak[rmp_reg] <= rmp_t;
        rmp_pend <= 0;
      end

      // --- 写缺失代价（按区域；含 refill；脏回写单独记录）---
      if (wr_miss && !wmp_pend) begin wmp_pend<=1; wmp_t<=1; wmp_reg<=reg_of(I_cpu_addr); end
      else if (wmp_pend) wmp_t <= wmp_t + 64'd1;
      if (wmp_pend && O_cpu_mem_ready && !wr_miss) begin
        wmp_total[wmp_reg] <= wmp_total[wmp_reg] + wmp_t;
        wmp_n[wmp_reg]     <= wmp_n[wmp_reg] + 64'd1;
        if (wmp_t > wmp_peak[wmp_reg]) wmp_peak[wmp_reg] <= wmp_t;
        wmp_pend <= 0;
      end
      // 写缺失脏回写（WR_WB 状态周期，按最后写缺失 region）
      if (wr_wb && wmp_reg < 5) wrmp_wb_total[wmp_reg] <= wrmp_wb_total[wmp_reg] + 64'd1;

      // --- MMIO（非缓存区）直接访存延迟（按区域）---
      if (!mmio_process && (I_cpu_rd_req || I_cpu_wr_req) && O_cpu_mem_ready) begin
        mmio_pend <= 1; mmio_t <= 1; mmio_reg <= reg_of(I_cpu_addr);
      end else if (mmio_pend) begin
        mmio_t <= mmio_t + 64'd1;
        if (O_cpu_mem_ready && !mmio_process) begin
          mmio_total[mmio_reg] <= mmio_total[mmio_reg] + mmio_t;
          mmio_n[mmio_reg]     <= mmio_n[mmio_reg] + 64'd1;
          if (mmio_t > mmio_peak[mmio_reg]) mmio_peak[mmio_reg] <= mmio_t;
          mmio_pend <= 0;
        end
      end
    end
  end

  function [63:0] avg(input [63:0] t, input [63:0] n); begin avg = (n!=0)?(t/n):0; end endfunction
  final begin
    $display("DCACHE_RD_MISS_PENALTY: psram(avg=%0d n=%0d peak=%0d) flash(avg=%0d n=%0d) sdram(avg=%0d n=%0d)",
      avg(rmp_total[R_PSRAM],rmp_n[R_PSRAM]), rmp_n[R_PSRAM], rmp_peak[R_PSRAM],
      avg(rmp_total[R_FLASH],rmp_n[R_FLASH]), rmp_n[R_FLASH],
      avg(rmp_total[R_SDRAM],rmp_n[R_SDRAM]), rmp_n[R_SDRAM]);
    $display("DCACHE_WR_MISS_PENALTY: psram(avg=%0d n=%0d) flash(avg=%0d n=%0d) sdram(avg=%0d n=%0d) | wr_wb_cyc=%0d",
      avg(wmp_total[R_PSRAM],wmp_n[R_PSRAM]), wmp_n[R_PSRAM],
      avg(wmp_total[R_FLASH],wmp_n[R_FLASH]), wmp_n[R_FLASH],
      avg(wmp_total[R_SDRAM],wmp_n[R_SDRAM]), wmp_n[R_SDRAM],
      c_wr_wb_cyc);
    $display("DCACHE_MMIO_LAT: sram(avg=%0d n=%0d peak=%0d) other(avg=%0d n=%0d)",
      avg(mmio_total[R_SRAM],mmio_n[R_SRAM]), mmio_n[R_SRAM], mmio_peak[R_SRAM],
      avg(mmio_total[R_MMIO],mmio_n[R_MMIO]), mmio_n[R_MMIO]);
    $display("DCACHE_STAT: rd_hit=%0d rd_miss=%0d(%.2f%%) wr_hit=%0d wr_miss=%0d(%.2f%%) rd_wb_cyc=%0d wr_wb_cyc=%0d",
      c_rd_hit, c_rd_miss, ((c_rd_hit+c_rd_miss)!=0)?(100.0*c_rd_miss/(c_rd_hit+c_rd_miss)):0.0,
      c_wr_hit, c_wr_miss, ((c_wr_hit+c_wr_miss)!=0)?(100.0*c_wr_miss/(c_wr_hit+c_wr_miss)):0.0,
      c_rd_wb_cyc, c_wr_wb_cyc);
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
