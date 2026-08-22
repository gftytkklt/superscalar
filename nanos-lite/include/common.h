#ifndef __COMMON_H__
#define __COMMON_H__

/* Uncomment these macros to enable corresponding functionality. */
#define HAS_CTE
//#define HAS_VME
//#define MULTIPROGRAM
//#define TIME_SHARING

// for different stage nanos-lite
// #define TEST_DUMMY
// #define TEST_FILE
#define TEST_KLOAD

// enable system call trace (strace) in nanos-lite
// #define STRACE

#include <am.h>
#include <klib.h>
#include <klib-macros.h>
#include <debug.h>

#endif
