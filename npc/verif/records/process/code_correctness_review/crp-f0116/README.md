# CRP F0116 — REF 显式中断注入写回 trap PC

2026-10-20。用户“提交后继续”确认F0112并授权分仓提交后执行本单元；前组root `12be663fdc8178a3d97815b70a09ec89a3e02c57` / PAL `a744ceedd5797135d045fcc2e36cfe3fda4740c0`已提交。本单元不授权新commit/push，不推进M2/M3。

## 计划、边界与验收

复用CCR/CRP整体计划及workflow，独立一个单元：只将`nemu/src/cpu/difftest/ref.c`中`isa_raise_intr(NO, cpu.pc)`返回值写回`cpu.pc`，与现行cpu-exec中断轮询一致。保持既有显式注入的cause透传及CSR/priv处理、void导出和33字PC/GPR包，不新增NPC中断调用或CSR同步协议。无需安装，无新契约裁决。

1. 核对F0116/P9 L08、现行RV64 trap/委托/vector和F0014/F0023/F0003依赖，保存原源码/配置/正式产物身份，原版反例见证。
2. 最小修复；host真实ref/intr源码定向验证M/S/U来源、委托/不委托、direct/vectored、中断及同步cause；比较PC/CSR/priv/GPR。
3. 复用`nemu/tests/m1_p9_ref.py`隔离构建真实RV64 SHARE/DEVICE=n/GARRAY REF，动态加载原导出，用真实guest CSR设置/特权返回、显式注入后执行首条handler及CSR读回；核对原33字ABI与普通执行。按依赖选择消费者，不将NPC未调用的注入接口冒充当前NPC IRQ验证。
4. 最终源码/构建/执行身份、完整diff正反重建、判据及清理核对，records/索引/.agent留档；完成后停止等待用户确认/提交，不自动进入下一组。

