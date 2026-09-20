// ============================================================================
// apbdly_check —— E1d：APB 延迟校准等式运行时自检（桥侧）
//
// 等式自检：在桥自身干净信号上测 t0/t1/t1'，校验 (t1-t0)*r == t1'-t0。
//   t0 = in_psel && in_penable 首次为高（访问开始）
//   t1 = out_pready（从机响应，桥收到）
//   t1'= in_pready（桥把响应呈现给主机）
//   k  = t1 - t0；期望 t1'-t0 == floor(r*k)
//
// ⚠️ 仅 PERF_DELAY（make perf）下有意义：直通时无延迟，t1'=t1，等式必然"violate"，
//    属预期；此时本模块只作事务统计，请勿当作故障。dummy 金标准已移除（测试程序相关）。
// ============================================================================
module apbdly_check (
  input clock, reset,
  input in_psel, in_penable,
  input in_pwrite,
  input [31:0] in_paddr,
  input out_pready, in_pready,
  input [31:0] in_prdata
);
  localparam int R_S = 7, S_SHIFT = 1;           // r = 3.5
  // 挂起看门狗阈值（周期）：最长合法等待 = flash XIP refill ≈4,529cyc（dcache 实测），
  // 经延迟桥呈现 ≤ 3.5×4,529 ≈ 15,852；refill+写回复合 ≤ ~3.2 万。取 10 万（≈3× 余量），
  // 超过即判死锁：打印现场并结束仿真，便于快速定位（详见面调试记录）。
  localparam int HANG_LIMIT = 100000;

  reg        prev_active, in_tq, have_k, g_done;
  reg [31:0] t, k_latch, last_paddr;
  reg [63:0] n_txn, n_viol, sum_exp, sum_act, sum_k;
  reg [31:0] max_k;

  wire acc_start = !prev_active && in_psel && in_penable;
  reg [31:0] wait_slave;
  reg hang_reported;
  // 看门狗：①从设备迟迟不响应 ②延迟桥迟迟不呈现（均为死锁特征）
  always @(posedge clock) begin
    if (reset) begin wait_slave <= 0; hang_reported <= 0; end
    else if (acc_start) wait_slave <= 32'd1;
    else if (in_psel && in_penable && !out_pready) wait_slave <= wait_slave + 32'd1;
    else if (!hang_reported) wait_slave <= 0;
    if (!reset && !hang_reported && (wait_slave > HANG_LIMIT)) begin
      hang_reported <= 1;
      $display("APBDLY HANG(WATCHDOG): APB 从设备无响应 wait=%0d addr=0x%08x %s in_psel=%b in_pen=%b out_pready=%b",
                wait_slave, in_paddr, in_pwrite?"W":"R", in_psel, in_penable, out_pready);
      $finish;
    end
  end

  always @(posedge clock) begin
    if (reset) begin
      prev_active <= 0; in_tq <= 0; have_k <= 0; g_done <= 0;
      t <= 0; k_latch <= 0; last_paddr <= 0;
      n_txn <= 0; n_viol <= 0; sum_exp <= 0; sum_act <= 0; sum_k <= 0; max_k <= 0;
    end else begin
      prev_active <= in_psel && in_penable;

      if (acc_start && !in_tq) begin
        in_tq <= 1; t <= 1; have_k <= 0; g_done <= 0; last_paddr <= in_paddr;
      end else if (in_tq) begin
        t <= t + 1;
        if (out_pready && !have_k) begin
          k_latch <= t; have_k <= 1;
          if (t > max_k) max_k <= t;
        end
        // 完成拍：in_pready 首次为高（g_done 防止电平重复触发）
        if (in_pready && have_k && !g_done) begin
          g_done <= 1;
          n_txn  <= n_txn + 1;
          sum_exp <= sum_exp + {32'b0, (k_latch*R_S)>>S_SHIFT};
          sum_act <= sum_act + {32'b0, t};
          sum_k   <= sum_k   + {32'b0, k_latch};
          if (t != ((k_latch*R_S)>>S_SHIFT)) begin
            n_viol <= n_viol + 1;
            if (n_txn < 8) $display("EQ t1'-t0=%0d k=%0d expect=%0d diff=%0d", t, k_latch, (k_latch*R_S)>>S_SHIFT, t-((k_latch*R_S)>>S_SHIFT));
          end
          if (!in_pready) in_tq <= 0;   // 若 pready 已回落即可结束；否则延续到回落
        end
        // 事务结束：完成且 pready 回落
        if (g_done && !in_pready) begin
          in_tq <= 0; have_k <= 0;
        end
      end
    end
  end

  final begin
    $display("APBDLY_CHECK: n_txn=%0d eq_viol=%0d avg_k=%0d avg_exp=%0d avg_t1'=%0d max_k=%0d  %s  (仅 PERF_DELAY 下等式有意义)",
      n_txn, n_viol, (n_txn!=0)?sum_k/n_txn:0, (n_txn!=0)?sum_exp/n_txn:0,
      (n_txn!=0)?sum_act/n_txn:0, max_k,
      (n_viol==0 && n_txn>0) ? "EQUATION OK" : (n_txn==0)? "NO TXN" : "eqv(直通下预期)");
  end
endmodule

bind apb_delayer apbdly_check u_apbdly_chk (
  .clock(clock), .reset(reset),
  .in_psel(in_psel), .in_penable(in_penable),
  .in_pwrite(in_pwrite), .in_paddr(in_paddr),
  .out_pready(out_pready), .in_pready(in_pready),
  .in_prdata(in_prdata)
);
