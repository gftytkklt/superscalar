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
│   ├── DEBUG_WORKFLOW.md    # 调试工作流与阶段 A–I 执行记录（权威验证链路、波形管理、启动流程）
│   ├── VERIF_TESTS.md       # 测试体系（现行）
│   ├── STAGE_H_ONWARDS_TASKS.md   # 阶段 H–K 任务定义与实现路径（进度见 §6）
│   ├── MEM_PIPELINE_OPT.md  # 访存流水线性能分析与优化方向（架构/瓶颈/验证/优化）
│   ├── records/             # 各阶段原始调试记录（STAGE1/2/3、STAGE_F、STAGE_I 等）
│   ├── Makefile             # make / make run T=xxx / make fst T=xxx / make assert / make formal
│   ├── tb_main.cpp          # AXI4 内存模型 + 时钟/复位 harness（断言失败返回非 0）
│   ├── tests/               # 汇编微测试：bug2_csr bug3_div bug4_fencei
│   ├── assert/              # 阶段2：bind 注入的仿真期断言（$error 监视器）
│   │   ├── cache_bypass_check.sv   # bug1：cacheable 访问不许进 MMIO 状态（可 CACHE_CHECK_OFF）
│   │   ├── csr_hazard_check.sv     # bug2：CSR 写读冒险（MEPC 定向）
│   │   └── div_zero_check.sv       # bug3：除零商必须为 -1
│   └── formal/              # 阶段2：SymbiYosys 形式化（.sby + SVA props；装 sby/z3 后 make formal）
│       ├── props_div.sv  div.sby       # bug3 证明 + cover
│       └── props_dcache.sv dcache.sby  # bug1 状态可达性 cover
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

## 3. 已知 Bug（本次代码审查 + 微验证得出）

> 均已通过 `npc/verif` 定向微测试在 RTL 级复现（观察值来自仿真）。

### 3.1 【高】Level-I/D Cache 完全被旁路，恒走 MMIO 单拍
- **根因**：`dcachectrl` 与 `icachectrl` 中 `mmio_flag` 被无条件置真——
  `ysyx_22040750.v:2014` `assign mmio_flag = (I_cpu_rd_req || I_cpu_wr_req);`，
  `:3199` `assign mmio_flag = I_cpu_rd_req;`。而 FSM 内 `if(mmio_flag) → MMIO_*` 先于
  `rd_hit/rd_miss/wr_*` 判定，导致命中/缺失分支**结构上不可达**。
- **证据**：全系统波形 `cache_e.icache_e.current_state` 全程仅出现
  `IDLE(0)/MMIO_AR(0x10)/MMIO_RD(0x20)`；`dcache` 仅出现 `IDLE/MMIO_AR/MMIO_AW/MMIO_RD/MMIO_WR`，
  从未进入 `RD_*/WR_*/FENCEI`。
- **影响**：所有取指/访存都退化为总线单拍（`arlen=0`）访问；8 块 SRAM、tag/valid/dirty 表、
  cacheline 回写与 fence.i 清缓存逻辑全部为死电路。IPC 极低（每指令一次总线往返）；对带读副作用
  的外设（UART FIFO 等）语义不严谨。功能上因直连总线兜底仍能通过 difftest。
- **修复方向**：将 `mmio_flag` 恢复为按地址区间的判定（源文件注释里保留的
  `ysyx4/ysyx6` 版本），并回归验证 cache 命中/未命中/替换/写回/fence.i。

### 3.2 【中】CSR 读写冒险：连续同址 CSR 操作读到旧值，且旧值回写会破坏 CSR
- **根因**：`stall_unit` 的 `intr_op` 只涵盖 `ecall/ebreak/mret/中断`（`ysyx_22040750.v:4148`），普通
  `CSRRW/CSRRS/CSRRC` 不触发任何停顿；`csr_foward`（`:1424-1429`）EX 前递源取的是译码
  时快照 `ID_EX_csr`（旧值），而非更新后值。
- **证据**（`verif/tests/bug2_csr.S`）：`csrw mepc,0x12345678` 后紧跟 `csrr t1,mepc`，
  实测 `t1 = 0`（规范应为 `0x12345678`）；且该 `csrr`（CSRRS）在回写阶段用旧值把
  `mepc` 从 `0x12345678` **改回 0**（波形 `csr_e.mepc`：0→0x12345678→0）。对照组
  （重写后隔开若干条指令再读）得到正确的 `0x12345678`，说明写通路本身无误，纯粹是
  冒险窗口问题。
- **修复方向**：对普通 CSR 写指令同样生成停顿（或正确前递 `EX_MEM_csr/MEM_WB_csr` 新值）。

### 3.3 【中】有符号除零（负被除数）商错误
- **根因**：`radix2_div`（`:3847-3885`）除零时每拍 `current_q=1`，`abs_quotient` 填全 1；
  商符号 `q_flag = dividend 符号`，负被除数时 `商 = -abs_quotient = +1`，而 RV64 规范要求
  `DIV x,neg,/0 = -1(全F)`。
