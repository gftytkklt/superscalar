#!/usr/bin/env python3
"""Bounded native boot, FIFO input, and actual shell-output assertions."""
import argparse
import hashlib
import shutil
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
p = argparse.ArgumentParser()
p.add_argument('--out', type=Path, default=root / 'npc/verif/build/linux-boot/nemu-p8')
p.add_argument('--timeout', type=float, default=180, help='automatic boot/shell timeout (seconds)')
p.add_argument('--interactive', action='store_true', help='keep a live serial terminal; Ctrl+C/Ctrl+] exit NEMU; no automatic timeout')
a = p.parse_args()
if a.interactive and not sys.stdin.isatty():
    p.error('--interactive requires a terminal on stdin')
out = a.out.resolve()
out.mkdir(parents=True, exist_ok=True)
if not a.interactive:
    (out / 'result.json').unlink(missing_ok=True)
firmware = out / 'opensbi/platform/generic/firmware/fw_jump.bin'
kernel = root / 'npc/verif/build/linux-kernel/nemu-p8/arch/riscv/boot/Image'
dtb = root / 'npc/verif/build/linux-dtb/nemu/nemu.dtb'
elf = firmware.with_suffix('.elf')
# Check firmware memory footprint, including BSS, independently of flat .bin size.
headers = subprocess.check_output(['riscv64-linux-gnu-readelf', '-lW', str(elf)], text=True)
(out / 'firmware-loads.txt').write_text(headers)
for line in headers.splitlines():
    fields = line.split()
    if fields and fields[0] == 'LOAD':
        base, size = int(fields[3], 16), int(fields[5], 16)
        if not (0x80000000 <= base <= base + size <= 0x80200000):
            raise SystemExit('Firmware LOAD/BSS overlaps next image or lies outside reserved area')
if kernel.stat().st_size > 0x2000000 or dtb.stat().st_size > 0x5e00000:
    raise SystemExit('Kernel/DTB exceeds planned memory interval')
fifo = out / ('serial-interactive.fifo' if a.interactive else 'serial-input.fifo')
if fifo.exists():
    raise SystemExit(f'Refusing to replace existing FIFO: {fifo}')
os.mkfifo(fifo, 0o600)
fd = os.open(fifo, os.O_RDWR | os.O_NONBLOCK)
log_path = out / ('boot-interactive.log' if a.interactive else 'boot.log')
cmd = [str(root / 'nemu/build/riscv64-nemu-interpreter'), '-b', '--timer-source=mtimer',
       f'--serial-input={fifo}', f'--kernel={kernel}', f'--dtb={dtb}', str(firmware)]
(out / ('interactive-command.json' if a.interactive else 'boot-command.json')).write_text(json.dumps(cmd, indent=2) + '\n')
env = dict(os.environ)
if not a.interactive:
    env.update(SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
proc = None
try:
    with log_path.open('wb') as log:
        if a.interactive:
            from console import interact
            print(f'Console log: {log_path}', flush=True)
            proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, env=env, start_new_session=True)
            (out / 'interactive-pid').write_text(str(proc.pid) + '\n')
            status = interact(proc, fd, log)
            # A deliberate console stop is a successful make run invocation.
            raise SystemExit(0 if status == 130 else status)
        proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env)
        (out / 'pid').write_text(str(proc.pid) + '\n')
        deadline = time.monotonic() + a.timeout
        sent = False
        second_round = False
        while time.monotonic() < deadline:
            text = log_path.read_bytes().decode(errors='replace').replace('\r', '')
            if not sent and '/ # ' in text:
                os.write(fd, b'ls /\necho M1P8_OK\n')
                sent = True
            if sent and not second_round and re.search(r'(?m)^(?:/ # )?M1P8_OK$', text):
                os.write(fd, b'cat /init\necho M1P8_DONE\n')
                second_round = True
            if second_round and re.search(r'(?m)^(?:/ # )?M1P8_DONE$', text):
                for expected in ['OpenSBI', 'Linux version', 'Run /init as init process',
                                 'M1P8_OK\n', '#!/bin/sh', '/bin/sh']:
                    if expected not in text:
                        raise RuntimeError(f'Missing boot/shell evidence: {expected}')
                if not re.search(r'(?m)^(?:/ # )?M1P8_OK$', text):
                    raise RuntimeError('Echo command output missing (command echo is insufficient)')
                if not all(word in text for word in ['dev', 'proc', 'sys', 'bin']):
                    raise RuntimeError('Root directory output missing')
                (out / 'result.json').write_text(json.dumps({'status': 'PASS', 'commands': ['ls /', 'echo M1P8_OK', 'cat /init'],
                    'termination': 'host terminated after shell assertions; no guest halt claimed'}, indent=2) + '\n')
                assets = [firmware, elf, kernel, dtb,
                          root / 'npc/verif/build/linux-initramfs/nemu-p8/initramfs.cpio.gz',
                          root / 'nemu/build/riscv64-nemu-interpreter',
                          root / 'npc/verif/build/linux-kernel/nemu/arch/riscv/boot/Image',
                          root / 'npc/verif/build/linux-initramfs/nemu/initramfs.cpio.gz']
                configs = {'nemu.config': root/'nemu/.config',
                           'kernel.config': root/'npc/verif/build/linux-kernel/nemu-p8/.config',
                           'opensbi.config': out/'opensbi/platform/generic/kconfig/.config'}
                for name, source in configs.items():
                    shutil.copyfile(source, out/name)
                    assets.append(out/name)
                manifest = {str(path): {'size': path.stat().st_size,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                            for path in assets}
                (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
                print(f'Linux native shell PASS: {log_path}')
                break
            if proc.poll() is not None:
                raise RuntimeError(f'NEMU exited {proc.returncode}: inspect {log_path}')
            time.sleep(0.1)
        else:
            raise TimeoutError(f'Boot/shell timeout: inspect {log_path}')
finally:
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    os.close(fd)
    fifo.unlink()
