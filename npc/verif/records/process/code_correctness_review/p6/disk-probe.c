#include <common.h>
#include <stdio.h>
#include <stdlib.h>
static unsigned char media[1024];static int present=1;
void halt(int c){exit(90);}void putch(char c){}
void ioe_read(int r,void*p){assert(r==AM_DISK_CONFIG);*(AM_DISK_CONFIG_T*)p=(AM_DISK_CONFIG_T){.present=present,.blksz=512,.blkcnt=2};}
void ioe_write(int r,void*p){assert(r==AM_DISK_BLKIO);AM_DISK_BLKIO_T*x=p;if(x->blkno>=2){printf("out_of_disk blk=%d count=%d\n",x->blkno,x->blkcnt);exit(42);}if(x->write)memcpy(media+x->blkno*512,x->buf,512);else memcpy(x->buf,media+x->blkno*512,512);}
__asm__(".pushsection .data\n.globl ramdisk_start,ramdisk_end\nramdisk_start:\n.byte 1,2,3,4,5,6,7,8\nramdisk_end:\n.popsection\n");
#include "nanos-lite/src/disk.c"
int main(int argc,char**argv){setbuf(stdout,NULL);for(int i=0;i<1024;i++)media[i]=i;const char*s=argv[1];if(!strcmp(s,"embed"))present=0;init_disk();unsigned char buf[16]={0};
 if(!strcmp(s,"normal")){disk_read(buf,510,8);printf("cross_read=%u,%u,%u,%u\n",buf[0],buf[1],buf[2],buf[7]);memset(buf,0x42,8);disk_write(buf,510,8);printf("rmw_edges=%x,%x payload=%x,%x\n",media[509],media[518],media[510],media[517]);}
 if(!strcmp(s,"range"))disk_read(buf,1024,1);
 if(!strcmp(s,"embed")){printf("read_tail=%zu\n",disk_read(buf,6,8));printf("bytes=%u,%u\n",buf[0],buf[1]);printf("write_tail=%zu\n",disk_write(buf,7,8));printf("eof=%zu\n",disk_read(buf,8,1));}
 return 0;}
