#!/usr/bin/env python3
"""Build an isolated REF and verify the existing NPC PC/GPR contract.

Uses only installed tools and existing NPC/riscv-tests/cpu-tests binaries.
Never reconfigures native NEMU, rebuilds NPC, or invokes tracer commits.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
NEMU = ROOT / "nemu"
EXPORTS = ("memcpy", "regcpy", "exec", "raise_intr", "init", "ref_display")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_state():
    paths = [NEMU / ".config", NEMU / "build/riscv64-nemu-interpreter"]
    for directory in ("include/config", "include/generated"):
        paths.extend(p for p in (NEMU / directory).rglob("*") if p.is_file())
    paths.extend(p for p in (NEMU / ".config.old", ROOT / "npc/build/.build_cfg",
                             ROOT / "npc/build/ysyxSoCFull") if p.is_file())
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def command(args, log, cwd=ROOT, env=None, timeout=120):
    env = dict(os.environ if env is None else env, CCACHE_DISABLE="1")
    with log.open("w") as stream:
        stream.write("argv: " + json.dumps([str(a) for a in args]) + "\n")
        stream.flush()
        result = subprocess.run(args, cwd=cwd, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"exit {result.returncode}: {log}")


def build(out):
    # Copy only build inputs. In particular, do not copy tools/spike or old objects.
    with tempfile.TemporaryDirectory(prefix="source-", dir=out) as temporary:
        tree = Path(temporary)
        for name in ("src", "include", "scripts", "configs"):
            shutil.copytree(NEMU / name, tree / name, symlinks=True,
                            ignore=shutil.ignore_patterns("generated", "config")
                            if name == "include" else None)
        for name in ("Makefile", "Kconfig"):
            shutil.copy2(NEMU / name, tree / name)
        for name in ("kconfig", "fixdep"):
            shutil.copytree(NEMU / "tools" / name, tree / "tools" / name,
                            symlinks=True)
        shutil.copy2(NEMU / "tools/difftest.mk", tree / "tools/difftest.mk")
        env = dict(os.environ, NEMU_HOME=str(tree), CCACHE_DISABLE="1")
        command(["make", "-o", "compile_git", "riscv64-ref_defconfig"],
                out / "config.log", tree, env)
        config = (tree / ".config").read_text()
        assert "CONFIG_TARGET_SHARE=y\n" in config
        for name in ("DEVICE", "TARGET_NATIVE_ELF", "DIFFTEST", "TRACE"):
            assert f"CONFIG_{name}=y\n" not in config, name
        command(["make", "-o", "compile_git", "-j8", "app", "LIBS=-lreadline -ldl"],
                out / "build.log", tree, env)
        shutil.copy2(tree / ".config", out / "ref.config")
        shutil.copy2(tree / "include/generated/autoconf.h", out / "ref.autoconf.h")
        shutil.copy2(tree / "build/riscv64-nemu-interpreter-so", out / "ref.so")
    command(["readelf", "-h", out / "ref.so"], out / "elf.log")
    assert re.search(r"Type:\s+DYN", (out / "elf.log").read_text())
    command(["nm", "-D", "--defined-only", out / "ref.so"], out / "exports.log")
    for name in EXPORTS:
        assert "difftest_" + name in (out / "exports.log").read_text()


def abi_probe(ref):
    lib = C.CDLL(str(ref), mode=os.RTLD_NOW | os.RTLD_LOCAL)
    lib.difftest_memcpy.argtypes = [C.c_uint64, C.c_void_p, C.c_size_t, C.c_bool]
    lib.difftest_regcpy.argtypes = [C.c_void_p, C.c_bool, C.c_bool]
    lib.difftest_exec.argtypes = [C.c_uint64]
    lib.difftest_init.argtypes = [C.c_int]
    for name in EXPORTS:
        getattr(lib, "difftest_" + name).restype = None
    lib.difftest_init(0)
    # Both ends of every REF memory domain, including SoC SDRAM with DEVICE=n.
    for base, size in ((0x80000000, 0x8000000), (0x30000000, 0x1000000),
                       (0x0F000000, 0x2000), (0x20000000, 0x1000),
                       (0xA0000000, 0x8000000)):
        for address in (base, base + size - 8):
            sent = C.c_uint64(address ^ 0x123456789ABCDEF0)
            got = C.c_uint64()
            lib.difftest_memcpy(address, C.byref(sent), 8, True)
            lib.difftest_memcpy(address, C.byref(got), 8, False)
            assert got.value == sent.value, hex(address)

    class Packet(C.Structure):
        _fields_ = [("before", C.c_uint64), ("words", C.c_uint64 * 33),
                    ("after", C.c_uint64)]

    data = Packet()
    sentinel = 0xBCDEF0123456789A
    data.before = data.after = sentinel
    for i in range(32):
        data.words[i] = i * 0x123456789
    data.words[32] = 0x30000000
    expected = list(data.words)
    lib.difftest_regcpy(data.words, True, True)
    assert list(data.words) == expected
    for i in range(33):
        data.words[i] = sentinel
    lib.difftest_regcpy(data.words, False, False)  # PC only
    assert list(data.words[:32]) == [sentinel] * 32
    assert data.words[32] == expected[32]
    data.words[32] = sentinel
    lib.difftest_regcpy(data.words, False, True)  # GPR only
    assert list(data.words[:32]) == expected[:32] and data.words[32] == sentinel
    assert data.before == data.after == sentinel
    # Actual execution from flash: time is zero without DEVICE; ordinary RV64
    # operations still update the PC/GPR packet. No new priv/CSR fields in ABI.
    code = (C.c_uint32 * 3)(0xC0102573, 0x00700593, 0x00B50633)
    lib.difftest_memcpy(0x30000000, code, C.sizeof(code), True)
    data.words[:] = [0] * 32 + [0x30000000]
    lib.difftest_regcpy(data.words, True, True)
    lib.difftest_exec(3)
    lib.difftest_regcpy(data.words, False, True)
    lib.difftest_regcpy(data.words, False, False)
    assert data.words[0] == data.words[10] == 0
    assert data.words[11] == data.words[12] == 7 and data.words[32] == 0x3000000C
    assert data.before == data.after == sentinel
    print("ABI PASS: 33 words/selective copies/canaries, 5 memory domains, exec/time=0")


def simulate(binary, image, ref, log, fault=None, memory_test=False):
    env = dict(os.environ, SIM_END="200000000" if memory_test else "20000000", WAVE_ON="0")
    if fault:
        env["M1P9_FAULT"] = fault
    command([binary, image, ref], log, env=env, timeout=240 if memory_test else 120)
    text = re.sub(r"\x1b\[[0-9;]*m", "", log.read_text())
    assert "difftest: ON" in text, log
    if fault:
        needle = "pc does not match" if fault == "pc" else "reg t0 does not match"
        assert "DIFF ABORT" in text and needle in text, log
    else:
        assert "HIT GOOD TRAP" in text, log
        for needle in ("DIFF ABORT", "HIT BAD TRAP", "does not match", "reach SIM_END"):
            assert needle not in text, log


def regress(out):
    binary = ROOT / "npc/build/ysyxSoCFull"
    assert binary.is_file(), "Build the existing NPC DIFF=1 simulator first"
    isa = ROOT / "am-kernels/tests/riscv-tests/isa/npc"
    tests = sorted(list(isa.glob("rv64ui-p-*.bin")) + list(isa.glob("rv64um-p-*.bin")))
    assert len(tests) == 67, f"Expected the existing 67-case UI/UM suite, got {len(tests)}"
    skips = {}
    for line in (ROOT / "npc/verif/riscv_tests_skip.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, reason = line.split(maxsplit=1)
            skips[name] = reason
    rows = []
    for image in tests:
        name = image.stem
        if name in skips:
            rows.append({"test": name, "status": "SKIP", "reason": skips[name]})
            continue
        simulate(binary, image, out / "ref.so", out / (name + ".log"))
        rows.append({"test": name, "status": "PASS", "sha256": digest(image)})
        print(name + ": PASS", flush=True)
    for name in ("dummy", "add", "load-store", "mul-longlong", "div", "shift", "mem-test"):
        image = ROOT / f"am-kernels/tests/cpu-tests/build/{name}-riscv64-npc.bin"
        assert image.is_file(), image
        simulate(binary, image, out / "ref.so", out / ("cpu-" + name + ".log"),
                 memory_test=name == "mem-test")
        rows.append({"test": "cpu-" + name, "status": "PASS", "sha256": digest(image)})
        print("cpu-" + name + ": PASS", flush=True)
    # Forward to the real REF, corrupting only comparison output. A DIFF=0
    # binary or a vacuous test cannot pass these independent PC/GPR controls.
    wrapper = out / "fault.c"
    wrapper.write_text(r'''
#include <dlfcn.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <assert.h>
static void *handle;
static void *sym(const char *name) {
  if (!handle) handle = dlopen(REAL_REF, RTLD_NOW | RTLD_LOCAL);
  assert(handle); void *p = dlsym(handle, name); assert(p); return p;
}
void difftest_init(int p) { ((void(*)(int))sym("difftest_init"))(p); }
void difftest_memcpy(uint64_t a, void *b, size_t n, bool d) {
  ((void(*)(uint64_t,void*,size_t,bool))sym("difftest_memcpy"))(a,b,n,d);
}
void difftest_regcpy(void *b, bool d, bool g) {
  ((void(*)(void*,bool,bool))sym("difftest_regcpy"))(b,d,g);
  const char *fault = getenv("M1P9_FAULT");
  if (!d && fault && ((g && fault[0]=='g') || (!g && fault[0]=='p')))
    ((uint64_t*)b)[g ? 5 : 32] ^= 4;
}
void difftest_exec(uint64_t n) { ((void(*)(uint64_t))sym("difftest_exec"))(n); }
void difftest_raise_intr(uint64_t n) { ((void(*)(uint64_t))sym("difftest_raise_intr"))(n); }
void difftest_ref_display(void) { ((void(*)(void))sym("difftest_ref_display"))(); }
''')
    command(["gcc", "-shared", "-fPIC", "-Wall", "-Werror",
             '-DREAL_REF=' + json.dumps(str(out / "ref.so")), wrapper,
             "-ldl", "-o", out / "fault.so"], out / "fault-build.log")
    for fault in ("pc", "gpr"):
        simulate(binary, isa / "rv64ui-p-add.bin", out / "fault.so",
                 out / ("negative-" + fault + ".log"), fault)
        print("Negative control " + fault + ": detected DIFF ABORT", flush=True)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "npc/verif/build/m1p9-ref")
    parser.add_argument("--install", action="store_true", help="Back up and replace default REF after all checks pass")
    parser.add_argument("--abi", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.abi:
        abi_probe(args.abi.resolve())
        return
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "result.json").exists():
        raise RuntimeError("Use a fresh --out directory to preserve earlier results")
    before = native_state()
    result = {"status": "IN_PROGRESS", "head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), "native_before": before}
    try:
        build(out)
        command([sys.executable, Path(__file__), "--abi", out / "ref.so"], out / "abi.log")
        result["tests"] = regress(out)
        assert native_state() == before, "Native NEMU / NPC inputs changed"
        if args.install:
            destination = NEMU / "build/riscv64-nemu-interpreter-so"
            if destination.exists():
                shutil.copy2(destination, out / "previous-ref.so")
                result["previous_ref_sha256"] = digest(out / "previous-ref.so")
            shutil.copy2(out / "ref.so", destination)
            result["installed_ref"] = str(destination)
        result["status"] = "PASS"
    except Exception as error:
        result["status"] = "FAIL"
        result["error"] = str(error)
        raise
    finally:
        result["native_unchanged"] = native_state() == before
        result["artifacts"] = {str(p): digest(p) for p in
            (out / "ref.so", out / "ref.config", out / "ref.autoconf.h",
             ROOT / "npc/build/ysyxSoCFull") if p.is_file()}
        (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("M1-P9 REF: PASS; " + str(out / "result.json"))


if __name__ == "__main__":
    main()
