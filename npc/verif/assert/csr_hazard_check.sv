// ---------------------------------------------------------------------------
// [3] Bug2: CSR 写读冒险（RAW）
// 在 ID 发出一次对 MEPC 的读（且未被停顿）时必须看到"按程序序应读到的新值"：
//   最新未提交写值(优先 WB->MEM->EX 段) else 已提交值。
// 当前 RTL(csr_foward 用译码快照 ID_EX_csr 前递)在 EX 段窗口必然违背，断言失败。
// 只针对 MEPC 演示；推广到任意 CSR 可把 committed 数组化。
// ---------------------------------------------------------------------------
module csr_hazard_check (
    input clk, rst,
    // 本拍 ID 发出的读
    input id_valid, id_stall, id_bubble,
    input [11:0] id_csr_addr,
    input [63:0] csr_forward,
    // EX 段正在计算的写
    input ex_csr_wen, input [11:0] ex_csr_addr, input [63:0] alu_csr_data,
    // MEM 段（未提交）的写
    input mem_csr_wen, input [11:0] mem_csr_addr, input [63:0] mem_csr,
    // WB 段（未提交）的写
    input wb_csr_wen, input [11:0] wb_csr_addr, input [63:0] wb_csr,
    input wb_valid
);
  localparam MEPC = 12'h341;

  // 已提交到 CSR 寄存器的最近值
  reg [63:0] committed;
  always @(posedge clk) begin
    if (rst)                             committed <= 0;
    else if (wb_valid && wb_csr_wen && wb_csr_addr == MEPC)
                                        committed <= wb_csr;
  end

  wire id_reads_mepc = id_valid && !id_stall && !id_bubble
                       && (id_csr_addr == MEPC);
  wire pending_wb  = wb_valid && wb_csr_wen && (wb_csr_addr == MEPC);
  wire pending_mem = mem_csr_wen          && (mem_csr_addr == MEPC);
  wire pending_ex  = ex_csr_wen           && (ex_csr_addr == MEPC);

  wire [63:0] expected =
        pending_ex  ? alu_csr_data :
        pending_mem ? mem_csr :
        pending_wb  ? wb_csr : committed;

  always @(posedge clk) begin
    if (!rst && id_reads_mepc)
      if (csr_forward != expected) $error("CSR hazard on MEPC: ID read=%016h, expected=%016h",
                    csr_forward, expected);
  end
endmodule

// bind 到 cpu_core：内部信号名见 vsrc/ysyx_22040750.v 的 cpu_core 例化与连线
bind ysyx_22040750_cpu_core csr_hazard_check u_csr (
  .clk(I_sys_clk), .rst(I_rst),
  .id_valid(IF_ID_input_valid), .id_stall(IF_ID_stall), .id_bubble(IF_ID_bubble),
  .id_csr_addr(csr_addr), .csr_forward(csr_forward_data),
  .ex_csr_wen(ID_EX_csr_wen), .ex_csr_addr(ID_EX_csr_addr),
  .alu_csr_data(alu_csr_data),
  .mem_csr_wen(EX_MEM_csr_wen), .mem_csr_addr(EX_MEM_csr_addr),
  .mem_csr(EX_MEM_csr),
  .wb_csr_wen(MEM_WB_csr_wen), .wb_csr_addr(MEM_WB_csr_addr),
  .wb_csr(MEM_WB_csr), .wb_valid(MEM_WB_valid)
);