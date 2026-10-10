# M1-P3 NEMU native initramfs

Run `make -C npc/verif/linux/initramfs`. The build reuses the M0 static musl/lp64 BusyBox and the already built Linux 6.1.188 `usr/gen_init_cpio`; neither tool is rebuilt. Override `BUSYBOX`, `GEN_INIT_CPIO`, or `OUT` if the M0 assets are elsewhere.

The generated `npc/verif/build/linux-initramfs/nemu/initramfs.list` records root ownership, file modes, `/bin/sh -> busybox`, and the `/dev/console` character device (major 5, minor 1). `gen_init_cpio` produces a `newc` archive; `gzip -n` writes `initramfs.cpio.gz` in the same directory. The generated files are ignored by git.

The tracked `init` mounts proc, sysfs, and devtmpfs, then executes `/bin/sh` on `/dev/console`. This stage checks the archive and BusyBox ISA/ABI only. P4 embedded the original archive. P8 boot testing found missing applet links; the current recipe adds /bin/mount, /bin/ls, /bin/cat and /bin/echo, and /init uses set -e plus an explicit shell prompt. The BusyBox binary itself is unchanged. P8 rebuilds into `npc/verif/build/linux-initramfs/nemu-p8/` through the [boot recipe](../boot/README.md), preserving the original P3 archive and P4 Image. Actual mount/ls/echo/cat and console input passed on NEMU; this supplements rather than retroactively changes the P3 static acceptance record.
