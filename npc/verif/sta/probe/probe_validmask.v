// ============================================================================
// B4-Q7/OPT-05 探针：dcache 写验证（write-validate）所需的**字节有效位元数据**面积/频率评估。
// 结构 = 128 行 × 32 bit 掩码（4KB/32B/2 路 = 128 行），按行做 OR 合并写入、
// 读回整行掩码 + 判某 8B lane 是否全有效（读命中检查用）。输入/输出均包 FF（探针口径）。
// 运行：cd npc/verif/sta/probe && ./probe_run.sh ysyx_22040750_probe_validmask 500 \
//         b4q7-validmask probe_validmask.v
// ============================================================================
module ysyx_22040750_probe_validmask(
    input         clk,
    input  [6:0]  i_wline,
    input  [31:0] i_wmask,
    input         i_wen,
    input  [6:0]  i_rline,
    input  [2:0]  i_rlane,
    output        o_lane_valid,
    output [31:0] o_rmask
);
    reg [6:0]  wline_q;
    reg [31:0] wmask_q;
    reg        wen_q;
    reg [6:0]  rline_q;
    reg [2:0]  rlane_q;
    always @(posedge clk) begin
        wline_q <= i_wline;
        wmask_q <= i_wmask;
        wen_q   <= i_wen;
        rline_q <= i_rline;
        rlane_q <= i_rlane;
    end

    reg [31:0] vmask [0:127];
    integer i;
    initial for (i = 0; i < 128; i = i + 1) vmask[i] = 32'b0;
    always @(posedge clk)
        if (wen_q) vmask[wline_q] <= vmask[wline_q] | wmask_q;

    wire [31:0] rmask_d = vmask[rline_q];
    wire [7:0]  lane_d  = rmask_d[{rlane_q, 3'b0} +: 8];

    reg        lane_valid_o;
    reg [31:0] rmask_o;
    always @(posedge clk) begin
        lane_valid_o <= &lane_d;
        rmask_o      <= rmask_d;
    end
    assign o_lane_valid = lane_valid_o;
    assign o_rmask      = rmask_o;
endmodule
