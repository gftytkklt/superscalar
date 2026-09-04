# npc — 自研 RISC-V64 处理器

`npc` 是"一生一芯"工程中的**自研处理器**。核心是一个 RV64 五级流水线 CPU（RTL 单文件
`vsrc/ysyx_22040750.v`，共 30 个模块），通过自定义握手接口接 `I/D Cache`，并以 AXI4 主接口
挂到 Chisel 生成的 SoC（`ysyxSoCFull`）总线上，与 Flash/SRAM/UART/GPIO 等外设通信，同时与
NEMU 进行 difftest 逐指令对拍。

- CPU 模块名 / 学号 ID：`ysyx_22040750`
- 指令集：RV64IM（含乘法/除法，M 扩展为多周期实现）
- 复位 PC：`0x2FFFFFFC`；启动后 `snpc = pc + 4` 首取 `0x30000000`（Flash 基址）
- 访存模型：AXI4（64 位数据总线，单拍/突发均可）

---

## 1. 目录结构

```
npc/
├── vsrc/                    # RTL 源码
│   └── ysyx_22040750.v      # 全部 30 个 module 的处理器核
├── verif/                   # 验证与调试文档 + 独立 RTL 微验证环境（见 §6 文档索引）
│   ├── DEBUG_WORKFLOW.md    # 调试工作流与阶段 A–J3 执行记录（权威验证链路、波形管理、启动流程）
│   ├── VERIF_TESTS.md       # 测试体系（现行）
│   ├── B3_PLAN.md + STAGE_B3_CACHE_PERF.md  # 当前阶段：B3 性能计数器与缓存调优
│   ├── records/             # 归档区：process/(阶段过程日志) + knowledge/(经验复盘)，见其 README
│   ├── Makefile             # make / make run T=xxx / make fst T=xxx / make assert / make formal
│   ├── tb_main.cpp          # AXI4 内存模型 + 时钟/复位 harness（断言失败返回非 0）
│   ├── tests/               # 汇编微测试：bug2_csr bug3_div bug4_fencei
│   ├── assert/              # 阶段2：bind 注入的仿真期断言（$error 监视器）
│   │   ├── cache_bypass_check.sv   # bug1：cacheable 访问不许进 MMIO 状态（可 CACHE_CHECK_OFF）
│   │   ├── csr_hazard_check.sv     # bug2：CSR 写读冒险（MEPC 定向）
│   │   └── div_zero_check.sv       # bug3：除零商必须为 -1
│   └── formal/              # 阶段2：SymbiYosys 形式化（.sby + SVA props；装 sby/z3 后 make formal）
│       ├── div.sby  + props_div.sv                 # 除零(bug3)证明——✅ PASS
│       ├── axiburst.sby + props_axiburst.sv        # axiburst2xxx 读通道证明——✅ PASS
│       └── (props_dcache.sv 残留：dcache.sby 已移除——含大查找表 BMC 不可判定，见 VERIF_TESTS §4)
├── scripts/linker-soc.ld    # SoC 内存布局 / 链接脚本（flash 0x30000000, sram 0x0f000000）
├── csrc/                    # C++ 仿真侧
│   ├── soctest.cpp          # Verilator 主循环（波形/复位/时钟/difftest）
│   └── util/                # difftest、probe(DPI)、memory(映像装载)
├── ysyxSoC/                 # Chisel 生成的 SoC（ysyxSoCFull + perip 外设）
├── test_prog/               # SoC 冒烟测试程序（char-test）编译入口
├── build/                   # Verilator 仿真二进制（ysyxSoCFull）
├── Makefile                 # 全系统仿真构建/运行（DIFF/WAVE 开关）
├── soc.vcd / soc.gtkw       # 全系统仿真波形（ps 级 VCD）与视图
└── (mill/playground/build.sc 为 Chisel 工程模板残留，可忽略)
```

## 2. RTL 架构

