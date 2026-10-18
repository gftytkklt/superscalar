# CRP F0019 — 表达式生成工具

2026-10-18。**Completed；本组结果用户确认/新commit Pending。** 用户“提交，然后继续修复”确认F0052补充并授权分仓提交后执行本单元；am-kernels实际22791cf，root实际f3d0252。旧历史未跟踪项保留，根干净后Start，M2保持；新修复不自动提交。

## 计划与修改范围

复用CRP整体计划/执行规则，单阶段按原版见证→最小修复→有界生成/独立oracle/故障与并发验证→真实NEMU CLI→记录/索引/状态后停止。目标为恢复非空有效表达式生成，保留`gen-expr [数量]`与Make接口，确保工具失败/零有效不能返回成功；只修改`nemu/tools/gen-expr/gen-expr.c`，113增29删，不改求值器、RTL、产品配置或用户日常步骤，不安装。

参考：2026-10-18读取[ICS-PA1.5 表达式求值](https://ysyx.oscc.cc/docs/ics-pa/1.5.html)“如何测试你的代码”，其随机表达式/宿主编译执行oracle思路用于本组。讲义面向无符号32位运算，本地expr使用RV64 word_t且仅32 token；本组生成每个中间值均在[0,INT_MAX]的四则表达式，使两种宽度结果一致并避免宿主C有符号溢出/负值/除零，不修改既有求值语义或声称覆盖全宽溢出。

- 实现递归数字、括号、四则组合；深度最多3、最多29 token，数字0..99，二元子表达式加括号并带空格。生成时的数值仅用于避免下溢、溢出和除零；**输出结果仍取自独立编译执行的C程序**，没有用生成时的数值取代oracle。输出维持`结果 表达式`。
- 严格检查正数量及表示范围，默认仍为1；0、负数、非法文本、溢出数量和多余参数失败。成功返回0意味着完整产出所请求行数。
- 检查源码写入/关闭、编译器退出、oracle读取/读错误/退出与结果格式、stdout写出/flush；失败返回非零，不再continue后静默exit0。oracle空输出、杂质、负值、越域或额外输出均拒绝。
- 使用每进程私有mkdtemp目录，正常及已处理失败路径清理自有文件；每次编译前移除旧可执行文件，防止编译器“成功但没生成新文件”时复用上一表达式结果。部分行已输出后再遇错仍返回非零，消费者必须同时检查exit和请求数量；本工具不承诺输出事务回滚。

生产SHA256：`3985ae67d96492724262abb0b2f5b066f2e30c47a92cd0cf5e6154f340c054bf`。源码快照local/before.c与after.c、repair.patch及实际构建/运行命令可恢复。

## 本次验证与证据

| 验收 | 本次结果 / local入口 |
|---|---|
| 原版精确见证 | before/：请求3，stdout 0行，编译器明确报错但gen-expr exit0。仅将原版两个固定/tmp路径替换为本组目录以隔离，生成/控制流未改；原始源码SHA和替换说明在result.json，不声称该路径副本与原版字节相同 |
| 固定输入与独立结果 | 固定time种子12345仅通过本地LD_PRELOAD注入，不增加生产seed参数；实际编译/执行128条C oracle，Python AST独立核对128/128，四运算均出现，观察最大27 token。相同种子再次生成128条字节一致；默认1条及原Make入口4条与相同序列前缀一致 |
| 生成边界/UB | ASan/UBSan连续生成10,000次通过；3棵强制完整29-token树通过，分别触发乘法越界候选回退、除零候选回退及最大节点加法；不是仅随机未碰到边界 |
| 输入及oracle失败 | 8种非法数量全部非零且无样例；编译失败、空输出、子程序错误退出、杂质、负值、超范围、额外行、短输出/错误退出、第二次未生成新exe共9场景全部拒绝/清理。最后一项保留已输出的首行，但exit1，未把不完整结果当成功 |
| 文件/输出失败 | 注入mkdtemp失败、源码关闭写入/dev/full失败及stdout flush失败，3/3非零，目录无新增残留；io-faults/ |
| 并发隔离 | 两个真实生成进程并行各16条，均exit0、同固定种子输出相同，私有临时目录均清理，未互相复用固定/tmp文件；final/concurrent-* |
| 既有构建入口 | 隔离复制原gen-expr Makefile及同版源码，使用原build.mk make CC=gcc成功；其产物真实生成4条，未改Make选项/目标；consumer/make.log与make-binary.stdout |
| 真实消费者 | 当前native NEMU逐条执行128个`p 表达式`，**128/128与生成oracle结果一致、CLI exit0**，无invalid expr/token超限/ABORT；consumer/cli-input.txt、cli.log及result.json |
| 最终终检 | validation.json **17/17**：测试/生产/Make副本源码一致、默认/Make输出前缀、独立样例/边界/错误/并发/真实CLI、原F0052的648文件清单无漂移、保护的解释器/REF/NPC旧模型及配置SHA不变、无暂存修改 |

命令配方：`python3 local/check.py`、`python3 local/consumer.py`、`python3 local/io-faults.py`、`python3 local/verify.py`；脚本保存实际argv/退出/日志，已有输出目录禁止覆盖，复现须新目录。check.py仅临时替换clock/编译器输出作定向注入，真实样例和CLI不以fake代替；consumer用现成已验收NEMU解释器，未重编/改动产品模拟器。C/AST/真实CLI三方结果分别记录；C编译与子进程的任何失败不会算PASS。

## 影响、限制与留档

本组生成域有意保证与本地32-token/RV64消费者一致：不覆盖全32/64位回绕、负中间值、寄存器/解引用/逻辑运算，也不把全括号表达式通过扩写为无括号优先级已充分测试。极长表达式、所有随机种子、异步杀死生成器后的临时目录清理未验证；未新增全局超时或通用子进程框架。外部gcc仍须在PATH可用；本组没有安装或升级工具。

CPU/RT/nanos启动不调用此生成工具，本轮未机械重跑CPU全集、RT update/msh或nanos三前台；只报告真实受影响消费者CLI。前组NPC/NEMU全集是历史验收，不冒充本次测试。默认NEMU/REF/NPC模型和配置原样保留，根旧NPC模型问题没有因本组自动更新。

一次性测试脚本/注入库/源码副本/日志/二进制仅local保存，不提交测试代码/生成资产；必要文件清单manifest.json为101条SHA文件条目，不是101项测试，正式终检为17项。ignored证据/.agent不随普通commit备份。没有新增长期架构裁决。

累计**35项修复Completed（34已确认提交，本组待确认提交）/84未修完**，含5CQ/F0040Partial。原审阅119项分类及旧完成记录保持；F0026固定栈预算、PAL/F0043/两缺源等不变。root HEADf3d0252，Working tree contains uncommitted CRP code/documentation changes；index空、无运行中动作、未push。报告/records索引/逐项镜像及状态已同步；本组完成后停止，未来仅沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动commit/push/下一组或推进M2。

<a id="approval-submit-20261018"></a>
## 用户确认及提交授权（2026-10-18）

用户“提交，继续”确认本组已报告的生成域/测试/限制并授权提交，然后执行唯一入口宿主内存组一个单元。101条必要文件清单/生产SHA与17项验收无漂移，复用验收，不重跑或重复Completion；实际回执见local/submit-receipt.json及.agent。无push，新组改动不自动提交。
