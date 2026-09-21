// ============================================================================
// Formal: 流水线 REF-vs-DUT（B4 #16，讲义"通过形式化验证测试流水线的实现"）
//
//   DUT = ysyx_22040750_cpu_core（真实流水线核）
//   REF = 本文件内的受限指令子集**单周期执行器**（RV64I：ALU/U/B/J/LOAD/STORE）
//
//   验证思路（讲义）：
//     - 指令流由自由输入 `xin` 提供（BMC 遍历各种指令与周期组合）；
//     - DUT 退休（difftest_valid）时，把该指令喂给 REF 执行，并对比：
//         ① REF 预测的下一条退休 PC == DUT 的退休 PC；
//         ② 写 GPR 时，DUT 写值（wr_data）== REF 计算值；
//         ③ 写使能存在性一致（DUT reg_wen == REF 语义是否写回）。
//     - load 数据由地址纯函数 memfn 提供（DUT/REF 同源），store 不比对（讲义）；
//     - 约束：assume 指令合法（子集内）+ 访存 8B 对齐 + 无中断；复位后 GPR 初值一致（RTL 已复位清零）。
//
//   状态空间控制：不含 cache/外设；存储器为组合函数 + 固定 1 拍响应（无数组状态）。
// ============================================================================
module pipeline_equiv (
    input clk
);
  // ---------------- 复位 ----------------
  reg [3:0] rstst;
  initial rstst = 4'd0;
  always @(posedge clk) if (rstst != 4'd15) rstst <= rstst + 4'd1;
  wire rst = (rstst < 4'd8);

  // ---------------- DUT ----------------
  wire [31:0] O_pc;
  wire        O_pc_valid;
  wire [31:0] O_mem_addr;
  wire        O_mem_rd_en, O_mem_wen;
  wire [63:0] O_mem_wr_data;
  wire [7:0]  O_mem_wr_strb, O_mem_rd_strb;
  wire        O_inst_fencei, O_mem_fencei;
  reg         rd_pend, wr_pend;
  always @(posedge clk) begin
    if (rst) begin rd_pend <= 1'b0; wr_pend <= 1'b0; end
    else begin rd_pend <= O_mem_rd_en; wr_pend <= O_mem_wen; end
  end
  function [63:0] memfn(input [31:0] a);
    memfn = {a ^ 32'h5A5A5A5A, {a[15:0], a[31:16]} ^ 32'h12345678};
  endfunction
  wire [63:0] rd_data = memfn(O_mem_addr);
  wire        rd_vld  = rd_pend;

  // formal-only probe 输出（由 trim_rtl.py 注入 cpu_core）
  wire [31:0] p_wb_pc, p_wb_inst, p_mem_addr, p_opc, p_ifid_pc, p_current_pc;
  wire        p_wb_v, p_wb_wen, p_rd_en, p_wr_en;
  wire [4:0]  p_wb_rd;
  wire [63:0] p_wr_data, p_rs1, p_rs1f, p_idex_rs1, p_aluout, p_memin, p_exm_alu;
  wire [1:0]  p_regin, p_exm_sel;
  wire        p_exm_v, p_exm_a, p_idex_v, p_idex_a, p_idex_mlt;
  wire [31:0] p_idex_pc, p_idex_inst, p_exm_pc, p_exm_inst;
  // 握手/流水控制探针（定位"同一指令被重复接受"）
  wire        p_if_v;
  wire        p_ifid_v, p_ifid_a, p_ifid_iv, p_ifid_b;
  wire [1:0]  p_ifid_s;
  wire        p_idex_iv, p_idex_b;
  wire [1:0]  p_idex_s;
  wire        p_exm_iv, p_exm_b;
  wire [1:0]  p_exm_s;
  wire        p_wbv, p_wba, p_wbiv, p_wbb;
  wire [1:0]  p_wbs;
  wire [31:0] p_dnpc, p_snpc;
  wire [3:0]  p_dnpc_sel;
  wire        p_opcv;

  // ---------------- 指令供给模型（按 PC 索引的指令存储） ----------------
  // 64 项自由初始化指令存储：**按 IF 当前取指 PC（cpu_core 内部 current_pc = pc_e.O_pc）
  // 索引**，不能用 cpu_core 输出端口 O_pc——该端口是 `assign O_pc = dnpc;`（下一条 PC），
  // 用它索引会把"下一条指令"喂给当前取指（PC/指令错位一拍的假反例）。
  // 时序：与真实 icache 命中一致 —— 请求握手后**下一拍**给出 1 拍 I_inst_valid
  // （不能恒置 1：停顿期间同一指令会被重复接受，造成"同指令执行两次"的假反例）。
  reg [31:0] imem [0:63];
  reg [31:0] req_pc_q;
  reg        inst_vld_q;
  always @(posedge clk) begin
    if (rst) begin req_pc_q <= 32'd0; inst_vld_q <= 1'b0; end
    else begin
      // icache 看到的请求地址 = cpu_core.O_pc = **dnpc**（SoC: .I_cpu_pc(cpu_pc)，cpu_core `assign O_pc = dnpc`）；
      // 数据在请求被接受后一拍返回，届时 pc_e.current_pc 也已更新为同一值（配对一致）。
      if (O_pc_valid && I_pc_ready) req_pc_q <= O_pc;
      inst_vld_q <= (O_pc_valid && I_pc_ready);         // 下一拍数据有效（1 拍脉冲）
    end
  end
  wire [31:0] fetch_inst = imem[req_pc_q[7:2]];

  ysyx_22040750_cpu_core dut (
    .I_sys_clk(clk), .I_rst(rst), .I_mtip(1'b0),
    .I_inst(fetch_inst), .I_inst_valid(inst_vld_q), .I_pc_ready(1'b1), .I_mem_ready(1'b1),
    .O_pc(O_pc), .O_pc_valid(O_pc_valid),
    .O_mem_addr(O_mem_addr), .O_mem_rd_en(O_mem_rd_en), .O_mem_wen(O_mem_wen),
    .I_mem_rd_data(rd_data), .I_mem_rd_data_valid(rd_vld), .I_mem_wr_data_valid(wr_pend),
    .O_mem_wr_data(O_mem_wr_data), .O_mem_wr_strb(O_mem_wr_strb), .O_mem_rd_strb(O_mem_rd_strb),
    .O_inst_fencei(O_inst_fencei), .O_mem_fencei(O_mem_fencei),
    // formal-only probes（由 trim_rtl.py 注入；yosys 不支持层次引用）
    .PROBE_MEM_WB_pc(p_wb_pc), .PROBE_MEM_WB_inst(p_wb_inst),
    .PROBE_difftest_valid(p_wb_v), .PROBE_MEM_WB_reg_wen(p_wb_wen),
    .PROBE_MEM_WB_rd_addr(p_wb_rd), .PROBE_wr_data(p_wr_data),
    .PROBE_EX_MEM_mem_rd_en(p_rd_en), .PROBE_EX_MEM_mem_wr_en(p_wr_en),
    .PROBE_EX_MEM_mem_addr(p_mem_addr),
    .PROBE_O_pc(p_opc), .PROBE_IF_ID_pc(p_ifid_pc), .PROBE_current_pc(p_current_pc),
    .PROBE_rs1_data(p_rs1), .PROBE_rs1_fwd(p_rs1f), .PROBE_ID_EX_rs1(p_idex_rs1),
    .PROBE_MEM_WB_regin_sel(p_regin), .PROBE_MEM_WB_alu_out(p_aluout), .PROBE_mem_in(p_memin),
    .PROBE_EX_MEM_valid(p_exm_v), .PROBE_EX_MEM_allowin(p_exm_a),
    .PROBE_EX_MEM_alu_out(p_exm_alu), .PROBE_EX_MEM_regin_sel(p_exm_sel),
    .PROBE_EX_MEM_pc(p_exm_pc), .PROBE_EX_MEM_inst(p_exm_inst),
    .PROBE_ID_EX_valid(p_idex_v), .PROBE_ID_EX_allowin(p_idex_a),
    .PROBE_ID_EX_pc(p_idex_pc), .PROBE_ID_EX_inst(p_idex_inst),
    .PROBE_ID_EX_alu_multicycle(p_idex_mlt),
    .PROBE_IF_valid(p_if_v),
    .PROBE_IF_ID_valid(p_ifid_v), .PROBE_IF_ID_allowin(p_ifid_a),
    .PROBE_IF_ID_input_valid(p_ifid_iv), .PROBE_IF_ID_bubble(p_ifid_b),
    .PROBE_IF_ID_stall(p_ifid_s),
    .PROBE_ID_EX_input_valid(p_idex_iv), .PROBE_ID_EX_bubble(p_idex_b),
    .PROBE_ID_EX_stall(p_idex_s),
    .PROBE_EX_MEM_input_valid(p_exm_iv), .PROBE_EX_MEM_bubble(p_exm_b),
    .PROBE_EX_MEM_stall(p_exm_s),
    .PROBE_MEM_WB_valid(p_wbv), .PROBE_MEM_WB_allowin(p_wba),
    .PROBE_MEM_WB_input_valid(p_wbiv), .PROBE_MEM_WB_bubble(p_wbb),
    .PROBE_MEM_WB_stall(p_wbs),
    .PROBE_dnpc(p_dnpc), .PROBE_dnpc_sel(p_dnpc_sel),
    .PROBE_snpc(p_snpc), .PROBE_O_pc_valid(p_opcv)
  );

  wire        wb_v   = p_wb_v;
  wire [31:0] wb_pc  = p_wb_pc;
  wire [31:0] wb_ins = p_wb_inst;
  wire        wb_wen = p_wb_wen && (p_wb_rd != 5'd0);
  wire [4:0]  wb_rd  = p_wb_rd;
  wire [63:0] wb_res = p_wr_data;
  // REF 以"取指存储内容"为执行指令（不依赖 debug 端口 MEM_WB_inst 的一致性）
  wire [31:0] wb_instr = imem[wb_pc[7:2]];
  wire [31:0] dbg_ref_pc = ref_pc;   // 诊断用（cover 保活）

  // ---------------- 指令字段（以取指存储为准） ----------------
  wire [6:0] op = wb_instr[6:0];
  wire [4:0] rd = wb_instr[11:7];
  wire [2:0] f3 = wb_instr[14:12];
  wire [4:0] rs1 = wb_instr[19:15];
  wire [4:0] rs2 = wb_instr[24:20];
  wire [6:0] f7 = wb_instr[31:25];

  // ---------------- REF 状态（复位清零，与 DUT GPR 初值一致） ----------------
  reg [63:0] ref_regs[31:0];
  reg [31:0] ref_pc;
  reg        ref_valid;
  integer k;
  wire [63:0] rv1 = ref_regs[rs1];
  wire [63:0] rv2 = ref_regs[rs2];

  function [63:0] sext64(input [63:0] x, input integer bits);
    sext64 = $signed(x[bits-1:0]);
  endfunction

  // 算术右移（显式符号填充；避免 yosys 前端对 $signed >>> 的处理差异）
  function [63:0] asr(input [63:0] x, input [5:0] sh);
    asr = (sh == 6'd0) ? x : ((x >> sh) | ({64{x[63]}} << (6'd64 - sh)));
  endfunction

  // 立即数
  wire [63:0] imm_i = {{52{wb_instr[31]}}, wb_instr[31:20]};
  wire [63:0] imm_s = {{52{wb_instr[31]}}, wb_instr[31:25], wb_instr[11:7]};
  wire [63:0] imm_b = {{51{wb_instr[31]}}, wb_instr[31], wb_instr[7], wb_instr[30:25], wb_instr[11:8], 1'b0};
  wire [63:0] imm_u = {{32{wb_instr[31]}}, wb_instr[31:12], 12'b0};
  wire [63:0] imm_j = {{43{wb_instr[31]}}, wb_instr[31], wb_instr[19:12], wb_instr[20], wb_instr[30:21], 1'b0};

  // 合法性（受限子集；M/SYSTEM/FENCE 等排除；shift 立即数高位约束）
  function automatic is_legal(input [31:0] i);
    begin
      is_legal = 1'b0;
      case (i[6:0])
        7'h37, 7'h17: is_legal = 1'b1;                                   // LUI/AUIPC
        7'h13: begin                                                     // OP-IMM
          case (i[14:12])
            3'b001: is_legal = (i[31:26] == 6'd0);                       // SLLI
            3'b101: is_legal = (i[31:26] == 6'd0) || (i[31:26] == 6'd16);// SRLI/SRAI
            3'b000, 3'b010, 3'b011, 3'b100, 3'b110, 3'b111: is_legal = 1'b1;
            default: is_legal = 1'b0;
          endcase
        end
        7'h33: begin                                                     // OP（按 funct3 精确约束 funct7）
          case (i[14:12])
            3'b000: is_legal = (i[31:25] == 7'h00) || (i[31:25] == 7'h20); // ADD/SUB
            3'b001: is_legal = (i[31:25] == 7'h00);                       // SLL
            3'b010: is_legal = (i[31:25] == 7'h00);                       // SLT
            3'b011: is_legal = (i[31:25] == 7'h00);                       // SLTU
            3'b100: is_legal = (i[31:25] == 7'h00);                       // XOR
            3'b101: is_legal = (i[31:25] == 7'h00) || (i[31:25] == 7'h20); // SRL/SRA
            3'b110: is_legal = (i[31:25] == 7'h00);                       // OR
            3'b111: is_legal = (i[31:25] == 7'h00);                       // AND
            default: is_legal = 1'b0;
          endcase
        end
        7'h63: is_legal = (i[14:12] == 3'b000 || i[14:12] == 3'b001 ||
                           i[14:12] == 3'b100 || i[14:12] == 3'b101 ||
                           i[14:12] == 3'b110 || i[14:12] == 3'b111);    // BRANCH
        7'h6F: is_legal = 1'b1;                                          // JAL
        7'h67: is_legal = (i[14:12] == 3'b000);                          // JALR
        7'h03: is_legal = (i[14:12] != 3'b111);                          // LOAD
        7'h23: is_legal = (i[14:12] <= 3'b011);                          // STORE
        default: is_legal = 1'b0;
      endcase
    end
  endfunction

  // ---------------- REF 语义（组合） ----------------
  wire signed [63:0] s1 = $signed(rv1);
  wire signed [63:0] s2 = $signed(rv2);
  wire [63:0] addr_ld = rv1 + imm_i;
  wire [63:0] addr_st = rv1 + imm_s;
  wire [63:0] ld64 = memfn(addr_ld[31:0]);

  // load 取数（假设 8B 对齐：memfn 低字节对应最低地址）
  wire [63:0] ref_ld =
      (f3 == 3'b000) ? sext64(ld64[7:0], 8)   :
      (f3 == 3'b001) ? sext64(ld64[15:0], 16) :
      (f3 == 3'b010) ? sext64(ld64[31:0], 32) :
      (f3 == 3'b011) ? ld64                   :
      (f3 == 3'b100) ? {56'd0, ld64[7:0]}     :
      (f3 == 3'b101) ? {48'd0, ld64[15:0]}    : {32'd0, ld64[31:0]};

  wire [63:0] shamt = {58'd0, wb_instr[25:20]};
  wire [63:0] opimm_res =
      (f3 == 3'b000) ? rv1 + imm_i                                   :
      (f3 == 3'b010) ? (s1 < $signed(imm_i) ? 64'd1 : 64'd0)         :
      (f3 == 3'b011) ? (rv1 < imm_i ? 64'd1 : 64'd0)                 :
      (f3 == 3'b100) ? (rv1 ^ imm_i)                                 :
      (f3 == 3'b110) ? (rv1 | imm_i)                                 :
      (f3 == 3'b111) ? (rv1 & imm_i)                                 :
      (f3 == 3'b001) ? (rv1 << shamt)                                :
      /* 101 */ ((wb_instr[30]) ? asr(rv1, shamt[5:0]) : (rv1 >> shamt));

  wire [63:0] op_res =
      (f3 == 3'b000) ? ((wb_instr[30]) ? rv1 - rv2 : rv1 + rv2) :
      (f3 == 3'b001) ? (rv1 << rv2[5:0])                      :
      (f3 == 3'b010) ? (s1 < s2 ? 64'd1 : 64'd0)              :
      (f3 == 3'b011) ? (rv1 < rv2 ? 64'd1 : 64'd0)            :
      (f3 == 3'b100) ? (rv1 ^ rv2)                            :
      (f3 == 3'b101) ? ((wb_instr[30]) ? asr(rv1, rv2[5:0]) : (rv1 >> rv2[5:0])) :
      (f3 == 3'b110) ? (rv1 | rv2)                            : (rv1 & rv2);

  wire br_take =
      (f3 == 3'b000) ? (rv1 == rv2)   :
      (f3 == 3'b001) ? (rv1 != rv2)   :
      (f3 == 3'b100) ? (s1 < s2)      :
      (f3 == 3'b101) ? (s1 >= s2)     :
      (f3 == 3'b110) ? (rv1 < rv2)    : (rv1 >= rv2);

  // REF 结果 / 写使能 / 下一条 PC（以 DUT 退休 PC 为基准，避免 REF 初值问题）
  reg [63:0] ref_res;
  reg        ref_wen;
  reg [31:0] ref_next;
  always @* begin
    ref_res = 64'd0;
    ref_wen = 1'b0;
    ref_next = wb_pc + 32'd4;
    case (op)
      7'h37: begin ref_res = imm_u; ref_wen = 1'b1; end
      7'h17: begin ref_res = {32'd0, wb_pc} + imm_u; ref_wen = 1'b1; end
      7'h13: begin ref_res = opimm_res; ref_wen = 1'b1; end
      7'h33: begin ref_res = op_res; ref_wen = 1'b1; end
      7'h03: begin ref_res = ref_ld; ref_wen = 1'b1; end
      7'h63: if (br_take) ref_next = wb_pc + imm_b[31:0];
      7'h6F: begin ref_res = {32'd0, wb_pc} + 64'd4; ref_wen = 1'b1;
                    ref_next = wb_pc + imm_j[31:0]; end
      7'h67: begin ref_res = {32'd0, wb_pc} + 64'd4; ref_wen = 1'b1;
                    ref_next = (rv1 + imm_i) & 64'hFFFF_FFFE; end
      7'h23: ;                                            // store：不比对
      default: ;
    endcase
    if (rd == 5'd0) ref_wen = 1'b0;                        // x0 不写
  end

  // ---------------- 假设 ----------------
  always @* begin
    if (!rst) begin
      assume (is_legal(fetch_inst));
      assume (!p_rd_en || (p_mem_addr[2:0] == 3'b000));
      assume (!p_wr_en || (p_mem_addr[2:0] == 3'b000));
    end
  end

  // ---------------- 断言与 REF 推进 ----------------
  // 注意：difftest_valid 是**保持电平**（MEM_WB 无输出握手，停顿时保持），
  // 不是每拍脉冲；必须按"退休指令变化"沿触发，否则同一指令会被重复执行。
  reg [31:0] prev_pc, prev_ins;
  reg        prev_v;
  wire wb_new = wb_v && (!prev_v || wb_pc != prev_pc || wb_instr != prev_ins);
  always @(posedge clk) begin
    if (rst) begin
      for (k = 0; k < 32; k = k + 1) ref_regs[k] <= 64'd0;
      ref_pc <= 32'h2FFFFFFC;
      ref_valid <= 1'b0;
      prev_v <= 1'b0;
      prev_pc <= 32'd0;
      prev_ins <= 32'd0;
    end else begin
      prev_v <= wb_v;
      prev_pc <= wb_pc;
      prev_ins <= wb_instr;
      if (wb_new) begin
        assert (wb_ins == wb_instr);   // debug 端口 MEM_WB_inst 必须与取指存储一致
        if (ref_valid) begin
          assert (ref_pc == wb_pc);
          assert (wb_wen == ref_wen);
          if (ref_wen) assert (wb_res == ref_res);
        end
        ref_valid <= 1'b1;
        ref_pc    <= ref_next;
        if (ref_wen) ref_regs[rd] <= ref_res;
      end
    end
  end

  // [t4] MEM_WB 保持期间写数据必须稳定（GPR 写使能=电平，若 wr_data 变化会重复写坏寄存器）
  reg [63:0] prev_wr_q;
  reg [31:0] prev_pc_q, prev_ins_q;
  reg        prev_v_q;
  always @(posedge clk) begin
    if (rst) begin
      prev_v_q <= 1'b0; prev_pc_q <= 32'd0; prev_ins_q <= 32'd0; prev_wr_q <= 64'd0;
    end else begin
      if (prev_v_q && wb_v && wb_pc == prev_pc_q && wb_instr == prev_ins_q)
        assert (wb_res == prev_wr_q);
      prev_v_q <= wb_v; prev_pc_q <= wb_pc; prev_ins_q <= wb_instr; prev_wr_q <= wb_res;
    end
  end

  // cover：流水线确实退休够指令（非空泛）
  reg [4:0] cov_cnt;
  always @(posedge clk) begin
    if (rst) cov_cnt <= 5'd0;
    else if (wb_new && cov_cnt != 5'd31) cov_cnt <= cov_cnt + 5'd1;
  end
  always @(posedge clk) if (cov_cnt == 5'd20) cover (1'b1);
  // 保活探针（cover 引用使 yosys 不裁掉这些观测信号；不影响 bmc 断言）
  always @(posedge clk) begin
    cover (p_regin == 2'b01);
    cover (p_memin != p_aluout);
    cover (p_rs1f != p_rs1);
    cover (p_exm_alu != p_aluout);
    cover (p_idex_v != p_exm_v);
    cover (p_exm_sel != p_regin);
    cover (dbg_ref_pc == wb_pc);   // 保活 REF 内部 PC 观测（诊断用）
    cover (p_ifid_v && p_ifid_a);      // IF_ID 有效且被下游接受
    cover (p_idex_iv && p_ifid_a);     // 同拍 IF_ID 允许 + ID_EX 输入有效（潜在重复接受窗口）
    cover (!p_idex_a && p_exm_a);      // ID_EX 停顿但 EX_MEM 可接受（重复锁存窗口）
  end
endmodule
