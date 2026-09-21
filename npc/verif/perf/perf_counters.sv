// ============================================================================
// 性能计数器（B3 阶段1）—— 非侵入式：bind 注入 + 纯仿真 $display，不改核 RTL。
//
// 与 assert/*.sv 的 bind 注入一致：单独 .sv，用 bind 挂到 ysyx_22040750_cpu_core，
// 仿真结束在 final 块汇总 $display。计数器不参与流片（无流片信号，纯仿真观测）。
//
// 事件定义（与讲义性能模型对应）：
//   ifu_deliver : IFU 取指令（总交付）        = icache 交付指令（I_inst_valid 上升拍）
//                   含分支/跳转后被冲刷的"取指槽"（bubble 取指），反映指令供给工作负载；
//   decode_*/总 : 译码出各类别指令（真实指令） = IF_ID_valid 且 ID_EX 接收(一次性)、非 bubble，
//                   按 decoder 控制字分成 mem/csr/branch/compute/other；
//   ifu_fetch   : IFU 取到指令（有效）         = decode_总（每条被真正取入并译码执行的指令，
//                   与 bubble 取指区分）；用于与动态指令数/译码总数的一致性对照；
//   lsu_data    : LSU 取到数据                 = cache 返回读数据（I_mem_rd_data_valid 上升拍）；
//   exu_compute : EXU 完成计算                 = ALU 完成一次计算（alu_out_valid 上升拍）；
//   retire      : 动态指令数                   = WB 提交（difftest_valid），一致性基准。
//
// 一致性检查（讲义）：decode_总 == ifu_fetch == retire；若 ifu_deliver 更大则说明存在
// 分支/跳转引起的"冲刷取指"（差 ≈ bubble 数），属微结构代价，应单独归因，非计数器错误。
// ============================================================================
module perf_counters #(
)(
  input I_clk, I_rst,
  input I_inst_valid,              // IFU 指令有效（cpu_core 端口）
  input I_mem_rd_data_valid,       // 读数据有效（cpu_core 端口）
  input I_mem_wr_data_valid,       // store 完成(bvalid)（cpu_core 端口）
  input O_mem_wen,                 // store 请求发送到 dcache 拍（cpu_core 端口）
  input [31:0] O_mem_addr,         // 访存地址（cpu_core 输出端口，=EX_MEM_mem_addr）
  input O_pc_valid,                // cpu 向 icache 发出取指请求（cpu_core 输出端口）
  input I_pc_ready,                // icache 接受取指（cpu_core 输入端口）
  input [31:0] O_pc,               // 取指 PC（=dnpc，cpu_core 输出端口）
  input EX_MEM_mem_rd_en,          // load 请求发送到 dcache 拍（cpu_core 内部）
  input ID_EX_alu_multicycle,      // 乘/除多周期标志（cpu_core 内部）
  input IF_ID_valid, ID_EX_allowin, IF_ID_bubble,
  input ID_EX_valid, EX_MEM_allowin, ID_EX_bubble,
  input [3:0] dnpc_sel,
  input mem_wen,
  input [8:0] mem_rstrb,
  input csr_wen, csr_mret, csr_intr,
  input reg_wen,
  input [31:0] MEM_WB_inst,
  input MEM_WB_valid,
  input [31:0] MEM_WB_pc,          // 提交 PC（= 该指令取指 PC）
  input difftest_valid,
  // B4-Q2 停顿/分支细分计数器输入（均为 cpu_core 内部信号，只读）
  input I_IF_ID_stall,                              // ID 停顿（load-use/M-D/intr 组合）
  input [1:0] I_ID_EX_stall, I_EX_MEM_stall,        // 前递匹配（消费者等待）信号
  input I_ID_EX_mem_rd_en, I_EX_MEM_mem_rd_en,      // 在途 load 标志
  input I_ID_EX_input_valid,                        // ID_EX 寄存器 valid（M/D 忙碌判定）
  input [3:0] I_ID_EX_alu_mlt,                      // ALU 多周期选择位 [13:10]
  input [31:0] I_IF_ID_inst                         // ID 段指令（分支类型细分）
);
  // cachesim trace 导出（仅当 C 侧 setenv CACHESIM_TRACE 时落盘，否则 no-op）
  import "DPI-C" function void csim_ifetch(input int pc);
  import "DPI-C" function void csim_dread(input int addr);
  import "DPI-C" function void csim_dwrite(input int addr);
  // 性能计数器周期快照（讲义"性能计数器的trace"；仅当 setenv PERF_CTR_TRACE 时落盘）
  import "DPI-C" function void ctr_snap(
    input longint unsigned cyc, input longint unsigned retire, input longint unsigned deliver,
    input longint unsigned decode, input longint unsigned exu, input longint unsigned ifu_miss,
    input longint unsigned lsu, input longint unsigned bubble, input longint unsigned mem,
    input longint unsigned csr, input longint unsigned branch, input longint unsigned compute,
    input longint unsigned other, input longint unsigned lsu_lat, input longint unsigned st_lat);
  localparam SNAP_CYCLES = 32'd100000;   // 快照间隔（周期）
  reg [31:0] snap_cyc;
  reg [63:0] c_deliver, c_lsu, c_exu, c_ret, c_decode_total;
  reg [63:0] c_mem, c_csr, c_branch, c_compute, c_other, c_bubble;
  reg [63:0] c_cycles, c_ifu_miss, c_lsu_lat_total, c_mul_cycles, c_st_lat_total;
  // B4-Q2 计数器
  reg [63:0] c_lduse_cyc, c_lduse_ev, c_mdu_ev, c_br_taken, c_br_ntaken, c_jal, c_jalr;
  reg lduse_pend, mdu_pend;
  reg [63:0] st_pend_len; reg st_pend;
  // 访存地址区域分类（在 load/store 请求拍采样 O_mem_addr）
  reg [63:0] rd_sram, rd_psram, rd_flash, rd_rdonly, st_sram, st_psram, st_mmio;
  wire [31:0] a = O_mem_addr;
  wire is_sram   = (a >= 32'h0f000000) && (a <  32'h0f002000);
  wire is_psram  = (a >= 32'h80000000) && (a <  32'h80400000);
  wire is_flash  = (a >= 32'h30000000) && (a <  32'h40000000);
  wire is_sdram  = (a >= 32'ha0000000) && (a <  32'ha8000000);
  wire is_cacheable = is_psram || is_flash || is_sdram;

  wire decode_ev = IF_ID_valid && ID_EX_allowin && !IF_ID_bubble;
  wire decode_bubble = IF_ID_valid && ID_EX_allowin && IF_ID_bubble;
  // EXU 完成计算 = 指令离开 EX 进入 MEM（每条真实指令 EX 段执行一次；排除 bubble，
  // 使 EXU 计数与动态指令数一致；单周期 ALU 的 alu_out_valid 恒为 1 不可用）。
  wire exu_ev = ID_EX_valid && EX_MEM_allowin && !ID_EX_bubble;
  // B4-Q2：停顿归因（与 stall_unit 内部条件一致：前递寄存器匹配 × 在途 load/M-D）
  wire lduse_stall = I_IF_ID_stall & ((|I_ID_EX_stall & I_ID_EX_mem_rd_en) |
                                      (|I_EX_MEM_stall & I_EX_MEM_mem_rd_en));
  wire mdu_stall   = I_IF_ID_stall & (|I_ID_EX_stall & ID_EX_alu_multicycle);
  // M/D 忙碌 = ID_EX 中为多周期 ALU 指令（覆盖整个 EX 执行期，而非"接受脉冲"）
  wire mdu_busy    = I_ID_EX_input_valid & (|I_ID_EX_alu_mlt);

  reg [63:0] ld_pend_len; reg ld_pend;      // 单 load 在途周期计数
  always @(posedge I_clk) begin
    if (I_rst) begin
      c_deliver<=0; c_lsu<=0; c_exu<=0; c_ret<=0; c_decode_total<=0;
      c_mem<=0; c_csr<=0; c_branch<=0; c_compute<=0; c_other<=0; c_bubble<=0;
      c_cycles<=0; c_ifu_miss<=0; c_lsu_lat_total<=0; c_mul_cycles<=0; c_st_lat_total<=0;
      ld_pend<=0; ld_pend_len<=0; st_pend<=0; st_pend_len<=0; snap_cyc<=0;
      c_lduse_cyc<=0; c_lduse_ev<=0; c_mdu_ev<=0; c_br_taken<=0; c_br_ntaken<=0;
      c_jal<=0; c_jalr<=0; lduse_pend<=0; mdu_pend<=0;
      rd_sram<=0; rd_psram<=0; rd_flash<=0; rd_rdonly<=0; st_sram<=0; st_psram<=0; st_mmio<=0;
    end else begin
      c_cycles <= c_cycles + 64'd1;
      if (I_inst_valid)        c_deliver <= c_deliver + 64'd1;
      if (I_mem_rd_data_valid) c_lsu     <= c_lsu     + 64'd1;
      if (O_pc_valid && !I_inst_valid) c_ifu_miss <= c_ifu_miss + 64'd1; // 取指在等 icache（供给缺口）
      // M/D 占用 EX 周期（修正：旧口径用 ID_EX_alu_multicycle 接受脉冲，恒 0，漏计 M/D）
      if (mdu_busy) c_mul_cycles <= c_mul_cycles + 64'd1;
      if (exu_ev)              c_exu     <= c_exu     + 64'd1;
      if (difftest_valid)      c_ret     <= c_ret     + 64'd1;
      if (decode_bubble)       c_bubble  <= c_bubble  + 64'd1;
      if (decode_ev) begin
        c_decode_total <= c_decode_total + 64'd1;
        if (mem_wen | (|mem_rstrb))              c_mem    <= c_mem    + 64'd1;
        else if (csr_wen | csr_mret | csr_intr)  c_csr    <= c_csr    + 64'd1;
        else if (!dnpc_sel[0])                   c_branch <= c_branch + 64'd1;
        else if (reg_wen)                        c_compute<= c_compute+ 64'd1;
        else                                     c_other  <= c_other  + 64'd1;
      end
      // B4-Q2：停顿归因计数 + 分支细分（decode_ev = 真实译码执行的指令）
      if (lduse_stall) c_lduse_cyc <= c_lduse_cyc + 64'd1;
      if (lduse_stall && !lduse_pend) begin
        c_lduse_ev <= c_lduse_ev + 64'd1; lduse_pend <= 1'b1;
      end else if (!lduse_stall) lduse_pend <= 1'b0;
      if (mdu_stall && !mdu_pend) begin
        c_mdu_ev <= c_mdu_ev + 64'd1; mdu_pend <= 1'b1;
      end else if (!mdu_stall) mdu_pend <= 1'b0;
      if (decode_ev) begin
        case (I_IF_ID_inst[6:0])
          7'h63: begin
            if (dnpc_sel[0]) c_br_ntaken <= c_br_ntaken + 64'd1;
            else             c_br_taken  <= c_br_taken  + 64'd1;
          end
          7'h6F: c_jal  <= c_jal  + 64'd1;
          7'h67: c_jalr <= c_jalr + 64'd1;
          default: ;
        endcase
      end
      // LSU 平均访存延迟：从 load 请求发出(EX_MEM_mem_rd_en)到数据返回(I_mem_rd_data_valid)
      if (EX_MEM_mem_rd_en && !ld_pend) begin ld_pend <= 1; ld_pend_len <= 0; end
      else if (ld_pend) ld_pend_len <= ld_pend_len + 64'd1;
      if (ld_pend && I_mem_rd_data_valid) begin
        c_lsu_lat_total <= c_lsu_lat_total + ld_pend_len + 64'd1;
        ld_pend <= 0;
      end
      // store 完成延迟：O_mem_wen(store 请求) -> I_mem_wr_data_valid(bvalid)
      if (O_mem_wen && !st_pend) begin st_pend <= 1; st_pend_len <= 0; end
      else if (st_pend) st_pend_len <= st_pend_len + 64'd1;
      if (st_pend && I_mem_wr_data_valid) begin
        c_st_lat_total <= c_st_lat_total + st_pend_len + 64'd1;
        st_pend <= 0;
      end
      // cachesim trace：取指按"icache 接受请求"逐次记录（与 ICACHE_STAT 口径一致；含被冲刷
      // 的 bubble 取指），load/store 各记录 1 次（与 rd/st_region 口径一致）
      if (O_pc_valid && I_pc_ready) csim_ifetch(O_pc);
      if (EX_MEM_mem_rd_en) csim_dread(O_mem_addr);
      if (O_mem_wen) csim_dwrite(O_mem_addr);
      // 性能计数器周期快照（讲义"性能计数器的trace"；SNAP_CYCLES 一行 CSV，环境变量门控）
      if (snap_cyc == SNAP_CYCLES - 1) begin
        snap_cyc <= 32'd0;
        ctr_snap(c_cycles, c_ret, c_deliver, c_decode_total, c_exu, c_ifu_miss, c_lsu, c_bubble,
                 c_mem, c_csr, c_branch, c_compute, c_other, c_lsu_lat_total, c_st_lat_total);
      end else snap_cyc <= snap_cyc + 32'd1;
      // 区域分类（load 请求 / store 请求拍）
      if (EX_MEM_mem_rd_en) begin
        if (is_psram) rd_psram <= rd_psram + 64'd1;
        else if (is_flash) rd_flash <= rd_flash + 64'd1;
        else if (is_sdram) rd_rdonly <= rd_rdonly + 64'd1;
        else if (is_sram) rd_sram <= rd_sram + 64'd1;
      end
      if (O_mem_wen) begin
        if (is_psram) st_psram <= st_psram + 64'd1;
        else if (is_sram) st_sram <= st_sram + 64'd1;
        else if (!is_cacheable) st_mmio <= st_mmio + 64'd1;
      end
    end
  end

  // 周期性进度快照：每 DUMP_CYCLES 打印一次当前计数（长仿真可随时 Ctrl-C 查看进度）。
  // 与 soctest.cpp 的周期 fflush 配合，使重定向到文件的日志也能及时落盘。
  localparam DUMP_CYCLES = 32'd5000000;
  reg [31:0] cyc;
  always @(posedge I_clk) begin
    if (I_rst) cyc <= 32'd0;
    else cyc <= (cyc == DUMP_CYCLES - 1) ? 32'd0 : cyc + 32'd1;
  end
  always @(posedge I_clk) if (!I_rst && (cyc == DUMP_CYCLES - 1)) begin
    $display("PERF[snap @ %0d]: cycles=%0d deliver=%0d decode=%0d retire=%0d lsu=%0d exu=%0d | ifu_miss=%0d mul_cyc=%0d lsu_lat=%0d | mem=%0d csr=%0d branch=%0d compute=%0d other=%0d bubble=%0d",
      cyc, c_cycles, c_deliver, c_decode_total, c_ret, c_lsu, c_exu,
      c_ifu_miss, c_mul_cycles, c_lsu_lat_total,
      c_mem, c_csr, c_branch, c_compute, c_other, c_bubble);
  end

  // ---- 一致性自检（counter 正确性校验）----
  // 不变式：decode_total == retire == exu；各类别和 == decode_total；
  //         ifu_deliver - decode == bubble（被冲刷的取指槽）。
  // 仅在计数逻辑正确时成立；若 fail 说明计数信号选错或被 held-valid 污染。
  wire [63:0] cat_sum = c_mem + c_csr + c_branch + c_compute + c_other;
  wire [63:0] deliver_minus_decode = (c_deliver >= c_decode_total) ? (c_deliver - c_decode_total) : 0;
  wire [63:0] retire_full = c_ret + 64'd1; // ebreak 计入
  always @(posedge I_clk) if (ebreak) begin
    if (c_decode_total != retire_full) $display("PERF-CHECK FAIL decode!=retire: decode=%0d retire=%0d", c_decode_total, retire_full);
    else $display("PERF-CHECK OK decode==retire==exu==%0d", c_decode_total);
    if (c_exu != retire_full) $display("PERF-CHECK FAIL exu!=retire: exu=%0d retire=%0d", c_exu, retire_full);
    if (cat_sum != c_decode_total) $display("PERF-CHECK FAIL cat_sum!=decode: sum=%0d decode=%0d", cat_sum, c_decode_total);
    else $display("PERF-CHECK OK cat_sum==decode==%0d (mem=%0d branch=%0d compute=%0d other=%0d csr=%0d)", c_decode_total, c_mem, c_branch, c_compute, c_other, c_csr);
    // deliver - decode 应为 bubble；允许 ±1（尾部一个被取但不计 bubble 的边界取指/复位边沿）。
    if (deliver_minus_decode > c_bubble + 64'd1) $display("PERF-CHECK FAIL deliver-decode!=bubble: diff=%0d bubble=%0d", deliver_minus_decode, c_bubble);
    else $display("PERF-CHECK OK deliver-decode≈bubble==%0d", c_bubble);
  end

  // ebreak：MEM_WB_inst == 0x00100073，即 HIT GOOD TRAP 前一拍（retire 中 ebreak 未计入 c_ret）
  wire ebreak = (MEM_WB_inst == 32'h00100073) && MEM_WB_valid && !I_rst;
  always @(posedge I_clk) if (ebreak) begin
    $display("PERF[ebreak]: cycles=%0d retire=%0d | ifu_deliver=%0d lsu=%0d exu=%0d",
      c_cycles, c_ret + 64'd1, c_deliver, c_lsu, c_exu);
    $display("PERF[ebreak]  consistency: decode_total(%0d)==ifu_fetch(%0d)==retire(%0d) ; deliver-decode=%0d (bubble=%0d)",
      c_decode_total, c_decode_total, c_ret + 64'd1,
      (c_deliver>c_decode_total)?(c_deliver-c_decode_total):(c_decode_total-c_deliver), c_bubble);
    $display("PERF[ebreak]  classes: mem=%0d csr=%0d branch=%0d compute=%0d other=%0d bubble=%0d",
      c_mem, c_csr, c_branch, c_compute, c_other, c_bubble);
    // 注意：按拍累加的 lsu/latency（c_lsu/c_lsu_lat_total/c_st_lat_total）因 O_cpu_rvalid/O_cpu_bvalid
    // 可保持多拍而**不可信**（真实 load/store 数与延迟见 dcache_stats.sv 的缺失代价/MMIO 延迟 + 区域分类）。
    $display("PERF[ebreak]  ifu_miss(fetch wait)=%0d  mul_multicycle=%0d  (注意: lsu/latency 已下放到 dcache_stats)",
      c_ifu_miss, c_mul_cycles);
    $display("PERF[ebreak]  stalls: lduse(cyc=%0d ev=%0d) mdu_ev=%0d | branches: taken=%0d ntaken=%0d jal=%0d jalr=%0d",
      c_lduse_cyc, c_lduse_ev, c_mdu_ev, c_br_taken, c_br_ntaken, c_jal, c_jalr);
    $display("PERF[ebreak]  rd_region: psram(heap,cache)=%0d flash(rodata)=%0d sram(.data/.bss+stack,MMIO)=%0d sdram=%0d | st_region: psram=%0d sram=%0d mmio=%0d",
      rd_psram, rd_flash, rd_sram, rd_rdonly, st_psram, st_sram, st_mmio);
  end

  final begin
    $display("PERF[final]: cycles=%0d retire=%0d ifu_deliver=%0d lsu=%0d exu=%0d ifu_miss=%0d mul_cyc=%0d lsu_lat_total=%0d st_lat_total=%0d",
      c_cycles, c_ret, c_deliver, c_lsu, c_exu, c_ifu_miss, c_mul_cycles, c_lsu_lat_total, c_st_lat_total);
    $display("PERF[final]  stalls: lduse_cyc=%0d lduse_ev=%0d mdu_ev=%0d | branches: taken=%0d ntaken=%0d jal=%0d jalr=%0d",
      c_lduse_cyc, c_lduse_ev, c_mdu_ev, c_br_taken, c_br_ntaken, c_jal, c_jalr);
  end
endmodule

bind ysyx_22040750_cpu_core perf_counters u_perf (
  .I_clk(I_sys_clk), .I_rst(I_rst),
  .I_inst_valid(I_inst_valid),
  .I_mem_rd_data_valid(I_mem_rd_data_valid),
  .I_mem_wr_data_valid(I_mem_wr_data_valid),
  .O_mem_wen(O_mem_wen),
  .O_mem_addr(O_mem_addr),
  .O_pc_valid(O_pc_valid),
  .I_pc_ready(I_pc_ready),
  .O_pc(O_pc),
  .EX_MEM_mem_rd_en(EX_MEM_mem_rd_en),
  .ID_EX_alu_multicycle(ID_EX_alu_multicycle),
  .IF_ID_valid(IF_ID_valid), .ID_EX_allowin(ID_EX_allowin), .IF_ID_bubble(IF_ID_bubble),
  .ID_EX_valid(ID_EX_valid), .EX_MEM_allowin(EX_MEM_allowin), .ID_EX_bubble(ID_EX_bubble),
  .dnpc_sel(dnpc_sel), .mem_wen(mem_wen), .mem_rstrb(mem_rstrb),
  .csr_wen(csr_wen), .csr_mret(csr_mret), .csr_intr(csr_intr),
  .reg_wen(reg_wen),
  .MEM_WB_inst(MEM_WB_inst), .MEM_WB_valid(MEM_WB_valid),
  .MEM_WB_pc(MEM_WB_pc),
  .difftest_valid(difftest_valid),
  .I_IF_ID_stall(IF_ID_stall),
  .I_ID_EX_stall(ID_EX_stall), .I_EX_MEM_stall(EX_MEM_stall),
  .I_ID_EX_mem_rd_en(ID_EX_regin_sel[1]), .I_EX_MEM_mem_rd_en(EX_MEM_regin_sel[1]),
  .I_ID_EX_input_valid(ID_EX_input_valid), .I_ID_EX_alu_mlt(ID_EX_alu_op_sel[13:10]),
  .I_IF_ID_inst(IF_ID_inst)
);
