#!/usr/bin/env python3
# ============================================================================
# B4 R-2: riscv-tests env 本地适配（幂等）——改写 env/p/riscv_test.h
#   1) 结束约定改为项目统一方式（同 cpu-tests）：ebreak + a0 退出码
#      （RVTEST_PASS: a0=0；RVTEST_FAIL: a0=(testnum<<1)|1；未处理异常 a0=1）
#      这样 NEMU（nemu_trap）与 NPC（probe.cpp sim_end）都能直接判 GOOD/BAD TRAP；
#   2) RVTEST_ADAPTED（nemu/npc 均定义）：跳过上游 env 的多 hart/PMP/NMI/delegation
#      初始化 —— 本项目核与 difftest REF(NEMU) 只实现 CSR 子集
#      （mepc/mstatus/mcause/mtvec/satp/mscratch），否则 NEMU 会 panic；
#      RVTEST_GET_HARTID 适配为 li a0,0（单 hart）。
#   3) NPC 目标（-DRVTEST_NPC）在 reset_vector 增加 .data LMA->VMA 拷贝与栈指针设置
#      （对齐 AM linker-soc 布局：text 在 flash 0x30000000、data/bss/stack 在 SRAM）。
# 用法：python3 riscv_tests_patch_env.py <riscv-tests 根目录>
# ============================================================================
import os
import sys

MARK = "B4 适配（R-2）"
ANCHOR = "#define RVTEST_CODE_BEGIN"

ADAPTED_BLOCK = """// B4 适配（R-2/RVTEST_ADAPTED）：本项目核与 difftest REF(NEMU) 仅实现 CSR 子集
// （mepc/mstatus/mcause/mtvec/satp/mscratch），跳过上游 env 的多 hart/PMP/NMI/delegation
// 初始化（否则 NEMU panic、NPC 空写）；单 hart 下 mhartid 视为 0。
#ifdef RVTEST_ADAPTED
#undef INIT_PMP
#define INIT_PMP
#undef INIT_RNMI
#define INIT_RNMI
#undef DELEGATE_NO_TRAPS
#define DELEGATE_NO_TRAPS
#undef RISCV_MULTICORE_DISABLE
#define RISCV_MULTICORE_DISABLE
#define RVTEST_GET_HARTID li a0, 0
#define RVTEST_FENCE
// 本核无特权级（M-only）：强制 mret 回到 M 模式（MPP=M），
// 否则 RVTEST_RV64U 会以 U 模式运行、ecall cause=8 与核的 11 不一致。
#define RVTEST_MSTATUS_INIT li t0, MSTATUS_MPP; csrs mstatus, t0
#else
#define RVTEST_GET_HARTID csrr a0, mhartid
#define RVTEST_FENCE fence
#define RVTEST_MSTATUS_INIT csrwi mstatus, 0
#endif

"""

NPC_INIT = """// B4 适配（R-2）：NPC 目标下 .data 需从 flash LMA 拷到 SRAM VMA（同 AM linker-soc 布局），
// 并设置栈指针；非 NPC 目标为空（NEMU/上游 link.ld 为连续加载，无需搬运）。
#ifdef RVTEST_NPC
#define RVTEST_NPC_INIT                                                 \\
        la t0, _sidata;                                                 \\
        la t1, _sdata;                                                  \\
        la t2, _edata;                                                  \\
 88:    bgeu t1, t2, 89f;                                              \\
        ld t3, 0(t0);                                                   \\
        sd t3, 0(t1);                                                   \\
        addi t0, t0, 8;                                                 \\
        addi t1, t1, 8;                                                 \\
        j 88b;                                                          \\
 89:    la t0, _bss_start;                                              \\
        la t1, _bss_end;                                                \\
 90:    bgeu t0, t1, 91f;                                              \\
        sd zero, 0(t0);                                                 \\
        addi t0, t0, 8;                                                 \\
        j 90b;                                                          \\
 91:    la sp, _stack_pointer;
#else
#define RVTEST_NPC_INIT
#endif

"""

