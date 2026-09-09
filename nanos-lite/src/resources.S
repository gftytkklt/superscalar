.section .rodata
.globl logo
logo:
.incbin "resources/logo.txt"
.byte 0

#ifdef KERNEL_EMBED_RAMDISK
// Embedded fsimg for platforms without a disk device (NPC SoC).
// The section is kept writable so that game save data works in-memory.
.section .ramdisk,"aw"
.globl ramdisk_start, ramdisk_end
ramdisk_start:
.incbin "build/ramdisk.img"
ramdisk_end:
#endif
