#!/usr/bin/env python3

import sys, os, shutil, subprocess, tempfile
from pathlib import Path

# global settings
AM_HOME = Path(os.environ["AM_HOME"])
AM_KERNELS_HOME = (AM_HOME / ".." / "am-kernels").resolve()
app_dir_list = [
  AM_KERNELS_HOME / "kernels" / "hello",
  AM_KERNELS_HOME / "benchmarks" / "microbench",
  AM_KERNELS_HOME / "kernels" / "typing-game",
  AM_KERNELS_HOME / "kernels" / "snake",
  # fceux-am：已修 gcc-13 -Werror（emufile.cpp 指针遍历）+ 注入 mario.nes，能编译链接；
  #   但已集成到 rt 时其超大 .bss(1.6MB) 使启动搬运过慢，故从 am-apps 集成中**移除**。
  #   若需跑，再临时加回（nes/rom/mario.nes 保留在 fceux-am，随 build-roms.py 再生成）。
  # AM_KERNELS_HOME / ".." / "fceux-am",
]

if len(sys.argv) != 3:
    print("Usage: python3 integrate-am-apps.py ARCH=[AM arch] CROSS_COMPILE=[prefix]")
    exit(-1)
if not sys.argv[1].startswith("ARCH="):
    print("Bad ARCH argument")
    exit(-1)
ARCH = sys.argv[1][5:]
if not sys.argv[2].startswith("CROSS_COMPILE="):
    print("Bad CROSS_COMPILE argument")
    exit(-1)
CROSS_COMPILE = sys.argv[2][14:]

lib_sym = [
  "memset", "memcpy", "memmove", "memcmp",
  "strlen", "strcat", "strcpy", "strncpy", "strcmp", "strncmp",
  "srand", "rand", "malloc", "free", "abs", "atoi",
  "printf", "sprintf", "snprintf", "vsprintf", "vsnprintf",
]
am_init_sym = [ "trm_init", "ioe_init", "cte_init", "vme_init", "mpe_init" ]

def run_tool(argv, **kwargs):
    print("+ " + " ".join(argv), flush=True)
    return subprocess.run(argv, check=True, **kwargs)

def read_lib_symbols(lib):
    libfile = AM_HOME / lib / "build" / f"{lib}-{ARCH}.a"
    if (not libfile.exists()):
        run_tool(["make", "-j", f"ARCH={ARCH}", "-C", str(AM_HOME / lib), "archive"])
    res = run_tool([f"{CROSS_COMPILE}nm", "-g", "--defined-only",
                    "--format=just-symbols", str(libfile)], stdout=subprocess.PIPE, text=True)
    global lib_sym
    lib_sym = sorted(set(lib_sym + res.stdout.split()))

def integrate(app_dir, generation, am_app_mk_fp, am_app_c_fp):
    app_name = app_dir.name.replace("-", "_")
    run_tool(["make", "-j", f"ARCH={ARCH}", "-C", str(app_dir)])
    dst = generation / app_name
    shutil.copytree(app_dir / "build" / ARCH, dst)
    objs = sorted(dst.rglob("*.o"))
    if not objs:
        raise RuntimeError(f"{app_name}: no object files in {dst}")
    redefine_sym_file = generation / "redefine_sym.txt"
    with redefine_sym_file.open("w") as redefine_sym_fp:
        for f in lib_sym:
            if f in am_init_sym:
                redefine_sym_fp.write(f"__am_{app_name}_{f} __dummy_{f}\n")
            elif f == "halt":
                redefine_sym_fp.write(f"__am_{app_name}_{f} __rt_am_halt\n")
            else:
                redefine_sym_fp.write(f"__am_{app_name}_{f} {f}\n")
    for obj in objs:
        run_tool([f"{CROSS_COMPILE}objcopy", f"--prefix-symbols=__am_{app_name}_",
                  "--set-section-flags", ".text*=readonly,noload",
                  "--set-section-flags", ".*rodata*=readonly,noload", str(obj)])
        run_tool([f"{CROSS_COMPILE}objcopy", f"--redefine-syms={redefine_sym_file}",
                  "--prefix-alloc-sections=__am_apps", str(obj)])
        run_tool([f"{CROSS_COMPILE}objcopy", "--set-section-flags", ".text*=readonly,code,alloc",
                  "--set-section-flags", ".*rodata*=readonly,data,alloc", str(obj)])
        am_app_mk_fp.write("SRCS += " + str(obj.relative_to("build/" + ARCH)) + "\n")
    os.remove(redefine_sym_file)
    am_app_c_fp.write(f"""extern int __am_{app_name}_main(const char *);
static void am_{app_name}(int argc, char *argv[]) {{
  am_app_start_wrapper("{app_name}", __am_{app_name}_main, argc, argv);
}}
MSH_CMD_EXPORT(am_{app_name}, AM {app_name});
""")

