// ============================================================================
// P-B 部件级频率探针：64bit 加减法器 —— 输入/输出包 FF，测进位链最差路径。
// 运行：cd npc/verif/sta/probe && ./probe_run.sh ysyx_22040750_probe_adder 1000 pb-adder probe_adder.v
// ============================================================================
module ysyx_22040750_probe_adder(
    input         clk,
    input  [63:0] i_a,
    input  [63:0] i_b,
    input         i_sub,
    output [63:0] o_sum,
    output        o_cout
);
    reg [63:0] a_q, b_q;
    reg        sub_q;
    always @(posedge clk) begin
        a_q   <= i_a;
        b_q   <= i_b;
        sub_q <= i_sub;
    end

    // sub ? a - b : a + b（带进位输出；与 ALU 加法通路同构）
    wire [64:0] ext = sub_q ? ({1'b0, a_q} + ~{1'b0, b_q} + 65'd1)
                            : ({1'b0, a_q} + {1'b0, b_q});

    reg [63:0] sum_o;
    reg        cout_o;
    always @(posedge clk) begin
        sum_o  <= ext[63:0];
        cout_o <= ext[64];
    end
    assign o_sum  = sum_o;
    assign o_cout = cout_o;
endmodule
