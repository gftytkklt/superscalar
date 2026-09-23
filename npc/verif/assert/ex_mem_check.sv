// ---------------------------------------------------------------------------
// [11] B1-4 (P1): EX_MEM 复合语义钉死（RTL_STD_MODELS B1 新增，bind 注入非侵入）
// EX_MEM 的 out_ready 是 P1+P3 复合式（响应门）：
//   out_ready = (valid ∧ 非load ∧ 非store在途) ∨ rvalid ∨ bvalid
// 即：非访存指令当拍可出队；load 槽必须等 R；store 槽必须等 B（在途期间阻塞出队）。
// 本监视器把该复合语义钉死为三条断言（构造性成立，防未来改写漂移）：
//   ① load 槽：无 R 到达时 out_valid 必为 0；
//   ② store 在途（valid ∧ mem_wstatus=1）且无 B 时 out_valid 必为 0；
//   ③ 被接受的 store 在 B 未到达期间 mem_wstatus 保持。
// ⚠️ 已知良性形态（勿当违例）：气泡接受拍会以 ID_EX 陈旧载荷改写 mem_wstatus，
//   存在 valid=0 ∧ mem_wstatus=1 的组合——wstatus 仅在槽占用（valid=1）时有意义；
//   故 ③ 必须以 input_valid 限定（首版误报 4 例的根因）。
// ---------------------------------------------------------------------------
module ex_mem_check (
    input clk, rst,
    input input_valid,      // O_EX_MEM_input_valid（模板 valid 寄存器）
    input regin_sel1,       // load 槽标记（O_regin_sel[1]）
    input mem_wstatus,      // store 在途标记
    input mem_rvalid, mem_bvalid,
    input stage_valid       // O_EX_MEM_valid
);
  reg pending_no_b;
  always @(posedge clk) begin
    pending_no_b <= input_valid && mem_wstatus && !mem_bvalid;
    if (!rst) begin
      if (input_valid && regin_sel1 && !mem_rvalid && stage_valid)
        $error("EXMEM: load slot valid without R response");
      if (input_valid && mem_wstatus && !mem_bvalid && stage_valid)
        $error("EXMEM: store in-flight valid without B response");
      if (pending_no_b && !mem_wstatus)
        $error("EXMEM: accepted store's mem_wstatus cleared while B not accepted");
    end
  end
endmodule

bind ysyx_22040750_EX_MEM_reg ex_mem_check u_exmem (
  .clk(I_sys_clk), .rst(I_rst),
  .input_valid(O_EX_MEM_input_valid),
  .regin_sel1(O_regin_sel[1]),
  .mem_wstatus(mem_wstatus),
  .mem_rvalid(I_mem_data_rvalid),
  .mem_bvalid(I_mem_data_bvalid),
  .stage_valid(O_EX_MEM_valid)
);
