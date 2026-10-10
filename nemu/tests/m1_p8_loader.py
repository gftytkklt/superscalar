#!/usr/bin/env python3
"""Exercise actual monitor argument/file checks; sparse negative images only."""
from pathlib import Path
import os
import subprocess
import tempfile
root = Path(__file__).resolve().parents[2]
binary = root / 'nemu/build/riscv64-nemu-interpreter'
env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
out = root / 'npc/verif/build/m1p8-tests'
out.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='m1p8-loader-') as temp:
    temp = Path(temp)
    sizes = {'empty': 0, 'one': 4, 'firmware-big': 0x200001,
             'kernel-big': 0x2000001, 'dtb-big': 0x5e00001}
    for name, size in sizes.items():
        with (temp/name).open('wb') as stream:
            stream.truncate(size)
    one = str(temp/'one')
    cases = [
        (['--kernel='+one, one], 'require each other'),
        (['--kernel='+one, '--dtb='+one], 'require each other'),
        (['--timer-source=invalid', one], 'Invalid timer source'),
        (['--serial-input=/dev/null', one], 'ordinary file or FIFO'),
    ]
    for name in ['empty', 'firmware-big', 'kernel-big', 'dtb-big']:
        fw = str(temp/name) if name in ['empty', 'firmware-big'] else one
        kernel = str(temp/name) if name == 'kernel-big' else one
        dtb = str(temp/name) if name == 'dtb-big' else one
        cases.append(([f'--kernel={kernel}', f'--dtb={dtb}', fw], 'Image out of range'))
    for index, (args, expected) in enumerate(cases):
        p = subprocess.run([str(binary), '-b', *args], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=10)
        (out/f'loader-{index}.log').write_bytes(p.stdout)
        assert p.returncode != 0 and expected.encode() in p.stdout, (index, p.returncode)
print(f'Monitor loader/source/input rejection: {len(cases)} cases PASS')
