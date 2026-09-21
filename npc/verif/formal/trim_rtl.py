#!/usr/bin/env python3
# 从 ysyx_22040750.v 抽取出供 yosys/sby 形式化用的自包含模块块。
#   - 既有集合：radix2_div / dcachectrl / axiburst2xxx / icachectrl（div/axiburst/icache sby 用）；
#   - 新增：`ysyx_22040750_cpu_core` 的依赖闭包（pipeline.sby 用，B4-Q5）；
#   - 处理：去掉 DPI-C import / initial set_gpr_ptr / 修 0 位宽字面量（yosys 不识别的写法）。
import re
import sys

EXTRA_TOPS = ["ysyx_22040750_cpu_core"]


PROBE_PORTS = """
    // ---- formal-only probes（B4-Q5 pipeline.sby 用；仅形式化抽取文件，不改核 RTL）----
    ,output [31:0] PROBE_MEM_WB_pc
    ,output [31:0] PROBE_MEM_WB_inst
    ,output        PROBE_difftest_valid
    ,output        PROBE_MEM_WB_reg_wen
    ,output [4:0]  PROBE_MEM_WB_rd_addr
    ,output [63:0] PROBE_wr_data
    ,output        PROBE_EX_MEM_mem_rd_en
    ,output        PROBE_EX_MEM_mem_wr_en
    ,output [31:0] PROBE_EX_MEM_mem_addr
    ,output [31:0] PROBE_O_pc
    ,output [31:0] PROBE_IF_ID_pc
    ,output [31:0] PROBE_current_pc
    ,output [63:0] PROBE_rs1_data
    ,output [63:0] PROBE_rs1_fwd
    ,output [63:0] PROBE_ID_EX_rs1
"""

PROBE_BODY = """
    // ---- formal-only probes ----
    assign PROBE_MEM_WB_pc       = MEM_WB_pc;
    assign PROBE_MEM_WB_inst     = MEM_WB_inst;
    assign PROBE_difftest_valid  = difftest_valid;
    assign PROBE_MEM_WB_reg_wen  = MEM_WB_reg_wen;
    assign PROBE_MEM_WB_rd_addr  = MEM_WB_rd_addr;
    assign PROBE_wr_data         = wr_data;
    assign PROBE_EX_MEM_mem_rd_en = EX_MEM_mem_rd_en;
    assign PROBE_EX_MEM_mem_wr_en = EX_MEM_mem_wr_en;
    assign PROBE_EX_MEM_mem_addr  = EX_MEM_mem_addr;
    assign PROBE_O_pc             = O_pc;
    assign PROBE_IF_ID_pc         = IF_ID_pc;
    assign PROBE_current_pc       = current_pc;
    assign PROBE_rs1_data         = rs1_data;
    assign PROBE_rs1_fwd          = rs1_forward_data;
    assign PROBE_ID_EX_rs1        = ID_EX_rs1;
"""


def add_pipeline_probes(code):
    """给 cpu_core 注入探针端口/连线（yosys 不支持层次引用）。"""
    name = "ysyx_22040750_cpu_core"
    m = re.search(r'(?ms)^module\s+' + name + r'\b.*?^endmodule', code)
    if not m:
        return code
    body = m.group(0)
    i = body.find(");")                      # 端口列表结束
    if i < 0:
        return code
    body2 = body[:i] + PROBE_PORTS + body[i:]
    j = body2.rfind("endmodule")
    body2 = body2[:j] + PROBE_BODY + body2[j:]
    return code[:m.start()] + body2 + code[m.end():]


def strip_bad(code):
    code = re.sub(r'^\s*import\s+"DPI-C".*?;\s*$', '', code, flags=re.M)
    code = re.sub(r'^\s*(?:initial\s+)?sim_end\s*\(.*?\)\s*;\s*$', ';', code, flags=re.M)  # 保留空语句
    code = re.sub(r'^\s*(?:initial\s+)?set_\w+\s*\(.*?\)\s*;\s*$',
                  '', code, flags=re.M)  # DPI 调用点
    return code.replace("0'h08", "8'h08")


def main():
    src = open(sys.argv[1]).read()
    mods = {}
    for m in re.finditer(r"(?ms)^module\s+(\w+).*?^endmodule", src):
        mods[m.group(1)] = m.group(0)
    keep = {"ysyx_22040750_radix2_div", "ysyx_22040750_dcachectrl",
            "ysyx_22040750_axiburst2xxx", "ysyx_22040750_icachectrl"}
    todo = list(EXTRA_TOPS)
    seen = set()
    while todo:
        name = todo.pop()
        if name in seen or name not in mods:
            continue
        seen.add(name)
        keep.add(name)
        body = mods[name]
        for inst in re.finditer(
                r'\b(ysyx_22040750_\w+)\b(?:\s*#\s*\([^;]*?\))?\s+\w+\s*\(', body):
            todo.append(inst.group(1))
    out = [strip_bad(mods[n]) for n in mods if n in keep]
    text = "\n\n".join(out)
    text = add_pipeline_probes(text)
    open(sys.argv[2], "w").write(text)
    print(f"[trim_rtl] extracted {len(out)} modules: {sorted(keep)}")


if __name__ == "__main__":
    main()
