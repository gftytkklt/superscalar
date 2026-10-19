# CRP F0001 — RV64算术的宿主语义与双端核验

2026-10-19 Start，用户“提交后继续”授权F0002提交784e73b后执行既有算术单元，并要求说明具体计算反例、同时核对NPC，若双端存在缺陷则一并修复。M2不变，本授权只覆盖本CRP的必要修复。

## 计划与边界

沿既有F0001计划：复用原P2反例→对比无插桩数值和UBSan诊断→核对NPC译码/ALU/乘法及当前执行器身份，以独立无符号期望验证双端→最小修复确认的缺陷→同版真实构建/CPU/RT/nanos共享消费者→留档后停止等确认/commit。保留Make/ABI/异常/性能参数，不安装。

范围为ADDIW/ADDW/SUBW/MUL/MULW/SLLW及同根SLLIW；发现同根立即纳入，不机械改无问题的RTL。交付确认缺陷的源文件、本报告/ignore及索引/状态；一次性测试/源码快照/生成日志和镜像local保留。验收0/±1/MIN/MAX、W高位噪声、左移0/31及移位掩码、rd别名/x0、PC+4；GCC/Clang优化与UBSan，双端真实guest独立比较ISA期望，避免只靠difftest同时同错。未测/既有限制分别记录。

## 结论与具体反例

**F0001 Completed，结果确认/commit Pending。** 你关于现有测试能通过的判断得到本轮复现支持：原NEMU在当前GCC/Clang普通`-O2`下，原7个反例及独立64项数值/PC/寄存器检查全部正确。未观察到这些普通构建的错误计算值；原问题的确定缺陷是宿主C未定义行为（UB），不能把“有UB”写成“现编译器已算错”。

| 指令 / 合法guest输入 | ISA要求的64位结果 | 原普通GCC/Clang O2 | 原GCC/Clang UBSan |
|---|---|---|---|
| ADDIW / ADDW：0x7fffffff + 1 | ffffffff80000000 | 结果正确 | `2147483647 + 1`超出int范围，exit1 |
| SUBW：0x80000000 − 1 | 000000007fffffff | 结果正确 | `-2147483648 - 1`超出int范围，exit1 |
| MUL：0x7fffffffffffffff × 2 | fffffffffffffffe | 结果正确 | signed 64位乘法溢出，exit1 |
| MULW：0x7fffffff × 2 | fffffffffffffffe | 结果正确 | signed int乘法溢出，exit1 |
| SLLW / SLLIW：低32位ffffffff，左移1 | fffffffffffffffe | 结果正确 | 对负int值−1做左移，exit1 |

例如原`SEXT(((signed)src1 + (signed)imm), 32)`会先做C的signed int加法，之后才执行SEXT；SEXT无法使前面的溢出成为有定义运算。RISC-V要求取低32/64位并允许回绕；C的signed溢出不提供该保证，负有符号值左移也有UB。这解释了现有程序/普通构建通过与UBSan失败可以同时成立，不能由一次普通构建通过推定所有优化/编译器行为。来源（2026-10-19读取）：[官方RV64I/M规范](https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf)W结果/低位乘法章节、[C11草案N1570](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1570.pdf)§6.2.5p9/§6.5p5/§6.5.7p4、[GCC signed溢出检测](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html)。ICS-PA2.2作为译码/执行背景，未用其简化范围替代ISA数值语义；当前官方规范返回20260120版本，仅补充本次既有RV64I/M契约，不扩新指令。

## 双端核验与最小改动

生产仅`nemu/src/isa/riscv32/inst.c` **8增7删**（RV64为RV32源目录软链接，共用一份）。ADDIW/ADDW/SUBW/SLLIW/SLLW/MUL/MULW改用既有无符号word_t计算；W类通过既有SEXT取低32位再符号扩展。Unsigned模2^64计算的低32位与直接模2^32结果一致，MUL保留低64位；不新增-fwrapv、不关闭UBSan，不改变Make接口、正常ISA结果、REF ABI或异常政策。

NPC核对`npc/vsrc/ysyx_22040750.v`译码、W mask、ALU加减/移位、Booth乘法与W写回：译码将对应指令送入定宽运算；加减按向量宽度截位，移位取低5位，W写回统一由bit31符号扩展，乘法保留所需低位。其RTL语义与宿主C的signed溢出不同，NEMU出现C UB不自动意味着NPC同一数值错误。

当前原NPC RTL/执行器用独立Python整数模运算生成的64项期望逐项自检，原REF和新REF两轮均GOOD TRAP；测试实际运行对应机器码，覆盖溢出、MIN/MAX/±1/0、W高32位噪声、移位0/31/32/63、rd=rs1/rs2/x0。将首项期望故意改错，NPC真实guest报主BAD TRAP/ret1，证实并非只凭difftest相等判通过。因此本次没有确认NPC对应缺陷，**保留原RTL，已完成双端核验，不制造无依据的对称修改**。若后续出现NPC具体反例，应按本批补充复核后修复；本结论不是全输入形式证明。

## 本次验收与证据

