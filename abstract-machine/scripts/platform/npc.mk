# 启动/链接方式可按程序选择：
#   LDS    : 链接脚本。linker-soc.ld = flash XIP（默认，数据段搬 SRAM）；
#            linker-sram.ld = 整程序搬入 SRAM 执行（阶段 D bootloader）。
#   BOOT_S : 启动汇编。start.S = flash 直启；start_sram.S = bootloader 搬 code 到 SRAM。
LDS    ?= $(AM_HOME)/scripts/linker-soc.ld
BOOT_S ?= riscv/npc/start.S

AM_SRCS := $(BOOT_S) \
           riscv/npc/boot_sram.c \
           riscv/npc/trm.c \
           riscv/npc/ioe.c \
           riscv/npc/timer.c \
           riscv/npc/input.c \
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