# CRP F0064/F0065 — 文件描述符及定位边界（2026-10-20）

## 整体计划与授权

用户“提交后继续”授权F0060提交后执行唯一下一组F0064/F0065。前组实际提交
`7b836855c4aeaacbbf399aa86b3829f79bac599f`，5文件107增3删，暂存/实际blob一致，
Start前root/index干净。复用既有CRP计划、workflow及队列，M2/M3不变，不安装。

1. F0064：read/write/lseek/close在索引前检查固定表fd范围，非法fd返回-1，
   不触发磁盘/设备、不修改offset或用户缓冲；包括零长度调用。
2. F0065：内部fs_lseek偏移参数与sys_lseek既有signed long一致；用不溢出的
   候选位置计算，拒绝负位置/越文件末端/不可表示的long返回值/坏whence，成功
   才更新offset。保留有效负向CUR/END、恰EOF和固定fd的close后仍可复用简化。
   不新增每进程打开表/errno/设备定位能力；真实新策略冲突时先停下裁决。
3. 定向：原fd/负定位及越末端反例，host sanitizer的fd边界/所有公共入口/
   offset与buf/handler哨兵；SET/CUR/END、零文件、LONG_MIN/MAX及失败不发布。
   构建实际nanos并用小型RV64用户payload走真实ecall/syscall，临时磁盘验证
   正常读写、错误/定位状态；旧版分别拒绝两问题，新版通过。默认三前台/hello
   与纯生产内核另验。测试夹具/文件表/磁盘只在隔离副本，不改日常入口/真实盘。
4. 保存源码/配置/输入/构建身份、实际命令/退出码与结果、最小测试源/patch；
   验证/目视后清理本组镜像/构建/截图/生产源副本，更新records/台账/.agent及
   唯一未来入口。host不替代真实guest，按闭包说明CPU/RT/NPC等未测范围。

结束节点：两项组合验收及留档后停止，等待用户确认/commit；本条指令不自动授权
提交新组、push或进入再下一项。计划落档时Active，现已Completed，确认/commit Pending。

## 本轮结果

**F0064、F0065 均 Completed；新结果确认/commit Pending。** 生产仅fs.c/fs.h，
合计26增6删。F0064四入口先检查fd；F0065内部签名用long接收既有signed syscall
偏移，以无符号候选/负数幅值计算避免LONG_MIN取负及正向加法溢出，验证文件范围
和long可表示性后一次发布offset。失败返回-1且保持旧offset，合法负CUR/END、
恰EOF与close后固定fd复用保持。未改公开syscall编号/libos ABI/Make/errno策略。

| 项目 | 本轮证据与结果 |
|---|---|
| F0064原版 | 从Git7b83685取fs.c，read(-1,buf,0)触发ASan heap-buffer-overflow；真实RV64旧内核在该调用处进入ERROR/坏trap。旧内核仅加一次性syscall入口日志，`FS-FD-WITNESS read fd=-1 len=0`位于故障前；未用无关启动失败当本项见证 |
| F0065原版 | host负SET(-1)虽返回-1但offset不再等于5，越末端SET(17)被误接受，两个断言均拒绝；真实旧用户payload在step004检查当前偏移时失败并坏trap/exit1。`unit-results.json`、before-seek-run.log |
| 最终host组合 | ASan/UBSan通过：30个非法fd场景（5种fd×6操作，含read/write零len）、28个定位边界及正常IO/固定fd复用，共129断言；逐场景检查全部offset、buf和handler计数。独立`__int128` oracle核对候选位置，不照抄生产计算；含LONG_MIN/MAX、零文件和不可表示返回值。巨大size只作算术局部探针，不宣称真实大文件能力。`unit.py`及after-all.log；LSan关闭不宣称通过 |
| 真实新用户syscall | 自编小型RV64 freestanding payload走真实ecall→do_syscall→fs接口：四种非法fd、零len、定位失败保持、负向定位、正常读写/EOF/close复用全部通过，FS-GUEST PASS+GOOD TRAP/exit0。夹具`/crp-data`从0123456789abcdef实际变为XY23456789abcdef，核对写盘差异；不是仅检查返回0。原/新payload与内核/磁盘身份见fixtures/appended-files/runs.json |
| 真实默认内核 | 不带观察钩子的当前内核及原NEMU执行器，1亿指令后q/exit0、hello持续进度。新header/实现均同版；原版/新版guest用同一payload、只有旧F0064内核额外入口打印。真实syscall不通过newlib wrapper，不扩写F0076/77/78为已修 |
| 默认三前台 | 52.86秒8观察点：PAL标题/场景，nterm输入qzx得到command not found及新提示符，nslider 0→1→0（返回像素SHA相同），F1/Enter后PAL有画面；hello38→165。contact已目视，PAL返回仍有既有蓝边，如实保留；自有组SIGTERM/实际exit0，非guest正常完成或物理音视频验收。`nanos/result.json`、visual-qa.json |
| 最终身份核对 | 28项预清理核对通过，174份consumer源/header身份保留；原NEMU/默认kernel产物/配置/真实Navy盘和表/loader/proc保持。临时普通盘与源盘同SHA，夹具盘的预期写入位于自有测试区，运行日志核对实际打开路径。`validation-preclean.json`、entry/consumer-source-identity |

