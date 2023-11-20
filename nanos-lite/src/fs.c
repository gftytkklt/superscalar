#include <fs.h>

typedef size_t (*ReadFn) (void *buf, size_t offset, size_t len);
typedef size_t (*WriteFn) (const void *buf, size_t offset, size_t len);

typedef struct {
  char *name;
  size_t size;
  size_t disk_offset;
  ReadFn read;
  WriteFn write;
} Finfo;

enum {FD_STDIN, FD_STDOUT, FD_STDERR, FD_FB};

size_t invalid_read(void *buf, size_t offset, size_t len) {
  panic("should not reach here");
  return 0;
}

size_t invalid_write(const void *buf, size_t offset, size_t len) {
  panic("should not reach here");
  return 0;
}

size_t serial_write(const void *buf, size_t offset, size_t len);

/* This is the information about all files in disk. */
static Finfo file_table[] __attribute__((used)) = {
  [FD_STDIN]  = {"stdin", 0, 0, invalid_read, invalid_write},
  [FD_STDOUT] = {"stdout", 0, 0, invalid_read, serial_write},
  [FD_STDERR] = {"stderr", 0, 0, invalid_read, serial_write},
#include "files.h"
};

static int filenum = sizeof(file_table) / sizeof(Finfo);
static long *fp_offt = NULL;

// const char* get_filename(int fd){
//   return (fd < filenum) ? file_table[fd].name : "undef file!";
// }

int fs_open(const char *pathname, int flags, int mode) {
  for(int i=0;i<filenum;i++){
    if(!strcmp(file_table[i].name, pathname)){return i;}
  }
  return -1;
}

long fs_read(int fd, void *buf, size_t len) {

  long rd_offt = fp_offt[fd] + file_table[fd].disk_offset;
  long offt_incr = 0;
  // normal file
  if (file_table[fd].read == NULL) {
    size_t ramdisk_rd_len = (fp_offt[fd] + len) < file_table[fd].size ? len : (file_table[fd].size - fp_offt[fd]);
    offt_incr = ramdisk_read(buf, rd_offt, ramdisk_rd_len);
  }
  // abstract file
  else {
    offt_incr = file_table[fd].read(buf, rd_offt, len);
  }
  fp_offt[fd] += offt_incr;
  return offt_incr;
}

long fs_write(int fd, const void *buf, size_t len) {
  long wr_offt = fp_offt[fd] + file_table[fd].disk_offset;
  long offt_incr = 0;
  if (file_table[fd].write == NULL) {
    size_t ramdisk_wr_len = (fp_offt[fd] + len) < file_table[fd].size ? len : (file_table[fd].size - fp_offt[fd]);
    offt_incr = ramdisk_write(buf, wr_offt, ramdisk_wr_len);
  }
  else {
    offt_incr = file_table[fd].write(buf, wr_offt, len);
  }
  //printf("fs_write %d at %p\n",fd, &fp_offt[fd]);
  fp_offt[fd] += offt_incr;
  return offt_incr;
}

long fs_lseek(int fd, size_t offset, int whence) {
  switch(whence) {
    case SEEK_SET: fp_offt[fd] = offset;break;
    case SEEK_CUR: fp_offt[fd] += offset;break;
    case SEEK_END: fp_offt[fd] = file_table[fd].size + offset;break;
    default: return -1;
  }
  return fp_offt[fd];
}

int fs_close(int fd) {
  fp_offt[fd] = 0;
  return 0;
}

void init_fs() {
  fp_offt=(long*)malloc(filenum*sizeof(long));
  for(int i=0;i<filenum;i++){fp_offt[i] = 0;}
  // TODO: initialize the size of /dev/fb
}
