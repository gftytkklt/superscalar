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
#include <memory/vaddr.h>

/* We use the POSIX regex functions to process regular expressions.
 * Type 'man regex' for more information about POSIX regex functions.
 */
#include <regex.h>

enum {
  TK_NOTYPE = 256, TK_EQ, TK_NUM, TK_LP, TK_RP, TK_HEX, TK_REG, TK_NEQ, TK_AND, TK_NLT, TK_NMT,

  /* TODO: Add more token types */

};

static struct rule {
  const char *regex;
  int token_type;
} rules[] = {

  /* TODO: Add more rules.
   * Pay attention to the precedence level of different rules.
   */

  {" +", TK_NOTYPE},    // spaces
  {"\\+", '+'},         // plus
  {"\\-", '-'},		// minus
  {"\\*", '*'},		// multiplication
  {"/",'/'},		// division
  {"==", TK_EQ},        // equal
  {"0x[0-9a-fA-F]+", TK_HEX}, // hex num
  {"[0-9]+", TK_NUM},	// decimal num
  {"\\(", TK_LP},	// left parentheses
  {"\\)", TK_RP},	// right parentheses
  //{"U", TK_NOTYPE},     // unsigned label, doesn't affect cal(for test)
  //{"L", TK_NOTYPE},     // long label, doesn't affect cal(for test)
  {"\\$[$0-9a-z]{2,3}", TK_REG}, // reg data, start with $
  {"!=", TK_NEQ},	// non equal
  {"&&", TK_AND},	// logical and
  {"<=", TK_NMT},
  {">=", TK_NLT},
  {"<", '<'},
  {">", '>'},
  
};

#define NR_REGEX ARRLEN(rules)

static regex_t re[NR_REGEX] = {};

/* Rules are used for many times.
 * Therefore we compile them only once before any usage.
 */
void init_regex() {
  int i;
  char error_msg[128];
  int ret;

  for (i = 0; i < NR_REGEX; i ++) {
    ret = regcomp(&re[i], rules[i].regex, REG_EXTENDED);
    if (ret != 0) {
      regerror(ret, &re[i], error_msg, 128);
      panic("regex compilation failed: %s\n%s", error_msg, rules[i].regex);
    }
  }
}

typedef struct token {
  int type;
  char str[32];
} Token;

static Token tokens[32] __attribute__((used)) = {};
static int nr_token __attribute__((used))  = 0;

static bool make_token(char *e) {
  int position = 0;
  int i;
  regmatch_t pmatch;

  nr_token = 0;

  while (e[position] != '\0') {
    /* Try all rules one by one. */
    for (i = 0; i < NR_REGEX; i ++) {
      if (regexec(&re[i], e + position, 1, &pmatch, 0) == 0 && pmatch.rm_so == 0) {
        char *substr_start = e + position;
        int substr_len = pmatch.rm_eo;
        if (substr_len > 32){printf("too long element!\n");return false;}

        //Log("match rules[%d] = \"%s\" at position %d with len %d: %.*s",
        //    i, rules[i].regex, position, substr_len, substr_len, substr_start);

        position += substr_len;

        /* TODO: Now a new token is recognized with rules[i]. Add codes
         * to record the token in the array `tokens'. For certain types
         * of tokens, some extra actions should be performed.
         */
        bool save_data = true;
        switch (rules[i].token_type) {
          case TK_NOTYPE: save_data = false;break;
          case TK_NUM: sscanf(substr_start, "%[0-9]s", tokens[nr_token].str);break;
          case TK_HEX: sscanf(substr_start, "%*[^x]x%[0-9a-fA-F]", tokens[nr_token].str);break;
          case TK_REG: sscanf(substr_start, "%*1[$]%3[$0-9a-z]", tokens[nr_token].str);break;
          default: break;
        }
        if(save_data){tokens[nr_token].type = rules[i].token_type; nr_token++;}
        break;
      }
    }

    if (i == NR_REGEX) {
      printf("no match at position %d\n%s\n%*.s^\n", position, e, position, "");
      return false;
    }
  }

  return true;
}