- **证据**（`verif/tests/bug3_div.S`）：`div a2,-5,0` → `0x0000000000000001`（规范 `-1`）；
  `rem a3,-5,0` → `-5`（正确）；`div a5,5,0` → `-1`（正确，仅负被除数异常）。
- **修复方向**：除零时直接把商置为全 1（被除数符号无关）、余数保持被除数，从而覆盖负被除数情形。

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

### 4.2 独立核微验证（npc/verif，定位 bug 用）
在不编译 SoC、不依赖 NEMU 的前提下，用 Verilator 直接编译 CPU 核本身，配一个自写的
AXI4 内存模型（`tb_main.cpp`）直接驱动取指/访存，适合写定向微用例。

`tb_main.cpp` 的从端模型按 Verilog 分层事件队列建模：每个仿真步 = 一次 posedge eval +
一次 settle eval；从端把组合输出与"触发器寄存器(NBA 拍延迟)"分开写，AR 请求延迟一拍给
rvalid、wdata 接收后延迟一拍再给 bvalid，全部握手驱动、无启发式退避。

```bash
cd npc/verif
make                  # 编译模型并跑全部 tests/*.S
make run  T=bug2_csr  # 只跑某个用例
make fst  T=bug2_csr  # 跑并保留 build/bug2_csr.fst 波形
make clean
```

- 用例机制：映像放到 Flash `0x30000000`（复位 PC `0x2ffffffc` → `snpc=pc+4` 自然引导）；
  程序把结果写入 SRAM `0x0f000000` 后 `ebreak` 结束；harness 打印 SRAM 区与 AXI 事务日志。
- 现有用例：`bug2_csr`(CSR 冒险)、`bug3_div`(除零)、`bug4_fencei`(fence.i 流程)。

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
- 等 **3.1 cache 修复**后补充命中/未命中/替换/脏写回/fence.i 序列用例；
- 将这些并入 `npc/verif`，形成可重复的回归套件。

### 阶段 2：断言与形式化（轻量、性价比最高）—— ✅ 已落地
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
     make assert        # 抓 bug2/bug3：当前结果 FAIL bug2_csr / FAIL bug3_div / PASS bug4_fencei
     make assert-cache  # 连 bug1 一起：三个用例首拍即报 "ICACHE bypassed"
     ```
2. **形式化（`npc/verif/formal/`）** ✅ 已实跑（yosys+z3+sby）
   - 工具链：`apt install yosys z3`；`sby` 需另装（非 PyPI 包）——从
     `github.com/YosysHQ/sby` 拉源码后 `make install PREFIX=~/.local`，并软链
     `/usr/bin/yosys-smtbmc -> ~/.local/bin/smtbmc`，然后 `make formal` 即可；
   - 内容：`props_div.sv`(除零规范断言+驱动) / `props_dcache.sv`(cache 状态可达性
     cover)；RTL 经 `formal/trim_rtl.py` 抽出 `radix2_div`/`dcachectrl` 自包含块
     给 yosys（避开 DPI-C），并修正 RTL 的 0 位宽字面量；
   - **当前结果（buggy RTL）**：
     - `div.sby`（bmc depth100）：z3 在 step 67 给出**真实反例**
       `-5/0`：quotient=+1（规范 -1）、remainder=-5（正确），与仿真断言一致；
     - `dcache.sby`（cover depth30）：RD_HIT/RD_MISS/WR_HIT/WR_MISS 四个 cover
       全部不可达 → 形式化证明 cache 恒旁路；
   - 修复对应 RTL 后两条均应转 PASS，作为"证明级"回归项。

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
| `verif/DEBUG_WORKFLOW.md` | 权威验证链路、数据逐级定位法、波形/编译开关管理（DIFF/WAVE/WITH_TRACE）、LDS/BOOT_S 链接启动、阶段 A–I 执行记录、程序启动流程 | 现行，持续更新 |
| `verif/VERIF_TESTS.md` | 测试体系（cpu-tests/test_prog/microbench 等判定标准） | 现行 |
| `verif/STAGE_H_ONWARDS_TASKS.md` | C5.5 讲义阶段 H–K 的任务定义与实现路径 | H/I/J0/J1 ✅，J2–J5/K 待开始 |
| `verif/MEM_PIPELINE_OPT.md` | 访存流水线性能分析与优化方向（架构分析/瓶颈/验证策略/优化方向/浪费点清单） | 审计完成，优化未实施 |
| `verif/records/` | 各阶段原始调试记录：STAGE1 缓存重构、STAGE2 访存接口、STAGE3 PSRAM 读回、STAGE_F RT-Thread 提示词、STAGE_I SDRAM 位扩展/字扩展、STAGE_J1 GPIO | 归档 |

> 注：`verif/` 下除 `records/README.md` 外的 md 文件被 `npc/.gitignore` 忽略（工作区本地文档，
> 不进 git 状态），按上面索引即可定位到各主题。

---

*RTL 文件：`npc/vsrc/ysyx_22040750.v`；验证环境与文档：`npc/verif/`；SoC：`npc/ysyxSoC/`。*