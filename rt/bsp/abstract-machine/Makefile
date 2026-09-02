ARCH ?= native
AM_APPS_MK = build/${ARCH}/am-apps.mk
FILE_MK = files.mk
FILE_TMP = .tmp.$(FILE_MK)
RTCONFIG_H = rtconfig.h

NAME = rtthread
SRCS = $(shell find src -name "*.c")
CFLAGS += -DHAVE_CCONFIG_H -D__RTTHREAD__
CFLAGS += -Wno-nonnull-compare
# RT-Thread 走 PSRAM 布局：整程序经二级 bootloader（FSBL+SSBL）搬入 PSRAM 执行。
#   FSBL(flash)→搬 SSBL 到 SRAM→SSBL(SRAM 快)搬主程序到 PSRAM。
#   不使用 extra.ld —— 其 INSERT BEFORE .data 在带 MEMORY 区域的链接脚本下会把
#   fsymtab/rt_init 节错放到 SRAM 基址(独立 LOAD 段)，使 flash 镜像跨度 528MB 无法加载；
#   这些节（fsymtab/rt_init/am-apps）已并入 linker-psram-ssbl.ld 的 .data/.bss。
# am-apps 集成（阶段 J5 基础）：默认不集成，显式 make update 才触发 integrate-am-apps.py。
LDS    ?= $(AM_HOME)/scripts/linker-psram-ssbl.ld
BOOT_S ?= riscv/npc/start_fsbl.S
# BOOT_S/LDS 是链接/汇编期参数，am-riscv64-npc.a 由子 make 构建（不会继承普通变量），
# 必须 export 才能让子 make 也以 start_sram.S 汇编入口（否则回退默认 start.S，
# 其 jal _trm_init 跨 flash→PSRAM 超 ±1MB 链接失败）。
export LDS BOOT_S
-include $(FILE_MK)
-include $(AM_APPS_MK)
include $(AM_HOME)/Makefile

$(RTCONFIG_H):
	touch $@
	scons --useconfig=.config

init: $(RTCONFIG_H)
	scons -c
	scons --verbose -n > $(FILE_TMP)
	cat $(FILE_TMP) | grep -o '[^ ]*\.c$$' | awk '{print "SRCS += " $$1}' > $(FILE_MK)
	cat $(FILE_TMP) | grep 'gcc ' | grep -o " -I[^ ]*" | sort -u | awk '{print "CFLAGS += " $$1}' >> $(FILE_MK)
	rm $(FILE_TMP)
	if [ "`sed -n '3p' $^`"x = x ]; then sed -i -e '2a#include "extra.h"' $^; fi

menuconfig:
	scons --menuconfig
	scons --genconfig
	$(MAKE) init

ifneq ($(MAKECMDGOALS),clean)
# am-apps 集成：仅显式 `make update` 触发（默认不集成，避免 make run 牵连生成）。
# 已生成的 am-apps.mk 会被 -include 读取；未生成则不集成。
update:
	@mkdir -p build/$(ARCH)
	@python3 integrate-am-apps.py ARCH=$(ARCH) CROSS_COMPILE=$(CROSS_COMPILE)
endif

.PHONY: init menuconfig update
