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

#include <isa.h>
#include <cpu/cpu.h>
#include <memory/vaddr.h>
#include <readline/readline.h>
#include <readline/history.h>
#include "sdb.h"

static int is_batch_mode = false;

void init_regex();
//void init_wp_pool();
WP *wp;

/* We use the `readline' library to provide more flexibility to read from stdin. */
static char* rl_gets() {
  static char *line_read = NULL;

  if (line_read) {
    free(line_read);
    line_read = NULL;
  }

  line_read = readline("(nemu) ");

  if (line_read && *line_read) {
    add_history(line_read);
  }

  return line_read;
}

static int cmd_c(char *args) {
  cpu_exec(-1);
  return 0;
}


static int cmd_q(char *args) {
  nemu_state.state = NEMU_QUIT;
  return -1;
}

static int cmd_si(char *args) {
  int step = 1;
  char *arg = strtok(NULL, " ");
  if (arg != NULL){sscanf(arg, "%u", &step);}
  cpu_exec(step);
  return 0;
}

static int cmd_info(char *args) {
  char *arg = strtok(NULL, " ");
  char info[] = "usage:\ninfo r: print reg value\ninfo w: print watch points info\n";
  if (arg == NULL){printf("%s", info);}
  else if(strcmp(arg, "r")==0){isa_reg_display();}
  else if(strcmp(arg, "w")==0){print_wp_info();}
  else{printf("%s", info);}
  return 0;
}

static int cmd_x(char *args) {
//  char *arg = strtok(NULL, " ");
  char *lenstr = strtok(NULL, " ");
  char *addrstr = strtok(NULL, "");
  char info[] = "usage: x <word_num> <base_addr>\n";
  if((addrstr == NULL) || (lenstr == NULL)){printf("%s", info);}
  else{
    unsigned rd_len = 0;
    unsigned long addr = 0;
    sscanf(lenstr, "%u", &rd_len);
    bool success = true;
    addr = expr(addrstr, &success);
    if(!success){printf("check addr expr\n");return 0;}
    //sscanf(addrstr, "%lx", &addr);
    for (int i=0;i<rd_len;i++){
      printf("0x%lx: %08lx\n", addr, vaddr_read(addr, 4));
      addr += 4;
      /*for(int j=0;j<4;j++){
        printf("%02lx ", vaddr_read(addr, 1));
        addr++;
      }
      printf("\n");*/
    }
  }
  return 0;
}

static int cmd_p(char *args) {
  bool success = true;
  unsigned long result = expr(args, &success);
  if(success) {printf("result = %lu(unsigned), %016lx(hex)\n", result, result);}
  else {printf("invalid expr\n");}
  return 0;
}

static int cmd_w(char *args) {
  char *arg = strtok(NULL, "");
  bool success = true;
  unsigned long result = expr(arg, &success);
  if(!success) {return 0;}
  //struct WP *wp;
  wp = new_wp();
  wp->expr_value = result;
  sscanf(arg, "%[^n]", wp->expr_str);
  printf("watch point NO%d of %s added\n",wp->NO, wp->expr_str);
  return 0;
  return 0;
}

static int cmd_d(char *args) {
  char *arg = strtok(NULL, " ");
  if (arg == NULL) {printf("input watchpoint number!\n");return 0;}
  else {int num = 0; sscanf(arg, "%u", &num);free_wp(num);}
  return 0;
}
static int cmd_help(char *args);

static struct {
  const char *name;
  const char *description;
  int (*handler) (char *);
} cmd_table [] = {
  { "help", "Display information about all supported commands", cmd_help },
  { "c", "Continue the execution of the program", cmd_c },
  { "q", "Exit NEMU", cmd_q },
  { "si", "Execute <inst_num> step(s), defalt=1", cmd_si },
  { "info", "Print CPU status", cmd_info },
  { "x", "Scan memory", cmd_x },
  { "p", "Expr eval", cmd_p },
  { "w", "Set watchpoints", cmd_w },
  { "d", "Delete watchpoints", cmd_d },
};

#define NR_CMD ARRLEN(cmd_table)

static int cmd_help(char *args) {
  /* extract the first argument */
  char *arg = strtok(NULL, " ");
  int i;

  if (arg == NULL) {
    /* no argument given */
    for (i = 0; i < NR_CMD; i ++) {
      printf("%s - %s\n", cmd_table[i].name, cmd_table[i].description);
    }
  }
  else {
    for (i = 0; i < NR_CMD; i ++) {
      if (strcmp(arg, cmd_table[i].name) == 0) {
        printf("%s - %s\n", cmd_table[i].name, cmd_table[i].description);
        return 0;
      }
    }
    printf("Unknown command '%s'\n", arg);
  }
  return 0;
}

void sdb_set_batch_mode() {
  is_batch_mode = true;
}

void sdb_mainloop() {
  if (is_batch_mode) {
    cmd_c(NULL);
    return;
  }

  for (char *str; (str = rl_gets()) != NULL; ) {
    char *str_end = str + strlen(str);

    /* extract the first token as the command */
    char *cmd = strtok(str, " ");
    if (cmd == NULL) { continue; }

    /* treat the remaining string as the arguments,
     * which may need further parsing
     */
    char *args = cmd + strlen(cmd) + 1;
    if (args >= str_end) {
      args = NULL;
    }

#ifdef CONFIG_DEVICE
    extern void sdl_clear_event_queue();
    sdl_clear_event_queue();
#endif

    int i;
    for (i = 0; i < NR_CMD; i ++) {
      if (strcmp(cmd, cmd_table[i].name) == 0) {
        if (cmd_table[i].handler(args) < 0) { return; }
        break;
      }
    }

    if (i == NR_CMD) { printf("Unknown command '%s'\n", cmd); }
  }
}

void init_sdb() {
  /* Compile the regular expressions. */
  init_regex();

  /* Initialize the watchpoint pool. */
  init_wp_pool();

  /* Initialize the ringbuf. */
  init_ringbuf();
}

static ringbuf ring[RINGBUF_LEN] = {};
static ringbuf* current_buf;
void init_ringbuf() {
  for (int i=0;i<(RINGBUF_LEN-1);i++) {
  strcpy(ring[i].instlog, "empty");
  ring[i].next = &ring[i+1];
  }
  strcpy(ring[RINGBUF_LEN-1].instlog, "empty");
  ring[RINGBUF_LEN-1].next = &ring[0];
  current_buf = ring;
}

void write_ringbuf(char *str){
  snprintf(current_buf->instlog, 128, "%s", str);
  current_buf = current_buf->next;
}
void inst_hist_display() {
  for (int i=0;i<RINGBUF_LEN;i++){
    if (current_buf == ring[i].next) {printf("--> ");}
    else {printf("    ");}
    printf("%s\n", ring[i].instlog);
  }
}
