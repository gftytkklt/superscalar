#include <device/map.h>
#include <device/timer.h>
#include <utils.h>

#if defined(CONFIG_RV64) && !defined(CONFIG_TARGET_AM)
static bool legacy = true;
static uint64_t time_offset;
static uint8_t *time_reg, *cmp_reg;

void nemu_timer_select(const char *source) {
  if (!strcmp(source, "legacy")) legacy = true;
  else if (!strcmp(source, "mtimer")) legacy = false;
  else { fprintf(stderr, "Invalid timer source: %s\n", source); exit(1); }
}
bool nemu_timer_legacy(void) { return legacy; }
uint64_t nemu_timer_time(void) { return get_time() + time_offset; }
bool nemu_timer_mtip(void) {
  uint64_t cmp;
  if (legacy || !cmp_reg) return false;
  memcpy(&cmp, cmp_reg, sizeof(cmp));
  return nemu_timer_time() >= cmp;
}
static void time_io(uint32_t offset, int len, bool write) {
  uint64_t value = nemu_timer_time();
  if (write) {
    // map_write already stored the written bytes; merge them with live time.
    memcpy((uint8_t *)&value + offset, time_reg + offset, len);
    time_offset = value - get_time();
  }
  memcpy(time_reg, &value, sizeof(value));
}
void init_mtimer(void) {
  if (legacy) return;
  time_reg = new_space(8);
  cmp_reg = new_space(8);
  memset(cmp_reg, 0xff, 8);
  uint64_t now = nemu_timer_time();
  memcpy(time_reg, &now, 8);
  add_mmio_map("mtime", 0x0200bff8, time_reg, 8, time_io);
  add_mmio_map("mtimecmp", 0x02004000, cmp_reg, 8, NULL);
}
#endif
