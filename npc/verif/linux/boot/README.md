# M1-P8 NEMU native Linux boot

This profile boots one RV64IMA/Sv39 hart with 128 MiB PMEM, OpenSBI FW_JUMP, Linux 6.1.188 and the static musl/lp64 BusyBox 1.36.1 initramfs. It uses installed tools and existing local sources; it does not install or fetch dependencies. NPC/REF validation belongs to later phases.

From the workspace root:

```sh
CCACHE_DISABLE=1 make -C nemu -o compile_git -j8 app
make -C npc/verif/linux/boot all
bash npc/verif/linux/boot/run.sh --timeout 90
```

To keep Linux running in your terminal for **manual interaction**, from the boot directory:

```sh
cd /home/gftyt/ysyx-workbench/npc/verif/linux/boot
make ARCH=riscv64-nemu run
```

`make ... run` builds the platform images and NEMU, then starts a persistent console. `ARCH=riscv64-nemu` selects this profile; other ARCH values are rejected. NEMU must already have its native RV64 DEVICE/SERIAL configuration (the target checks it). To reuse existing binaries without a build, use `bash ./run.sh --interactive`.

Wait for `/ # `, then enter Linux commands normally (for example `ls /`, `cat /init`). This mode sends no automatic commands and has no automatic timeout. **Ctrl+C exits NEMU** and restores your host terminal; Ctrl+] is an alternate exit key. Enter/backspace are forwarded to the guest console. Ctrl+C is reserved for stopping this host session, not for interrupting a guest command. Input must be a real terminal (an IDE integrated terminal is suitable).

`--interactive` reuses the same firmware/kernel/DTB and LOAD/BSS checks, forwards terminal input to its own UART FIFO, and displays output live while recording `npc/verif/build/linux-boot/nemu-p8/boot-interactive.log`. It records `interactive-command.json` and `interactive-pid`, removes its FIFO and stops its NEMU child on exit or SIGTERM/SIGHUP. It preserves automatic `boot.log`/`result.json`; rerunning an interactive session replaces only the interactive log. Interactive mode inherits the normal SDL/display environment, so an enabled NEMU GUI remains available and closing its window follows NEMU's existing quit path. On a machine without a display, prefix the command with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`. GUI here is NEMU's device window, not a Linux desktop. NEMU still uses batch execution internally; the terminal belongs to Linux UART, not the SDB monitor. Closing the shell is not guaranteed to shut down Linux PID 1; use Ctrl+C or Ctrl+] to end the host session.

The command without `--interactive` remains the **automatic smoke test**: it sends commands, checks their output and terminates the guest after success. If images need rebuilding, run `make all` in this directory first.

The NEMU build must be native RV64 with DEVICE, SERIAL and TIMER enabled. `-o compile_git` skips the existing automatic commit hook; the boot profile's new `make ... run` target uses this safe build and invokes the interpreter without entering the original `nemu/` make run commit hook. Kernel input is the existing writable `npc/verif/build/linux-kernel/nemu-src/` and P4 `.config`; OpenSBI defaults to `$HOME/linux-m0/opensbi`. Override `KERNEL_SRC`, `KERNEL_BASE`, `OPENSBI_SRC`, `CROSS_COMPILE`, `JOBS` or output variables on make as needed. Initramfs defaults to the existing `$HOME/linux-m0/busybox-1.36.1/busybox` and Linux `usr/gen_init_cpio` (override BUSYBOX/GEN_INIT_CPIO via make).

P8 outputs are separate from the original P3 archive and P4 Image:

| Asset | Default output / physical address |
|---|---|
| Firmware | `npc/verif/build/linux-boot/nemu-p8/opensbi/platform/generic/firmware/fw_jump.{bin,elf}` / `0x80000000` |
| Kernel | `npc/verif/build/linux-kernel/nemu-p8/arch/riscv/boot/Image` / `0x80200000` |
| Initramfs | `npc/verif/build/linux-initramfs/nemu-p8/initramfs.cpio.gz` / embedded in Image |
| DTB | `npc/verif/build/linux-dtb/nemu/nemu.dtb` / `0x82200000` |
| Evidence | `npc/verif/build/linux-boot/nemu-p8/` |

The kernel config delta is SERIAL_OF_PLATFORM=y and the P8 initramfs path; FPU and compressed ISA stay disabled. OpenSBI uses rv64ima_zicsr_zifencei/lp64 and disables its optional SERIAL_SEMIHOSTING probe in its own output configuration: that probe uses ebreak, which is the existing NEMU halt ABI. External OpenSBI source is unchanged. The runner checks firmware LOAD ranges including BSS against the 2 MiB reservation before starting.