```
ysyx_22040750 (vsrc/ysyx_22040750.v)
├── cpu_core_e        (#$IF_ID/ID_EX/EX_MEM/MEM_WB 流水线核)
│   ├── pc_e / npc_e      # PC 寄存器与下一条 PC 计算(snpc/jal/jalr/csr/fence.i)
│   ├── stall_unit_e      # 停顿控制(load-use、多周期M/D、中断冲刷)
│   ├── forward_unit_e    # 数据前递(EX/MEM/WB -> ID)
│   ├── csr_foward_e      # CSR 前递
│   ├── decoder_e         # 译码(imm/控制字/dnpc_sel/csr 操作)
│   ├── alu_e             # ALU 顶层
│   │   ├── gpr_alu_e     # 整数运算 + booth_mul_serial(串行乘) + radix2_div(基2除)
│   │   └── csr_alu_e     # CSR 值运算(direct/set/clr)
│   ├── gpr_e             # 寄存器堆(32×64)
│   ├── mem_ld_e/mem_sd_e # 访存字节对齐/符号扩展
│   ├── csr_e             # CSRs(mstatus/mie/mtvec/mepc/mcause/mip/satp) + 定时中断
│   └── timerintr_e       # 定时中断使能/去毛刺
├── cache_e            (# icache/dcache 与 AXI crossbar)
│   ├── icache_e       # 指令缓存(2路组相联 4KB/32B)
│   ├── dcache_e       # 数据缓存(同上, 支持写回)
│   └── crossbar_e     # AXI 读通道(AR/R)双主仲裁
├── slave_crossbar_e   # AXI 地址译码(CLINT 0x02000000 区间 -> clint, 其余 -> 总线)
└── clint_e            # CLINT(mtime/mtimecmp -> mtip 定时中断)
```

- **流水线**：经典 IF/ID/EX/MEM/WB 五级；`IF_ID/ID_EX/EX_MEM/MEM_WB` 流水寄存器带 valid/allowin
  握手；数据前递 + 停顿消除数据冒险；load-use 采用停两拍 + WB 前递；乘除法**多周期**执行并由
  `alu_out_valid` 反压流水。
- **访存**：cpu_core 以握手接口（`pc/mem_addr/rvalid/...`）连缓存；缓存内部转 AXI4。I 缓存只用
  AR/R 通道，D 缓存同时用 AW/W/B（写响应）通道；读通道经 `axi_crossbar` 仲裁后上总线。
- **异常/中断**：ecall/ebreak/mret/定时中断走 CSR 写回 + `npc` 跳转（mtvec/mepc）。

## 3. 历史缺陷与修复（均已解决，2026-09-02 复验）

> 以下三项在早期被 `npc/verif` 定向微测试在 RTL 级复现（观察值来自仿真）。**当前均已修复**：
> `make`（10 例）、`make assert`（10 例）、`make assert-cache`（10 例）全 PASS，
> `formal/div.sby`、`formal/axiburst.sby` 证明级 PASS（见 §4/§5）。此处保留根因/证据/修复作历史参考。

### 3.1 【已修复】Level-I/D Cache 曾被完全旁路，恒走 MMIO 单拍
- **根因**：`dcachectrl` 与 `icachectrl` 中 `mmio_flag` 曾被无条件置真（早期
  `assign mmio_flag = (I_cpu_rd_req || I_cpu_wr_req);` 等），FSM 内 `if(mmio_flag) → MMIO_*`
  先于 `rd_hit/rd_miss/wr_*` 判定，命中/缺失分支**结构上不可达**。
- **证据（当时）**：全系统波形 `cache_e.icache_e.current_state` 全程仅出现
  `IDLE/MMIO_AR/MMIO_RD`；`dcache` 仅出现 `IDLE/MMIO_AR/MMIO_AW/MMIO_RD/MMIO_WR`。
- **影响（当时）**：取指/访存退化为总线单拍，cache/tag/写回/fence.i 全为死电路，IPC 极低。
- **修复**：`mmio_flag` 恢复为**按地址区间判定**（现 `ysyx_22040750.v:2071-2074`），可缓存区 =
  PSRAM `[0x80000000,0x80400000)` + flash `[0x30000000,0x40000000)` + SDRAM
  `[0xa0000000,0xa8000000)`，其余（外设/SRAM/MROM/空洞）走 MMIO 单拍；并补齐 SRAM 存储
  （`ysyx_22040750_sram_behav`×8）与完整 fence.i（脏行回写 + icache 失效）。
- **验证**：`cache_data`/`cache_region`/`fencei_cache`/`partial_store`/`pmem_stress`/`psram_burst`
  微测试全 PASS（flash 与 pmem 主存模式），`assert-cache` 的 `cache_bypass_check.sv` 不再报。

### 3.2 【已修复】CSR 读写冒险：连续同址 CSR 操作会读到旧值并写坏 CSR
- **根因**：早期 `csr_foward` 只取译码时快照 `ID_EX_csr`（旧值），而非更新后的在飞值。
- **证据（当时）**（`bug2_csr.S`）：`csrw mepc,0x12345678` 后紧跟 `csrr t1,mepc` 得 `t1=0`；
  且该 `csrr` 用旧值把 `mepc` 从 `0x12345678` 改回 0。
