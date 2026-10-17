# CRP 首批：CCR-F0015 修复与局部回归

2026-10-17。**Completed；满足已确认的五项 host 局部验收，修复结果待用户确认，尚未提交修复。**
独立任务 CRP，不占用或推进 Linux Milestone/Phase，不 Reopen CCR-P10。

## 授权、恢复与范围

用户先要求“仅执行第一批已确认的修复项”，随后明确“提交后继续实施”。沿用
[已确认方案](../REPAIR_AND_REGRESSION.md#repair-plan-approval-20261017)，没有重新生成修复计划。
准备文档的可跟踪导航已提交 `2f11b081f5fc2ab5c8bebdc8bb6a0ec52c9ca61f`；只含
`npc/verif/records/process/README.md` 的两行新增。未 push、未 force-add ignored 资产。
普通 commit 首次遇到 `.git/index.lock` 只读限制，使用已授权的沙箱提升重试成功。

Project Resume / Guard：根仓库为 `boot_linux`，提交准备文档前 HEAD `0ee3778`；原唯一
tracked 修改为已知方案导航，暂存区为空。10 个嵌套仓库的 HEAD、binary diff 和 status
与 CCR 原记录一致；F0015 两处关联源码 SHA 与台账一致。状态差异均可由当前授权解释，
无 State Consistency Conflict；没有全量重审或重跑历史验收。

| CCR-F | 原因 / 最小修复 | 文件、依赖与状态 |
|---|---|---|
| CCR-F0015 / Medium / Confirmed | 32 GPR 循环未检查 REF 执行后 PC；新增 `difftest_check_reg("pc", pc, ref_r->pc, cpu.pc)`，将结果纳入原返回值 | 仅生产文件 `nemu/src/isa/riscv32/difftest/dut.c` 增加一行；已修复并通过本批局部验收，待确认/提交 |

`riscv64 -> riscv32` 为既有软链接，RV64 使用该实现。函数参数 `pc` 仍为诊断用指令地址，
实际比较双方执行后 PC。原 GPR 循环、33 字 packet、CPU_state、skip/detach/attach 和错误传播
代码均未改。调用方 `nemu/src/cpu/difftest/dut.c`、真实头文件及 Spike adapter 为只读依赖。
没有其他 CCR-F/CQ 硬前置；没有修改 NPC→NEMU REF 三参接口、RTL、原配置或原 build。

## 修改与证据文件

- 生产实现：上述 `dut.c`，一行新增，原模式 `0775` 保持。
- [harness.c](harness.c)：43 个固定案例；链接真实比较函数、真实 `difftest_step` 和原头文件。
  REF 执行/transport、RAM transport、寄存器名称数组及显示依赖为 fixture；没有替换比较逻辑。
- [run.py](run.py)：隔离复制源码、头和配置，仅 overlay 启用 DIFFTEST；逐项归档编译 argv、
  stdout/stderr、退出码、输入/产物 hash，失败/空结果不得 PASS，已有输出目录不覆盖。
- 本 README、记录索引及本地 `.agent`：修复结果、当前状态和停点；不重写 CCR 最终报告、
  findings.json、coverage 或 P10 历史 manifest。
- `baseline.json`、`repair.patch`、`gate-checks.json`、`relocations.json`、`validation.json`、
  `manifest.json` 及 `build/` 下日志/快照为本地 ignored 证据，普通 commit 不备份它们。

原实现 SHA256：`a3eaaed25f24a192dfccc0127cac7084725a9fbcbf86cd31b2b29d8fc89038a8`。
修复后 SHA256：`bc43226e3d9f58f76f0324e5939051a3839e2dc4d9a38912ee9c6753db414733`。
调用链 SHA256 保持 `65d248290c71bf718c6d1ca0c737e10bce9674037330064406d3fb9a12c0cd4c`。

## 验证与实际结果

现有 `.config` 为 RV64、DIFFTEST 关闭。P3 对本问题只有静态证据，没有可直接复用的动态
反例；因此新增的是针对 PC 遗漏、宽度/取样时点、错误传播及比较恢复的定向测试。
用 `/usr/bin/gcc` 13.3.0、`-std=gnu11 -O2 -Wall -Wextra -fsanitize=undefined
-fno-sanitize-recover=all` 编译独立副本；三单元编译无警告，正常用例 stderr 为空。
受控 REF 只提供预先设定的公开状态，不计算 DUT 的正确结果。

运行时命令（在工作区根目录执行）：

```sh
python3 npc/verif/records/process/code_correctness_review/crp-f0015/run.py --stage before --out npc/verif/records/process/code_correctness_review/crp-f0015/before-02
python3 npc/verif/records/process/code_correctness_review/crp-f0015/run.py --stage after --out npc/verif/records/process/code_correctness_review/crp-f0015/after
git diff --check
git apply --reverse --check npc/verif/records/process/code_correctness_review/crp-f0015/repair.patch
```

输出随后移入已有忽略规则覆盖的 `build/`，避免快照中的 `.c/.h/.py` 成为待提交源码。
移动没有更改证据字节，原 argv/日志保留执行时路径；映射见 `relocations.json`。
当前证据位置为 `build/before-02`、`build/after`。再次运行请使用新的
`--out .../crp-f0015/build/replay-<唯一名称>`；原版重现须使用 `build/before-02/source`
中的原实现及冻结输入另建副本，不覆盖当前源码。

| 已确认验收 | 本轮实际结果 / 证据 |
|---|---|
| 1. 原版反例先于修改 | `build/before-02/summary.json`：43 项实际执行，36 PASS、7 FAIL，整体退出 1。PC-only 低位/高位比较错误返回 true；普通 step 状态仍 RUNNING、halt_pc 为哨兵，外层断言失败。同值及 32 个 GPR 差异对照均按预期工作。失败集合精确匹配，随后才修改生产代码。 |
| 2. 字段/取样矩阵 | `build/after/summary.json`：43/43 PASS，退出 0。PC 低位差 4、仅高 32 位不同、逐个 32 GPR、PC+GPR 同时不同均检出；两端执行后状态相同且诊断参数不同仍通过。 |
| 3. 真调用链/状态 | 普通 step 的 PC-only 差异进入 NEMU_ABORT，halt_pc 为该条指令地址、显示计数为 1；一致时保持 RUNNING。原日志检查 REF/right 和 DUT/wrong 值，低/高位诊断均与输入一致。 |
| 4. 控制路径/ABI | skip-ref 同步后先正常比较，再检出新 PC 差异；skip-dut 未追上时跳过，追上时用 GPR 差异证明进入比较，窗口结束后恢复并检出 PC 差异；detach 禁止比较/skip 请求，attach 同步后先正常比较再检出 PC 差异。静态及运行时断言 word=8、32 GPR、PC offset=256、packet=264 字节，CSR 在 packet 外。 |
| 5. 判据/归档 | 清单固定 43、逐项名称/有效数/退出码/marker 核对。`gate-checks.json`：失败工具 `/usr/bin/false`、假成功无产物工具 `/usr/bin/true`、未知案例、缺失案例，四项均退出 2，均不能 PASS。源码/config/模式、工具、编译 argv、日志、产物 hash 已归档；diff 空白检查和回滚 dry check 退出 0。 |

原版 7 个失败案例：`pc-low`、`pc-high`、`step-pc-low`、`step-pc-high`、`skip-ref`、
`skip-dut`、`detach-attach`。before 的 FAIL 是修复前真实缺口，不改写为产品 PASS。

保留的准备失败：首次基线采集误用字段 `source_sha256`，KeyError 后未写 baseline；已用
正确 `sha256` 重核。首次 `build/before/compile-0.stderr` 记录默认 gcc 经 ccache 因只读
cache 失败，整体退出 2、零案例执行；后续改用现有 `/usr/bin/gcc`。未安装或修改系统配置。最终审计首次将 Git 的 executable 标记误当作宿主模式 0755；实际前后均为 0775，已按冻结输入模式更正审计条件，原失败结果保存在 `validation-first.json`，没有修改文件权限。

## 验证边界、回归风险与未解决项

- 本批 host 局部验收满足；不把编译或 43 PASS 等同 ISA/guest/整机功能正确，也不将 L08
  标为全通过。完整 Spike、NPC→REF、guest/Linux/OpenSBI、RV32/其他 ISA 均为 NotRun。
- transport 只传原 adapter 的 33 字 prefix；没有动态加载真实 Spike，也未验证实际 REF
  指令执行/内存、RAM 字节内容或设备状态。attach 只检查调用顺序/范围/计数及寄存器同步。
- CSR/priv/内存不在比较承诺中；skip 窗口、detach 期间仍不比较。本修复可能更早暴露原先
  被 PC 漏检隐藏的差异，不能将新失败直接当成误报或扩大 skip。
- skip-dut 追上时原调用方以 `npc` 作为诊断/halt_pc 标签，测试明确保留该存量行为；本次
  未改变它，普通 step 的指令地址传播另行严格断言。
- 原 CCR 的 119 项为审阅结束时历史统计；本轮只处理 F0015，其余 118 项仍未解决，含
  5 CQ。F0016、F0116、F0119 等相邻接口问题保持原状态，两缺源仍未审。

## 回滚、下一批与停点

`repair.patch` 仅包含生产文件的一行补丁。已运行反向应用 dry check 成功；需要回滚时先
核对当前实现 SHA/mode，再 `git apply --reverse .../repair.patch`，核对原 SHA/mode。
若之后已有其他修改，停下核对，不能整文件覆盖或 reset/clean；测试及证据可以保留。

本批 Completed，修复和新增测试/记录 **未 commit、待用户确认**。只有准备文档已提交
2f11b08；没有自动提交修复、push 或开始下一批。建议下一批先对 CCR-F0052 确定负例判据：
构建/工具失败必须失败，`wrong` 必须实际运行后按预期失败，意外成功也失败；连同零有效
样例/空结果规则经用户确认后再实施。该策略尚未裁决，其他 R0 项不自动纳入。


## 2026-10-17 收尾确认与提交授权

用户明确要求当前修复满足后续回归需求时闭合提交，并将其他既有修改按阶段分别提交。
据此确认本批既有局部修复结果并授权 F0015 独立提交；不重跑或扩大本批验收，不把原
43项host结果写成真实CPU/guest回归。本节覆盖前文“结果待确认、未提交”的交付时截面。
实际提交号在 REPAIR_AND_REGRESSION 的收尾回执及本地.agent检查点登记。

用户同时确定后续nemu/AM/nanos/navy/RT功能修复必须使用真实产品回归：CPU-tests全集
（正例PASS、明确负例XFAIL），RT update/run后到msh，nanos update/run后验证现有
pal/nterm/nslider三前台F1–F3切换及后台hello。无GUI不能用host stub代替guest执行；
具体统一要求见[后续回归契约](../crp-f0052/README.md#product-regression-contract-20261017)。
