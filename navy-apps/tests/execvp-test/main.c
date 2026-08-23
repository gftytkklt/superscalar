#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

// Mimic NTerm's builtin shell: execvp() searches PATH to run a busybox applet.
int main() {
  setenv("PATH", "/bin", 0);
  printf("[execvp-test] PATH=%s, execvp(\"cat\", ...)\n", getenv("PATH"));
  char *argv[] = {"cat", "/share/files/num", NULL};
  execvp("cat", argv);
  printf("[execvp-test] execvp failed\n");
  return 0;
}