- **修复**：新增 `ysyx_22040750_csr_foward`（`ysyx_22040750.v:1419-1449`），按
  `I_csr_wen_EX/MEM/WB` 门控，读音取 EX→MEM→WB→ID 中最新的同址写值（注释 "bug2 fix"）。
- **验证**：`bug2_csr` 微测试 + `csr_hazard_check.sv` 断言均 PASS。

### 3.3 【已修复】有符号除零（负被除数）商错误
- **根因**：早期 `radix2_div` 除零时 `current_q=1`、`abs_quotient` 填全 1，负被除数经
  `q_flag` 取反得商 `+1`，而 RV64 规范要求 `DIV x,neg,/0 = -1(全F)`。
- **证据（当时）**（`bug3_div.S`）：`div a2,-5,0` → `0x1`（规范 `-1`）；`rem a3,-5,0` → `-5`。
- **修复**：新增 `div_zero` 闩存（`ysyx_22040750.v:3974-3999`），
  `quotient = div_zero ? {64{1'b1}} : ...`（`:4019`，被除数符号无关，覆盖负被除数），
  余数保持被除数。
- **验证**：`bug3_div` 微测试 + `div_zero_check.sv` 断言 + `formal/div.sby`（bmc）证明级 PASS。

### 3.4 曾被怀疑、经实验排除的项（避免误判）
- `sltw` 符号扩展问题：`sltw` 并非 RV64I 合法指令（不存在 word 类有符号比较），gcc 直接拒绝
  汇编，ALU 的 slt 路径只作用于 64 位 → 不成立。
- `EX_MEM_reg.mem_rd_en` 时序上的"多余读"：实测 `mem_rd_en` 在请求拍（IDLE 且 `mem_ready=1`）
  即经 `rd_handshake` 清零，数据返回前早已复位，load→store 事务日志中无多余 AR → 不成立。

## 4. 仿真执行方法

### 4.1 全系统仿真（SoC + difftest，推荐回归路径）
环境依赖：`verilator`、`riscv64-linux-gnu-*` 工具链、`llvm`、`SDL2`；difftest 需先构建 NEMU
（`nemu/build/riscv64-nemu-interpreter-so`）。

```bash
# 构建仿真模型（DIFF 开差异对拍，WAVE 开波形）
cd npc
make DIFF=1 WAVE=1          # 产物 build/ysyxSoCFull

# 可视化配置（可选）：持久化 DIFF/WAVE/WITH_TRACE/WITH_SDL/BOOT_MODE/HEAP_SIZE 到 npc/.npc_config；
# 命令行传参（make WAVE=1 ...）仍优先于配置。
cd npc && make menuconfig

# 编译一个测试程序为 flash 映像（0x30000000）并跑全系统仿真
cd npc/test_prog && make    # 生成 build/char-test.bin 并自动调用 npc sim
# 等价的手工方式：
make -C npc sim IMG=$(pwd)/npc/test_prog/build/char-test.bin
```

- 仿真结束后 difftest 逐指令与 NEMU 对拍，任何 GPR/PC 不一致立即 `DIFF ABORT` 报错；
- `WAVE=1` 时输出 `soc.vcd`（ps 级，可 `vcd2fst` 转 FST 后结合 GTKWave/`soc.gtkw` 或
   MCP 波形工具查看）；
- **NVBoard（阶段 J0，可选）**：`WITH_SDL=y` 接入虚拟板卡（LED/拨码/数码管/键盘/UART/VGA）。
  需已装 `libsdl2-ttf-dev`/`libsdl2-image-dev`；用法
  `cd npc/test_prog && make PROC=gpio_demo.c WITH_SDL=y SIM_END=1000000000 run`
  （死循环演示靠 `SIM_END` 停止；引脚绑定见 `npc/constr/ysyxSoCFull.nxdc`）。

### 4.2 独立核微验证（npc/verif，模块级/微测试用）
在不编译 SoC、不依赖 NEMU 的前提下，用 Verilator 直接编译 CPU 核本身，配一个自写的
AXI4 内存模型（`tb_main.cpp`）直接驱动取指/访存，适合写定向微用例。

