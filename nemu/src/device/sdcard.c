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
#include "mmc.h"

// http://www.files.e-shop.co.il/pdastore/Tech-mmc-samsung/SEC%20MMC%20SPEC%20ver09.pdf

// see page 26 of the manual above
#define MEMORY_SIZE (16ull * 1024 * 1024 * 1024)  // 16GB
#define READ_BL_LEN 15
#define BLOCK_LEN (1 << READ_BL_LEN)
#define NR_BLOCK (MEMORY_SIZE / BLOCK_LEN)
#define C_SIZE_MULT 7  // only 3 bits
#define MULT (1 << (C_SIZE_MULT + 2))
#define C_SIZE (NR_BLOCK / MULT - 1)

// This is a simple hardware implementation of linux/drivers/mmc/host/bcm2835.c
// No DMA and IRQ is supported, so the driver must be modified to start PIO
// right after sending the actual read/write commands.

enum {
  SDCMD, SDARG, SDTOUT, SDCDIV,
  SDRSP0, SDRSP1, SDRSP2, SDRSP3,
  SDHSTS, __PAD0, __PAD1, __PAD2,
  SDVDD, SDEDM, SDHCFG, SDHBCT,
  SDDATA, __PAD10, __PAD11, __PAD12,
  SDHBLC
};

static FILE *fp = NULL;
static uint32_t *base = NULL;
static uint32_t blkcnt = 0;
static uint64_t disk_pos = 0;
static uint64_t image_size = 0;
static uint32_t addr = 0;
static bool write_cmd = 0;
static bool read_ext_csd = false;
static bool transfer_active = false;

static void flush_write() {
  if (transfer_active && write_cmd && !read_ext_csd) {
    Assert(fflush(fp) == 0, "sdcard flush failed");
  }
}

static void prepare_rw(int is_write) {
  flush_write();
  disk_pos = (uint64_t)base[SDARG] * 512;
  Assert(disk_pos < MEMORY_SIZE && (off_t)disk_pos >= 0 &&
      (uint64_t)(off_t)disk_pos == disk_pos, "sdcard block out of range: %u", base[SDARG]);
  Assert(fp != NULL && fseeko(fp, (off_t)disk_pos, SEEK_SET) == 0,
      "sdcard seek failed: offset=%" PRIu64, disk_pos);
  write_cmd = is_write;
  read_ext_csd = false;
  transfer_active = true;
}

static void sdcard_handle_cmd(int cmd) {
  switch (cmd) {
    case MMC_GO_IDLE_STATE:
      flush_write();
      transfer_active = read_ext_csd = false;
      break;
    case MMC_SEND_OP_COND: base[SDRSP0] = 0x80ff8000; break;
    case MMC_ALL_SEND_CID:
      base[SDRSP0] = 0x00000001;
      base[SDRSP1] = 0x00000000;
      base[SDRSP2] = 0x00000000;
      base[SDRSP3] = 0x15000000;
      break;
    case 52: // ???
      break;
    case MMC_SEND_CSD:
      base[SDRSP0] = 0x92404001;
      base[SDRSP1] = 0x124b97e3 | ((C_SIZE & 0x3) << 30);
      base[SDRSP2] = 0x0f508000 | (C_SIZE >> 2) | (READ_BL_LEN << 16);
      base[SDRSP3] = 0x9026012a;
      break;
    case MMC_SEND_EXT_CSD:
      flush_write();
      read_ext_csd = transfer_active = true;
      write_cmd = false;
      addr = 0;
      break;
    case MMC_SLEEP_AWAKE: break;
    case MMC_APP_CMD: break;
    case MMC_SET_RELATIVE_ADDR: break;
    case MMC_SELECT_CARD: break;
    case MMC_SET_BLOCK_COUNT: blkcnt = base[SDARG] & 0xffff; break;
    case MMC_READ_MULTIPLE_BLOCK: prepare_rw(false); break;
    case MMC_WRITE_MULTIPLE_BLOCK: prepare_rw(true); break;
    case MMC_SEND_STATUS: base[SDRSP0] = 0x900; base[SDRSP1] = base[SDRSP2] = base[SDRSP3] = 0; break;
    case MMC_STOP_TRANSMISSION:
      flush_write();
      transfer_active = read_ext_csd = false;
      break;
    default:
      panic("unhandled command = %d", cmd);
  }
}

static void sdcard_io_handler(uint32_t offset, int len, bool is_write) {
  Assert(len == 4 && offset % 4 == 0, "invalid sdcard register access: offset=%u len=%d", offset, len);
  int idx = offset / 4;
  switch (idx) {
    case SDCMD:
      if (is_write) sdcard_handle_cmd(base[SDCMD] & 0x3f);
      break;
    case SDARG:
    case SDRSP0:
    case SDRSP1:
    case SDRSP2:
    case SDRSP3:
      break;
    case SDDATA:
       if (!transfer_active || is_write != write_cmd) break;
       if (read_ext_csd) {
         // See section 8.1 JEDEC Standard JED84-A441
         uint32_t data;
         switch (addr) {
           case 192: data = 2; break; // EXT_CSD_REV
           case 212: data = MEMORY_SIZE / 512; break;
           default: data = 0;
         }
         base[SDDATA] = data;
         addr += 4;
         if (addr == 512) read_ext_csd = transfer_active = false;
       } else {
         Assert(disk_pos <= MEMORY_SIZE - 4, "sdcard transfer out of range: offset=%" PRIu64, disk_pos);
         if (!write_cmd) {
           // Unwritten capacity reads as zero; an unexpected short read is an error.
           size_t expected = disk_pos < image_size ?
             (image_size - disk_pos < 4 ? (size_t)(image_size - disk_pos) : 4) : 0;
           base[SDDATA] = 0;
           size_t done = fread(&base[SDDATA], 1, expected, fp);
           Assert(done == expected && !ferror(fp), "sdcard short read: %zu/%zu", done, expected);
         } else {
           size_t done = fwrite(&base[SDDATA], 1, 4, fp);
           Assert(done == 4 && !ferror(fp), "sdcard short write: %zu/4", done);
           if (disk_pos + 4 > image_size) image_size = disk_pos + 4;
         }
         disk_pos += 4;
         // Complete each PIO block before the driver can report it as transferred.
         if (write_cmd && disk_pos % 512 == 0) flush_write();
       }
       break;
    default:
      Log("offset = 0x%x(idx = %d), is_write = %d, data = 0x%x", offset, idx, is_write, base[idx]);
      panic("unhandle offset = %d", offset);
  }
}

void init_sdcard() {
  base = (uint32_t *)new_space(0x80);
  add_mmio_map("sdhci", CONFIG_SDCARD_CTL_MMIO, base, 0x80, sdcard_io_handler);

  Assert(C_SIZE < (1 << 12), "shoule be fit in 12 bits");

  const char *img = CONFIG_SDCARD_IMG_PATH;
  fp = fopen(img, "r+");
  Assert(fp != NULL, "can not open sdcard image: %s", img);
  Assert(fseeko(fp, 0, SEEK_END) == 0, "sdcard image seek failed: %s", img);
  off_t size = ftello(fp);
  Assert(size >= 0, "sdcard image size failed: %s", img);
  image_size = (uint64_t)size;
  Assert(fseeko(fp, 0, SEEK_SET) == 0, "sdcard image rewind failed: %s", img);
  // Keep the 16 GiB capacity virtual: no allocation, prefill, or file extension.
  Log("sdcard image: %s (%" PRIu64 " bytes, capacity=%" PRIu64 ")", img, image_size, (uint64_t)MEMORY_SIZE);
}
