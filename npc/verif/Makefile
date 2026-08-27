# ---------------------------------------------------------------------------
# Standalone RTL micro-verification for npc/vsrc/ysyx_22040750.v
#
# The CPU core is compiled by Verilator together with tb_main.cpp (a tiny
# AXI4-slave memory model + clock/reset harness) and booted from a binary
# image at 0x30000000 (PC reset 0x2ffffffc, snpc = pc+4 does the boot jump).
#
# 依赖完整性：每个构建产物都带一个"依赖指纹"文件(.deps_*)。
#   - 源文件内容变化  -> md5 变 -> 指纹更新 -> 产物重建；
#   - 断言文件增删    -> 文件清单变化 -> 指纹更新 -> 产物重建
#     （普通 mtime 比较感知不到"删除"，这是靠指纹清单兜底的）
# 杜绝"改了源码却拿旧模型跑出新结论"。修改 RTL 后直接跑任意目标即可，
# 不需要手动 clean。
#
# Usage:
#   make                 build the model, then run every tests/*.S
#   make run  T=bug2_csr run a single test
#   make fst  T=bug2_csr run a single test and keep its waveform
#   make assert          阶段2断言回归（关 bug1 检查，聚焦 bug2/bug3）
#   make assert-cache    阶段2断言回归（含 bug1：cache 旁路检查全开）
#   make formal          阶段2形式化（yosys/sby/z3，跑全部 formal/*.sby）
#   make clean
# ---------------------------------------------------------------------------