OLD_TRAP = """  other_exception:                                                      \\
        /* some unhandlable exception occurred */                       \\
  1:    ori TESTNUM, TESTNUM, 1337;                                     \\
  write_tohost:                                                         \\
        sw TESTNUM, tohost, t5;                                         \\
        sw zero, tohost + 4, t5;                                        \\
        j write_tohost;                                                 \\"""

NEW_TRAP = """  other_exception:                                                      \\
        /* B4: unhandled exception -> BAD TRAP (a0=1) */                \\
  1:    ori TESTNUM, TESTNUM, 1337;                                     \\
        li a0, 1;                                                       \\
  write_tohost:                                                         \\
        /* B4: 项目统一结束约定（同 cpu-tests）：ebreak + a0 退出码      \\
           （RVTEST_PASS: a0=0；RVTEST_FAIL: a0=(testnum<<1)|1） */      \\
        ebreak;                                                         \\
        j write_tohost;                                                 \\"""

OLD_RESET = """        la t0, trap_vector;                                             \\
        csrw mtvec, t0;                                                 \\
        CHECK_XLEN;                                                     \\"""

NEW_RESET = """        la t0, trap_vector;                                             \\
        csrw mtvec, t0;                                                 \\
        RVTEST_NPC_INIT;                                                \\
        CHECK_XLEN;                                                     \\"""

OLD_HARTID = """        csrw mepc, t0;                                                  \\
        csrr a0, mhartid;                                               \\
        mret;                                                           \\"""

NEW_HARTID = """        csrw mepc, t0;                                                  \\
        RVTEST_GET_HARTID;                                              \\
        mret;                                                           \\"""

# NEMU（本题的 REF/原生解释器）未实现 fence（funct3=000），仅 fence.i；
# PASS/FAIL 宏开头的 fence 统一改为 RVTEST_FENCE（适配目标为空）。
OLD_PASS = """#define RVTEST_PASS                                                     \\
        fence;                                                          \\"""

NEW_PASS = """#define RVTEST_PASS                                                     \\
        RVTEST_FENCE;                                                   \\"""

OLD_FAIL = """#define RVTEST_FAIL                                                     \\
        fence;                                                          \\"""

NEW_FAIL = """#define RVTEST_FAIL                                                     \\
        RVTEST_FENCE;                                                   \\"""

OLD_MSTATUS = """1:      csrwi mstatus, 0;                                               \\"""

NEW_MSTATUS = """1:      RVTEST_MSTATUS_INIT;                                            \\"""


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    path = os.path.join(root, "env/p/riscv_test.h")
    src = open(path, encoding="utf-8").read()
    if MARK in src:
        print(f"[patch_env] 已是适配版本，跳过：{path}")
        return 0
    for name, old in (("RVTEST_CODE_BEGIN", ANCHOR), ("trap", OLD_TRAP),
                      ("reset_vector", OLD_RESET), ("mhartid", OLD_HARTID),
                      ("RVTEST_PASS", OLD_PASS), ("RVTEST_FAIL", OLD_FAIL),
                      ("mstatus", OLD_MSTATUS)):
        if src.count(old) != 1:
            print(f"[patch_env] 未找到唯一匹配点（{name}，count={src.count(old)}）：{path}")
            return 1
    src = src.replace(ANCHOR, ADAPTED_BLOCK + NPC_INIT + ANCHOR, 1)
    src = src.replace(OLD_TRAP, NEW_TRAP, 1)
    src = src.replace(OLD_RESET, NEW_RESET, 1)
    src = src.replace(OLD_HARTID, NEW_HARTID, 1)
    src = src.replace(OLD_PASS, NEW_PASS, 1)
    src = src.replace(OLD_FAIL, NEW_FAIL, 1)
    src = src.replace(OLD_MSTATUS, NEW_MSTATUS, 1)
    open(path, "w", encoding="utf-8").write(src)
    print(f"[patch_env] 已适配：{path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
