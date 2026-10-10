# NEMU native profile. PMEM comes from the emulator build configuration.
NEMU_CONFIG ?= ../../../../nemu/.config
ifeq ($(wildcard $(NEMU_CONFIG)),)
$(error Missing NEMU_CONFIG=$(NEMU_CONFIG))
endif
NEMU_MBASE := $(shell sed -n 's/^CONFIG_MBASE=//p' $(NEMU_CONFIG))
NEMU_MSIZE := $(shell sed -n 's/^CONFIG_MSIZE=//p' $(NEMU_CONFIG))
ifeq ($(strip $(NEMU_MBASE)),)
$(error NEMU_CONFIG needs CONFIG_MBASE)
endif
ifeq ($(strip $(NEMU_MSIZE)),)
$(error NEMU_CONFIG needs CONFIG_MSIZE)
endif

# Target clock contract: NEMU RTC reads are currently in microseconds.
# MTIMER and CSR time use the same native microsecond clock.
TIMEBASE_HZ ?= 1000000
DT_CPPFLAGS += -DDT_RAM_BASE=$(NEMU_MBASE)
DT_CPPFLAGS += -DDT_RAM_UNIT=$(patsubst 0x%,%,$(NEMU_MBASE))
DT_CPPFLAGS += -DDT_RAM_SIZE=$(NEMU_MSIZE)
DT_CPPFLAGS += -DDT_TIMEBASE_HZ=$(TIMEBASE_HZ)
