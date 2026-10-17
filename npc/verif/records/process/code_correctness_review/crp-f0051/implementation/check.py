#!/usr/bin/env python3
"""Bounded F0051 subprocess/publication checks; fake objects, no guest execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

p = argparse.ArgumentParser()
p.add_argument("source", type=Path)
p.add_argument("output", type=Path)
args = p.parse_args()
source = args.source.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
work = Path(tempfile.mkdtemp(prefix="crp-f0051-check-"))
arch = "riscv64-npc"
apps = ["kernels/hello", "benchmarks/microbench", "kernels/typing-game", "kernels/snake"]

def snapshot(root):
    return {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in root.rglob("*") if f.is_file()}

fake_body = "#!" + sys.executable + "\n" + '''
import json,os,sys
from pathlib import Path
tool=Path(sys.argv[0]).name; mode=os.environ['FAIL_MODE']
with open('tools.jsonl','a') as f: f.write(json.dumps([tool,*sys.argv[1:]])+'\\n')
if tool=='make':
    d=Path(sys.argv[sys.argv.index('-C')+1])
    if mode=='lib-make' and d.name=='am': sys.exit(7)
    if mode in ['app-make','first-failure','recovery-fail'] and d.name=='hello': sys.exit(7)
    if d.name in ['am','klib']:
        lib=d/'build'/f'{d.name}-riscv64-npc.a'
        lib.parent.mkdir(parents=True,exist_ok=True); lib.write_text('mock archive')
    sys.exit(0)
if tool=='test-nm':
    if mode=='nm': sys.exit(9)
    print('putch\\nhalt\\ntrm_init'); sys.exit(0)
step=1 if any(a.startswith('--prefix-symbols=') for a in sys.argv) else (2 if any(a.startswith('--redefine-syms=') for a in sys.argv) else 3)
obj=Path(sys.argv[-1]); obj.write_bytes(f'step{step}\\n'.encode()+obj.read_bytes())
target={'objcopy1':'hello','objcopy2':'microbench','objcopy3':'snake'}.get(mode)
if mode==f'objcopy{step}' and obj.parent.name==target: sys.exit(11)
'''

results = []
for mode in ["success", "repeat", "lib-make", "app-make", "nm", "objcopy1", "objcopy2",
             "objcopy3", "missing-copy", "empty", "missing-tool", "first-failure", "recovery"]:
    cwd = work / mode
    am = cwd / "mock/abstract-machine"
    for lib in ["am", "klib"]:
        d = am / lib / "build"
        d.mkdir(parents=True)
        if mode != "lib-make":
            (d / f"{lib}-{arch}.a").write_text("mock archive")
    for app in apps:
        if mode == "missing-copy" and app == apps[-1]:
            continue
        d = am.parent / "am-kernels" / app / "build" / arch
        d.mkdir(parents=True)
        if mode != "empty" or app != apps[-1]:
            (d / "input.o").write_text("mock input object")
    build = cwd / "build"
    published = build / arch
    published.mkdir(parents=True)
    mk = published / "am-apps.mk"
    if mode != "first-failure":
        old_obj = published / "am-apps/hello/orphan.o"
        old_obj.parent.mkdir(parents=True)
        old_obj.write_text("previous object")
        mk.write_text("SRCS += build/am-apps.c\nSRCS += am-apps/hello/orphan.o\n")
        (build / "am-apps.c").write_text("previous C")
    before = snapshot(build)
    shutil.copyfile(source, cwd / "generator.py")
    bins = cwd / "bin"
    bins.mkdir()
    fake = bins / "tool"
    fake.write_text(fake_body)
    fake.chmod(0o700)
    for tool in ["make", "test-nm", "test-objcopy"]:
        if mode != "missing-tool" or tool != "test-nm":
            (bins / tool).symlink_to(fake.name)

    def run(suffix, failure):
        cmd = [sys.executable, "generator.py", "ARCH=" + arch, "CROSS_COMPILE=test-"]
        proc = subprocess.run(cmd, cwd=cwd, env={**os.environ, "AM_HOME": str(am),
            "FAIL_MODE": failure, "PATH": str(bins)}, capture_output=True, text=True, timeout=20)
        (out / f"{mode}-{suffix}.stdout.txt").write_text(proc.stdout)
        (out / f"{mode}-{suffix}.stderr.txt").write_text(proc.stderr)
        return proc.returncode

    exits = []
    if mode == "recovery":
        exits.append(run("failure", "recovery-fail"))
        preserved = snapshot(build) == before and exits[-1] != 0
        exits.append(run("success", "success"))
    else:
        preserved = True
        exits.append(run("first", mode))
    normal = mode in ["success", "repeat", "recovery"]
    checks = {"exit": exits[-1] == 0 if normal else exits[-1] != 0}
    if normal:
        rows = [line.removeprefix("SRCS += ") for line in mk.read_text().splitlines()]
        objs = [x for x in rows if x.endswith(".o")]
        cs = [x for x in rows if x.endswith(".c")]
        checks.update({"four_objects_no_orphan": len(objs) == 4 and all("orphan" not in x for x in objs),
            "same_generation": len(cs) == 1 and "/gen-" in cs[0] and all(
                str((published / x).parent.parent) == str((cwd / cs[0]).parent) for x in objs),
            "paths_exist": all((published / x).is_file() for x in objs) and all((cwd / x).is_file() for x in cs),
            "legacy_preserved": all(snapshot(build).get(k) == v for k,v in before.items() if k != f"{arch}/am-apps.mk"),
            "recovery_failure_preserved": preserved})
        if mode == "repeat":
            first = snapshot(build)
            first_mk = mk.read_bytes()
            exits.append(run("second", "success"))
            checks["repeat_new_set_old_preserved"] = exits[-1] == 0 and mk.read_bytes() != first_mk and all(
                snapshot(build).get(k) == v for k,v in first.items() if k != f"{arch}/am-apps.mk")
    else:
        checks["old_set_unchanged_no_partial_files"] = snapshot(build) == before
        if mode == "first-failure":
            checks["no_first_publication"] = not mk.exists()
        if (cwd / "tools.jsonl").exists():
            calls = [json.loads(line) for line in (cwd / "tools.jsonl").read_text().splitlines()]
            expected = "make" if mode in ["lib-make", "app-make"] else ("test-nm" if mode == "nm" else "test-objcopy")
            if mode in ["lib-make", "app-make", "nm", "objcopy1", "objcopy2", "objcopy3"]:
                checks["stop_at_failed_tool"] = calls[-1][0] == expected
    if (cwd / "tools.jsonl").exists():
        shutil.copyfile(cwd / "tools.jsonl", out / f"{mode}.tools.jsonl")
    if mk.is_file():
        (out / f"{mode}.mk.txt").write_bytes(mk.read_bytes())
    results.append({"case": mode, "cwd": str(cwd), "exits": exits, "checks": checks, "pass": all(checks.values())})

data = {"scope": "host/fake, not guest validation", "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "workspace": str(work), "cases": results}
(out / "results.json").write_text(json.dumps(data, indent=2) + "\n")
print(json.dumps({"cases": len(results), "passed": sum(x["pass"] for x in results),
                  "failed": [x["case"] for x in results if not x["pass"]]}))
sys.exit(0 if all(x["pass"] for x in results) else 1)
