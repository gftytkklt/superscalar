REPO_PATH = repo
ifeq ($(wildcard repo/include/ONScripter.h),)
  $(shell git clone --depth=1 git@github.com:NJU-ProjectN/onscripter-navy.git $(REPO_PATH))
endif

NAME = onscripter
SRCS = $(shell find $(REPO_PATH)/src/ -name "*.cpp")
INC_PATH = $(REPO_PATH)/include
LIBS += libminiSDL libSDL_ttf libSDL_image libSDL_mixer
include $(NAVY_HOME)/Makefile

# For ISA=native the app runs hosted and links the system C++ runtime
# (libstdc++), so the freestanding flags must go. Other ISAs (riscv64) have
# no C++ runtime available; the ONScripter sources use no exceptions/RTTI/STL
# (verified by grep: only libc rand()), so they compile fine with them.
ifeq ($(ISA),native)
CXXFLAGS := $(filter-out -ffreestanding -fno-rtti -fno-exceptions,$(CXXFLAGS))
endif

init:;
.PHONY: init
