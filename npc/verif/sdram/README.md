# verif/sdram —— SDRAM AXI 控制器定向回归

P-D 阶段（SDRAM AXI 突发链）两个隐蔽缺陷的定向回归测试。两缺陷都只在
"背靠背/单拍转两拍"的时序组合下出现，difftest 大规模跑测可暴露但难以定位，
本 TB 用 AXI BFM 直接驱动 `sdram_top_axi` + 自制 SDRAM 颗粒模型复现/防回归。

## 两个回归点

1. **突发读背靠背**（`sdram.v` 读输出）：READ 每 2 chip cycle 一次，旧的
   "预取+保持 2 cycle" 实现会被下一拍命令清掉 `rd_pend` → `arlen>0` 的读每隔
   一拍返回 0。受害面：可缓存 SDRAM 的 32B refill（bf/15pz 数据错）、
   axi64to32 拆出的 2 拍 64bit MMIO 读（`ld` 高半字丢失）。
   修复：CAS 流水线（`RD_DELAY=2`，逐拍无缝衔接）。
2. **FIXED 单拍宽拆**（`axi64to32.v`）：dcache MMIO 的 `ld/sd` 是
   size=3、len=0、burst=FIXED 的 64bit 单拍；拆成两拍 32bit 时若沿用 FIXED，
   从端两拍落同一地址 → 高半字覆盖低半字（`sd` 后 `ld` 得 0）。
   修复：宽拍拆分强制 INCR（`out_arburst/out_awburst = wide ? 2'b01 : in_*`）。

## 运行

```bash
cd npc/verif/sdram && ./run.sh
```

覆盖：A 突发写+单读 / B 单写+突发读 / C 单写+单读 / D 突发写+突发读 /
E 写-读-写-读交替 / F 16 拍长突发 / G 跨 512 列行边界。期望 `[TB] ALL PASS`。

> 说明：TB 内含 `#150000` 等待（控制器上电初始化 100us：CKE/PRECHARGE/REFRESH/LMR）。
> `sdram.v` 的 `SDRAM_MODEL_DBG` 宏（默认关）可打印颗粒侧 ACT/WR/RD/PRE 逐命令现场。
