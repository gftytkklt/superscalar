// ---------------------------------------------------------------------------
// [7] S3 (P2): mul/div 数据+valid 对拍纪律（RTL_STD_MODELS S3 新增，bind 注入非侵入）
// 设计侧：div 输出已改为寄存对（D 值同沿捕获，呈现拍/位值不变）；
//         mul 保持组合呈现拍（终值恰在第 33 窗口累加拍存在），成对性由既有
//         捕获机制（gpr_alu 的 *_reg/*_reg_valid）保证。本文件钉死四条纪律：
//   ① div/mul start-while-busy 不可达（当前流水线下由 ID_EX alu_output_valid 阻塞保证）；
//   ② done 单拍脉冲（Q_valid / P_valid）；
//   ③ P_valid 必伴随进行中的乘法；
//   ④ 捕获寄存器值 == done 拍呈现值（捕获对与呈现对一致）。
// ---------------------------------------------------------------------------
module div_pair_check (
    input clk, rst,
    input div_valid, div_process, Q_valid
);
  reg q_prev;
  always @(posedge clk) begin
    q_prev <= Q_valid;
    if (!rst) begin
      if (div_valid && div_process)
        $error("DIV: start-while-busy (div_valid during in-flight division)");
      if (q_prev && Q_valid)
        $error("DIV: Q_valid longer than one cycle");
    end
  end
endmodule

bind ysyx_22040750_radix2_div div_pair_check u_div_pair (
  .clk(clk), .rst(rst),
  .div_valid(div_valid), .div_process(div_process), .Q_valid(Q_valid)
);

module mul_pair_check (
    input clk, rst,
    input mul_valid, mul_process, P_valid
);
  reg p_prev;
  always @(posedge clk) begin
    p_prev <= P_valid;
    if (!rst) begin
      if (mul_valid && mul_process)
        $error("MUL: start-while-busy (mul_valid during in-flight multiply)");
      if (p_prev && P_valid)
        $error("MUL: P_valid longer than one cycle");
      if (P_valid && !mul_process)
        $error("MUL: P_valid without active multiply");
    end
  end
endmodule

bind ysyx_22040750_booth_mul_serial mul_pair_check u_mul_pair (
  .clk(clk), .rst(rst),
  .mul_valid(mul_valid), .mul_process(mul_process), .P_valid(P_valid)
);

module mdu_capture_check (
    input clk, rst,
    input mul_out_valid, div_out_valid,
    input mul_reg_valid, div_reg_valid,
    input [63:0] mul_result, mul_reg,
    input [63:0] div_result, div_reg,
    input [63:0] rem_result, rem_reg
);
  reg mul_ov_d, div_ov_d, mul_rv_d, div_rv_d;
  reg [63:0] mul_res_d, div_res_d, rem_res_d;
  always @(posedge clk) begin
    mul_ov_d  <= mul_out_valid;  div_ov_d  <= div_out_valid;
    mul_rv_d  <= mul_reg_valid;  div_rv_d  <= div_reg_valid;
    mul_res_d <= mul_result;     div_res_d <= div_result;   rem_res_d <= rem_result;
    if (!rst) begin
      // 捕获发生在 done 拍（out_valid=1）且下游未就绪 → 下一拍核对捕获==呈现
      if (mul_reg_valid && !mul_rv_d && mul_ov_d && (mul_reg != mul_res_d))
        $error("MUL: captured mul_reg=%016h != presented mul_result=%016h",
               mul_reg, mul_res_d);
      if (div_reg_valid && !div_rv_d && div_ov_d &&
          ((div_reg != div_res_d) || (rem_reg != rem_res_d)))
        $error("DIV: captured div/rem(%016h/%016h) != presented(%016h/%016h)",
               div_reg, rem_reg, div_res_d, rem_res_d);
    end
  end
endmodule

bind ysyx_22040750_gpr_alu mdu_capture_check u_mdu_cap (
  .clk(I_sys_clk), .rst(I_rst),
  .mul_out_valid(mul_out_valid), .div_out_valid(div_out_valid),
  .mul_reg_valid(mul_reg_valid), .div_reg_valid(div_reg_valid),
  .mul_result(mul_result), .mul_reg(mul_reg),
  .div_result(div_result), .div_reg(div_reg),
  .rem_result(rem_result), .rem_reg(rem_reg)
);
