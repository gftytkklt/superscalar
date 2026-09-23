// ---------------------------------------------------------------------------
// [9] S5 (P4): slave_crossbar owner 纪律（RTL_STD_MODELS S5 新增，bind 注入非侵入）
// 设计侧（S5 后）：六路 *_rd/wr_process owner 在 AR/AW 握手点置位、
//   rlast 握手（读）/ B 握手带 ready 门（写）释放；W/R/B 路由随 owner（随 AW/AR 锁存）。
// 本监视器钉死四条纪律：
//   ① 地址译码三路 flag 互斥；       ② owner 至多一路（读/写各一）；
//   ③ 有响应路由 ⇔ 恰有一路 owner；  ④ W 拍被接受时必有写 owner。
// ---------------------------------------------------------------------------
module slave_crossbar_check (
    input clk, rst,
    // 地址译码 flag
    input [2:0] ar_flags,  // {clint, psram, bus}
    input [2:0] aw_flags,
    // owner
    input [2:0] rd_owner,  // {clint_rd_process, psram_rd_process, bus_rd_process}
    input [2:0] wr_owner,  // {clint_wr_process, psram_wr_process, bus_wr_process}
    // 路由侧观测
    input cache_rvalid, cache_bvalid,
    input cache_wvalid, cache_wready
);
  always @(posedge clk) begin
    if (!rst) begin
      // ① 地址区间互斥
      if (ar_flags != 0 && (ar_flags & (ar_flags - 3'b001)) != 0)
        $error("XBAR: AR address flags not mutually exclusive (%b)", ar_flags);
      if (aw_flags != 0 && (aw_flags & (aw_flags - 3'b001)) != 0)
        $error("XBAR: AW address flags not mutually exclusive (%b)", aw_flags);
      // ② owner 至多一路
      if ((rd_owner & (rd_owner - 3'b001)) != 0)
        $error("XBAR: multiple read owners (%b)", rd_owner);
      if ((wr_owner & (wr_owner - 3'b001)) != 0)
        $error("XBAR: multiple write owners (%b)", wr_owner);
      // ③ 有响应路由 ⇔ 恰有一路 owner
      if (cache_rvalid && rd_owner == 0)
        $error("XBAR: R response routed without read owner");
      if (cache_bvalid && wr_owner == 0)
        $error("XBAR: B response routed without write owner");
      // ④ W 拍被接受时必有写 owner
      if (cache_wvalid && cache_wready && wr_owner == 0)
        $error("XBAR: W beat accepted without write owner");
    end
  end
endmodule

bind ysyx_22040750_slave_crossbar slave_crossbar_check u_xbar (
  .clk(I_clk), .rst(I_rst),
  .ar_flags({clint_ar_flag, psram_ar_flag, bus_ar_flag}),
  .aw_flags({clint_aw_flag, psram_aw_flag, bus_aw_flag}),
  .rd_owner({clint_rd_process, psram_rd_process, bus_rd_process}),
  .wr_owner({clint_wr_process, psram_wr_process, bus_wr_process}),
  .cache_rvalid(O_cache_rvalid), .cache_bvalid(O_cache_bvalid),
  .cache_wvalid(I_cache_wvalid), .cache_wready(O_cache_wready)
);
