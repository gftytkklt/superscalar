#include <am.h>
#include <nemu.h>

#define KEYDOWN_MASK 0x8000
#define KEYNUM_MASK 0x7fff

void __am_input_keybrd(AM_INPUT_KEYBRD_T *kbd) {
  unsigned x = inl(KBD_ADDR);
  kbd->keycode = x & KEYNUM_MASK;// only accept 0-256, 0x80xx is invalid
  kbd->keydown = x & KEYDOWN_MASK;
}
