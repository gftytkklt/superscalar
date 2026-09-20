// ============================================================================
// sdramcore_probe —— P-D 调试辅助：SDRAM 控制器核心（sdram_axi_core）卡点定位
//
// 判据：有请求在途（ram_req_w）但核心长期不接收（!ram_accept_w）→ 打印状态现场：
//   state_q / next_state / target_state / delay_state / refresh_q / ram_ack_w /
//   ram_rd_w / ram_wr_w / row_open_q / delay_r
// 阈值 80000（比 pmem 探针 90000 更早，确保本探针先报现场）。
// ============================================================================
module sdramcore_probe (
  input        clock, reset,
  input        ram_req_w, ram_accept_w, ram_ack_w,
  input        ram_rd_w, input [3:0] ram_wr_w,
  input [3:0]  state_q, next_state_r, target_state_q, delay_state_q,
  input        refresh_q,
  input [7:0]  row_open_q,
  input [3:0]  delay_r
);
  localparam int HANG_LIMIT = 80000;
  reg [31:0] cnt; reg rep;

  always @(posedge clock) begin
    if (reset) begin cnt<=0; rep<=0; end
    else if (!rep) begin
      if (ram_req_w && !ram_accept_w) cnt<=cnt+32'd1; else cnt<=0;
      if (cnt > HANG_LIMIT) begin
        rep<=1;
        $display("SDRAMCORE STUCK: req=1 accept=0 持续 %0d 拍", cnt);
        $display("  state_q=%0d next=%0d target=%0d delay_state=%0d refresh_q=%b ack=%b",
                  state_q, next_state_r, target_state_q, delay_state_q, refresh_q, ram_ack_w);
        $display("  ram_rd=%b ram_wr=%b row_open=%b delay_r=%0d",
                  ram_rd_w, ram_wr_w, row_open_q, delay_r);
        $finish;
      end
    end
  end
endmodule

bind sdram_axi_core sdramcore_probe u_coreprobe (
  .clock(clk_i), .reset(rst_i),
  .ram_req_w(ram_req_w), .ram_accept_w(ram_accept_w), .ram_ack_w(ram_ack_w),
  .ram_rd_w(ram_rd_w), .ram_wr_w(ram_wr_w),
  .state_q(state_q), .next_state_r(next_state_r), .target_state_q(target_state_q),
  .delay_state_q(delay_state_q), .refresh_q(refresh_q),
  .row_open_q(row_open_q), .delay_r(delay_r)
);
