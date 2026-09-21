// ============================================================================
// P-B 部件级频率探针：寄存器堆（gpr）—— 输入/输出均包 FF，测 FF→读 mux→FF /
// FF→写译码→FF 的最差路径。使用需与 verif/sta/ysyx_22040750_synth.v（已去 DPI/
// initial 的核源码）一起读入（top 为本模块）。
// 运行：cd npc/verif/sta/probe && ./probe_run.sh ysyx_22040750_probe_gpr 1000 pb-gpr \
//         probe_gpr.v ../ysyx_22040750_synth.v
// ============================================================================
module ysyx_22040750_probe_gpr(
    input         clk,
    input  [63:0] i_wr_data,
    input         i_wen,
    input  [4:0]  i_rd_addr,
    input  [4:0]  i_rs1_addr,
    input  [4:0]  i_rs2_addr,
    output [63:0] o_rs1_data,
    output [63:0] o_rs2_data
);
    // 输入包 FF
    reg [63:0] wr_data_q;
    reg        wen_q;
    reg [4:0]  rd_q, rs1_q, rs2_q;
    always @(posedge clk) begin
        wr_data_q <= i_wr_data;
        wen_q     <= i_wen;
        rd_q      <= i_rd_addr;
        rs1_q     <= i_rs1_addr;
        rs2_q     <= i_rs2_addr;
    end

    wire [63:0] rs1_d, rs2_d;
    ysyx_22040750_gpr u_gpr(
        .I_sys_clk (clk),
        .I_rst     (1'b0),
        .I_wr_data (wr_data_q),
        .I_wen     (wen_q),
        .I_rd_addr (rd_q),
        .I_rs1_addr(rs1_q),
        .O_rs1_data(rs1_d),
        .I_rs2_addr(rs2_q),
        .O_rs2_data(rs2_d)
    );

    // 输出包 FF
    reg [63:0] rs1_o, rs2_o;
    always @(posedge clk) begin
        rs1_o <= rs1_d;
        rs2_o <= rs2_d;
    end
    assign o_rs1_data = rs1_o;
    assign o_rs2_data = rs2_o;
endmodule
