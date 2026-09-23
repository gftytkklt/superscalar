// ---------------------------------------------------------------------------
// [5] S1 (P3): dcache 写通道 B 响应纪律（RTL_STD_MODELS S1 新增，bind 注入非侵入）
// 设计侧（ysyx_22040750_dcachectrl）：b_ack = bvalid && bready 为唯一协议应答点
// （正确性不依赖 bready 恒 1）；b_pend 在 AW 发出拍置位、b_ack 拍清除。
// 本监视器检查三条纪律：
//   ① AW_IDLE 拍发起新写事务时不得已有在途 B（outstanding ≤ 1）；
//     —— 注意 wr_issue 是电平型条件（fencei/MMIO 写飞行期间保持 1），
//        必须限定在 aw_state==AW_IDLE 的"发起新事务"拍检查，否则误报。
//   ② B 应答必须对应在途写事务（无凭空 B）；
//   ③ 在途 B 有界进度（>256 拍未 ack 判挂死）。
// ---------------------------------------------------------------------------
module dcache_write_check (
    input clk, rst,
    input b_ack, b_pend, wr_issue,
    input [2:0] aw_state,
    input [3:0] wb_state,
    input [15:0] current_state
);
  localparam AW_IDLE = 3'b001;

  reg [7:0] pend_cnt;
  always @(posedge clk) begin
    if (rst)                      pend_cnt <= 0;
    else if (b_pend && !b_ack)    pend_cnt <= pend_cnt + 1;
    else                          pend_cnt <= 0;
  end

  always @(posedge clk) begin
    if (!rst) begin
      if (wr_issue && b_pend && aw_state == AW_IDLE)
        $error("DCACHE: new write issue while B pending (outstanding>1) state=%h aw=%h wb=%h",
               current_state, aw_state, wb_state);
      if (b_ack && !b_pend)
        $error("DCACHE: B response without outstanding write state=%h aw=%h wb=%h",
               current_state, aw_state, wb_state);
      if (&pend_cnt)
        $error("DCACHE: B response pending >256 cycles state=%h aw=%h wb=%h",
               current_state, aw_state, wb_state);
    end
  end
endmodule

// bind 到 dcachectrl：内部信号 b_ack/b_pend/wr_issue/aw_state/wb_state/current_state
// 见 vsrc/ysyx_22040750.v（S1 新增 b_ack/b_pend/wr_issue；其余为既有 FSM 状态）
bind ysyx_22040750_dcachectrl dcache_write_check u_dcache_wb (
  .clk(I_clk), .rst(I_rst),
  .b_ack(b_ack), .b_pend(b_pend), .wr_issue(wr_issue),
  .aw_state(aw_state), .wb_state(wb_state), .current_state(current_state)
);
