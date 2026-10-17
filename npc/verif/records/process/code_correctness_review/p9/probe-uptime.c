#include <am.h>
#include <NDL.h>
#include <stdio.h>
static uint32_t tick;
uint32_t NDL_GetTicks(void){return tick;}
int NDL_PollEvent(char *p,int n){return 0;}
int main(void){AM_TIMER_UPTIME_T a,b;tick=0xffffffff;ioe_read(AM_TIMER_UPTIME,&a);tick=0;ioe_read(AM_TIMER_UPTIME,&b);printf("before_us=%llu after_us=%llu backwards=%d\n",(unsigned long long)a.us,(unsigned long long)b.us,b.us<a.us);return !(a.us==4294967295000ull && b.us==0);}
