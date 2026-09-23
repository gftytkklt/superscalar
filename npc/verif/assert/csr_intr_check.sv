// ---------------------------------------------------------------------------
// [10] S6 (P5): CSR 仲裁/中断提交纪律（RTL_STD_MODELS S6 新增，bind 注入非侵入）
// 设计侧（ysyx_22040750_csr）：单 always 优先级链 csr_wen > csr_intr_wr > csr_mret_wr，
//   原注释"will not occur at the same time"由本监视器升级为断言钉死；
//   中断"恰一次消费"的硬件机制 = intr 提交清 mstatus.MIE（mret 经 MPIE 恢复），
//   本监视器一并钉死（ assumptions：处理机入口首指令不写 MIE——当前软件生态成立）。
// ---------------------------------------------------------------------------
module csr_intr_check (
    input clk, rst,
    input csr_wen, csr_intr_wr, csr_mret_wr,
    input [63:0] mstatus
);
  reg intr_d;
  always @(posedge clk) begin
    intr_d <= csr_intr_wr;
    if (!rst) begin
      // 三事件同拍互斥（同一 WB 指令按译码只能是三者之一）
      if (csr_wen && csr_intr_wr)
        $error("CSR: csr_wen && csr_intr_wr same cycle (priority chain would silently drop intr)");
      if (csr_wen && csr_mret_wr)
        $error("CSR: csr_wen && csr_mret_wr same cycle");
      if (csr_intr_wr && csr_mret_wr)
        $error("CSR: csr_intr_wr && csr_mret_wr same cycle");
      // intr 提交必须清 MIE（防立即重取中断的硬件机制）
      if (intr_d && mstatus[3])
        $error("CSR: mstatus.MIE not cleared after intr commit (intr would retake immediately)");
    end
  end
endmodule

// bind 到 csr：csr_wen/csr_intr_wr/csr_mret_wr 为 I_MEM_WB_valid 门控后的内部线网，
// mstatus 为 CSR 寄存器组（见 vsrc/ysyx_22040750.v ysyx_22040750_csr）
bind ysyx_22040750_csr csr_intr_check u_csr_intr (
  .clk(I_sys_clk), .rst(I_rst),
  .csr_wen(csr_wen), .csr_intr_wr(csr_intr_wr), .csr_mret_wr(csr_mret_wr),
  .mstatus(mstatus)
);