AM_APP_C = """#include <am.h>
#include <klib.h>
#include <rtthread.h>
extern Area am_apps_heap, am_apps_data, am_apps_bss;
extern uint8_t * am_apps_data_content;
struct am_app_args {
  int (*main)(const char *);
  char mainargs[];
};
static void am_app_cleanup(struct rt_thread *thread) {
  rt_free(thread->parameter);
  thread->parameter = RT_NULL;
}
static void am_app_start_thread(void *parameter) {
  struct am_app_args *args = parameter;
  args->main(args->mainargs);
}
static void am_app_start_wrapper(const char *app_name, int (*app_main)(const char *), int argc, char *argv[]) {
  const char *mainargs = (argc >= 2 ? argv[1] : "");
  rt_size_t size = rt_strlen(mainargs) + 1;
  struct am_app_args *args = rt_malloc(sizeof(*args) + size);
  if (args == RT_NULL) {
    rt_kprintf("AM app %s: no memory for arguments\\n", app_name);
    return;
  }
  args->main = app_main;
  rt_memcpy(args->mainargs, mainargs, size);
  rt_thread_t tid = rt_thread_create(app_name, am_app_start_thread, args, 0x4000, 0, 20);
  if (tid == RT_NULL) {
    rt_free(args);
    rt_kprintf("AM app %s: thread creation failed\\n", app_name);
    return;
  }
  // RT's idle cleanup owns the record, including exit/delete before entry.
  tid->cleanup = am_app_cleanup;
  memcpy(am_apps_data.start, am_apps_data_content, am_apps_data.end - am_apps_data.start);
  memset(am_apps_bss.start, 0, am_apps_bss.end - am_apps_bss.start);
  heap = am_apps_heap;
  if (rt_thread_startup(tid) != RT_EOK) {
    rt_thread_delete(tid);
    rt_kprintf("AM app %s: thread startup failed\\n", app_name);
  }
}
bool __dummy_ioe_init() { return true; }
bool __dummy_cte_init(Context *(*handler)(Event ev, Context *ctx)) { return true; }
bool __dummy_vme_init(void *(*pgalloc)(int), void (*pgfree)(void *)) { return true; }
bool __dummy_mpe_init(void (*entry)()) { return true; }
void __rt_am_halt(int code) {
  void rt_thread_exit(void);
  rt_thread_exit();
}
"""

def generate():
    build_dir = Path("build") / ARCH
    generations = build_dir / "am-apps"
    generations.mkdir(parents=True, exist_ok=True)
    generation = Path(tempfile.mkdtemp(prefix="gen-", dir=generations)).resolve().relative_to(Path.cwd())
    try:
        read_lib_symbols("am")
        read_lib_symbols("klib")
        with (generation / "am-apps.mk").open("w") as mk_fp, \
             (generation / "am-apps.c").open("w") as c_fp:
            mk_fp.write(f"SRCS += {generation / 'am-apps.c'}\n")
            c_fp.write(AM_APP_C)
            for app in app_dir_list:
                integrate(app, generation, mk_fp, c_fp)
        # The mk is the single publication point for its immutable C/object set.
        os.replace(generation / "am-apps.mk", build_dir / "am-apps.mk")
    except BaseException:
        shutil.rmtree(generation, ignore_errors=True)
        raise
    # Previous generations remain available until the existing `make clean`.

if __name__ == "__main__":
    try:
        generate()
    except (subprocess.CalledProcessError, OSError, RuntimeError) as error:
        print(f"AM application integration failed: {error}", file=sys.stderr)
        sys.exit(1)
