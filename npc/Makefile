#for run npc

VSRC = $(shell find $(abspath ./vsrc) -name "*.v")
VSRC += $(shell find $(abspath ./ysyxSoC/perip) -type f -name "*.v")
VSRC += $(shell find $(abspath ./ysyxSoC/generated) -name "ysyxSoCFull.v")

CSRC = $(shell find $(abspath ./csrc) -name "*.cpp")

BUILD_DIR = ./build
INC_PATH ?= $(NPC_HOME)/csrc/include

# ---- NVBoard（阶段 J0，WITH_SDL=y 时接入）----
NVBOARD_HOME ?= $(abspath ../nvboard)
export NVBOARD_HOME
NXDC_FILE = $(abspath ./constr/ysyxSoCFull.nxdc)
SRC_AUTO_BIND = $(BUILD_DIR)/auto_bind.cpp
ifeq ($(WITH_SDL), y)
# 约束文件 → 引脚绑定代码（auto_bind.cpp：nvboard_bind_all_pins）
$(SRC_AUTO_BIND): $(NXDC_FILE)
	@mkdir -p $(BUILD_DIR)
	python3 $(NVBOARD_HOME)/scripts/auto_pin_bind.py $< $@
CSRC += $(SRC_AUTO_BIND)
CFLAGS += -DCONFIG_NVBOARD
include $(NVBOARD_HOME)/scripts/nvboard.mk   # 追加 NVBOARD_USR_INC 到 INC_PATH + SDL 链接
endif

INCLUDES = $(addprefix -I, $(INC_PATH))
CFLAGS += -MMD -O3 $(INCLUDES) -I/usr/lib/llvm-12/include -std=c++14   -fno-exceptions -D_GNU_SOURCE -D__STDC_CONSTANT_MACROS -D__STDC_LIMIT_MACROS -fPIE
ifeq ($(DIFF), 1)
	CFLAGS += -DCONFIG_DIFFTEST
endif
ifeq ($(WAVE), 1)
	CFLAGS += -DCONFIG_WAVEFORM
endif
LDFLAGS += $(shell llvm-config --libs) -ldl
# NVBoard（WITH_SDL=y）由 nvboard.mk 提供 SDL 链接；这里只保留非 SDL 情况占位
LDFLAGS += $(if $(filter y,$(WITH_SDL)),$(NVBOARD_ARCHIVE) $(shell sdl2-config --libs) -lSDL2_image -lSDL2_ttf,)
OBJ_DIR = $(BUILD_DIR)/obj_dir
BIN = $(BUILD_DIR)/$(TOPNAME)

OBJS = $(CSRC:%.cpp=$(OBJ_DIR)/%.o)
-include $(OBJS:.o=.d)

# verilator flag
TOPNAME = ysyxSoCFull
VERILATOR = verilator
VERILATOR_INCPATH = ./ysyxSoC/perip/uart16550/rtl ./ysyxSoC/perip/spi/rtl
VERILATOR_INCFLAGS := $(addprefix -I,$(VERILATOR_INCPATH))
# WITH_TRACE: 是否编译 Verilator trace 支持（会显著拖慢仿真，即使运行时不 dump）。
#   默认 y（保持可出波形）；跑大程序/长回归/纯性能仿真时用 WITH_TRACE=n 重建提速。
WITH_TRACE ?= y
VERILATOR_CFLAGS += -MMD --build -cc \
		    -O3 --x-assign fast --x-initial fast \
		    --noassert -Wno-NOTREDOP \
			-autoflush \
			$(VERILATOR_INCFLAGS)
ifeq ($(WITH_TRACE), y)
VERILATOR_CFLAGS += --trace
endif


default: $(BIN)

$(shell mkdir -p $(BUILD_DIR))

#INCFLAGS = $(addprefix -I, $(INC_PATH))
CFLAGS += -DTOP_NAME="\"V$(TOPNAME)\""
LDFLAGS += $(if $(filter y,$(WITH_SDL)),-lSDL2 -lSDL2_image,)
#-include *.d
# 编译配置 stamp：把影响 $(BIN) 的编译期开关（DIFF/WAVE/WITH_TRACE）记入 build/.build_cfg。
# 任一开关变化 → stamp 内容变化 → $(BIN) 自动重建（免去手动 rm -rf build 的旧坑；
# 运行时开关 WAVE_ON/WAVE_FILE/WAVE_DIV/WAVE_START/WAVE_END/SIM_END 不进 stamp，无需重建）。
BUILD_CFG = $(BUILD_DIR)/.build_cfg
$(BUILD_CFG): FORCE
	@mkdir -p $(BUILD_DIR)
	@printf 'DIFF=%s\nWAVE=%s\nWITH_TRACE=%s\n' '$(DIFF)' '$(WAVE)' '$(WITH_TRACE)' > $@.tmp
	@cmp -s $@ $@.tmp || cp $@.tmp $@
	@rm -f $@.tmp
FORCE:
.PHONY: FORCE

$(BIN): $(VSRC) $(CSRC) $(BUILD_CFG)
	@rm -rf $(OBJ_DIR)
	$(VERILATOR) $(VERILATOR_CFLAGS) \
		-top $(TOPNAME) $(VSRC) $(CSRC) \
		$(addprefix -CFLAGS , $(CFLAGS)) $(addprefix -LDFLAGS , $(LDFLAGS)) \
		--Mdir $(OBJ_DIR) --exe -o $(abspath $(BIN)) \
		--timescale "1ns/1ns" --no-timing


# RUNARGS := $(BIN) $(IMG).bin $(IMG).elf
RUNARGS := $(BIN) $(IMG)
DIFF_NEMU = $(NEMU_HOME)/build/riscv64-nemu-interpreter-so

RUNARGS += $(DIFF_NEMU)

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
	@echo "Running $(CSRC)"
	@rm -f $(BUILD_DIR)/soc.vcd    # 每次 run 前清理旧波形，避免残留大文件误导
	@$(RUNARGS)
	@if [ "$(WAVE_ON)" != "1" ] && [ -f $(BUILD_DIR)/soc.vcd ]; then \
		rm -f $(BUILD_DIR)/soc.vcd; \
		echo "waveform: removed $(BUILD_DIR)/soc.vcd (WAVE_ON!=1, 如需波形: 先 WAVE=1 重建再 WAVE_ON=1 运行)"; \
	fi

# 显式保留波形的一次性运行：需先用 WAVE=1 重建二进制（改 CFLAGS 需 rm -rf build）。
#   WAVE_KEEP=1 时 sim 结束不删波形；WAVE_FILE=/path/xx.vcd 可指定输出路径。
clean-wave:
	rm -f $(BUILD_DIR)/soc.vcd

.PHONY: clean-wave

-include ../Makefile
