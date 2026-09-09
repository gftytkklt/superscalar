#include <common.h>
#include <string.h>

#define BLKSZ 512
static uint8_t blkbuf[BLKSZ] __attribute__((aligned(8)));

#ifdef KERNEL_EMBED_RAMDISK
// Fallback backing store for platforms without a disk device (e.g. NPC SoC):
// the whole fsimg is embedded into the kernel image at build time.
extern char ramdisk_start, ramdisk_end;
#endif

static int disk_present = 0;
static char *embed_ptr = NULL;
static size_t embed_size = 0;

void init_disk() {
  AM_DISK_CONFIG_T cfg = io_read(AM_DISK_CONFIG);
  disk_present = cfg.present;
  if (disk_present) {
    assert(cfg.blksz == BLKSZ);
    Log("disk: blksz=%d blkcnt=%d", cfg.blksz, cfg.blkcnt);
    return;
  }
#ifdef KERNEL_EMBED_RAMDISK
  embed_ptr = &ramdisk_start;
  embed_size = (size_t)(&ramdisk_end - &ramdisk_start);
  Log("disk device absent, using embedded ramdisk: %d bytes", (int)embed_size);
#else
  Log("disk device absent and no embedded ramdisk, disk disabled");
#endif
}

static size_t embed_read(void *buf, size_t offset, size_t len) {
  if (offset >= embed_size) return 0;
  if (len > embed_size - offset) len = embed_size - offset;
  memcpy(buf, embed_ptr + offset, len);
  return len;
}

/* read `len` bytes at byte offset `offset` from the disk into `buf` */
size_t disk_read(void *buf, size_t offset, size_t len) {
  if (!disk_present) return embed_read(buf, offset, len);
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
  if (!disk_present) {
    // embedded ramdisk: in-memory write-back (the section is writable)
    if (!embed_ptr) return 0;
    if (offset >= embed_size) return 0;
    if (len > embed_size - offset) len = embed_size - offset;
    memcpy(embed_ptr + offset, buf, len);
    return len;
  }
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
