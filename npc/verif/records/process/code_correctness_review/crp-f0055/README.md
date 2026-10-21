# CRP F0055 — RTC能力声明与日历占位必要分析

> **现行结果**：用户批准两平台最小声明修正，has_rtc=false已实现/验证，F0055 Completed；本批结果确认/commit Pending。日历占位/UPTIME/J4/原rtc_test保持，109+6+2+2；以下Pending内容是批准前历史，最终结果见#implementation-20261021。

## 整体计划（2026-10-21）

用户“提交后继续”确认并实际提交F0030/F0054分析3450275后执行本单元，复用CRP计划/workflow及TASK_QUEUE#crp-next，不推进M2。

范围/目标：NEMU/NPC AM TIMER_CONFIG.has_rtc与TIMER_RTC返回、UPTIME及设备名称RTC的区别；核am-tests rtc_test、RT/Navy/nanos/Linux实际调用和讲义允许的占位范围。原F0055为CQ，先澄清是否标记无墙钟或保留教学占位，不自行新增墙钟源/改NPC时基。

阶段/交付：固定必要源码/八正式资产/ONS差异→定向调用/课程及能力契约复核→真实RV64必要原版见证（NEMU真实IOE/RTC/UPTIME，NPC模块仅同RV64环境的实际函数执行，明确不是NPC RTL验证）→最少方案/用户裁决→验证身份和产物清理、记录/索引/.agent及唯一后续入口。

验收：能力查询、六日历字段、跨1秒后是否改变分别观察；UPTIME增长不冒称墙钟存在。NPC代码在NEMU执行仅检软件字段/查询，不调用CLINT/重判J4时间域，不声称真实NPC板卡。原rtc_test若以受控打印截断观察，须说明测试非正常返回及退出来源。生产未改时不重跑无关CPU/RT/游戏，不以静态消费者未用自动关闭CQ。

停点/人工：能力声明/占位或真正墙钟支持的策略未冻结时分析后裁决，不擅自改has_rtc、RTC接口或日历；安装/系统改动即停。不自动commit本分析/push/下一组/M2。

## 必要分析结论

基线为根3450275（完整commit及14源/八正式资产SHA见local/entry.json）。两平台IOE的TIMER_CONFIG均present=true/has_rtc=true；NEMU timer_rtc固定1900/0/0 00:00:00，NPC固定1970/1/1 00:00:00。NEMU名为RTC的MMIO高字读取锁存get_time()，其值为启动后的时间差；它不是年月日来源。NPC TIMER_UPTIME直接读取CLINT mtime并沿J4已批准相对时基，不能用增长的mtime自动推断出真实历法。本轮不重判J4、不修改RTC设备/CSR time/SBI timer或timebase-frequency。

