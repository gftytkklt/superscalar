# 把 nanos-lite 作为 Navy 应用编译的 wrapper（不改动原工程）。
# 目标：让 nanos-lite 的源码在 Navy 运行时(libam)上编译通过。
NAME = nanos-lite-guest

NANOS_LITE_HOME = $(abspath ../../../nanos-lite)

# 复用 nanos-lite/src 下的源文件（VPATH 定位），
# 以便其中的 "files.h"/"syscall.h" 等引号头文件按原路径解析。
SRCS = main.c mm.c device.c fs.c syscall.c loader.c proc.c irq.c ramdisk.c ramdisk_stubs.S stubs.c
VPATH = $(NANOS_LITE_HOME)/src
INC_PATH += $(NANOS_LITE_HOME)/include

# libam 提供 AM 的 TRM/IOE/CTE 实现；libc/libos 由 Navy Makefile 对非 native 自动加入
LIBS += libam

include $(NAVY_HOME)/Makefile