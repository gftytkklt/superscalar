ENTRY(_start)

MEMORY {
  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
  sdram (rwx) : ORIGIN = 0xa0000000, LENGTH = 128M
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
}

SECTIONS {
  /* 单级 bootloader：VMA=LMA=flash，NPC 复位后从 flash 取指执行。
   * 它把主程序从 flash(LMA) 搬入 SDRAM(VMA)，再跳转到 SDRAM 执行。
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

  /* 主程序（RT-Thread + am-apps）：VMA=SDRAM，LMA=flash（-O binary 按 LMA 输出，
   * .bin 是连续 flash 镜像）。 */
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
    /* RT-Thread 节信息（finsh 符号表 + 组件自动初始化表）。 */
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
    /* 阶段 J5 am-apps：集成 AM 程序的数据段。 */
    . = ALIGN(0x8);
    __am_apps_data_start = .;
    *(__am_apps.data*)
    *(__am_apps.sdata*)
    __am_apps_data_end = .;
    _edata = .;
  } > sdram AT> flash
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  .bss : {
    _bss_start = ALIGN(0x0008);
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    /* 阶段 J5 am-apps：集成 AM 程序的 bss 段。 */
    . = ALIGN(0x8);
    __am_apps_bss_start = .;
    *(__am_apps.bss*)
    *(__am_apps.sbss*)
    *(__am_apps.scommon*)
    __am_apps_bss_end = .;
    _bss_end = .;
  } > sdram

  /* 栈：SRAM（bootloader 用绝对地址 la sp, _stack_pointer 设定）。 */
  _stack_pointer = _sram_start + _stack_offt;

  /* 堆区：SDRAM 顶（RT-Thread heap = AM heap = [_heap_start,_heap_end)，需大）。
   * 大小自动 = 128MB - 代码/数据占用（对齐 0x1000）。 */
  . = ALIGN(0x1000);
  _heap_start = .;
  _heap_end = ORIGIN(sdram) + LENGTH(sdram);
  end = .;
  _end = .;
}
