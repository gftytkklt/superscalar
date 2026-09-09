#include <am.h>

// 阶段 J3：PS/2 键盘 IOE。
//
// 硬件（ps2_top_apb，基址 0x10011000，mmio 区 / difftest skip）只给原始 AT 扫描码：
//   0x0  扫描码（8bit 只读，弹出式；FIFO 空返回 0）
//   0x4  状态（bit0=非空）
// 扫描码协议（对齐 nvboard at_scancode.h 输出的 AT 码）：
//   - make      : 逐字节 扫描码（LSB 先已由硬件还原为字节）
//   - break     : 0xF0 前缀 + 扫描码
//   - 扩展键    : 0xE0 前缀 + 扫描码（如 RIGHT/UP/PAGEUP），break 为 0xE0 0xF0 码
// 本驱动维护内部事件队列（16）+ ext/brk 前缀状态机，把扫描码流翻译为
// {keydown, AM_KEY_*} 事件。无 AM 对应键（LGUI/RGUI/PRINTSCREEN/KP_* 等）直接丢弃
// （am-tests keyboard 以 AM_KEY_NONE 判定队列空，残留 NONE 事件会提前 break 循环）。
#define PS2_BASE    0x10011000L
#define PS2_DATA    (*(volatile uint32_t *)(PS2_BASE + 0x0L))
#define PS2_STATUS  (*(volatile uint32_t *)(PS2_BASE + 0x4L))
#define PS2_EMPTY   0x0

#define KEYDOWN_MASK 0x8000
#define KEYCODE_MASK 0x7fff
#define KEY_QUEUE_LEN 16

static int key_queue[KEY_QUEUE_LEN] = {};
static int key_f = 0, key_r = 0;
static int kbd_ext = 0;   // 0xE0 扩展前缀待处理
static int kbd_brk = 0;   // 0xF0 断码前缀待处理

// 普通（非扩展）AT 扫描码 → AM_KEY_*（据 nvboard/src/at_scancode.h）。
// 无 AM 对应键置 0（丢弃）：SCROLLLOCK(0x7E)、NUMLOCKCLEAR(0x77)、KP_* 等。
static const int keymap[256] = {
  [0x1C] = AM_KEY_A, [0x32] = AM_KEY_B, [0x21] = AM_KEY_C, [0x23] = AM_KEY_D,
  [0x24] = AM_KEY_E, [0x2B] = AM_KEY_F, [0x34] = AM_KEY_G, [0x33] = AM_KEY_H,
  [0x43] = AM_KEY_I, [0x3B] = AM_KEY_J, [0x42] = AM_KEY_K, [0x4B] = AM_KEY_L,
  [0x3A] = AM_KEY_M, [0x31] = AM_KEY_N, [0x44] = AM_KEY_O, [0x4D] = AM_KEY_P,
  [0x15] = AM_KEY_Q, [0x2D] = AM_KEY_R, [0x1B] = AM_KEY_S, [0x2C] = AM_KEY_T,
  [0x3C] = AM_KEY_U, [0x2A] = AM_KEY_V, [0x1D] = AM_KEY_W, [0x22] = AM_KEY_X,
  [0x35] = AM_KEY_Y, [0x1A] = AM_KEY_Z,
  [0x45] = AM_KEY_0, [0x16] = AM_KEY_1, [0x1E] = AM_KEY_2, [0x26] = AM_KEY_3,
  [0x25] = AM_KEY_4, [0x2E] = AM_KEY_5, [0x36] = AM_KEY_6, [0x3D] = AM_KEY_7,
  [0x3E] = AM_KEY_8, [0x46] = AM_KEY_9,
  [0x0E] = AM_KEY_GRAVE,   [0x4E] = AM_KEY_MINUS,     [0x55] = AM_KEY_EQUALS,
  [0x5D] = AM_KEY_BACKSLASH, [0x66] = AM_KEY_BACKSPACE, [0x29] = AM_KEY_SPACE,
  [0x0D] = AM_KEY_TAB,     [0x58] = AM_KEY_CAPSLOCK,  [0x12] = AM_KEY_LSHIFT,
  [0x14] = AM_KEY_LCTRL,   [0x11] = AM_KEY_LALT,      [0x59] = AM_KEY_RSHIFT,
  [0x5A] = AM_KEY_RETURN,  [0x76] = AM_KEY_ESCAPE,
  [0x05] = AM_KEY_F1,  [0x06] = AM_KEY_F2,  [0x04] = AM_KEY_F3,  [0x0C] = AM_KEY_F4,
  [0x03] = AM_KEY_F5,  [0x0B] = AM_KEY_F6,  [0x83] = AM_KEY_F7,  [0x0A] = AM_KEY_F8,
  [0x01] = AM_KEY_F9,  [0x09] = AM_KEY_F10, [0x78] = AM_KEY_F11, [0x07] = AM_KEY_F12,
  [0x54] = AM_KEY_LEFTBRACKET, [0x5B] = AM_KEY_RIGHTBRACKET, [0x4C] = AM_KEY_SEMICOLON,
  [0x52] = AM_KEY_APOSTROPHE,  [0x41] = AM_KEY_COMMA,   [0x49] = AM_KEY_PERIOD,
  [0x4A] = AM_KEY_SLASH,
};

