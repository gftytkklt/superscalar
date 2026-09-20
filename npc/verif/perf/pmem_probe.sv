// ============================================================================
// pmem_probe —— P-D 调试辅助：SDRAM pmem 层仲裁/元数据 FIFO 卡点定位（最早报警）
// 观察：req_wr_q/req_rd_q/req_prio_q/hold 标志、write_active/read_active、prio、
//       req_fifo_accept_w（元数据 FIFO 是否有空位）、FIFO count/valid、resp_accept_w
// 判据：AXI 有请求在途（awvalid|arvalid）但两者 active 均 0 持续 → 打印现场
// ============================================================================
module pmem_probe (
  input        clock, reset,
  input        axi_awvalid_i, axi_awready_o, axi_arvalid_i,
  input        axi_wvalid_i, input [3:0] axi_wstrb_i, input [3:0] ram_wr_o, input ram_rd_o, input ram_accept_i,
  input        write_active_w, read_active_w, write_prio_w, read_prio_w,
  input        req_wr_q, req_rd_q, req_prio_q, req_hold_rd_q, req_hold_wr_q,
  input        req_fifo_accept_w, req_out_valid_w, resp_accept_w,
  input [2:0]  fifo_count,
  input [7:0]  req_len_q
);
  localparam int HANG_LIMIT = 70000;
  reg [31:0] cnt; reg rep;
  // 实证计数器（最终恒定输出，供跨配置对比）
  reg [63:0] n_aw_hs, n_w_hs, n_wstrb0, n_aw_no_w;
  always @(posedge clock) begin
    if (reset) begin cnt<=0; rep<=0; n_aw_hs<=0; n_w_hs<=0; n_wstrb0<=0; n_aw_no_w<=0; end
    else if (!rep) begin
      // 触发条件改为：AW 在途但未被接受（无论内部 active 如何）
      if (axi_awvalid_i && !axi_awready_o)
        cnt <= cnt + 32'd1;
      else cnt <= 0;
      if (axi_awvalid_i && axi_awready_o) n_aw_hs<=n_aw_hs+64'd1;
      if (axi_wvalid_i && (axi_wstrb_i==4'd0)) n_wstrb0<=n_wstrb0+64'd1;
      if (axi_awvalid_i && !axi_wvalid_i) n_aw_no_w<=n_aw_no_w+64'd1;
      if (cnt > HANG_LIMIT) begin
        rep<=1;
        $display("PMEM STUCK: AW 未被接受持续 %0d 拍 (awv=%b awready=%b arv=%b)",
                  cnt, axi_awvalid_i, axi_awready_o, axi_arvalid_i);
        $display("  prio: wr_prio=%b rd_prio=%b req_prio_q=%b hold_rd=%b hold_wr=%b",
                  write_prio_w, read_prio_w, req_prio_q, req_hold_rd_q, req_hold_wr_q);
        $display("  state: req_wr_q=%b req_rd_q=%b req_len_q=%0d | fifo_accept=%b fifo_count=%0d out_valid=%b resp_accept=%b",
                  req_wr_q, req_rd_q, req_len_q, req_fifo_accept_w, fifo_count, req_out_valid_w, resp_accept_w);
        $display("  W通道: wvalid=%b wstrb=%b | ram_wr_o=%b ram_rd_o=%b ram_accept_i=%b",
                  axi_wvalid_i, axi_wstrb_i, ram_wr_o, ram_rd_o, ram_accept_i);
        $finish;
      end
    end
  end

  // 恒定计数输出（仿真结束），用于"是否真的出现零 strb / AW 无 W"的实证
  final begin
    $display("PMEM COUNT: aw_hs=%0d wstrb0_beats=%0d aw_without_w_cycles=%0d", n_aw_hs, n_wstrb0, n_aw_no_w);
  end
endmodule

bind sdram_axi_pmem pmem_probe u_pmemprobe (
  .clock(clk_i), .reset(rst_i),
  .axi_awvalid_i(axi_awvalid_i), .axi_awready_o(axi_awready_o), .axi_arvalid_i(axi_arvalid_i),
  .axi_wvalid_i(axi_wvalid_i), .axi_wstrb_i(axi_wstrb_i), .ram_wr_o(ram_wr_o), .ram_rd_o(ram_rd_o), .ram_accept_i(ram_accept_i),
  .write_active_w(write_active_w), .read_active_w(read_active_w),
  .write_prio_w(write_prio_w), .read_prio_w(read_prio_w),
  .req_wr_q(req_wr_q), .req_rd_q(req_rd_q), .req_prio_q(req_prio_q),
  .req_hold_rd_q(req_hold_rd_q), .req_hold_wr_q(req_hold_wr_q),
  .req_fifo_accept_w(req_fifo_accept_w), .req_out_valid_w(req_out_valid_w),
  .resp_accept_w(resp_accept_w), .fifo_count(u_requests.count), .req_len_q(req_len_q)
);
