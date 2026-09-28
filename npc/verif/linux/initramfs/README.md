# M1-P3 NEMU native initramfs

Run `make -C npc/verif/linux/initramfs`. The build reuses the M0 static musl/lp64 BusyBox and the already built Linux 6.1.188 `usr/gen_init_cpio`; neither tool is rebuilt. Override `BUSYBOX`, `GEN_INIT_CPIO`, or `OUT` if the M0 assets are elsewhere.

The generated `npc/verif/build/linux-initramfs/nemu/initramfs.list` records root ownership, file modes, `/bin/sh -> busybox`, and the `/dev/console` character device (major 5, minor 1). `gen_init_cpio` produces a `newc` archive; `gzip -n` writes `initramfs.cpio.gz` in the same directory. The generated files are ignored by git.

The tracked `init` mounts proc, sysfs, and devtmpfs, then executes `/bin/sh` on `/dev/console`. This stage checks the archive and BusyBox ISA/ABI only. M1-P4 will enable the required kernel options and embed the archive; later M1 steps will validate console input and Linux boot on NEMU.
