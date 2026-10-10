#ifndef NEMU_DEVICE_SERIAL_H
#define NEMU_DEVICE_SERIAL_H
#include <common.h>
#if defined(CONFIG_RV64) && defined(CONFIG_DEVICE) && !defined(CONFIG_TARGET_AM)
void nemu_serial_input(const char *path);
#endif
#endif
