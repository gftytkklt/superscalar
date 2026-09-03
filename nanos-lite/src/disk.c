#include <common.h>
#include <string.h>

#define BLKSZ 512
static uint8_t blkbuf[BLKSZ] __attribute__((aligned(8)));

void init_disk() {
  AM_DISK_CONFIG_T cfg = io_read(AM_DISK_CONFIG);
  assert(cfg.present);
  Log("disk: blksz=%d blkcnt=%d", cfg.blksz, cfg.blkcnt);
}

/* read `len` bytes at byte offset `offset` from the disk into `buf` */
size_t disk_read(void *buf, size_t offset, size_t len) {
  size_t blksz = io_read(AM_DISK_CONFIG).blksz;
  size_t done = 0;
  while (done < len) {
    size_t pos = offset + done;
    size_t blkno = pos / blksz;
    size_t in_blk = pos % blksz;
    size_t n = (len - done < blksz - in_blk) ? (len - done) : (blksz - in_blk);
    // read the block into blkbuf (a phys-addressable buffer), then copy out
    io_write(AM_DISK_BLKIO, .write = 0, .buf = blkbuf, .blkno = blkno, .blkcnt = 1);
    memcpy((char *)buf + done, blkbuf + in_blk, n);
    done += n;
  }
  return len;
}

/* write `len` bytes from `buf` to byte offset `offset` on the disk */
size_t disk_write(const void *buf, size_t offset, size_t len) {
  size_t blksz = io_read(AM_DISK_CONFIG).blksz;
  size_t done = 0;
  while (done < len) {
    size_t pos = offset + done;
    size_t blkno = pos / blksz;
    size_t in_blk = pos % blksz;
    size_t n = (len - done < blksz - in_blk) ? (len - done) : (blksz - in_blk);
    // read-modify-write: pull the block, patch the bytes, push it back
    io_write(AM_DISK_BLKIO, .write = 0, .buf = blkbuf, .blkno = blkno, .blkcnt = 1);
    memcpy(blkbuf + in_blk, (const char *)buf + done, n);
    io_write(AM_DISK_BLKIO, .write = 1, .buf = blkbuf, .blkno = blkno, .blkcnt = 1);
    done += n;
  }
  return len;
}