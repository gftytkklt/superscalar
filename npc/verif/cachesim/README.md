# cachesim —— 参数化 cache 模拟器（B3 阶段3）

> 用途：用 trace 判定 icache/dcache 命中率，在 **8KB = 8×(128bit×64) SRAM、整颗 SRAM 为单位** 的
> 约束下做设计空间探索，按访存区间 + 缺失/脏回写/MMIO 行为参数化计算 TMT，推荐最优配置。
> 分析/结论见 `../records/knowledge/B3_CACHESIM_ANALYSIS.md`。

## 组成
| 文件 | 作用 |
|---|---|
| `cachesim.h` | `Cache` 类、`CacheParams`、`RegionCost`、`make_cache_from_srams()`（约束判定） |
| `cachesim.cpp` | `Cache` 实现（元数据：tag/valid/dirty；命中/缺失/替换/3C 近似；成本累计）；`RegionCost` 初值 |
| `main.cpp` | 读 trace、按约束枚举配置、回放、算 TMT/hit、排序 + 推荐 |

## 编译
```bash
cd npc/verif/cachesim
g++ -O2 -std=c++17 -o cachesim main.cpp cachesim.cpp
# 产物 ./cachesim（一个自包含二进制，无外部依赖）
```

## 输入 trace（由 npc 仿真导出）
导出：`perf_counters.sv` 里 `csim_*` DPI + `csrc/trace.cpp`，仅当设置环境变量才落盘：
```bash
cd am-kernels/benchmarks/microbench
CACHESIM_TRACE=/tmp/mb.trace make ARCH=riscv64-npc HEAP_SIZE=0x400000 WITH_TRACE=n run mainargs=test
# /tmp/mb.trace 每行: F <取指PC> / R <读地址> / W <写地址>（十六进制、无 0x 前缀）
```

## 运行
```bash
./cachesim /tmp/mb.trace                        # 扫全部合法配置，打印排序 + 推荐
./cachesim /tmp/mb.trace --cal                  # 用 2026-09-21 校准成本集扫描（推荐）
./cachesim /tmp/mb.trace --i sram=4:blk=32:ways=2 --d sram=4:blk=32:ways=2   # 单配置
./cachesim /tmp/mb.trace --i ... --d ... --cal  # 单配置 + 校准成本（RTL 对账用；打印按区缺失）
```
- `--i/--d <cfg>`：单配置模式，打印完整统计（access/hit/miss/refill/wb/mmio + 按区读/写缺失）。
- `--total T`：SRAM 总颗数（1KB/颗，默认 8）→ 扫描 `ni+nd=T` 的全部合法几何（放宽总量用）。
- `--tsv`：机器可读输出（`TSV total ni nd iblk iways dblk dways I_hit D_hit TMT`），
  配合 `dse_area.py` 生成面积模型 + Pareto 前沿（E3，见 `../records/process/B3_STAGE8_PE_DSE.md`）。
- `--cal`：校准成本集（RTL 实测 r=3.5）：icache flash 4285/sdram 1346；dcache psram 读 1676
  /写 2244、flash 读 4529、sdram 读 1370/写 1422；MMIO sram 18/其它 7；hit 1/2。
  校准后与 RTL 缺失计数/缺失 TMT **逐项一致**（见 `../records/process/B3_STAGE8_PE_CACHESIM_DIFF.md`）。
- 替换策略：与 RTL 一致（miss 时先填空路；2 路否则换 way0；>2 路轮转近似 LRU）。
- trace 取指口径：`F` = icache 接受请求拍（含被冲刷的 bubble 取指），与 `ICACHE_STAT`
  总数一致；`R/W` = LSU 请求拍，与 `rd/st_region` 一致。
- trace = 每条访问一行；`F` 喂 icache，`R`/`W` 喂 dcache（自动分离）。
- 输出：每配置的 `I_hit`/`D_hit`/`extra-stall TMT`/`vs_base`/`Amdahl(≈)`。

## 配置/成本模型（参数化修改接口）
- **几何**：`make_cache_from_srams(nsram, is_icache, block, ways, &p, &err)` 校验
  `ways*block==16*nsram && sets==64 && block 为 16 倍数`（整颗 SRAM 约束）。`main.cpp` 据此枚举 `(Ni,Nd), Ni+Nd=8`。
- **成本**：`cachesim.cpp` 的 `RegionCost()` 初值（按区域 `base/base_w/wb/mmio`，未校准）；
  用 `--cal` 切到 2026-09-21 校准集。`base`=读 refill、`base_w`=写 refill（RTL 写缺失均值已含
  脏回写，故 wb=0）、`wb`=脏块写回（仅当未含在 base_w 时使用）；块大小按 `block/32` 比例缩放。
  - 区域判定：PSRAM `[0x80000000,0x80400000)`、flash `[0x30000000,0x40000000)`、SDRAM `[0xa0000000,0xa8000000)`、
    SRAM `[0x0f000000,0x0f002000)`（非缓存→MMIO）、其它（如 UART `0x10000000`）=MMIO。
- **报告口径**：`extra-stall TMT = refill + 脏回写 + MMIO`（**不含命中延迟**；命中为有序流水已覆盖）。

## 校验
- `make_cache_from_srams` 对非法组合报错并提示合法 `(ways,block)`。
- 建议先跑小 synthetic trace 验证命中率合理，再上真实 trace（注意另存大 trace 会很慢）。
