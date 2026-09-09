# 启动/链接方式可按程序选择：
#   LDS    : 链接脚本。linker-soc.ld = flash XIP（默认，数据段搬 SRAM）；
#            linker-sram.ld = 整程序搬入 SRAM 执行（阶段 D bootloader）；
#            linker-psram.ld = 整程序搬入 PSRAM（阶段 E/F，单级 bootloader）；
#            linker-psram-ssbl.ld = FSBL+SSBL 二级加载（阶段 G）。
#   BOOT_S : 启动汇编。start.S = flash 直启；start_sram.S = 单级 bootloader；
#            start_fsbl.S = FSBL（二级 bootloader 第一级）。
#
# 持久配置：读入 npc/.npc_config（由 `make -C npc menuconfig` 生成）。其中 BOOT_MODE
# 决定 (LDS, BOOT_S) 的固定搭配（堆/程序执行位置不同），HEAP_SIZE 一并配置。
# 命令行显式传 LDS/BOOT_S/HEAP_SIZE/BOOT_MODE 仍优先（make ?= 语义）。
-include $(NPC_HOME)/.npc_config

# UART 波特率除数随 NVBoard：WITH_SDL（配置或命令行）→ 1（匹配 NVBoard divisor 16）；
# 否则 → 54（115200 波特）。供 AM trm.c uart_config_divisor 用（UART_DIVISOR 宏）。
ifeq ($(filter 1 y,$(WITH_SDL)),)
CFLAGS += -DUART_DIVISOR=54
else
CFLAGS += -DUART_DIVISOR=1
endif

# BOOT_MODE → (LDS, BOOT_S) 绑定表（与 npc/scripts/menuconfig.py 的选项一一对应）：
#   xip=flash直启/堆PSRAM | sram=搬SRAM | psram=搬PSRAM |
#   psram-ssbl=FSBL+SSBL | sdram=搬SDRAM | sdram-heap=XIP+堆SDRAM
ifeq ($(BOOT_MODE), sram)
  LDS ?= $(AM_HOME)/scripts/linker-sram.ld
  BOOT_S ?= riscv/npc/start_sram.S
else ifeq ($(BOOT_MODE), psram)
  LDS ?= $(AM_HOME)/scripts/linker-psram.ld
  BOOT_S ?= riscv/npc/start_sram.S
else ifeq ($(BOOT_MODE), psram-ssbl)
  LDS ?= $(AM_HOME)/scripts/linker-psram-ssbl.ld
  BOOT_S ?= riscv/npc/start_fsbl.S
else ifeq ($(BOOT_MODE), sdram)
  LDS ?= $(AM_HOME)/scripts/linker-sdram.ld
  BOOT_S ?= riscv/npc/start_sram.S
else ifeq ($(BOOT_MODE), sdram-heap)
  LDS ?= $(AM_HOME)/scripts/linker-sdram-heap.ld
  BOOT_S ?= riscv/npc/start.S
else
  # 默认 / xip
  LDS ?= $(AM_HOME)/scripts/linker-soc.ld
  BOOT_S ?= riscv/npc/start.S
endif

AM_SRCS := $(BOOT_S) \
           riscv/npc/boot_sram.c \
           riscv/npc/fsbl.c \
           riscv/npc/ssbl.c \
           riscv/npc/trm.c \
           riscv/npc/ioe.c \
           riscv/npc/timer.c \
           riscv/npc/input.c \
           riscv/npc/video.c \
           riscv/npc/cte.c \
           riscv/npc/trap.S \
           platform/dummy/vme.c \
           platform/dummy/mpe.c

CFLAGS    += -fdata-sections -ffunction-sections
# 堆区大小（PSRAM）按程序可调：默认 32KB 足够 cpu-tests / mem-test 快速扫测；
# 跑 microbench/RT-Thread 等大堆程序时用 HEAP_SIZE=0x400000(4MB) 覆盖。
HEAP_SIZE ?= 0x8000
LDFLAGS   += -T $(LDS) \
						 --defsym=_pmem_start=0x30000000 --defsym=_entry_offset=0x0 \
                                                 --defsym=_sram_start=0x0f000000 --defsym=_stack_offt=0x1800 \
                                                 --defsym=_heap_size=$(HEAP_SIZE)
LDFLAGS   += --gc-sections -e _start
CFLAGS += -DMAINARGS=\"$(mainargs)\"
.PHONY: $(AM_HOME)/am/src/riscv/npc/trm.c

image: $(IMAGE).elf
	@$(OBJDUMP) -d $(IMAGE).elf > $(IMAGE).txt
	@echo + OBJCOPY "->" $(IMAGE_REL).bin
	@$(OBJCOPY) -S --set-section-flags .bss=alloc,contents -O binary $(IMAGE).elf $(IMAGE).bin

run: image
	$(MAKE) -C $(NPC_HOME) sim IMG=$(IMAGE).bin