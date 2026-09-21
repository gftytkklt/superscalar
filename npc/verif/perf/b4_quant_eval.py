#!/usr/bin/env python3
# ============================================================================
# B4-Q1 量化评估 v2：精确重建"动态退休序列 + 气泡位置"，统计类别/分支细分/RAW 距离。
#   - 取指流（CACHESIM_TRACE，取指握手口径，F=1,732,607）与
#     退休流（同一程序早期导出的 retire 口径 trace，F=1,352,016）做**双指针对齐**：
#     取指流中与退休流当前项不匹配的记录 = 该拍被冲刷的取指（气泡），位置精确。
#   - 无需启发式；残余误差仅首尾 ±1。
# 用法：
#   python3 b4_quant_eval.py --trace /tmp/mb_pe2.trace --retire-trace /tmp/mb_pe.trace \
#       --objdump am-kernels/benchmarks/microbench/build/microbench-riscv64-npc.txt [--out tmp/b4_q1]
# ============================================================================
import argparse
import os
import re
import sys
from collections import Counter

REG = re.compile(r"^(x\d+|zero|ra|sp|gp|tp|t[0-6]|s\d+|a\d+)$")

R3 = {"add","sub","and","or","xor","sll","srl","sra","slt","sltu","mul","mulh","mulhsu",
      "mulhu","div","divu","rem","remu","addw","subw","sllw","srlw","sraw","mulw","divw",
      "divuw","remw","remuw"}
IMM = {"addi","andi","ori","xori","slti","sltiu","slli","srli","srai","addiw","slliw",
       "srliw","sraiw"}
LOADS = {"lb","lh","lw","ld","lbu","lhu","lwu"}
STORES = {"sb","sh","sw","sd"}
BR = {"beq","bne","blt","bge","bltu","bgeu"}
BRZ = {"beqz","bnez","blez","bgez","bltz","bgtz"}
CSR = {"csrrw","csrrs","csrrc","csrrwi","csrrsi","csrrci","ecall","ebreak","mret","fence.i",
       "csrr","csrw","csrs","csrc","fence"}


def parse_objdump(path):
    instr = {}
    pat = re.compile(r"^\s*([0-9a-f]+):\s+[0-9a-f ]+\s+(\S+)\s*(.*)$")
    for ln in open(path, encoding="utf-8", errors="ignore"):
        m = pat.match(ln)
        if m:
            instr[int(m.group(1), 16)] = {"mn": m.group(2), "ops": m.group(3).strip()}
    for pc, it in instr.items():
        mn, ops = it["mn"], it["ops"]
        parts = [p.strip() for p in ops.split(",")] if ops else []
        rd, srcs, kind, target = None, [], "compute", None

        def reg(s):
            s = s.strip()
            return s if REG.match(s) else None

        if mn in LOADS or mn in STORES:
            kind = "mem"
            if mn in LOADS:
                rd = reg(parts[0]) if parts else None
            elif parts:
                srcs.append(reg(parts[0]) or "")
            if len(parts) > 1:
                mm = re.search(r"\((\w+)\)", parts[1])
                if mm:
                    srcs.append(mm.group(1))
        elif mn in R3:
            rd, srcs = reg(parts[0]), [reg(x) for x in parts[1:3]]
        elif mn in IMM:
            rd, srcs = reg(parts[0]), [reg(parts[1]) if len(parts) > 1 else None]
        elif mn in ("lui", "auipc", "li"):
            rd = reg(parts[0])
        elif mn in ("mv", "not", "neg", "seqz", "snez", "sext.w"):
            rd, srcs = reg(parts[0]), [reg(parts[1]) if len(parts) > 1 else None]
        elif mn in BR:
            kind, srcs = "branch", [reg(parts[0]), reg(parts[1])]
            if len(parts) > 2 and re.match(r"^[0-9a-f]+$", parts[2].split()[0]):
                target = int(parts[2].split()[0], 16)
        elif mn in BRZ:
            kind, srcs = "branch", [reg(parts[0])]
            if len(parts) > 1 and re.match(r"^[0-9a-f]+$", parts[1].split()[0]):
                target = int(parts[1].split()[0], 16)
        elif mn in ("jal", "j"):
            kind = "jal"
            rd = None
            if mn == "jal":
                rd = reg(parts[0]) if len(parts) > 1 else "ra"
            if re.match(r"^[0-9a-f]+$", parts[-1].split()[0]):
                target = int(parts[-1].split()[0], 16)
        elif mn in ("jalr",) or mn == "jr":
            kind = "jalr"
            if mn == "jr":
                srcs = [reg(parts[0])] if parts else []
            else:
                rd = reg(parts[0]) if len(parts) > 1 else None
                srcs = [reg(parts[0])] if len(parts) == 1 else [reg(parts[1])]
                if len(parts) > 2 and re.match(r"^-?[0-9a-f]+$", parts[2].split()[0]):
                    try:
                        target = int(parts[2].split()[0], 16)
                    except ValueError:
                        target = None
        elif mn == "ret":
            kind, srcs, rd = "jalr", ["ra"], None
        elif mn in CSR:
            kind = "csr"
            if parts and reg(parts[0]):
                rd = reg(parts[0])
            for p in parts[1:]:
                if reg(p):
                    srcs.append(reg(p))
        else:
            kind = "compute"
            rd = reg(parts[0]) if parts else None
            srcs = [reg(x) for x in parts[1:]]
        it.update(kind=kind, rd=rd, srcs=[s for s in srcs if s], target=target)
    return instr


