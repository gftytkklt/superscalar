# CRP F0016 与 NEMU/nanos 性能分析（2026-10-19）

## 本轮整体计划与边界

来源：用户“继续CRP修复，同时做一个当前nemu运行nanos-lite慢的性能分析测试”。Guard：前组F0009已确认提交d28c393，root/index干净；复用既有CRP计划及TASK_QUEUE#crp-next，本轮不推进M2/M3，不提交/push。

本轮单元：F0016启动输入同步修复 + 独立nanos性能诊断，一并交付后停止。

1. 在隔离构建中复现旧实现漏同步kernel/DTB；保持现命令行及DiffTest ABI，把实际装载段的地址/长度/内容在首次执行前送入golden。单镜像/内置镜像保持。交付最小生产修复。
2. 三段独立哨兵、真实golden与最小guest核验；独立检查首条执行前同步范围/内容，漏段/地址错负例必须拒绝。原loader失败检查、native/REF构建及ABI按依赖闭包验证；不运行完整Linux或安装QEMU。
3. 使用现nanos/Navy输入的临时磁盘副本测量固定指令吞吐及真实PAL前台负载；检查配置与构建身份，收集宿主函数画像、guest热点和设备活动，用诊断性消融识别主因。perf不可用时使用已安装工具，不改系统权限。不把诊断副本变化作为生产优化或功能验收。
4. 保存命令、工具/配置/输入/源码身份、退出码及结果；清理可再生产物，更新records索引、逐项状态与.agent，统一报告后停止。完成/用户确认/commit分别记录。

验收：旧问题新鲜拒绝；修复三段/单镜像/内置镜像真实执行通过，负例被检出；性能结果注明wall/CPU、测量开销、运行环境和限制，结论可复现且不凭host原生速度推定解释器应达性能。CPU/RT/NPC/nanos按实际调用闭包解释选测。不修改用户配置/真实ramdisk/日常Make流程，无安装/系统改动；若出现真实新策略再停。

当前状态：F0016 Completed，性能诊断Completed；本轮新结果确认/commit Pending，未开始下一单元。

<a id="implementation-result-20261019"></a>
## F0016 修复结果

**Completed，结果确认/commit Pending。** 生产仅改3文件19增1删：`monitor.c`在成功装载时记录真实段地址/长度，保留原`init_difftest`同步首段，再在进入SDB/执行guest前同步其余段；`dut.c`提取内部`difftest_sync_memory`，header提供关闭DiffTest时的空实现。未改启动参数、Make选项、导出的golden ABI、支持组合或失败语义；未禁用DiffTest。

原问题动态复现：从Git `d28c393`重建native RV64 DEVICE+DIFFTEST，用三段不同内容（firmware 88、kernel 257、DTB 129字节）。审计器首次执行前报告mask=1并拒绝（实际exit255）；绕开审计直接用现有Spike时，在读取kernel哨兵后真实对拍ABORT/exit1。修复后的同一guest读取kernel/DTB首部及末字节，与独立常量比较，Spike真实执行GOOD/exit0。

| 验证 | 实际结果 / 本地证据 |
|---|---|
| 全段输入审计 + Spike执行 | 实际地址80000000/80200000/82200000、长度及所有字节与独立输入文件一致，首次exec前检查；`tests.json`、`fixed-spike.log` |
| 新构建NEMU REF读回 + 执行 | 首次exec前从golden逐段读回所有字节，三段完全一致，guest GOOD/exit0。NPC REF的regcpy有第三个GPR/PC选择参数，**仅夹具显式适配**；不宣称它与NEMU-DUT的Spike接口天然相同。`fixed-ref.log` |
| 判据负例 | 丢firmware、丢kernel、丢DTB、DTB地址+4096，四例均在首次exec前诊断拒绝（实际exit255；夹具调用abort，不把返回码改写为预期信号），不能伪PASS；`drop-*.log`、`wrong-dtb.log` |
| 兼容路径 | 真正单镜像+Spike、内置镜像+Spike、单镜像native、多镜像native均GOOD/exit0；原loader的8个参数/尺寸拒绝保持；`extra-tests.json`、`loader-results.log` |
| 构建 / ABI | 原版DIFF、新版DIFF、新版native、REF隔离构建通过；现有REF ABI检查通过；`builds.json`、`ref-abi.log` |
| 真实nanos | 新native相同配置/原guest执行1亿指令两次，正常到进程初始化，hello789/782条；5亿指令诊断运行hello4307条，无ABORT/BAD/崩溃，按输入的有限`si`后`q`正常exit0。不是guest完成退出或GUI全功能复验 |

