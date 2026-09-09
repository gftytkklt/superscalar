// ---------------------------------------------------------------------------
// [2] Bug3: 有符号除零，负被除数时商错（应恒为 -1 / 余数=被除数）
// 影子寄存器记录"本次除法是否为除零"，在 Q_valid 时核对结果。
// 当前 RTL(radix2_div)负被除数除零会给出 +1，断言必失败。
// ---------------------------------------------------------------------------
module div_zero_check (
    input clk, rst,
    input [63:0] dividend, divisor,
    input is_signed, div_valid,
    output [63:0] quotient, remainder,
    input Q_valid
);
  reg zero_div;
  always @(posedge clk) begin
    if (rst)                            zero_div <= 0;
    else if (div_valid && divisor == 0) zero_div <= 1;
    else if (Q_valid)                   zero_div <= 0;
  end

  always @(posedge clk) begin
    if (!rst && Q_valid && zero_div) begin
      if (quotient != {64{1'b1}}) $error("DIV-zero: quotient=%016h, expected -1(0xff..f)", quotient);
      if (remainder != dividend) $error("REM-zero: remainder=%016h, expected dividend %016h", remainder, dividend);
    end
  end
endmodule

bind ysyx_22040750_radix2_div div_zero_check u_div (
  .clk(clk), .rst(rst),
  .dividend(dividend), .divisor(divisor),
  .is_signed(is_signed), .div_valid(div_valid),
  .quotient(quotient), .remainder(remainder),
  .Q_valid(Q_valid)
);