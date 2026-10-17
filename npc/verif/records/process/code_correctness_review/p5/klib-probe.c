#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <am.h>

extern char *ccr_strncpy(char *, const char *, size_t);
extern int ccr_strcmp(const char *, const char *);
extern int ccr_strncmp(const char *, const char *, size_t);
extern void *ccr_memmove(void *, const void *, size_t);
extern int ccr_snprintf(char *, size_t, const char *, ...);
extern int ccr_atoi(const char *);
extern void *ccr_malloc(size_t);
extern void ccr_free(void *);
extern unsigned long long __udivmoddi4(unsigned long long, unsigned long long, unsigned long long *);
extern long long __divdi3(long long, long long);
extern long long __moddi3(long long, long long);
extern int __clzdi2(long long), __ctzdi2(long long);
Area heap;
void putch(char c) { (void)c; }
void halt(int n) { exit(n); }

int main(int argc, char **argv) {
  setvbuf(stdout, NULL, _IONBF, 0);
  if (argc != 2) return 2;
  if (!strcmp(argv[1], "strncpy-pad")) {
    char dst[5]; memset(dst, 0x5a, sizeof dst);
    ccr_strncpy(dst, "a", sizeof dst);
    printf("bytes=%02x %02x %02x %02x %02x expected=61 00 00 00 00\n", dst[0],dst[1],dst[2],dst[3],dst[4]);
  } else if (!strcmp(argv[1], "strncpy-bound")) {
    char src[1]={'a'}, dst[1];
    ccr_strncpy(dst, src, 1);
    printf("copied=%c\n",dst[0]);
  } else if (!strcmp(argv[1], "format")) {
    char out[100], expected[100];
#define FMT(f, v) do { int a=ccr_snprintf(out,sizeof out,f,v); int b=snprintf(expected,sizeof expected,f,v); printf("fmt=%s actual=[%s]/%d expected=[%s]/%d\n",f,out,a,expected,b); } while(0)
    FMT("%X", 0xabu); FMT("%x", 0x80000000u); FMT("%du", -7);
    FMT("%s", "hi"); FMT("%c", 'A'); FMT("%ld", 123456789012L);
    char tiny[2]={'Z','Z'}; int n=ccr_snprintf(tiny,2,"%s","abcd");
    printf("truncate=[%s] count=%d expected=a/4\n",tiny,n);
    printf("size0=%d expected=4\n",ccr_snprintf(NULL,0,"abcd"));
    char one='Z'; n=ccr_snprintf(&one,1,"abc"); printf("size1=%d byte=%d expected=3/0\n",n,one);
  } else if (!strcmp(argv[1], "format-negative")) {
    char out[100]; ccr_snprintf(out,sizeof out,"%d",-7);
    printf("negative=%s expected=-7\n",out);
  } else if (!strcmp(argv[1], "format-octal")) {
    char tiny[2]; ccr_snprintf(tiny, sizeof tiny, "%lo", ULONG_MAX);
    printf("unexpected sanitizer silence\n");
  } else if (!strcmp(argv[1], "atoi")) {
    const char *v[]={"123", "-12", "+12", "\t12", "  12x", ""};
    for (unsigned i=0;i<sizeof v/sizeof v[0];i++) printf("atoi[%s]=%d expected=%d\n",v[i],ccr_atoi(v[i]),atoi(v[i]));
  } else if (!strcmp(argv[1], "malloc")) {
    _Alignas(16) unsigned char buf[64]; heap=(Area){buf,buf+64};
    void *a=ccr_malloc(1), *b=ccr_malloc(8), *c=ccr_malloc(80);
    printf("offsets=%ld/%ld/%ld alignment8=%lu cursor=%ld capacity=64\n",(char*)a-(char*)buf,(char*)b-(char*)buf,(char*)c-(char*)buf,(uintptr_t)b%8,(char*)heap.start-(char*)buf);
    ccr_free(a); printf("free cursor=%ld\n",(char*)heap.start-(char*)buf);
  } else if (!strcmp(argv[1], "memory")) {
    char s[]="abcdef"; ccr_memmove(s+1,s,5); printf("overlap-right=%s expected=aabcde\n",s);
    ccr_memmove(s,s+1,5); s[5]=0; printf("overlap-left=%s expected=abcde\n",s);
    char hi[]={ (char)0xff,0 }, lo[]={1,0};
    printf("unsigned-char compare=%d/%d expected-positive\n",ccr_strcmp(hi,lo),ccr_strncmp(hi,lo,1));
  } else if (!strcmp(argv[1], "move-zero")) {
    char b=0; ccr_memmove(&b,&b,0); puts("zero move returned");
  } else if (!strcmp(argv[1], "int64-min")) {
    volatile long long a=LLONG_MIN, b=1;
    printf("quotient=%lld\n",__divdi3(a,b));
  } else if (!strcmp(argv[1], "int64")) {
    unsigned long long vals[]={0,1,2,3,0xffffffffULL,0x100000000ULL,0x8000000000000000ULL,0xffffffffffffffffULL};
    int count=0;
    for (unsigned i=0;i<8;i++) for(unsigned j=1;j<8;j++) {
      unsigned long long r, q=__udivmoddi4(vals[i],vals[j],&r);
      if(q!=vals[i]/vals[j] || r!=vals[i]%vals[j]) return 3;
      count++;
    }
    unsigned long long seed=123;
    for(int i=0;i<10000;i++) { seed=seed*6364136223846793005ULL+1; unsigned long long a=seed; seed=seed*6364136223846793005ULL+1; unsigned long long b=seed|1,r,q=__udivmoddi4(a,b,&r); if(q!=a/b || r!=a%b)return 4; }
    for(int i=0;i<64;i++) if(__clzdi2(1ULL<<i)!=63-i || __ctzdi2(1ULL<<i)!=i)return 5;
    if(__divdi3(-7,3)!=-2 || __moddi3(-7,3)!=-1)return 6;
    printf("udivmod=%d+10000 vectors bit-count=64 signed-normal=2 PASS\n",count);
  } else return 2;
  return 0;
}
