#!/usr/bin/env python3
"""Observe legacy AM programs; a timeout alone is never a passing result."""
from pathlib import Path
import os
import subprocess
import time
root = Path(__file__).resolve().parents[2]
out = root / 'npc/verif/build/m1p8-tests'
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
cases = [
    ('rtc', 'npc/verif/build/m1p8-tests/am-rtc.bin',
     lambda s: '1 second).' in s and '2 seconds).' in s),
    ('intr', 'am-kernels/tests/am-tests/build/amtest-riscv64-nemu.bin',
     lambda s: 'Hello, AM World' in s and s.split('t = timer, d = device, y = yield', 1)[-1].count('t') >= 3 and s.split('t = timer, d = device, y = yield', 1)[-1].count('y') >= 3),
    ('threads', 'am-kernels/kernels/thread-os/build/thread-os-riscv64-nemu.bin',
     lambda s: all(f'Thread-{letter}' in s for letter in 'ABCDE')),
    ('yield', 'am-kernels/kernels/yield-os/build/yield-os-riscv64-nemu.bin',
     lambda s: 'ABAB' in s),
    ('nanos', 'nanos-lite/build/nanos-lite-riscv64-nemu.bin',
     lambda s: 'Hello World from Navy-apps for the' in s and 'Initializing processes' in s),
]
for name, image, check in cases:
    log = out / f'am-{name}.log'
    with log.open('wb') as stream:
        p = subprocess.Popen([str(root/'nemu/build/riscv64-nemu-interpreter'), '-b',
                              '--timer-source=legacy', str(root/image)],
                             stdout=stream, stderr=subprocess.STDOUT, env=env)
        try:
            until = time.monotonic() + 10
            while time.monotonic() < until:
                text = log.read_bytes().decode(errors='replace')
                if check(text):
                    print(f'AM {name}: observable assertions PASS', flush=True)
                    break
                if p.poll() is not None:
                    raise RuntimeError(f'{name} exited {p.returncode}: {log}')
                time.sleep(0.05)
            else:
                raise TimeoutError(f'{name} observable assertion missing: {log}')
        finally:
            if p.poll() is None:
                p.terminate()
                p.wait(timeout=5)
