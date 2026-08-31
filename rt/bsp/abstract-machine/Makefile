ARCH ?= native
FILE_MK = files.mk
FILE_TMP = .tmp.$(FILE_MK)
RTCONFIG_H = rtconfig.h

NAME = rtthread
SRCS = $(shell find src -name "*.c")
CFLAGS += -DHAVE_CCONFIG_H -D__RTTHREAD__
CFLAGS += -Wno-nonnull-compare
# RT-Thread 走 PSRAM 布局（阶段 F）：整程序经 bootloader 搬入 PSRAM 执行。
#   不再使用 extra.ld —— 其 INSERT BEFORE .data 在带 MEMORY 区域的链接脚本下会把
#   fsymtab/rt_init 节错放到 SRAM 基址(独立 LOAD 段)，使 flash 镜像跨度 528MB 无法加载；
#   这些节已并入 linker-psram.ld 的 .data（见该脚本注释）。
LDS    ?= $(AM_HOME)/scripts/linker-psram.ld
BOOT_S ?= riscv/npc/start_sram.S
# BOOT_S/LDS 是链接/汇编期参数，am-riscv64-npc.a 由子 make 构建（不会继承普通变量），
# 必须 export 才能让子 make 也以 start_sram.S 汇编入口（否则回退默认 start.S，
# 其 jal _trm_init 跨 flash→PSRAM 超 ±1MB 链接失败）。
export LDS BOOT_S
-include $(FILE_MK)
include $(AM_HOME)/Makefile

$(RTCONFIG_H):
	touch $@
	scons --useconfig=.config

init: $(RTCONFIG_H)
	scons -c
	scons --verbose -n > $(FILE_TMP)
	cat $(FILE_TMP) | grep -o '[^ ]*.c$$' | awk '{print "SRCS += " $$1}' > $(FILE_MK)
	cat $(FILE_TMP) | grep 'gcc ' | head -n 1 | grep -o " -I[^ ]*" | awk '{print "CFLAGS += " $$1}' >> $(FILE_MK)
	rm $(FILE_TMP)
	if [ "`sed -n '3p' $^`"x = x ]; then sed -i -e '2a#include "extra.h"' $^; fi

menuconfig:
	scons --menuconfig
	scons --genconfig
	$(MAKE) init

.PHONY: init menuconfig
