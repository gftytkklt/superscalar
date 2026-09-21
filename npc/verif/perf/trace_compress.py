#!/usr/bin/env python3
# ============================================================================
# P-H/H2（讲义 #19）：压缩 trace 对比 —— 文本 vs 二进制/位打包/差分varint/段合并
#   × 通用压缩器 gzip/bzip2/xz，输出体积 + 编解码/压缩/解压耗时对比表。
# 输入：CACHESIM_TRACE（每行 "F/R/W <32bit hex addr>"，与 cachesim 同源）。
# 编码格式（全部 round-trip 逐记录校验；多字节整数 LEB128 小端，差分 zigzag）：
#   text   : 原样 "F 30000000\n"（基线）
#   bin5   : 1B 流标('F'/'R'/'W') + 4B 地址（大端）
#   bitpack: 连续位流，每记录 2bit 流 + 32bit 地址（34bit/记录）
#   dvar   : 每记录 1B 流标(0/1/2) + zigzag varint(地址-本流上次地址)
#   dseg   : = dvar + 段合并：连续记录若"流相同且差分相同"（如 F 步进 4、R 轮询 0）
#            合并为 1 条：流标|0x80 + varint(delta) + varint(run 数)
# 用法：
#   python3 trace_compress.py /tmp/mb_pe2.trace [--out tmp/ph_h2] [--max N] [--no-general]
# ============================================================================
import argparse
import bz2
import gzip
import lzma
import os
import sys
import time

import numpy as np

STREAMS = {"F": 0, "R": 1, "W": 2}
NAMES = ["F", "R", "W"]


def parse_trace(path, max_n=0):
    ops, addrs = [], []
    with open(path, "r") as f:
        for ln in f:
            if len(ln) < 3 or ln[0] not in STREAMS:
                continue
            ops.append(STREAMS[ln[0]])
            addrs.append(int(ln[2:].strip(), 16))
            if max_n and len(addrs) >= max_n:
                break
    return ops, addrs


# ---- varint / zigzag ----
def put_uv(buf, n):
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            buf.append(b | 0x80)
        else:
            buf.append(b)
            return


def get_uv(data, i):
    n = 0
    sh = 0
    while True:
        b = data[i]
        i += 1
        n |= (b & 0x7F) << sh
        if not (b & 0x80):
            return n, i
        sh += 7


def zz(d):
    return (d << 1) if d >= 0 else ((-d << 1) - 1)


def unzz(u):
    return (u >> 1) if not (u & 1) else -((u + 1) >> 1)


# ---- 编码器 / 解码器 ----
def enc_text(ops, addrs):
    out = []
    for o, a in zip(ops, addrs):
        out.append(f"{NAMES[o]} {a:08x}\n".encode())
    return b"".join(out)


def dec_text(data):
    ops, addrs = [], []
    for ln in data.decode().splitlines():
        if len(ln) >= 3 and ln[0] in STREAMS:
            ops.append(STREAMS[ln[0]])
            addrs.append(int(ln[2:], 16))
    return ops, addrs


def enc_bin5(ops, addrs):
    import struct
    out = bytearray()
    for o, a in zip(ops, addrs):
        out += bytes([0x46 + o]) + struct.pack(">I", a)      # 'F'/'G'/'H' 递增标记
    return bytes(out)


def dec_bin5(data):
    import struct
    ops, addrs = [], []
    for i in range(0, len(data), 5):
        ops.append(data[i] - 0x46)
        addrs.append(struct.unpack(">I", data[i + 1:i + 5])[0])
    return ops, addrs


class BitWriter:
    def __init__(self):
        self.buf = bytearray()
        self.acc = 0
        self.n = 0

    def put(self, val, bits):
        self.acc |= (val << self.n)
        self.n += bits
        while self.n >= 8:
            self.buf.append(self.acc & 0xFF)
            self.acc >>= 8
            self.n -= 8

    def done(self):
        if self.n:
            self.buf.append(self.acc & 0xFF)
        return bytes(self.buf)


class BitReader:
    def __init__(self, data):
        self.d = data
        self.i = 0
        self.acc = 0
        self.n = 0

    def get(self, bits):
        while self.n < bits:
            self.acc |= self.d[self.i] << self.n
            self.i += 1
            self.n += 8
        v = self.acc & ((1 << bits) - 1)
        self.acc >>= bits
        self.n -= bits
        return v


def enc_bitpack(ops, addrs):
    out = bytearray()
    put_uv(out, len(ops))                     # 记录数（解码终止用）
    w = BitWriter()
    for o, a in zip(ops, addrs):
        w.put(o, 2)
        w.put(a & 0xFFFFFFFF, 32)
    out += w.done()
    return bytes(out)


def dec_bitpack(data):
    n, i = get_uv(data, 0)
    r = BitReader(data[i:])
    ops, addrs = [], []
    for _ in range(n):
        ops.append(r.get(2))
        addrs.append(r.get(32))
    return ops, addrs


def enc_dvar(ops, addrs):
    out = bytearray()
    prev = [0, 0, 0]
    for o, a in zip(ops, addrs):
        out.append(o)
        put_uv(out, zz(a - prev[o]))
        prev[o] = a
    return bytes(out)


