#include <am.h>
#include <nemu.h>

// disk device control registers (relative to DISK_ADDR)
enum {
  DISK_BLKNO   = 0x00,
  DISK_BLKCNT  = 0x04,
  DISK_BUF_LO  = 0x08,
  DISK_BUF_HI  = 0x0c,
  DISK_WRITE   = 0x10,
  DISK_CMD     = 0x14,
  DISK_PRESENT = 0x18,
  DISK_BLKSZ   = 0x1c,
  DISK_NBLKCNT = 0x20,
  DISK_READY   = 0x24,
};

void __am_disk_config(AM_DISK_CONFIG_T *cfg) {
  cfg->present = inl(DISK_ADDR + DISK_PRESENT) != 0;
  cfg->blksz = inl(DISK_ADDR + DISK_BLKSZ);
  cfg->blkcnt = inl(DISK_ADDR + DISK_NBLKCNT);
}

void __am_disk_status(AM_DISK_STATUS_T *stat) {
  stat->ready = inl(DISK_ADDR + DISK_READY) == 1;
}

void __am_disk_blkio(AM_DISK_BLKIO_T *io) {
  outl(DISK_ADDR + DISK_BLKNO, io->blkno);
  outl(DISK_ADDR + DISK_BLKCNT, io->blkcnt);
  outl(DISK_ADDR + DISK_BUF_LO, (uint32_t)((uintptr_t)io->buf));
  outl(DISK_ADDR + DISK_BUF_HI, (uint32_t)((uintptr_t)io->buf >> 32));
  outl(DISK_ADDR + DISK_WRITE, io->write ? 1 : 0);
  outl(DISK_ADDR + DISK_CMD, 1); // trigger the transfer
}