2026-10-21读取[讲义输入输出/时钟](https://ysyx.oscc.cc/docs/ics-pa/2.5.html)：AM_TIMER_RTC是当前日历，AM_TIMER_UPTIME是经过的微秒；讲义明确允许未实现RTC时rtc_test输出固定占位。此支持不新增墙钟，却未说明has_rtc在占位下必须取何值，故不从“课程正常”自行关闭本CQ。尝试读取的公开AM_Devices页面仅为TODO，未作为能力契约依据；搜索返回的非官方博客未用于裁定。访问时页面不冒充用户当年版本。

### 实际消费者和用户追问：改为false是否影响现有程序

| 消费端 | 当前路径 / 对只改has_rtc的影响 |
|---|---|
| am-tests rtc_test | 不读CONFIG，直接等UPTIME整秒再读六日历字段；只改标志仍按原节奏打印固定日期，不会跳过测试 |
| AM demo aclock | 不查CONFIG，直接用hour/minute/second绘图；保持原占位读取，不使时钟突然拥有真日历。本轮仅静态核调用，没有运行整个图形demo |
| devscan | timer_test只测UPTIME差；不按has_rtc分支 |
| RT BSP | 调度/tick来自UPTIME；native启动有一次被忽略的TIMER_CONFIG读取。当前BSP未用has_rtc或AM_TIMER_RTC决策；不等于对外部RT驱动逐个保证 |
| nanos/Navy | sys_gettimeofday从UPTIME拆秒/微秒，NDL/SDL使用其计时；Navy独立libam包装层本来返回has_rtc=false。其余Navy调用者未发现该标志分支 |
| Linux | 当前计划/已实现MTIMER与CSR time使用独立计数时域，不经AM TIMER_CONFIG。不能从该声明导出真实墙钟，也无本轮新增墙钟需求 |

本轮在以上目录定向查has_rtc/AM_TIMER_RTC，未找到现有程序按该标志分支。**对本次已核调用者，纯声明修改不改变现有运行路径；读取该查询值的程序会观察到true→false，并可能跳过日历功能，这是能力声明变化本身。** 不保证任意外部/未来客户端行为不变，不更改AM native平台本来有真实日期的声明。直接TIMER_RTC读取仍返回原占位，不因为has_rtc=false而panic或删除handler。

用户追问“标记不支持会影响现有程序行为吗？”已按上述证据答复；这次追问不是实施批准，当前生产仍未改。WORKFLOW_POLICY §3要求公开能力语义取舍由用户明确决定，已继续请用户选择最小声明修正或延期，不能因未反对推定批准。

## 原版真实RV64观察

local/run.py在隔离build复制现有AM，按原ARCH=riscv64-nemu image入口构建probe/original两guest。probe用真实NEMU IOE/TIMER_CONFIG/RTC/UPTIME；NPC两个原文件仅通过预处理重命名IOE/timer符号，与NEMU模块同一RV64程序并存，读取**真实NPC软件**CONFIG/RTC函数。NPC CLINT uptime和UART/GPU处理函数未执行，不冒称NPC RTL/板卡/时基回归；其他LUT链接目标由既有NEMU模块满足，未据此验收其NPC设备。

- NEMU经过1100013 us后has_rtc仍1，六字段仍1900/0/0 0:0:0；NPC软件查询has_rtc1、六字段1970/1/1 0:0:0不变。6断言，真实guest GOOD TRAP/exit0。
- 原rtc_test源函数实际运行，输出1、2、3 seconds三行固定1900-0-0 00:00:00。测试包装仅把printf输出转发并在第三行后明确harness halt0，以有界观察替代原无限循环；约3000037 us，GOOD TRAP不是原测试自然返回。
- 两构建/两运行共4命令exit0；原版观察PASS只证明声明/返回/调用，不是F0055已修。正式NEMU、磁盘、内核/RT产物与配置不替换，未安装软件。

## 最小建议与实施门槛

建议只将NEMU/NPC两个TIMER_CONFIG handler的has_rtc置false，present保持true；六日历占位、UPTIME、J4时基、RTC MMIO与原rtc_test不改，不新增日历/错误返回/Make步骤。备选为维持现状延期或另立真正墙钟需求。若用户批准最小范围，同组直接实施两行并用旧/新同版查询对照、保留原rtc_test输出/uptime和源码/资产身份验证；未受影响CPU/RT/Linux/游戏不无故重跑，完整NPC RTL未运行必须单列。分析文档未提交不增加同组实施门槛。


## 分析收尾与当前状态

技术分析Completed，公开能力语义选择Pending；用户追问影响已答复并记录，尚未批准has_rtc=false或延期。F0055仍ContractQuestion/Low/未修，生产零改动，108+7+2+2保持。14必要源码、额外aclock消费端、八正式资产及ONS既有编码diff保持；两构建/两运行已结束，删除前登记196文件/链接685042B并清理隔离AM副本/对象/库/ELF/BIN，0 tracked/正式资产删除。命令/原日志/SHA/最小probe/npc-fields/rtc-original/run配方、参考/验证/清理及manifest保留，Git不等于ignored资产备份。

复现按local/entry.json根3450275与现有正式引擎SHA，在records下新证据目录放置最小配方后执行`python3 "$H/run.py"`，不覆盖本轮日志。原rtc_test三行后harness halt明确保留，NPC仅软件模块执行，不宣传完整NPC或真墙钟通过。生产未改，本轮不重跑无关CPU/RT/游戏。

唯一下一入口TASK_QUEUE#crp-next等待用户选择“按最小范围改false”或“维持现状延期”；答复后沿同单元实施或仅补延期，不把分析文档commit新增为技术前置。当前分析文档未提交，无运行中本组动作，不commit新分析/push/下一组/M2。会话建议：可在当前对话继续；当前证据和待决选项明确。

最终终检13项通过，16份保留证据manifest固定；能力策略仍Pending、无生产修改/新提交，原版行为不计修复验收。

## 用户最小范围批准与实施计划（2026-10-21）

用户在影响答复后明确选择**“按上述最小范围改为 false（推荐）”**，此前能力语义Pending解除；同单元直接实施，不要求分析文档先commit。仅NEMU/NPC两个TIMER_CONFIG handler将has_rtc置false，present保持true；原日历handler、UPTIME、J4时基、原rtc_test、接口/构建流程均保留。

复用原版查询true的真实对照，在新源上以同一RV64 probe验证查询false、六字段仍为原占位、跨1.1秒UPTIME增长及原rtc_test三行不变。NPC模块仅实际软件字段在同RV64环境执行，不冒充RTL；由于无硬件/计时/消费者分支变化，CPU/RT/Linux/完整游戏不额外重跑。归档完整两源diff、正反逐字节核验、正式资产/旧证据身份、最小判据负例及清理后更新状态/索引，结果确认/提交门槛保持，不自动commit/push/下一组/M2。


<a id="implementation-20261021"></a>
## 最小能力声明修正完成（2026-10-21）

用户在实际影响答复后明确批准“按上述最小范围改为 false（推荐）”。本轮只改两个handler的`cfg->has_rtc = false`，两源合计2增2删；`present=true`与LUT/handler均保留，固定RTC读数、UPTIME及NPC J4时基原样。没有增加墙钟、MMIO/公开接口/Make步骤；AM native平台本来具有日期来源，不在修改范围。

其功能是如实暴露“有计时器、无已实现日历RTC”。现程序直接读RTC仍得到原占位；按has_rtc分支的外部/未来程序可能跳过日历，这是批准的能力查询变化，不承诺任意外部程序都保持旧分支。

### 实际验证与影响选择

| 验证 | 结果 / 限制 |
|---|---|
| 原版对照复用 | 分析阶段真实输出两平台has_rtc1，不能满足新false契约；未重跑已完成原版测试。原16份保留证据SHA全保持 |
| 新源真实RV64 | 同一probe/原构建入口，两平台软件查询present1/has_rtc0；6断言，NEMU跨1100025us增长、两组六日历字段仍原占位，GOOD TRAP/exit0。NPC真实软件模块仅符号重命名并在NEMU执行，未执行CLINT/RTL/板卡，不称完整NPC通过 |
| 原rtc_test实际函数 | 新源仍打印1/2/3秒三行固定1900-0-0，逐行与旧源输出相同；约3000066us，第三行后测试printf包装harness halt0/GOOD，原无限循环没有自然返回 |
| 判据 | 旧true结果、删除完成标记、非零退出共三种结果均拒绝；新源四构建/运行命令全部exit0。未声称ASan/host并发或实体墙钟验收 |
| 消费者范围 | rtc_test实际重跑；aclock/RT/nanos/Navy既有调用已静态定位，无按此标志分支，计时实现不变。CPU/RT调度/Linux/完整游戏及完整NPC RTL不因这两处查询值改动重跑，不能把源码影响判断写为它们本轮动态PASS |

### 完整两源diff与身份

根仓ysyx-workbench，旧完整commit `3450275a0bb8413e0fb126ee28825f0116e3fb71`；新为2026-10-21未提交工作树，两文件mode保持。以下全部hunks与实际patch一致，正向应用等于新源、反向恢复旧源，implementation/archive-validation.json保存逐字节核验。

| 路径 | 旧SHA256 | 新SHA256 |
|---|---|---|
| `abstract-machine/am/src/platform/nemu/ioe/ioe.c` | `4563d53e7032d4814904390fb83f3b0ff40cbea70c5a3a5f62e6f4e37137e021` | `fe6db7d5ff95818e869fb80db756e90b7302491463ed9f9de6f69d8579da723e` |
| `abstract-machine/am/src/riscv/npc/ioe.c` | `37d4d057e94713ea4b9a8ba5afa27f819b205b7171f0038af144fe7804da6874` | `af8338a4016d2a0ec5d990919d9408a6391effa48cb66fbaa72bae4869938197` |

```diff
diff --git a/abstract-machine/am/src/platform/nemu/ioe/ioe.c b/abstract-machine/am/src/platform/nemu/ioe/ioe.c
index 7cbfca9779af9a7fc15b9bf892746c6246c8ccbe..38db1347f49f72b8b3f749692b7b38c3b953a562 100755
--- a/abstract-machine/am/src/platform/nemu/ioe/ioe.c
+++ b/abstract-machine/am/src/platform/nemu/ioe/ioe.c
@@ -18,7 +18,7 @@ void __am_disk_config(AM_DISK_CONFIG_T *cfg);
 void __am_disk_status(AM_DISK_STATUS_T *stat);
 void __am_disk_blkio(AM_DISK_BLKIO_T *io);
 
-static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = true; }
+static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = false; }
 static void __am_input_config(AM_INPUT_CONFIG_T *cfg) { cfg->present = true;  }
 static void __am_uart_config(AM_UART_CONFIG_T *cfg)   { cfg->present = false; }
 static void __am_net_config (AM_NET_CONFIG_T *cfg)    { cfg->present = false; }
diff --git a/abstract-machine/am/src/riscv/npc/ioe.c b/abstract-machine/am/src/riscv/npc/ioe.c
index ff79d4b12e64b6e0c75b2a07119e1cf17f4389ed..67329b55d854a8c0e17a2b99db93e4ca73747c65 100755
--- a/abstract-machine/am/src/riscv/npc/ioe.c
+++ b/abstract-machine/am/src/riscv/npc/ioe.c
@@ -15,7 +15,7 @@ void __am_gpu_config(AM_GPU_CONFIG_T *);
 void __am_gpu_status(AM_GPU_STATUS_T *);
 void __am_gpu_fbdraw(AM_GPU_FBDRAW_T *);
 
-static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = true; }
+static void __am_timer_config(AM_TIMER_CONFIG_T *cfg) { cfg->present = true; cfg->has_rtc = false; }
 static void __am_input_config(AM_INPUT_CONFIG_T *cfg) { cfg->present = true; }
 static void __am_uart_config(AM_UART_CONFIG_T *cfg) { cfg->present = true; }
 static void __am_uart_tx(AM_UART_TX_T *tx) { putch(tx->data); }
```

### 清理、恢复与停点

14必要输入仅上述两源变化，其他12源及额外aclock、八正式资产和ONS既有编码diff均保持；原分析manifest16份保持。四同步命令已结束，验证/完整diff正反核验后登记并清理本次196文件/链接687445逻辑字节，0 tracked/正式资产删除。分析阶段另196文件685042B清理保持历史；两个清理回执不合并重写。保留最小配方、probe/rtc-original/npc-fields、实际命令/日志/身份/patch、验证/清理及manifest；已删AM副本/ELF/BIN需从Git+patch重建，不声称仍可直接执行。

复现先按旧根+本报告patch恢复两源和entry正式引擎身份，再在records下新证据目录放implementation最小配方，执行`python3 "$H/run.py"`；不覆盖分析/本轮原日志。不提交一次性夹具/原始证据/.agent，Git不是这些本地资产的备份。

F0055在批准的无日历RTC能力契约内Completed，**结果确认/本轮commit Pending**；不以范围批准推定结果已获确认。原CQ的has_rtc语义现已冻结并实现，不新增墙钟需求；原FINAL_FINDINGS/P10历史不改写。119=109已修+6CRP未修完+2能力移交+2无需实施闭合；六剩余为F0029/F0030/F0054（CQ延期）、F0043/F0073（延期）、F0040（并发Partial）。根HEAD3450275/index空，Working tree contains uncommitted F0055 repair/documentation changes。

唯一下一入口TASK_QUEUE#crp-next：本组结果确认/提交后，另有继续才F0040 C++并发边界/实际需求必要分析一个单元（Planned未Start），不擅自新增同步/异常/析构运行时。当前无运行中动作，不commit/push/下一组/M2。可在当前对话继续，修改范围及恢复证据已收尾。

实施终检19项全部通过，18份本次保留证据manifest固定；原分析16证据保持，不覆盖历史manifest。结果确认/commit仍Pending，无push/下一组/M2。


<a id="submit-20261021"></a>
## 用户确认与本批提交（2026-10-21）

用户“提交，现在已经完成所有待修复问题的决策了吗？”确认此前报告范围并授权累计八路径提交，替代当前“暂不提交”停点。包含F0055两平台has_rtc=false两行修正、两组报告/.gitignore和两索引；F0040无新增生产实现，保持用户批准的Partial延期。既有动态验收与清理直接复用，本轮仅核对源码、56份保留证据、正式资产、原ONS编码差异、完整patch及提交归属，未重跑产品测试。

原119行当前处置逐项分类：109已修、6批准延期/Partial（F0029/F0030/F0040/F0043/F0054/F0073）、2移交Linux（F0031/F0071）、2当前范围无需实施闭合（F0017/F0084），无未分类或当前处置待决项。将来重启延期项仍须明确实现契约；不据此宣称119全修或CRP整体验收完成。本轮只回答决策状态，后续完整范围收尾核对仍Planned、未执行。

本提交包含本附记，实际commit及路径/blob回执保存于`../crp-f0040/local/submit-20261021/`和.agent补充记录；本地忽略资产不因提交而备份。无push，不启动下一单元/M2。
