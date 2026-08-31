ENTRY(_start)

MEMORY {
  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
  psram (rwx) : ORIGIN = 0x80000000, LENGTH = 4M
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
}

SECTIONS {
  /* bootloader：VMA=LMA=flash，NPC 复位后从 flash 取指执行。
   * 它把主程序从 flash(LMA) 搬入 PSRAM(VMA)，再跳转 PSRAM 执行。
   * 栈保留在 SRAM（提升函数调用/局部变量效率，讲义阶段 E 要求）。 */
  . = ORIGIN(flash);
  .bootloader : {
    *(entry)
    *(.bootloader)
    *(.text.bootloader)
    *(.text.*.bootloader)
    *(.rodata.bootloader)
    *(.data.bootloader)
  } > flash

  /* 主程序：VMA=PSRAM，LMA=flash（-O binary 按 LMA 输出，.bin 是连续 flash 镜像）。 */
  . = ORIGIN(psram);
  .text : ALIGN(0x8) {
    *(.text*)
  } > psram AT> flash
  _text_vma = ADDR(.text);
  _text_lma = LOADADDR(.text);
  etext = .;
  _etext = .;
  .rodata : ALIGN(0x8) {
    *(.rodata*)
    *(.srodata*)
  } > psram AT> flash
  .data : ALIGN(0x8) {
    _sdata = .;
    *(.data*)
    *(.sdata*)
    /* RT-Thread 节信息（finsh 符号表 + 组件自动初始化表）。原本由 rt/bsp/abstract-machine 的
     * extra.ld 以 INSERT BEFORE .data 注入；但 INSERT 在带 MEMORY 区域的脚本下会把该节错放到
     * SRAM 基址(独立 LOAD 段)，导致 flash 镜像跨度巨大(528MB)无法加载。故直接并入 .data，
     * 随 .data 一起被 bootloader/trm loader 搬入 PSRAM。对无这些输入节的程序无影响。 */
    . = ALIGN(0x8);
    __fsymtab_start = .;
    KEEP(*(FSymTab))
    __fsymtab_end = .;
    . = ALIGN(0x8);
    __vsymtab_start = .;
    KEEP(*(VSymTab))
    __vsymtab_end = .;
    . = ALIGN(0x8);
    __rt_init_start = .;
    KEEP(*(SORT(.rti_fn*)))
    __rt_init_end = .;
    . = ALIGN(0x8);
    __rt_utest_tc_tab_start = .;
    KEEP(*(UtestTcTab))
    __rt_utest_tc_tab_end = .;
    _edata = .;
  } > psram AT> flash
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  .bss : {
    _bss_start = ALIGN(0x0008);
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    _bss_end = .;
  } > psram

  /* 栈：SRAM（bootloader 用绝对地址 la sp, _stack_pointer 设定）。 */
  _stack_pointer = _sram_start + _stack_offt;

  /* 堆区：PSRAM，从代码/bss 之后（对齐 0x1000）到 PSRAM 顶。
   * 大小自动 = 4MB - 代码/数据占用，无需 HEAP_SIZE。 */
  . = ALIGN(0x1000);
  _heap_start = .;
  _heap_end = ORIGIN(psram) + LENGTH(psram);
  end = .;
  _end = .;
}