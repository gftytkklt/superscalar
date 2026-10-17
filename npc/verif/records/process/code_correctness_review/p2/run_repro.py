#!/usr/bin/env python3
"""Isolated CCR-P2 defect reproductions; never invokes project make or Git mutations."""
import hashlib
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, help='new evidence directory; existing manifest is rejected')
args = parser.parse_args()
OUT = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix='ccr-p2-evidence-'))
OUT.mkdir(parents=True, exist_ok=True)
if (OUT / 'repro-results.json').exists():
    raise SystemExit('Refusing to overwrite existing evidence; choose a new --output directory')
WORK = Path(tempfile.mkdtemp(prefix="ccr-p2-"))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
SOURCE = ["src/cpu/cpu-exec.c", "src/isa/riscv32/inst.c", "src/isa/riscv32/reg.c",
          "src/isa/riscv32/system/intr.c", "src/isa/riscv32/system/mmu.c",
          "src/memory/paddr.c", "src/memory/vaddr.c", "src/utils/state.c",
          "src/engine/interpreter/hostcall.c", "src/isa/riscv32/logo.c"]
records = []
def run(label, cmd, **kw):
    p = subprocess.run(cmd, cwd=WORK, text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=60, **kw)
    (OUT / (label + ".log")).write_text(p.stdout)
    records.append(dict(label=label, command=cmd, cwd=str(WORK), returncode=p.returncode,
                        log=label + ".log"))
    print(label, "exit", p.returncode, flush=True)
    return p

shutil.copytree(ROOT / "nemu/include", WORK / "include")
shutil.copytree(ROOT / "nemu/src/isa/riscv32/local-include", WORK / "local-include")
shutil.copytree(ROOT / "nemu/src/isa/riscv32/include", WORK / "isa-include")
for name in SOURCE:
    target = WORK / name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "nemu" / name, target)
# Preserve relative include paths used by the original translation units.
shutil.copytree(ROOT / "nemu/src/isa/riscv32/local-include", WORK / "src/isa/riscv32/local-include")
shutil.copy2(HERE / "repro.c", WORK / "repro.c")
run("compiler", ["/usr/bin/gcc", "--version"])
run("compiler-defaults", ["/usr/bin/gcc", "-dM", "-E", "-x", "c", "/dev/null"])
common = ["/usr/bin/gcc", "-O2", "-g", "-D__GUEST_ISA__=riscv64",
          "-Iinclude", "-Iisa-include", "-I."]
normal = run("build", common + ["repro.c"] + SOURCE + ["-o", "repro"])
if normal.returncode == 0:
    for name in ["jal", "jalr", "branch", "high-bare", "high-pt", "fencei", "inv-end"]:
        run(name, [str(WORK / "repro"), name])
san = run("build-ubsan", common + ["-fsanitize=undefined", "-fno-sanitize-recover=all",
                                  "repro.c"] + SOURCE + ["-o", "repro-ubsan"])
if san.returncode == 0:
    for name in ["addiw", "addw", "subw", "mul", "mulw", "sllw", "unaligned"]:
        run(name, [str(WORK / "repro-ubsan"), name])
config = WORK / "include/generated/autoconf.h"
original = config.read_text()
config.write_text(original.replace("#define CONFIG_PMEM_GARRAY 1", "#define CONFIG_PMEM_MALLOC 1"))
run("malloc-compile", common + ["-fsyntax-only", "src/memory/paddr.c"])
config.write_text(original)
config.write_text(original.replace('#define CONFIG_DEVICE 1', '/* DEVICE disabled for isolated REF CPU path */'))
nodevice = run('nodevice-build', common + ['repro.c'] + SOURCE + ['-o', 'repro-nodevice'])
if nodevice.returncode == 0:
    run('nodevice-inv-end', [str(WORK / 'repro-nodevice'), 'inv-end'])
config.write_text(original)
hashes = {name: hashlib.sha256((ROOT / "nemu" / name).read_bytes()).hexdigest() for name in SOURCE}
hashes["include/generated/autoconf.h"] = hashlib.sha256(config.read_bytes()).hexdigest()
manifest = dict(date="2026-10-17 Asia/Shanghai", work=str(WORK), sources=hashes,
                commands=records, production_edits=False, make_invoked=False,
                stubs="device_update/time/MMIO external inputs only; MMIO denied; CPU/ISA/MMU/memory original",
                binaries={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in [WORK / "repro", WORK / "repro-ubsan", WORK / 'repro-nodevice'] if p.exists()})
(OUT / "repro-results.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("isolated work:", WORK)
print('evidence:', OUT)
