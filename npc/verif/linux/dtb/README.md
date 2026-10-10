# Linux DTB build targets

Run `make -C npc/verif/linux/dtb TARGET=nemu`. The NEMU profile reads PMEM base and size from `nemu/.config`; its timebase is set in `targets/nemu.mk`. The preprocessed DTS and padded DTB are generated under `npc/verif/build/linux-dtb/nemu/`. Only `TARGET=nemu` is provided in M1-P2. Add a separate NPC profile/DTS for M5; each platform needs its own firmware and image layout.

The original M1-P2 structural baseline advertised no UART/timer. In M1-P8 the active DTS now describes the implemented native RV64 platform: ns16550a UART at 0xa00003f8 (8 byte registers, 1843200 Hz, 115200, no IRQ), ACLINT MTIMER mtime@0x0200bff8 and mtimecmp@0x02004000, CPU INTC cause 7, and serial0 console/earlycon. Boot this DTB with `--timer-source=mtimer`; default legacy mode does not publish MTIMER MMIO. The old RTC remains a separate AM ABI.

P8 verified OpenSBI → Linux → /init → interactive shell with this DTB. See [boot recipe](../boot/README.md) for independent firmware/kernel outputs, fixed load addresses and shell assertions; [process record](../../records/process/LINUX_M1_NEMU.md#m1-p8-execution-20261010) contains the evidence. This is a NEMU native profile, not an NPC DTS or a PLIC/MSIP implementation.
