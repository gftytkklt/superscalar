#!/usr/bin/env python3
"""Materialize CCR-P3 static finding and coverage evidence; no project build/run."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
CCR = ROOT / "npc/verif/records/process/code_correctness_review"
OUT = CCR / "p3"


def issue(number, title, severity, paths, expected, actual, reach, fix, limits):
    locations = []
    for path, lines in paths:
        source = ROOT / path
        locations.append({"path": path, "lines": lines,
                          "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    return {"id": f"CCR-F{number:04d}", "title": title, "severity": severity,
            "status": "Confirmed", "phase": "CCR-P3", "locations": locations,
            "expected_contract_and_basis": expected, "actual_and_root_cause": actual,
            "reachability_and_impact": reach,
            "validation": "2026-10-17 静态调用链及源码行检查；未执行本问题的动态复现；P3.md与p3/source-evidence.json列身份和环境限制。",
            "minimal_fix": fix, "recommended_regression": "隔离副本中对所述正常、边界、错误及重复操作做定向复现；由契约独立给出期望并检查退出码/状态。",
            "unconfirmed_assumptions_and_limits": limits,
            "evidence": ["p3/source-evidence.json", "P3.md"]}


ISSUES = [
    issue(9, "disk DMA未校验来宾地址及整段长度", "High",
          [("nemu/src/device/disk.c", [57, 65]), ("nemu/src/memory/paddr.c", [80, 85])],
          "设备命令只能在已注册的来宾缓冲区与磁盘块范围内传输；P1 C-N09及D21已要求长度/地址/错误路径正确，C对象访问须有界。",
          "将64位寄存器地址强转paddr_t，再用guest_to_host取得无范围验证的指针；块数乘512后直接fread/fwrite，忽略fseek/传输结果，ready恒为1。",
          "当前DEVICE/HAS_DISK均开启；提供NAVY_HOME磁盘镜像后，来宾写cmd可令缓冲区起于PMEM末尾或高32位非零且blkcnt>0。读盘可越界写宿主内存，写盘可越界读并污染磁盘。",
          "先在64位地址域校验完整DMA区间、块数/文件偏移及乘法溢出，再映射host buffer；检查短I/O并公开错误状态。",
          "只有磁盘镜像成功打开时传输可达；本轮未执行破坏性盘写。与F0002的CPU物理地址截断共享宽度风险，但DMA缺少整段校验是独立根因。"),
    issue(10, "audio初始化回调检查了samples而非init寄存器偏移", "Medium",
          [("nemu/src/device/audio.c", [20, 27, 88, 93])],
          "写reg_init（index4、偏移16）后启动SDL音频；P1 C-N09设备寄存器契约。",
          "audio_io_handler仅在offset==8时检查reg_init，offset8实际是reg_samples。单独写init不会调用SDL_audio_init。",
          "当前HAS_AUDIO开启；正常guest依次设置频率/声道/样本数并写init时音频设备不启动；之后重写samples可能意外启动。",
          "按reg_init*4识别完整合法写入并记录初始化状态；失败时报告SDL错误。",
          "未进行主机声音人工观察；结论仅关于明确的偏移和调用可达性。"),
    issue(11, "audio回调欠载时只清零一个输出字节", "Medium",
          [("nemu/src/device/audio.c", [47, 68])],
          "SDL回调应写满提供的stream缓冲区，欠载尾部为静音；P1 C-N09和回调长度接口。",
          "循环变量为i，却反复执行stream[nread]=0；nread+1到len-1未写。",
          "当前HAS_AUDIO开启且初始化后，count<len时可把上次/未初始化样本交给宿主音频输出；nread=0时仅首字节被清零。",
          "按stream+i逐字节清零或对stream+nread做memset，并按SDL规定同步环形缓冲区状态。",
          "F0010可能使通常启动路径到不了回调；在修正偏移或其他路径启动后可达。本轮未运行音频线程。"),
    issue(12, "expression词法器缺少token数量和字符串边界检查", "Medium",
          [("nemu/src/monitor/sdb/expr.c", [83, 134, 252, 259])],
          "monitor表达式无论长度、空输入均应拒绝或有界解析；P1 C-N10及C11对象边界。",
          "tokens固定32项但nr_token无上界；32字符token允许写满str[32]无NUL，sscanf无宽度；expr(NULL)直接解引用，空串令eval(0,-1)。",
          "当前native monitor的p/w/x命令可传用户文本；33个单字符token或超长数字可写越界，p无参数可崩溃；错误表达式可污染watchpoint判据。",
          "token计数、每种拷贝宽度及NUL统一校验；空指针/空串先拒绝。",
          "静态确认边界缺失；未对原二进制输入模糊测试。"),
    issue(13, "watchpoint命令无界复制且耗尽后解引用空指针", "Medium",
          [("nemu/src/monitor/sdb/sdb.c", [124, 134]), ("nemu/src/monitor/sdb/watchpoint.c", [52, 69]), ("nemu/src/monitor/sdb/sdb.h", [23, 29])],
          "用户表达式应有界保存，32个watchpoint用尽应作为可恢复错误；P1 C-N10。",
          "sscanf(arg,\"%[^n]\",expr_str)无宽度且遇字母n截断；new_wp用尽返回NULL，cmd_w立即写wp->expr_value。",
          "native monitor启用w命令；超过127字节的有效表达式可越界写；创建第33项时崩溃，含n的表达式可记录错误文本。",
          "验证字符串长度并复制到128字节缓冲区，检查new_wp返回值，保存与首次求值相同的文本。",
          "WATCHPOINT当前.config关闭但w命令和池仍编译进native monitor；逐指令触发检测只在开关开启时。"),
    issue(14, "NEMU REF memcpy只验证首地址，未验证传输范围", "Medium",
          [("nemu/src/cpu/difftest/ref.c", [45, 61]), ("nemu/src/memory/paddr.c", [80, 85])],
          "NPC→NEMU REF内存复制须对每个已注册物理区域验证addr+n；D17 33字ABI与P1 C-N11/C-X02。",
          "addr_to_soc只按首地址选区域，随后int i与size_t n比较并逐字节访问；跨界会越界，n>INT_MAX循环变量溢出。",
          "已导出的difftest_memcpy可由NPC loader和测试调用；合法首地址加过大长度、负向/高地址可破坏REF宿主内存或读越界。",
          "在完整地址域验证整个区间和n，再用size_t循环；失败明确返回/终止，测试五种内存域的末尾与越界。",
          "现有m1_p9_ref.py仅测各域末尾的8字节有效访问；没有本轮跨界动态复现。"),
    issue(15, "NEMU DUT逐指令difftest只比较GPR，漏掉PC", "Medium",
          [("nemu/src/isa/riscv32/difftest/dut.c", [20, 26]), ("nemu/src/cpu/difftest/dut.c", [138, 143])],
          "golden应至少比较公开的33字GPR+PC，报告每次实际比较的字段；D17/P1 C-N11。",
          "Spike适配器提供PC，但isa_difftest_checkregs仅循环32个GPR，不读取ref_r->pc；日志中pc只是标签。CSR/priv也不在该ABI。",
          "开启NEMU→Spike DIFFTEST时，分支PC错误而GPR未变的指令可被判为一致；后续是否分歧取决于后续执行。",
          "比较ref.pc与cpu.pc，同时把未比较CSR/priv/内存及skip窗口列为显式限制。",
          "当前.config DIFFTEST关闭；这是选配golden路径的确定覆盖缺口，不声称现有测试已经误报PASS。"),
    issue(16, "multi-image启动只把firmware送入Spike参考内存", "Medium",
          [("nemu/src/monitor/monitor.c", [60, 95]), ("nemu/src/cpu/difftest/dut.c", [67, 97])],
          "同时使用--kernel/--dtb与--diff时，DUT及golden须接收同一组镜像，或拒绝该不受支持组合；P1 C-N02/C-N11与L08。",
          "load_img依次装载firmware/kernel/DTB，但只返回firmware大小；init_difftest仅从RESET_VECTOR复制返回的那段。",
          "native RV64 DEVICE及DIFFTEST组合可由参数触发；Spike缺kernel/DTB内容，后续对拍可因输入不一致失败或由skip掩盖，不能视为guest正确性结论。",
          "分别同步已装载镜像的地址与长度，或明确拒绝multi-image+diff；记录镜像哈希。",
          "未在本轮运行Spike/Linux对拍；这是输入同步事实，不推定实际运行到内核的结果。"),
    issue(17, "QEMU RV64 adapter的PC包布局和物理地址宽度不匹配", "Medium",
          [("nemu/tools/qemu-diff/include/isa.h", [26, 44]), ("nemu/tools/qemu-diff/include/common.h", [24, 28]), ("nemu/tools/qemu-diff/src/diff-test.c", [30, 46])],
          "若选择RV64 QEMU参考，33字GPR+PC复制须匹配GDB寄存器布局且64位地址不截断；P1 C-N11。",
          "RV64 union在32 GPR后插入32 FPR，PC位于第64字；通用regcpy仅memcpy前33字，错把FPR0当PC。适配器paddr_t固定uint32_t。",
          "Kconfig的QEMU RV64选项可选但当前选Spike；选QEMU后PC同步/读取错误，高物理地址参数截断。",
          "为RV64显式提取/写入GPR和PC，统一64位地址及GDB回复尺寸验证。",
          "未启动QEMU；具体GDB远端寄存器顺序仍需以所选QEMU版本动态核验。"),
    issue(18, "monitor load失败时已部分覆盖CPU和PMEM", "Medium",
          [("nemu/src/monitor/sdb/sdb.c", [173, 183])],
          "提示load失败时现有运行状态应保持或明确标记不可继续；P1 C-N10错误状态/所有权检查。",
          "先把CPU直接fread进活状态，再把PMEM直接fread进活内存，最后才检查两个返回值；短文件可留下部分新CPU/内存。",
          "native monitor执行load到截断/坏快照，随后仍可c继续执行混合状态；没有版本/配置/校验和校验。",
          "先读入临时完整快照并验证长度/格式、读写返回值，再原子替换活状态并重建必要外设/REF状态。",
          "当前快照仅CPU_state+PMEM，不包含设备、difftest/计时器状态；即使完整加载也不能宣称全机恢复。"),
    issue(19, "gen-expr工具生成空表达式，不能形成有效oracle", "Low",
          [("nemu/tools/gen-expr/gen-expr.c", [26, 64])],
          "表达式生成器若用于验证，应产生非空有效表达式并用独立宿主计算结果；P1 C-N12及计划§8 oracle要求。",
          "gen_rand_expr仅把buf[0]置NUL，生成的C代码为unsigned result = ;，gcc编译失败后continue，循环无测试行。",
          "调用工具不会产生有效的expr校验样例；若脚本只看进程退出0会把空验证误作通过。",
          "实现有界表达式生成并使零有效样例返回非零；比较器检查样例数量、源码、退出码。",
          "工具未在P3执行；结论来自当前源码，不作为expr行为的动态失败证据。"),
    issue(20, "SD卡寄存器回调忽略读写方向并可重放命令", "Medium",
          [("nemu/src/device/sdcard.c", [83, 112])],
          "SD命令只由写命令寄存器触发；数据端口按传输方向读或写，错误/EOF应反映状态；P1 C-N09。",
          "case SDCMD不检查is_write，读命令寄存器也执行sdcard_handle_cmd；SDDATA仅看write_cmd，读写均推进文件并忽略fread/fwrite结果。",
          "HAS_SDCARD可选但当前关闭；启用后guest读SDCMD可重放磁盘动作，反方向SDDATA访问也可推进文件位置或修改镜像。",
          "按寄存器及命令状态校验is_write/len；检查文件边界和返回值，失败写入可观察状态。",
          "当前native配置SD卡关闭；未运行Linux驱动/镜像，第三方集成驱动只审公开MMIO调用关系。"),
    issue(21, "FTRACE加载ELF缺少符号表尺寸校验", "Medium",
          [("nemu/src/monitor/monitor.c", [167, 180, 224, 255])],
          "可选-e输入即使无符号表或损坏也应拒绝，不得除零或用无效偏移污染调试结论；P1 C-N10。",
          "shoff/entsize/section边界未按文件长验证；若没有SYMTAB，symentsize保持0，symsize/symentsize除零；fseek/fread错误只打印并继续使用buf。",
          "CONFIG_FTRACE启用、-e指向无SYMTAB或截断ELF即可在启动阶段崩溃，函数名/范围也可能从错误字符串表读取。",
          "使用经校验的ELF64解析器或逐字段检查文件界限、表项大小、索引和读取结果；失败禁用trace并返回错误。",
          "当前FTRACE关闭；本轮没有加载非可信ELF动态测试。"),
    issue(22, "TARGET_AM镜像复制缺少目的PMEM容量检查", "Medium",
          [("nemu/src/monitor/monitor.c", [390, 421]), ("nemu/src/am-bin.S", [15, 22])],
          "AM bin_start..bin_end长度必须不超过从RESET_VECTOR起可用PMEM；P1 C-N02装载及D21有界访问原则。",
          "load_img计算bin长度后直接memcpy(guest_to_host(RESET_VECTOR),...,size)，没有边界/整数转换检查。",
          "选TARGET_AM且mainargs嵌入的bin大于配置MSIZE时，host复制越过PMEM；riscv64-am_defconfig的MSIZE为32MiB。",
          "在复制前验证RESET_VECTOR、size和剩余容量，并统一错误退出；构建阶段也可拒绝超大bin。",
          "AM平台自身启动/链接属于P4；本条仅审NEMU宿主装载，未构造大镜像。")
]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    write_json(OUT / "findings.json", ISSUES)
    existing = json.loads((CCR / "findings.json").read_text())
    assert len(existing) == 8 and [x["id"] for x in existing] == [f"CCR-F{i:04d}" for i in range(1, 9)]
    write_json(CCR / "findings.json", existing + ISSUES)

    markdown = (CCR / "FINDINGS.md").read_text()
    anchor = "\n<a id=\"ccr-p3-findings-20261017\"></a>\n"
    markdown = markdown.split(anchor)[0]
    markdown += anchor + "## CCR-P3 新增问题（静态确认）\n\n"
    markdown += "P2八项保持原编号；本节14项均是P3本次源码静态确认，未运行定向动态复现。完整结构化字段见[p3/findings.json](p3/findings.json)。\n\n"
    markdown += "| ID | 严重程度 | 问题 | 当前配置 |\n|---|---|---|---|\n"
    for x in ISSUES:
        cfg = "可选配置" if int(x["id"][-4:]) in (15, 16, 17, 20, 21, 22) else "当前路径"
        markdown += f'| [{x["id"]}](#{x["id"].lower()}) | {x["severity"]} | {x["title"]} | {cfg} |\n'
    for x in ISSUES:
        markdown += f'\n<a id="{x["id"].lower()}"></a>\n### {x["id"]} — {x["title"]}\n\n'
        markdown += f'- 严重程度/状态：{x["severity"]} / Confirmed；CCR-P3。\n'
        markdown += '- 位置：' + '；'.join(f'`{v["path"]}:{v["lines"][0]}`（SHA-256 `{v["sha256"]}`）' for v in x['locations']) + '。\n'
        for key, label in (("expected_contract_and_basis", "预期及依据"), ("actual_and_root_cause", "实际与根因"),
                           ("reachability_and_impact", "可达条件/影响"), ("validation", "本次验证"),
                           ("minimal_fix", "最小修复建议"), ("recommended_regression", "建议回归"),
                           ("unconfirmed_assumptions_and_limits", "限制")):
            markdown += f'- {label}：{x[key]}\n'
    (CCR / "FINDINGS.md").write_text(markdown)
    print(f"P3 findings: {len(ISSUES)}; total: {len(existing) + len(ISSUES)}")


if __name__ == "__main__":
    main()
