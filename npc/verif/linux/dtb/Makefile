# Build a platform-specific Linux FDT. Each TARGET has its own DTS and profile.
TARGET ?= nemu
PROFILE := targets/$(TARGET).mk
SOURCE := dts/$(TARGET).dts
OUT ?= ../../build/linux-dtb/$(TARGET)
CPP := cpp
DTC ?= dtc

ifeq ($(wildcard $(PROFILE)),)
$(error Unknown TARGET=$(TARGET): missing $(PROFILE))
endif
ifeq ($(wildcard $(SOURCE)),)
$(error Unknown TARGET=$(TARGET): missing $(SOURCE))
endif
include $(PROFILE)

.PHONY: all
all:
	@mkdir -p $(OUT)
	$(CPP) -x assembler-with-cpp -P -nostdinc -undef -D__DTS__ $(DT_CPPFLAGS) $(SOURCE) > $(OUT)/$(TARGET).dts
	$(DTC) -I dts -O dtb -p 4096 -o $(OUT)/$(TARGET).dtb $(OUT)/$(TARGET).dts
