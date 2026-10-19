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
#include <limits.h>
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
static uint64_t disk_size = 0;

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

  if (disk_fp == NULL || disk_base[reg_blkcnt] == 0) return;

  uint64_t paddr = ((uint64_t)disk_base[reg_buf_hi] << 32) | disk_base[reg_buf_lo];
  uint64_t blkno = disk_base[reg_blkno], blkcnt = disk_base[reg_blkcnt];
  uint64_t pos = blkno * BLKSZ, bytes = blkcnt * BLKSZ;
  // Keep the full register address and arithmetic until all narrowing is safe.
  Assert((uint64_t)(paddr_t)paddr == paddr && bytes <= SIZE_MAX &&
      pos <= LONG_MAX && bytes <= (uint64_t)LONG_MAX - pos &&
      blkno < disk_blkcnt && blkcnt <= disk_blkcnt - blkno,
      "invalid disk DMA: addr=0x%" PRIx64 " block=%" PRIu64 " count=%" PRIu64,
      paddr, blkno, blkcnt);
  uint8_t *host_buf = addr_to_soc_range((paddr_t)paddr, (size_t)bytes);
  Assert(host_buf != NULL, "invalid disk DMA memory span: addr=0x%" PRIx64
      " bytes=%" PRIu64, paddr, bytes);

  // BLKIO has no error return: never resume the guest after a failed command.
  Assert(fseek(disk_fp, (long)pos, SEEK_SET) == 0,
      "disk seek failed: offset=%" PRIu64, pos);
  if (disk_base[reg_write]) {
    size_t done = fwrite(host_buf, 1, (size_t)bytes, disk_fp);
    Assert(done == bytes && !ferror(disk_fp), "disk short write: %zu/%" PRIu64, done, bytes);
    Assert(fflush(disk_fp) == 0, "disk flush failed");
    if (pos + bytes > disk_size) disk_size = pos + bytes;
  } else {
    // Only the known partial final block is padded; unexpected EOF is an error.
    uint64_t available = pos < disk_size ? disk_size - pos : 0;
    size_t expected = available < bytes ? available : (size_t)bytes;
    size_t done = fread(host_buf, 1, expected, disk_fp);
    Assert(done == expected && !ferror(disk_fp), "disk short read: %zu/%zu", done, expected);
    memset(host_buf + expected, 0, (size_t)bytes - expected);
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
    Assert(fseek(disk_fp, 0, SEEK_END) == 0, "disk image seek failed: %s", path);
    long size = ftell(disk_fp);
    Assert(size >= 0, "disk image size failed: %s", path);
    disk_size = (uint64_t)size;
    uint64_t blocks = disk_size / BLKSZ + (disk_size % BLKSZ != 0);
    // AM_DISK_CONFIG exposes the block count as an int.
    Assert(blocks <= INT_MAX, "disk image too large: %" PRIu64 " blocks", blocks);
    disk_blkcnt = (uint32_t)blocks;
    Assert(fseek(disk_fp, 0, SEEK_SET) == 0, "disk image rewind failed: %s", path);
    Log("disk image: %s (%ld bytes, %u blocks)", path, size, disk_blkcnt);
  } else {
    Log("disk image not found at %s, disk disabled", path);
  }
}
