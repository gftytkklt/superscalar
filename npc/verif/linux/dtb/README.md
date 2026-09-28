# Linux DTB build targets

Run `make -C npc/verif/linux/dtb TARGET=nemu`. The NEMU profile reads PMEM base and size from `nemu/.config`; its timebase is set in `targets/nemu.mk`. The preprocessed DTS and padded DTB are generated under `npc/verif/build/linux-dtb/nemu/`. Only `TARGET=nemu` is provided in M1-P2. Add a separate NPC profile/DTS for M5; each platform needs its own firmware and image layout.

The present `nemu.dts` is a **structural M1-P2 baseline**, not a Linux boot-ready DTB. `rv64ima`, Sv39, CPU interrupt controller, and the 1 MHz timebase are the M1 target contract; the current NEMU core lacks some of these features. Current NEMU serial is output-only and cannot drive OpenSBI/Linux 8250; its RTC is not ACLINT and has no guest timer comparator. The DTS therefore advertises neither UART nor timer and has no `stdout-path`. Add those nodes only when the NEMU device implementation and boot logs validate their bindings. See `../../records/process/LINUX_M1_NEMU.md`.
