#!/usr/bin/env python3
# 从 vsrc 的 ysyx_22040750_dcachectrl 端口表生成两个几何采样 wrapper（base=32B/4KB、A=64B/8KB）。
# 用法（在 verif/sta 目录）：python3 probe/gen_dcache_geo_wrappers.py
# 说明：wrapper 不例化 SRAM（SRAM 在综合中为黑盒/不驱动），用于同流程下比较"逻辑面积（不含
# SRAM）"；与 P-B 探针同一 nangate45 目标流程（probe_run.sh）。
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
STA = os.path.dirname(HERE)
SRC = os.path.join(STA, '..', '..', 'vsrc', 'ysyx_22040750.v')

src = open(SRC, encoding='utf-8').read()
m = re.search(r'module ysyx_22040750_dcachectrl #\((.*?)\n\)\(\n(.*?)\n\);', src, re.S)
params_txt, ports_txt = m.group(1), m.group(2)
ports = []
for line in ports_txt.splitlines():
    line = line.strip().rstrip(',')
    mm = re.match(r'(input|output)\s+(reg\s+)?(\[[^\]]+\]\s+)?(\w+)', line)
    if mm:
        ports.append((mm.group(1), mm.group(3) or '', mm.group(4)))

def emit(name, blk, cache, grp):
    wayw = blk * 8
    lines = ["// 自动生成（verif/sta/probe/gen_dcache_geo_wrappers.py）：dcache 几何采样包装",
             f"// 参数：BLOCK_SIZE={blk}, CACHE_SIZE={cache}, GROUP_NUM={grp}（SRAM 未例化/黑盒）",
             f"module {name}(",
             "  input clk, input rst,"]
    decl = []
    for d, w, n in ports:
        if n in ('I_clk', 'I_rst'):
            continue
        width = w.replace('WAY_W', str(wayw))
        decl.append(f"  {d} {width}{n}".replace('  ', ' ').rstrip())
    lines.append(",\n".join("  " + d.lstrip() for d in decl))
    lines.append(");")
    lines.append(f"  ysyx_22040750_dcachectrl #(.BLOCK_SIZE({blk}), .CACHE_SIZE({cache}), .GROUP_NUM({grp})) u_dut (")
    conns = []
    for d, w, n in ports:
        if n == 'I_clk':
            conns.append("    .I_clk(clk)")
        elif n == 'I_rst':
            conns.append("    .I_rst(rst)")
        else:
            conns.append(f"    .{n}({n})")
    lines.append(",\n".join(conns))
    lines.append("  );")
    lines.append("endmodule")
    return "\n".join(lines) + "\n"

open(os.path.join(HERE, 'probe_dcache_geo_base.v'), 'w', encoding='utf-8').write(
    emit('ysyx_22040750_probe_dcache_geo_base', 32, 4096, 2))
open(os.path.join(HERE, 'probe_dcache_geo_A.v'), 'w', encoding='utf-8').write(
    emit('ysyx_22040750_probe_dcache_geo_A', 64, 8192, 2))
print("wrappers written: probe_dcache_geo_{base,A}.v")