夹具修正与限制：最初freestanding编译误用宿主交叉glibc头，缺stubs-lp64.h，已改为
项目既有newlib include，不安装。首次旧F0064系统运行直接内核ERROR而未输出用户FAIL，
原检查器要求用户marker过窄，故未计PASS；保留initial日志/结果，增加旧内核入口
观察并用新版同payload完整PASS区分该错误。期间显式禁用small-data依赖作为夹具
自包含措施，不把早期故障归因为未经证实的gp问题。最终checker分别要求F0064的
准确入口+ERROR+非零/坏trap、F0065的step004+坏trap、新版PASS+GOOD和实际写盘差异；
早期尝试/diagnostic-runs保留，不混入最终4次有效结果或覆盖已删产物的身份。

[ICS-PA sfs](https://ysyx.oscc.cc/docs/ics-pa/3.4.html)于2026-10-20查阅，规定固定
文件大小及偏移不越边界、固定fd简化；讲义size_t示例与项目已存在的RV64 newlib
`off_t`/sys_lseek为signed long分开记录，修复保留现有负向CUR/END能力，不机械
删除负定位。不改变已经用于可选文件探测的open失败返回-1行为。

## 影响与未测

改动调用闭包是nanos fs公共入口、loader和真实用户syscall，故做实际旧/新用户
负例、普通IO及默认三前台回归；CPU-tests/RT/REF接口/NPC RTL不消费该文件表，未
重跑。未测NPC nanos、所有应用/设备/长期/物理音视频、完整Linux或libc errno；
F0066/F0067短缓冲、F0068 framebuffer范围、F0075磁盘失败、F0076/77/78及其他已知
问题继续保留，不能从非法fd零len安全推定所有有效设备零len均安全。无打开状态
跟踪，close有效fd后重置偏移且仍可复用；这是既有简化，不是新POSIX承诺。

累计49已修/70未修完；前47项含F0060已确认提交，本组两项待用户确认/commit。
完成留档后停止，未来仅TASK_QUEUE#crp-next维护F0066/F0067候选范围/必读/验收与
门槛，不自动开始、提交/push或推进M2/M3。

## 再生与清理

local保留unit.py/test.c、guest.c/start.S、prepare.py/run.py、必要修正/观察脚本、
before-fd-observation.patch、repair.patch、配置/源/输入身份与实际命令/exit/result。
从Git7b83685及repair.patch在新的空local目录复现，先unit.py，再prepare.py/run.py
和`python3 nanos-run.local nanos`。prepare已含最终freestanding/newlib/旧FD观察，
不需重做早期夹具失败；初始结果仍保留解释来源。payload只追加到原Navy盘的自有
副本，数据区与表按appended-files再生，run.py每次重置自有16字节文件并检查写后
差异。Navy原盘/表与原native执行器身份见entry-identity，切勿用另一版输入冒充。
构建用git_commit=避开自动提交；未提交修复保留patch，ignored/.agent不由commit备份。

实际验证/目视/结果已完成，随后只清理本组镜像/ELF/构建/截图/生产源副本，删除前
保存路径/类别/哈希，旧identity缺失合并cleanup回执解释；清理数量见下方附记。


实际清理完成：389个本组可再生产物、315283627逻辑字节（约300.7MiB），无tracked删除，剩余产物0。cleanup-plan/receipt保留逐路径/类别/删除前SHA及结果；旧身份的预期缺失按回执解释。原生产盘/默认产物及文字证据未删除。


## 用户确认及提交授权（2026-10-20）

用户“提交，继续”确认本组已报告结果/限制，授权提交后执行唯一F0066/F0067。72条manifest及19项终检保持，复用技术验收及清理，不重跑或重建。仅提交本组可归属6文件，本节随提交落盘；实际SHA/范围见local/submit-receipt.json及.agent。旧Pending为完成时截面，ignored/.agent不由commit备份，不push，不自动提交下一组。
