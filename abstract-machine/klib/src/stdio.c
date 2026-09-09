#include <am.h>
#include <klib.h>
#include <klib-macros.h>
#include <stdarg.h>

#if !defined(__ISA_NATIVE__) || defined(__NATIVE_USE_KLIB__)
enum {INVALID_TYPE, STR, NUMBER, CHAR, };

typedef struct {
  // padding info
  bool zeropad;// if argtype != NUMBER, this is forced to be false
  int width;// if strlen < width, padding ' ' or '0' (strlen-width) times
  // fmt info
  int argtype;
  // valid only argtype == NUMBER
  bool islong;
  bool ispointer;
  bool issigned;
  bool isupperdigit;
  int radix;
  // int numtype;
} formatinfo;
// decode fmt string, return string ptr increment value
// fmt is already fmt symbol, not %!
// all return 0 means INVALID type, ptr will point to this invalid char
// as a result, skip % and treat this invalid char as normal char
// do not change init value if value 0/false don't need changed
static int decode_fmt(const char* fmt, formatinfo* info){
  const char *tmp = fmt;
  // if(!*tmp){return 0;}
  // decode padding info first
  if(*tmp == '0'){info->zeropad = true;}
  // get minimum width
  while(*tmp >= '0' && *tmp <= '9'){
    info->width = (info->width)*10 + (*tmp - '0');
    tmp++;
  }
  // decode fmt: %(l)d/i/o/u/x/X, %c/s/p
  // now tmp points to below elems
  if(*tmp == 'l') {info->islong = true; tmp++;}
  // as behavior of invalid fmt as %lp/%ls is UB, deal them with valid info is OK
  // info in struct formatinfo is invalid when meet inv fmt above
  switch (*tmp++) {
    case 'c':
      info->argtype = CHAR;
      break;
    case 's':
      info->argtype = STR;
      break;
    case 'p':
      info->argtype = NUMBER;
      info->radix = 16;
      info->islong = true;
      info->ispointer = true;
      break;
    case 'd': case 'i': case 'u':
      info->argtype = NUMBER;
      info->radix = 10;
      info->issigned = (*tmp == 'u') ? false : true;
      break;
    case 'o':
      info->argtype = NUMBER;
      info->radix = 8;
      break;
    case 'x': case 'X':
      info->argtype = NUMBER;
      info->radix = 16;
      info->isupperdigit = (*tmp == 'X') ? true : false;
      break;
    default:
      info->argtype = INVALID_TYPE;// as a result, invalid fmt will be ignored
      break;
  }
  return (tmp-fmt);
}
// get str of number
// e.g, -123456 -> "-123456"
static void num2str(char* dst, long val, bool issigned, bool isupper, bool ispointer, int radix){
  assert(radix != 0);
  const char* lowerstr = "0123456789abcdef";
  const char* upperstr = "0123456789ABCDEF";
  const char* usestr = isupper ? upperstr : lowerstr;
  char *tmp = dst;
  if (val == 0){*tmp++ = '0';*tmp = '\0';return;}
  else if(issigned && (val < 0)){*tmp++ = '-';}
  else if(ispointer){*tmp++ = '0';*tmp++ = 'x';}
  // tmp points to lsb digit, p points to wr pos
  char *p = tmp;
  unsigned long val_abs = (unsigned long) val;
  while(val_abs != 0){
    *p++ = usestr[val_abs % radix];
    val_abs /= radix;
  }
  *p = '\0';
  p--;// points to msb
  // swap str from{(-)[LSB->MSB]} to {(-)[MSB->LSB]}
  while (p > tmp){
    char tmpchar = *p;
    *p-- = *tmp;
    *tmp++ = tmpchar;
  }
}

// ---------------------------------------------------------------------
// streaming output core: every produced character is fed to emit(arg, ch).
// this is the standard libc architecture: printf/sprintf/snprintf all share
// one formatter, differing only in where the characters go. no large buffer
// is needed on the caller's stack.
// ---------------------------------------------------------------------
typedef void (*emit_f)(void *, char);

static void vformat(emit_f emit, void *arg, const char *fmt, va_list ap) {
  if (!fmt) return;
  while(*fmt){
    if(*fmt != '%') {emit(arg, *fmt++);continue;}
    // before if statement below, fmt points to first %
    if(*++fmt == '%') {emit(arg, *fmt++);continue;}// change "%%" -> "%"
    // here fmt points to symbol next to %, and symbol must not be '%'
    formatinfo info={0};
    fmt += decode_fmt(fmt, &info);
    // fill str into out at pos of buf
    switch(info.argtype){
      case CHAR:{
        char val_char = va_arg(ap, int);
        for (int i=1;i<info.width;i++){
          emit(arg, ' ');
        }
        emit(arg, val_char);
        break;
      }
      case STR:{
        char* str = va_arg(ap, char*);
        int len = str ? (int)strlen(str) : 0;
        for(int i=len;i<info.width;i++){
          emit(arg, ' ');
        }
        if (str) while(*str) emit(arg, *str++);
        break;
      }
      case NUMBER:{
        long val_num = info.islong ? va_arg(ap, long) : (long) va_arg(ap, int);
        char numstr[21] = {0};
        char padding = info.zeropad ? '0' : ' ';
        num2str(numstr, val_num, info.issigned, info.isupperdigit, info.ispointer, info.radix);
        for(int i=strlen(numstr);i<info.width;i++){
          emit(arg, padding);
        }
        char *p = numstr;
        while(*p){
          emit(arg, *p++);
        }
        break;
      }
      default: // INVALID type, should not reach here
        break;
    }
  }
}

// ---- buffer sink used by vsprintf/vsnprintf ----
typedef struct {
  char *buf;
  size_t n;
  size_t cnt;
} sink_t;

static void sink_emit(void *arg, char c) {
  sink_t *s = (sink_t*) arg;
  if (s->buf && (s->cnt + 1) < s->n) {
    s->buf[s->cnt] = c;
  }
  s->cnt++;
}

// ---- stream sink for printf: write each char directly to putch ----
static int putch_counter;
static void putch_emit(void *arg, char c) {
  (void)arg;
  putch(c);
  putch_counter++;
}

int vsnprintf(char *out, size_t n, const char *fmt, va_list ap) {
  sink_t s = {out, n, 0};
  vformat(sink_emit, &s, fmt, ap);
  if (n > 0) out[(s.cnt < (n - 1)) ? s.cnt : (n - 1)] = '\0';
  return s.cnt;
}

int vsprintf(char *out, const char *fmt, va_list ap) {
  return vsnprintf(out, (size_t)-1, fmt, ap);
}

int printf(const char *fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  putch_counter = 0;
  vformat(putch_emit, NULL, fmt, ap);
  va_end(ap);
  return putch_counter;
}

int sprintf(char *out, const char *fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  int ret = vsprintf(out, fmt, ap);
  va_end(ap);
  return ret;
}

int snprintf(char *out, size_t n, const char *fmt, ...) {
  va_list ap;
  va_start(ap, fmt);
  int ret = vsnprintf(out, n, fmt, ap);
  va_end(ap);
  return ret;
}

#endif