// no expr input with full parentheses
static int find_mainop(int p, int q){
  int position = 0;// position of main_op
  int delta = 0;// main_op possibility, only 0 is possible main_op
  int priority_level = 0;// main_op priority, lower value for low cal priority
  for (int i=p; i<q; i++){
    if ((tokens[i].type == TK_LP)) {delta++;}
    else if ((tokens[i].type == TK_RP)) {delta--;}
    if (delta == 0) {
      if (tokens[i].type == TK_AND) {
        position = i;
        priority_level = 1;
      }
      else if ((tokens[i].type == TK_EQ) || (tokens[i].type == TK_NEQ)) {
      	if ((priority_level == 0) || (priority_level >= 2)) {
      	  position = i;
      	  priority_level = 2;
      	}
      }
      else if ((tokens[i].type == TK_NMT) || (tokens[i].type == TK_NLT) ||(tokens[i].type == '>') || (tokens[i].type == '<')) {
      	if ((priority_level == 0) || (priority_level >= 3)) {
      	  position = i;
      	  priority_level = 3;
      	}
      }
      else if ((tokens[i].type == '+') || (tokens[i].type == '-')) {
        if ((priority_level == 0) || (priority_level >= 4)) {
      	  position = i;
      	  priority_level = 4;
      	}
      }
      else if((tokens[i].type == '*') || (tokens[i].type == '/')) {
        if ((priority_level == 0) || (priority_level >= 5)) {
      	  position = i;
      	  priority_level = 5;
      	}
      }
    }
  }
  if ((position < p) || (position >= q)) {return 0;}
  return position;
}
// return 0: valid expr with match parentheses
// return 1: valid expr without match parentheses
// return -1: invalid expr, parentheses do not match
static int check_parentheses(int p, int q) {
  int delta = 0;// LP - RP
  if ((tokens[p].type != TK_LP) || (tokens[q].type != TK_RP)) {return 1;}
  for (int i=p; i<=q; i++) {
    if(tokens[i].type == TK_LP){delta++;}
    else if(tokens[i].type == TK_RP){delta--;if(delta==0){return (i!=q);}}
    if(delta<0){return -1;}
  }
  return 1;
}
static word_t eval(int p, int q, bool *success) {
  word_t value;
  if (p>q) {
    printf("no minus lenth expr!\n");
    *success = false;
  }
  else if (p==q) {
    if (tokens[p].type == TK_NUM) {sscanf(tokens[p].str, "%lu", &value);/*printf("num = %lu\n", value);*/}
    else if (tokens[p].type == TK_HEX) {sscanf(tokens[p].str, "%lx", &value);}
    else if (tokens[p].type == TK_REG) {value = isa_reg_str2val(tokens[p].str, success);}
    else{printf("unknown value type!\n");*success = false;}
  }
  else if (check_parentheses(p, q) == -1) {printf("parentheses not match!\n");*success = false;return 0;}
  else if (check_parentheses(p, q) == 0) {return eval(p+1, q-1, success);}
  else {
    word_t op_position, val_l, val_r;
    op_position = find_mainop(p, q);
    if (op_position == 0) {printf("invalid op position!\n");*success = false;return 0;}
    else if (op_position == p) { // unary op
      value = eval(p+1,q,success);
      if ((tokens[op_position].type) == '-') {
        value = -value;
      }
      else if((tokens[op_position].type) == '*') {
        value = vaddr_read(value, sizeof(word_t));
      }
    }
    else {
      val_l = eval(p, (op_position - 1),success);
      val_r = eval((op_position + 1), q,success);
      switch (tokens[op_position].type) {
        case('+'): return (val_l + val_r);
        case('-'): return (val_l - val_r);
        case('*'): return (val_l * val_r);
        case('/'): if(val_r != 0){return (val_l / val_r);}else{printf("can't divide by 0!\n");*success = false;return 0;}
        case(TK_EQ): return (val_l == val_r);
        case(TK_NEQ): return (val_l != val_r);
        case(TK_AND): return (val_l && val_r);
        case(TK_NLT): return (val_l >= val_r);
        case(TK_NMT): return (val_l <= val_r);
        case('>'): return (val_l > val_r);
        case('<'): return (val_l < val_r);
      }
    }
  }
  return value;
}

word_t expr(char *e, bool *success) {
  if (!make_token(e)) {
    *success = false;
    return 0;
  }

  /* TODO: Insert codes to evaluate the expression. */
  return eval(0,(nr_token-1),success);
}
