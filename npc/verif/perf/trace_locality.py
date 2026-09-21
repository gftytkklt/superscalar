#!/usr/bin/env python3
# ============================================================================
# P-H/H1（讲义 #12）：CACHESIM_TRACE 二次处理 —— 观察程序的局部性。
#   trace 格式（npc 仿真导出，csrc/trace.cpp）：每行 "F/R/W <32bit hex addr>"
#     F = icache 取指握手拍、R/W = LSU 读写请求（见 perf_counters.sv）
#   输出：
#     1) 汇总表：每流的访问数、unique 行、区域分布、同线/邻近线占比、相邻行距、重用间隔分位；
#     2) 四联图（PNG）：窗口工作集曲线（时间局部性）、相邻访问距离直方（空间局部性）、
#        重用间隔直方（时间局部性）、区域占比；
#     3) 曲线 CSV（工作集 / 直方）。
# 用法：
#   python3 trace_locality.py /tmp/mb_pe.trace [--out tmp/ph_h1] [--line 64]
#                             [--window 4096] [--max 0] [--streams F,R,W] [--no-plot]
# ============================================================================
import os
import sys
import argparse
import numpy as np

# 与 dcache_stats.sv / cachesim RegionCost 相同的区域口径（上界开区间）
REGIONS = [
    ("PSRAM", 0x80000000, 0x80400000),
    ("flash", 0x30000000, 0x40000000),
    ("SDRAM", 0xA0000000, 0xA8000000),
    ("SRAM",  0x0F000000, 0x0F002000),
]


def region_of(addrs):
    names = np.full(addrs.shape, "MMIO", dtype="U5")
    for name, lo, hi in REGIONS:
        m = (addrs >= lo) & (addrs < hi)
        names[m] = name
    return names


def parse_trace(path, streams, max_n):
    ops, addrs = [], []
    with open(path, "r") as f:
        for ln in f:
            if len(ln) < 3 or ln[0] not in streams:
                continue
            try:
                a = int(ln[2:].strip(), 16)
            except ValueError:
                continue
            ops.append(ln[0])
            addrs.append(a)
            if max_n and len(addrs) >= max_n:
                break
    return np.array(ops, dtype="U1"), np.array(addrs, dtype=np.uint64)


def stream_stats(op, addrs, line):
    """单流统计：返回 dict。addrs 按时间序。"""
    n = len(addrs)
    st = {"n": n}
    if n == 0:
        return st
    lines = addrs // line
    st["unique"] = int(np.unique(lines).size)
    st["regions"] = {r: int(c) for r, c in zip(*np.unique(region_of(addrs), return_counts=True))}

    if n > 1:
        dl = np.abs(np.diff(lines.astype(np.int64)))
        st["same_line"] = float(np.mean(dl == 0))
        st["near_line"] = float(np.mean(dl <= 1))          # 同行或相邻行
        st["seq_fwd"] = float(np.mean(np.diff(lines.astype(np.int64)) == 1))  # 严格顺序前进
        st["dist_mean"] = float(dl.mean())
        st["dist_p50"] = float(np.percentile(dl, 50))
        st["dist_hist"] = np.bincount(np.minimum(np.log2(dl + 1).astype(np.int64), 31), minlength=32)
    else:
        st.update(same_line=0.0, near_line=0.0, seq_fwd=0.0, dist_mean=0.0,
                  dist_p50=0.0, dist_hist=np.zeros(32, dtype=np.int64))

    # 重用间隔：同一行两次访问之间隔了多少次本流访问（时间局部性近似，同 cachesim 的 LRU 近似口径）
    last = {}
    gaps = np.empty(n, dtype=np.int64)
    gaps[0] = -1
    last[int(lines[0])] = 0
    for i in range(1, n):
        li = int(lines[i])
        p = last.get(li, -1)
        gaps[i] = i - p if p >= 0 else -1
        last[li] = i
    g = gaps[gaps > 0]
    st["reuse_n"] = int(g.size)
    if g.size:
        st["gap_p50"] = float(np.percentile(g, 50))
        st["gap_p90"] = float(np.percentile(g, 90))
        st["gap_p99"] = float(np.percentile(g, 99))
        st["gap_le64"] = float(np.mean(g <= 64))
        st["gap_hist"] = np.bincount(np.minimum(np.log2(g).astype(np.int64), 31), minlength=32)
    else:
        st.update(gap_p50=0, gap_p90=0, gap_p99=0, gap_le64=0.0, gap_hist=np.zeros(32, dtype=np.int64))
    return st


def working_set(lines, window):
    """按窗口统计 unique 行数，返回 (窗口结束访问号, unique 数)。"""
    ends, uniq = [], []
    for s in range(0, len(lines), window):
        chunk = lines[s:s + window]
        ends.append(min(s + window, len(lines)))
        uniq.append(int(np.unique(chunk).size))
    return np.array(ends), np.array(uniq)


