#include <stdio.h>
#include <assert.h>
#include <NDL.h>

int main() {
  NDL_Init(0);
  uint32_t half_sec = 500;
  while(1) {
    uint32_t cur_time = NDL_GetTicks();
    if(cur_time >= half_sec){
      printf("%d ms\n", cur_time);
      half_sec += 500;
    }
  }
  return 0;
}
