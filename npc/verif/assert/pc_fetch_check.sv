// ---------------------------------------------------------------------------
// [6] S2 (P1): pc 取指槽纪律（RTL_STD_MODELS S2 新增，bind 注入非侵入）
// 设计侧（ysyx_22040750_pc）：响应槽 slot_valid/inst_slot 采用规范式
//   slot_valid' = load ∨ (slot_valid ∧ ¬accept)。
// 本监视器检查两条跨模块契约：
//   ① 槽满时上游不得再交付新响应（icache 单次交付契约）——原实现该场景会静默
//     覆盖 inst_cache（指令丢失隐患），重构后为"保持旧值 + 此断言"；
//   ② 不变式 slot_valid ⇒ IF_valid（槽内有未交付响应 ⇒ 取指请求仍在途未交付）。
// ---------------------------------------------------------------------------
module pc_fetch_check (
    input clk, rst,
    input I_inst_valid,
    input slot_valid,
    input IF_valid,
    input I_IF_ID_allowin
);
  always @(posedge clk) begin
    if (!rst) begin
      if (I_inst_valid && slot_valid)
        $error("PC: new fetch response while slot full (icache duplicate delivery?)");
      if (slot_valid && !IF_valid)
        $error("PC: slot_valid without IF_valid (invariant broken)");
    end
  end
endmodule

// bind 到 pc：内部信号 slot_valid/IF_valid 见 vsrc/ysyx_22040750.v（S2 更名自 cache_valid）
bind ysyx_22040750_pc pc_fetch_check u_pc_fetch (
  .clk(I_sys_clk), .rst(I_rst),
  .I_inst_valid(I_inst_valid),
  .slot_valid(slot_valid), .IF_valid(IF_valid),
  .I_IF_ID_allowin(I_IF_ID_allowin)
);
