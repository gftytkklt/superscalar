#for run npc

# 显式固定默认目标：否则 WITH_SDL=y 时 `$(SRC_AUTO_BIND)` 规则（ifeq 内，位于 default 之前）
# 会成为 make 的首个目标，导致 `make WITH_SDL=y` 只生成 auto_bind.cpp 而不构建 BIN
#（2026-09-01 修复）。
.DEFAULT_GOAL := default

# ---- 持久配置（make menuconfig 生成 npc/.npc_config；命令行传参优先覆盖）----
# 布尔归一化到 *_B（1/y/yes → 1），供判断用；不覆盖原变量（命令行原始值保留，兼容
# `make WAVE=1` / `make WITH_TRACE=n` / `make WITH_SDL=y` 等既有用法）。
-include .npc_config
DIFF ?= 0
WAVE ?= 0
WITH_TRACE ?= 1
WITH_SDL ?= 0
DIFF_B := $(if $(filter 1 y yes Y YES,$(DIFF)),1,0)
WAVE_B := $(if $(filter 1 y yes Y YES,$(WAVE)),1,0)
WITH_TRACE_B := $(if $(filter 1 y yes Y YES,$(WITH_TRACE)),1,0)
WITH_SDL_B := $(if $(filter 1 y yes Y YES,$(WITH_SDL)),1,0)

VSRC = $(shell find $(abspath ./vsrc) -name "*.v")
VSRC += $(shell find $(abspath ./ysyxSoC/perip) -type f -name "*.v")
VSRC += $(shell find $(abspath ./ysyxSoC/generated) -name "ysyxSoCFull.v")

CSRC = $(shell find $(abspath ./csrc) -name "*.cpp")

BUILD_DIR = ./build
INC_PATH ?= $(NPC_HOME)/csrc/include

# ---- NVBoard（阶段 J0，WITH_SDL=1 时接入）----
NVBOARD_HOME ?= $(abspath ../nvboard)
export NVBOARD_HOME
NXDC_FILE = $(abspath ./constr/ysyxSoCFull.nxdc)
SRC_AUTO_BIND = $(BUILD_DIR)/auto_bind.cpp
ifeq ($(WITH_SDL_B), 1)
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
ifeq ($(DIFF_B), 1)
	CFLAGS += -DCONFIG_DIFFTEST
endif
ifeq ($(WAVE_B), 1)
	CFLAGS += -DCONFIG_WAVEFORM
endif
LDFLAGS += $(shell llvm-config --libs) -ldl
# NVBoard（WITH_SDL=1）由 nvboard.mk 提供 SDL 链接；这里只保留非 SDL 情况占位
LDFLAGS += $(if $(filter 1,$(WITH_SDL_B)),$(NVBOARD_ARCHIVE) $(shell sdl2-config --libs) -lSDL2_image -lSDL2_ttf,)
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
#   默认开（保持可出波形）；跑大程序/长回归/纯性能仿真时用 WITH_TRACE=0 重建提速。
VERILATOR_CFLAGS += -MMD --build -cc \
		    -O3 --x-assign fast --x-initial fast \
		    --noassert -Wno-NOTREDOP \
			-autoflush \
			$(VERILATOR_INCFLAGS)
ifeq ($(WITH_TRACE_B), 1)
VERILATOR_CFLAGS += --trace
endif


default: $(BIN)

$(shell mkdir -p $(BUILD_DIR))

#INCFLAGS = $(addprefix -I, $(INC_PATH))
CFLAGS += -DTOP_NAME="\"V$(TOPNAME)\""
#-include *.d
# 编译配置 stamp：把影响 $(BIN) 的编译期开关（DIFF/WAVE/WITH_TRACE/WITH_SDL）记入
# build/.build_cfg。任一开关变化 → stamp 内容变化 → $(BIN) 自动重建（免去手动 rm -rf build
# 的旧坑；运行时开关 WAVE_ON/WAVE_FILE/WAVE_DIV/WAVE_START/WAVE_END/SIM_END 不进 stamp）。
# ⚠️ 必须含 WITH_SDL：否则切 WITH_SDL 不重建，二进制残留 NVBoard（CONFIG_NVBOARD）→
#    WITH_SDL=n 仍弹 NVBoard 窗口且除数 54 串口跑飞（2026-09-01 修复）。
BUILD_CFG = $(BUILD_DIR)/.build_cfg
$(BUILD_CFG): FORCE
	@mkdir -p $(BUILD_DIR)
	@printf 'DIFF=%s\nWAVE=%s\nWITH_TRACE=%s\nWITH_SDL=%s\n' '$(DIFF_B)' '$(WAVE_B)' '$(WITH_TRACE_B)' '$(WITH_SDL_B)' > $@.tmp
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

.PHONY: test verilog help compile bsp reformat checkformat clean menuconfig

# 可视化配置界面（参考 NEMU menuconfig）：编辑 npc/.npc_config 持久配置。
# 命令行传参（make WAVE=1 DIFF=1 ...）仍优先于配置（make 内建优先级）。
menuconfig:
	python3 $(abspath ./scripts/menuconfig.py)
	@echo "已生成/更新 .npc_config；命令行传参可覆盖（如 make WAVE=1 run）"

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
