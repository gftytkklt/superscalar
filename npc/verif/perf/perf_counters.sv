// ============================================================================
// 性能计数器（B3 阶段1）—— 非侵入式：bind 注入 + 纯仿真 $display，不改核 RTL。
//
// 与 assert/*.sv 的 bind 注入一致：单独 .sv，用 bind 挂到 ysyx_22040750_cpu_core，
// 仿真结束在 final 块汇总 $display。计数器不参与流片（无流片信号，纯仿真观测）。
//
// 事件定义（与讲义性能模型对应）：
//   ifu_deliver : IFU 取指令（总交付）        = icache 交付指令（I_inst_valid 上升拍）
//                   含分支/跳转后被冲刷的"取指槽"（bubble 取指），反映指令供给工作负载；
//   decode_*/总 : 译码出各类别指令（真实指令） = IF_ID_valid 且 ID_EX 接收(一次性)、非 bubble，
//                   按 decoder 控制字分成 mem/csr/branch/compute/other；
//   ifu_fetch   : IFU 取到指令（有效）         = decode_总（每条被真正取入并译码执行的指令，
//                   与 bubble 取指区分）；用于与动态指令数/译码总数的一致性对照；
//   lsu_data    : LSU 取到数据                 = cache 返回读数据（I_mem_rd_data_valid 上升拍）；
//   exu_compute : EXU 完成计算                 = ALU 完成一次计算（alu_out_valid 上升拍）；
//   retire      : 动态指令数                   = WB 提交（difftest_valid），一致性基准。
//
// 一致性检查（讲义）：decode_总 == ifu_fetch == retire；若 ifu_deliver 更大则说明存在
// 分支/跳转引起的"冲刷取指"（差 ≈ bubble 数），属微结构代价，应单独归因，非计数器错误。
// ============================================================================
module perf_counters #(
)(
  input I_clk, I_rst,
  input I_inst_valid,              // IFU 指令有效（cpu_core 端口）
  input I_mem_rd_data_valid,       // 读数据有效（cpu_core 端口）
  input IF_ID_valid, ID_EX_allowin, IF_ID_bubble,
  input ID_EX_valid, EX_MEM_allowin, ID_EX_bubble,
  input [3:0] dnpc_sel,
  input mem_wen,
  input [8:0] mem_rstrb,
  input csr_wen, csr_mret, csr_intr,
  input reg_wen,
  input [31:0] MEM_WB_inst,
  input MEM_WB_valid,
  input difftest_valid
);
  reg [63:0] c_deliver, c_lsu, c_exu, c_ret, c_decode_total;
  reg [63:0] c_mem, c_csr, c_branch, c_compute, c_other, c_bubble;

  wire decode_ev = IF_ID_valid && ID_EX_allowin && !IF_ID_bubble;
  wire decode_bubble = IF_ID_valid && ID_EX_allowin && IF_ID_bubble;
  // EXU 完成计算 = 指令离开 EX 进入 MEM（每条真实指令 EX 段执行一次；排除 bubble，
  // 使 EXU 计数与动态指令数一致；单周期 ALU 的 alu_out_valid 恒为 1 不可用）。
  wire exu_ev = ID_EX_valid && EX_MEM_allowin && !ID_EX_bubble;

  always @(posedge I_clk) begin
    if (I_rst) begin
      c_deliver<=0; c_lsu<=0; c_exu<=0; c_ret<=0; c_decode_total<=0;
      c_mem<=0; c_csr<=0; c_branch<=0; c_compute<=0; c_other<=0; c_bubble<=0;
    end else begin
      if (I_inst_valid)        c_deliver <= c_deliver + 64'd1;
      if (I_mem_rd_data_valid) c_lsu     <= c_lsu     + 64'd1;
      if (exu_ev)              c_exu     <= c_exu     + 64'd1;
      if (difftest_valid)      c_ret     <= c_ret     + 64'd1;
      if (decode_bubble)       c_bubble  <= c_bubble  + 64'd1;
      if (decode_ev) begin
        c_decode_total <= c_decode_total + 64'd1;
        if (mem_wen | (|mem_rstrb))              c_mem    <= c_mem    + 64'd1;
        else if (csr_wen | csr_mret | csr_intr)  c_csr    <= c_csr    + 64'd1;
        else if (!dnpc_sel[0])                   c_branch <= c_branch + 64'd1;
        else if (reg_wen)                        c_compute<= c_compute+ 64'd1;
        else                                     c_other  <= c_other  + 64'd1;
      end
    end
  end

  // 周期性进度快照：每 DUMP_CYCLES 打印一次当前计数（长仿真可随时 Ctrl-C 查看进度）。
  // 与 soctest.cpp 的周期 fflush 配合，使重定向到文件的日志也能及时落盘。
  localparam DUMP_CYCLES = 32'd5000000;
  reg [31:0] cyc;
  always @(posedge I_clk) begin
    if (I_rst) cyc <= 32'd0;
    else cyc <= (cyc == DUMP_CYCLES - 1) ? 32'd0 : cyc + 32'd1;
  end
  always @(posedge I_clk) if (!I_rst && (cyc == DUMP_CYCLES - 1)) begin
    $display("PERF[snap @ %0d]: deliver=%0d decode=%0d retire=%0d lsu=%0d exu=%0d | mem=%0d csr=%0d branch=%0d compute=%0d other=%0d bubble=%0d",
      cyc, c_deliver, c_decode_total, c_ret, c_lsu, c_exu,
      c_mem, c_csr, c_branch, c_compute, c_other, c_bubble);
  end

  // ebreak：MEM_WB_inst == 0x00100073，即 HIT GOOD TRAP 前一拍（retire 中 ebreak 未计入 c_ret）
  wire ebreak = (MEM_WB_inst == 32'h00100073) && MEM_WB_valid && !I_rst;
  always @(posedge I_clk) if (ebreak) begin
    $display("PERF[ebreak]: ifu_deliver=%0d decode_total=%0d ifu_fetch=%0d retire=%0d lsu=%0d exu=%0d",
      c_deliver, c_decode_total, c_decode_total, c_ret + 64'd1, c_lsu, c_exu);
    $display("PERF[ebreak]  consistency: decode_total(%0d)==ifu_fetch(%0d)==retire(%0d) ; deliver-decode=%0d (bubble=%0d)",
      c_decode_total, c_decode_total, c_ret + 64'd1,
      (c_deliver>c_decode_total)?(c_deliver-c_decode_total):(c_decode_total-c_deliver), c_bubble);
    $display("PERF[ebreak]  classes: mem=%0d csr=%0d branch=%0d compute=%0d other=%0d bubble=%0d",
      c_mem, c_csr, c_branch, c_compute, c_other, c_bubble);
  end

  final begin
    $display("PERF[final]: ifu_deliver=%0d decode_total=%0d retire=%0d lsu=%0d exu=%0d",
      c_deliver, c_decode_total, c_ret, c_lsu, c_exu);
  end
endmodule

bind ysyx_22040750_cpu_core perf_counters u_perf (
  .I_clk(I_sys_clk), .I_rst(I_rst),
  .I_inst_valid(I_inst_valid),
  .I_mem_rd_data_valid(I_mem_rd_data_valid),
  .IF_ID_valid(IF_ID_valid), .ID_EX_allowin(ID_EX_allowin), .IF_ID_bubble(IF_ID_bubble),
  .ID_EX_valid(ID_EX_valid), .EX_MEM_allowin(EX_MEM_allowin), .ID_EX_bubble(ID_EX_bubble),
  .dnpc_sel(dnpc_sel), .mem_wen(mem_wen), .mem_rstrb(mem_rstrb),
  .csr_wen(csr_wen), .csr_mret(csr_mret), .csr_intr(csr_intr),
  .reg_wen(reg_wen),
  .MEM_WB_inst(MEM_WB_inst), .MEM_WB_valid(MEM_WB_valid),
  .difftest_valid(difftest_valid)
);
