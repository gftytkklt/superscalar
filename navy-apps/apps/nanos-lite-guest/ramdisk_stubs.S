# 提供 nanos-lite 依赖的 ramdisk 符号（原工程由 resources.S 内嵌 ramdisk.img 定义）。
.global ramdisk_start, ramdisk_end
ramdisk_start:
ramdisk_end: