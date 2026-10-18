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

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <assert.h>
#include <string.h>
#include <errno.h>
#include <limits.h>
#include <ctype.h>
#include <unistd.h>

static char buf[65536];
static char code_buf[sizeof(buf) + 128];
static size_t used;
static const char *code_format =
"#include <stdio.h>\n"
"int main() { "
"  unsigned result = %s; "
"  printf(\"%%u\", result); "
"  return 0; "
"}";

static void gen_char(char ch) {
  assert(used + 1 < sizeof(buf));
  buf[used++] = ch;
  buf[used] = '\0';
}

// Depth 3 needs at most 29 tokens, within the monitor's 32-token limit.
// Keep every intermediate in [0, INT_MAX], where C and RV64 agree.
// The returned value only selects safe operators; the C program is the oracle.
static unsigned gen_rand_expr(unsigned depth) {
  unsigned choice = depth == 3 ? 0 : (unsigned)rand() % 3;
  if (choice == 0) {
    unsigned value = (unsigned)rand() % 100;
    int n = snprintf(buf + used, sizeof(buf) - used, "%u", value);
    assert(n > 0 && (size_t)n < sizeof(buf) - used);
    used += n;
    return value;
  }

  gen_char('(');
  unsigned lhs = gen_rand_expr(depth + 1);
  if (choice == 1) {
    gen_char(')');
    return lhs;
  }

  gen_char(' ');
  size_t op_pos = used;
  gen_char('+');
  gen_char(' ');
  unsigned rhs = gen_rand_expr(depth + 1);
  gen_char(')');
  char op = "+-*/"[(unsigned)rand() % 4];
  if ((op == '+' && lhs > INT_MAX - rhs) ||
      (op == '-' && lhs < rhs) ||
      (op == '*' && rhs != 0 && lhs > INT_MAX / rhs)) {
    op = rhs != 0 ? '/' : '+';
  }
  if (op == '/' && rhs == 0) op = '+';
  buf[op_pos] = op;
  switch (op) {
    case '+': return lhs + rhs;
    case '-': return lhs - rhs;
    case '*': return lhs * rhs;
    default: return lhs / rhs;
  }
}

int main(int argc, char *argv[]) {
  long loop = 1;
  char *end;
  if (argc > 2) {
    fprintf(stderr, "Usage: %s [positive count]\n", argv[0]);
    return 1;
  }
  if (argc == 2) {
    errno = 0;
    loop = strtol(argv[1], &end, 10);
    if (errno || end == argv[1] || *end || loop <= 0 || loop > INT_MAX) {
      fprintf(stderr, "gen-expr: invalid count\n");
      return 1;
    }
  }
  srand((unsigned)time(NULL));

  char dir[] = "/tmp/gen-expr.XXXXXX";
  if (mkdtemp(dir) == NULL) {
    perror("gen-expr: mkdtemp");
    return 1;
  }
  char source[128], executable[128], command[320];
  snprintf(source, sizeof(source), "%s/code.c", dir);
  snprintf(executable, sizeof(executable), "%s/expr", dir);
  int status = 1;
  for (long i = 0; i < loop; i++) {
    used = 0;
    buf[0] = '\0';
    gen_rand_expr(0);
    int n = snprintf(code_buf, sizeof(code_buf), code_format, buf);
    if (n < 0 || (size_t)n >= sizeof(code_buf)) goto cleanup;

    FILE *fp = fopen(source, "w");
    if (fp == NULL) goto cleanup;
    int written = fputs(code_buf, fp);
    int closed = fclose(fp);
    if (written == EOF || closed != 0) goto cleanup;

    // Paths are private mkdtemp names, not command-line input.
    snprintf(command, sizeof(command), "gcc %s -o %s", source, executable);
    if (unlink(executable) != 0 && errno != ENOENT) goto cleanup;
    if (system(command) != 0) goto cleanup;
    fp = popen(executable, "r");
    if (fp == NULL) goto cleanup;
    char output[64];
    int complete = fgets(output, sizeof(output), fp) != NULL;
    int extra = fgetc(fp);
    int read_error = ferror(fp);
    int child_status = pclose(fp);
    if (!complete || extra != EOF || read_error || child_status != 0) goto cleanup;

    errno = 0;
    unsigned long result = strtoul(output, &end, 10);
    if (errno || !isdigit((unsigned char)output[0]) || result > INT_MAX) goto cleanup;
    while (isspace((unsigned char)*end)) end++;
    if (*end != '\0') goto cleanup;
    if (printf("%u %s\n", (unsigned)result, buf) < 0) goto cleanup;
  }
  if (fflush(stdout) == 0) status = 0;

cleanup:
  if (status != 0) fprintf(stderr, "gen-expr: failed to produce all requested samples\n");
  unlink(source);
  unlink(executable);
  rmdir(dir);
  return status;
}
