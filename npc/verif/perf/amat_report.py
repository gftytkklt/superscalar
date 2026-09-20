#!/usr/bin/env python3
# P-C 数据分析平台：从 make perf 日志解析性能计数器，输出 AMAT/TMT 表（讲义 #17/#27）。
# 用法：python3 amat_report.py <perf.log> [标签]
# 公式（讲义「缓存的优化」）：
#   AMAT = 命中时间 + 缺失率 × 缺失代价
#   icache AMAT = hit_lat + miss_rate × miss_penalty（全部实测）
#   dcache 侧：rd/wr 缺失率与代价实测；命中时间未单独计数（报告标 n/a，后续可加）
#   TMT = Σ 缺失代价（icache tmt_sum + dcache rd/wr 各区 avg×n）
# 注意：retire 随 UART 轮询时变（见 B3_STAGE7_RECALIB_PERF §2.1），跨配置只比 IPC/cycles/TMT。
import re, sys

def ints(s):
    return int(s) if s else 0

def main():
    log = open(sys.argv[1]).read()
    tag = sys.argv[2] if len(sys.argv) > 2 else "run"

    def g(pat, conv=float, default=0.0):
        m = re.search(pat, log)
        return conv(m.group(1)) if m else default

    # ---- 顶层 ----
    cycles = g(r"PERF\[final\]: cycles=(\d+)", int)
    retire = g(r"PERF\[final\]: cycles=\d+ retire=(\d+)", int)
    ipc = retire / cycles if cycles else 0

    # ---- icache ----
    i_hit = g(r"ICACHE_STAT: hit=(\d+)", int)
    i_miss = g(r"ICACHE_STAT: hit=\d+ miss=(\d+)", int)
    i_hlat = g(r"hit_lat\(avg=(\d+)", int)
    i_tmt = g(r"tmt_sum=(\d+)", int)
    i_rate = i_miss / (i_hit + i_miss) if (i_hit + i_miss) else 0.0

    def line_of(prefix):
        m = re.search(re.escape(prefix) + r"(.*)", log)
        return m.group(1) if m else ""

    def region_avg(line, name):
        # 在限定行内解析 "psram(avg=N n=M"
        m = re.search(name + r"\(avg=(\d+) n=(\d+)", line)
        return (ints(m.group(1)), ints(m.group(2))) if m else (0, 0)

    i_mp = {}
    ic_line = line_of("ICACHE_MISS_PENALTY:")
    for r in ["psram", "flash", "sdram", "sram_mmio", "other_mmio"]:
        i_mp[r] = region_avg(ic_line, r)
    # 加权 icache 缺失代价
    tot_n = sum(n for _, n in i_mp.values())
    i_cost = sum(a * n for a, n in i_mp.values()) / tot_n if tot_n else 0
    i_amat = i_hlat + i_rate * i_cost

    # ---- dcache ----
    d_rhit = g(r"DCACHE_STAT: rd_hit=(\d+)", int)
    d_rmiss = g(r"DCACHE_STAT: rd_hit=\d+ rd_miss=(\d+)", int)
    d_whit = g(r"wr_hit=(\d+)", int)
    d_wmiss = g(r"wr_hit=\d+ wr_miss=(\d+)", int)
    d_tmt = 0
    d_rows = []
    for kind, pat in [("rd", r"DCACHE_RD_MISS_PENALTY: (.*)"), ("wr", r"DCACHE_WR_MISS_PENALTY: (.*)")]:
        m = re.search(pat, log)
        if not m:
            continue
        for a, n in re.findall(r"\w+\(avg=(\d+) n=(\d+)", m.group(1)):
            d_tmt += ints(a) * ints(n)
            if ints(n):
                d_rows.append(f"{kind}:{n}×{a}")
    d_wrwb = g(r"wr_wb_cyc=(\d+)", int)
    d_mmio_line = line_of("DCACHE_MMIO_LAT:")
    m = re.search(r"sram\(avg=(\d+) n=(\d+)", d_mmio_line)
    d_mmio_sram = (ints(m.group(1)), ints(m.group(2))) if m else (0, 0)

    # ---- 输出 ----
    print(f"== AMAT/TMT 报告 [{tag}] ==")
    print(f"cycles={cycles:,}  retire={retire:,}  IPC={ipc:.4f}")
    print(f"icache: hit={i_hit:,} miss={i_miss:,} (缺失率 {i_rate*100:.2f}%)  hit_lat={i_hlat}  缺失代价(加权)={i_cost:.0f}")
    print(f"  icache AMAT = {i_hlat} + {i_rate*100:.2f}% × {i_cost:.0f} = {i_amat:.2f} cyc/取指")
    print(f"  icache 各区缺失代价: " + "  ".join(f"{r}={a}(n={n})" for r, (a, n) in i_mp.items() if n))
    print(f"dcache: rd {d_rhit:,}/{d_rmiss:,} ({(d_rmiss/(d_rhit+d_rmiss)*100 if d_rhit+d_rmiss else 0):.2f}%)  "
          f"wr {d_whit:,}/{d_wmiss:,} ({(d_wmiss/(d_whit+d_wmiss)*100 if d_whit+d_wmiss else 0):.2f}%)")
    print(f"  dcache TMT 组成: {' '.join(d_rows)}  (wr_wb_cyc={d_wrwb:,})")
    print(f"  dcache MMIO(SRAM): avg={d_mmio_sram[0]} n={d_mmio_sram[1]}")
    print(f"TMT 总计 = icache {i_tmt:,} + dcache {d_tmt:,} = {i_tmt + d_tmt:,} cyc"
          f"（占 T {100.0 * (i_tmt + d_tmt) / cycles:.1f}%，注意部分等待可与流水重叠，口径见记录）")

if __name__ == "__main__":
    main()
