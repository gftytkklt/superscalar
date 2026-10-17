#!/usr/bin/env python3
"""Isolated CCR-F0015 regression. No project make, config edit or network.

Every binary case uses the repaired contract even for the before run: missed
PC-only mismatches return nonzero, rather than being reclassified as passes.
The before summary separately verifies the exact expected failure witnesses.
Outputs must be new directories; snapshots and old evidence are never replaced.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
ISA = "nemu/src/isa/riscv32/difftest/dut.c"
CHAIN = "nemu/src/cpu/difftest/dut.c"
CASES = ["abi", "equal", "pc-low", "pc-high", "pc-gpr"] + [
    f"gpr-{i:02d}" for i in range(32)
] + ["step-equal", "step-pc-low", "step-pc-high", "skip-ref", "skip-dut", "detach-attach"]
BASELINE_FAILURES = {"pc-low", "pc-high", "step-pc-low", "step-pc-high",
                     "skip-ref", "skip-dut", "detach-attach"}
REG_NAMES = ["$0", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
             "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",
             "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11",
             "t3", "t4", "t5", "t6"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def snapshot(out):
    paths = list((ROOT / "nemu/include").rglob("*.h")) + [
        ROOT / p for p in [ISA, CHAIN, "nemu/src/isa/riscv32/include/isa-def.h",
                          "nemu/src/isa/riscv32/local-include/reg.h", "nemu/.config",
                          "nemu/tools/spike-diff/difftest.cc", "nemu/src/isa/riscv32/reg.c"]
    ] + [HERE / "harness.c", Path(__file__).resolve()]
    entries = []
    for source in sorted(set(paths)):
        rel = source.relative_to(ROOT)
        target = out / "source" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        entries.append({"path": str(rel), "sha256": digest(source.read_bytes()),
                        "mode": oct(stat.S_IMODE(source.stat().st_mode))})
    write_json(out / "inputs.json", entries)
    # Only enable DIFFTEST in a separate generated-header overlay.
    generated = out / "overlay/generated/autoconf.h"
    generated.parent.mkdir(parents=True)
    original = (out / "source/nemu/include/generated/autoconf.h").read_text()
    assert "#define CONFIG_DIFFTEST " not in original
    assert "#define CONFIG_RV64 1" in original and "#define CONFIG_ISA64 1" in original
    generated.write_text(original + "\n/* CRP-F0015 isolated test only. */\n#define CONFIG_DIFFTEST 1\n")
    return entries


def command(out, name, argv, commands):
    result = subprocess.run(argv, cwd=out, capture_output=True, timeout=60)
    (out / f"{name}.stdout").write_bytes(result.stdout)
    (out / f"{name}.stderr").write_bytes(result.stderr)
    commands.append({"name": name, "argv": argv, "cwd": str(out),
                     "exit_code": result.returncode,
                     "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr)})
    write_json(out / "commands.json", commands)
    return result


def diagnostics(name, stdout):
    if name == "pc-gpr":
        return "pc is different" in stdout and "t2 is different" in stdout
    if name.startswith("gpr-"):
        return REG_NAMES[int(name[4:])] + " is different" in stdout
    if name in {"pc-low", "pc-high", "step-pc-low", "step-pc-high", "skip-ref",
                "skip-dut", "detach-attach"}:
        return ("pc is different" in stdout and "right = 0x" in stdout
                and "wrong = 0x0000000180000104" in stdout) if name != "skip-dut" else (
                    "gp is different" in stdout and "pc is different" in stdout)
    return " is different" not in stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=["before", "after"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cc", default="/usr/bin/gcc")
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    try:
        entries = snapshot(out)
        cc = shutil.which(args.cc)
        if not cc:
            raise RuntimeError(f"compiler unavailable: {args.cc}")
        version = command(out, "compiler-version", [cc, "--version"], commands)
        if version.returncode:
            raise RuntimeError("compiler version command failed")
        write_json(out / "environment.json", {
            "python": sys.version, "compiler": cc,
            "head": subprocess.check_output(["git", "--no-optional-locks", "-C", str(ROOT),
                                             "rev-parse", "HEAD"], text=True).strip(),
            "stage": args.stage, "case_list": CASES,
            "config_delta": "overlay adds only CONFIG_DIFFTEST=1",
            "scope": "host local; REF execution/transport and RAM contents are stubs",
        })
        src = out / "source"
        common = [cc, "-std=gnu11", "-O2", "-g", "-Wall", "-Wextra",
                  "-fsanitize=undefined", "-fno-sanitize-recover=all",
                  "-D__GUEST_ISA__=riscv64", "-I" + str(out / "overlay"),
                  "-I" + str(src / "nemu/include"),
                  "-I" + str(src / "nemu/src/isa/riscv32/include")]
        sources = [src / ISA, src / CHAIN, src / (HERE / "harness.c").relative_to(ROOT)]
        objects = []
        for i, source in enumerate(sources):
            obj = out / f"unit-{i}.o"
            result = command(out, f"compile-{i}", common + ["-c", str(source), "-o", str(obj)], commands)
            if result.returncode:
                raise RuntimeError(f"compile-{i} failed")
            objects.append(str(obj))
        binary = out / "f0015-test"
        result = command(out, "link", [cc, "-fsanitize=undefined", *objects, "-ldl", "-o", str(binary)], commands)
        if result.returncode:
            raise RuntimeError("link failed")
        results = []
        for name in CASES:
            result = command(out, name, [str(binary), name], commands)
            stdout = result.stdout.decode(errors="replace")
            passed = (result.returncode == 0 and stdout.count(f"CASE_PASS {name}\n") == 1
                      and not result.stderr and (args.stage == "before" or diagnostics(name, stdout)))
            results.append({"case": name, "exit_code": result.returncode, "pass": passed,
                            "diagnostics_ok": diagnostics(name, stdout)})
        failed = {x["case"] for x in results if not x["pass"]}
        # Original files/config must remain byte-identical during the isolated run.
        unchanged = all(digest((ROOT / x["path"]).read_bytes()) == x["sha256"]
                        and oct(stat.S_IMODE((ROOT / x["path"]).stat().st_mode)) == x["mode"]
                        for x in entries)
        complete = (len(results) == len(CASES) == 43 and len(set(CASES)) == 43)
        witnesses = args.stage == "before" and failed == BASELINE_FAILURES and all(
            x["exit_code"] == 1 for x in results if x["case"] in BASELINE_FAILURES)
        success = not failed and complete and unchanged
        summary = {"stage": args.stage, "result": "PASS" if success else "FAIL",
                   "expected_count": len(CASES), "executed_count": len(results),
                   "passed": sum(x["pass"] for x in results), "failed": sorted(failed),
                   "baseline_witnesses_confirmed": witnesses,
                   "input_bytes_and_modes_unchanged": unchanged, "results": results}
        write_json(out / "summary.json", summary)
        write_json(out / "artifacts.json", {str(p.relative_to(out)): digest(p.read_bytes())
                                             for p in sorted(out.rglob("*")) if p.is_file()})
        print(json.dumps({k: v for k, v in summary.items() if k != "results"}, ensure_ascii=False))
        return 0 if success else 1
    except Exception as exc:
        write_json(out / "error.json", {"error": str(exc), "type": type(exc).__name__})
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
