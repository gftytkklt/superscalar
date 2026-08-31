ENTRY(_start)

MEMORY {
  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
  sdram (rwx) : ORIGIN = 0xa0000000, LENGTH = 16M
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
}

SECTIONS {
  /* bootloader：VMA=LMA=flash，NPC 复位后从 flash 取指执行。
   * 它把主程序从 flash(LMA) 搬入 SDRAM(VMA)，再跳转 SDRAM 执行（阶段 H）。
   * 栈保留在 SRAM。 */
  . = ORIGIN(flash);
  .bootloader : {
    *(entry)
    *(.bootloader)
    *(.text.bootloader)
    *(.text.*.bootloader)
    *(.rodata.bootloader)
    *(.data.bootloader)
  } > flash

  /* 主程序：VMA=SDRAM，LMA=flash（-O binary 按 LMA 输出，.bin 是连续 flash 镜像）。 */
  . = ORIGIN(sdram);
  .text : ALIGN(0x8) {
    *(.text*)
  } > sdram AT> flash
  _text_vma = ADDR(.text);
  _text_lma = LOADADDR(.text);
  etext = .;
  _etext = .;
  .rodata : ALIGN(0x8) {
    *(.rodata*)
    *(.srodata*)
  } > sdram AT> flash
  .data : ALIGN(0x8) {
    _sdata = .;
    *(.data*)
    *(.sdata*)
    /* RT-Thread 节信息（finsh 符号表 + 组件自动初始化表），与 linker-psram.ld 同策略。
     * 对无这些输入节的程序（cpu-tests/mem-test）无影响。 */
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
  } > sdram AT> flash
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  .bss : {
    _bss_start = ALIGN(0x0008);
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    _bss_end = .;
  } > sdram

  /* 栈：SRAM（bootloader 用绝对地址 la sp, _stack_pointer 设定）。 */
  _stack_pointer = _sram_start + _stack_offt;

  /* 堆区：SDRAM，从代码/bss 之后（对齐 0x1000）起，大小 = HEAP_SIZE（--defsym=_heap_size）。
   * 默认 32KB；mem-test 用小堆（如 HEAP_SIZE=0x1000=4KB）快速扫测。 */
  . = ALIGN(0x1000);
  _heap_start = .;
  _heap_end = _heap_start + _heap_size;
  end = .;
  _end = .;
}