def main():
    ap = argparse.ArgumentParser(description="trace 局部性分析（#12）")
    ap.add_argument("trace")
    ap.add_argument("--out", default="tmp/ph_h1", help="输出目录（默认 tmp/ph_h1）")
    ap.add_argument("--line", type=int, default=64, help="行粒度(字节)，默认 64")
    ap.add_argument("--window", type=int, default=4096, help="工作集窗口(访问数)，默认 4096")
    ap.add_argument("--max", type=int, default=0, help="最多读取访问数（0=全部）")
    ap.add_argument("--streams", default="F,R,W")
    ap.add_argument("--cacheable-only", action="store_true",
                    help="仅保留可缓存区(PSRAM/flash/SDRAM)——剔除 RTL 非缓存的 SRAM/MMIO（如 UART 轮询）")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    streams = [s for s in args.streams.split(",") if s]
    ops, addrs = parse_trace(args.trace, set(streams), args.max)
    if args.cacheable_only:
        keep = np.zeros(addrs.shape, dtype=bool)
        for _, lo, hi in REGIONS:
            if hi != 0x0F002000:            # SRAM 在 RTL 中按 MMIO 处理（故意非缓存）
                keep |= (addrs >= lo) & (addrs < hi)
        ops, addrs = ops[keep], addrs[keep]
    if ops.size == 0:
        print("空 trace（或 --streams 过滤后为空）", file=sys.stderr)
        return 1
    os.makedirs(args.out, exist_ok=True)
    size_mb = os.path.getsize(args.trace) / 1e6

    report, curves = [], {}
    for s in streams:
        idx = np.where(ops == s)[0]
        st = stream_stats(s, addrs[idx], args.line)
        curves[s] = working_set(addrs[idx] // args.line, args.window) if st["n"] else (np.array([]), np.array([]))
        report.append((s, st))

    # ---- 汇总表 ----
    lines_out = [
        f"# trace={args.trace}  size={size_mb:.1f}MB  accesses={ops.size:,}  line={args.line}B  window={args.window}",
        "",
        "| stream | accesses | unique_lines | regions(top) | same_line% | near_line% | seq_fwd% | dist_mean | dist_p50 | gap_p50 | gap_p90 | gap<=64% |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s, st in report:
        if st["n"] == 0:
            lines_out.append(f"| {s} | 0 | - | - | - | - | - | - | - | - | - | - |")
            continue
        top = " ".join(f"{k}:{100.0*v/st['n']:.1f}%" for k, v in
                       sorted(st["regions"].items(), key=lambda kv: -kv[1])[:3])
        lines_out.append(
            f"| {s} | {st['n']:,} | {st['unique']:,} | {top} | {100*st['same_line']:.1f} | "
            f"{100*st['near_line']:.1f} | {100*st['seq_fwd']:.1f} | {st['dist_mean']:.0f} | "
            f"{st['dist_p50']:.0f} | {st['gap_p50']:.0f} | {st['gap_p90']:.0f} | {100*st['gap_le64']:.1f} |")
    table = "\n".join(lines_out)
    print(table)
    with open(os.path.join(args.out, "locality_summary.md"), "w") as f:
        f.write(table + "\n")

    # ---- CSV ----
    with open(os.path.join(args.out, "locality_working_set.csv"), "w") as f:
        f.write("stream,end_access,unique_lines\n")
        for s, (ends, uniq) in curves.items():
            for e, u in zip(ends, uniq):
                f.write(f"{s},{e},{u}\n")
    with open(os.path.join(args.out, "locality_hist.csv"), "w") as f:
        f.write("stream,kind,log2bin,count\n")
        for s, st in report:
            if not st["n"]:
                continue
            for i, c in enumerate(st["dist_hist"]):
                f.write(f"{s},dist,{i},{c}\n")
            for i, c in enumerate(st["gap_hist"]):
                f.write(f"{s},gap,{i},{c}\n")

    # ---- 绘图（英文标签，避免字体缺字）----
    if not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(2, 2, figsize=(14, 10))
        colors = {"F": "tab:blue", "R": "tab:green", "W": "tab:red"}

        for s, (ends, uniq) in curves.items():
            if len(ends):
                ax[0, 0].plot(ends / 1e6, uniq, lw=1.0, label=f"{s} ({len(uniq)} win)", color=colors.get(s))
        ax[0, 0].set(title=f"Working-set curve (unique {args.line}B lines / {args.window} accesses)",
                     xlabel="access index (M)", ylabel="unique lines")
        ax[0, 0].set_yscale("log")
        ax[0, 0].legend(fontsize=8)
        ax[0, 0].grid(alpha=0.3)

        for s, st in report:
            if not st["n"]:
                continue
            h = st["dist_hist"].astype(float)
            h = h / h.sum()
            x = np.arange(32)
            ax[0, 1].step(x, h, where="mid", label=s, color=colors.get(s))
        ax[0, 1].set(title="Adjacent access line-distance (spatial locality)",
                     xlabel="log2(|line_i - line_{i-1}| + 1)  [0 = same line]", ylabel="fraction")
        ax[0, 1].set_yscale("log")
        ax[0, 1].legend(fontsize=8)
        ax[0, 1].grid(alpha=0.3)

        for s, st in report:
            if not st["n"]:
                continue
            h = st["gap_hist"].astype(float)
            h = h / h.sum()
            x = np.arange(32)
            ax[1, 0].step(x, h, where="mid", label=s, color=colors.get(s))
        ax[1, 0].set(title="Reuse gap (temporal locality; same line re-touched after N accesses)",
                     xlabel="log2(gap)  [first touch excluded]", ylabel="fraction")
        ax[1, 0].set_yscale("log")
        ax[1, 0].legend(fontsize=8)
        ax[1, 0].grid(alpha=0.3)

        reg_names = [r for r, _, _ in REGIONS] + ["MMIO"]
        bottom = np.zeros(len(streams))
        for r in reg_names:
            frac = np.array([st["regions"].get(r, 0) / st["n"] if st["n"] else 0
                             for _, st in report])
            if frac.sum() > 0:
                ax[1, 1].bar(streams, frac, bottom=bottom, label=r)
                bottom += frac
        ax[1, 1].set(title="Access address-region mix", ylabel="fraction")
        ax[1, 1].legend(fontsize=8)
        fig.tight_layout()
        png = os.path.join(args.out, "locality.png")
        fig.savefig(png, dpi=130)
        print(f"\n[PNG] {png}")
    print(f"[OUT] {args.out}/locality_summary.md  locality_working_set.csv  locality_hist.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
