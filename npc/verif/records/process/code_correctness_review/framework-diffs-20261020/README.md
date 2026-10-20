# CRP 框架与 OS 组件修复 diff 留档（2026-10-20）

## 本轮计划

用户要求检查当前 CRP 中所有 newlib 等 OS 组件修复，在各问题验收文档直接补充修改前后 diff，并结合代码语句说明功能实现，完成后提交。
本轮复用 CRP 总体计划及 workflow，只做一个文档补充单元：盘点已实施修复 → 从实际 Git/已验收补丁提取差异 → 在原问题报告追加逐段说明 → 核验 diff、覆盖和链接 → 提交文档后停止。

范围覆盖 newlib/libos、Navy 构建、nanos-lite、AM/klib、RT BSP/集成及 am-kernels 配套修复；包含 F0040 的已实施部分，不将未修项或撤回候选写成已修。NEMU/RTL 自身缺陷不属于 OS 组件；RT 修复依赖的 mret 改动随对应报告说明。保留原报告和验收历史，不执行下一修复单元或推进 M2。

交付为各原报告内可复制的 unified diff、仓库/前后版本、语句与功能/失败语义对应说明，以及本页覆盖表和记录索引。验收要求：diff 与实际修复 commit 或已验收工作树一致；逐文件从旧 blob 应用后等于新 blob；本地补丁相符；所有已修相关问题可沿表定位；当前生产源码不变。本轮不重跑既有产品验收，不将文档检查冒作功能回归。

无需安装或新的策略裁决。用户已明确授权文档补充后提交；根仓库当前 F0083 报告及其索引是本轮相关文档，纳入留档。F0083 嵌套源码的结果确认/代码提交门槛保持，本轮只提交说明文档，不从文档提交推定生产修复获准或启动 F0089。嵌套仓库原执行位差异保留，忽略规则不变，local/.agent 不随普通提交备份。

## 覆盖清单

根仓库实际跟踪 AM/klib、nanos-lite、Navy Makefile/libos 及相关 RT 适配文件；newlib 与 am-kernels 为独立嵌套仓库，根提交不会保存它们的源码。所有下列报告均内嵌完整修复 diff；嵌套路径按各自仓库根解析，恢复时勿直接套到主目录。

