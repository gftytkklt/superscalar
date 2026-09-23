// ---------------------------------------------------------------------------
// [8] S4 (P1 辅助): 冒险/前递 match 纪律（RTL_STD_MODELS S4 新增，bind 注入非侵入）
// 设计侧（S4 后）：五要素 match 单点化于 stall_unit ——
//   match[rsX] = 消费者读 rsX 且 rsX≠0（decoder.stall_en）∧ rsX==rd ∧ rd≠0 ∧ wen，
//   valid 门控在输出级；forward_unit 按固定优先级 EX > MEM > WB 选择。
// 本监视器钉死四条纪律：
//   ① x0 永不参与匹配/前递；         ② match ⇒ 生产者 valid；
//   ③ 完备性（五要素组合与 match 一一对应）；④ 前递选择与优先级一致。
// ---------------------------------------------------------------------------
module hazard_forward_check (
    input clk, rst,
    // 消费者（ID）
    input [4:0] rs1_addr, rs2_addr,
    input [1:0] stall_en,
    // 生产者 match/属性
    input [1:0] ex_stall, mem_stall, wb_stall,
    input [4:0] ex_rd, mem_rd, wb_rd,
    input ex_valid, mem_valid, wb_valid,
    input ex_wen, mem_wen, wb_wen_v,
    // 前递选择结果与候选数据
    input [63:0] rs1_fwd, rs2_fwd,
    input [63:0] ex_data, mem_data, wb_data
);
  always @(posedge clk) begin
    if (!rst) begin
      // ① x0 永不参与匹配
      if (ex_stall != 0 && ex_rd == 0)   $error("HZD: x0 match at EX");
      if (mem_stall != 0 && mem_rd == 0) $error("HZD: x0 match at MEM");
      if (wb_stall != 0 && wb_rd == 0)   $error("HZD: x0 match at WB");
      // ② match ⇒ 生产者在槽内
      if (ex_stall != 0 && !ex_valid)    $error("HZD: EX match without EX valid");
      if (mem_stall != 0 && !mem_valid)  $error("HZD: MEM match without MEM valid");
      if (wb_stall != 0 && !wb_valid)    $error("HZD: WB match without WB valid");
      // ③ 完备性：五要素组合 ⇔ match（6 组全查）
      if (stall_en[1] && (rs1_addr == ex_rd) && ex_wen && ex_valid && !ex_stall[1])
        $error("HZD: EX/rs1 match incomplete");
      if (stall_en[0] && (rs2_addr == ex_rd) && ex_wen && ex_valid && !ex_stall[0])
        $error("HZD: EX/rs2 match incomplete");
      if (stall_en[1] && (rs1_addr == mem_rd) && mem_wen && mem_valid && !mem_stall[1])
        $error("HZD: MEM/rs1 match incomplete");
      if (stall_en[0] && (rs2_addr == mem_rd) && mem_wen && mem_valid && !mem_stall[0])
        $error("HZD: MEM/rs2 match incomplete");
      if (stall_en[1] && (rs1_addr == wb_rd) && wb_wen_v && wb_valid && !wb_stall[1])
        $error("HZD: WB/rs1 match incomplete");
      if (stall_en[0] && (rs2_addr == wb_rd) && wb_wen_v && wb_valid && !wb_stall[0])
        $error("HZD: WB/rs2 match incomplete");
      // ④ 前递选择与 EX > MEM > WB 优先级一致（rs1/rs2 对称 6 条）
      if (ex_stall[1] && ex_wen && rs1_fwd != ex_data)
        $error("FWD: rs1 should select EX");
      if (!(ex_stall[1] && ex_wen) && mem_stall[1] && mem_wen && rs1_fwd != mem_data)
        $error("FWD: rs1 should select MEM");
      if (!(ex_stall[1] && ex_wen) && !(mem_stall[1] && mem_wen) && wb_stall[1] && wb_wen_v && rs1_fwd != wb_data)
        $error("FWD: rs1 should select WB");
      if (ex_stall[0] && ex_wen && rs2_fwd != ex_data)
        $error("FWD: rs2 should select EX");
      if (!(ex_stall[0] && ex_wen) && mem_stall[0] && mem_wen && rs2_fwd != mem_data)
        $error("FWD: rs2 should select MEM");
      if (!(ex_stall[0] && ex_wen) && !(mem_stall[0] && mem_wen) && wb_stall[0] && wb_wen_v && rs2_fwd != wb_data)
        $error("FWD: rs2 should select WB");
    end
  end
endmodule

// bind 到 cpu_core：信号名见 stall_unit_e/forward_unit_e 实例连线
// （vsrc/ysyx_22040750.v；wb_wen_v = forward_unit 的 I_WB_reg_wen = MEM_WB_reg_wen & MEM_WB_valid）
bind ysyx_22040750_cpu_core hazard_forward_check u_hzd (
  .clk(I_sys_clk), .rst(I_rst),
  .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .stall_en(stall_en),
  .ex_stall(ID_EX_stall), .mem_stall(EX_MEM_stall), .wb_stall(MEM_WB_stall),
  .ex_rd(ID_EX_rd_addr), .mem_rd(EX_MEM_rd_addr), .wb_rd(MEM_WB_rd_addr),
  .ex_valid(ID_EX_input_valid), .mem_valid(EX_MEM_input_valid), .wb_valid(MEM_WB_input_valid),
  .ex_wen(ID_EX_reg_wen), .mem_wen(EX_MEM_reg_wen), .wb_wen_v(MEM_WB_reg_wen & MEM_WB_valid),
  .rs1_fwd(rs1_forward_data), .rs2_fwd(rs2_forward_data),
  .ex_data(alu_out), .mem_data(EX_MEM_alu_out), .wb_data(wr_data)
);
