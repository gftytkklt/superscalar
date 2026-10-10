/***************************************************************************************
* Copyright (c) 2014-2022 Zihao Yu, Nanjing University
*
* NEMU is licensed under Mulan PSL v2.
* You can use this software according to the terms and conditions of the Mulan PSL v2.
* You may obtain a copy of Mulan PSL v2 at:
*          http://license.coscl.org.cn/MulanPSL2
*
* THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
* EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
* MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
*
* See the Mulan PSL v2 for more details.
***************************************************************************************/

#include <utils.h>
#include <device/map.h>

#if defined(CONFIG_RV64) && !defined(CONFIG_TARGET_AM)
#include <device/serial.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>

static uint8_t *serial_base;
static uint8_t ier, lcr, mcr, scr, dll, dlm, fcr;
static uint8_t rx[16];
static unsigned head, count;
static bool thre_pending;
static const char *input_path;
static int input_fd = -1;
void nemu_serial_input(const char *path) { input_path = path; }
static void receive(void) {
  if (input_fd < 0 || count == sizeof(rx)) return;
  uint8_t buf[16];
  ssize_t n = read(input_fd, buf, sizeof(rx) - count);
  if (n < 0 && errno != EAGAIN && errno != EWOULDBLOCK && errno != EINTR) {
    perror("serial input"); exit(1);
  }
  for (ssize_t i = 0; i < n; i++) rx[(head + count++) % sizeof(rx)] = buf[i];
}
static void serial_io_handler(uint32_t offset, int len, bool write) {
  assert(len == 1);
  receive();
  uint8_t value = serial_base[offset];
  if (write) {
    switch (offset) {
      case 0:
        if (lcr & 0x80) dll = value;
        else {
          if (mcr & 0x10) {
            if (count < sizeof(rx)) rx[(head + count++) % sizeof(rx)] = value;
          } else putc(value, stderr);
          thre_pending = true;
        }
        break;
      case 1:
        if (lcr & 0x80) dlm = value;
        else { if ((value & 2) && !(ier & 2)) thre_pending = true; ier = value & 15; }
        break;
      case 2:
        fcr = value;
        if (value & 2) head = count = 0;
        if (value & 4) thre_pending = true;
        break;
      case 3: lcr = value; break;
      case 4: mcr = value & 31; break;
      case 7: scr = value; break;
    }
    return;
  }
  value = 0;
  switch (offset) {
    case 0:
      if (lcr & 0x80) value = dll;
      else if (count) { value = rx[head++ % sizeof(rx)]; count--; }
      break;
    case 1: value = (lcr & 0x80) ? dlm : ier; break;
    case 2:
      value = 1; // No physical IRQ wire; these IDs also drive Linux polling.
      if ((ier & 1) && count) {
        static const unsigned trigger[] = {1, 4, 8, 14};
        value = count >= trigger[(fcr >> 6) & 3] ? 4 : 12;
      } else if ((ier & 2) && thre_pending) { value = 2; thre_pending = false; }
      if (fcr & 1) value |= 0xc0;
      break;
    case 3: value = lcr; break;
    case 4: value = mcr; break;
    case 5: value = 0x60 | (count ? 1 : 0); break;
    case 6:
      if (mcr & 0x10) value = ((mcr & 2) << 3) | ((mcr & 1) << 5) |
                             ((mcr & 4) << 4) | ((mcr & 8) << 4);
      break;
    case 7: value = scr; break;
  }
  serial_base[offset] = value;
}
void init_serial(void) {
  serial_base = new_space(8);
  memset(serial_base, 0, 8);
  if (input_path) {
    input_fd = open(input_path, O_RDONLY | O_NONBLOCK | O_CLOEXEC);
    if (input_fd < 0) { perror(input_path); exit(1); }
    struct stat st;
    if (fstat(input_fd, &st) || !(S_ISREG(st.st_mode) || S_ISFIFO(st.st_mode))) {
      fprintf(stderr, "Serial input must be an ordinary file or FIFO: %s\n", input_path); exit(1);
    }
  }
  add_mmio_map("serial", CONFIG_SERIAL_MMIO, serial_base, 8, serial_io_handler);
}
#else


#include <utils.h>
#include <device/map.h>

/* http://en.wikibooks.org/wiki/Serial_Programming/8250_UART_Programming */
// NOTE: this is compatible to 16550

#define CH_OFFSET 0

static uint8_t *serial_base = NULL;


static void serial_putc(char ch) {
  MUXDEF(CONFIG_TARGET_AM, putch(ch), putc(ch, stderr));
}

static void serial_io_handler(uint32_t offset, int len, bool is_write) {
  assert(len == 1);
  switch (offset) {
    /* We bind the serial port with the host stderr in NEMU. */
    case CH_OFFSET:
      if (is_write) serial_putc(serial_base[0]);
      else panic("do not support read");
      break;
    default: panic("do not support offset = %d", offset);
  }
}

void init_serial() {
  serial_base = new_space(8);
#ifdef CONFIG_HAS_PORT_IO
  add_pio_map ("serial", CONFIG_SERIAL_PORT, serial_base, 8, serial_io_handler);
#else
  add_mmio_map("serial", CONFIG_SERIAL_MMIO, serial_base, 8, serial_io_handler);
#endif

}

#endif
