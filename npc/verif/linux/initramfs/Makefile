# NEMU native initramfs: reuse the M0 static BusyBox and kernel gen_init_cpio.
SHELL := /bin/bash

BUSYBOX ?= $(HOME)/linux-m0/busybox-1.36.1/busybox
GEN_INIT_CPIO ?= $(HOME)/linux-m0/linux-6.1.188/usr/gen_init_cpio
OUT ?= ../../build/linux-initramfs/nemu
MANIFEST := $(OUT)/initramfs.list
ARCHIVE := $(OUT)/initramfs.cpio.gz

.PHONY: all
all: $(ARCHIVE)

$(OUT):
	mkdir -p "$@"

$(ARCHIVE): init Makefile $(BUSYBOX) $(GEN_INIT_CPIO) | $(OUT)
	@printf '%s\n' \
		'dir /bin 0755 0 0' \
		'dir /dev 0755 0 0' \
		'dir /proc 0755 0 0' \
		'dir /sys 0755 0 0' \
		'dir /tmp 1777 0 0' \
		'slink /bin/sh busybox 0777 0 0' \
		'slink /bin/mount busybox 0777 0 0' \
		'slink /bin/ls busybox 0777 0 0' \
		'slink /bin/cat busybox 0777 0 0' \
		'slink /bin/echo busybox 0777 0 0' \
		'nod /dev/console 0600 0 0 c 5 1' \
		'nod /dev/null 0666 0 0 c 1 3' > "$(MANIFEST)"
	@printf 'file /bin/busybox %s 0755 0 0\n' "$(abspath $(BUSYBOX))" >> "$(MANIFEST)"
	@printf 'file /init %s 0755 0 0\n' "$(abspath init)" >> "$(MANIFEST)"
	@set -euo pipefail; \
		trap 'rm -f "$(ARCHIVE).tmp"' EXIT; \
		"$(GEN_INIT_CPIO)" -t 0 "$(MANIFEST)" | gzip -n -9 > "$(ARCHIVE).tmp"; \
		mv "$(ARCHIVE).tmp" "$(ARCHIVE)"