本轮只改monitor启动同步路径；CPU语义、CSR、Sv39算法、AM/Navy、调度、RTL和REF导出接口未改。CPU-tests全集、RT/NPC、STA、nanos三前台切换不属于新增受影响闭包，不为补计数重跑；受影响单/多镜像、native启动及真实golden已覆盖。未测完整Linux/大镜像长时启动、QEMU adapter、设备状态恢复、多次同进程init；不从最小guest推定这些能力已验收。

参考背景：[ICS-PA Differential Testing](https://ysyx.oscc.cc/docs/ics-pa/2.4.html)，2026-10-19查阅；实际修复契约以本项目已支持的multi-image命令和队列验收为准。

<a id="performance-result-20261019"></a>
## NEMU运行nanos-lite/PAL的性能分析

**当前瓶颈是guest指令需求叠加Sv39/访存解释成本；本轮没有生产性能优化。** “Linux宿主”不会使被解释的RV64程序直接获得x86原生吞吐：本次约1600–1800万guest指令/秒，同时还在解释后台忙循环、软件音频合成和逐像素写入。

条件：Linux 6.8 x86_64，i9-13980HX，GCC 13.3，`-O2`，RV64 interpreter，128MiB PMEM，800×600 VGA，legacy timer；TRACE/FTRACE/MTRACE/ETRACE/WATCHPOINT/DIFFTEST关闭。沿用当前nanos与Navy ramdisk，PAL前台+hello后台、不注入键盘输入，SDL video/audio=`dummy`。不绑定CPU、不固定频率；温度/调度/共享宿主负载可带来波动。cgroup/CPU/affinity见`perf/identity.json`。这不是窗口桌面延迟或物理音频测试。

最终测量显式设置`NAVY_HOME=local/perf`，NEMU启动日志核对实际磁盘路径为临时副本；副本与真实盘SHA均为`815fca56e386ad16df98941d1a7cace235cc6e92cc166cd781d7ded9d913e7d4`，测试前后保持。初步试跑沿用了会话NAVY_HOME、打开源盘，未产生内容变化；这些条目保留在runs.json但**不列入下表最终副本测量**。PAL/hello符号ELF与ramdisk对应段逐字节SHA一致，避免用另一版源码/ELF解释热点。

| 最终副本测试 | guest指令 | 执行吞吐 | 总wall / user / sys（秒） |
|---|---:|---:|---:|
| 新native，第1次 | 1亿 | 17.361 M/s | 6.121 / 6.065 / 0.057 |
| 新native，第2次 | 1亿 | 17.915 M/s | 5.939 / 5.894 / 0.046 |
| 采样诊断，延长观察 | 5亿 | 16.192 M/s | 31.257 / 31.180 / 0.085 |
| 诊断：跳过宿主SDL绘制 | 1亿 | 16.418 M/s | 6.457 / 6.389 / 0.069 |
| 诊断：device_update每32条才读宿主时间 | 1亿 | 18.427 M/s | 5.784 / 5.735 / 0.050 |

吞吐分母取NEMU原执行区间`g_timer`（不含初始化/进程退出），独立记录总wall及子进程CPU时间；测试副本只在区间结束后打印一次计数。wall≈user+sys，未见大量宿主阻塞等待；关宿主绘制没有可见提速，批量时钟检查只有小幅变化且受波动影响，不能宣称其稳定提升或生产安全。两种诊断都会改变设备呈现/轮询时机，**不作为功能保持或可合入优化**。

### guest负载：前台获得的算力被后台和软件音频显著分摊

5亿指令，每4096条采样一次，按`(satp,pc)`区分地址空间，共122071样本（原计数U态447078167/M态52921833）。只调度PAL与hello，按独立ELF地址/符号范围识别；样本占比估计的是**guest指令**，不是host CPU时间，定周期抽样可能存在偏差。

| 路径 | 占全部guest采样 |
|---|---:|
| 后台hello用户态 | 45.46% |
| 其中hello main的volatile忙循环 | 43.06% |
| PAL中DBOPL软件FM音频合成函数合计 | 27.14% |
| PAL `SDL_UpdateRect` | 10.06% |
| 内核AM `__am_gpu_fbdraw` | 5.09% |

`nanos-lite/src/proc.c:schedule()`让前台与hello交替运行；`navy-apps/tests/hello/hello.c`每10000次volatile递增才打印，没有阻塞/休眠。因此后台“仅打印hello”实际消耗近半指令。PAL仍在guest中运行OPL合成：宿主audio=dummy只去掉实际播放，**不会省掉guest合成计算**。视频路径是guest像素转换、syscall/内核复制和逐像素MMIO，不能把这些成本等同宿主`SDL_RenderPresent`。

首次纹理提交发生在约5000万指令后；100→200次纹理上传间隔约11.54秒。`fb_write`按行sync，纹理提交可能是部分画面，**这些次数不是完整PAL帧数/FPS**。本轮不采集截图、不冒作完整画面或稳定游戏帧率验收。最初1亿与延长5亿的负载占比不同，已保留两份原采样/分析，避免只凭启动窗口下结论。

### host热点：每次取指/访存都重走检查与页表

系统`perf_event_paranoid=4`，`perf stat -e task-clock true`被拒绝；未提权/改系统。最终使用测试副本的SIGPROF/ITIMER_PROF约1ms PC采样，读取进程maps并用本版`nm -S`解析主程序，30884样本；不依赖perf权限。共享库/vDSO按映射归类。此副本同时做guest采样，存在测量扰动；信号与legacy定时器可能偏置中断处理样本，不把采样百分比当精密cycle计数。

| host函数（self PC样本） | 占比 |
|---|---:|
| `rv64_translate` | 19.61% |
| `find_mem_region_range` | 10.53% |
| `decode_exec` | 10.52% |
| `paddr_read` / `mem_read` | 7.44% / 6.72% |
| `rv64_prepare_access` | 5.77% |
| `paddr_try_read_region` / `rv64_try_read` | 3.97% / 2.92% |

列明的翻译/访问准备/内存检查相关函数合计约61%（互斥self样本，不累加调用栈inclusive时间）；当前Sv39无软件TLB，每次翻译都遍历页表，store预检后mark_dirty又走一次翻译，检查后paddr读路径还会重新找区间。`-pg`补充画像在1亿指令下计到约1.57亿次`rv64_translate`、4.01亿次`paddr_try_read_region`和5.29亿次`paddr_read`，支持“重复翻译/检查很多”的判断。**gprof执行降至3.41 M/s，约5倍扰动，不能拿它的速度或百分比当正常性能**；且其初步运行输入源盘内容与最终副本相同，作用仅为辅助调用次数证据。

### 建议的优化顺序与本轮限制

1. 优先评估NEMU软件TLB及取指/普通内存访问快路径，减少重复页表遍历和区间定位；必须保持Sv39权限、A/D、MPRV/SUM/MXR、satp/sfence失效和精确异常，不可简单绕过检查。
2. 另行明确前台响应/后台演示的时间片目标；调整hello的等待/份额有直接收益，但会改变现调度教学行为，本轮未改。
3. 优化PAL音频供给/合成和guest绘图批量搬运；是否允许无音乐、降采样/降低音质须单独决定。不能用静音或禁用音频掩盖性能需求。
4. 宿主时钟调用批量化可以后续评估，当前证据不支持把它或SDL提交当首要瓶颈。

未与同一工作负载的原生PAL、旧Git版本性能作严格对照，不能归因某次CRP造成退化；未测桌面GPU驱动、真实声音、频率固定、其他宿主/guest/长时稳态、Linux guest全启动。本轮只提交（待用户授权）F0016正确性修复及报告，不包含性能实现/新开关/安装。

<a id="reproduction-cleanup-20261019"></a>
## 复现与收尾

本地最小夹具/分析脚本不随修复提交：`build.py`、`test.py/audit.c/guest.S`、`extra-tests.py`、`instrument-measurement.py`、`performance.py`、`sample.h/diagnostics.py/analyze-samples.py`；命令与exit/result见`builds.json`、`tests.json`、`extra-tests.json`、`perf/runs.json/metrics.json`。身份见`input-identity.json`、各纯构建identity、`final-build-identity.json`；`repair.patch`保留未提交修复，`*-source.patch`记录各诊断副本相对生产的精确差异。临时磁盘由现Navy ramdisk复制；原始输入不备份到Git。

在**空的新local子目录**复制这些必要脚本复现，避免覆盖旧结果：从Git d28c393取得源，再应用repair.patch重建修复版；`python3 build.py old-diff native new-diff new-native ref profile`；`python3 instrument-measurement.py native new-native profile`；`python3 diagnostics.py`；准备`perf/build/ramdisk.img`后运行`test.py`/`extra-tests.py`；`python3 performance.py new-native new-native no-render batched-clock`；`CRP_STEPS=500000000 python3 performance.py sample`；`python3 analyze-samples.py`。原版构建脚本定向从d28c393取3个源文件；其他源以当前修复版为准，诊断副本差异可用保留patch校核。所有Make使用`-o compile_git`，不触发构建自动提交；本轮无commit/push。

验证完成后依[CRP清理规则](../workflow/README.md#artifact-cleanup)删除本批镜像/ELF/执行器/构建与生产源副本，保留文字结果/配置/必要最小脚本/patch及逐文件回执；旧清单中的产物哈希是执行时身份，不代表清理后还能查看。`.agent`/local等ignored资料不随普通commit备份。

清理实际完成：主回执`local/cleanup-receipt.json`删除2670文件/169636970逻辑字节（约161.8MiB），工具自身导入缓存另清1文件/13066字节，见`cleanup-tool-cache-receipt.json`；不含tracked删除，无需压缩日志。定向postscan为0；未删主工程或真实Navy输入。清理前21项核验通过，清理后终检另见`validation-final.json`，保留本次文字manifest。删除回执解释本批旧构建identity中可预期缺失，不用已删除执行器重跑已验收测试。

<a id="approval-submit-20261019"></a>
## 用户提交授权补充（2026-10-19）

用户要求补充hello调度比例并“测试无误后提交修改”，随后明确为每100次调度99fg/1hello；该纠正只修改新增调度目标，不撤回提交授权。此前本组已报告结果/限制得到提交确认，技术证据与原完成快照复用；不重做Completion、不重建已清理产物。新增调度作为独立单元验收与提交；本组复用原技术结果。本节随对应代码提交，完整实际SHA及暂存/实际集合另存local/submit-receipt.json及.agent；不push/不开始下一单元。

原manifest为交付完成时文字身份；README增加本提交授权补充是预期新增事实，其余原条目按哈希核验保持。当前状态以本补充及实际提交回执为准，旧Pending为完成时历史截面；ignored/local/.agent不等于获得Git备份。
