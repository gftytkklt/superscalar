#include <isa.h>
#include <device/map.h>
#include <device/mmio.h>
#include <device/timer.h>
#include <device/serial.h>
#include <unistd.h>
#include <fcntl.h>
CPU_state cpu;
FILE *log_fp;
static uint64_t now;
uint64_t get_time(void) { return now; }
bool log_enable(void) { return false; }
void assert_fail_msg(void) { abort(); }
void init_map(void);
void init_serial(void);
#define UART 0xa00003f8u
#define TIME_ADDR 0x0200bff8u
#define CMP 0x02004000u
int main(int argc, char **argv) {
  assert(argc == 2 || argc == 3); log_fp = stdout;
  init_map(); nemu_timer_select("mtimer"); init_mtimer();
  assert(!nemu_timer_mtip());
  mmio_write(CMP, 8, 1000); now = 999; assert(!nemu_timer_mtip());
  now = 1000; assert(nemu_timer_mtip());
  mmio_write(CMP, 4, 2000); assert(!nemu_timer_mtip());
  assert(mmio_read(CMP, 8) == 2000);
  mmio_write(CMP + 4, 4, 1); assert(mmio_read(CMP, 8) == 0x1000007d0ull);
  mmio_write(CMP + 1, 1, 0x12); assert(mmio_read(CMP, 2) == 0x12d0);
  mmio_write(TIME_ADDR, 8, 5000); assert(nemu_timer_time() == 5000);
  now++; assert(mmio_read(TIME_ADDR, 8) == 5001);
  mmio_write(TIME_ADDR + 4, 4, 1); assert(nemu_timer_time() == 0x100001389ull);
  assert(mmio_read(TIME_ADDR, 4) == (uint32_t)nemu_timer_time());
  uint64_t before = nemu_timer_time();
  mmio_write(TIME_ADDR + 1, 2, 0x4567);
  assert(nemu_timer_time() == ((before & ~0xffff00ull) | 0x456700));
  assert(!mmio_range_mapped(CMP + 4, 8));
  nemu_serial_input(argv[1]); init_serial();
  if (argc == 3) {
    assert(mmio_read(UART + 5, 1) == 0x60); // FIFO without a writer
    int fd = open(argv[1], O_WRONLY | O_NONBLOCK); assert(fd >= 0);
    assert(write(fd, "abc", 3) == 3); close(fd);
  }
  assert(mmio_read(UART + 5, 1) == 0x61);
  mmio_write(UART + 3, 1, 0x80); mmio_write(UART, 1, 12); mmio_write(UART + 1, 1, 3);
  assert(mmio_read(UART, 1) == 12 && mmio_read(UART + 1, 1) == 3);
  mmio_write(UART + 3, 1, 3); mmio_write(UART + 1, 1, 3);
  assert((mmio_read(UART + 2, 1) & 15) == 4);
  for (int i = 0; i < 3; i++) assert(mmio_read(UART, 1) == (unsigned)("abc"[i]));
  assert((mmio_read(UART + 2, 1) & 15) == 2);
  assert((mmio_read(UART + 2, 1) & 15) == 1);
  assert(mmio_read(UART + 5, 1) == 0x60); // EOF does not quit/block
  if (argc == 3) {
    int fd = open(argv[1], O_WRONLY | O_NONBLOCK); assert(fd >= 0);
    assert(write(fd, "Q", 1) == 1); close(fd);
    assert(mmio_read(UART, 1) == 'Q'); // writer reconnects after EOF
  }
  mmio_write(UART + 4, 1, 0x1e); assert(mmio_read(UART + 6, 1) == 0xd0);
  mmio_write(UART, 1, 'Z'); assert(mmio_read(UART, 1) == 'Z');
  mmio_write(UART + 7, 1, 0x5a); assert(mmio_read(UART + 7, 1) == 0x5a);
  mmio_write(UART + 2, 1, 7); assert((mmio_read(UART + 2, 1) & 0xc0) == 0xc0);
  puts("MTIMER partial/deadline/time + UART DLAB/RX/IIR/loopback/EOF PASS");
}
