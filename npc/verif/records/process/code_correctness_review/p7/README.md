# CCR-P7 证据与复现

主记录：[P7](../P7.md)、[用户运行时](../USER_RUNTIME.md)、[ABI表](../SYSCALL_ABI.md)、[第三方边界](../THIRD_PARTY_P7.md)。P6已按本轮明确授权提交`bdc02a3`；本目录属于未提交P7，不含生产修复。

## 证据

| 文件 | 内容与解释 |
|---|---|
| baseline.json / coverage.before.jsonl.gz / findings.before.json | P6提交后2689输入及11011行P7原责任；coverage全量40010行备份和旧75问题，供差集验证 |
| libc-provenance.json / libc-import-diff.txt / *-template.diff | 独立repo/import身份、本地71变更条目、模板原字节对比；不是独立上游tarball认证 |
| file-review.jsonl / branch-review.jsonl / review-summary.json | 逐身份深度和结论；8322条件是导航，不是运行覆盖率；无关第三方算法只BoundaryReviewed |
| asset-review.json / fsimg-match.json / scope-correction.json | 初始1756资产格式、108镜像extent匹配、65个native产物S06更正 |
| support-sources.json / os-call-sites.txt | 跨P6/AM/NDL头/包装支持输入哈希、定向源码导航；不推进P8实现审阅 |
| probes/ | 第一组56命令，全部符合预期退出码；43 RV64生产单元编译、ABI、反汇编、calloc、零大小fwrite |
| supplement/ | 第二组10命令；保留一次探针自身原型错误导致的失败；两条repair-results修复重编/重跑成功。libam3 RV64单元、宿主hook/heap、errno/sbrk、fake-make失败传递 |
| width/ | 第三组5命令；host LP64返回宽度现象与RV643份汇编，不能跨架构类推误编译 |
| findings.json | 本轮14个问题的源码hash、等级依据、可达性、验证/建议/限制 |
| validation.json / manifest.json | 最终差集/身份/文档/生命周期检查与交付哈希；检查脚本见validate.py |

## 复现方法和隔离

现有工具：系统`/usr/bin/riscv64-linux-gnu-gcc/g++`及binutils、host gcc/g++、Python3、make；完整版本和argv在各results/log中。不安装软件，不下载第三方，不执行项目原始make（即使make -n也可能触发解析期副作用），不启动NEMU/NPC/guest。

```bash
python3 npc/verif/records/process/code_correctness_review/p7/run_probes.py
python3 npc/verif/records/process/code_correctness_review/p7/run_supplement.py
python3 npc/verif/records/process/code_correctness_review/p7/run_width.py
```

上述每次创建新的/tmp工作与输出目录，不覆盖已归档证据；无须为本阶段再次重跑。`run_probes.py`复制生产libc/libos，RV64只编译选定单元，不作全库/全产品链接。宿主fwrite只重命名导出符号并提供外部FILE钩子；UBSan退出1是预期复现，不是测试遗漏。calloc stub只捕获尺寸且返回NULL，不验证实际allocator分配后行为。

`run_supplement.py`隔离副本仅把libos寄存器/asm/return块替换为p7_ecall；重命名reent低层errno防止与宿主TLS errno混淆，其他wrapper保持文本。libam保持RV64软件CTE分支，host trm原非RISC-V输出函数被gc-sections裁掉。fake-make仅返回7/0；未安装或改写真实fsimg。

原始`errno-paths`退出4源于fixture缺少`p7_sbrk(intptr_t)`声明，负8被调用者当32位实参；不是生产_sbrk bug。补声明后只重编该probe并重跑：`errno-build-fixed`与`errno-paths-fixed`均0，详repair-results。当前fixture已包含声明，再运行脚本不应重现该脚本错误。保留初始日志，不将其抹成全部首跑通过。

`run_width.py`使用生产readr/writer/lseekr及受控64位stub；host观察截断，而当前RV64没有额外截断指令。memory visibility probe当前也重新读缓冲，F0078只列Robustness。所有宿主实验证明范围都限于替换/桩明确列出的局部逻辑。

记录生成阶段曾纠正两个校验假设：部分native .d只列本地头，排除依据应是目标与EM_X86_64对象逐一对应；生成器首次缺errno目录分类。链接文件名校验也捕获过旧草稿日志名。这些属于留档工具校验，已修正，不是生产失败或新增问题。

## 持久化边界

本仓库规则忽略多数Markdown/JSON/日志及.agent；普通git提交不会完整备份这些证据。未改忽略规则、未force-add、未上传。`manifest.json`列可携带的本地证据；/tmp编译产物不承诺永久存在，长期恢复使用已归档源hash、fixture、argv及日志配方。P7结果待用户确认/commit，P8未Start。
