# CRP F0119 — NPC 与 REF 初始化函数签名一致

2026-10-20。用户再次“提交后继续”确认F0116并授权提交后执行F0119一个单元；前组实际提交`f5b9973412e7c466cc5111dcf1f10c8759100c49`。本单元不授权新commit/push，不推进M2/M3。

## 计划、范围及验收

沿CCR/CRP整体计划及唯一入口，只改`npc/csrc/util/difftest.cpp`中REF init指针/解析为`void (*)(int)`并显式传0，匹配现有`nemu/src/cpu/difftest/ref.c`的`void difftest_init(int port)`；现port仅printf，无网络/端口分配功能。不新增Make选项、版本协议或公共ABI，其他memcpy/regcpy/exec/skip保持。无需安装，无未决策略。

1. 核对P9 L08/F0119及现双方源码，记录HEAD/默认产物和配置/已有nested差异；原版用确定性类型契约编译见证，不断言UB调用的随机port。
2. 最小两行修复。实际NPC difftest源码配真实difftest.h做host链接，动态库哨兵检查int参数0与init→memcpy→regcpy、既有包/方向/PC、step及skip；真实REF动态加载验证显式0及原33字ABI。
3. 隔离构建同版完整SoC NPC DIFF=1与REF，用现标准CPU-tests构建/运行全集，严格核主终态和difftest，不只看exit0。按影响选择消费者并披露未测范围；不替换默认产物/配置。
4. 完整diff正反、最终源码/模型/输入身份、必要清理及records/.agent留档后停止，等确认/提交，不串行下一组。

