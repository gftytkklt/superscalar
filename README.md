# "一生一芯" 工程项目（ysyx-workbench）

这是"一生一芯"课程的工程工作区，包含软件模拟器、自研处理器 RTL 以及配套的软件栈/OS 实验。通过

```bash
bash init.sh subproject-name
```

初始化各子项目，具体流程请参考[实验讲义][lecture note]。

## 整体架构

工作区由若干协同工作的子项目组成：

| 目录 | 角色 | 说明 |
| --- | --- | --- |
| `nemu/` | 软件参考模型 | RISC-V 指令级模拟器（NEMU），在真机流片中作为 difftest 对拍的 golden model |
| `npc/` | **自研处理器** | 自研 RISC-V64 处理器（RTL 单文件 `vsrc/ysyx_22040750.v`：五级流水 + 参数化 I/D Cache），集成进 Chisel 生成的 `ysyxSoCFull` SoC，经 AXI4（64bit）接入总线；SDRAM 走 `AXI4SDRAM` + 32B 突发、带延迟校准模块；含独立验证环境与文档 `npc/verif/`（详见 [npc/README.md](./npc/README.md) §6 文档索引） |
| `abstract-machine/` | 运行库 | AM（Abstract Machine）教学运行库：TRM / IOE / CTE / VME，为 OS 与 App 提供统一硬件抽象 |
| `am-kernels/` | 核内测试集 | 运行在 AM 之上的内核测试程序 |
| `nanos-lite/` | 操作系统 | 基于 AM 的教学操作系统（进程/虚存/文件系统/设备驱动） |
| `navy-apps/` | 应用 | 运行在 nanos-lite 上的应用集合（pal、仙剑、Lua、NES 模拟器等） |
| `rt/` | RTOS | RT-Thread，可移植到 AM 之上运行的操作系统实验 |
| `fceux-am/` | 应用 | 移植到 AM 的 FC 模拟器 |
| `nvboard/` | FPGA | 基于 FPGA 的板卡支持环境 |

> **工程边界**：本工程的自研产出集中在 `npc/`（处理器 RTL + `npc/verif/` 验证/性能/归档体系）；
> 其余目录（`nemu/`、`abstract-machine/`、`am-kernels/`、`nanos-lite/`、`navy-apps/`、`rt/`、
> `fceux-am/`、`nvboard/`）为课程上游子仓库，由 `init.sh` 初始化、按讲义配套使用，
> 其仓库内的改动不属于本工程的归档/提交范围。

### 数据流概览

```
   C/汇编 测试程序 (am-kernels / test_prog)
        │ 编译链接（flash 基址 0x30000000）
        ▼
   NPC 核（RV64 五级流水）─→ I/D Cache（4KB/32B/2 路，可参数化）
        │                          │ AXI4（64bit；cacheable 32B 突发 / MMIO 单拍）
        │                          ▼
        │                  ysyxSoC 总线 ─→ Flash / PSRAM / SRAM / UART/GPIO/PS2/VGA
        │                          └─→ SDRAM 控制器（AXI4SDRAM；axi4_delayer/axi64to32 校准与宽拆）
        ▲
        │ difftest 同步（GPR/PC 逐指令对拍）
   nemu 软件参考模型
```

- 真机侧：`npc` 的 RTL 在 FPGA/SoC 上运行，通过 UART 与外部交互；
- 仿真侧：`npc` 经 Verilator 编译成 `ysyxSoCFull` 仿真模型，与 `nemu` 进行 difftest 逐指令对拍，保证 RTL 与参考模型行为一致；
- 软件侧：`abstract-machine` 及以上运行于处理器之上，支撑整机程序与操作系统实验。

### 验证/测试分层（工具用途与用法目录：`npc/verif/README.md` §3）

| 层 | 对象 | 主要技术与入口 |
| --- | --- | --- |
| L1 裸核微验证 | CPU 核 + 自写 AXI 内存模型 | `npc/verif` 的 `make`/`run`/`fst`（13 例定向微测试）、`ptest`/`pfst`（主存模式）、`assert`/`assert-cache`（4 断言） |
| L2 形式化 | 核/缓存/总线模块（裁剪 RTL + 46 个 `PROBE_*`） | `make formal` 四件（div/axiburst/icache/pipeline；`pipeline` 深探 depth 20） |
| L3 全系统 + difftest | `ysyxSoCFull` + NEMU 参考模型 | `npc` 的 `make DIFF=1 WAVE=1 sim` + AM/cpu-tests/riscv-tests 套件（riscv-tests NPC 自校验 66 PASS/1 SKIP） |
| L4 性能/面积 | SoC+总线延迟模型 / 综合网表 | 性能计数器与看门狗（`make perf`：18,318,000/1,352,016）、cachesim、`npc/verif/sta/` STA 与部件频率探针 |

