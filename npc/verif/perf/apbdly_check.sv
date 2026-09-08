// ============================================================================
// apbdly_check —— E1d：APB 延迟校准运行时自检（桥侧 + golden 参考比对）
//
// ① golden 参考比对（数据正确性）：dummy 从 0x30000000 起的指令字参考表。
//    物理配对：读事务的【请求地址 in_paddr @ t0】 ↔ 【返回数据 in_prdata @ 完成拍】。
//    因为 bridge 锁存的就是 t0 地址对应的数据，故用 t0 的 last_paddr 比对。
//    命中代码段则比对 GOLDEN，有误立即报 >GOLDEN MISMATCH。
// ② 等式自检：在桥侧干净信号上测 t0/t1/t1'，校验 (t1-t0)*r == t1'-t0。
//    （t0=in_psel&&in_penable 首高；t1=out_pready；t1'=in_pready；k=t1-t0）
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
  localparam int CODE_BASE  = 32'h30000000;
  localparam int CODE_WORDS = 60;

  // ---- golden 参考表（dummy .bin，0x30000000 起）----
  const int unsigned GOLDEN[CODE_WORDS] = '{
    32'h00000413,32'hdf001117,32'h7fc10113,32'h094000ef,
    32'h00000513,32'h00008067,32'h100007b7,32'h0037c703,
    32'h03600613,32'h100006b7,32'h08076713,32'h00e781a3,
    32'h10000737,32'h00c70023,32'h000680a3,32'h0037c703,
    32'h07f77713,32'h00e781a3,32'h00008067,32'hdf000517,
    32'hfb450513,32'hdf000617,32'hfac60613,32'hff010113,
    32'h40a60633,32'h00000597,32'h09458593,32'h00113423,
    32'h058000ef,32'hdf000797,32'hf8c78793,32'hdf000717,
    32'hf8470713,32'h00e7f863,32'h00178793,32'hfe078fa3,
    32'hfee79ce3,32'h00813083,32'h01010113,32'h00008067,
    32'hff010113,32'h00113423,32'hf71ff0ef,32'hfa1ff0ef,
    32'h00000517,32'h04050513,32'hf59ff0ef,32'h00050513,
    32'h00100073,32'h0000006f,32'h02060063,32'h00050793,
    32'h00c58633,32'h0005c703,32'h00158593,32'h00178793,
    32'hfee78fa3,32'hfec598e3,32'h00008067,32'h00000000 };

  reg        prev_active, in_tq, have_k, g_done;
  reg [31:0] t, k_latch, last_paddr;
  reg [63:0] n_txn, n_viol, sum_exp, sum_act, sum_k;
  reg [31:0] max_k;
  reg [63:0] n_golden_chk, n_golden_bad;

  wire acc_start = !prev_active && in_psel && in_penable;

  always @(posedge clock) begin
    if (reset) begin
      prev_active <= 0; in_tq <= 0; have_k <= 0; g_done <= 0;
      t <= 0; k_latch <= 0; last_paddr <= 0;
      n_txn <= 0; n_viol <= 0; sum_exp <= 0; sum_act <= 0; sum_k <= 0; max_k <= 0;
      n_golden_chk <= 0; n_golden_bad <= 0;
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

          // golden：t0 请求地址 ↔ 完成拍返回数据
          if (!in_pwrite && (last_paddr >= CODE_BASE)
              && (((last_paddr - CODE_BASE) >> 2) < CODE_WORDS)) begin
            n_golden_chk <= n_golden_chk + 1;
            if (in_prdata !== GOLDEN[(last_paddr - CODE_BASE) >> 2]) begin
              n_golden_bad <= n_golden_bad + 1;
              if (n_golden_bad <= 8)
                $display(">GOLDEN MISMATCH: t0addr=0x%08x got=0x%08x want=0x%08x (t1'=%0d k=%0d)",
                  last_paddr, in_prdata, GOLDEN[(last_paddr-CODE_BASE)>>2], t, k_latch);
            end
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
    $display("APBDLY_CHECK: n_txn=%0d eq_viol=%0d avg_k=%0d avg_exp=%0d avg_t1'=%0d max_k=%0d  %s",
      n_txn, n_viol, (n_txn!=0)?sum_k/n_txn:0, (n_txn!=0)?sum_exp/n_txn:0,
      (n_txn!=0)?sum_act/n_txn:0, max_k,
      (n_viol==0 && n_txn>0) ? "EQUATION OK" : (n_txn==0)? "NO TXN" : "EQUATION VIOLATED");
    $display("GOLDEN: checked=%0d bad=%0d  %s",
      n_golden_chk, n_golden_bad,
      (n_golden_bad==0 && n_golden_chk>0) ? "ALL CODE-READ DATA MATCH" :
      (n_golden_chk==0)?"NO CODE READ":"*** DATA MISMATCH ***");
  end
endmodule

bind apb_delayer apbdly_check u_apbdly_chk (
  .clock(clock), .reset(reset),
  .in_psel(in_psel), .in_penable(in_penable),
  .in_pwrite(in_pwrite), .in_paddr(in_paddr),
  .out_pready(out_pready), .in_pready(in_pready),
  .in_prdata(in_prdata)
);
