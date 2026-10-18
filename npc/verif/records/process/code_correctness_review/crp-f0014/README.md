# CRP F0014 — REF 内存复制整段边界

## 计划及授权（2026-10-18）

用户“提交，继续”确认前组并授权提交后执行唯一下一单元；前组已实际提交
`77a9471d6da2ccbee3a5180b39852bedbe9189c5`，提交后 root/index 干净。
沿现行 [CRP 规则](../workflow/README.md)，本单元只处理 F0014，不推进 M2。

目标/范围：REF difftest_memcpy 只在完整区间属于同一注册物理内存且已分配时访问；
用 size_t 循环避免 int 溢出。保持五域、方向、void ABI、原零长度无访问语义，
不拼接跨区、不增加可恢复错误协议。非零非法区间按现有物理越界 panic 契约报告并
终止；host buffer 仍由调用者提供合法大小。修改限 ref.c、paddr.c、paddr.h。

本单元：先最小修复及原版反例，再同版边界/真实消费者验证，留档后停等用户确认/
commit，不自动串行下一单元。无安装或新策略裁决；若实际出现契约冲突则停相关项。
交付为生产修复、本报告/局部ignore、records索引/逐项状态/.agent，以及本地证据。

验收：五域首尾双向复制、0长度/区尾/跨界/高地址/地址回绕/n>INT_MAX/SIZE_MAX；
检查失败在任一读写前、哨兵不变。host ASan/UBSan、真实独立REF构建/导出/33字ABI/
实际执行，复用 M1-P9 入口；CPU-tests全集与真实 RT/NPC 到 msh 覆盖 REF 初始化
消费者，按实际影响选测，不重跑不调用REF复制的 nanos/NEMU native 应用。

