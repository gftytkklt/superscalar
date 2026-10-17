# CCR-P5 证据与复现

审阅结果：[P5](../P5.md)、[AM_RUNTIME](../AM_RUNTIME.md)、[问题](../FINDINGS.md#ccr-p5-findings-20261017)、[Final Gate](validation.json)。仅RV64 NEMU/NPC运行时与AM BSP责任，生产代码未修复；不开展P6。

- 身份：[baseline.json](baseline.json)、coverage.before.jsonl.gz；源输入相对P1零漂移；[S06更正](scope-correction.json)将1个误留RV32 ELF明确排除，2,536保留文件已审。
- 覆盖：[file-review.jsonl](file-review.jsonl)、[branch-review.jsonl](branch-review.jsonl)、[source-evidence.jsonl](source-evidence.jsonl)、[artifact-review.json](artifact-review.json)、[汇总](review-summary.json)。S01/S02/S03深度不是功能PASS。
- 问题：[findings.json](findings.json)；旧问题不重编号。
- 第一组：[run_probes.py](run_probes.py)、[klib-probe.c](klib-probe.c)、[device-probe.c](device-probe.c)、[命令/环境/哈希](probe-results.json)。53条终版命令。
- 第二组：[run_supplement.py](run_supplement.py)、[NPC/BSP命令](supplement-results.json)。18条，包含PS2 MMIO替换、RT边界stub与原生成器wrapper模板的延迟启动复现。
- 最终定向组：[run_final_probes.py](run_final_probes.py)、[命令](final-probe-results.json)。8条，IOE结构断言、guard ABI、真实RT声明、测试recipe与fake工具失败传播。
- Final Gate：[validate_p5.py](validate_p5.py)、[validation.json](validation.json)、[manifest.json](manifest.json)。门检查结构/状态/证据，不代表没有遗留缺陷。

在工作区根执行上述三个run脚本可重现各自证据；只调用既有GCC/G++/binutils与host程序，**不调用原make/run/update/scons，不安装/下载、不接真实硬件、不commit**。脚本创建唯一`/tmp/ccr-p5-*`输出树并复制必要源/头；只写本目录的证据。会更新本目录同名日志/命令JSON，需要保存旧批次时先另存；当前批次精确/tmp位置、工具版本、argv、必要环境与产物hash见三份result。build_review.py只生成审阅元数据，不执行目标程序。

host采用LP64和unsigned char；NEMU通过替换nemu.h访问函数、NPC PS2只替换两个MMIO表达式，video/UART用私有匿名mmap。BSP为小RT边界stub，无真实线程切换；wrapper延迟启动是允许的故障触发前提，默认立即调度可能掩盖。fake make/nm/objcopy测试仅验证生成器失败传播，不是构建测试。没有guest/FPGA/GUI/声音/并发线程执行。

非零退出不一律是harness失败：strncpy/format/int64预期sanitizer1，超容量音频harness上限42，缺设备fail映射halt为61，真实RT声明冲突编译1。全部终版命令均匹配各自预期。attempt日志是先前环境/fixture不完整或首次发现异常的真实保留，不计入79条终版命令；原始失败输出未清理。普通commit不备份ignored报告/JSON/压缩证据/.agent，未改跟踪规则。
