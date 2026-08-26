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
#   make assert         (阶段2) 用 --assert 模型跑全部用例，断言命中即 FAIL
#   make formal         (阶段2) 运行 formal/*.sby（需 yosys+sby+z3）
#   make clean
# ---------------------------------------------------------------------------

BUILD   := build
OBJ     := $(BUILD)/obj_dir
AOBJ    := $(BUILD)/obj_dirA
AOBJ2   := $(BUILD)/obj_dirA2
IMG     := $(BUILD)/img
MODEL   := $(OBJ)/Vnpc
AMODEL  := $(AOBJ)/VnpcA     # 断言模型（含全部检查）
CMODEL  := $(AOBJ2)/VnpcA    # 断言模型（关掉 cache 旁路检查，聚焦 CSR/除零断言）
RTL     := ../vsrc/ysyx_22040750.v
LDS     := ../scripts/linker-soc.ld
XC      := riscv64-linux-gnu
ASSERTS := $(wildcard assert/*.sv)
SBYS    := $(wildcard formal/*.sby)

CFLAGS  += -fno-pic -march=rv64g -mcmodel=medany -O0 -nostdlib
LDFLAGS := -melf64lriscv -T $(LDS) \
           --defsym=_pmem_start=0x30000000 --defsym=_entry_offset=0x0 \
           --defsym=_sram_start=0x0f000000 --defsym=_stack_offt=0x2000

TESTS   := $(basename $(notdir $(wildcard tests/*.S)))
BINS    := $(patsubst tests/%.S,$(IMG)/%.bin,$(wildcard tests/*.S))
VTRIM   := $(BUILD)/vsrc_fm.v        # 供 yosys/sby 解析的裁剪版 RTL（剥 DPI-C）
T       ?= $(firstword $(TESTS))

.PHONY: all run fst assert assert-cache formal bins clean
all:
	@for n in $(TESTS); do echo "== $$n =="; $(MAKE) run T=$$n; echo; done

run: $(MODEL) $(IMG)/$(T).bin
	./$(MODEL) $(IMG)/$(T).bin

fst: $(MODEL) $(IMG)/$(T).bin
	./$(MODEL) $(IMG)/$(T).bin $(BUILD)/$(T).fst

# ---- 阶段2：仿真期断言（Verilator --assert + bind) -------------------------
# assert:       聚焦 CSR 冒险(bug2) / 除零(bug3) / AXI 协议；关掉 cache 旁路检查
#               避免 bug1 在任何取指时优先命中而盖住其它断言
# assert-cache: 打开全部检查，展示 cache 恒旁路(bug1)在每条用例首拍即被抓
assert: $(CMODEL) $(BINS)
	@fail=0; \
	for n in $(TESTS); do \
	  ./$(CMODEL) $(IMG)/$$n.bin > $(BUILD)/assert_$$n.log 2>&1; \
	  if [ $$? -eq 0 ]; then echo "PASS $$n"; \
	  else echo "FAIL $$n"; fail=1; \
	       grep -m3 -E "%Error" $(BUILD)/assert_$$n.log; fi; \
	done; \
	exit $$fail

assert-cache: $(AMODEL) $(BINS)
	@fail=0; \
	for n in $(TESTS); do \
	  ./$(AMODEL) $(IMG)/$$n.bin > $(BUILD)/assertc_$$n.log 2>&1; \
	  if [ $$? -eq 0 ]; then echo "PASS $$n"; \
	  else echo "FAIL $$n"; fail=1; \
	       grep -m2 -E "%Error" $(BUILD)/assertc_$$n.log; fi; \
	done; \
	exit $$fail

$(AMODEL): tb_main.cpp $(RTL) $(ASSERTS)
	mkdir -p $(AOBJ)
	verilator --binary --assert --trace-fst -O1 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		-Mdir $(AOBJ) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o VnpcA $(RTL) $(ASSERTS) tb_main.cpp

$(CMODEL): tb_main.cpp $(RTL) $(ASSERTS)
	mkdir -p $(AOBJ2)
	verilator --binary --assert --trace-fst -O1 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		+define+CACHE_CHECK_OFF \
		-Mdir $(AOBJ2) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o VnpcA $(RTL) $(ASSERTS) tb_main.cpp

# ---- 阶段2：形式化（SymbiYosys；需 yosys / sby / z3）----------------------
formal: $(BINS) $(VTRIM) $(SBYS)
	@command -v sby >/dev/null 2>&1 || { \
	  echo "SymbiYosys not found (Needs: apt yosys z3 + sby源码安装, 见 npc/README)"; exit 1; }
	@rm -rf formal/dcache formal/div
	@fail=0; \
	for f in $(SBYS); do echo "== $$f"; \
	  (cd formal && sby $$(basename $$f)); \
	  rc=$$?; if [ $$rc -ne 0 ]; then fail=1; echo "## FAIL $$f (see formal/$$(basename $$f .sby)/engine_0/)"; fi; \
	done; \
	exit $$fail

$(VTRIM): formal/trim_rtl.py $(RTL)
	mkdir -p $(BUILD)
	python3 formal/trim_rtl.py $(abspath $(RTL)) $(abspath $(VTRIM))

# ---- 常规目标 --------------------------------------------------------------
$(MODEL): tb_main.cpp $(RTL)
	mkdir -p $(OBJ)
	verilator --binary --trace-fst -O3 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		-Mdir $(OBJ) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o Vnpc $(RTL) tb_main.cpp

bins: $(BINS)

$(IMG)/%.bin: tests/%.S
	mkdir -p $(OBJ) $(IMG)
	$(XC)-gcc $(CFLAGS) -c $< -o $(OBJ)/$*.o
	$(XC)-ld $(LDFLAGS) $(OBJ)/$*.o -o $(OBJ)/$*.elf
	$(XC)-objcopy -O binary -j .text $(OBJ)/$*.elf $@

clean:
	rm -rf $(BUILD)