参考（2026-10-18访问）：[ICS-PA 基础设施(2)](https://ysyx.oscc.cc/docs/ics-pa/2.4.html)
定义 difftest_memcpy 的 addr/buf/n/direction 和 void 接口；非法范围处置以本地
既有内存/断言契约为准，讲义并未规定新增跨区/恢复能力。原问题/P3证据及
`nemu/tests/m1_p9_ref.py` 是本组恢复入口；临时脚本/日志/binary保留在 local/。


## 技术发现与修改

`addr_to_soc_range(addr,n)` 共用既有 mem_regions 查找，先取得合法首地址，再检查
`n <= region.size - offset`，不计算可能溢出的 addr+n；未注册区、未分配指针或跨出
同一区域返回 NULL。未改变原 addr_to_soc、paddr_read/write 或 MMIO/页表访问逻辑。
REF 入口在非零失败时沿现有 panic/断言机制终止，copy 循环统一 size_t；零长度
立即返回，不访问 buf/guest，也不形成 guest 指针。

**地址宽度**：当前 REF 配置的 paddr_t 是 32 位，但 NPC difftest.cpp 的函数指针及
M1-P9 ctypes ABI 均传 uint64_t。旧入口直接使用 paddr_t，`base + 2^32` 会在校验前
截断到 base。本次入口使用调用方既有 uint64_t，先检查可由 paddr_t 表示再转换，
拒绝高位别名。未改变 NPC 函数指针、导出名称、void返回值/方向或33字寄存器包，
不新支持超出当前物理地址域的访问。讲义的泛型 paddr_t 不替代本地实际调用契约。

## 定向及真实 REF 验证

| 验证 | 本次结果与证据 |
|---|---|
| 原版反例 | 跨 MROM 尾部 2B、INT_MAX+1 长度、高地址别名三项均失败；高地址旧版会读低地址而非拒绝，超大长度被 ASan 捕获 host 缓冲区溢出，跨尾由未拒绝断言抓到。不声称实际分配/复制了 2GiB。local/before-*.log |
| 同版 ASan/UBSan | 三反例全部通过，组合3030断言通过；五域首尾双向copy、末字节、0长度/one-past零长度、跨尾、base-1、整域+1、INT_MAX+1、SIZE_MAX、UINT64_MAX/回绕、高位别名、未分配区域指针。错误以隔离 assert_fail_msg/longjmp 观察，检查首尾guest/host哨兵不变；不替代真实进程终止验证。local/host-results.json、after-all.log |
| 真实 REF API | 77/77 场景：15个首/尾/末字节双向roundtrip、24个零长度无访问、38个独立非法区间调用。非法调用以无效host指针0x1证明先拒绝区间；均诊断range out of bounds并SIGABRT（-6），没有先SIGSEGV。local/real-results.json、real-invalid/ |
| 真实构建/ABI/执行 | 复用nemu/tests/m1_p9_ref.py的隔离build与--abi入口；DYN/六导出、原五域、33字PC/GPR选择复制/哨兵、flash三条指令/time=0通过。local/ref-final/{config,build,elf,exports,abi}.log及ref.config/so |
| native保护检查 | 原.config及generated/config headers未改；默认native重建后p 1+2=3、内置guest GOOD TRAP/exit0。新函数不改变原native物理访问路径。local/native-build.log、native-result.json |

真实API测试没有stub CPU/内存；ASan夹具引用真实paddr/ref源码和独立REF配置，仅
截获错误终止以检验失败前后字节。超大n不实际分配大host内存，拒绝前绝不能访问它。
同一注册区域的完整长度只作pointer/range检查；实际大块copy由NPC的整16MiB flash
初始化覆盖，不声称遍历五域所有字节或所有物理配置。

## 命令与复现资料

复用既有M1-P9的build(out)和 `python3 nemu/tests/m1_p9_ref.py --abi <ref.so>`，
输出独立local/ref-final；配置固定 riscv64-ref_defconfig、SHARE=y、DEVICE=n、
GARRAY。未执行该脚本的全UI/UM回归，也未调用其--install；消费者回归见下方本组
记录。首份local/ref-build为发现地址截断前的中间构建，不作为最终验收产物。

- host编译/执行精确argv：local/host-commands.json；gcc -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -no-pie，使用local/include里的ref.autoconf.h及真实项目头文件。
- host运行：ASAN_OPTIONS=detect_leaks=0:abort_on_error=1，UBSAN_OPTIONS=halt_on_error=1；local/harness-{before,after}.c保留一次性源，原版只执行独立反例，不当作最终组合结果。
- 真实API：`python3 npc/verif/records/process/code_correctness_review/crp-f0014/local/real-ref.py`；ctypes参数固定uint64/void*/size_t/bool，子进程禁止core dump。
- native构建：`CCACHE_DISABLE=1 make -C nemu -j4 app NEMU_HOME="$PWD/nemu" 'git_commit='`；CLI使用SDL_VIDEODRIVER=dummy/SDL_AUDIODRIVER=dummy，输入p 1+2、c、q。
- 消费者：`python3 .../local/consumer-run.py cpu` 与 `python3 .../local/consumer-run.py rt`，argv/env/输入身份见consumer-fixture.json及逐例结果。

临时夹具/日志/binary/快照只保留local/，不纳入提交。生产变更仅ref.c、paddr.c、
paddr.h；不新增Make选项/日常运行步骤，不安装软件。完整源/配置/产物身份将在
local/identities.json和manifest记录；.agent仍是本地忽略资料。


## 真实消费者及完成结论

**F0014 Completed；结果确认 Pending，修复 commit Pending。** HEAD 为前组
77a9471；Working tree contains uncommitted CRP repair/documentation changes，index空。

| 消费者 | 本次结果 |
|---|---|
| CPU-tests全集 | 37个既有riscv64-npc镜像逐个执行，36 PASS + wrong 1 XFAIL，无ERROR/超时。使用与当前RTL主文件/difftest.cpp一致的既有DIFF=1仿真器和新ref-final/ref.so，逐例核对NPC专有终态、difftest ON及无分歧；不以工具exit0替代guest结果。local/cpu-results.json、cpu/ |
| RT真实NPC | 同一新REF、真实既有RT镜像，141.57秒到Hello RISC-V!/msh，difftest ON、无DIFF ABORT/预算耗尽。观察到msh后对自有进程组SIGTERM，exit=-15，非guest正常退出。local/rt-run.log、rt-process/rt-recheck.json |
| RT判据修正 | 首次supervisor的原始字符串匹配未剥离ANSI，虽然guest已到msh，diff_on字段误判false、supervisor exit1。保留rt-result/rt-supervisor初始失败；修正ANSI规范化后复核同一原日志通过，并以去掉ON/去掉prompt/追加晚到DIFF ABORT三个负例确认拒绝；未重复启动guest，不将初始错误结果改写为成功 |
| 最终一致性 | local/validation.json共17项全部通过；最终源码快照、配置/产物身份、HEAD/index、实际默认REF、既有native配置/header及根NPC二进制保护全部核对 |

本次只改REF的copy入口及新增独立范围helper，没有修改生成器、guest源码或NPC RTL。
CPU/RT使用之前已构建并验收的现成镜像，本轮**未执行CPU/RT重构建或RT update**；
完整命令及每个镜像输入在cpu-results/consumer-fixture中保留。NPC复制完整16MiB
flash到REF后正常执行；本轮对拍仍仅旧PC/GPR/skip边界，不扩大priv/CSR/内存比较。
未跑全UI/UM、NEMU-on-AM、非RV64/PMEM64/malloc配置或Linux完整启动。
新增helper不改变native paddr访问路径，已做native真实smoke；nanos三前台/hello
不消费REF loader，本轮未重跑，不能以RT或内置guest结果冒充这些回归。

最终新REF SHA256：
`2ae21a862cbd667658efbb8bf465df9d2e197cb84e777ab925fe86adef4f79ce`。
验收后已复制到原默认 `nemu/build/riscv64-nemu-interpreter-so`，仅替换既有本地构建
产物，不是软件/系统安装。旧产物保存在local/previous-ref.so，SHA256
`ea44e661db1b9ef12612ef6d07449bc9c5efa920c8267149801d45f4a134ee62`，需要回滚时
复制回原默认路径即可；install-receipt保存实际回执。native已重新构建，配置/
headers/NPC原binary未改变；不会将本次验证副本产物冒称根NPC已重建。

累计26项功能已修，93项未修完（含5CQ和F0040 Partial）；此前25项已提交，本组
1项待确认/提交。保留PAL供给/性能因果、F0043协议、五CQ、并发及缺源风险，不从
本批验收推定其获裁决。按本组计划停止，下一单元只沿TASK_QUEUE；不自动提交
本轮新修复、不push/安装/推进M2。local证据与.agent不随commit备份。


<a id="approval-submit-20261018"></a>
## 用户确认及提交授权（2026-10-18）

用户“提交，继续”确认本组已报告范围及限制，授权提交后执行唯一下一单元。
提交前146条manifest逐字节无漂移，原17项validation全部通过，index空；复用原
3030/77/CPU全集/RT验收，不重跑动态测试。仅提交3份生产文件、本报告/局部ignore、
process索引、repair-status及前组实际提交回执；local/.agent沿用本地持久化，
commit不代表备份。实际提交以包含本节的Git提交及local回执为准，不预记成功；
不授权push或扩大未测能力。
