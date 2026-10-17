# CCR-P3 证据索引

本目录是 2026-10-17 NEMU RV64 运行支撑静态审阅的本地证据；结论、边界和 Final Gate 见 [P3.md](../P3.md)。`coverage.jsonl` 的 P1 行 ID 不变，文件/条件行在本阶段加 `p3_review`；N02 补链保留 P2 状态，另加 `p3_loader_supplement`。

| 证据 | 用途 |
|---|---|
| [source-evidence.json](source-evidence.json) | HEAD、原/现矩阵 SHA、分母、模块深度、源身份漂移、动态状态 |
| [file-review.jsonl](file-review.jsonl) | 2,612 个 P3 文件身份、处置/来源哈希/问题链接；含一条 S06 排除 |
| [branch-review.jsonl](branch-review.jsonl) | 1,183 条 P3 条件/endif 导航和 RV64/边界判定 |
| [n02-loader-supplement.jsonl](n02-loader-supplement.jsonl) | 2 个 P2 文件的 P3 宿主装载责任补链 |
| [findings.json](findings.json) | CCR-F0009–F0022 的位置、SHA、条件、修复/回归与限制 |
| [coverage.before.jsonl.gz](coverage.before.jsonl.gz) | P3 标注前冻结矩阵；防覆盖原 P1/P2 证据 |
| [build_records.py](build_records.py)、[update_coverage.py](update_coverage.py) | 可重放留档生成；只写 CCR 证据，不构建生产代码 |
| [validate_p3.py](validate_p3.py)、[validation.json](validation.json) | Final Gate 结构和来源身份核对，不等于动态行为测试 |

来源边界：S01 的 Spike/kconfig/fixdep 上游代码只核来源、工作树差异和实际 adapter；S03 的历史产物只核身份及生成/消费，不证明与当前源码/flags 配对。P3 未运行 SDL/LLVM/REF/Spike/业务 guest；无安装、下载、系统修改或生产源码改动。
