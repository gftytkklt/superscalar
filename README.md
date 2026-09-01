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
| `npc/` | **自研处理器** | 自研 RISC-V64 处理器（Verilog RTL `ysyx_22040750.v`），集成进 Chisel 生成的 `ysyxSoCFull` SoC，并经 AXI4 接入总线路由到存储与外设；内含独立验证环境与文档 `npc/verif/`（调试工作流/阶段任务/访存性能分析，详见 [npc/README.md](./npc/README.md) §6 文档索引） |
| `abstract-machine/` | 运行库 | AM（Abstract Machine）教学运行库：TRM / IOE / CTE / VME，为 OS 与 App 提供统一硬件抽象 |
| `am-kernels/` | 核内测试集 | 运行在 AM 之上的内核测试程序 |
| `nanos-lite/` | 操作系统 | 基于 AM 的教学操作系统（进程/虚存/文件系统/设备驱动） |
| `navy-apps/` | 应用 | 运行在 nanos-lite 上的应用集合（pal、仙剑、Lua、NES 模拟器等） |
| `rt/` | RTOS | RT-Thread，可移植到 AM 之上运行的操作系统实验 |
| `fceux-am/` | 应用 | 移植到 AM 的 FC 模拟器 |
| `nvboard/` | FPGA | 基于 FPGA 的板卡支持环境 |

### 数据流概览

```
   C/汇编 测试程序 (am-kernels / test_prog)
        │ 编译链接（flash 基址 0x30000000）
        ▼
   npc/ysyxSoCFull  --(AXI4)-->  存储与外设（Flash/SRAM/UART/GPIO/...）
        ▲
        │ difftest 同步（GPR/PC 逐指令对拍）
   nemu 软件参考模型
```

- 真机侧：`npc` 的 RTL 在 FPGA/SoC 上运行，通过 UART 与外部交互；
- 仿真侧：`npc` 经 Verilator 编译成 `ysyxSoCFull` 仿真模型，与 `nemu` 进行 difftest 逐指令对拍，保证 RTL 与参考模型行为一致；
- 软件侧：`abstract-machine` 及以上运行于处理器之上，支撑整机程序与操作系统实验。

## 使用

- 子项目编译/仿真各自在自己的目录内以 `make` 驱动（参见各子项目 README）；
- 顶层 `Makefile` 仅用于 ysyx 自动 git 提交（tracer 机制），请勿修改其中"勿动"部分。

## 分支说明（本地）
new_world（当前分支）: PA4.5选做部分分支，npc验证环境与用例搭建
soc: 与第六期讲义兼容的分支，大概开发至SPI接口（未完成）
pa3-test: 软件部分运行仙剑和rt的第五期流片环境
其余分支: 我也记不清都是什么了

[lecture note]: https://ysyx.oscc.cc/docs/