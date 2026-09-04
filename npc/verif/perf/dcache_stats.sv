// 数据缓存命中/缺失统计（复核 store 高延迟）—— 非侵入式 bind 注入 dcachectrl。
// 说明：dcache 为 write-back + write-allocate；store 缺失走
//   WR_MISS -> WR_RELOAD(取行) -> [WR_WB 脏行回写] -> WR_ALLOCATE -> WR_HIT，
//   多 burst 路径显著慢于 load。用本模块量化 store/load 的命中/缺失与脏回写次数，
//   确认 store 高延迟是否源于"store 多缺失 + 脏回写"（而非测量伪影）。
module dcache_stats (
  input I_clk, I_rst,
  input rd_hit, rd_miss,             // dcachectrl 内部
  input wr_hit, wr_miss,             // dcachectrl 内部
  input wr_wb,                       // dcachectrl 内部（WR_WB 状态）
  input rd_wb
);
  reg [63:0] c_rd_hit, c_rd_miss, c_wr_hit, c_wr_miss, c_wr_wb, c_rd_wb;
  always @(posedge I_clk) begin
    if (I_rst) begin
      c_rd_hit<=0; c_rd_miss<=0; c_wr_hit<=0; c_wr_miss<=0; c_wr_wb<=0; c_rd_wb<=0;
    end else begin
      if (rd_hit)  c_rd_hit  <= c_rd_hit  + 64'd1;
      if (rd_miss) c_rd_miss <= c_rd_miss + 64'd1;
      if (wr_hit)  c_wr_hit  <= c_wr_hit  + 64'd1;
      if (wr_miss) c_wr_miss <= c_wr_miss + 64'd1;
      if (wr_wb)   c_wr_wb   <= c_wr_wb   + 64'd1;
      if (rd_wb)   c_rd_wb   <= c_rd_wb   + 64'd1;
    end
  end
  final begin
    $display("DCACHE_STAT: rd_hit=%0d rd_miss=%0d(rd_miss_rate=%.2f%%) wr_hit=%0d wr_miss=%0d(wr_miss_rate=%.2f%%) wr_wb=%0d rd_wb=%0d",
      c_rd_hit, c_rd_miss,
      ((c_rd_hit+c_rd_miss)!=0) ? (100.0*c_rd_miss/(c_rd_hit+c_rd_miss)) : 0.0,
      c_wr_hit, c_wr_miss,
      ((c_wr_hit+c_wr_miss)!=0) ? (100.0*c_wr_miss/(c_wr_hit+c_wr_miss)) : 0.0,
      c_wr_wb, c_rd_wb);
  end
endmodule

bind ysyx_22040750_dcachectrl dcache_stats u_dcstat (
  .I_clk(I_clk), .I_rst(I_rst),
  .rd_hit(rd_hit), .rd_miss(rd_miss),
  .wr_hit(wr_hit), .wr_miss(wr_miss),
  .wr_wb(wr_wb), .rd_wb(rd_wb)
);
