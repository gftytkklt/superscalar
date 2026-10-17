#include <stdint.h>
#include <stddef.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <setjmp.h>
#include <stdio.h>
#include <unistd.h>
#include <dirent.h>
#include <termios.h>
#include <utmp.h>
_Static_assert(sizeof(void *) == 8 && sizeof(long) == 8 && sizeof(int) == 4, "LP64");
_Static_assert(sizeof(size_t) == 8 && sizeof(ssize_t) == 8 && sizeof(off_t) == 8, "lengths");
_Static_assert(sizeof(struct timeval) == 16 && offsetof(struct timeval, tv_usec) == 8, "timeval");
_Static_assert(sizeof(jmp_buf) == 208, "RV64 integer and FP slots reserved");
#define FIELD(n, expr) const unsigned long n = (expr)
FIELD(size_stat, sizeof(struct stat));
FIELD(align_stat, _Alignof(struct stat));
FIELD(off_stat_size, offsetof(struct stat, st_size));
FIELD(off_stat_atim, offsetof(struct stat, st_atim));
FIELD(size_dirent, sizeof(struct dirent));
FIELD(off_dirent_name, offsetof(struct dirent, d_name));
FIELD(size_DIR, sizeof(DIR));
FIELD(size_termios, sizeof(struct termios));
FIELD(size_utmp, sizeof(struct utmp));
FIELD(size_FILE, sizeof(FILE));
FIELD(size_reent, sizeof(struct _reent));
FIELD(size_mode, sizeof(mode_t));
FIELD(size_pid, sizeof(pid_t));
FIELD(size_time, sizeof(time_t));
FIELD(size_clock, sizeof(clock_t));
FIELD(size_maxalign, _Alignof(max_align_t));
FIELD(size_read_return, sizeof(read(0, 0, 0)));
