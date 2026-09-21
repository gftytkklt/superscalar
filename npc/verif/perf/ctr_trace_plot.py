#!/usr/bin/env python3
# ============================================================================
# B3 补充（讲义"性能计数器的trace"）：读 PERF_CTR_TRACE CSV（perf_counters.sv 每 10 万周期
# 一行），绘制性能计数器随时间的变化曲线 + 区间指标（IPC / 取指等待 / 气泡 / 指令类别构成）。
# 用法：python3 ctr_trace_plot.py <ctr.csv> [--out DIR] [--smooth N] [--no-plot]
# 生成 CSV 的仿真命令（microbench test；与 make perf 同条件）：
#   cd am-kernels/benchmarks/microbench
#   PERF_CTR_TRACE=/path/ctr.csv make ARCH=riscv64-npc HEAP_SIZE=0x400000 WITH_TRACE=0 PERF=1 mainargs=test run
# ============================================================================
import argparse
import os
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser(description="性能计数器 trace 绘图")
    ap.add_argument("csv")
    ap.add_argument("--out", default="tmp/ctr_trace", help="输出目录（默认 tmp/ctr_trace）")
    ap.add_argument("--smooth", type=int, default=3, help="区间 IPC 的滚动平均窗口（默认 3）")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    data = np.genfromtxt(args.csv, delimiter=",", names=True)
    if data.size == 0:
        print("空 CSV", file=sys.stderr)
        return 1
    n = len(data["cycle"])
    cyc, ret = data["cycle"], data["retire"]
    dcyc = np.diff(cyc, prepend=0.0)
    dret = np.diff(ret, prepend=0.0)
    ipc = np.divide(dret, dcyc, out=np.zeros(n), where=dcyc > 0)
    smooth = max(1, args.smooth)
    kern = np.ones(smooth) / smooth
    ipc_s = np.convolve(ipc, kern, mode="same")
    overall_ipc = ret[-1] / cyc[-1] if cyc[-1] else 0

    dmis = np.diff(data["ifu_miss"], prepend=0.0) / np.maximum(dcyc, 1)
    dbub = np.diff(data["bubble"], prepend=0.0) / np.maximum(dcyc, 1)
    dmem = np.diff(data["mem"], prepend=0.0) / np.maximum(dcyc, 1)
    dbr = np.diff(data["branch"], prepend=0.0) / np.maximum(dcyc, 1)
    dco = np.diff(data["compute"], prepend=0.0) / np.maximum(dcyc, 1)
    dot = np.diff(data["other"], prepend=0.0) / np.maximum(dcyc, 1)
    dcsr = np.diff(data["csr"], prepend=0.0) / np.maximum(dcyc, 1)

    print(f"# trace={args.csv}  points={n}  cycles={cyc[-1]:,.0f}  retire={ret[-1]:,.0f}  IPC={overall_ipc:.4f}")
    print(f"# interval IPC: mean={ipc.mean():.4f} p50={np.percentile(ipc,50):.4f} "
          f"p90={np.percentile(ipc,90):.4f} max={ipc.max():.4f}")
    print(f"# fetch-wait(ifu_miss)/cyc: mean={dmis.mean():.3f}  bubble/cyc: mean={dbub.mean():.3f} "
          f"| classes/cyc: mem={dmem.mean():.3f} branch={dbr.mean():.3f} compute={dco.mean():.3f} "
          f"other={dot.mean():.3f} csr={dcsr.mean():.4f}")

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "ctr_trace_summary.md"), "w") as f:
        f.write(f"# trace={args.csv} points={n} cycles={cyc[-1]:,.0f} retire={ret[-1]:,.0f} IPC={overall_ipc:.4f}\n\n")
        f.write("| interval(万周期) | Δcycles | Δretire | IPC | ifu_miss/cyc | bubble/cyc |\n|---|---|---|---|---|---|\n")
        for i in range(n):
            f.write(f"| {i+1} | {dcyc[i]:,.0f} | {dret[i]:,.0f} | {ipc[i]:.4f} | {dmis[i]:.3f} | {dbub[i]:.3f} |\n")

    if not args.no_plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x = cyc / 1e6
        fig, ax = plt.subplots(2, 2, figsize=(14, 10))

        ax[0, 0].plot(x, ret, lw=1.0, label="retire", color="tab:blue")
        ax[0, 0].plot(x, data["deliver"], lw=0.8, label="deliver (fetched slots)", color="tab:orange")
        ax[0, 0].set(title="Cumulative counters vs time", xlabel="cycles (M)", ylabel="count")
        ax[0, 0].legend(fontsize=8)
        ax[0, 0].grid(alpha=0.3)

        ax[0, 1].plot(x, ipc, lw=0.6, color="lightgray", label="per-interval IPC")
        ax[0, 1].plot(x, ipc_s, lw=1.2, color="tab:red", label=f"IPC (rolling {smooth})")
        ax[0, 1].axhline(overall_ipc, ls="--", lw=1.0, color="black", label=f"overall IPC={overall_ipc:.4f}")
        ax[0, 1].set(title="IPC over time (interval = 100k cycles)", xlabel="cycles (M)", ylabel="IPC")
        ax[0, 1].legend(fontsize=8)
        ax[0, 1].grid(alpha=0.3)

        ax[1, 0].plot(x, dmis, lw=1.0, label="ifu_miss / cycle (fetch wait)", color="tab:purple")
        ax[1, 0].plot(x, dbub, lw=1.0, label="bubble / cycle (flushed fetch)", color="tab:brown")
        ax[1, 0].set(title="Frontend stalls over time", xlabel="cycles (M)", ylabel="fraction")
        ax[1, 0].legend(fontsize=8)
        ax[1, 0].grid(alpha=0.3)

        ax[1, 1].stackplot(x, dmem, dbr, dco, dot, dcsr,
                           labels=["mem", "branch", "compute", "other", "csr"], alpha=0.8)
        ax[1, 1].set(title="Decoded instruction classes per cycle (interval)", xlabel="cycles (M)",
                     ylabel="instructions/cycle")
        ax[1, 1].legend(fontsize=8, loc="upper right")
        fig.tight_layout()
        png = os.path.join(args.out, "ctr_trace.png")
        fig.savefig(png, dpi=130)
        print(f"[PNG] {png}")
    print(f"[OUT] {args.out}/ctr_trace_summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
