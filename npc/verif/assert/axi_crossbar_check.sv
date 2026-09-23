// ---------------------------------------------------------------------------
// [12] S7 (P4 归档): axi_crossbar 仲裁纪律（RTL_STD_MODELS S7 新增，bind 注入非侵入）
// C 批归档项（仅断言，不改结构）。本模块为 I/D cache 共享 SDRAM AXI 通道的
// 二选一仲裁器（ch0=icache / ch1=dcache），纪律：
//   ① AR grant 互斥（ch0_ar_flag / ch1_ar_flag 不同拍同 1）；
//   ② R 路由互斥（ch0_rd_flag / ch1_rd_flag 不同拍同 1，FSM 状态天然互斥）；
//   ③ 响应事务保持：rd 拍非 last 握手则下一拍仍在同一通道（不中途重仲裁）。
// rr 指针（priority_flag）仅在 IDLE 仲裁拍翻转——与状态耦合的既有设计归档不动
// （候选台账：抽通用 rr_arbiter 收益低不做）。
// ---------------------------------------------------------------------------
module axi_crossbar_check (
    input clk, rst,
    input ch0_ar_flag, ch1_ar_flag,
    input ch0_rd_flag, ch1_rd_flag,
    input ch0_last_hs, ch1_last_hs
);
  reg ch0_rd_d, ch1_rd_d;
  reg ch0_last_d, ch1_last_d;   // last 握手是组合单拍信号，需与 rd_d 同沿对齐采样
  always @(posedge clk) begin
    ch0_rd_d   <= ch0_rd_flag;
    ch1_rd_d   <= ch1_rd_flag;
    ch0_last_d <= ch0_last_hs;
    ch1_last_d <= ch1_last_hs;
    if (!rst) begin
      // ① AR grant 互斥
      if (ch0_ar_flag && ch1_ar_flag)
        $error("XBAR2: AR grant to both channels");
      // ② R 路由互斥
      if (ch0_rd_flag && ch1_rd_flag)
        $error("XBAR2: R routed to both channels");
      // ③ 响应事务保持（非 last 拍不得离开本通道；last 握手取同拍延迟值比对）
      if (ch0_rd_d && !ch0_last_d && !ch0_rd_flag)
        $error("XBAR2: ch0 response transaction preempted before last");
      if (ch1_rd_d && !ch1_last_d && !ch1_rd_flag)
        $error("XBAR2: ch1 response transaction preempted before last");
    end
  end
endmodule

bind ysyx_22040750_axi_crossbar axi_crossbar_check u_xbar2 (
  .clk(I_clk), .rst(I_rst),
  .ch0_ar_flag(ch0_ar_flag), .ch1_ar_flag(ch1_ar_flag),
  .ch0_rd_flag(ch0_rd_flag), .ch1_rd_flag(ch1_rd_flag),
  .ch0_last_hs(ch0_last_handshake), .ch1_last_hs(ch1_last_handshake)
);
