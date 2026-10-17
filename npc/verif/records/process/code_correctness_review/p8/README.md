# CCR-P8 证据入口与复现

主记录：[P8](../P8.md)、[服务](../SERVICE_RUNTIME.md)、[媒体](../MEDIA_RUNTIME.md)、[应用](../APP_OS_CALLS.md)、[边界](../BOUNDARIES_P8.md)。Final Gate **Partial**：两项保留缺源，未标Completed；P8未提交，P9未Start。

| 文件 | 用途 |
|---|---|
| baseline.json / coverage.before.jsonl.gz / findings.before.json | HEAD679cc16、6,434输入的bytes/mode/link、原coverage和89问题 |
| provenance.json / *-local.diff | 四个嵌套repo当前HEAD/remote/status、tracked byte比较及既有差异；不是上游认证 |
| call-sites.json / app-call-sites.txt | 应用直接调用导航；参数/返回/所有权及间接wrapper解释在APP_OS_CALLS |
| file-review.jsonl / branch-review.jsonl / review-summary.json | 逐文件深度/边界/排除理由/问题，条件责任导航；Unavailable不算已审 |
| findings.json | 新26项完整字段、位置/hash、来源/上下游/回归与限制 |
| probes/ | 原24条；12个编译被ccache只读访问阻断，原样保留 |
| probes-fixed/ | 禁用cache后24条；12生产RV64单元编译、video/rw/timer/close、key与oddmix sanitizer、mixer wrap |
| supplement/ | 27条WAV和应用/media编译，window.cpp头冲突保留；测试同名日志首次碰撞，后112组补齐；两次RWops focused各2命令 |
| app-compile/ | 112单元唯一日志：PAL41/ONS32/Lua35/测试4，全部编译成功；非全产品链接/guest |
| validation.json / manifest.json | Final Gate结构检查与完整未通过原因、最终交付哈希；多数本地文件被git忽略 |

`run_probes.py`/`run_supplement.py`源码可复现隔离单元逻辑，均写新/tmp目录，未调用原Makefile/clone/install。原日志目录保持首次结果；再次执行会更新脚本指定证据目录，长期归档应先复制证据（无需为已通过项重跑）。`run_probes.py`新增rwoverflow分支供focused sanitizer使用；首次普通RWops probe查询tell会把内部负pos重新clamp，未证明安全；补充probe在下一次read前不seek，ASan证实base-1读取。两份结果都保留。

host使用系统libc和NDL受控桩，mixer-wrap/WAV harness直接include生产mixer.c并用gc-sections裁掉无关部分。目标编译使用现有/usr/bin/riscv64-linux-gnu-gcc/g++、本地newlib与Navy头，`CCACHE_DISABLE=1`，未执行目标文件。`app-compile`命令记录每个argv；无需网络/安装。没有保证/tmp二进制永久保存。

`build_review.py`仅从冻结coverage生成P8责任和问题；`finalize_docs.py`仅生成本阶段报告/索引/状态检查点，重跑前应先检查后续工作避免覆盖新阶段。源代码没有修复。缺源恢复后按Guard定向补查，不能用本轮记录代替缺失实现验收。


<a id="p8-waiver-20261017"></a>
## 2026-10-17 授权补充：保存 Partial 后提前进入 P9

用户在已获知 P8 Final Gate 未通过、两项缺源及未提交状态后明确回复：“同意，先提交再执行，那两个缺源暂不解决”。据此接受保存 P8 Partial 交付，授权提交当前 P8 可跟踪修改，并明确豁免 P8 完成/结果确认作为 P9 的前置门槛；先实际提交再启动 P9。fceux 与 oslab0 继续保留缺源/未审，不标 Completed、不标 Excluded；暂缓解决不等于消除缺口。P9 只执行 L01–L09，Final Gate 后停止，不进入 P10。

提交前只读核对 P8 manifest 247 项全部匹配、Git diff 空白检查通过、待提交为五份 README 导航及 p8 九份说明/证据源码。没有重跑已记录测试；原 validation/manifest 和 Partial 检查点保持历史字节。多数报告、JSON、日志及 .agent 仍为本地忽略资料，不 force-add、不修改跟踪策略。实际提交号另附回执。
