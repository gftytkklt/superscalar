# Existing sources only. Independent P8 output; original P4/M0 assets preserved.
ROOT := $(abspath ../../../..)
ARCH ?= riscv64-nemu
OUT ?= $(ROOT)/npc/verif/build/linux-boot/nemu-p8
KERNEL_SRC ?= $(ROOT)/npc/verif/build/linux-kernel/nemu-src
KERNEL_BASE ?= $(ROOT)/npc/verif/build/linux-kernel/nemu/.config
KERNEL_OUT ?= $(ROOT)/npc/verif/build/linux-kernel/nemu-p8
OPENSBI_SRC ?= $(HOME)/linux-m0/opensbi
OPENSBI_OUT ?= $(OUT)/opensbi
CROSS_COMPILE ?= riscv64-linux-gnu-
INITRAMFS_OUT ?= $(ROOT)/npc/verif/build/linux-initramfs/nemu-p8
JOBS ?= 8
export CCACHE_DISABLE := 1
.PHONY: all kernel firmware dtb initramfs
all: kernel firmware dtb
initramfs:
	$(MAKE) -C ../initramfs OUT=$(INITRAMFS_OUT)
kernel: initramfs
	@test -f $(KERNEL_BASE) && test -f $(KERNEL_SRC)/Makefile
	@mkdir -p $(KERNEL_OUT) $(OUT)
	@test -f $(KERNEL_OUT)/.config || cp $(KERNEL_BASE) $(KERNEL_OUT)/.config
	$(KERNEL_SRC)/scripts/config --file $(KERNEL_OUT)/.config --enable SERIAL_OF_PLATFORM --set-str INITRAMFS_SOURCE $(INITRAMFS_OUT)/initramfs.cpio.gz
	$(MAKE) -C $(KERNEL_SRC) O=$(KERNEL_OUT) ARCH=riscv CROSS_COMPILE=$(CROSS_COMPILE) olddefconfig
	$(MAKE) -C $(KERNEL_SRC) O=$(KERNEL_OUT) ARCH=riscv CROSS_COMPILE=$(CROSS_COMPILE) -j$(JOBS) Image
	@diff -u $(KERNEL_BASE) $(KERNEL_OUT)/.config > $(OUT)/kernel-config.diff || test $$? -eq 1
firmware:
	python3 configure_opensbi.py $(OPENSBI_SRC) $(OPENSBI_OUT)
	$(MAKE) -C $(OPENSBI_SRC) O=$(OPENSBI_OUT) PLATFORM=generic CROSS_COMPILE=$(CROSS_COMPILE) \
		PLATFORM_RISCV_XLEN=64 PLATFORM_RISCV_ISA=rv64ima_zicsr_zifencei PLATFORM_RISCV_ABI=lp64 \
		FW_TEXT_START=0x80000000 FW_JUMP_ADDR=0x80200000 FW_JUMP_FDT_ADDR=0x82200000 -j$(JOBS)
dtb:
	$(MAKE) -C ../dtb TARGET=nemu

# Same build -> image -> execution convention as the AM application Makefiles.
# This directory currently supplies only the NEMU native RV64 platform profile.
.PHONY: image nemu run check-arch
check-arch:
	@test "$(ARCH)" = riscv64-nemu || { echo "Unsupported ARCH=$(ARCH); supported: riscv64-nemu" >&2; exit 1; }
image: check-arch all
nemu: check-arch
	@grep -qx 'CONFIG_RV64=y' $(ROOT)/nemu/.config && \
	 grep -qx 'CONFIG_TARGET_NATIVE_ELF=y' $(ROOT)/nemu/.config && \
	 grep -qx 'CONFIG_DEVICE=y' $(ROOT)/nemu/.config && \
	 grep -qx 'CONFIG_HAS_SERIAL=y' $(ROOT)/nemu/.config || \
	 { echo 'NEMU must already be configured for native RV64 with DEVICE/SERIAL' >&2; exit 1; }
	$(MAKE) -C $(ROOT)/nemu -o compile_git app
run: image nemu
	bash ./run.sh --interactive --out=$(OUT)
