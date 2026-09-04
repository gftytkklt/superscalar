# records/process —— 日志型归档（阶段实施/调试过程/任务提示词）

> 按时间顺序的"当时做了什么"：实施记录、调试时间线、任务定义与续作提示词（PROMPT）、修复计划。
> 可复用的经验与方法论见 [`../knowledge/README.md`](../knowledge/README.md)。
> 入口总览/现状目标见 [`../../PROJECT_OVERVIEW.md`](../../PROJECT_OVERVIEW.md)。

## 访存体系（阶段 1–3）

| 文件 | 主题 | 要点 |
|---|---|---|
| `STAGE1_CACHE_REWORK.md` | 缓存重构 + SoC 访存接口适配 | cache AX/X 耦合点 C1–C8、dcache 写分配掩码、fence.i/cacheline 写回 bug、验证体系（末尾含"阶段2"草稿，与 STAGE2 重叠） |
| `STAGE2_MEM_IF.md` | 阶段2 访存接口重构设计基线 | CPU↔cache 接口、AXI burst/MMIO 生成、slave_crossbar、SoC 地址映射、S0–S5 实施计划 |
| `STAGE3_PSRAM_READDBG.md` | 阶段3 PSRAM 读回错位调试 | flash 数据通路修复、PSRAM 读回逐级定位、根因=dcache 写分配掩码 |

## RT-Thread / SDRAM / 外设（阶段 F–K）

| 文件 | 主题 | 要点 |
|---|---|---|
| `STAGE_F_RTTHREAD_PROMPT.md` | 阶段 F 任务提示词 | RT-Thread 在 PSRAM 执行的原始任务说明（结论见 DEBUG_WORKFLOW 阶段 F 记录） |
| `STAGE_H_ONWARDS_TASKS.md` | 阶段 H–K 任务定义与实现路径 | SDRAM/字扩展/外设 J1–J5/ChipLink 的任务分解+完成记录 |
| `STAGE_I_SDRAM_EXT_PROMPT.md` | 阶段 I 任务提示词 | SDRAM 位扩展(2颗粒→32bit)+字扩展(4颗粒)——新对话续作提示词 |
| `STAGE_I_SDRAM_EXT.md` | 阶段 I 实施记录 | 位扩展(64MB)+字扩展(128MB)的相位推导/改动/坑/验证数据 |
| `STAGE_J0_NVBOARD.md` | J0 NVBoard 接入 | NVBoard 接入 soctest + GPIO 7 段译码；坑与验证 |
| `STAGE_J1_GPIO.md` | J1 GPIO | GPIO 控制器 RTL + 寄存器/引脚验证（difftest ON + 波形） |
| `STAGE_J2_UART.md` | J2 UART | AM_UART_RX + 除数随 NVBoard 条件化 + RT-Thread 键入 + am-tests hello 验证 |
| `STAGE_J3_PS2.md` | J3 PS/2 键盘 | RTL 解码+FIFO + AM 键盘 IOE 翻译表 + soctest 防误采 |
| `STAGE_J4_VGA.md` | J4 VGA/timer/video | vga_top_apb + AM GPU IOE + mtime；坑=NVBoard UART 除数、.bss 搬运 |
| `STAGE_J5_RTTHREAD_AM.md` | J5 rt-am 合并 + am-apps 集成 | make update 集成 hello/microbench/snake → msh am_<app>；附录含 RT-Thread 带 NVBoard 的 make 链路 |
| `STAGE_J_ONWARDS_PROMPT.md` | 阶段 J 后续任务提示词 | J1–J5 现状/目标/实现路径——新对话续作提示词 |

## ONScripter 移植（PA4.5 选做，2026-09-03 ~ 09-04）

| 文件 | 主题 | 要点 |
|---|---|---|
| `ONSCRIPTER_PROMPT_V2.md` | 续作提示词 | 任务目标/已固化事实/工作流约束/建议执行顺序 |
| `ONSCRIPTER_NAVY_NATIVE_DEBUG.md` | navy-native 透明窗口调试（**结案**） | 根因=native.cpp 上屏偏离官方框架；含 §2 劫持误判修正、§8 调试技巧、§9 结案（定位方法/逻辑锁） |
| `ONSCRIPTER_FIX_PLAN.md` | 显示修复整体计划与执行 | 阶段 A–D：误判修正→双侧对照→根因定性→官方化修复 |
| `ONSCRIPTER_RISCV_NEMU_PORT.md` | riscv64(NEMU) 移植（**验证通过**） | navy 编译打通；内核三修复（fs_open/sys_execve·exit/max_brk）；syncconfig 坑；运行命令；NPC 内嵌 ramdisk 休眠机制 |
