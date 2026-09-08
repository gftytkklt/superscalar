#!/usr/bin/env python3
# 从 ysyx_22040750.v 生成供 yosys-sta 综合的 RTL（E1a：npc 可综合化适配）。
# 处理：
#   1) 删除所有 `import "DPI-C" ...` 行（yosys 无法综合 DPI）；
#   2) 删除调用 DPI 函数的 always/initial 块（set_diff_ptr/set_mmio_ptr/set_wb_pc_ptr/
#      set_wb_inst_ptr/sim_end）；
#   3) 把行为级 SRAM（ysyx_22040750_sram_behav）替换为 (* blackbox *) 桩（无 SRAM 宏库，
#      时序不覆盖 SRAM 内部路径 —— 报告频率相对乐观，已在文档注明）。
#   4) 顺带删除 `define 产生的宽度字面量问题（沿用 trim_rtl.py 的 0'h08 修正，如有）。
import re, sys

def main():
    src = open(sys.argv[1]).read()
    lines = src.split('\n')
    out = []
    i = 0
    n = len(lines)
    DPI_CALL = re.compile(r'set_diff_ptr|set_mmio_ptr|set_wb_pc_ptr|set_wb_inst_ptr|set_gpr_ptr|sim_end\s*\(')
    while i < n:
        L = lines[i]
        # 1) DPI import 行
        if 'import "DPI-C"' in L:
            i += 1; continue
        # 2) initial <dpi call>;
        if L.strip().startswith('initial') and DPI_CALL.search(L):
            i += 1; continue
        # 2') always @(*) begin \n <dpi call> \n end  （三行小块）
        if L.strip().startswith('always @(*) begin') and i + 2 < n and DPI_CALL.search(lines[i+1]) \
           and lines[i+2].strip() == 'end':
            i += 3; continue
        # 2'') sim_end 块: always @(posedge ...) \n if (simend) \n sim_end();
        if L.strip().startswith('always @(posedge') and i + 2 < n and 'simend' in lines[i+1] \
           and 'sim_end()' in lines[i+2]:
            i += 3; continue
        out.append(L)
        i += 1
    text = '\n'.join(out).replace("0'h08", "8'h08")
    # 3) blackbox 行为级 SRAM
    text = re.sub(
        r"(?ms)^module ysyx_22040750_sram_behav\(.*?^endmodule",
        "(* blackbox *)\nmodule ysyx_22040750_sram_behav(\n"
        "    input I_clk, input CEN, input WEN, input [127:0] BWEN,\n"
        "    input [5:0] A, input [127:0] D, output [127:0] Q\n"
        ");\nendmodule",
        text)
    open(sys.argv[2], 'w').write(text)
    # 汇报
    removed_import = sum(1 for l in lines if 'import "DPI-C"' in l and l not in out)
    print(f"gen_synth_rtl: {sys.argv[2]} written; DPI imports removed={removed_import}, "
          f"sram_behav blackboxed={'(* blackbox *)' in text}")

if __name__ == '__main__':
    main()
