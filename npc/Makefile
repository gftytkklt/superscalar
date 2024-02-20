#for run npc

VSRC = $(shell find $(abspath ./vsrc) -name "*.v")
VSRC += $(shell find $(abspath ./ysyxSoC/perip) -type f -name "*.v")
VSRC += $(shell find $(abspath ./ysyxSoC/generated) -name "ysyxSoCFull.v")

CSRC = $(shell find $(abspath ./csrc) -name "*.cpp")

CFLAGS += -MMD -O3 $(INCLUDES) -I/usr/lib/llvm-12/include -std=c++14   -fno-exceptions -D_GNU_SOURCE -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -fPIE

LDFLAGS += $(shell llvm-config --libs) -ldl

# verilator flag
TOPNAME = ysyxSoCFull
VERILATOR = verilator
VERILATOR_INCPATH = ./ysyxSoC/perip/uart16550/rtl ./ysyxSoC/perip/spi/rtl
VERILATOR_INCFLAGS := $(addprefix -I,$(VERILATOR_INCPATH))
VERILATOR_CFLAGS += -MMD --build -cc \
		    -O3 --x-assign fast --x-initial fast \
		    --noassert --trace \
			$(VERILATOR_INCFLAGS)
BUILD_DIR = ./build
OBJ_DIR = $(BUILD_DIR)/obj_dir
BIN = $(BUILD_DIR)/$(TOPNAME)

default: $(BIN)

$(shell mkdir -p $(BUILD_DIR))

#INCFLAGS = $(addprefix -I, $(INC_PATH))
CFLAGS += -DTOP_NAME="\"V$(TOPNAME)\""
LDFLAGS += -lSDL2 -lSDL2_image
#-include *.d
$(BIN): $(VSRC) $(CSRC)
	@rm -rf $(OBJ_DIR)
	$(VERILATOR) $(VERILATOR_CFLAGS) \
		-top $(TOPNAME) $^ \
		$(addprefix -CFLAGS , $(CFLAGS)) $(addprefix -LDFLAGS , $(LDFLAGS)) \
		--Mdir $(OBJ_DIR) --exe -o $(abspath $(BIN)) \
		--timescale "1ns/1ns" --no-timing


# RUNARGS := $(BIN) $(IMG).bin $(IMG).elf
RUNARGS := $(BIN)

#original makefile

BUILD_DIR = ./build

export PATH := $(PATH):$(abspath ./utils)

test:
	./mill -i __.test

verilog:
	$(call git_commit, "generate verilog")
	mkdir -p $(BUILD_DIR)
	./mill -i __.test.runMain Elaborate -td $(BUILD_DIR)

help:
	./mill -i __.test.runMain Elaborate --help

compile:
	./mill -i __.compile

bsp:
	./mill -i mill.bsp.BSP/install

reformat:
	./mill -i __.reformat

checkformat:
	./mill -i __.checkFormat

clean:
	-rm -rf $(BUILD_DIR)

.PHONY: test verilog help compile bsp reformat checkformat clean

sim: $(BIN)
	$(call git_commit, "sim RTL") # DO NOT REMOVE THIS LINE!!!
	@$(RUNARGS)

-include ../Makefile