| 问题 | 原验收文档（新增 diff 锚点） | 代码仓库 | 修复版本 |
|---|---|---|---|
| F0079/F0080 | [crp-f0079-f0080](../crp-f0079-f0080/README.md#framework-diff-20261020) | `navy-apps/libs/libc` | `5d9ffdb869f3` |
| F0077/F0088 | [crp-f0077-f0078-f0088](../crp-f0077-f0078-f0088/README.md#framework-diff-20261020) | `navy-apps/libs/libc` | `71fac82b2953` |
| F0078 | [crp-f0077-f0078-f0088](../crp-f0077-f0078-f0088/README.md#framework-diff-20261020) | `.` | `23b031327d97` |
| F0081/F0082 | [crp-f0081-f0082](../crp-f0081-f0082/README.md#framework-diff-20261020) | `navy-apps/libs/libc` | `d923fa4be105` |
| F0083 | [crp-f0083](../crp-f0083/README.md#framework-diff-20261020) | `navy-apps/libs/libc` | `WORKTREE（2026-10-20，未提交）` |
| F0085 | [crp-f0085](../crp-f0085/README.md#framework-diff-20261020) | `.` | `b7391768dd6c` |
| F0060 | [crp-f0060](../crp-f0060/README.md#framework-diff-20261020) | `.` | `7b836855c4ae` |
| F0064/F0065 | [crp-f0064-f0065](../crp-f0064-f0065/README.md#framework-diff-20261020) | `.` | `5941586720da` |
| F0066/F0067 | [crp-f0066-f0067](../crp-f0066-f0067/README.md#framework-diff-20261020) | `.` | `07bba7481b19` |
| F0068 | [crp-f0068](../crp-f0068/README.md#framework-diff-20261020) | `.` | `9fb8831caab7` |
| F0069 | [crp-f0069](../crp-f0069/README.md#framework-diff-20261020) | `.` | `e58bbd0a37e4` |
| F0023 | [crp-f0023](../crp-f0023/README.md#framework-diff-20261020) | `.` | `c9be8980d76b` |
| F0024 | [crp-f0024](../crp-f0024/README.md#framework-diff-20261020) | `.` | `fc7835ed53ca` |
| F0025/F0027/F0028 | [crp-f0025-f0027-f0028](../crp-f0025-f0027-f0028/README.md#framework-diff-20261020) | `.` | `f3a5d0cf8c2b` |
| F0037/F0038 | [crp-f0037-f0038](../crp-f0037-f0038/README.md#framework-diff-20261020) | `.` | `0aa1dca5a497` |
| F0033/F0056 | [crp-f0033-f0056](../crp-f0033-f0056/README.md#framework-diff-20261020) | `.` | `5b7a0454f38c` |
| F0034/F0035/F0036 | [crp-f0034-f0035-f0036](../crp-f0034-f0035-f0036/README.md#framework-diff-20261020) | `.` | `71c6cf84f0b5` |
| F0039 | [crp-f0039-f0040](../crp-f0039-f0040/README.md#framework-diff-20261020) | `.` | `b2229ef5cfb1` |
| F0040（部分）/F0044 | [crp-compatibility-20261018](../crp-compatibility-20261018/README.md#framework-diff-20261020) | `.` | `1603f8883715` |
| F0041/F0042 | [crp-f0041-f0042-f0053](../crp-f0041-f0042-f0053/README.md#framework-diff-20261020) | `.` | `e83df62d7b7b` |
| F0053 | [crp-f0041-f0042-f0053](../crp-f0041-f0042-f0053/README.md#framework-diff-20261020) | `am-kernels` | `6dc302a117ae` |
| F0045 | [crp-f0045](../crp-f0045/README.md#framework-diff-20261020) | `.` | `f4e3c0cf840c` |
| F0046/F0048/F0050 | [crp-f0046-f0048-f0050](../crp-f0046-f0048-f0050/README.md#framework-diff-20261020) | `.` | `e9a71f3cd3d1` |
| F0049 | [crp-f0049](../crp-f0049/README.md#framework-diff-20261020) | `.` | `d9a3d423928b` |
| F0051 | [crp-f0051](../crp-f0051/README.md#framework-diff-20261020) | `.` | `4ab9f3f04c12` |
| F0052 | [crp-f0052](../crp-f0052/README.md#framework-diff-20261020) | `am-kernels` | `c1ba0bb884ea` |
| F0052（终态补充） | [crp-f0052-ref-terminal](../crp-f0052-ref-terminal/README.md#framework-diff-20261020) | `am-kernels` | `22791cfe514a` |

未实施的 F0057/F0058/F0059/F0061/F0062/F0063、F0070～F0076、F0084/F0086/F0087/F0089 等不产生虚构 diff；F0040 仅列已经实施的串行 ABI 部分。无关 NEMU/RTL 缺陷、独立性能/99:1 调度需求不在此次问题修复盘点内。修复计数仍为 60 已修/59 未修完。

## 本轮完成与验证

**文档补充 Completed，按本轮授权提交文档；未新增生产代码修改或功能验收。** 共 25 份原验收报告、41 个稳定问题 ID（40 个已修及 F0040 已实施部分）、48 份逐文件 diff；F0052 首次修复与终态补充分别保存，同报告跨仓库的修复分别标注。

- 48/48 内嵌 diff 从所列旧版本正向应用后逐字节等于对应新版本；反向应用还原旧版本，48/48 与原验收目录保存的补丁相符。F0051 特别校验重建旧文件 SHA256 等于当时 baseline，避免把首次跟踪误写成从空文件新增功能。
- 41 个 ID 与当前逐项状态表中 OS/运行时/适配层范围的“已修/部分修复”集合一致；本轮报告/盘点互链与显式锚点检查通过。修改说明按原问题分工复核，保留 F0040 Partial、F0043 未修、旧 memory 未复现误编译、实际 open 内核能力等限制。
- 当前生产文件内容身份保持；newlib 仍仅 F0083 setenv_r.c 内容未提交，HEAD d923fa4，既有执行位差异不纳入；am-kernels HEAD 22791cf 保持。所有源码 diff 以文本内嵌，未强行把整个框架库加入根跟踪。
- 普通 `git diff --check` 会把内嵌 unified diff 的空上下文行、历史删除行空格及上下文前缀加 Makefile tab 报为空白告警。逐条定位确认所有这些告警均在原样 diff 代码块中；块外新增说明无此告警。为保证补丁可复制应用，保留原字节，不对证据做 rstrip/空格转 tab；未更改 Git 空白策略。
- 本轮只做文档/源码差异验证，复用各报告已有功能验收；没有重新运行 CPU/RT/nanos 或宣称新通过结果。临时正反应用目录自动清理，未创建构建/镜像/截图。

核验细目及本轮工具保留于 local/inventory.json、validation.json、source-identity.json、verify-docs.py；它们是本地辅助，不代替正文中已提交的 diff、版本和说明。原报告追加使旧 manifest 的 README 哈希预期变化，历史 manifest 保持原样，本次变化由该附记解释。local/.agent 仍不随根提交备份。

## 提交边界与后续

本批根提交包含上述 25 份报告、这份盘点记录及其局部忽略、process/repair-status 索引，以及原已完成 F0083 的相关报告/局部忽略和索引记录。用户授权是“完成所有相关说明文档补充以后提交”，本次按文档范围提交；F0083 生产源码没有提交，结果确认/嵌套代码提交仍 Pending，不能用根文档提交解除该门槛。原报告中的未提交描述属于当时截面，以本段和本地实际提交回执为最新文档归属说明。

实际根 commit、暂存路径及提交后检查记 local/submit-receipt.json 和 .agent 补充回执；不为回填本次自身 SHA 再制造一轮文档 commit。下一入口仍为 TASK_QUEUE#crp-next：先处理 F0083 代码确认/提交门槛，F0089 未开始，M2 保持。本轮提交后停止，不 push。
