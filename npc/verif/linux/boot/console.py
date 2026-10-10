"""POSIX terminal bridge to NEMU's independent UART input FIFO."""
import os
import select
import signal
import sys
import termios
import tty


class ConsoleSignal(Exception):
    def __init__(self, number):
        self.number = number


def interact(proc, fifo_fd, log):
    """Return on host Ctrl+C, Ctrl+], terminal EOF, a stop signal, or guest exit."""
    input_fd = sys.stdin.fileno()
    output_fd = sys.stdout.fileno()
    pipe_fd = proc.stdout.fileno()
    saved = termios.tcgetattr(input_fd)
    previous_handlers = {}
    pending = bytearray()

    def stop(number, frame):
        raise ConsoleSignal(number)

    try:
        for number in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous_handlers[number] = signal.signal(number, stop)
        # Cbreak keeps host ISIG: Ctrl+C ends this NEMU session. Guest input
        # still arrives one byte at a time, without duplicate host echo.
        tty.setcbreak(input_fd)
        print('Linux serial console: Ctrl+C or Ctrl+] exits NEMU.', flush=True)
        while True:
            # Bound a pasted-input backlog and respect FIFO backpressure.
            readers = [pipe_fd]
            if len(pending) < 65536:
                readers.append(input_fd)
            ready, writable, _ = select.select(readers, [fifo_fd] if pending else [], [], 0.1)
            if pipe_fd in ready:
                data = os.read(pipe_fd, 65536)
                if not data:
                    return proc.wait()
                log.write(data)
                log.flush()
                view = memoryview(data)
                while view:
                    written = os.write(output_fd, view)
                    view = view[written:]
            if input_fd in ready:
                data = os.read(input_fd, 4096)
                if not data or b'\x1d' in data:  # Ctrl+]
                    return 0
                pending.extend(data.replace(b'\r', b'\n'))
            if fifo_fd in writable:
                try:
                    written = os.write(fifo_fd, pending[:4096])
                    del pending[:written]
                except BlockingIOError:
                    pass
    except ConsoleSignal as stopped:
        return 128 + stopped.number
    finally:
        try:
            termios.tcsetattr(input_fd, termios.TCSANOW, saved)
        finally:
            for number, handler in previous_handlers.items():
                signal.signal(number, handler)