def dec_dvar(data):
    ops, addrs = [], []
    prev = [0, 0, 0]
    i = 0
    while i < len(data):
        o = data[i]
        i += 1
        d, i = get_uv(data, i)
        a = prev[o] + unzz(d)
        prev[o] = a
        ops.append(o)
        addrs.append(a)
    return ops, addrs


def enc_dseg(ops, addrs):
    out = bytearray()
    prev = [0, 0, 0]
    i, n = 0, len(ops)
    while i < n:
        o = ops[i]
        d = addrs[i] - prev[o]
        prev[o] = addrs[i]
        j = i + 1
        while j < n and ops[j] == o and addrs[j] - prev[o] == d:
            prev[o] = addrs[j]
            j += 1
        run = j - i
        out.append(o | (0x80 if run > 1 else 0))
        put_uv(out, zz(d))
        if run > 1:
            put_uv(out, run)
        i = j
    return bytes(out)


def dec_dseg(data):
    ops, addrs = [], []
    prev = [0, 0, 0]
    i = 0
    while i < len(data):
        h = data[i]
        i += 1
        o = h & 0x03
        d, i = get_uv(data, i)
        run = 1
        if h & 0x80:
            run, i = get_uv(data, i)
        for _ in range(run):
            prev[o] += unzz(d)
            ops.append(o)
            addrs.append(prev[o])
    return ops, addrs


CODECS = [
    ("text", enc_text, dec_text),
    ("bin5", enc_bin5, dec_bin5),
    ("bitpack", enc_bitpack, dec_bitpack),
    ("dvar", enc_dvar, dec_dvar),
    ("dseg", enc_dseg, dec_dseg),
]
GENERAL = [
    ("gzip-9", lambda d: gzip.compress(d, 9), gzip.decompress),
    ("bzip2-9", lambda d: bz2.compress(d, 9), bz2.decompress),
    ("xz-9", lambda d: lzma.compress(d, preset=9), lzma.decompress),
]


def timed(fn):
    t0 = time.perf_counter()
    r = fn()
    return r, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser(description="trace 压缩对比（#19）")
    ap.add_argument("trace")
    ap.add_argument("--out", default="tmp/ph_h2")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--no-general", action="store_true", help="只测编码，不叠 gzip/bzip2/xz")
    args = ap.parse_args()

    ops, addrs = parse_trace(args.trace, args.max)
    if not ops:
        print("空 trace", file=sys.stderr)
        return 1
    os.makedirs(args.out, exist_ok=True)
    lines = []
    hdr = f"# trace={args.trace}  records={len(ops):,}  raw_text={os.path.getsize(args.trace):,}B"
    lines.append(hdr)
    lines.append("")
    lines.append("## 1) 编码格式（无通用压缩器）")
    lines.append("| format | bytes | vs text(raw) | enc MB/s | dec MB/s | roundtrip |")
    lines.append("|---|---|---|---|---|---|")

    raw_bytes = len(ops) * 11
    mb = raw_bytes / 1e6
    encoded = {}
    for name, enc, dec in CODECS:
        data, te = timed(lambda e=enc: e(ops, addrs))
        dec_data, td = timed(lambda d=data: dec(d))
        ok = dec_data == (ops, addrs)
        encoded[name] = data
        lines.append(f"| {name} | {len(data):,} | {raw_bytes/len(data):.2f}× | {mb/te:.1f} | {mb/td:.1f} | {'OK' if ok else 'FAIL'} |")
        print(f"[enc] {name:8s} {len(data):>10,}B  {raw_bytes/len(data):5.2f}×  enc {mb/te:6.1f}MB/s  dec {mb/td:6.1f}MB/s  {'OK' if ok else 'FAIL'}")

    if not args.no_general:
        lines.append("")
        lines.append("## 2) 叠通用压缩器（level 9；第 4 列=相对原文本的压缩率，第 5 列=相对该编码本体的再压缩率）")
        lines.append("| format | codec | bytes | vs raw_text | vs 该格式 | comp MB/s | decomp MB/s |")
        lines.append("|---|---|---|---|---|---|---|")
        for name, data in encoded.items():
            for gname, gc, gd in GENERAL:
                cdata, tc = timed(lambda d=data, f=gc: f(d))
                back, td = timed(lambda d=cdata, f=gd: f(d))
                assert back == data
                line = (f"| {name} | {gname} | {len(cdata):,} | {raw_bytes/len(cdata):.2f}× | "
                        f"{(1-len(cdata)/len(data))*100:.1f}%↓ | {len(data)/1e6/tc:.1f} | {len(data)/1e6/td:.1f} |")
                lines.append(line)
                print(f"[gen] {name:8s}+{gname:8s} {len(cdata):>10,}B  vs_raw {raw_bytes/len(cdata):5.2f}×  "
                      f"own {(1-len(cdata)/len(data))*100:5.1f}%↓  c {len(data)/1e6/tc:5.1f}MB/s  d {len(data)/1e6/td:6.1f}MB/s")

    table = "\n".join(lines)
    print("\n" + table)
    with open(os.path.join(args.out, "compress_summary.md"), "w") as f:
        f.write(table + "\n")
    print(f"[OUT] {args.out}/compress_summary.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