`tb_main.cpp` 的从端模型按 Verilog 分层事件队列建模：每个仿真步 = 一次 posedge eval +
一次 settle eval；从端把组合输出与"触发器寄存器(NBA 拍延迟)"分开写，AR 请求延迟一拍给
rvalid、wdata 接收后延迟一拍再给 bvalid，全部握手驱动、无启发式退避。

```bash
cd npc/verif
make             # 编译模型并跑全部 tests/*.S（当前 10/10 全 PASS）
make run  T=bug2_csr  # 只跑某个用例
make fst  T=bug2_csr  # 跑并保留 build/bug2_csr.fst 波形
make clean
```

- 用例机制：映像放到 Flash `0x30000000`（复位 PC `0x2ffffffc` → `snpc=pc+4` 自然引导）；
  程序把结果写入 SRAM `0x0f000000` 后 `ebreak` 结束；harness 打印 SRAM 区与 AXI 事务日志。
- 现有用例（10 个，见 `VERIF_TESTS.md` §1）：`bug2_csr`(CSR 冒险)、`bug3_div`(除零)、
  `bug4_fencei`(fence.i)、`cache_data`/`cache_region`/`fencei_cache`/`partial_store`/
  `pmem_stress`(缓存路径)、`psram_burst`(PSRAM 32B burst)、`residual_mret`(mret)。

### 4.3 调试辅助
- 波形：`soc.gtkw`（全系统）、`verif/build/<用例>.fst`（微验证）；
- RTL 为单文件，`module` 内部信号可直接在 GTKWave 树内逐层展开。

## 5. 后续更完备验证的开发策略

当前验证以定向微用例 + difftest 冒烟为主，覆盖率与通用性有限。建议按以下阶段推进：

### 阶段 1：测试载荷更完备（无环境改造，可立即推进）
- 引入官方指令测试集：`riscv-tests/isa`、`riscv-arch-test`（RV64IM 定向/签名文件）；
- 自研/引入随机指令流生成器（约束 PC-跳转、寄存器依赖、访存对齐等），跑长随机回归；
- 补齐边界用例：非对齐读写、乘除溢出（`INT64_MIN/-1`）、除零两种符号、CSR 组合与
  mret/ecall 连续、定时中断抢占、多周期指令后跟 load-use 等；
- cache 已修复（见 §3.1），可在此基础上补充更密的命中/未命中/替换/脏写回/fence.i 序列用例；
- 将这些并入 `npc/verif`，形成可重复的回归套件。

### 阶段 2：断言与形式化（轻量、性价比最高）—— ✅ 已落地且全 PASS
在 `npc/verif` 中实现，分两条腿：

