#include <common.h>
#include <stdio.h>
#include <stdlib.h>
void halt(int c){exit(90);}void putch(char c){}
void __am_timer_init(void){}
void __am_timer_rtc(AM_TIMER_RTC_T*p){}void __am_timer_uptime(AM_TIMER_UPTIME_T*p){}
void __am_input_keybrd(AM_INPUT_KEYBRD_T*p){}void __am_gpu_config(AM_GPU_CONFIG_T*p){}void __am_gpu_status(AM_GPU_STATUS_T*p){}void __am_gpu_fbdraw(AM_GPU_FBDRAW_T*p){}
__asm__(".pushsection .data\n.globl ramdisk_start,ramdisk_end\nramdisk_start:\n.byte 1\nramdisk_end:\n.popsection\n");
#include "abstract-machine/am/src/riscv/npc/ioe.c"
#include "nanos-lite/src/disk.c"
int main(void){setbuf(stdout,NULL);ioe_init();printf("calling init_disk with embedded image present\n");init_disk();printf("reached fallback\n");return 0;}
