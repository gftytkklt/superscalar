#!/usr/bin/env python3
"""F0051 analysis only: copied generator + fake tools, never production make."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").exists())
OUT = HERE / "analysis-results.json"
if OUT.exists():
    raise SystemExit("Existing evidence: use a new evidence directory instead of overwriting")
WORK = Path(tempfile.mkdtemp(prefix="crp-f0051-analysis-"))
ARCH = "riscv64-npc"
APPS = ["kernels/hello", "benchmarks/microbench", "kernels/typing-game", "kernels/snake"]
SOURCE = ROOT / "rt/bsp/abstract-machine/integrate-am-apps.py"
cases = []

for mode in ["success", "make-fails", "nm-fails", "objcopy-fails", "last-copy-missing"]:
    cwd = WORK / mode
    am = cwd / "mock/abstract-machine"
    for lib in ["am", "klib"]:
        d = am / lib / "build"
        d.mkdir(parents=True)
        (d / f"{lib}-{ARCH}.a").write_bytes(b"fake archive\n")
    for app in APPS:
        if mode == "last-copy-missing" and app == APPS[-1]:
            continue
        d = am.parent / "am-kernels" / app / "build" / ARCH
        d.mkdir(parents=True)
        (d / "input.o").write_bytes(b"fake input object\n")
    published = cwd / "build" / ARCH
    old_obj = published / "am-apps/hello/previous.o"
    old_obj.parent.mkdir(parents=True)
    old_obj.write_bytes(b"previously published object\n")
    mk = published / "am-apps.mk"
    c = cwd / "build/am-apps.c"
    mk.write_text("SRCS += am-apps/hello/previous.o\nSRCS += build/am-apps.c\n")
    c.write_text("/* previous complete C */\n")
    before = {str(p.relative_to(cwd)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [mk, c, old_obj]}
    shutil.copy2(SOURCE, cwd / "integrate-am-apps.py")
    bin_dir = cwd / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "fake-tool"
    fake.write_text("#!" + sys.executable + "\n" + '''
from pathlib import Path
import os,sys,json
name=Path(sys.argv[0]).name
mode=os.environ['PROBE_MODE']
with open('tools.jsonl','a') as log:
    log.write(json.dumps({'tool':name,'argv':sys.argv[1:]})+'\\n')
if name=='make':
    sys.exit(7 if mode=='make-fails' else 0)
if name.endswith('nm'):
    if mode=='nm-fails': sys.exit(9)
    print('putch'); sys.exit(0)
obj=Path(sys.argv[-1])
if mode=='objcopy-fails':
    obj.write_bytes(b'partial-transform\\n'+obj.read_bytes())
    sys.exit(11)
sys.exit(0)
''')
    fake.chmod(0o700)
    for name in ["make", "probe-nm", "probe-objcopy"]:
        (bin_dir / name).symlink_to(fake.name)
    argv = [sys.executable, "integrate-am-apps.py", "ARCH=" + ARCH, "CROSS_COMPILE=probe-"]
    proc = subprocess.run(argv, cwd=cwd, env={**os.environ, "AM_HOME": str(am),
        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "PROBE_MODE": mode},
        capture_output=True, text=True, timeout=20)
    for label, value in [("stdout", proc.stdout), ("stderr", proc.stderr),
                         ("mk", mk.read_text()), ("c", c.read_text()),
                         ("tools.jsonl", (cwd / "tools.jsonl").read_text())]:
        (HERE / f"{mode}.{label}").write_text(value)
    cases.append({"case": mode, "cwd": str(cwd), "argv": argv, "exit": proc.returncode,
        "old_hashes": before, "after_hashes": {str(p.relative_to(cwd)):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in [mk, c, old_obj]},
        "mk_lists_previous_object": "previous.o" in mk.read_text(),
        "mk_app_object_lines": [x for x in mk.read_text().splitlines() if x.endswith(".o")],
        "partial_object_bytes": old_obj.read_text() if mode == "objcopy-fails" else None})

# Exercise the exact BSP Makefile, with only its AM include supplied by an inert stub.
# No production AM Makefile or platform rules are parsed or executed.
cwd = WORK / "consumer"
cwd.mkdir()
shutil.copy2(ROOT / "rt/bsp/abstract-machine/Makefile", cwd / "Makefile")
(cwd / "src").mkdir()
(cwd / "src/kernel.c").write_text("/* stub; never compiled */\n")
am = cwd / "mock-am"
am.mkdir()
(am / "Makefile").write_text('inspect:\n\t@echo "SRCS=$(SRCS)"\n')
published = cwd / "build" / ARCH
published.mkdir(parents=True)
mk = published / "am-apps.mk"
mk.write_text("SRCS += am-apps/hello/previous.o\nSRCS += build/am-apps.c\n")
for mode in ["mk-present", "mk-removed"]:
    if mode == "mk-removed":
        mk.unlink()
    argv = ["make", "--no-print-directory", "ARCH=" + ARCH, "inspect"]
    proc = subprocess.run(argv, cwd=cwd, env={**os.environ, "AM_HOME": str(am)},
                          capture_output=True, text=True, timeout=20)
    (HERE / f"consumer-{mode}.log").write_text(proc.stdout + proc.stderr)
    cases.append({"case": "consumer-" + mode, "cwd": str(cwd), "argv": argv,
                  "exit": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})

OUT.write_text(json.dumps({"scope": "host/fake analysis, no guest validation",
    "workspace": str(WORK), "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "cases": cases}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"workspace": str(WORK), "observations": [
    {"case": x["case"], "exit": x["exit"]} for x in cases]}))
