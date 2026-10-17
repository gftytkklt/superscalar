# CCR-P6 证据入口

2026-10-17；基线boot_linux `632b843`。[阶段报告](../P6.md)、[OS矩阵](../OS_RUNTIME.md)、[跨层链](../CROSS_LAYER_P6.md)、[覆盖清单](REVIEW_CHECKLIST.md)、[问题明细](findings.json)、[Final Gate](resume-validation.json)。

| 资产 | 用途与限制 |
|---|---|
| baseline.json / coverage.before.jsonl.gz | 70输入身份和P6开始前coverage；保留链接文本/目标字节语义 |
| file-review.jsonl / branch-review.jsonl | 70文件、91条件；六维检查和问题反查，不是动态覆盖率 |
| artifact-review.json / ramdisk-review.json | 49历史/生成接口资产元数据，108文件边界及48 ELF装载输入；不执行镜像，不审用户业务实现 |
| support-sources.json | 既有跨层接口源hash；续作仅确认身份，不据此宣称用户端已审 |
| findings.json | F0057–75，含逐问题契约、严重性理由、现有覆盖及缺口 |
| probe-results.json / supplement-results.json / *.log | 续作前71+22命令与原始退出/输出；3条预期不符保留，见P6报告 |
| *-probe.c / run_probes.py / run_supplement.py | 已有隔离验证配方，当前轮未执行；若未来运行须重新核授权/输入并保留新一轮证据，不覆盖此批 |
| build_review.py / build_findings.py / inspect_assets.py | 中断前生成辅助脚本；再生成可能覆盖续作补充字段，不是当前Final Gate入口 |
| resume-drafts-before.json.gz | 续作前OS/问题/矩阵草稿快照，支持编号与计数勘误追溯 |
| validate_p6.py / resume-validation.json / manifest.json | 只读源/已有日志，检查覆盖、hash、文档/生命周期一致性；输出只写本证据目录，不运行产品/探针 |

本轮验证入口：`python3 npc/verif/records/process/code_correctness_review/p6/validate_p6.py`。只检查已有材料，不建立新实验。报告/JSON/gzip/.agent遵循既有ignore；未擅自提交或改变跟踪规则。
