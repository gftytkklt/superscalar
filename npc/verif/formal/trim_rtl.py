#!/usr/bin/env python3
# 从 ysyx_22040750.v 抽取出供 yosys/sby 形式化用的自包含模块块。
# 只保留 radix2_div 与 dcachectrl（无 DPI-C），并修掉写 RTL 的 0 位宽字面量。
import re, sys

def main():
    src = open(sys.argv[1]).read()
    # 保留供 yosys/sby 形式化用的自包含模块块（无 DPI-C）
    keep = {"ysyx_22040750_radix2_div", "ysyx_22040750_dcachectrl",
            "ysyx_22040750_axiburst2xxx"}
    out = []
    for m in re.finditer(r"(?ms)^module\s+(\w+).*?^endmodule", src):
        if m.group(1) in keep:
            out.append(m.group(0).replace("0'h08", "8'h08"))
    open(sys.argv[2], "w").write("\n\n".join(out))

if __name__ == "__main__":
    main()