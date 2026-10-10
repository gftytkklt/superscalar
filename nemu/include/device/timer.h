#ifndef NEMU_DEVICE_TIMER_H
#define NEMU_DEVICE_TIMER_H
#include <common.h>

#if defined(CONFIG_RV64) && defined(CONFIG_DEVICE) && !defined(CONFIG_TARGET_AM)
void nemu_timer_select(const char *source);
bool nemu_timer_legacy(void);
bool nemu_timer_mtip(void);
uint64_t nemu_timer_time(void);
void init_mtimer(void);
#else
static inline bool nemu_timer_legacy(void) { return true; }
static inline bool nemu_timer_mtip(void) { return false; }
// No autonomous host clock or device source in the REF/AM build.
static inline uint64_t nemu_timer_time(void) { return 0; }
#endif
#endif
