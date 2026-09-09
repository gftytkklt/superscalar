HAS_NAVY = 1
RAMDISK_FILE = build/ramdisk.img

NAME = nanos-lite
SRCS = $(shell find -L ./src/ -name "*.c" -o -name "*.cpp" -o -name "*.S")

# The NPC SoC has no disk device: embed the whole fsimg (ramdisk) into the
# kernel image instead. Other platforms use the AM disk device.
# (Must come BEFORE including the AM Makefile so the define reaches the
# pattern rules' flags.)
ifeq ($(ARCH),riscv64-npc)
CFLAGS += -DKERNEL_EMBED_RAMDISK
ASFLAGS += -DKERNEL_EMBED_RAMDISK
endif

include $(AM_HOME)/Makefile

ifeq ($(ARCH),native)
ISA = am_native
else
INC_PATH += include $(NAVY_HOME)/libs/libc/include
endif

./src/resources.S: $(RAMDISK_FILE)
	@touch $@

ifeq ($(HAS_NAVY),)
files = $(RAMDISK_FILE) src/files.h src/syscall.h
# create an empty file if it does not exist
$(foreach f,$(files),$(if $(wildcard $f),, $(shell touch $f)))
else

ifeq ($(wildcard $(NAVY_HOME)/libs/libos/src/syscall.h),)
  $(error $$NAVY_HOME must be a Navy-apps repo)
endif

# When virtual memory is enabled, navy apps must be linked to 0x40000000
HAS_VME := $(shell grep -q '^#define HAS_VME' include/common.h && echo 1)

update:
	$(MAKE) -s -C $(NAVY_HOME) ISA=$(ISA) $(if $(HAS_VME),VME=1,) ramdisk
	@ln -sf $(NAVY_HOME)/build/ramdisk.img $(RAMDISK_FILE)
	@ln -sf $(NAVY_HOME)/build/ramdisk.h src/files.h
	@ln -sf $(NAVY_HOME)/libs/libos/src/syscall.h src/syscall.h

.PHONY: update
endif
