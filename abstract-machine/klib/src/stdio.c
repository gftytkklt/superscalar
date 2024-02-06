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
      // info->numtype = LOWERDIGIT;
      info->radix = 16;
      // info->issigned = false;
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
  if (val == 0){*tmp++ = '0';return;}
  else if(issigned && (val < 0)){*tmp++ = '-';}
  else if(ispointer){*tmp++ = '0';*tmp++ = 'x';}
  // tmp points to lsb digit, p points to wr pos
  char *p = tmp;
  unsigned long val_abs = (unsigned long) val;
  while(val_abs != 0){
    *p++ = usestr[val_abs % radix];
    val_abs /= radix;
  }
  p--;// points to msb
  // swap str from{(-)[LSB->MSB]} to {(-)[MSB->LSB]}
  while (p > tmp){
    char tmpchar = *p;
    *p-- = *tmp;
    *tmp++ = tmpchar;
  }
}

int printf(const char *fmt, ...) {
  // panic("Not implemented");
  va_list ap;
  va_start(ap, fmt);
  // int ret = 0;
  char buf[2048] = {0};
  int ret = vsnprintf(buf, 2048, fmt, ap);
  assert(ret <= 2048);
  char *p = buf;
  while(*p){
    putch(*p++);
  }
  // if(outsize > sizeof(buf))
  // while (*fmt){
  //   int outsize = vsnprintf(buf, 1024, fmt, ap);
  //   fmt += outsize;
  //   ret += outsize;
  //   char *p = buf;
  //   while(*p){
  //     putch(*p++);
  //   }
  //   // break;
  // }
  va_end(ap);
  return ret;
  
}
// UB behav: invalid/unimpl fmt like %a is ignored and will output nothing
int vsprintf(char *out, const char *fmt, va_list ap) {
  // panic("Not implemented");
  char *buf = out;
  // va_list ap;
  // va_start(ap, fmt);
  while(*fmt){
    if(*fmt != '%') {*buf++ = *fmt++;continue;}
    // before if statement below, fmt points to first %
    if(*++fmt == '%') {*buf++ = *fmt++;continue;}// change "%%" -> "%", fill it in out
    // here fmt points to symbol next to %, and symbol must not be '%'
    formatinfo info={0};
    fmt += decode_fmt(fmt, &info);
    // fill str into out at pos of buf
    switch(info.argtype){
      case CHAR:{
        char val_char = va_arg(ap, int);
        for (int i=1;i<info.width;i++){
          *buf++ = ' ';
        }
        *buf++ = val_char;
        break;
      }
      case STR:{
        char* str = va_arg(ap, char*);
        for(int i=strlen(str);i<info.width;i++){
          *buf++ = ' ';
        }
        while(*str){
          *buf++ = *str++;
        }
        break;
      }
      case NUMBER:{
        long val_num = info.islong ? va_arg(ap, long) : (long) va_arg(ap, int);
        char numstr[21] = {0};
        char padding = info.zeropad ? '0' : ' ';
        num2str(numstr, val_num, info.issigned, info.isupperdigit, info.ispointer, info.radix);
        for(int i=strlen(numstr);i<info.width;i++){
          *buf++ = padding;
        }
        char *p = numstr;
        while(*p){
          *buf++ = *p++;
        }
        break;
      }
      default: // INVALID type, should not reach here
        break;
    }
  }
  *buf = '\0';
  return strlen(out);
}

int sprintf(char *out, const char *fmt, ...) {
  // panic("Not implemented");
  va_list ap;
  va_start(ap, fmt);
  int ret = vsprintf(out, fmt, ap);
  va_end(ap);
  return ret;
}

int snprintf(char *out, size_t n, const char *fmt, ...) {
  // panic("Not implemented");
  va_list ap;
  va_start(ap, fmt);
  int ret = vsnprintf(out, n, fmt, ap);
  va_end(ap);
  return ret;
}

int vsnprintf(char *out, size_t n, const char *fmt, va_list ap) {
  // panic("Not implemented");
  // panic("Not implemented");
  char *buf = out;
  // unsafe impl but don't care
  const char *const end = out + n - 1;
  int ret = 0;
  // va_list ap;
  // va_start(ap, fmt);
  while(*fmt){
    if(*fmt != '%') {
      if(buf < end){*buf++ = *fmt;}
      fmt++;ret++;
      continue;
    }
    // before if statement below, fmt points to first %
    if(*++fmt == '%') {
      if(buf < end){*buf++ = *fmt;}
      fmt++;ret++;
      continue;
    }// change "%%" -> "%", fill it in out
    // here fmt points to symbol next to %, and symbol must not be '%'
    formatinfo info={0};
    fmt += decode_fmt(fmt, &info);
    // fill str into out at pos of buf
    switch(info.argtype){
      case CHAR:{
        char val_char = va_arg(ap, int);
        for (int i=1;i<info.width;i++){
          if(buf < end) {*buf++ = ' ';}
          ret++;
        }
        if(buf < end) {*buf++ = val_char;}
        ret++;
        break;
      }
      case STR:{
        char* str = va_arg(ap, char*);
        for(int i=strlen(str);i<info.width;i++){
          if(buf < end) {*buf++ = ' ';}
          ret++;
        }
        ret += strlen(str);
        while(*str){
          if(buf < end) {*buf++ = *str;}
          str++;
        }
        break;
      }
      case NUMBER:{
        long val_num = info.islong ? va_arg(ap, long) : (long) va_arg(ap, int);
        char numstr[21] = {0};
        char padding = info.zeropad ? '0' : ' ';
        num2str(numstr, val_num, info.issigned, info.isupperdigit, info.ispointer, info.radix);
        for(int i=strlen(numstr);i<info.width;i++){
          if(buf < end) {*buf++ = padding;}
          ret++;
        }
        char *p = numstr;
        ret+= strlen(numstr);
        while(*p){
          if(buf < end) {*buf++ = *p;}
          p++;
        }
        break;
      }
      default: // INVALID type, should not reach here
        break;
    }
  }
  if(n>0) {*buf = '\0';}
  return ret;
}

#endif
