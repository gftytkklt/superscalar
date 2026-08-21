#include <am.h>
#include <stdio.h>
#include <stdlib.h>

Area heap;

void putch(char ch) {
  putchar(ch);
}

void halt(int code) {
  exit(code);

  // should not reach here
  while (1);
}