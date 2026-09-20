// ============================================================================
// dcache_axi_probe —— P-D 调试：dcache 侧 AXI 写拍/读拍日志（跨级对账，干净版）
//   地址 = 行基址 + 当前拍序号*8（拍序号 AW/AR 握手清零、W/R 握手 +1，同拍用组合当前值）
//   仅记录 SDRAM 区（awaddr/araddr[31:24]==0xa0），条数上限 20000。
// ============================================================================
module dcache_axi_probe (
  input        I_clk, I_rst,
  input [31:0] O_mem_awaddr, O_mem_araddr,
  input [63:0] O_mem_wdata, I_mem_rdata,
  input [7:0]  O_mem_wstrb,
  input        O_mem_awvalid, I_mem_awready,
  input        O_mem_wvalid, I_mem_wready, O_mem_wlast,
  input        O_mem_arvalid, I_mem_arready,
  input        I_mem_rvalid, O_mem_rready, I_mem_rlast,
  input        rd_ax_hs
);
  reg [15:0] n_w, n_r, rbeat;
  reg [1:0]  dbeat;
  wire aw_hs  = O_mem_awvalid && I_mem_awready;
  wire ar_hs  = O_mem_arvalid && I_mem_arready;
  wire wr_hs  = O_mem_wvalid  && I_mem_wready;
  wire rd_hs  = I_mem_rvalid  && O_mem_rready;
  wire [1:0]  cur_wbeat = (aw_hs || rd_ax_hs) ? 2'd0 : dbeat;
  wire [15:0] cur_rbeat = rd_ax_hs ? 16'd0 : rbeat;

  always @(posedge I_clk) begin
    if (I_rst) begin n_w<=0; n_r<=0; rbeat<=0; dbeat<=0; end
    else begin
      if (aw_hs || (wr_hs && O_mem_wlast)) dbeat <= 2'd0;
      else if (wr_hs)                      dbeat <= dbeat + 2'd1;
      if (rd_ax_hs)                        rbeat <= 16'd0;
      else if (rd_hs)                      rbeat <= rbeat + 16'd1;

      if (wr_hs && n_w < 16'd20000 && (O_mem_awaddr[31:24]==8'ha0)) begin
        n_w <= n_w + 16'd1;
        $display("DCW: addr=0x%08x data=0x%016x strb=%02x last=%b", O_mem_awaddr + {27'd0, cur_wbeat, 3'b0}, O_mem_wdata, O_mem_wstrb, O_mem_wlast);
      end
      if (rd_hs && n_r < 16'd20000 && (O_mem_araddr[31:24]==8'ha0)) begin
        n_r <= n_r + 16'd1;
        $display("DCR: addr=0x%08x data=0x%016x last=%b", O_mem_araddr + {13'd0, cur_rbeat, 3'b0}, I_mem_rdata, I_mem_rlast);
      end
    end
  end
endmodule

bind ysyx_22040750_dcachectrl dcache_axi_probe u_dcaxiprobe (
  .I_clk(I_clk), .I_rst(I_rst),
  .O_mem_awaddr(O_mem_awaddr), .O_mem_araddr(O_mem_araddr),
  .O_mem_wdata(O_mem_wdata), .I_mem_rdata(I_mem_rdata), .O_mem_wstrb(O_mem_wstrb),
  .O_mem_awvalid(O_mem_awvalid), .I_mem_awready(I_mem_awready),
  .O_mem_wvalid(O_mem_wvalid), .I_mem_wready(I_mem_wready), .O_mem_wlast(O_mem_wlast),
  .O_mem_arvalid(O_mem_arvalid), .I_mem_arready(I_mem_arready),
  .I_mem_rvalid(I_mem_rvalid), .O_mem_rready(O_mem_rready), .I_mem_rlast(I_mem_rlast),
  .rd_ax_hs(rd_ax_hs)
);
