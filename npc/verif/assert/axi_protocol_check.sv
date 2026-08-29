// ============================================================================
// AXI 通道协议断言（仿真期，bind 注入，不改核 RTL）
//
// [1] ARVALID 保持到 ARREADY 握手
//     AXI 规范：VALID 置位后，在 READY&&VALID 握手完成前不得撤销。
//     S1.5 解耦后 arvalid = rd_ax_busy（寄存器，握手才清），本断言应恒成立。
// [2] 可缓存区请求必须 32B burst；MMIO 请求必须单拍
//     可缓存区(PSRAM) miss 时 cache 发 arlen=3(size=3)；MMIO 发 arlen=0。
// ============================================================================
module axi_arvalid_hold (
    input clk, rst,
    input arvalid, arready
);
  reg arvalid_d, arready_d;
  always @(posedge clk) begin
    arvalid_d <= arvalid;
    arready_d <= arready;
  end
  // AXI 规范: 上一拍 arvalid 且未握手(arready=0), 本拍 arvalid 必须保持。
  // (arvalid 在握手当拍撤销是合法的; 从端回 R 时 arready 变 0 与本断言无关)
  always @(posedge clk) begin
    if (!rst && arvalid_d && !arready_d && !arvalid)
      $error("AXI: ARVALID dropped before ARREADY handshake");
  end
endmodule

module axi_cacheable_burst (
    input clk, rst,
    input arvalid, arready,
    input cacheable,       // 1: 可缓存区(burst)事务
    input mmio_single,     // 1: MMIO 单拍事务
    input [7:0] arlen
);
  always @(posedge clk) begin
    if (!rst && arvalid && arready && cacheable && !mmio_single)
      if (arlen != 8'd3)
        $error("AXI: cacheable req must be 32B burst (arlen=3), got %0d", arlen);
    if (!rst && arvalid && arready && mmio_single)
      if (arlen != 8'd0)
        $error("AXI: MMIO req must be single beat (arlen=0), got %0d", arlen);
  end
endmodule

// ---- bind dcachectrl ----
bind ysyx_22040750_dcachectrl axi_arvalid_hold u_dc_arh (
  .clk(I_clk), .rst(I_rst),
  .arvalid(O_mem_arvalid), .arready(I_mem_arready)
);
bind ysyx_22040750_dcachectrl axi_cacheable_burst u_dc_cb (
  .clk(I_clk), .rst(I_rst),
  .arvalid(O_mem_arvalid), .arready(I_mem_arready),
  .cacheable(~mmio_process), .mmio_single(mmio_process),
  .arlen(O_mem_arlen)
);

// ---- bind icachectrl ----
bind ysyx_22040750_icachectrl axi_arvalid_hold u_ic_arh (
  .clk(I_clk), .rst(I_rst),
  .arvalid(O_mem_arvalid), .arready(I_mem_arready)
);
bind ysyx_22040750_icachectrl axi_cacheable_burst u_ic_cb (
  .clk(I_clk), .rst(I_rst),
  .arvalid(O_mem_arvalid), .arready(I_mem_arready),
  .cacheable(~mmio_process), .mmio_single(mmio_process),
  .arlen(O_mem_arlen)
);