| 验收 | 结果 / local入口 |
|---|---|
| 原P2反例新鲜复现 | p2.py链接当前成套CPU/ISA/MMU/内存，仅设备/时间受控；原7条在GCC/Clang O2共14次得到正确数值，GCC/Clang UBSan共14次均精确报告5种signed溢出/两种负值移位并exit1。p2-results.json及逐例日志保留；本轮在P2夹具仅补SLLIW同根分支，不改原P2归档 |
| 64项生产CPU链定向 | baseline2 GCC/Clang O2各64/64；final GCC/Clang O2及两种UBSan各64/64，PC+4、32 GPR整体、priv/cause保持。期望来自Python大整数/显式位掩码，非抄生产算术表达式。cases.json/vectors.py/repro.c、original与baseline2/final成套源与日志可回查 |
| native/REF真实构建 | 同版隔离构建两配置，native内置guest/原33字PC-GPR/五内存域REF ABI通过，builds.json/ref-abi.log。原配置/模型不动，Make禁用compile_git，AM传git_commit= |
| 双端真实算术guest | 相同64项独立期望/原始机器码汇编，经原AM接口分别构建NPC/NEMU镜像。NPC先配原REF、再配新REF均主GOOD；native/新REF亦GOOD。guest程序逐项分支判定，失败返回case编号，避免两端相等但同错。见npc-directed-baseline2/final.json、guest-results.json、算术guest原始日志/镜像/反汇编 |
| 故障判据 | 故意改错首项独立期望：NPC主BAD/ret1（模拟器进程exit0、另有REF附加BAD）；NEMU BAD/exit1，均正确拒绝。negative2日志及JSON保存；host判据另对非零exit、缺行、重复行、FAIL、错PC及UB诊断6种故障拒绝，不把退出0单独作为PASS |
| CPU真实全集 | 新REF/当前NPC及新native各36 PASS + wrong 1 XFAIL，make均exit0，65.94/26.03秒；74份原始主终态/退出码核验通过，无SIGTERM或预算结束当成功。NPC执行器SHA/与当前源比较先核；NEMU沿用既有_heap_end测试兼容符号与-j1，不声称默认缺符号入口已修 |
| RT真实消费者 | 原已验收NPC + 新REF，168.44秒到msh，difftest ON，无分歧。RT源/生成器未变，复用已验收镜像/记录SHA，不重update；观察后自有组SIGTERM/exit-15，非guest正常退出 |
| nanos真实消费者 | 隔离当前AM/nanos源码、现Navy ramdisk，在新native下51.74秒完成8截图点，F2终端及命令、F3 slide0→1→0、F1回PAL与Enter后继续；后台hello1262→5850递增，截图已目视核对。Navy源/生成器未改，不重复update；观察后自有组SIGTERM/exit-15 |
| 终检/身份 | validation.json **24/24**，含6判据故障、默认模型/配置、原HEAD、同版构建/定向/生产源码、原NPC与当前源码一致、前组285文件manifest无漂移、空index/空白检查。必要manifest **326文件**，是配置/测试/源码身份/日志/镜像/截图的SHA条目，不是326条测试 |

## 恢复、限制与停止边界

命令：`python3 local/p2.py`、`vectors.py`、`directed.py baseline2`（随后修复再`directed.py final`）；`prepare-consumers.py`、`npc-directed.py baseline2`；`build.py`后`npc-directed.py final`、`guest.py`；`cpu.py`、`rt.py`、`python3 local/nanos-run.local nanos`；`verify.py`。均从本报告目录运行并使用新建输出语义，复现应换路径，避免覆盖现有证据。guest负例判据修订后的本次实际补跑命令为`python3 local/guest.py negative-only`，复用了先前已通过的native/REF正例，不重复执行。

无效测试尝试留档、不计PASS：初版64项C夹具漏init_mem声明，GCC可编译但Clang拒绝；补原型后baseline2/final通过。尝试省略REF以关闭NPC difftest，现执行器编译期启用difftest并要求REF实参，此尝试失败/原始模拟器exit码Unknown，不推断算术错误或双端测试完成；最终正常传原/新REF，独立guest常量照常自检。负例首轮误把NPC主BAD与REF附加BAD计为两个主终态，原始guest其实已正确失败；修订为主终态计数并按要求重测判据，不改生产runner，guest-attempt1.py/bad-npc.log与negative2日志保留。

当前为x86小端/RV64/paddr32、默认native及静态PMEM REF；未跑RV32/RVE/PMEM64/全部编译器或优化组合、Linux/长时/实际声音/完整四AM应用。没有宣称找到了原普通O2数值错误、证明所有输入正确或修复PAL性能；既有F0003指令对齐、F0009 DMA、F0026栈预算、五CQ、F0040Partial、F0043与两缺源保留。

本组一次性C/Python/汇编、快照/JSON/日志/镜像/截图均仅local保管；未来提交候选只含确认缺陷的生产文件、本报告/ignore和必要索引/镜像。root HEAD784e73b，Working tree contains uncommitted CRP code/documentation changes，index空，无push/安装/运行中动作。普通commit不备份ignored/.agent资料或外部RT/Navy资源，冷启动需携带本地证据与隔离配方。

累计 **42项Completed / 77项未修完**；前41项已确认提交，本批F0001结果确认/commit Pending。统一留档后停止；下一单元仅沿[TASK_QUEUE](../../../../../../.agent/TASK_QUEUE.md#crp-next)，不自动提交或推进M2。

## 2026-10-19 确认/提交补充

用户“提交后继续”确认本批已报告范围/限制并授权提交；326文件manifest、24项既有验收及生产/默认模型/配置身份无漂移，复用动态结果。仅提交生产inst.c、本报告/局部ignore、process索引与repair-status五文件；测试/原始证据继续local保留。实际提交回执见local/submit-receipt.json与.agent补充，无push；ignored/.agent不由commit备份。用户同时放行TASK_QUEUE唯一入口F0003一个单元，保留双端核验及真实新能力裁决停点。
