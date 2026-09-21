// ============================================================================
// tb_sdram_ctrl —— SDRAM AXI 控制器（sdram_top_axi）定向回归 TB
//
// 用途：P-D 阶段定位两个隐蔽读写缺陷，并作为其回归测试：
//   · 突发读背靠背（每 2 chip cycle 一次）——旧 sdram.v 模型"预取+保持"实现会丢偶拍
//     （表现为 arlen>0 的读每隔一拍返回 0；可缓存 32B refill / 64bit MMIO ld 均受害）。
//   · 64bit 单拍（FIXED, size=3, len=0）→ axi64to32 拆两拍时若沿用 FIXED，从端两拍落
//     同一地址（高半字覆盖低半字，sd 后 ld 得 0）。
//
// 覆盖：A 突发写+单读 / B 单写+突发读 / C 单写+单读 / D 突发写+突发读 /
//       E 读-写-读 / F 16 拍长突发 / G 跨 512 列行边界突发。
//
// 运行（Verilator）：
//   cd npc/verif/sdram && ./run.sh
// ============================================================================
`timescale 1ns/1ps
module tb;
  reg clock = 0;
  reg reset = 1;
  always #5 clock = ~clock;

  reg         in_awvalid = 0;
  wire        in_awready;
  reg  [31:0] in_awaddr = 0;
  reg  [3:0]  in_awid = 0;
  reg  [7:0]  in_awlen = 0;
  reg  [2:0]  in_awsize = 3'd2;
  reg  [1:0]  in_awburst = 2'b01;
  reg         in_wvalid = 0;
  wire        in_wready;
  reg  [31:0] in_wdata = 0;
  reg  [3:0]  in_wstrb = 4'hf;
  reg         in_wlast = 0;
  reg         in_bready = 1;
  wire        in_bvalid;
  wire [1:0]  in_bresp;
  wire [3:0]  in_bid;
  reg         in_arvalid = 0;
  wire        in_arready;
  reg  [31:0] in_araddr = 0;
  reg  [3:0]  in_arid = 0;
  reg  [7:0]  in_arlen = 0;
  reg  [2:0]  in_arsize = 3'd2;
  reg  [1:0]  in_arburst = 2'b01;
  reg         in_rready = 1;
  wire        in_rvalid;
  wire [31:0] in_rdata;
  wire [1:0]  in_rresp;
  wire        in_rlast;
  wire [3:0]  in_rid;
  wire        sdram_clk, sdram_cke, sdram_cs, sdram_ras, sdram_cas, sdram_we;
  wire [12:0] sdram_a;
  wire [1:0]  sdram_ba;
  wire [3:0]  sdram_dqm;
  wire        sdram_rank;
  wire [31:0] sdram_dq;

  sdram_top_axi dut (
    .clock(clock), .reset(reset),
    .in_awready(in_awready), .in_awvalid(in_awvalid), .in_awaddr(in_awaddr),
    .in_awid(in_awid), .in_awlen(in_awlen), .in_awsize(in_awsize), .in_awburst(in_awburst),
    .in_wready(in_wready), .in_wvalid(in_wvalid), .in_wdata(in_wdata), .in_wstrb(in_wstrb),
    .in_wlast(in_wlast), .in_bready(in_bready), .in_bvalid(in_bvalid), .in_bresp(in_bresp), .in_bid(in_bid),
    .in_arready(in_arready), .in_arvalid(in_arvalid), .in_araddr(in_araddr), .in_arid(in_arid),
    .in_arlen(in_arlen), .in_arsize(in_arsize), .in_arburst(in_arburst),
    .in_rready(in_rready), .in_rvalid(in_rvalid), .in_rdata(in_rdata), .in_rresp(in_rresp),
    .in_rlast(in_rlast), .in_rid(in_rid),
    .sdram_clk(sdram_clk), .sdram_cke(sdram_cke), .sdram_cs(sdram_cs), .sdram_ras(sdram_ras),
    .sdram_cas(sdram_cas), .sdram_we(sdram_we), .sdram_a(sdram_a), .sdram_ba(sdram_ba),
    .sdram_dqm(sdram_dqm), .sdram_rank(sdram_rank), .sdram_dq(sdram_dq)
  );

  sdram u_sdram (
    .clk(sdram_clk), .cke(sdram_cke), .cs(sdram_cs), .ras(sdram_ras), .cas(sdram_cas), .we(sdram_we),
    .rank(sdram_rank), .a(sdram_a), .ba(sdram_ba), .dqm(sdram_dqm), .dq(sdram_dq)
  );

  integer errors = 0;
  reg [31:0] wdat [0:15];
  reg [31:0] rdat [0:15];
  reg [31:0] rtmp;
  integer wlen, rlen, wi, ri;
  reg aw_drive = 0, w_drive = 0, ar_drive = 0;

  always @(posedge clock)
    if (!reset && aw_drive && in_awready) aw_drive <= 0;
  always @(posedge clock)
    if (!reset && w_drive && in_wready) begin
      if (wi == wlen-1) w_drive <= 0;
      else wi <= wi + 1;
    end
  always @(posedge clock)
    if (!reset && ar_drive && in_arready) ar_drive <= 0;

  always @(*) begin
    in_awvalid = aw_drive;
    in_awlen   = wlen[7:0] - 1;
    in_wvalid  = w_drive;
    in_wdata   = wdat[wi];
    in_wlast   = w_drive && (wi == wlen-1);
    in_wstrb   = 4'hf;
    in_arvalid = ar_drive;
    in_arlen   = rlen[7:0] - 1;
    in_arsize  = 3'd2;
    in_arburst = 2'b01;
  end

  task automatic do_write(input [31:0] addr, input integer n);
    begin
      in_awaddr = addr; wlen = n; wi = 0;
      aw_drive = 1; w_drive = 1;
      wait (!aw_drive);
      wait (!w_drive);
      wait (in_bvalid);
      @(posedge clock);
    end
  endtask

  task automatic do_read(input [31:0] addr, input integer n);
    begin
      in_araddr = addr; rlen = n;
      ar_drive = 1;
      wait (!ar_drive);
      for (ri = 0; ri < n; ri = ri + 1) begin
        @(posedge clock);
        while (!in_rvalid) @(posedge clock);
        if (n == 1) rtmp = in_rdata; else rdat[ri] = in_rdata;
        @(posedge clock);
      end
    end
  endtask

  task automatic check(input [31:0] base, input integer n, input [127:0] tag);
    begin
      for (ri = 0; ri < n; ri = ri + 1)
        if (rdat[ri] !== wdat[ri]) begin
          $display("[TB] %0s MISMATCH beat %0d addr=%h exp=%h got=%h", tag, ri, base+4*ri, wdat[ri], rdat[ri]);
          errors = errors + 1;
        end
    end
  endtask

  integer i;
  initial begin
    #3000000;
    $display("[TB] GLOBAL TIMEOUT (hang)");
    $finish;
  end
  initial begin
    repeat (20) @(posedge clock);
    reset = 0;
    repeat (20) @(posedge clock);
    #150000;   // SDRAM 控制器上电初始化 100us（CKE/PRECHARGE/REFRESH/LMR）

    // A: burst write 8, then 8 single reads
    $display("[TB] A burstW + singleR");
    for (i = 0; i < 8; i = i + 1) wdat[i] = 32'h11110000 + i;
    do_write(32'ha0004400, 8);
    for (i = 0; i < 8; i = i + 1) begin
      do_read(32'ha0004400 + 4*i, 1);
      rdat[i] = rtmp;
    end
    check(32'ha0004400, 8, "A");

    // B: 8 single writes, then burst read
    $display("[TB] B singleW + burstR");
    for (i = 0; i < 8; i = i + 1) wdat[i] = 32'h22220000;
    for (i = 0; i < 8; i = i + 1) do_write(32'ha0004480 + 4*i, 1);
    do_read(32'ha0004480, 8);
    check(32'ha0004480, 8, "B");

    // C: 4 single writes, then 4 single reads
    $display("[TB] C singleW + singleR");
    for (i = 0; i < 4; i = i + 1) wdat[i] = 32'h33330000;
    for (i = 0; i < 4; i = i + 1) do_write(32'ha0006400 + 4*i, 1);
    for (i = 0; i < 4; i = i + 1) begin
      do_read(32'ha0006400 + 4*i, 1);
      rdat[i] = rtmp;
    end
    check(32'ha0006400, 4, "C");

    // D: burst4 write, then burst4 read
    $display("[TB] D burstW + burstR");
    for (i = 0; i < 4; i = i + 1) wdat[i] = 32'h44440000 + i;
    do_write(32'ha0006480, 4);
    do_read(32'ha0006480, 4);
    check(32'ha0006480, 4, "D");

    // E: burst write -> burst read -> burst write -> burst read (read/write 交替)
    $display("[TB] E W-R-W-R");
    for (i = 0; i < 4; i = i + 1) wdat[i] = 32'h55550000 + i;
    do_write(32'ha0005000, 4);
    do_read(32'ha0005000, 4);
    for (i = 0; i < 4; i = i + 1) wdat[i] = 32'h66660000 + i;
    do_write(32'ha0005000, 4);
    do_read(32'ha0005000, 4);
    check(32'ha0005000, 4, "E");

    // F: 16-beat burst
    $display("[TB] F burst16");
    for (i = 0; i < 16; i = i + 1) wdat[i] = 32'h77770000 + i;
    do_write(32'ha0007000, 16);
    do_read(32'ha0007000, 16);
    check(32'ha0007000, 16, "F");

    // G: burst crossing 512-column row boundary (col 0x1FF -> next row)
    $display("[TB] G row-cross");
    for (i = 0; i < 4; i = i + 1) wdat[i] = 32'h88880000 + i;
    do_write(32'ha0001ffc, 4);
    do_read(32'ha0001ffc, 4);
    check(32'ha0001ffc, 4, "G");

    if (errors == 0) $display("[TB] ALL PASS");
    else $display("[TB] FAILURES: %0d", errors);
    $finish;
  end
endmodule
