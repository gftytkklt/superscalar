# CCR-P2 证据索引

2026-10-17。权威结论：[P2](../P2.md)、[问题台账](../FINDINGS.md)。本目录不包含生产代码修复。

| 资产 | 用途 |
|---|---|
| [baseline.json](baseline.json) | 开始时HEAD/Git状态、29个P2源与P1哈希对应 |
| [coverage.before.jsonl](coverage.before.jsonl) | 更新前P1矩阵完整字节；保持原ID/哈希可比 |
| [file-review.json](file-review.json) | 29个文件的P2范围、检查维度、证据/问题连接 |
| [branch-review.jsonl](branch-review.jsonl) | 166个条件导航逐行判定；含非RV64不适用、P3边界，不等于166条动态测试 |
| [repro.c](repro.c) / [run_repro.py](run_repro.py) | 原源码隔离CPU诊断；不调用项目make，不修改原配置/源码；新版默认新输出目录、防覆盖 |
| [repro-results.json](repro-results.json) | 原始19条命令、退出码、工作目录、输入/二进制哈希；各label.log完整输出 |
| [supplement-results.json](supplement-results.json) | DEVICE=n编译/INV末尾补充；nodevice-*.log |
| [validation.json](validation.json) | P2 Final Gate结构/链接/身份/保护验证与统计；不代表缺陷已修 |
| [manifest.json](manifest.json) | 当前交付资产哈希，供恢复与复核 |

关键日志：addiw/addw/subw/mul/mulw（F0001）、high-bare/high-pt（F0002）、jal/jalr/branch（F0003）、unaligned（F0004）、malloc-compile（F0005）、fencei（F0006）、nodevice-inv-end（F0007）。sllw为GNU/C标准差异证据，不另计当前GCC缺陷；F0008仅静态证据。exit0可能表示错误行为成功复现，非正确性PASS。

实际副本`/tmp/ccr-p2-ca_2djl2`；回收后可运行runner创建新副本。来源哈希须仍匹配；旧binary/原build不是此证据。当前源码测试配置为RV64/native/GARRAY/GCC-O2，另有UBSan/MALLOC编译/DEVICE=n受控变体；设备/时钟stub限制见P2。日志/JSON/矩阵及非README技术Markdown仍ignored（本README、C/Python辅助程序可跟踪），普通commit不备份全部资料。
