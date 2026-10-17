# CCR-P4 证据索引

2026-10-17。[P4审阅与Final Gate](../P4.md)覆盖RV64 NEMU/NPC启动、链接、Context及VME/MPE；120文件、78条件，10问题（5 Confirmed / 2 Robustness / 3 ContractQuestion）。用户明确允许CQ/能力限制留档完成，不批准教学简化。生产源码未修，P5未开始。

| 资产 | 内容 |
|---|---|
| `baseline.json`、`coverage.before.jsonl.gz` | 开始HEAD/工作树、120文件原身份及P3后完整矩阵；`.before`为阶段前本地状态保护副本，不是新Completion |
| `file-review.jsonl`、`branch-review.jsonl`、`source-evidence.json` | 每文件/条件的P4责任、来源hash、边界、问题、分母；P5仍待审 |
| `findings.json` | F0023–F0032完整字段；总台账在上级findings.json/FINDINGS.md |
| `artifact-review.json` | 78个历史.o/.a/.d的ELF头、archive成员或依赖文本；不是当前源码/配置绑定证明 |
| `probe-results.json`、`*.log` | 75条工具/编译/链接/objcopy/host-dummy命令，14个基础/边界ELF与bin hash |
| `supplement-results.json`、`aligned.S` | 16条命令、5个高对齐rodata链接；对应LMA/VMA反例 |
| `gnu11-results.json` | 10个C单元补用项目GNU11/-Wall/-Werror，全部对象字节与初始编译相同 |
| `vme-results.json`、`vme-probe.c` | 真实VME C仅替换2处satp CSR表达式的host观察；失败首轮缺harness halt stub日志另存 |
| `layout.c`、`fixture.S`、`dummy.c` | C/asm布局断言、最小链接输入、未修改dummy API host观察 |
| `validation.json`、`manifest.json` | Final Gate结构/身份/文档检查与证据文件hash；不等于RV64运行PASS |

所有编译/链接/host执行都在`/tmp/ccr-p4-*`，不运行项目make/run/clean，不改原build，不安装/下载/自动commit。未运行guest、NPC仿真或板卡。103条成功命令及1次harness链接失败分开记录；元数据检查另计。

复现需新证据目录，脚本拒覆盖既有正式结果：

```bash
python3 npc/verif/records/process/code_correctness_review/p4/run_probes.py --output /tmp/ccr-p4-replay-new
python3 npc/verif/records/process/code_correctness_review/p4/run_supplement.py --evidence /tmp/ccr-p4-replay-new
python3 npc/verif/records/process/code_correctness_review/p4/check_gnu11.py --evidence /tmp/ccr-p4-replay-new
python3 npc/verif/records/process/code_correctness_review/p4/run_vme_probe.py --output /tmp/ccr-p4-vme-replay-new
```

`build_review.py`为本次人工结论的元数据落盘脚本，不是自动正确性审计器；已有正式结果时拒重写。`validate_p4.py`可在同一阶段HEAD/交付边界下复验；后续提交/阶段变化须作为新检查点，不能重写历史Gate冒充原时刻。

Markdown/JSON/压缩证据及.agent依现有ignore为本地资产；用户已确认P4并授权提交；本次提交包含README、Python、C/S小fixture，确认与提交回执见[P4记录](../P4.md#ccr-p4-approval-commit-20261017)。普通commit不等于完整证据备份。