参考（2026-10-20读取）：[ICS-PA基础设施(2)](https://ysyx.oscc.cc/docs/ics-pa/2.4.html)的difftest接口背景；[RISC-V machine规范](https://docs.riscv.org/reference/isa/v20260120/priv/machine.html)的mtvec及委托规则。显式注入已由调用者决定trap，保持原函数不重新查询MIE/MIP的契约。同步cause只校对既有透传/helper行为，不把导出扩成新的异常API。

## 实现与结果

F0116 **Completed，结果确认/本轮修复commit Pending**。生产仅`ref.c`一行1增1删：`cpu.pc = isa_raise_intr(NO, cpu.pc);`。右侧在赋值前取得被中断PC，现行RV64 helper保存epc、cause/tval和status/priv，并返回按委托及tvec mode计算的入口；随后写回PC。普通`cpu-exec.c`中断轮询已有同样消费方式。未修改共享trap helper、mtvec前递、CTE/mscratch、PC/GPR包或其他导出；既有同步cause透传也保持。

F0014的完整内存范围/64位地址接口保持；F0023属于AM CTE栈约定，此处不替换其trap汇编/Context；F0003既有NEMU异常向量及NPC精确提交链路未改。当前NPC只dlsym/assert `difftest_raise_intr`，没有实际调用，NEMU DUT侧亦只解析符号；显式注入是调用者已经决定的trap，不新增MIE/MIP轮询或DUT中断同步能力。

| 验证 | 本次结果 |
|---|---|
| 原版真实REF见证 | 同配方构建原版、实际dlopen：从M态PC `80000080` 注入高位interrupt+7，目标`80001000`，PC仍`80000080`；再exec1实际错误路径marker为258（+2）。随后仅用原33字包改PC到handler的CSR读取段，读回mepc=`80000080`、mcause=`8000000000000007`、tval=0，证实CSR已更新而PC未转向；不将该人工转PC当作修复成功。local/real-before/00.log |
| host真实源 | 普通O2、ASan+UBSan各36/36；真实ref.c及RV64 intr.c，M/S/U来源×委托/不委托×direct/vectored×IRQ5/IRQ9/同步9，交错IE开/关。独立期望核对PC/priv/全部18 CSR/32 GPR，检查未选中trap bank保持。局部链接gc去除未调用的memcpy/exec等，不stub trap算法；host仅验证注入状态，不冒充执行handler。local/host-results.json及两log |
| 真实共享REF执行 | final 37/37：上述36场景加M态IRQ7。用正式memcpy/regcpy写RV64指令及寄存器，真实CSR写指令和mret进入M/S/U；无私有CPU结构访问或测试导出。注入后先核对PC和32 GPR不变，再exec1，实际handler首条addi将marker 256→257，所有其他GPR及PC精确匹配；再执行四条CSR读指令，核对所选bank epc/cause/tval/status及PC、包前后哨兵。local/real-final-results.json/real-final/ |
| 旧版判据负例 | 同一最终PC判据运行旧REF，在第一例U→M即拒绝旧PC（子进程exit1），未当作PASS。首次负例外层核对脚本把非委托目标误写为SBASE，已按实际MBASE纠正；产品负例日志保留，最终37例重新生成并通过。local/negative-original*、negative-control.json |
| 真实构建及ABI | 复用M1-P9隔离builder，前后配置完全同版：RV64/SHARE/DEVICE=n/GARRAY，DYN及六导出通过；`--abi`原33字选择复制/前后哨兵、五内存域两端、flash真实3条指令及time=0通过。未调用--install。local/{before,final}-ref及abi.log |
| 身份/归档 | 19项preclean通过；97个当前源码/配置输入身份、前后REF/归一化config/header身份落盘；最终唯一生产变更精确一行，完整diff正反逐字节恢复通过。正式native config/generated headers/interpreter、默认REF、默认NPC和其他依赖源无漂移。local/identity.json、validation-preclean.json |

真实执行覆盖的是宿主共享库内的RV64解释器与实际指令/特权/CSR链路，不是将REF本身交叉编译成RV64 ELF。host与真实REF均通过相同36状态组合，额外M IRQ7沿原反例；不声称穷尽所有cause/CSR/异常优先级或异步竞态。IE关闭场景仍显式注入，确认未意外加上查询门槛。

## 回归选择、限制与复现

只改变显式注入入口，当前NPC/NEMU DUT均无调用点；native NEMU、CPU-tests、RT/NPC及nanos运行路径不经过此入口，故本轮不重跑这些消费者，也未运行真实NPC IRQ。通过新REF普通执行及原完整ABI检查守护同一动态库接口。未重建NPC、未测试S态DUT/CSR对拍/实际定时IRQ同步，不以本轮解除M3/M6范围。默认REF仍为原正式产物，未覆盖；本次新库只在隔离路径验收，收尾后按清理契约删除，可按源码重建。

精确构建/执行日志及命令保留本目录local；测试源、一次性runner和生成配置只保留本地，不加入生产接口或用户日常Make流程。复现时在工作区根设置`H=npc/verif/records/process/code_correctness_review/crp-f0116/local`：

```sh
python3 "$H/build.py" before
python3 "$H/real.py" before "$H/before-ref/ref.so"
python3 "$H/build.py" final
python3 "$H/run-host.py"
python3 "$H/real.py" final "$H/final-ref/ref.so"
python3 nemu/tests/m1_p9_ref.py --abi "$H/final-ref/ref.so"
python3 "$H/verify.py"
```

before配方从下述完整旧commit重建原ref.c，其他输入沿identity；本轮最初直接调用相同M1-P9 builder构建before，后续保留的build.py提供隔离旧源重建。最终保留build.py/run-host.py已实际执行后重跑同版37/ABI/preclean。原版应仅用before模式观察缺陷；final模式喂旧库是预期失败的判据负例，先保存结果并恢复最终记录。归档初尝试把临时目录置于工作区子目录，git apply受父仓前缀影响未通过；改为仓外`/tmp`隔离临时目录后正反核验通过。生产行为与源码不受这些夹具修正影响。

## 完整修复diff及版本

根仓`ysyx-workbench`，路径`nemu/src/cpu/difftest/ref.c`。旧完整commit `12be663fdc8178a3d97815b70a09ec89a3e02c57`；新为2026-10-20未提交工作树。Git mode保持100755。

- 旧源SHA256：`4b3f5f1dafcaf3580b2bc5c5b155d934f94645cf78cbb64742f7232e91872d23`。
- 新源SHA256：`50ea29771810d6ffa04e8197b67d125a230e226087030f9c16f951d2ab0ccf21`。
- 最终验收REF SHA256：`322892ee5581dddd6e7f10fa940d51625f59046871e6b3d7867d64ee60b302e7`；二进制收尾后删除，哈希只标识当时验收产物。

```diff
diff --git a/nemu/src/cpu/difftest/ref.c b/nemu/src/cpu/difftest/ref.c
index f33ce41420106025bede5994a149125fe10211b8..e739abaa32755e9c941a1a590b1d66f9da2d2fb1 100755
--- a/nemu/src/cpu/difftest/ref.c
+++ b/nemu/src/cpu/difftest/ref.c
@@ -99,7 +99,7 @@ __EXPORT void difftest_exec(uint64_t n) {
 
 __EXPORT void difftest_raise_intr(word_t NO) {
   //assert(0);
-  isa_raise_intr(NO, cpu.pc);
+  cpu.pc = isa_raise_intr(NO, cpu.pc);
 }
 
 __EXPORT void difftest_ref_display() {
```

以上内嵌diff等于实际完整生产差异；旧源从明确Git版本取回，正向应用等于新源、反向恢复旧源。原FINAL_FINDINGS/P9为历史审阅截面不重写，现行状态由本报告及repair-status维护。

## 清理与完成停点

必要验证/归档完成、所有本组构建和执行已结束后，按local/cleanup-plan及receipt删除4份可再生ELF/共享库，共235576逻辑字节、0 tracked删除，无截图或镜像留存。97输入身份/配置、构建日志、host及真实REF原始输出/退出码、必要测试源、完整补丁/本报告保留；identity所记before/final REF及host binary预期缺失，以cleanup回执解释，不声称仍可直接运行。生产源/正式默认产物未删除。

累计92已修/27未修完（含5CQ与F0040 Partial）；前91已确认提交，本项Completed、确认及修复commit Pending。Working tree contains uncommitted F0116 repair/documentation changes，root HEAD仍为前组12be663，index空；PAL原差异保留。本轮不自动提交新改动/不push/M2，停等用户确认；未来只沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)。本地ignored证据及.agent不由普通commit备份。

最终终检122项全部通过，79份保留身份及2条内嵌原样diff空白已逐条核对；local/final-validation.json、manifest.json、whitespace-review.json为入口。此为本单元收尾事实，不新增执行授权或重复Completion。


<a id="submit-20261020"></a>
## 用户确认与提交（2026-10-20）

用户再次“提交后继续”确认本组已报告范围，授权精确提交后执行F0119一个单元。提交前79份保留身份/生产patch无漂移，复用122终检及原host/真实REF/ABI验收与清理，不重跑动态测试或重复Completion。提交仅生产ref.c一行、本报告/.gitignore及两个索引；实际root提交以local/submit-receipt.json及.agent回执为准，不预记成功。本附记解释旧manifest的报告哈希变化，旧技术证据不改写；92已修均获确认，27未修完，不push/M2，不恢复旧连续提交授权。

可在当前对话继续：下一项同属REF接口，范围/依赖及恢复资料明确。忽略的local/.agent仍不由commit备份。
