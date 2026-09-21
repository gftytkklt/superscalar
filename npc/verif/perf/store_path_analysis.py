#!/usr/bin/env python3
# ============================================================================
# B4-Q6/OPT-05：store 写路径采样分析（零 RTL 风险）
#   输入：取指握手 trace（F/R/W）+ 退休口径 trace + objdump（store 宽度/掩码）
#   模型：Python dcache（4KB/32B/2 路；miss 填空路否则换 way0——与 cachesim/RTL 一致），
#         按 trace 时间序喂 R（填充行）与 W（写分配/字节掩码），统计：
#           - 写缺失数；脏行驱逐的整行/部分覆盖分布
#           - **写缺失 episode 在驱逐前被写满整行** 的数量（no-write-allocate/写合并的候选）
#           - 每行 store 次数与"连续写段"（可跨缺失合并为一个 burst 的行数）
#   用法：
#     python3 store_path_analysis.py --trace /tmp/mb_pe2.trace --retire-trace /tmp/mb_pe.trace \
#         --objdump <microbench.txt> [--out tmp/b4_opt05]
# ============================================================================
import argparse
import importlib.util
import os
import sys
from collections import Counter, defaultdict

spec = importlib.util.spec_from_file_location(
    "b4q1", os.path.join(os.path.dirname(__file__), "b4_quant_eval.py"))
b4q1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b4q1)

LINE = 32
SETS = 64
WAYS = 2
FULL = (1 << LINE) - 1
SIZE = {"sb": 1, "sh": 2, "sw": 4, "sd": 8}


class DCache:
    def __init__(self):
        self.valid = [[False] * WAYS for _ in range(SETS)]
        self.dirty = [[False] * WAYS for _ in range(SETS)]
        self.mask = [[0] * WAYS for _ in range(SETS)]
        self.tag = [[0] * WAYS for _ in range(SETS)]
        self.ep_write = [[False] * WAYS for _ in range(SETS)]   # 本 episode 由写缺失分配
        self.ep_full = [[False] * WAYS for _ in range(SETS)]    # 本 episode 已被写满整行
        self.st = Counter()
        self.evict_full = self.evict_part = 0
        self.wrmiss_full = 0          # 写缺失 episode：驱逐前写满整行（可免填充）
        self.evict_bytes = Counter()

    def _evict(self, s, w):
        if self.valid[s][w]:
            if self.dirty[s][w]:
                bits = bin(self.mask[s][w]).count("1")
                self.evict_bytes[bits] += 1
                if bits == LINE:
                    self.evict_full += 1
                else:
                    self.evict_part += 1
                if self.ep_write[s][w] and self.ep_full[s][w]:
                    self.wrmiss_full += 1
                self.st["wb"] += 1
            self.valid[s][w] = False
            self.dirty[s][w] = False
            self.ep_write[s][w] = False
            self.ep_full[s][w] = False

    def _alloc(self, line, tag, by_write):
        s = line % SETS
        for w in range(WAYS):
            if not self.valid[s][w]:
                self.valid[s][w] = True
                self.tag[s][w] = tag
                self.dirty[s][w] = False
                self.mask[s][w] = 0
                self.ep_write[s][w] = by_write
                self.ep_full[s][w] = False
                return s, w
        self._evict(s, 0)
        self.valid[s][0] = True
        self.tag[s][0] = tag
        self.dirty[s][0] = False
        self.mask[s][0] = 0
        self.ep_write[s][0] = by_write
        self.ep_full[s][0] = False
        return s, 0

    def read(self, line, tag):
        s = line % SETS
        for w in range(WAYS):
            if self.valid[s][w] and self.tag[s][w] == tag:
                self.st["rd_hit"] += 1
                return
        self.st["rd_miss"] += 1
        self._alloc(line, tag, False)

    def write(self, line, tag, size, off):
        s = line % SETS
        for w in range(WAYS):
            if self.valid[s][w] and self.tag[s][w] == tag:
                self.st["wr_hit"] += 1
                self._mark(s, w, size, off)
                return
        self.st["wr_miss"] += 1
        s, w = self._alloc(line, tag, True)
        self._mark(s, w, size, off)

    def _mark(self, s, w, size, off):
        self.dirty[s][w] = True
        self.mask[s][w] |= (((1 << size) - 1) << (off % LINE)) & FULL
        if self.mask[s][w] == FULL:
            self.ep_full[s][w] = True


