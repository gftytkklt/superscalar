#!/usr/bin/env python3
# npc 仿真配置菜单（make menuconfig → 写 npc/.npc_config）
#
# 生成一个 makefile 片段：DIFF/WAVE/WITH_TRACE/WITH_SDL（0/1）、BOOT_MODE、HEAP_SIZE。
# 命令行传参（make WAVE=1 ...）优先于本配置（make 内建优先级），故本文件只是"持久默认"。
#
# 用法：
#   make menuconfig                  # 交互菜单（数字切换/编辑，s 保存，q 退出）
#   python3 menuconfig.py --list     # 打印当前配置
#   python3 menuconfig.py --set DIFF=1 WAVE=1   # 批量设置（脚本化/测试用）
import sys, os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".npc_config")
CONFIG_PATH = os.path.abspath(CONFIG_PATH)

# 布尔开关（0/1）
BOOLS = [
    ("DIFF",       "difftest 逐指令对拍（NEMU）"),
    ("WAVE",       "Verilator trace 波形支持"),
    ("WITH_TRACE", "Verilator --trace 编译（纯性能可关）"),
    ("WITH_SDL",   "NVBoard 虚拟板卡接入"),
]
# 启动模式（BOOT_MODE → LDS/BOOT_S 固定搭配，见 npc.mk 绑定表）
BOOT_MODES = [
    ("xip",        "flash 直启，堆在 PSRAM（linker-soc.ld + start.S）"),
    ("sram",       "整程序搬 SRAM（linker-sram.ld + start_sram.S）"),
    ("psram",      "整程序搬 PSRAM（linker-psram.ld + start_sram.S）"),
    ("psram-ssbl", "FSBL+SSBL 二级加载（linker-psram-ssbl.ld + start_fsbl.S）"),
    ("sdram",      "整程序搬 SDRAM（linker-sdram.ld + start_sram.S）"),
    ("sdram-heap", "flash XIP + 堆在 SDRAM（linker-sdram-heap.ld + start.S）"),
]
HEAP_DEFAULT = "0x8000"

def read_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        for line in open(CONFIG_PATH):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            cfg[k.strip()] = v.strip()
    return cfg

def write_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        f.write("# npc 仿真配置（由 make menuconfig 生成；命令行传参可覆盖，如 make WAVE=1）\n")
        f.write("# BOOT_MODE → (LDS, BOOT_S) 绑定见 abstract-machine/scripts/platform/npc.mk\n")
        for k, _ in BOOLS:
            f.write(f"{k} = {cfg.get(k, '0')}\n")
        f.write(f"BOOT_MODE = {cfg.get('BOOT_MODE', 'xip')}\n")
        f.write(f"HEAP_SIZE = {cfg.get('HEAP_SIZE', HEAP_DEFAULT)}\n")
    print(f"[menuconfig] 已保存 {CONFIG_PATH}")

def norm_bool(v):
    return "1" if str(v).lower() in ("1", "y", "yes", "on") else "0"

def parse_argv_set(args):
    """--set KEY=VALUE [KEY=VALUE...]：批量设置（脚本化/测试用）。"""
    cfg = read_config()
    for item in args:
        if "=" not in item:
            print(f"[menuconfig] 忽略非法项: {item}")
            continue
        k, v = item.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in [b[0] for b in BOOLS]:
            cfg[k] = norm_bool(v)
        elif k == "BOOT_MODE":
            if v in [m[0] for m in BOOT_MODES]:
                cfg[k] = v
            else:
                print(f"[menuconfig] 未知 BOOT_MODE: {v}（可选: {', '.join(m[0] for m in BOOT_MODES)}）")
        elif k == "HEAP_SIZE":
            cfg[k] = v
        else:
            print(f"[menuconfig] 未知键: {k}")
    write_config(cfg)
    return 0

def print_current(cfg):
    print("当前 npc 仿真配置 (.npc_config):")
    for k, desc in BOOLS:
        print(f"  {k:11s}= {cfg.get(k, '0')}   ({desc})")
    print(f"  BOOT_MODE   = {cfg.get('BOOT_MODE', 'xip')}")
    print(f"  HEAP_SIZE   = {cfg.get('HEAP_SIZE', HEAP_DEFAULT)}")

def interactive():
    cfg = read_config()
    for k, _ in BOOLS:
        cfg.setdefault(k, "0")
    cfg.setdefault("BOOT_MODE", "xip")
    cfg.setdefault("HEAP_SIZE", HEAP_DEFAULT)

    while True:
        if sys.stdout.isatty():
            os.system("clear")
        print("=" * 62)
        print("  npc 仿真配置  (make menuconfig)")
        print("=" * 62)
        for i, (k, desc) in enumerate(BOOLS, 1):
            mark = "[x]" if norm_bool(cfg.get(k, "0")) == "1" else "[ ]"
            print(f"  {i}) {mark} {k:11s} {desc}")
        print(f"  5) BOOT_MODE = {cfg['BOOT_MODE']}")
        for m, d in BOOT_MODES:
            sel = " *" if m == cfg["BOOT_MODE"] else "  "
            print(f"        {sel}{m:11s} {d}")
        print(f"  6) HEAP_SIZE = {cfg['HEAP_SIZE']}")
        print("-" * 62)
        print("  (s) 保存并退出   (q) 不保存退出   (数字) 切换/编辑")
        print("-" * 62)
        try:
            key = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n[menuconfig] 未保存，退出")
            return 1
        if key == "s":
            write_config(cfg)
            return 0
        if key == "q":
            print("[menuconfig] 未保存，退出")
            return 0
        if key in ("1", "2", "3", "4"):
            k = BOOLS[int(key) - 1][0]
            cfg[k] = "0" if norm_bool(cfg.get(k, "0")) == "1" else "1"
        elif key == "5":
            try:
                choice = input(f"选择启动模式 ({'/'.join(m[0] for m in BOOT_MODES)}): ").strip()
            except EOFError:
                continue
            if choice in [m[0] for m in BOOT_MODES]:
                cfg["BOOT_MODE"] = choice
            else:
                print(f"[menuconfig] 未知: {choice}")
                input("回车继续...")
        elif key == "6":
            try:
                v = input(f"堆区大小 (如 0x8000 / 0x400000): ").strip()
            except EOFError:
                continue
            if v:
                cfg["HEAP_SIZE"] = v

def main():
    args = sys.argv[1:]
    if args and args[0] == "--list":
        print_current(read_config())
        return 0
    if args and args[0] == "--set":
        return parse_argv_set(args[1:])
    return interactive()

if __name__ == "__main__":
    sys.exit(main())