# ---------------------------------------------------------------------------
# Standalone RTL micro-verification for npc/vsrc/ysyx_22040750.v
#
# The CPU core is compiled by Verilator together with tb_main.cpp (a tiny
# AXI4-slave memory model + clock/reset harness) and booted from a binary
# image at 0x30000000 (PC reset 0x2ffffffc, snpc = pc+4 does the boot jump).
#
# Usage:
#   make                 build the model, then run every tests/*.S
#   make run  T=bug2_csr run a single test
#   make fst  T=bug2_csr run a single test and keep its waveform
#   make clean
# ---------------------------------------------------------------------------

BUILD   := build
OBJ     := $(BUILD)/obj_dir
IMG     := $(BUILD)/img
MODEL   := $(OBJ)/Vnpc
RTL     := ../vsrc/ysyx_22040750.v
LDS     := ../scripts/linker-soc.ld
XC      := riscv64-linux-gnu

CFLAGS  += -fno-pic -march=rv64g -mcmodel=medany -O0 -nostdlib
LDFLAGS := -melf64lriscv -T $(LDS) \
           --defsym=_pmem_start=0x30000000 --defsym=_entry_offset=0x0 \
           --defsym=_sram_start=0x0f000000 --defsym=_stack_offt=0x2000

TESTS   := $(basename $(notdir $(wildcard tests/*.S)))
T       ?= $(firstword $(TESTS))

.PHONY: all run fst clean
all:
	@for n in $(TESTS); do echo "== $$n =="; $(MAKE) run T=$$n; echo; done

run: $(MODEL) $(IMG)/$(T).bin
	./$(MODEL) $(IMG)/$(T).bin

fst: $(MODEL) $(IMG)/$(T).bin
	./$(MODEL) $(IMG)/$(T).bin $(BUILD)/$(T).fst

$(MODEL): tb_main.cpp $(RTL)
	mkdir -p $(OBJ)
	verilator --binary --trace-fst -O3 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		-Mdir $(OBJ) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o Vnpc $(RTL) tb_main.cpp

$(IMG)/%.bin: tests/%.S
	mkdir -p $(OBJ) $(IMG)
	$(XC)-gcc $(CFLAGS) -c $< -o $(OBJ)/$*.o
	$(XC)-ld $(LDFLAGS) $(OBJ)/$*.o -o $(OBJ)/$*.elf
	$(XC)-objcopy -O binary -j .text $(OBJ)/$*.elf $@

clean:
	rm -rf $(BUILD)