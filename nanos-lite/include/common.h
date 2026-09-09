#ifndef __COMMON_H__
#define __COMMON_H__

/* Uncomment these macros to enable corresponding functionality. */
#define HAS_CTE
#define HAS_VME

// for different stage nanos-lite (mutually exclusive; define exactly ONE):
//#define TEST_DUMMY        // PA3: batch system, ramdisk dummy, naive_uload
//#define TEST_FILE         // PA3.5: single user program, fs, naive_uload
//#define TEST_KLOAD        // PA4.1 stage1: kernel threads, no loader
// #define TEST_NTERM        // single process: NTerm + execvp (manual input)
//#define MULTIPROGRAM      // PA4.1 stage2-4: multiprogram + execve
//#define TIME_SHARING      // PA4.4: time-sharing (preemptive multitasking)
#define FG_PROCESS        // PA4.5: foreground-process demo (F1/F2/F3 switch pal/bird/nslider)
#if defined(TEST_KLOAD) || defined(MULTIPROGRAM) || defined(TIME_SHARING) || defined(FG_PROCESS)
# define MULTITASK         // has process scheduling (schedule())
#endif

// enable system call trace (strace) in nanos-lite
// #define STRACE

#include <am.h>
#include <klib.h>
#include <klib-macros.h>
#include <debug.h>

#endif
