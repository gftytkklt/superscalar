// ============================================================================
// axidly_check —— P-D/D3：AXI 延迟校准等式运行时自检（仿 apbdly_check）
//
// 等式（讲义）：(t1 - t0) * r == t1' - t0
//   · 读 burst 逐拍：t0=AR 握手拍；t1_i=slave 呈现第 i 拍；t1'_i=本桥向 master 呈现该拍。
//   · 单写事务：t0=AW/W 首个握手；t1=B 响应呈现；t1'=B 呈现给 master。
// 独立计数：只用桥的端口握手信号 + 本模块自己的计数器（不引用桥内部状态）。
// ⚠️ 仅 PERF_DELAY 下等式有意义；直通时 t1'=t1 必然"violate"，属预期（只作事务统计）。
// ============================================================================
module axidly_check (
  input        clock, reset,
  input        in_arvalid, out_arready, input [31:0] in_araddr, input [7:0] in_arlen,
  input        out_rvalid, in_rvalid, in_rready, in_rlast,
  input        in_awvalid, out_awready, input [31:0] in_awaddr, input [7:0] in_awlen,
  input        in_wvalid, out_wready, in_wlast,
  input        out_bvalid, in_bvalid, in_bready
);
  localparam int R_S = 7, S_SHIFT = 1;   // r = 3.5（与 axi4_delayer/apb_delayer 一致）
  // 挂起看门狗阈值（同 apbdly_check，10 万周期）：读/写事务超时即判死锁 → 打印现场 + 结束仿真
  localparam int HANG_LIMIT = 100000;

  // ---------------- 读：逐拍等式 ----------------
  reg         r_ctx;         // 读事务上下文（AR 握手起，末拍交付止）
  reg         r_held;        // 已记录到、未交付的拍
  reg  [31:0] rt;            // 自 t0 起的拍数
  reg  [31:0] rk;            // 拍呈现时的 k
  reg  [7:0]  r_need;        // 本 burst 应交付拍数（arlen+1）
  reg  [7:0]  r_got;         // 已交付拍数
  reg  [63:0] n_r, n_rviol, n_rmismatch;

  wire ar_hs   = in_arvalid && out_arready;
  wire r_arr   = out_rvalid && !r_held && r_ctx;      // 新拍呈现
  wire r_deliv = in_rvalid && in_rready;             // 拍交付给 master

  // ---------------- 边界等待看门狗（区分"卡在 SoC 互连" vs "卡在转换器/控制器"）----------------
  reg [31:0] aw_stall, ar_stall, w_stall; reg stall_rep;
  always @(posedge clock) begin
    if (reset) begin aw_stall<=0; ar_stall<=0; w_stall<=0; stall_rep<=0; end
    else begin
      if (in_awvalid && !out_awready) aw_stall<=aw_stall+32'd1; else aw_stall<=0;
      if (in_arvalid && !out_arready) ar_stall<=ar_stall+32'd1; else ar_stall<=0;
      if (in_wvalid  && !out_wready ) w_stall <=w_stall +32'd1; else w_stall<=0;
      if (!stall_rep) begin
        if (aw_stall > HANG_LIMIT) begin stall_rep<=1;
          $display("AXIDLY HANG: AW 在 AXI4SDRAM 边界未被接受 stall=%0d addr=%h len=%0d", aw_stall, in_awaddr, in_awlen); $finish; end
        if (ar_stall > HANG_LIMIT) begin stall_rep<=1;
          $display("AXIDLY HANG: AR 在 AXI4SDRAM 边界未被接受 stall=%0d addr=%h len=%0d", ar_stall, in_araddr, in_arlen); $finish; end
        if (w_stall > HANG_LIMIT) begin stall_rep<=1;
          $display("AXIDLY HANG: W 在 AXI4SDRAM 边界未被接受 stall=%0d", w_stall); $finish; end
      end
    end
  end

  // ---------------- 写：单事务 B 等式 ----------------
  reg         w_ctx, b_held;
  reg  [31:0] wt, bk;
  reg  [63:0] n_b, n_bviol;
  wire w_hs  = (in_awvalid && out_awready) || (in_wvalid && out_wready && in_wlast);
  wire b_arr = out_bvalid && !b_held && w_ctx;
  wire b_del = in_bvalid && in_bready;

  always @(posedge clock) begin
    if (reset) begin
      r_ctx<=0; r_held<=0; rt<=0; rk<=0; r_need<=0; r_got<=0; n_r<=0; n_rviol<=0; n_rmismatch<=0;
      w_ctx<=0; b_held<=0; wt<=0; bk<=0; n_b<=0; n_bviol<=0;
    end else begin
      // ---- 读 ----
      if (!r_ctx && ar_hs) begin
        r_ctx<=1; rt<=1; r_held<=0; r_got<=0; r_need<=in_arlen+8'd1;
      end else if (r_ctx) begin
        rt<=rt+32'd1;
      end
      if (r_ctx && r_arr) begin
        r_held<=1; rk<=rt;
      end
      if (r_ctx && r_deliv) begin
        r_held<=0; r_got<=r_got+8'd1;
        n_r<=n_r+64'd1;
        // 等式：交付拍 t 应为 floor(r * k)（k=该拍呈现时刻）
        if (rt != ((rk*R_S)>>S_SHIFT)) begin
          n_rviol<=n_rviol+64'd1;
          if (n_rviol < 8) $display("AXIEQ R: t1'-t0=%0d k=%0d expect=%0d (addr burst need=%0d)", rt, rk, (rk*R_S)>>S_SHIFT, r_need);
        end
        if (in_rlast) begin
          r_ctx<=0;
          if (r_got+8'd1 != r_need) begin
            n_rmismatch<=n_rmismatch+64'd1;
            if (n_rmismatch < 8) $display("AXIEQ R BURST: need=%0d got=%0d", r_need, r_got+8'd1);
          end
        end
      end
      // ---- 看门狗 ----
      if (r_ctx && (rt > HANG_LIMIT)) begin
        $display("AXIDLY HANG(WATCHDOG): read burst 超时 rt=%0d need=%0d got=%0d held=%b", rt, r_need, r_got, r_held);
        $finish;
      end
      if (w_ctx && (wt > HANG_LIMIT)) begin
        $display("AXIDLY HANG(WATCHDOG): write 事务超时 wt=%0d b_held=%b", wt, b_held);
        $finish;
      end
      // ---- 写 ----
      if (!w_ctx && w_hs) begin
        w_ctx<=1; wt<=1; b_held<=0;
      end else if (w_ctx) begin
        wt<=wt+32'd1;
      end
      if (w_ctx && b_arr) begin
        b_held<=1; bk<=wt;
      end
      if (w_ctx && b_del) begin
        b_held<=0; w_ctx<=0;
        n_b<=n_b+64'd1;
        if (wt != ((bk*R_S)>>S_SHIFT)) begin
          n_bviol<=n_bviol+64'd1;
          if (n_bviol < 8) $display("AXIEQ B: t1'-t0=%0d k=%0d expect=%0d", wt, bk, (bk*R_S)>>S_SHIFT);
        end
      end
    end
  end

  final begin
    $display("AXIDLY_CHECK: n_rbeats=%0d eq_viol_r=%0d burst_mismatch=%0d | n_b=%0d eq_viol_b=%0d  %s  (仅 PERF_DELAY 下等式有意义)",
      n_r, n_rviol, n_rmismatch, n_b, n_bviol,
      ((n_rviol+n_bviol+n_rmismatch)==0 && (n_r+n_b)>0) ? "EQUATION OK" :
        ((n_r+n_b)==0) ? "NO TXN" : "eqv(直通下预期)");
  end
endmodule

bind axi4_delayer axidly_check u_axidly_chk (
  .clock(clock), .reset(reset),
  .in_arvalid(in_arvalid), .out_arready(out_arready), .in_araddr(in_araddr), .in_arlen(in_arlen),
  .out_rvalid(out_rvalid), .in_rvalid(in_rvalid), .in_rready(in_rready), .in_rlast(in_rlast),
  .in_awvalid(in_awvalid), .out_awready(out_awready), .in_awaddr(in_awaddr), .in_awlen(in_awlen),
  .in_wvalid(in_wvalid), .out_wready(out_wready), .in_wlast(in_wlast),
  .out_bvalid(out_bvalid), .in_bvalid(in_bvalid), .in_bready(in_bready)
);