1. **仿真期断言（`npc/verif/assert/`）**
   - 不改核 RTL，用 `bind` 注入 `$error` 监视器（Verilator `--assert` 构建），
     `tb_main.cpp` 检测到 `Verilated::gotError()` 即返回非 0；
   - 覆盖已证实的三类问题：`cache_bypass_check.sv`(bug1)、`csr_hazard_check.sv`(bug2)、
     `div_zero_check.sv`(bug3)。bug1 检查用 `` `CACHE_CHECK_OFF `` 可单独关掉，
     以便聚焦 bug2/bug3 専属断言；
   - 运行：
     ```bash
     cd npc/verif
     make assert        # 聚焦 bug2/bug3：当前 10/10 全 PASS
     make assert-cache  # 连 bug1 一起：当前 10/10 全 PASS（cache 已不旁路）
     ```
2. **形式化（`npc/verif/formal/`）** ✅ 已实跑且全部证明级 PASS（yosys+z3+sby）
   - 工具链：`apt install yosys z3`；`sby` 需另装（非 PyPI 包）——从
     `github.com/YosysHQ/sby` 拉源码后 `make install PREFIX=~/.local`，并软链
     `/usr/bin/yosys-smtbmc -> ~/.local/bin/smtbmc`，然后 `make formal` 即可；
   - 内容：`div.sby`(除零规范断言+驱动，bmc) / `axiburst.sby`(axiburst2xxx 读通道)；
     RTL 经 `formal/trim_rtl.py` 抽出自包含块给 yosys（避开 DPI-C），并修正 0 位宽字面量；
   - **当前结果（修复后）**：
     - `div.sby`（bmc depth100）：**PASS**——除零规范（商 -1、余=被除数）证明达成；
     - `axiburst.sby`（bmc depth35）：**PASS**——读通道 32bit 单拍 + burst 重组 + ARVALID 保持；
     - `dcache.sby` 因含 128-entry lookup_table + 256bit cacheline，BMC 状态空间不可判定，
       已移除（改用仿真断言 + 定向微测试覆盖，见 VERIF_TESTS §4）。

### 阶段 3：接入 UVM 等验证流程
CPU 类同步设计的 UVM 化要点：

1. **平台骨架**：以 `ysyx_22040750` 为 DUT，包一层 `dut_wrapper`；两侧分别挂
   AXI master-agent（内存侧，仿真存储/外设）与"程序注入/观测"agent；
2. **事务/序列**：定义 `InstItem / MemTrans` 等 transaction；Sequence 负责指令流生成
   （定向段 + 随机段）；Driver 通过 interface（clocking block）驱动；Monitor 采样
   每周期 WB 指令（pc+inst+GPR 写端口）与 AXI 事务；
3. **参考模型与 Scoreboard**：把现成的 NEMU/Spike 封装成 `ref_model`（即 difftest 的
   UVM 化），Scoreboard 按程序顺序比对 WB 结果（pc/rd/写值），并独立校验总线事务
   （地址/掩码/突发长度、cache 状态机可达性）；
4. **Sequence 库**：`reset_seq / smoke_seq / random_seq / csr_seq / cache_seq /
   isr_seq`；用 `uvm_objection/phase` 管理 run 阶段，failure 通过 `report catcher`
   汇总；
5. **覆盖率**：functional covergroups（指令类型、冒险组合、cache 状态跳转、CSR/中断）、
   配合 code coverage 收敛，收敛门限后结题。

> 工具注意：若继续使用 Verilator，UVM 类库可选用开源
> `UVM-SV`（verilator 5+ 已支持大部分）；或将验证平台切换到商业 UML 打件流
> （VCS/Questa）。`npc/verif` 的 C++ harness 保留作为快速定向调试入口，与 SV/UVM
> 回归互为补充。

### 阶段 4：CI 与流程固化
- 接入 CI（本地 make + git hook 或 GitLab/GitHub Actions）：每次修改 RTL 后自动跑
  「verif 微用例 + 全系统 difftest + 随机回归 + 断言」，失败即阻断合入；
- 归档每次回归的对象二进制与波形，便于回归定位。

---

## 6. 验证与调试文档索引（npc/verif/）

> 本文档（README）描述处理器架构与验证环境概览；**详细工作流、阶段任务与性能分析以
> `npc/verif/` 下文档为准**，按需查阅。

| 文档 | 内容 | 进度 |
|---|---|---|
| `verif/PROJECT_OVERVIEW.md` | **项目整体介绍（入口）**：组件地图、阶段 A–K 进度总表、文档索引、快速开始、关键事实 | ✅ 现行 |
| `verif/RUN_GUIDE.md` | **运行速查**：cpu-tests/am-tests/microbench/rt(PSRAM+SDRAM)/test_prog/npc sim/verif 的编译运行命令 + 参数 + 常见坑 | ✅ 现行 |
| `verif/DEBUG_WORKFLOW.md` | 权威验证链路、数据逐级定位法、波形/编译开关管理（DIFF/WAVE/WITH_TRACE/WITH_SDL）、LDS/BOOT_S 链接启动、程序启动流程、硬件经验 | 现行，持续更新 |
| `verif/VERIF_TESTS.md` | 测试体系（verif 微测试/断言/形式化；运行命令见 RUN_GUIDE） | 现行 |
|  `verif/records/process/STAGE_H_ONWARDS_TASKS.md` | C5.5 讲义阶段 H–K 的任务定义与实现路径 + 完成记录 | H–J5 ✅；K 🔶（ChipLink 结构保证） |
|  `verif/records/knowledge/MEM_PIPELINE_OPT.md` | 访存流水线性能分析与优化方向（架构分析/瓶颈/验证策略/优化方向/浪费点清单） | 审计完成，优化未实施 |
| `verif/records/process/` | 日志型归档：各阶段实施/调试过程记录与任务提示词 | 归档 |
| `verif/records/knowledge/` | 经验性归档：案例复盘/方法论/性能分析 | 归档 |

> 注：`verif/` 下除各级 `README.md` 外的 md 文件被 `npc/.gitignore` 忽略（工作区本地文档，
> 不进 git 状态），按上面索引即可定位到各主题。

---

*RTL 文件：`npc/vsrc/ysyx_22040750.v`；验证环境与文档：`npc/verif/`；SoC：`npc/ysyxSoC/`。*