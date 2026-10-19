# nanos前台/hello调度99:1与提交收尾（2026-10-19）

## 本轮计划与用户来源

用户先要求“再做一个修改…测试无误后提交修改”，随后明确纠正：“不是hello的打印频率，是hello的调度频率…100次调度里，只有一次真正切换到hello”。最新澄清优先，原测试后提交授权保留。上一中断轮只做只读核对，未改hello.c、未启动构建/测试；Guard：HEAD d28c393，F0016和宿主优化未提交范围与Session/状态一致，index空，无状态冲突。

本轮一个单元：只在FG_PROCESS模式将每100次schedule选择改为99次fg、1次hello（第100次选hello，随后回fg），保留所有进程上下文保存、F1/F2/F3切前台、hello原10000计数打印阈值和其他配置分支。不按原50%份额“再除100”实现为0.5%，以用户明确1/100调度槽为准；不新增参数/日常步骤。

执行/交付：
1. 修改proc.c并用实际生产schedule函数做确定性测试：启动、多个100调度窗口、当前前台重复选择、hello后返回、F键更换指向与边界；非FG分支保持旧逻辑。
2. 重建实际nanos内核与native NEMU，保留Navy/真实ramdisk不变。用隔离副本内核加一次性计数诊断，验证真实timer/yield事件的每100次99/1；真实三前台/后台hello进度/上下文切换验收，纯生产内核另做启动/持续进度检查。受影响调用闭包是nanos调度，不因源码小而只做host夹具；CPU/RT/NPC RTL不受该kernel模式变化影响，不重复此前已验收底层矩阵。
3. 保存实际命令/退出码、源/二进制/输入身份、目视结果、必要patch，清理本批验证镜像/截图/编译副本，更新records索引及状态。F0016/宿主优化复用已完成验收与清理回执，只补新用户确认及提交事实，不重做原Completion。
4. 核对提交范围后提交本轮以及此前已报告的F0016/宿主优化及对应报告/索引；按修改原因组织提交，临时脚本/产物留local。提交后记录实际SHA/暂存集合并停止，不push、不启动F0018或M2/M3。

验收：确定性窗口严格99/1、每100次真实切入hello一次，非hello槽使用当前fg而非旧指向，prev保存正确；真实guest中调度计数与三前台/hello均有效，未改hello打印阈值/盘内容。无安装或系统改动事项。当前Completed，测试已通过；用户已授权提交，实际回执见本文收尾。

## 实施与验证结果

**Completed；用户已预授权测试通过后提交。** 生产只新增`nanos-lite/src/proc.c`的12增4删；FG_PROCESS的静态计数器从0开始，第1–99次选择当时的fg_pcb，第100次选择pcb[3]/hello并归零，第101次回到当前fg。`current->cp = prev`及原上下文返回保持；F键更新后的fg在非hello槽即时采用。非FG编译分支保留原表达式。未改Navy hello.c的10000打印计数阈值、打印文本、输入文件或时钟配置。

| 验证 | 实际结果 |
|---|---|
| 实际生产schedule函数的确定性执行 | 50000次调用：49500次fg、500次hello、500次真正切入hello；每个连续100调用滑动窗口都只有1次hello。覆盖启动、前台重复选择、hello返回、F键指向变化（含99/100边界）、prev保存与返回指针；非FG另50000次验证旧选择逻辑保持。`unit-results.json` |
| 实际内核调度事件 | 只在隔离内核加入计数输出，不改选择逻辑；真实NEMU运行观测**31个完整100调度窗口**，每个窗口均99fg/1hello且真实切入hello恰好1次。累计total3100、fg3069、hello31、switches31。`schedule-results.json`及`nanos/guest.log` |
| 三前台与后台 | 约52.86秒、8观察点：PAL有场景/标题图；nterm输入qzx后command not found与新提示符；nslider 0→1→同0（SHA相同）；返回PAL/Enter后有画面；hello39→168持续进度。已目视contact图，`nanos/visual-qa.json`留文字与SHA；观察后自有组SIGTERM，实际exit0，非guest程序正常完成声明 |
| 纯生产内核 | 不含SCHED诊断的主工程新nanos内核执行3亿指令后q，**exit0、约14.00秒、43条后台hello**，初始化/持续进度正常，无BAD/ABORT；不以打印条数代替调度比例判据。`production-result.json` |
| 实际构建与输入身份 | 主工程NEMU native/nanos image及隔离诊断内核均成功，均使用同一生产调度代码；默认配置保持。真实Navy ramdisk和hello.c SHA与开始时相同；主工程NEMU/nanos构建输出按本轮测试要求已刷新。`builds.json/final-identity.json` |

host夹具只检验调度选择/指针状态，不替代真实guest；guest计数来自实际timer/yield入口共用的schedule，不是打印次数换算。纯生产内核另行验证避免只验带探针的版本。1%是**调度选择次数比例**，不是忙闲状态下严格墙钟CPU时间比例；没有改timer频率或许诺完整游戏FPS。

本轮改动只属于nanos FG_PROCESS模式调度策略。CPU/RT/NEMU执行语义/NPC RTL未增加改动，复用上一轮已完成的双CPU/RT/宿主访存底层验收，不重造已清理产物；未运行NPC nanos、其他内核调度模式的完整系统、物理音视频或长期压力，不宣称这些配置全验收。其他模式只验证选择逻辑未变，既有独立问题不在本轮扩展。

## 再生与提交边界

local保留`unit.py`（直接include对应Git版生产proc.c）、`prepare.py`（隔离nanos/AM及原Navy临时副本）、`diagnostic.patch`、`nanos-run.local/observe_sdl.c`、实际命令/结果/源码与配置身份、`scheduler.patch`。重建先按原NEMU/nanos Make入口并使用`-o compile_git`/`git_commit=`避免自动提交；再在空新local目录运行unit/prepare/真实观察脚本。纯生产验证argv与输入保存在production-result.json；源盘/guest依final-identity从主工程现输入或原配方取得，不备份大镜像。

当前授权覆盖已报告的F0016多镜像同步、宿主访存优化和本轮99:1调度，按修改原因分3次提交，原技术验收/清理回执复用。本次新结果为用户条件预授权下由agent验证，不冒作用户逐项人工复核。提交前核对每批暂存集合/源码身份，实际提交SHA及完整文件集合见local/submit-receipt.json和.agent回执；不提交local一次性测试、编译/截图/镜像产物。不push，不开始F0018/M2/M3。

验证完成后定向清理239个本批临时镜像/截图/编译和生产源码副本，共164930816逻辑字节（约157.3MiB），无tracked删除；postscan为0。回执local/cleanup-receipt.json解释当时identity中的预期缺失，截图已先目视留文字；保留本轮源码patch/配置/必要脚本和实际结果。467项提交前证据核对（含前两组文字manifest条目，非新guest用例数）通过；不重建前两组已清理产物。主工程新NEMU/nanos执行器与镜像不在本记录树清理范围，Navy盘不变；ignored资产不由普通commit备份。


## 2026-10-20 接续状态勘误

本组已实际确认/提交：F0016 `de7e3be`、宿主优化 `a52ca9e`、调度 `7e0c97e`。
本文旧 Pending 是交付时截面；涉及“下一 F0018 / 不启动 F0018”的未来文字误选了
已于 2026-10-18 确认提交 `37b3195` 的任务，并不表示重新打开。技术验收不重跑、
历史事实不覆盖；见[勘误](../crp-f0069/README.md)，当前只沿 TASK_QUEUE#crp-next。
