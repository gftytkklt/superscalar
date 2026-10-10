// Link actual nanos gettimeofday and NDL conversion; control only AM uptime.
#include <am.h>
#include <assert.h>
#include <stdio.h>
#include <sys/time.h>
uint32_t NDL_GetTicks(void);
int sys_gettimeofday(struct timeval *, struct timezone *);
static uint64_t uptime;
void ioe_read(int reg, void *buf) {
  assert(reg == AM_TIMER_UPTIME);
  ((AM_TIMER_UPTIME_T *)buf)->us = uptime;
}
int gettimeofday(struct timeval *tv, void *tz) { return sys_gettimeofday(tv, tz); }
int main(void) {
  uint64_t samples[] = {999999, 1000000, 12345678, 4294967000ull};
  uint32_t previous = 0;
  for (unsigned i = 0; i < sizeof(samples)/sizeof(samples[0]); i++) {
    uptime = samples[i];
    struct timeval tv;
    assert(sys_gettimeofday(&tv, NULL) == 0);
    assert(tv.tv_sec == uptime / 1000000 && tv.tv_usec == uptime % 1000000);
    uint32_t tick = NDL_GetTicks();
    assert(tick == uptime / 1000 && tick > previous);
    previous = tick;
  }
  puts("Actual nanos gettimeofday -> NDL_GetTicks conversion/increase PASS (controlled AM uptime)");
}