BUILD    := build
OBJ      := $(BUILD)/obj_dir
AOBJ     := $(BUILD)/obj_dirA
AOBJ2    := $(BUILD)/obj_dirA2
IMG      := $(BUILD)/img
MODEL    := $(OBJ)/Vnpc
AMODEL   := $(AOBJ)/VnpcA     # 断言模型（含全部检查）
CMODEL   := $(AOBJ2)/VnpcA    # 断言模型（关掉 cache 旁路检查，聚焦 CSR/除零断言）
RTL      := ../vsrc/ysyx_22040750.v
LDS      := ../scripts/linker-soc.ld
XC       := riscv64-linux-gnu
ASSERTS  := $(wildcard assert/*.sv)
SBYS     := $(wildcard formal/*.sby)
VTRIM    := $(BUILD)/vsrc_fm.v        # 供 yosys/sby 解析的裁剪版 RTL

DEPS_MODEL  := tb_main.cpp $(RTL)
DEPS_AMODEL := tb_main.cpp $(RTL) $(ASSERTS)
STAMP_MODEL  := $(BUILD)/.deps_model
STAMP_AMODEL := $(BUILD)/.deps_amodel
STAMP_CMODEL := $(BUILD)/.deps_cmodel
STAMP_VTRIM  := $(BUILD)/.deps_vtrim

CFLAGS  += -fno-pic -march=rv64g -mcmodel=medany -O0 -nostdlib
LDFLAGS := -melf64lriscv -T $(LDS) \
           --defsym=_pmem_start=0x30000000 --defsym=_entry_offset=0x0 \
           --defsym=_sram_start=0x0f000000 --defsym=_stack_offt=0x2000

TESTS   := $(basename $(notdir $(wildcard tests/*.S)))
BINS    := $(patsubst tests/%.S,$(IMG)/%.bin,$(wildcard tests/*.S))
T       ?= $(firstword $(TESTS))

# 指纹生成：清单+md5。与旧内容一致则不落盘（保持 mtime，避免无谓重建），
# 有差异才替换 —— 之后下游目标因指纹变新而重建。
# $(1)=stamp 路径, $(2)=依赖列表
define deps_stamp
	@mkdir -p $(BUILD)
	@{ echo "# auto deps fingerprint"; \
	   echo "files: $(strip $(2))"; \
	   for f in $(strip $(2)); do md5sum $$f 2>/dev/null; done; } > $(1).tmp
	@if cmp -s $(1) $(1).tmp; then rm -f $(1).tmp; else mv -f $(1).tmp $(1); fi
endef

.PHONY: all run fst assert assert-cache formal bins clean FORCE
.DEFAULT_GOAL := all
FORCE: ;

all:
	@for n in $(TESTS); do echo "== $$n =="; $(MAKE) run T=$$n; echo; done

run: $(MODEL) $(IMG)/$(T).bin
	./$(MODEL) $(IMG)/$(T).bin

fst: $(MODEL) $(IMG)/$(T).bin
	./$(MODEL) $(IMG)/$(T).bin $(BUILD)/$(T).fst

bins: $(BINS)

$(IMG)/%.bin: tests/%.S
	mkdir -p $(OBJ) $(IMG)
	$(XC)-gcc $(CFLAGS) -c $< -o $(OBJ)/$*.o
	$(XC)-ld $(LDFLAGS) $(OBJ)/$*.o -o $(OBJ)/$*.elf
	$(XC)-objcopy -O binary -j .text $(OBJ)/$*.elf $@

# ---- 常规模型 --------------------------------------------------------------
$(MODEL): $(DEPS_MODEL) $(STAMP_MODEL)
	mkdir -p $(OBJ)
	verilator --binary --trace-fst -O3 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		-Mdir $(OBJ) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o Vnpc $(RTL) tb_main.cpp

$(STAMP_MODEL): $(DEPS_MODEL) FORCE
	$(call deps_stamp,$(STAMP_MODEL),$(DEPS_MODEL))

# ---- 阶段2：仿真期断言（Verilator --assert + bind) -------------------------
# assert:       聚焦 CSR 冒险(bug2) / 除零(bug3)；关掉 cache 旁路检查(bug1)，
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

$(AMODEL): $(DEPS_AMODEL) $(STAMP_AMODEL)
	mkdir -p $(AOBJ)
	verilator --binary --assert --trace-fst -O1 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		-Mdir $(AOBJ) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o VnpcA $(RTL) $(ASSERTS) tb_main.cpp

$(STAMP_AMODEL): $(DEPS_AMODEL) FORCE
	$(call deps_stamp,$(STAMP_AMODEL),$(DEPS_AMODEL))

$(CMODEL): $(DEPS_AMODEL) $(STAMP_CMODEL)
	mkdir -p $(AOBJ2)
	verilator --binary --assert --trace-fst -O1 -j 0 -Wno-fatal -Wno-DECLFILENAME \
		+define+CACHE_CHECK_OFF \
		-Mdir $(AOBJ2) --top-module ysyx_22040750 --timescale 1ns/1ns --no-timing \
		-o VnpcA $(RTL) $(ASSERTS) tb_main.cpp

$(STAMP_CMODEL): $(DEPS_AMODEL) FORCE
	$(call deps_stamp,$(STAMP_CMODEL),$(DEPS_AMODEL))

# ---- 阶段2：形式化（SymbiYosys；需 yosys / sby / z3）----------------------
formal: $(BINS) $(SBYS) $(VTRIM) $(STAMP_VTRIM)
	@command -v sby >/dev/null 2>&1 || { \
	  echo "SymbiYosys not found (Needs: apt yosys z3 + sby源码安装, 见 npc/README)"; exit 1; }
	@rm -rf formal/dcache formal/div
	@fail=0; \
	for f in $(SBYS); do echo "== $$f"; \
	  (cd formal && sby $$(basename $$f)); \
	  rc=$$?; if [ $$rc -ne 0 ]; then fail=1; echo "## FAIL $$f (see formal/$$(basename $$f .sby)/engine_0/)"; fi; \
	done; \
	exit $$fail

$(VTRIM): formal/trim_rtl.py $(RTL) $(STAMP_VTRIM)
	mkdir -p $(BUILD)
	python3 formal/trim_rtl.py $(abspath $(RTL)) $(abspath $(VTRIM))

$(STAMP_VTRIM): formal/trim_rtl.py $(RTL) FORCE
	$(call deps_stamp,$(STAMP_VTRIM),formal/trim_rtl.py $(RTL))

clean:
	rm -rf $(BUILD)