def cacheable(a):
    return ((0x80000000 <= a < 0x80400000) or    # PSRAM
            (0x30000000 <= a < 0x40000000) or    # flash
            (0xa0000000 <= a < 0xa8000000))      # SDRAM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", required=True)
    ap.add_argument("--retire-trace", required=True)
    ap.add_argument("--objdump", required=True)
    ap.add_argument("--out", default="tmp/b4_opt05")
    args = ap.parse_args()

    instr = b4q1.parse_objdump(args.objdump)
    ret = b4q1.load_f(args.retire_trace)
    stores = [(pc, instr[pc]["mn"]) for pc in ret
              if pc in instr and instr[pc]["kind"] == "mem" and instr[pc]["mn"] in SIZE]

    w_pos, size_cnt, total_bytes = 0, Counter(), 0
    cache = DCache()
    line_writes = Counter()
    w_line_seq = []                       # W 流中的行号序列（用于连续段统计）
    for ln in open(args.trace):
        if ln[0] == "R":
            a = int(ln[2:], 16)
            if cacheable(a):
                cache.read(a // LINE, (a // LINE) // SETS)
        elif ln[0] == "W":
            a = int(ln[2:], 16)
            mn = stores[w_pos][1] if w_pos < len(stores) else "sw"
            w_pos += 1
            if not cacheable(a):
                continue                     # SRAM/MMIO 直写不入 dcache
            size_cnt[mn] += 1
            total_bytes += SIZE[mn]
            cache.write(a // LINE, (a // LINE) // SETS, SIZE[mn], a % LINE)
            line_writes[a // LINE] += 1
            w_line_seq.append(a // LINE)

    # 连续写段：同一行在 W 流中出现的所有位置是否连续（可合并为一个 burst 写）
    pos = defaultdict(list)
    for i, l in enumerate(w_line_seq):
        pos[l].append(i)
    contiguous = sum(1 for l, ps in pos.items() if ps[-1] - ps[0] + 1 == len(ps))

    os.makedirs(args.out, exist_ok=True)
    L = []
    L.append(f"# store 指令 {len(stores):,} / W 记录 {w_pos:,}")
    L.append("")
    L.append("| 宽度 | 条数 | 字节 |")
    L.append("|---|---|---|")
    for mn in ("sb", "sh", "sw", "sd"):
        L.append(f"| {mn} | {size_cnt[mn]:,} | {size_cnt[mn]*SIZE[mn]:,} |")
    L.append(f"| 合计 | {sum(size_cnt.values()):,} | {total_bytes:,} |")
    L.append("")
    L.append("| dcache 模型 | 值 |")
    L.append("|---|---|")
    L.append(f"| rd_hit / rd_miss | {cache.st['rd_hit']:,} / {cache.st['rd_miss']:,} |")
    L.append(f"| wr_hit / wr_miss | {cache.st['wr_hit']:,} / {cache.st['wr_miss']:,} |")
    L.append(f"| 脏行驱逐 | {cache.st['wb']:,}（整行覆盖 {cache.evict_full:,} / 部分 {cache.evict_part:,}） |")
    L.append(f"| **写缺失 episode：驱逐前写满整行** | **{cache.wrmiss_full:,}** |")
    L.append(f"| 驱逐覆盖字节（位）分布 | " + " ".join(f"{k}:{v}" for k, v in sorted(cache.evict_bytes.items())) + " |")
    L.append(f"| 有写访问的行数 / 连续写段行数 | {len(line_writes):,} / {contiguous:,} |")
    vals = sorted(line_writes.values())
    L.append(f"| 每行 store 次数 p50/p90/max | {vals[len(vals)//2]}/{vals[int(len(vals)*0.9)]}/{vals[-1]} |")
    text = "\n".join(L)
    print(text)
    with open(os.path.join(args.out, "store_analysis.md"), "w") as f:
        f.write(text + "\n")
    print(f"[OUT] {args.out}/store_analysis.md")


if __name__ == "__main__":
    sys.exit(main())
