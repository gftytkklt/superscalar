#!/usr/bin/env python3
"""Run the existing RT -> AM -> NPC path in the prepared isolated fixture."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

here = Path(__file__).resolve().parent
fixture = json.loads((here / "guest-fixture-final.json").read_text())
result = here / "guest-run-result.json"
if result.exists():
    raise SystemExit("Existing guest evidence; do not overwrite")
argv = ["make", "--no-print-directory", "-j4", "-o", "build/ysyxSoCFull",
        "ARCH=riscv64-npc", "DIFF=1", "WAVE=0", "WITH_TRACE=0", "WITH_SDL=0",
        "PERF=1", "PERF_R45=1", "git_commit=",
        "MAKE=/usr/bin/make -o build/ysyxSoCFull", "run"]
log_path = here / "guest-run.log"
start = time.time()
with log_path.open("wb") as log:
    proc = subprocess.Popen(argv, cwd=fixture["rt_cwd"], env={**os.environ, **fixture["env"]},
                            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
(here / "guest-run-process.json").write_text(json.dumps({"pid": proc.pid, "argv": argv,
    "cwd": fixture["rt_cwd"], "start": start}, indent=2) + "\n")
stop = "process-exit"
observed = []
while proc.poll() is None:
    data = log_path.read_text(errors="replace")
    # These strings are guest output, not source listing or make target names.
    if any(x in data for x in ["DIFF ABORT", "does not match!", "HIT BAD TRAP", "Assertion failed"]):
        stop = "guest-failure"
        break
    if re.search(r"msh[^\r\n>]*>", data):
        observed.append("msh prompt")
        # Give the existing preset am_hello a chance to run as extra evidence.
        if "Hello, AbstractMachine!" in data:
            observed.append("integrated am_hello output")
            stop = "guest-markers-reached"
            break
    if time.time() - start > 180:
        stop = "wall-timeout"
        break
    time.sleep(0.5)
if proc.poll() is None:
    os.killpg(proc.pid, signal.SIGTERM)
try:
    rc = proc.wait(timeout=10)
except subprocess.TimeoutExpired:
    os.killpg(proc.pid, signal.SIGKILL)
    rc = proc.wait()
data = log_path.read_text(errors="replace")
images = Path(fixture["rt_cwd"]) / "build"
artifacts = {p.name: {"bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in images.glob("rtthread-riscv64-npc.*") if p.is_file()}
payload = {"argv": argv, "cwd": fixture["rt_cwd"], "exit": rc,
    "stop_reason": stop, "elapsed_seconds": time.time() - start,
    "msh_reached": bool(re.search(r"msh[^\r\n>]*>", data)),
    "am_hello_output": "Hello, AbstractMachine!" in data,
    "difftest_on": bool(re.search(r"difftest:.*ON", data)),
    "observed": list(dict.fromkeys(observed)), "artifacts": artifacts,
    "generator_sha256": fixture["generator_sha256"]}
result.write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload), flush=True)
