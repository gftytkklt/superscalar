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

#ifndef __SDB_H__
#define __SDB_H__

#include <common.h>

word_t expr(char *e, bool *success);
//struct watchpoint;
typedef struct watchpoint {
  int NO;
  struct watchpoint *next;
  unsigned long expr_value;
  char expr_str[128];
  int triggered_time;
  /* TODO: Add more members if necessary */
} WP;
void init_wp_pool();
void print_wp_info();
WP* new_wp();
void free_wp(int n);
//ringbuf

#define RINGBUF_LEN 64
typedef struct ringbuf{
  char instlog[128];
  struct ringbuf* next;
} ringbuf;
void init_ringbuf();
void write_ringbuf(char* str);
void inst_hist_display();

#endif
