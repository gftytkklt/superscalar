#!/usr/bin/env python3
# P-E/E3 后处理：cachesim --tsv 扫描结果 + 面积模型 → DSE 表 / Pareto 前沿。
# 用法：python3 dse_area.py /tmp/pe_dse_T*.tsv
#
# 面积模型（透明估算，口径见 records/process/B3_STAGE8_PE_DSE.md）：
#   · 逻辑（综合口径，不含 SRAM）：A_ctrl + (A_now-A_ctrl) × meta_bits/meta_now
#       meta_bits = ways×64 × (tag_bits+2)，tag_bits = 32-log2(block)-6
#       icache: A_now=25,862 A_ctrl=12,931 meta_now=2944；dcache: A_now=36,335 A_ctrl=18,168
#   · SRAM 宏（fakeram45 拟合）：capacity_bytes × 4.1 μm²/B（1024x32=16,406、512x64=17,301）
#   · 全芯片估算 = 56,609（其余固定部分 = 118,806-62,197）+ 逻辑 + SRAM
import sys, math, glob

A_NOW = {'i': 25862.0, 'd': 36335.0}
A_CTRL = {'i': 12931.0, 'd': 18168.0}
META_NOW = 64.0 * 2 * (21 + 2)       # 64 sets × 2 ways = 128 slots × (tag21+valid+dirty)
SRAM_UPB = 4.11                       # μm²/byte（fakeram45 小宏拟合）
REST = 118805.71 - (A_NOW['i'] + A_NOW['d'])

def logic_area(nsram, blk, ways, which):
    slots = ways * 64
    tag = 32 - int(math.log2(blk)) - 6
    meta = slots * (tag + 2)
    return A_CTRL[which] + (A_NOW[which] - A_CTRL[which]) * meta / META_NOW

def rows(files):
    out = []
    for f in files:
        for l in open(f):
            if not l.startswith('TSV\t'): continue
            p = l.rstrip('\n').split('\t')[1:]
            total, ni, nd = int(p[0]), int(p[1]), int(p[2])
            iblk, iw, dblk, dw = int(p[3]), int(p[4]), int(p[5]), int(p[6])
            ih, dh, tmt = float(p[7]), float(p[8]), int(p[9])
            li = logic_area(ni, iblk, iw, 'i')
            ld = logic_area(nd, dblk, dw, 'd')
            sram = (ni + nd) * 1024 * SRAM_UPB
            out.append(dict(total=total, ni=ni, nd=nd, iblk=iblk, iw=iw, dblk=dblk, dw=dw,
                            ih=ih, dh=dh, tmt=tmt, logic=li+ld, sram=sram,
                            tot=li+ld+sram, chip=REST+li+ld+sram))
    return out

def fmt(r):
    return (f"I{r['ni']}SR {r['iblk']}B/{r['iw']}w + D{r['nd']}SR {r['dblk']}B/{r['dw']}w")

def main():
    rs = rows(sys.argv[1:])
    base = [r for r in rs if r['total']==8 and r['iblk']==32 and r['iw']==2 and r['dblk']==32 and r['dw']==2][0]
    print(f"# 基线: {fmt(base)}  TMT={base['tmt']:,}  I_hit={base['ih']:.2f}% D_hit={base['dh']:.2f}%  "
          f"逻辑={base['logic']:,.0f} SRAM={base['sram']:,.0f} 全芯片≈{base['chip']:,.0f}μm²")

    # E2：8KB 内 16B vs 32B（每类取 TMT 最优）
    print("\n## E2 16B vs 32B（total=8，校准成本，TMT 越小越好）")
    print("| 配置 | I_hit | D_hit | TMT | vs 基线 | 逻辑面积 | +SRAM |")
    print("|---|---|---|---|---|---|---|")
    for blk in (16, 32, 64):
        cands = [r for r in rs if r['total']==8 and r['dblk']==blk]
        if not cands: continue
        b = min(cands, key=lambda r: r['tmt'])
        print(f"| {fmt(b)} | {b['ih']:.2f}% | {b['dh']:.2f}% | {b['tmt']:,} | {base['tmt']/b['tmt']:.3f}× | "
              f"{b['logic']:,.0f} | {b['logic']+b['sram']:,.0f} |")

    # E3：全局 Pareto（TMT ↓、全芯片面积 ↓）
    rs_sorted = sorted(rs, key=lambda r: (r['chip'], r['tmt']))
    pareto, best_tmt = [], 1e30
    for r in rs_sorted:
        if r['tmt'] < best_tmt - 1e-9:
            pareto.append(r); best_tmt = r['tmt']
    print("\n## E3 Pareto 前沿（面积↓ + TMT↓；全芯片=固定56,565+逻辑+SRAM）")
    print("| 配置 | I_hit | D_hit | TMT | vs基线 | 逻辑(不含SRAM) | +SRAM | 全芯片估算 | IPC× (p=0.75) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(pareto, key=lambda r: r['chip']):
        amd = 1.0/((1-0.75) + 0.75*r['tmt']/base['tmt'])
        print(f"| {fmt(r)} | {r['ih']:.2f}% | {r['dh']:.2f}% | {r['tmt']:,} | {base['tmt']/r['tmt']:.3f}× | "
              f"{r['logic']:,.0f} | {r['logic']+r['sram']:,.0f} | {r['chip']:,.0f} | {amd:.3f}× |")

    # 推荐：面积不增（±2%）内的 TMT 最优；以及 TMT 最优
    near = [r for r in rs if r['chip'] <= base['chip']*1.02]
    best_near = min(near, key=lambda r: r['tmt'])
    best_all = min(rs, key=lambda r: r['tmt'])
    print(f"\n## 推荐\n- 面积不增(≤+2%)最优: {fmt(best_near)}  TMT={best_near['tmt']:,} ({base['tmt']/best_near['tmt']:.3f}×) "
          f"芯片≈{best_near['chip']:,.0f}μm²\n- TMT 全局最优: {fmt(best_all)}  TMT={best_all['tmt']:,} "
          f"({base['tmt']/best_all['tmt']:.3f}×) 芯片≈{best_all['chip']:,.0f}μm²")

if __name__ == '__main__':
    main()