## 现状与目标

本工作区作为同时包含 **RISC-V 软件解释器（NEMU）、自研处理器 RTL（NPC）、简易操作系统
（nanos-lite / RT-Thread）与 SoC 集成（ysyxSoCFull）** 的完整平台：

- ✅ **NEMU**：已完成 PA 全部内容（指令集/系统调用/difftest/设备，含磁盘设备）；
- ✅ **NPC**：支持 **ChipLink 以外**的全部功能（cache/SDRAM AXI 突发/外设/RT-Thread/VGA/AM-apps 等，
  阶段 A–K 完成情况见 `npc/verif/docs/PROJECT_OVERVIEW.md` §3）；
- ✅ **B3「性能优化和简易缓存」**：全部可执行项均完成或已记录豁免——
  阶段 1–7 结案；阶段 8（P-A~P-H）全部完成（E4 缓存几何落地按用户裁决暂停）；
  train 规模：xip 2.458B / sdram-heap 2.135B / **全 SDRAM 1.917B cycles**（长跑最优），
  见 `npc/verif/docs/B3_PLAN.md`、`npc/verif/docs/STAGE_B3_CACHE_PERF.md`；
- ✅ **B4「流水线优化与验证深化」**：Q1–Q7 全部结档（量化/计数器/branchsim/fence.i 反例/流水线形式化
  depth 20/2 个真实 RTL 缺陷修复/OPT-05 暂缓、OPT-11 否决），见
  `npc/verif/docs/B4_PLAN.md`、`npc/verif/records/process/B4_Q7_CLOSE.md`；
- ✅ **riscv-tests 接入与 R-5 修复**：官方 rv64ui+rv64um 67 例（NPC 自校验），修复 divuw/remuw 与
  `jalr rd=rs1` 两个真实缺陷后 **66 PASS / 0 FAIL / 1 SKIP**（ma_data 对齐异常未实现）；
  **NEMU REF 语义缺陷（mulh/div）已单独立项修复（N-1）**，NEMU 原生同为 66/0/1/0 且 mul/div 用例可 DIFF=1；
  见 `npc/verif/docs/RISCV_TESTS_PLAN.md`、`npc/verif/records/process/{B4_R5_RISCV_FIXES,NEMU_REF_FIXES}.md`；
- ✅ **验证体系**：13 例定向微测试、4 个仿真期断言、形式化四件（`pipeline.sby` depth 20）、
  difftest 对拍、性能计数器/看门狗/cachesim/STA 等；**调试技术目录见
  `npc/verif/README.md` §3**（每项含用途/用法/产物）；
- 🎯 **未来目标**：
  1. 在 **NEMU 与 NPC 双端启动 Linux 操作系统**；
  2. **持续对 NPC 架构进行性能分析与优化**（方法底座见
     `npc/verif/records/knowledge/MEM_PIPELINE_OPT.md`；候选见 `npc/verif/docs/ARCH_OPT_BACKLOG.md`；
     DSE 备选方案见 `npc/verif/records/process/B3_STAGE8_PE_DSE.md`，如需重启 E4 落地）。

> **文档入口链**：根 `README.md`（本文件）→ `npc/README.md`（处理器/验证总览）→
> `npc/verif/README.md`（验证环境、**调试技术目录 15 项**与文档索引）→
> `npc/verif/docs/PROJECT_OVERVIEW.md`（项目总览）。专题：`ARCH_OPT_BACKLOG.md`（架构优化台账）、
> `RISCV_TESTS_PLAN.md`（riscv-tests 接入与 R-5）、`B4_PLAN.md`/`B3_PLAN.md`（阶段计划）。
> **历史归档**：`npc/verif/records/README.md`（`process/` 按项目推进顺序、`knowledge/` 经验复盘，
> 含"权威/快照/被取代"关系表；2026-09-21 结构化重构）。

## 使用

- 子项目编译/仿真各自在自己的目录内以 `make` 驱动（参见各子项目 README）；
- 顶层 `Makefile` 仅用于 ysyx 自动 git 提交（tracer 机制），请勿修改其中"勿动"部分。

## 分支说明（本地）
new_world（当前分支）: PA4.5选做部分分支，npc验证环境与用例搭建
soc: 与第六期讲义兼容的分支，大概开发至SPI接口（未完成）
pa3-test: 软件部分运行仙剑和rt的第五期流片环境
其余分支: 我也记不清都是什么了

[lecture note]: https://ysyx.oscc.cc/docs/