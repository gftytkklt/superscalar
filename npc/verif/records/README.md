# npc/verif/records —— 分阶段调试过程记录（归档）

> 历史调试过程/交接文档。**入口/总览见 `../PROJECT_OVERVIEW.md`（项目介绍+阶段总览+文档索引），
> 运行命令速查见 `../RUN_GUIDE.md`；主工作流与各阶段结论以 `../DEBUG_WORKFLOW.md` 为准**
> （§4 阶段执行记录、§5 启动流程）。此处保留各阶段更原始/更详细的排查过程，便于回查，不再单独维护。
> 集中归档于 2026-08-31（原在 verif/ 根目录）。

| 文件 | 阶段/主题 | 要点 |
|---|---|---|
| `STAGE1_CACHE_REWORK.md` | 缓存重构 + SoC 访存接口适配 | cache AX/X 耦合点 C1–C8、dcache 写分配掩码、fence.i/cacheline 写回 bug、验证体系（注：末尾含一段"阶段2"草稿，与 STAGE2 重叠） |
| `STAGE2_MEM_IF.md` | 阶段2 访存接口重构设计基线 | CPU↔cache 接口、AXI burst/MMIO 生成、slave_crossbar、SoC 地址映射、重构实施计划 S0–S5 |
| `STAGE3_PSRAM_READDBG.md` | 阶段3 PSRAM 读回错位调试 | flash 数据通路修复、PSRAM 读回逐级定位、根因=dcache 写分配掩码 |
| `STAGE_F_RTTHREAD_PROMPT.md` | 阶段 F 任务提示词 | RT-Thread 在 PSRAM 执行的原始任务说明（结论见 DEBUG_WORKFLOW 阶段 F 记录 + §5） |
| `STAGE_I_SDRAM_EXT_PROMPT.md` | 阶段 I 任务提示词 | SDRAM 位扩展(2颗粒→32bit)+字扩展(4颗粒)——**新对话续作提示词** |
| `STAGE_I_SDRAM_EXT.md` | 阶段 I 实施记录 | 位扩展(64MB)+字扩展(128MB)的相位推导/改动/坑/验证数据；结论见 DEBUG_WORKFLOW 阶段 I 记录 |
| `STAGE_J1_GPIO.md` | 阶段 J1 实施记录 | GPIO 控制器 RTL + 寄存器/引脚验证（difftest ON + 波形）；NVBoard 显示待 J0 |
| `STAGE_J0_NVBOARD.md` | 阶段 J0 实施记录 | NVBoard 接入 soctest（Makefile/soctest/nxdc/auto_bind）+ GPIO 7 段译码；坑与验证 |
| `STAGE_J2_UART.md` | 阶段 J2 实施记录 | AM_UART_RX + UART 除数随 NVBoard 条件化 + RT-Thread 键入命令 + am-tests hello 验证 |
| `STAGE_J3_PS2.md` | 阶段 J3 实施记录 | PS/2 控制器 RTL（解码+FIFO）+ AM 键盘 IOE（翻译表）+ soctest 防误采；am-tests keyboard + NVBoard 打印 Got (kbd) |
| `STAGE_J4_VGA.md` | 阶段 J4 实施记录 | VGA/timer/video：RTL vga_top_apb(已有)+AM GPU IOE+AM_TIMER_UPTIME(mtime 单8B读)；NVBoard 画面+FPS；坑=NVBoard UART 仅支持除数1、.bss 搬运、时间比例待定 |
| `STAGE_J_ONWARDS_PROMPT.md` | 阶段 J 后续任务提示词 | J 阶段 J1–J5 现状/目标/实现路径（J3–J5 已陆续完成）——**新对话续作提示词** |
| `STAGE_J5_RTTHREAD_AM.md` | 阶段 J5：rt-am 合并 + am-apps 集成 | rt-am 的 am-apps 集成机制并入 rt（保留 npc 布局适配，默认不集成）；`make update` 集成 hello/microbench/typing-game/snake → msh `am_<app>` 跑 AM 程序线程（am_hello 目视验证）；fceux 编译阻塞待修；**附录含 RT-Thread 带 NVBoard 的 make 链路与组件归属 + SDRAM 路径** |
| `rtthread-stackoverflow-debug.md` | RT-Thread 栈溢出调试（NEMU 平台） | 现象→定位→验证→修复：根因是 main 线程栈溢出破坏对象链表，非 NEMU bug |
| `STAGE_B3_CACHE_PERF.md` | B3《性能优化和简易缓存》任务完成说明 | 讲义任务清单→现状映射；icache/dcache 参数化分析（容量/块大小→index/tag 已参数化，路数/行宽/替换策略/AXI 突发硬编码+原因）；icache 形式化（REF-vs-DUT 实测 3 次不可判定，与 dcache.sby 同因），form 化树保持 div/axiburst PASS |
| `B3_PLAN.md` | B3 分阶段整体计划（工作流确认稿） | 把 B3 剩余可执行任务排成 阶段1 性能计数器 → 阶段2 扩展+Amdahl瓶颈 → 阶段3 cachesim → 阶段4 APB延迟校准 → 阶段5 make perf → 阶段6(可选)icache BMC；每阶段=一个"停点"，含人工决策/软件安装标识 |
| `ONSCRIPTER_NAVY_NATIVE_DEBUG.md` | PA4.5 选做：ONScripter Navy native 黑屏/透明调试 | **已结案**：根因=native.cpp 本地上屏实现（renderer/ARGB 纹理）偏离官方框架、与 mutter 合成不兼容（§9）；自研 miniSDL/NDL 经双侧对照证实无恙；修复=上屏路径官方化（WindowSurface+BlitScaled, AMASK=0）+ UpdateRect 强制 alpha=0xff；含 §2 劫持误判修正、riscv64 链接失败为既有问题备注 |
| `ONSCRIPTER_PROMPT_V2.md` | ONScripter navy native 显示问题——**新对话续作提示词** | 任务目标/已固化事实（架构+SDL版本硬证据+修复定性表）/工作流约束（禁改 native.cpp）/建议执行顺序/关键文件与复现方式 |
| `ONSCRIPTER_FIX_PLAN.md` | ONScripter 显示修复整体计划（2026-09-04 结案） | 阶段 A–D 计划与执行结果：劫持误判修正→双侧对照打印验证自研层→根因定性（框架呈现段）→官方化修复+诊断清除；调试方法论（fb 转储分界判据/逻辑锁）见主记录 §9.2 |
| `ONSCRIPTER_RISCV_NEMU_PORT.md` | ONScripter riscv64(NEMU) 移植（2026-09-04 验证通过） | navy riscv64 编译打通（Makefile 条件过滤）；内核三修复（fs_open POSIX+路径规范化 / sys_execve·sys_exit 补 FG_PROCESS 守卫 / context_uload 重置 max_brk）；NEMU VGA 800x600 + syncconfig 坑；运行命令；NPC 内嵌 ramdisk 机制（休眠未验证） |

> 阶段 D/E/F/G/H/I 的最终结论、坑与修复已固化进 `../DEBUG_WORKFLOW.md` §4（阶段 A–I 记录）与
> §5（启动流程）；`VERIF_TESTS.md`（测试体系）仍在 verif/ 根目录，作为现行参考。
> 仿真配置界面（`make menuconfig`、`npc/.npc_config`、BOOT_MODE 启动模式绑定）见
> `../DEBUG_WORKFLOW.md` §2.9。