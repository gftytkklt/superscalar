// ============================================================================
// 阶段2 仿真期断言集（bind 注入，不改动核 RTL）
// 通过 `make assert` 使用：verilator 模型加 --assert 并编入本目录 *.sv。
// 任何断言失败都会打日志并令 tb 以非 0 退出。
// ============================================================================

// ---------------------------------------------------------------------------
// [1] Bug1: I/D Cache 恒被旁路（mmio_flag 恒真）
// 属性：对"可缓存区域"(MROM/FLASH/SRAM)的请求，下一个周期绝不能进入 MMIO_*。
// 当前 RTL(dcachectrl:2014 / icachectrl:3199)下必失败；修复 cache 后应恒成立。
// ---------------------------------------------------------------------------
module cache_bypass_check_dc (
    input clk, rst,
    input rd, wr, fencei,
    input [31:0] addr,
    input [15:0] state
);
  function automatic bit cacheable(input [31:0] a);
    bit ok = 0;
    if ((a >= 32'h20000000 && a < 32'h20001000) || // MROM
        (a >= 32'h30000000 && a < 32'h31000000) || // FLASH
        (a >= 32'h0f000000 && a < 32'h0f002000))   // SRAM
      ok = 1;
    return ok;
  endfunction

  wire mmio = |(state & 16'h7800);  // MMIO_AR/AW/RD/WR
`ifndef CACHE_CHECK_OFF
  always @(posedge clk) begin
    if (!rst && rd && cacheable(addr) && !fencei)
      if (mmio) $error("DCACHE bypassed: cacheable rd @%08x hits MMIO state", addr);
    if (!rst && wr && cacheable(addr) && !fencei)
      if (mmio) $error("DCACHE bypassed: cacheable wr @%08x hits MMIO state", addr);
  end
`endif
endmodule

module cache_bypass_check_ic (
    input clk, rst,
    input rd, fencei,
    input [31:0] addr,
    input [6:0] state
);
  function automatic bit cacheable(input [31:0] a);
    bit ok = 0;
    if ((a >= 32'h20000000 && a < 32'h20001000) ||
        (a >= 32'h30000000 && a < 32'h31000000) ||
        (a >= 32'h0f000000 && a < 32'h0f002000))
      ok = 1;
    return ok;
  endfunction

  wire mmio = |(state & 7'h30);  // MMIO_AR(0x10) / MMIO_RD(0x20)
`ifndef CACHE_CHECK_OFF
  always @(posedge clk) begin
    if (!rst && rd && cacheable(addr) && !fencei)
      if (mmio) $error("ICACHE bypassed: cacheable ifetch @%08x hits MMIO state", addr);
  end
`endif
endmodule

bind ysyx_22040750_dcachectrl cache_bypass_check_dc u_dc (
  .clk(I_clk), .rst(I_rst),
  .rd(I_cpu_rd_req), .wr(I_cpu_wr_req), .fencei(I_cpu_fencei),
  .addr(I_cpu_addr), .state(current_state)
);

bind ysyx_22040750_icachectrl cache_bypass_check_ic u_ic (
  .clk(I_clk), .rst(I_rst),
  .rd(I_cpu_rd_req), .fencei(I_cpu_fencei),
  .addr(I_cpu_addr), .state(current_state)
);