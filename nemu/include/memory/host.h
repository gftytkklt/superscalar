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

#ifndef __MEMORY_HOST_H__
#define __MEMORY_HOST_H__

#include <common.h>

// Local integer objects avoid alignment and effective-type assumptions on RAM.
static inline word_t host_read(void *addr, int len) {
  switch (len) {
    case 1: { uint8_t data; memcpy(&data, addr, 1); return data; }
    case 2: { uint16_t data; memcpy(&data, addr, 2); return data; }
    case 4: { uint32_t data; memcpy(&data, addr, 4); return data; }
    IFDEF(CONFIG_ISA64, case 8: { uint64_t data; memcpy(&data, addr, 8); return data; });
    default: MUXDEF(CONFIG_RT_CHECK, assert(0), return 0);
  }
}

static inline void host_write(void *addr, int len, word_t data) {
  switch (len) {
    case 1: { uint8_t value = data; memcpy(addr, &value, 1); return; }
    case 2: { uint16_t value = data; memcpy(addr, &value, 2); return; }
    case 4: { uint32_t value = data; memcpy(addr, &value, 4); return; }
    IFDEF(CONFIG_ISA64, case 8: { uint64_t value = data; memcpy(addr, &value, 8); return; });
    IFDEF(CONFIG_RT_CHECK, default: assert(0));
  }
}

#endif
