# CCR-P9 证据索引

[P9报告](../P9.md) / [跨层总览](../CROSS_LAYER_P9.md) / [INTERFACES](../INTERFACES.md)。只执行P9，Final Gate后停；P8 Partial已按用户豁免提交5f88749，两缺源暂缓；P9未commit，P10未Start。

| 证据 | 内容 |
|---|---|
| [baseline.json](baseline.json) / *.before.gz | 授权、HEAD、P8提交前manifest核对、原coverage/interfaces/findings与M2/历史前缀 |
| [chains.json](chains.json) / L01.md–L09.md | 九链×15字段，实际双方、故障传播、旧/新问题、配置与动态限制 |
| [endpoints.json](endpoints.json) / [source-check.json](source-check.json) | 121原独立端点加必要支撑；1951实际身份/链接语义与SHA零漂移 |
| [cross-layer-coverage.jsonl](cross-layer-coverage.jsonl) / [review-summary.json](review-summary.json) | 2082原责任+108补充接点，2190增量；旧40010身份及各阶段事实不改写 |
| [X03_SUPPORT.md](X03_SUPPORT.md) | 14 Linux支撑文件/6冻结条件；代码13+派生pyc1边界 |
| [findings.json](findings.json) | F0116–F0119全部字段，旧115对象保留；F0010实际首次打开顺序限定见L06 |
| [END_TO_END.md](END_TO_END.md) / e2e-attempt1–5/ / faults/ | 四次fixture构建失败、第五次完整target成功、两类实际失败与mtimer成功；命令/版本/源/产物/输入SHA |
| probes/ / probes2/ | 第一次测试桩链接失败保留；第二次原函数REF、uptime、audio三个接点probe，明确不冒充硬件全栈 |
| layout.c / layout-result.json / key-match.json / fsimg-match.json | RV64结构断言、82键序列、108当前fsimg extent比对 |
| [pre-gate.json](pre-gate.json) / [validation.json](validation.json) / [manifest.json](manifest.json) | 审阅Final Gate、保护/状态/导航与交付哈希，不是全部产品正确性认证 |

复现命令/可控替换/动态限制见END_TO_END。生产源只读；临时大产物不承诺长期存在。audit_inputs.py只读检查并写本目录；build_findings.py/build_chains.py/update_coverage.py/finalize_docs.py是本阶段证据生成器，后续阶段不得直接重跑覆盖新记录，finalize有重复完成保护。validate.py可只读重新核对当前阶段（写验证结果）；来源更新后应按Guard补证据，不伪造旧哈希。

多数主报告、JSON、原日志及.agent被既有规则忽略；可跟踪README/测试fixture与脚本不包含全部证据。未force-add、未改变跟踪策略。冷启动需携带本地忽略资料或按源码SHA和配方复现；原P0–P8证据不重写。
