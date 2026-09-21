// ============================================================================
// axiwatch —— P-D 调试辅助：npc 顶层 AXI 主口（io_master_*）挂起看门狗
//
// 判据（"无进展即死锁"）：读/写事务在途且某通道连续 HANG_LIMIT 周期无任何握手进展，
// 或 AR/AW/W 长时间不被从设备接受 → 打印现场（含捕获的地址/长度）并 $finish。
// 阈值 100000 周期：最长合法等待 = flash XIP refill ≈4,529cyc，×r(3.5) ≈15,852；
// refill+写回复合 ≤ ~3.2 万 → 10 万留 ≈3× 余量（据调试记录确定）。
// 非侵入 bind 到 npc 顶层；仅仿真辅助，不参与综合。
// ============================================================================
module axiwatch (
  input        clock, reset,
  input        io_master_arvalid, input io_master_arready,
  input [31:0] io_master_araddr, input [7:0] io_master_arlen,
  input        io_master_rvalid, input io_master_rready, input io_master_rlast,
  input        io_master_awvalid, input io_master_awready,
  input [31:0] io_master_awaddr, input [7:0] io_master_awlen,
  input        io_master_wvalid, input io_master_wready, input io_master_wlast,
  input        io_master_bvalid, input io_master_bready
);
  localparam int HANG_LIMIT = 100000;
  reg hang_rep;
  // 读
  reg         r_ctx;  reg [31:0] r_wait, ar_stall, ar_addr_q;
  reg [7:0]   ar_len_q;
  // 写
  reg         w_ctx;  reg [31:0] w_wait, aw_stall, aw_addr_q;
  reg [7:0]   aw_len_q; reg b_ctx; reg [31:0] b_wait;
  wire ar_hs = io_master_arvalid && io_master_arready;
  wire r_prog= io_master_rvalid && io_master_rready;
  wire aw_hs = io_master_awvalid && io_master_awready;
  wire w_hs  = io_master_wvalid && io_master_wready;
  wire b_done= io_master_bvalid && io_master_bready;

  always @(posedge clock) begin
    if (reset) begin
      hang_rep<=0; r_ctx<=0; r_wait<=0; ar_stall<=0; ar_addr_q<=0; ar_len_q<=0;
      w_ctx<=0; w_wait<=0; aw_stall<=0; aw_addr_q<=0; aw_len_q<=0; b_ctx<=0; b_wait<=0;
    end else begin
      // ---- AR / R ----
      if (!r_ctx && ar_hs) begin r_ctx<=1; r_wait<=0; ar_addr_q<=io_master_araddr; ar_len_q<=io_master_arlen; end
      else if (r_ctx) begin
        if (r_prog) r_wait<=0; else r_wait<=r_wait+32'd1;
        if (r_prog && io_master_rlast) r_ctx<=0;
      end
      if (io_master_arvalid && !io_master_arready) ar_stall<=ar_stall+32'd1; else ar_stall<=0;
      // ---- AW / W / B ----
      if (!w_ctx && (aw_hs || w_hs)) begin w_ctx<=1; w_wait<=0; aw_addr_q<=io_master_awaddr; aw_len_q<=io_master_awlen; end
      if (w_ctx) begin
        if (w_hs) w_wait<=0; else w_wait<=w_wait+32'd1;
      end
      if (!b_ctx && aw_hs) b_ctx<=1;
      if (b_ctx) begin
        if (b_done) begin b_ctx<=0; b_wait<=0; w_ctx<=0; end else b_wait<=b_wait+32'd1;
      end
      if (io_master_awvalid && !io_master_awready) aw_stall<=aw_stall+32'd1; else aw_stall<=0;

      // ---- 报告（只报一次，随后 $finish）----
      if (!hang_rep) begin
        if (r_ctx && (r_wait > HANG_LIMIT)) begin
          hang_rep<=1;
          $display("AXIWATCH HANG: R 无进展 wait=%0d addr=0x%08x len=%0d ar_stall=%0d rvalid=%b rready=%b",
                    r_wait, ar_addr_q, ar_len_q, ar_stall, io_master_rvalid, io_master_rready);
          $finish;
        end
        if (w_ctx && (w_wait > HANG_LIMIT)) begin
          hang_rep<=1;
          $display("AXIWATCH HANG: W 无进展 wait=%0d awaddr=0x%08x awlen=%0d aw_stall=%0d wvalid=%b wready=%b",
                    w_wait, aw_addr_q, aw_len_q, aw_stall, io_master_wvalid, io_master_wready);
          $finish;
        end
        if (b_ctx && (b_wait > HANG_LIMIT)) begin
          hang_rep<=1;
          $display("AXIWATCH HANG: B 无响应 wait=%0d awaddr=0x%08x awlen=%0d bvalid=%b",
                    b_wait, aw_addr_q, aw_len_q, io_master_bvalid);
          $finish;
        end
        if (ar_stall > HANG_LIMIT) begin
          hang_rep<=1;
          $display("AXIWATCH HANG: AR 未被接受 stall=%0d araddr=0x%08x arlen=%0d", ar_stall, io_master_araddr, io_master_arlen);
          $finish;
        end
        if (aw_stall > HANG_LIMIT) begin
          hang_rep<=1;
          $display("AXIWATCH HANG: AW 未被接受 stall=%0d awaddr=0x%08x awlen=%0d", aw_stall, io_master_awaddr, io_master_awlen);
          $finish;
        end
      end
    end
  end
endmodule

bind ysyx_22040750 axiwatch u_axiwatch (
  .clock(clock), .reset(reset),
  .io_master_arvalid(io_master_arvalid), .io_master_arready(io_master_arready),
  .io_master_araddr(io_master_araddr), .io_master_arlen(io_master_arlen),
  .io_master_rvalid(io_master_rvalid), .io_master_rready(io_master_rready), .io_master_rlast(io_master_rlast),
  .io_master_awvalid(io_master_awvalid), .io_master_awready(io_master_awready),
  .io_master_awaddr(io_master_awaddr), .io_master_awlen(io_master_awlen),
  .io_master_wvalid(io_master_wvalid), .io_master_wready(io_master_wready), .io_master_wlast(io_master_wlast),
  .io_master_bvalid(io_master_bvalid), .io_master_bready(io_master_bready)
);