The runner owns a fresh FIFO in its output directory, waits for `/ # `, sends `ls /` and an echo marker, then sends `cat /init` and a second marker after receiving the first result. It verifies actual command output, terminates NEMU after success, and removes its FIFO. Timeout or early exit fails; an existing FIFO is not overwritten. `boot.log`, `boot-command.json`, `firmware-loads.txt`, `result.json` and `manifest.json` preserve evidence; success is not a guest GOOD TRAP or a shutdown test.

All monitor options precede the firmware IMAGE:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
  nemu/build/riscv64-nemu-interpreter -b --timer-source=mtimer \
  --serial-input=PREEXISTING_FILE_OR_FIFO \
  --kernel=npc/verif/build/linux-kernel/nemu-p8/arch/riscv/boot/Image \
  --dtb=npc/verif/build/linux-dtb/nemu/nemu.dtb \
  npc/verif/build/linux-boot/nemu-p8/opensbi/platform/generic/firmware/fw_jump.bin
```

MTIMER mtime is at 0x0200bff8 and mtimecmp at 0x02004000 (8 bytes each, 1 MHz). CSR time shares this clock; the initial comparator is UINT64_MAX. This is a timer device, without MSIP. `--timer-source=mtimer` excludes the legacy alarm latch from MTIP; it does not modify alarm.c. Default `legacy` retains the periodic CPU.INTR source and consumes it only when the common CPU arbiter selects it. Legacy AM software must be relinked with the updated RV64 NEMU CTE that enables MTIE; handlers and applications are unchanged.

The byte-wide UART at 0xa00003f8 implements the tested 8250 register subset, a 16-byte receive queue and immediate TX. It has no IRQ wire/PLIC; Linux uses its IRQ=0 polling path. FIFO receive timeout reporting is simplified rather than baud-cycle accurate. RX reads a nonblocking file/FIFO and never uses SDB stdin; EOF is idle and FIFO writers can reconnect. Other ISA/TARGET_AM serial code retains its prior implementation.

P8 verification (native build first; the console test uses a real PTY and headless SDL):

```sh
bash nemu/tests/m1_p8_host.sh
bash nemu/tests/m1_p8_guest.sh
bash nemu/tests/m1_p8_nodevice.sh
python3 nemu/tests/m1_p8_loader.py
python3 nemu/tests/m1_p8_console.py --make-run
bash nemu/tests/m1_p5_priv.sh
bash nemu/tests/m1_p6_atomic.sh
bash nemu/tests/m1_p7_sv39.sh
```

The host harnesses link actual CSR/arbiter/device/nanos scheduler/NDL code with controlled inputs. FG F1/F2/F3 testing injects AM keyboard events into actual nanos `events_read` and checks actual context switches; it is not graphical keyboard end-to-end validation. The NDL harness checks actual nanos gettimeofday/NDL conversion using controlled AM uptime. Actual old RTC progression is observed separately in AM `t`. The No-DEVICE check links CSR/interrupt code and syntax-checks inst/monitor, without reconfiguring the active build; it is not a REF .so acceptance test. Device-free CSR time is currently constant zero, without a host clock.

For the AM observer, export the workspace AM_HOME/NAVY_HOME/NEMU_HOME, use `CCACHE_DISABLE=1`, and build images without `run`:

```sh
export AM_HOME="$PWD/abstract-machine" NAVY_HOME="$PWD/navy-apps" NEMU_HOME="$PWD/nemu" CCACHE_DISABLE=1
make -C am-kernels/tests/am-tests ARCH=riscv64-nemu mainargs=t image
mkdir -p npc/verif/build/m1p8-tests
cp am-kernels/tests/am-tests/build/amtest-riscv64-nemu.bin npc/verif/build/m1p8-tests/am-rtc.bin
make -C am-kernels/tests/am-tests ARCH=riscv64-nemu mainargs=i image
make -C am-kernels/kernels/thread-os ARCH=riscv64-nemu image
make -C am-kernels/kernels/yield-os ARCH=riscv64-nemu image
make -C nanos-lite ARCH=riscv64-nemu image
python3 nemu/tests/m1_p8_am.py
```

The observer requires repeated timer/yield output, threads A–E, ABAB collaboration, background Navy hello and RTC second 1/2 before terminating the resident guests. Full graphical foreground apps, RT-Thread tick changes, REF/NPC difftest and cycle-accurate devices are not certified here. The standard UI/UM runner remains unchanged (`TARGET=nemu`, 66 PASS/0 FAIL/1 existing ma_data SKIP in P8). See [P8 process record](../../records/process/LINUX_M1_NEMU.md#m1-p8-execution-20261010) for hashes, findings and limits. P8 completion requires review/commit before a separately authorized P9; this profile does not advance the phase itself.
