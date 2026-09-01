ENTRY(_start)

MEMORY {
  mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
  sram (rw) : ORIGIN = 0x0f000000, LENGTH = 8K
  sdram (rwx) : ORIGIN = 0xa0000000, LENGTH = 128M
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
}

SECTIONS {
  /* 程序 flash XIP（difftest 可对拍），堆区分配在 SDRAM —— 用于 mem-test 扫 SDRAM。
   * 阶段 H：mem-test 从 flash 执行，只把 _heap_start~_heap_end 放在 SDRAM，
   * 对 SDRAM 的访存经 mmio skip（NEMU 无 SDRAM），由 mem-test 自校验。 */
  . = ORIGIN(flash);
  .text : {
    *(entry)
    *(.text*)
  } > flash
  etext = .;
  _etext = .;
  .rodata : ALIGN(0x8) {
    *(.rodata*)
    *(.srodata*)
  } > flash
  .data : ALIGN(0x8) {
    _sdata = .;
    *(.data*)
    *(.sdata*)
    _edata = .;
  } > sram AT> flash
  .bss : {
    _bss_start = ALIGN(0x0008);
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    _bss_end = .;
  } > sram
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  _stack_pointer = _sram_start + _stack_offt;
  . = _stack_pointer;
  /* 堆区：SDRAM（0xa0000000 起，可缓存 16MB），大小 = HEAP_SIZE（默认 32KB）。 */
  _heap_start = 0xa0000000;
  _heap_end = _heap_start + _heap_size;
  end = .;
  _end = .;
}