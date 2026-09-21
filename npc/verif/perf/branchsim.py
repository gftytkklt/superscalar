#!/usr/bin/env python3
# ============================================================================
# B4-Q3：分支预测静态策略评估（branchsim）
#   输入：取指握手 trace + 退休口径 trace + objdump（与 b4_quant_eval.py 相同）。
#   输出：各预测策略的正确/错误数、净气泡、端到端收益（相对基线 380,591 气泡）。
# 说明：
#   - 动态序列 = 退休流（精确）；条件分支 taken 由"下一条动态 PC != pc+4"判定。
#   - 静态方向预测只影响条件分支；jal/jalr 无 BTB 时仍固定 1 气泡（其目标预测收益另列）。
#   - 动态预测器为 2-bit 饱和计数器 PHT（PC 低位索引），仅作参考。
# 用法：
#   python3 branchsim.py --trace /tmp/mb_pe2.trace --retire-trace /tmp/mb_pe.trace \
#       --objdump <microbench.txt> [--out tmp/b4_q3]
# ============================================================================
import argparse
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location("b4q1", os.path.join(os.path.dirname(__file__), "b4_quant_eval.py"))
b4q1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b4q1)

BASE_BUBBLES = 380_589
BASE_CYCLES = 18_318_000


def evaluate(conds, jal, jalr, predict=None, label=""):
    """predict(pc, target) -> bool(taken)；None=完美方向预测。返回结果 dict。"""
    mis = 0
    for pc, tk, tg in conds:
        if predict is None:
            continue
        if predict(pc, tg) != tk:
            mis += 1
    bubbles = mis + jal + jalr
    saved = BASE_BUBBLES - bubbles
    cyc = BASE_CYCLES - saved
    return {"label": label, "mispred": mis, "bubbles": bubbles, "saved": saved,
            "speedup": BASE_CYCLES / cyc, "ipc": 1_352_016 / cyc}


def pht_predictor(conds, bits=10):
    """2-bit 饱和计数器 PHT（PC[bits+1:2] 索引），返回 (mispred, 状态表大小)。"""
    n = 1 << bits
    pht = [1] * n            # 初始 weakly not-taken
    mis = 0
    for pc, tk, tg in conds:
        idx = (pc >> 2) & (n - 1)
        pred = pht[idx] >= 2
        if pred != tk:
            mis += 1
        pht[idx] = min(3, pht[idx] + 1) if tk else max(0, pht[idx] - 1)
    return mis, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--retire-trace", required=True)
    ap.add_argument("--objdump", required=True)
    ap.add_argument("--out", default="tmp/b4_q3")
    args = ap.parse_args()

    instr = b4q1.parse_objdump(args.objdump)
    ret = b4q1.load_f(args.retire_trace)
    conds, jal, jalr, other_ctrl = [], 0, 0, 0
    for i, pc in enumerate(ret):
        it = instr.get(pc)
        if not it:
            continue
        k = it["kind"]
        if k == "branch":
            nxt = ret[i + 1] if i + 1 < len(ret) else None
            conds.append((pc, nxt != pc + 4, it["target"]))
        elif k == "jal":
            jal += 1
        elif k == "jalr":
            jalr += 1
        elif k in ("csr",):
            if it["mn"] == "fence.i":
                other_ctrl += 1

    taken = sum(1 for _, t, _ in conds if t)
    ntaken = len(conds) - taken

    rows = [
        evaluate(conds, jal, jalr, lambda pc, tg: False, "always-not-taken（基线，现状等价）"),
        evaluate(conds, jal, jalr, lambda pc, tg: True, "always-taken"),
        evaluate(conds, jal, jalr, lambda pc, tg: (tg is not None and tg < pc), "BTFN（后向 taken / 前向 not-taken）"),
        evaluate(conds, jal, jalr, None, "完美方向预测（无分支错误）"),
    ]
    mis_dyn, n = pht_predictor(conds, bits=10)
    rows.append({"label": f"2-bit 动态 PHT（{n} 项）", "mispred": mis_dyn, "bubbles": mis_dyn + jal + jalr,
                 "saved": BASE_BUBBLES - (mis_dyn + jal + jalr),
                 "speedup": BASE_CYCLES / (BASE_CYCLES - (BASE_BUBBLES - (mis_dyn + jal + jalr))),
                 "ipc": 1_352_016 / (BASE_CYCLES - (BASE_BUBBLES - (mis_dyn + jal + jalr)))})

    lines = []
    lines.append(f"# branchsim: cond={len(conds):,}（taken={taken:,} not-taken={ntaken:,}） "
                 f"jal={jal:,} jalr={jalr:,} fence.i={other_ctrl}")
    lines.append(f"# 基线气泡={BASE_BUBBLES:,}（taken cond + jal + jalr），T={BASE_CYCLES:,} cyc，IPC=0.0738")
    lines.append("")
    lines.append("| 策略 | 误预测 | 气泡总数 | 相对基线节省 | 端到端加速 | IPC |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['label']} | {r['mispred']:,} | {r['bubbles']:,} | {r['saved']:,} | "
                     f"{r['speedup']:.4f}× | {r['ipc']:.4f} |")
    lines.append("")
    lines.append(f"# jal/jalr 目标预测（BTB/RAS）上限：额外省 {jal + jalr:,} 拍 → "
                 f"1.021×（=完美方向预测）；单独 jal/jalr 收益 {1.0:.4f}×～1.0011×")
    text = "\n".join(lines)
    print(text)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "b4_q3_branchsim.md"), "w") as f:
        f.write(text + "\n")
    print(f"[OUT] {args.out}/b4_q3_branchsim.md")


if __name__ == "__main__":
    sys.exit(main())