// 扩展（0xE0 前缀）AT 扫描码 → AM_KEY_*。无 AM 对应（LGUI/RGUI/PRINTSCREEN/KP_DIVIDE/
// KP_ENTER）置 0 丢弃。
static int keymap_ext(uint8_t code) {
  switch (code) {
    case 0x14: return AM_KEY_RCTRL;
    case 0x11: return AM_KEY_RALT;
    case 0x2F: return AM_KEY_APPLICATION;
    case 0x70: return AM_KEY_INSERT;
    case 0x6C: return AM_KEY_HOME;
    case 0x7D: return AM_KEY_PAGEUP;
    case 0x71: return AM_KEY_DELETE;
    case 0x69: return AM_KEY_END;
    case 0x7A: return AM_KEY_PAGEDOWN;
    case 0x75: return AM_KEY_UP;
    case 0x6B: return AM_KEY_LEFT;
    case 0x72: return AM_KEY_DOWN;
    case 0x74: return AM_KEY_RIGHT;
    default:   return 0;
  }
}

static void push_event(bool keydown, int keycode) {
  if ((key_r + 1) % KEY_QUEUE_LEN == key_f) return;   // 满则丢
  key_queue[key_r] = (keydown ? KEYDOWN_MASK : 0) | keycode;
  key_r = (key_r + 1) % KEY_QUEUE_LEN;
}

static bool pop_event(AM_INPUT_KEYBRD_T *kbd) {
  if (key_f == key_r) return false;
  int k = key_queue[key_f];
  key_f = (key_f + 1) % KEY_QUEUE_LEN;
  kbd->keydown = (k & KEYDOWN_MASK) != 0;
  kbd->keycode = k & KEYCODE_MASK;
  return true;
}

void __am_input_keybrd(AM_INPUT_KEYBRD_T *kbd) {
  // 1) 先弹内部已翻译事件
  if (pop_event(kbd)) return;

  // 2) 把硬件 FIFO 中的扫描码全部灌入内部队列
  while ((PS2_STATUS & 1) != 0) {
    uint8_t sc = (uint8_t)PS2_DATA;
    if (sc == 0xE0) { kbd_ext = 1; continue; }
    if (sc == 0xF0) { kbd_brk = 1; continue; }
    bool keydown = !kbd_brk;
    kbd_brk = 0;

    int keycode = kbd_ext ? keymap_ext(sc) : keymap[sc];
    kbd_ext = 0;
    if (keycode != 0) push_event(keydown, keycode);
    // 无 AM 对应键：丢弃该事件（状态已复位）
  }

  // 3) 弹出最早事件；空 → AM_KEY_NONE
  if (!pop_event(kbd)) {
    kbd->keydown = false;
    kbd->keycode = AM_KEY_NONE;
  }
}