// ============================================================================
// Formal properties: radix2_div (Bug3) -- spec: DIV by zero => -1, REM => dividend
// 配合 div.sby 使用：sby -f div.sby
// 当前 RTL 在负被除数 / 0 时给出 +1，bmc 会立即返回反例。
// 采用过程式 assert/cover（yosys -formal 直接支持，无 SVA property）。
// ============================================================================
module div_top (
    input clk, rst,
    input [63:0] dividend, divisor,
    input is_signed, div_valid,
    output [63:0] quotient, remainder,
    output Q_valid
);
  ysyx_22040750_radix2_div u_div (
    .clk(clk), .rst(rst),
    .dividend(dividend), .divisor(divisor),
    .is_signed(is_signed), .div_valid(div_valid),
    .quotient(quotient), .remainder(remainder), .Q_valid(Q_valid)
  );

  reg zero_div;
  always @(posedge clk) begin
    if (rst)                              zero_div <= 0;
    else if (div_valid && divisor == 0)   zero_div <= 1;
    else if (Q_valid)                     zero_div <= 0;
  end

  // --- 敌手驱动：首拍复位，随后稳定注入 "signed -5 / 0"，跑真实除法序列
  reg [1:0] st;
  initial st = 2'd0;
  always @(posedge clk) begin           // 纯计数器，不依赖 rst，防止卡在复位
    if (st < 2'd3) st <= st + 2'd1;
  end
  always @(posedge clk) begin
    if (st == 2'd0) begin
      assume (rst === 1'b1);
      assume (div_valid === 1'b0);
    end else if (st == 2'd1) begin
      assume (rst === 1'b0);
      assume (div_valid === 1'b1);
      assume (divisor === 64'd0);
      assume (dividend === 64'hFFFF_FFFF_FFFF_FFFB);  // -5
      assume (is_signed === 1'b1);
    end else begin
      assume (rst === 1'b0);
      assume (div_valid === 1'b0);
      assume (divisor === 64'd0);
      assume (dividend === 64'hFFFF_FFFF_FFFF_FFFB);  // -5
      assume (is_signed === 1'b1);
    end
  end

  // 除零完成后：商必须为 -1（全 1），余数必须等于被除数
  always @(posedge clk) begin
    if (!rst && zero_div && Q_valid) begin
      assert (quotient == {64{1'b1}});
      assert (remainder == dividend);
    end
  end

  // cover：正/负被除数两类除零路径都应可达
  always @(posedge clk) begin
    if (!rst && div_valid && divisor == 0 && !is_signed) cover (div_valid);
    if (!rst && div_valid && divisor == 0 &&  is_signed) cover (div_valid);
    if (!rst && zero_div && Q_valid) cover (Q_valid);
  end
endmodule