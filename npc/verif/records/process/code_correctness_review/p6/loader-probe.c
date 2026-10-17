#include <proc.h>
#include <fs.h>
#include <elf.h>
#include <stdlib.h>
#include <stdio.h>
static unsigned char image[8192]; static size_t image_size=sizeof(image), pos;
static unsigned char pages[1024*1024] __attribute__((aligned(4096))); static size_t used;
static struct {uintptr_t va;void *pa;} maps[256]; static int nmaps,duplicate;
static Context ctx; static int closes; static int missing;
Area heap; PCB *current,*fg_pcb;
void halt(int c){exit(c?90:0);} void putch(char c){}
void *new_page(size_t n){void *p=pages+used;used+=n*4096;assert(used<=sizeof(pages));return p;}
void protect(AddrSpace *as){as->area=(Area){(void*)0x40000000,(void*)0x80000000};as->ptr=(void*)1;as->pgsize=4096;}
void map(AddrSpace *as,void *v,void *p,int prot){for(int i=0;i<nmaps;i++)if(maps[i].va==(uintptr_t)v){maps[i].pa=p;duplicate++;return;}maps[nmaps].va=(uintptr_t)v;maps[nmaps++].pa=p;}
static void *pa(uintptr_t v){for(int i=0;i<nmaps;i++)if(maps[i].va==(v&~4095UL))return (char*)maps[i].pa+(v&4095);return NULL;}
Context *ucontext(AddrSpace *as,Area s,void *e){ctx.mepc=(uintptr_t)e;return &ctx;}
int fs_open(const char *p,int f,int m){pos=0;return missing?-1:8;}
int fs_close(int f){closes++;return 0;}
long fs_lseek(int f,size_t o,int w){pos=o;return o;}
long fs_read(int f,void *b,size_t n){if(pos>=image_size)return 0;if(n>image_size-pos)n=image_size-pos;memcpy(b,image+pos,n);pos+=n;return n;}
#include "nanos-lite/src/loader.c"
static PCB pcb;
int main(int argc,char **argv){
 setbuf(stdout,NULL);memset(pages,0xa5,sizeof(pages));
 Elf64_Ehdr *e=(void*)image;memcpy(e->e_ident,"\177ELF",4);e->e_ident[EI_CLASS]=ELFCLASS64;e->e_ident[EI_DATA]=ELFDATA2LSB;e->e_machine=EM_RISCV;e->e_type=ET_EXEC;e->e_version=EV_CURRENT;e->e_ehsize=64;e->e_entry=0x40000100;e->e_phoff=64;e->e_phentsize=56;e->e_phnum=1;
 Elf64_Phdr *p=(void*)(image+64);p->p_type=PT_LOAD;p->p_offset=0x100;p->p_vaddr=0x40000100;p->p_filesz=32;p->p_memsz=5000;p->p_align=4096;memset(image+0x100,0x42,32);
 const char *s=argv[1];
 if(!strcmp(s,"phentsize")) e->e_phentsize=128;
 if(!strcmp(s,"short"))image_size=0x110;
 if(!strcmp(s,"wrong-type")){e->e_ident[EI_CLASS]=ELFCLASS32;e->e_machine=EM_X86_64;e->e_entry=0x1234;}
 if(!strcmp(s,"overflow")){p->p_vaddr=UINTPTR_MAX-7;p->p_memsz=32;p->p_filesz=16;}
 if(!strcmp(s,"filesz")){p->p_filesz=32;p->p_memsz=16;}
 if(!strcmp(s,"kernel")){p->p_vaddr=0x80000000;e->e_entry=p->p_vaddr;}
 if(!strcmp(s,"shared")){e->e_phnum=2;p->p_memsz=32;p[1]=*p;p[1].p_vaddr=0x40000200;p[1].p_offset=0x200;memset(image+0x200,0x43,32);}
 if(!strcmp(s,"stack-overlap")){p->p_vaddr=0x7ffff000;p->p_memsz=4096;p->p_filesz=32;}
 if(!strcmp(s,"alignment")||!strcmp(s,"args-large")||!strcmp(s,"missing")||!strcmp(s,"stack-overlap")){
   char *av[]={"/bin/pal","--skip",NULL};char *ev[]={NULL};char *big=NULL;
   if(!strcmp(s,"args-large")){big=malloc(40001);memset(big,'a',40000);big[40000]=0;av[0]=big;}
   if(!strcmp(s,"missing")){missing=1;pcb.max_brk=123;pcb.cp=(void*)456;}
   int rc=context_uload(&pcb,"/bin/pal",av,ev);
   printf("status=%d argc_sp_mod16=%lu sp=%lx used=%zu duplicate=%d max_brk=%lx cp=%p\n",rc,ctx.GPRx%16,ctx.GPRx,used,duplicate,pcb.max_brk,(void*)pcb.cp);
 }else{
   protect(&pcb.as);uintptr_t entry=loader(&pcb,"fixture");
   printf("entry=%lx pages=%zu duplicate=%d close_calls=%d max_brk=%lx\n",entry,used/4096,duplicate,closes,pcb.max_brk);
   if(!strcmp(s,"valid")){unsigned char *a=pa(0x40000100),*b=pa(0x40000120);printf("file=%x bss=%x tail_bss=%x prefix=%x\n",*a,*b,*(unsigned char*)pa(0x40001487),*(unsigned char*)pa(0x40000000));}
   if(!strcmp(s,"shared"))printf("first=%x expected=42 second=%x expected=43\n",*(unsigned char*)pa(0x40000100),*(unsigned char*)pa(0x40000200));
   if(!strcmp(s,"short"))printf("missing_file_byte=%x expected=rejected\n",*(unsigned char*)pa(0x40000110));
   if(!strcmp(s,"filesz"))printf("byte_past_memsz=%x expected=rejected\n",*(unsigned char*)pa(0x40000110));
 }
 return 0;
}
