#!/usr/bin/env python3
"""Use a real host PTY to exercise the Linux console and terminal cleanup."""
import argparse
import errno
import os
from pathlib import Path
import pty
import re
import select
import signal
import subprocess
import termios
import time

root = Path(__file__).resolve().parents[2]
out = root / 'npc/verif/build/linux-boot/nemu-p8'
parser = argparse.ArgumentParser()
parser.add_argument('--make-run', action='store_true', help='also test the real build/run Makefile entry')
args = parser.parse_args()
direct = ['bash', str(root/'npc/verif/linux/boot/run.sh'), '--interactive']
command = ['make', '-C', str(root/'npc/verif/linux/boot'), 'ARCH=riscv64-nemu', 'run'] if args.make_run else direct
log = bytearray()
master, slave = pty.openpty()
saved = termios.tcgetattr(slave)
def terminal_session():
    # Make the slave the foreground controlling terminal so ISIG-generated
    # Ctrl+C exercises the same path as a human terminal.
    os.setsid()
    import fcntl
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
proc = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave,
                        preexec_fn=terminal_session, env=env)

def wait_for(pattern, timeout=90):
    deadline = time.monotonic() + timeout
    start = len(log)
    while time.monotonic() < deadline:
        ready, _, _ = select.select([master], [], [], 0.1)
        if ready:
            try:
                data = os.read(master, 65536)
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
                data = b''
            log.extend(data)
        if re.search(pattern, bytes(log[start:]).replace(b'\r', b'')):
            return
        if proc.poll() is not None:
            raise RuntimeError(f'Console exited {proc.returncode} before {pattern!r}')
    raise TimeoutError(f'Missing console output {pattern!r}')


def check_clean():
    assert termios.tcgetattr(slave) == saved, 'Host terminal attributes not restored'
    assert not (out/'serial-interactive.fifo').exists(), 'FIFO left behind'
    child = int((out/'interactive-pid').read_text())
    try:
        os.kill(child, 0)
    except ProcessLookupError:
        return
    raise AssertionError(f'NEMU child {child} is still alive')

try:
    wait_for(rb'/ # ')
    attrs = termios.tcgetattr(slave)
    assert not (attrs[3] & (termios.ICANON | termios.ECHO))
    assert attrs[3] & termios.ISIG
    os.write(master, b'echo MANUAL_ONE\r')
    wait_for(rb'(?m)^(?:/ # )?MANUAL_ONE$')
    os.write(master, b'echo MANUAL_TWZ\x7fO\r')
    wait_for(rb'(?m)^(?:/ # )?MANUAL_TWO$')
    os.write(master, b'\x1d')
    assert proc.wait(timeout=7) == 0
    check_clean()
    print('Linux PTY multi-command/Enter/backspace/Ctrl+] + cleanup PASS', flush=True)
    command = direct
    # No extra kernel boot is needed for host stop/guest-exit cleanup checks.
    for stop in ['ctrl-c', 'sigterm', 'guest-exit']:
        proc = subprocess.Popen(command, stdin=slave, stdout=slave, stderr=slave,
                                preexec_fn=terminal_session, env=env)
        wait_for(rb'Linux serial console:')
        if stop == 'ctrl-c':
            os.write(master, b'\x03')
            expected = 0
        elif stop == 'sigterm':
            proc.send_signal(signal.SIGTERM)
            expected = 128 + signal.SIGTERM
        else:
            os.kill(int((out/'interactive-pid').read_text()), signal.SIGTERM)
            expected = 256 - signal.SIGTERM
        assert proc.wait(timeout=7) == expected
        check_clean()
        print(f'Console {stop} terminal/child/FIFO cleanup PASS', flush=True)
finally:
    if proc.poll() is None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=7)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    (out/'interactive-pty-test.log').write_bytes(log)
    termios.tcsetattr(slave, termios.TCSANOW, saved)
    os.close(master)
    os.close(slave)