def load_f(path, maxn=0):
    out = []
    for ln in open(path):
        if ln[0] == "F":
            out.append(int(ln[2:], 16))
            if maxn and len(out) >= maxn:
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True, help="取指握手口径 trace")
    ap.add_argument("--retire-trace", required=False, help="退休口径 trace（同程序早期导出）")
    ap.add_argument("--objdump", required=True)
    ap.add_argument("--out", default="tmp/b4_q1")
    ap.add_argument("--max", type=int, default=0)
    args = ap.parse_args()

    instr = parse_objdump(args.objdump)
    fetch = load_f(args.trace, args.max)
    lines = [f"# fetch={args.trace} retire={args.retire_trace} objdump={args.objdump}"]

    if args.retire_trace:
        ret = load_f(args.retire_trace, args.max)
        # 双指针对齐：匹配=真实退休指令；不匹配=气泡（记录前一条真实指令的类型）
        i, bubbles, real = 0, Counter(), []
        bubble_after = Counter()
        unknown = 0
        for pc in fetch:
            if i < len(ret) and pc == ret[i]:
                real.append(pc)
                i += 1
            else:
                bubbles["total"] += 1
                prev = real[-1] if real else None
                k = instr[prev]["kind"] if prev in instr else "unknown"
                if k in ("branch", "jal", "jalr"):
                    bubble_after[k] += 1
                else:
                    bubble_after["other"] += 1
                if pc not in instr:
                    unknown += 1
        lines.append(f"# align: fetch={len(fetch):,} retire={len(ret):,} matched={i:,} "
                     f"bubbles={bubbles['total']:,} unknown_bubble_pc={unknown}")
        lines.append(f"# bubble attribution (by preceding real instr): "
                     + " ".join(f"{k}={v:,}" for k, v in sorted(bubble_after.items())))
        dyn = real
    else:
        # 旧启发式（无退休流时）：仅用于对照
        out, bubbles = [], 0
        for pc in fetch:
            if pc not in instr:
                continue
            if len(out) >= 2:
                b = instr.get(out[-2])
                if b and b["kind"] in ("branch", "jal", "jalr") and out[-1] == out[-2] + 4 and \
                   ((b["kind"] in ("jal", "jalr")) or (b["target"] is not None and pc == b["target"])):
                    out.pop()
                    bubbles += 1
            out.append(pc)
        lines.append(f"# heuristic: fetch={len(fetch):,} cleaned={len(out):,} bubbles={bubbles:,}")
        dyn = out

    lines.append("")
    cls, brk = Counter(), Counter()
    for pc in dyn:
        k = instr[pc]["kind"] if pc in instr else "unknown"
        cls[k] += 1
        if k in ("branch", "jal", "jalr"):
            brk[k] += 1
        if k == "branch":
            # taken = 下一条动态指令 != pc+4
            pass
    lines.append("| kind | dynamic | % |")
    lines.append("|---|---|---|")
    tot = sum(cls.values())
    for k, v in cls.most_common():
        lines.append(f"| {k} | {v:,} | {100*v/tot:.1f} |")
    lines.append("")
    lines.append("| control split | count |")
    lines.append("|---|---|")
    for k in ("branch", "jal", "jalr"):
        lines.append(f"| {k} | {brk[k]:,} |")
    # taken/not-taken（动态序列内下一条 PC 判定），标注取指流位置以计入气泡间距
    taken = Counter()
    for idx, pc in enumerate(dyn):
        it = instr.get(pc)
        if it and it["kind"] in ("branch", "jal", "jalr"):
            nxt = dyn[idx + 1] if idx + 1 < len(dyn) else None
            if it["kind"] == "branch":
                taken["taken" if nxt != pc + 4 else "not_taken"] += 1
            else:
                taken[it["kind"]] += 1
    lines.append("")
    lines.append("| branch outcome | count |")
    lines.append("|---|---|")
    for k in ("taken", "not_taken", "jal", "jalr"):
        lines.append(f"| {k} | {taken[k]:,} |")

    # RAW：按"流水槽位"距离（取指流中气泡占槽）；用取指流 + 气泡标记构造槽序列
    burst = []
    if args.retire_trace:
        i = 0
        for pc in fetch:
            if i < len(ret) and pc == ret[i]:
                burst.append(pc)
                i += 1
            else:
                burst.append(None)   # 气泡槽
        slots = burst
    else:
        slots = dyn
    raw = Counter()
    raw_load1 = 0
    for i in range(1, len(slots)):
        cons_pc = slots[i]
        if cons_pc is None or cons_pc not in instr:
            continue
        cons = instr[cons_pc]
        for d in (1, 2, 3):
            j = i - d
            if j < 0:
                break
            prod_pc = slots[j]
            if prod_pc is None or prod_pc not in instr:
                continue
            prod = instr[prod_pc]
            if prod["rd"] and prod["rd"] != "x0" and prod["rd"] in cons["srcs"]:
                raw[d] += 1
                if d == 1 and prod["kind"] == "mem":
                    raw_load1 += 1
                break
    lines.append("")
    lines.append("| RAW slot-distance | pairs |")
    lines.append("|---|---|")
    for d in (1, 2, 3):
        lines.append(f"| d={d} | {raw[d]:,} |")
    lines.append(f"| d=1 且生产者是 load | {raw_load1:,} |")
    stalls_no = raw[1] * 2 + raw[2] * 1 + raw[3] * 0
    stalls_with = raw_load1 * 1
    lines.append("")
    lines.append(f"# 无转发需停顿（2/1/0 假设）：{stalls_no:,} 拍")
    lines.append(f"# 转发后仍需停顿（load-use d=1）：{stalls_with:,} 拍")
    lines.append(f"# 转发净收益：{stalls_no - stalls_with:,} 拍")

    text = "\n".join(lines)
    print(text)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "b4_quant_raw.md"), "w") as f:
        f.write(text + "\n")
    print(f"[OUT] {args.out}/b4_quant_raw.md")


if __name__ == "__main__":
    sys.exit(main())
