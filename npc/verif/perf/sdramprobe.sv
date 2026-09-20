// ============================================================================
// sdramprobe —— P-D 调试辅助：SDRAM 从端（sdram_top_axi）突发语义 + 影子内存对账
//   ① 突发语义：AW(awlen)↔W 拍数/wlast；AR(arlen)↔R 拍数/rlast
//   ② 影子内存：记录从端收到的写数据（按字节 wstrb），读回逐字节比对 → 区分写错/读错
//   ③ 挂起看门狗：写/读事务超 10 万周期未完成 → 现场 + $finish
// 覆盖：SDRAM 前 4MB（addr[21:2]，bf 堆所在）；越界不记不比。
// ============================================================================
module sdramprobe (
  input        clock, reset,
  input        in_awvalid, in_awready, input [31:0] in_awaddr, input [7:0] in_awlen,
  input        in_wvalid, in_wready, input [31:0] in_wdata, input [3:0] in_wstrb, input in_wlast,
  input        in_bvalid, in_bready,
  input        in_arvalid, in_arready, input [31:0] in_araddr, input [7:0] in_arlen,
  input        in_rvalid, in_rready, input [31:0] in_rdata, input in_rlast
);
  localparam int HANG_LIMIT  = 90000;   // 比其它看门狗早 1 万拍，确保本探针先报（多狗竞速）
  localparam int SHADOW_WORDS = 1048576;   // 4MB/4B

  reg [31:0] shadow [0:SHADOW_WORDS-1];
  reg [3:0]  smask  [0:SHADOW_WORDS-1];

  reg         w_rep, r_rep, wlast_seen;
  reg [15:0]  base_log;      // 基址区(0xa0000000..0x1ff)访问日志条数上限
  reg [31:0]  aw_addr_q, ar_addr_q, w_wait, r_wait, n_rmis;
  reg [7:0]   aw_len_q, ar_len_q, w_cnt, r_cnt;
  reg [19:0]  w_idx_q, r_idx_q;     // 当前拍的字索引（addr[21:2]）
  reg         wr_open, rd_open;
  reg [31:0]  aw_wait, arw_wait, rd_done_cnt, wr_done_cnt;
  reg         aw_rep, arw_rep;
  integer     k;

  wire aw_hs = in_awvalid && in_awready;
  wire w_hs  = in_wvalid  && in_wready;
  wire b_hs  = in_bvalid  && in_bready;
  wire ar_hs = in_arvalid && in_arready;
  wire r_hs  = in_rvalid  && in_rready;

  // 当前拍索引（AW/AR 同拍时以新事务地址为准）
  wire [19:0] w_cur = aw_hs ? in_awaddr[21:2] : w_idx_q;
  wire [19:0] r_cur = ar_hs ? in_araddr[21:2] : r_idx_q;
  wire [19:0] w_cur_idx = aw_hs ? in_awaddr[21:2] : w_idx_q;
  wire [19:0] r_cur_idx = ar_hs ? in_araddr[21:2] : r_idx_q;
  wire w_rng = (aw_hs ? in_awaddr : {10'h0, w_idx_q, 2'b0}) >= 32'ha0000000 &&
               (aw_hs ? in_awaddr : {10'h0, w_idx_q, 2'b0}) <  32'ha0400000;
  wire r_rng = (ar_hs ? in_araddr : {10'h0, r_idx_q, 2'b0}) >= 32'ha0000000 &&
               (ar_hs ? in_araddr : {10'h0, r_idx_q, 2'b0}) <  32'ha0400000;

  always @(posedge clock) begin
    if (reset) begin
      w_rep<=0; r_rep<=0; wlast_seen<=0; wr_open<=0; rd_open<=0;
      aw_addr_q<=0; aw_len_q<=0; w_cnt<=0; w_wait<=0; w_idx_q<=0;
      ar_addr_q<=0; ar_len_q<=0; r_cnt<=0; r_wait<=0; r_idx_q<=0; n_rmis<=0;
      aw_wait<=0; arw_wait<=0; aw_rep<=0; arw_rep<=0; rd_done_cnt<=0; wr_done_cnt<=0;
    end else begin
      // ---- 控制器边界：AW/AR 长期未被接受（多狗竞速中本探针阈值最低，最先报）----
      if (!aw_rep) begin
        if (in_awvalid && !in_awready) aw_wait<=aw_wait+32'd1; else aw_wait<=0;
        if (aw_wait > HANG_LIMIT) begin aw_rep<=1;
          $display("SDRAMPROBE AW-PENDING: 控制器 awready 长期为低 awaddr=0x%08x awlen=%0d awvalid=%b | 已完读=%0d 已完写=%0d rd_open=%b wr_open=%b",
                    in_awaddr, in_awlen, in_awvalid, rd_done_cnt, wr_done_cnt, rd_open, wr_open);
          $finish; end
      end
      if (!arw_rep) begin
        if (in_arvalid && !in_arready) arw_wait<=arw_wait+32'd1; else arw_wait<=0;
        if (arw_wait > HANG_LIMIT) begin arw_rep<=1;
          $display("SDRAMPROBE AR-PENDING: 控制器 arready 长期为低 araddr=0x%08x arlen=%0d arvalid=%b | 已完读=%0d 已完写=%0d rd_open=%b wr_open=%b",
                    in_araddr, in_arlen, in_arvalid, rd_done_cnt, wr_done_cnt, rd_open, wr_open);
          $finish; end
      end
      // ---------------- B：基址区访问日志（0xa0000000..0x1ff）----------------
      if (base_log < 16'd60000) begin
        if (w_hs && (aw_addr_q[31:14] == 18'h28000)) begin
          base_log <= base_log + 16'd1;
          $display("BASE W: addr=0x%08x data=0x%08x strb=%b last=%b", {10'h0, w_cur_idx, 2'b0}, in_wdata, in_wstrb, in_wlast);
        end
        if (r_hs && (ar_addr_q[31:14] == 18'h28000)) begin
          base_log <= base_log + 16'd1;
          $display("BASE R: addr=0x%08x data=0x%08x last=%b", {10'h0, r_cur_idx, 2'b0}, in_rdata, in_rlast);
        end
      end
      // ---------------- 写 ----------------
      if (aw_hs) begin
        wr_open<=1; aw_addr_q<=in_awaddr; aw_len_q<=in_awlen; w_wait<=0;
        w_idx_q <= in_awaddr[21:2] + (w_hs ? 20'd1 : 20'd0);
        w_cnt   <= w_hs ? 8'd1 : 8'd0;
        wlast_seen <= w_hs ? in_wlast : 1'b0;
      end else if (w_hs) begin
        w_cnt   <= w_cnt + 8'd1;
        w_idx_q <= w_idx_q + 20'd1;
        if (in_wlast) wlast_seen<=1;
      end
      // 影子写
      if (w_hs && w_rng)
        for (k=0;k<4;k=k+1)
          if (in_wstrb[k]) begin
            shadow[w_cur][8*k +: 8] <= in_wdata[8*k +: 8];
            smask [w_cur][k]        <= 1'b1;
          end
      if (b_hs) begin
        wr_open<=0; wr_done_cnt<=wr_done_cnt+32'd1;
        if ((w_cnt != (aw_len_q + 8'd1)) || !wlast_seen)
          $display("SDRAMPROBE W-BURST MISMATCH: awaddr=0x%08x awlen=%0d(期望%0d拍) 实收=%0d wlast=%b",
                    aw_addr_q, aw_len_q, aw_len_q+8'd1, w_cnt, wlast_seen);
      end
      if (wr_open) begin
        w_wait<=w_wait+32'd1;
        if (!w_rep && (w_wait > HANG_LIMIT)) begin
          w_rep<=1;
          $display("SDRAMPROBE W-STUCK: awaddr=0x%08x awlen=%0d 已收W拍=%0d wlast=%b wvalid=%b wready=%b",
                    aw_addr_q, aw_len_q, w_cnt, wlast_seen, in_wvalid, in_wready);
          $finish;
        end
      end else w_wait<=0;

      // ---------------- 读 ----------------
      if (ar_hs) begin
        rd_open<=1; ar_addr_q<=in_araddr; ar_len_q<=in_arlen; r_wait<=0;
        r_idx_q <= in_araddr[21:2] + (r_hs ? 20'd1 : 20'd0);
        r_cnt   <= r_hs ? 8'd1 : 8'd0;
      end else if (r_hs) begin
        r_cnt   <= r_cnt + 8'd1;
        r_idx_q <= r_idx_q + 20'd1;
      end
      if (r_hs && r_rng)
        for (k=0;k<4;k=k+1)
          if (smask[r_cur][k] && (shadow[r_cur][8*k +: 8] !== in_rdata[8*k +: 8])) begin
            n_rmis <= n_rmis + 32'd1;
            if (n_rmis < 20)
              $display("SDRAMPROBE RD-MISMATCH: addr=0x%08x byte%0d 期望=0x%02x 实收=0x%02x (arlen=%0d beat=%0d)",
                        {10'h0, r_cur, 2'b0}, k, shadow[r_cur][8*k +: 8], in_rdata[8*k +: 8], ar_len_q, r_cnt);
          end
      if (r_hs && in_rlast) begin
        rd_open<=0; rd_done_cnt<=rd_done_cnt+32'd1;
        if (r_cnt != ar_len_q)
          $display("SDRAMPROBE R-BURST MISMATCH: araddr=0x%08x arlen=%0d(期望%0d拍) 实收=%0d",
                    ar_addr_q, ar_len_q, ar_len_q+8'd1, r_cnt+8'd1);
      end
      if (rd_open) begin
        r_wait<=r_wait+32'd1;
        if (!r_rep && (r_wait > HANG_LIMIT)) begin
          r_rep<=1;
          $display("SDRAMPROBE R-STUCK: araddr=0x%08x arlen=%0d 已收R拍=%0d rvalid=%b rready=%b",
                    ar_addr_q, ar_len_q, r_cnt, in_rvalid, in_rready);
          $finish;
        end
      end else r_wait<=0;
    end
  end
endmodule

bind sdram_top_axi sdramprobe u_sdramprobe (
  .clock(clock), .reset(reset),
  .in_awvalid(in_awvalid), .in_awready(in_awready), .in_awaddr(in_awaddr), .in_awlen(in_awlen),
  .in_wvalid(in_wvalid), .in_wready(in_wready), .in_wdata(in_wdata), .in_wstrb(in_wstrb), .in_wlast(in_wlast),
  .in_bvalid(in_bvalid), .in_bready(in_bready),
  .in_arvalid(in_arvalid), .in_arready(in_arready), .in_araddr(in_araddr), .in_arlen(in_arlen),
  .in_rvalid(in_rvalid), .in_rready(in_rready), .in_rdata(in_rdata), .in_rlast(in_rlast)
);
