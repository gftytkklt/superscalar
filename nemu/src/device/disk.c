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

#include <device/map.h>
#include <memory/paddr.h>
#include <stdlib.h>
#include <string.h>

// Disk control registers (relative to CONFIG_DISK_CTL_MMIO)
enum {
  reg_blkno,      // 0x00  write: starting block number
  reg_blkcnt,     // 0x04  write: number of blocks
  reg_buf_lo,     // 0x08  write: low 32 bits of the guest physical buffer address
  reg_buf_hi,     // 0x0c  write: high 32 bits of the guest physical buffer address
  reg_write,      // 0x10  write: 1 = write to disk, 0 = read from disk
  reg_cmd,        // 0x14  write: value written starts the transfer
  reg_present,    // 0x18  read
  reg_blksz,      // 0x1c  read
  reg_nblkcnt,    // 0x20  read: total number of blocks on the disk
  reg_ready,      // 0x24  read
  nr_reg,
};

#define BLKSZ 512

static uint32_t *disk_base = NULL;
static FILE *disk_fp = NULL;
static uint32_t disk_blkcnt = 0;

static void disk_io_handler(uint32_t offset, int len, bool is_write) {
  uint32_t *reg = disk_base + (offset / 4);

  if (!is_write) {
    if (offset == reg_blksz * 4) *reg = BLKSZ;
    else if (offset == reg_nblkcnt * 4) *reg = disk_blkcnt;
    else if (offset == reg_present * 4) *reg = (disk_fp != NULL);
    else if (offset == reg_ready * 4) *reg = 1;
    return;
  }

  // For writes the map layer has already stored the value into disk_base[..],
  // so here we only act when the command register is written.
  if (offset != reg_cmd * 4) return;

  if (disk_fp) {
    uint64_t paddr = ((uint64_t)disk_base[reg_buf_hi] << 32) | disk_base[reg_buf_lo];
    // guest_to_host() already subtracts CONFIG_MBASE, so pass the raw paddr
    uint8_t *host_buf = guest_to_host((paddr_t)paddr);
    fseek(disk_fp, (long)disk_base[reg_blkno] * BLKSZ, SEEK_SET);
    size_t bytes = (size_t)disk_base[reg_blkcnt] * BLKSZ;
    if (disk_base[reg_write]) { size_t _r = fwrite(host_buf, bytes, 1, disk_fp); (void)_r; }
    else { size_t _r = fread(host_buf, bytes, 1, disk_fp); (void)_r; }
    fflush(disk_fp);
  }
}

void init_disk() {
  disk_base = (uint32_t *)new_space(nr_reg * 4);
  add_mmio_map("disk", CONFIG_DISK_CTL_MMIO, disk_base, nr_reg * 4, disk_io_handler);

  // The disk image path: $NAVY_HOME/build/ramdisk.img (a host file).
  const char *navy = getenv("NAVY_HOME");
  if (navy == NULL) navy = "";
  char path[512];
  snprintf(path, sizeof(path), "%s/build/ramdisk.img", navy);
  disk_fp = fopen(path, "r+b");
  if (disk_fp) {
    fseek(disk_fp, 0, SEEK_END);
    long size = ftell(disk_fp);
    disk_blkcnt = (size + BLKSZ - 1) / BLKSZ;
    fseek(disk_fp, 0, SEEK_SET);
    Log("disk image: %s (%ld bytes, %d blocks)", path, size, disk_blkcnt);
  } else {
    Log("disk image not found at %s, disk disabled", path);
  }
}