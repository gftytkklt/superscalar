#include <am.h>
#include <elf.h>
#include <sys/time.h>
#include <sys/types.h>
#include <SDL.h>
#define S(t,n) _Static_assert(sizeof(t)==n,#t)
#define O(t,f,n) _Static_assert(offsetof(t,f)==n,#t "." #f)
S(void *,8);S(long,8);S(int,4);S(size_t,8);S(off_t,8);S(struct timeval,16);O(struct timeval,tv_usec,8);
S(Elf64_Ehdr,64);S(Elf64_Phdr,56);O(Elf64_Phdr,p_offset,8);O(Elf64_Phdr,p_vaddr,16);O(Elf64_Phdr,p_filesz,32);O(Elf64_Phdr,p_memsz,40);
S(Context,288);O(Context,pdir,0);O(Context,gpr,0);O(Context,mcause,256);O(Context,mstatus,264);O(Context,mepc,272);O(Context,np,280);
S(Area,16);S(AddrSpace,32);O(AddrSpace,area,8);O(AddrSpace,ptr,24);S(Event,32);
S(AM_TIMER_UPTIME_T,8);S(AM_INPUT_KEYBRD_T,8);O(AM_INPUT_KEYBRD_T,keycode,4);
S(AM_GPU_CONFIG_T,16);O(AM_GPU_CONFIG_T,width,4);S(AM_GPU_FBDRAW_T,32);O(AM_GPU_FBDRAW_T,pixels,8);O(AM_GPU_FBDRAW_T,w,16);O(AM_GPU_FBDRAW_T,sync,24);
S(AM_AUDIO_CONFIG_T,8);S(AM_AUDIO_CTRL_T,12);O(AM_AUDIO_CTRL_T,channels,4);O(AM_AUDIO_CTRL_T,samples,8);S(AM_AUDIO_STATUS_T,4);S(AM_AUDIO_PLAY_T,16);
S(AM_DISK_CONFIG_T,12);S(AM_DISK_BLKIO_T,24);O(AM_DISK_BLKIO_T,buf,8);O(AM_DISK_BLKIO_T,blkno,16);
S(SDL_KeyboardEvent,2);S(SDL_Event,24);O(SDL_AudioSpec,callback,16);S(SDL_AudioSpec,32);
int layout_probe;