参考：[ICS-PA基础设施(2)](https://ysyx.oscc.cc/docs/ics-pa/2.4.html)（2026-10-20读取）的difftest初始化/动态加载顺序。讲义示例为无参init；本地实际REF导出有int port，故以本地生产双方匹配为准，不将讲义泛型或Spike不同regcpy ABI套入NPC路径。现有M1-P9测试也显式`init(0)`，沿此确定值。

## 实现与验收结果

F0119 **Completed，结果确认/本轮commit Pending**。`npc/csrc/util/difftest.cpp`只有两行功能修复，并补齐文件末尾换行（实际diff 3增3删，Git mode100755保持）：

- `void(*nemu_difftest_init)(int) = (void (*)(int))dlsym(...)`同时统一局部变量类型及解析后的调用类型；仍在同一位置检查符号非NULL。
- `nemu_difftest_init(0)`提供明确int实参，符合实际REF `void difftest_init(int port)`；该函数仍只打印日志。无新增端口选项或连接动作。

保留init→整段flash copy→33字GPR/PC同步顺序、memcpy的uint64/size_t/bool、regcpy的三参/选择复制，以及exec/step/skip；不改REF初始化/复位行为、CSR/priv包或NEMU DUT→Spike的不同二参regcpy契约。F0116写回注入PC保持，不添加NPC IRQ调用。

| 验证 | 本次结果与证据 |
|---|---|
| 旧类型确定性见证 | 在实际NPC源码副本的局部声明后插入仅测试用`static_assert(is_same<decltype(nemu_difftest_init), void (*)(int)>)`，GCC/Clang两版均正确拒绝原无参类型；最终源码同测试均编译通过。不是宣称未加此断言的原生产源码不能编译。local/{before,final}-type-*.log |
| 旧动态调用见证 | 实际旧NPC difftest源码与声明int的测试DSO均由Clang `-fsanitize=function,undefined -fno-sanitize-recover=all`构建，旧调用在41行明确报告incorrect function type并exit1；不根据寄存器残值猜测旧port值，也未运行旧普通构建来断言UB表现。local/before-san.log |
| 最终host链接 | GCC O2及Clang function/UBSan两版均exit0/唯一HOST PASS；真实difftest.cpp及生产difftest.h参与链接，common.h仅测试替换Verilator模型依赖并提供相同FLASH_BASE。实际dlopen测试DSO，port从非零哨兵变0；严格init→memcpy→regcpy调用序、base/8字节/方向、33字包/GPR/PC、一次exec、一次skip只同步不exec及下一次step全部匹配。测试DSO不模拟SoC，真实执行另见下行。local/host-results.json及probe两构建日志 |
| 新同版REF | M1-P9隔离build，RV64 SHARE/DEVICE=n/GARRAY；DYN/六导出、原33字选择复制/前后哨兵/五内存域两端及真实三条指令/time=0通过，显式init0。未安装/覆盖默认REF。local/final-ref/{config,build,elf,exports}.log及ref-abi.log |
| 新完整SoC NPC | 当前C++/RTL源复制隔离构建，make现有DIFF=1/WAVE=0/WITH_TRACE=0/WITH_SDL=0/PERF=1/PERF_R45=1，exit0，15.202秒；未复用根目录陈旧NPC binary，不修改RTL或Make接口。local/soc-build.log/result及binaries.json |
| 真实CPU-tests全集 | 标准CPU-tests run、-j1、隔离当前AM/klib源码重新构建37个guest并运行新NPC+新REF，exit0，60.312秒，36 PASS+wrong 1 XFAIL；37份日志独立确认唯一init port0、difftest ON、主终态正确，无DIFF ABORT/预算耗尽/错误分歧。使用`MAKE=/usr/bin/make -o build/ysyxSoCFull`仅复用本轮已新建的同版模型，不免除guest构建。local/cpu-results.json/cpu-log-validation.json/cpu-logs及74个bin/elf输入身份 |
| 实际对拍故障控制 | 同一新NPC/真实REF，透明转发DSO只污染比较输出的PC或t0；两例均出现所需mismatch+DIFF ABORT，host exit0仍按日志拒绝，不误当guest通过。转发init同时断言实参0。local/negative-results.json及negative-{pc,gpr}.log |
| 最终身份/归档 | 693项preclean全部通过（以身份/归档检查为主，非693个功能场景）；258个消费者输入、97个REF输入与根源及隔离副本/两新模型/74guest身份匹配，完整diff正反恢复精确；native/config/默认NPC/默认REF/正式盘及PAL旧差异保持。local/identity.json、validation-preclean.json |

host初次类型检查被只读ccache缓存目录拒绝；仅在测试进程设置`CCACHE_DISABLE=1`重试，得到预期的原版类型失败及最终通过。原缓存错误保留local/initial-ccache-failure.log，未安装软件或修改系统配置。普通/Clang两组host-results共7项包括预期失败的类型/旧调用见证，不能把这些exit1写成原版产品通过。

## 影响选测与限制

本修复位于NPC的difftest初始化，真实CPU全集37次初始化与连续逐条对拍覆盖直接消费路径；PC/GPR两故障控制证明对拍实际生效。未重跑RT到msh或nanos三前台：改动不涉及guest/OS/REF运行语义，RT共用的初始化已经CPU全集覆盖，nanos native不调用NPC初始化。未运行NVBoard/GUI、其他ABI平台或端口后端；当前port仍仅打印，不能据此声称网络功能或真实中断同步能力。新模型只在隔离路径验收，根正式默认NPC/REF没有替换。

## 完整修复diff与版本

根仓`ysyx-workbench`，相对路径`npc/csrc/util/difftest.cpp`。旧完整commit `f5b9973412e7c466cc5111dcf1f10c8759100c49`；新为2026-10-20未提交工作树，mode100755保持，末尾换行变化如实保留。

- 旧SHA256：`ed48e5a07f33a94ac747e7dc4ec49518e763e21af21cbd6d6d8de0f44cc73233`。
- 新SHA256：`85c5de2fd766db9fdaf95d8dd263d9842ca2c9b3ede34041823dfba1dfb61099`。
- 本次新NPC SHA256：`617787cecfda8a0e4872fe6c9c364e20f367ad47985a595a3c8b3b8f9b206836`。
- 本次新REF SHA256：`3057934201409b7f9aa38c5e6ff8a04a548b4fd6b34bc735c7071c1cda81995d`。

```diff
diff --git a/npc/csrc/util/difftest.cpp b/npc/csrc/util/difftest.cpp
index f9238a75e661b976509fe31ea3044c8c32e5b5be..0a9a0846d0e3f08a0f48972b9df89d6348775822 100755
--- a/npc/csrc/util/difftest.cpp
+++ b/npc/csrc/util/difftest.cpp
@@ -33,12 +33,12 @@ void init_difftest(char *ref_so_file, long img_size, uint8_t* mem, uint64_t *cpu
     assert(nemu_difftest_exec);
     nemu_difftest_raise_intr = (void (*)(uint64_t))dlsym(handle, "difftest_raise_intr");
     assert(nemu_difftest_raise_intr);
-    void(*nemu_difftest_init)(void) = (void (*)())dlsym(handle, "difftest_init");
+    void(*nemu_difftest_init)(int) = (void (*)(int))dlsym(handle, "difftest_init");
     assert(nemu_difftest_init);
     void (*nemu_difftest_ref_display)(void) = (void (*)())dlsym(handle, "difftest_ref_display");
     assert(nemu_difftest_ref_display);
     // printf("difftest link end\n");
-    nemu_difftest_init();
+    nemu_difftest_init(0);
     nemu_difftest_memcpy(FLASH_BASE, mem, img_size, DIFFTEST_TO_REF);
     for(int i = 0;i<32;i++){
         cpu_context[i] = cpu_gpr[i];
@@ -77,4 +77,4 @@ bool difftest_step(uint64_t pc, uint64_t* dut, uint64_t sim_time){
         if(dut[i] != ref_data[i]){printf("time: %ld, pc: %lx(dut), %lx(ref), reg %s does not match! ref: %lx, dut: %lx\n", sim_time, pc, ref_data[32], regs[i], ref_data[i], dut[i]);error = true;}
     }
     return error;
-}
\ No newline at end of file
+}
```

内嵌diff等于完整生产差异；从明确旧版本取源，正向应用等于新源，反向恢复含原无末尾换行字节的旧源，两项均实际通过。原FINAL_FINDINGS/P9为历史审阅截面，不改写历史“未修”结论，现行修复状态由本报告及repair-status维护。

## 复现配方与提交范围

在工作区根设置`H=npc/verif/records/process/code_correctness_review/crp-f0119/local`，清理后的隔离目录不存在，可按下列步骤从Git/当前源码再建；build.py复用现有M1-P9 builder，不下载/安装，不执行自动commit hook：

```sh
python3 "$H/run-host.py"
python3 "$H/prepare.py"
python3 "$H/build.py"
python3 "$H/run-cpu.py"
python3 "$H/negative.py"
python3 "$H/verify.py"
```

prepare记录当前输入身份并复制源码，build使用已安装Verilator/编译器；后续源码若变化应按identity恢复相应版本，不把未来新版结果冒充本次验收。旧host源码由本报告旧Git版本自动取回，类型见证副本由同一源加测试断言生成，无需保留整份生产源码快照。必要的probe/故障转发/配方及文本日志本地保留，单次测试代码不加入生产仓库；提交候选仅生产两行及报告/.gitignore/records索引/repair-status，本轮不自动提交。ignored local/.agent不由普通commit备份。

## 清理与完成停点

693项preclean及全部动态验收完成、所有本组构建/执行已结束后，按cleanup-plan/receipt删除565条路径（502文件），137996332逻辑字节，0 tracked删除。包括两新模型、host/DSO及故障二进制、74guest bin/elf、隔离NPC/AM/CPU源码/构建树、原版/类型见证生产快照；不跟随symlink，正式源码/资源/默认产物保留。构建/执行日志、配置/输入身份、最小测试/复现脚本、完整patch保留；identity指向已删除产物的哈希仅作当时身份，以cleanup回执解释预期缺失，不宣称现在仍可直接执行。

累计93已修/26未修完（含5CQ/F0040 Partial），前92已确认提交；F0119 Completed，结果确认/commit Pending。Working tree contains uncommitted F0119 repair/documentation changes，root HEAD仍f5b9973/index空，原nested差异保留。未来只沿[TASK_QUEUE唯一入口](../../../../../../.agent/TASK_QUEUE.md#crp-next)，本轮停止等确认，不自动commit/push/下一组/M2。

会话建议：建议开启新对话；本轮已累积REF/NPC构建与多层证据，下一单元转libam时间桥接，恢复资料已落档。建议本身不增加批准门槛或要求另造启动Prompt。

最终终检463项全部通过、130份保留身份，完整内嵌diff与正文空白检查无告警；入口为local/final-validation.json、manifest.json、whitespace-review.json。复用本单元完成快照，不新增动态验收/执行授权。

<a id="submit-20261020"></a>
## 用户确认与提交（2026-10-20）

用户再次“提交后继续”确认本单元已报告范围并授权精确提交，以及提交后执行TASK_QUEUE登记的F0117一个单元。提交前130项保留证据manifest及生产SHA核对无漂移，复用463项最终终检与既有动态验收，不重复测试/完成快照。提交仅含生产源码、报告/.gitignore和两个索引；实际commit回执见local/submit-receipt.json及.agent，ignored证据不随commit备份。无push。

会话建议：可在当前对话继续；本对话刚完成状态恢复，下一单元边界与证据入口明确。
