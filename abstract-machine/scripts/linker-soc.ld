ENTRY(_start)
/* PHDRS { text PT_LOAD; data PT_LOAD; } */

MEMORY {
  mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
  sram (rw) : ORIGIN = 0x0f000000, LENGTH = 8K
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
}

SECTIONS {
  /* _pmem_start and _entry_offset are defined in LDFLAGS */
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
  /* .data : AT(ADDR(.rodata) + SIZEOF(.rodata)){
    *(.data)
  } > sram */
  /* _edata = .; */
  /* _data = .; */
  .bss : {
	  _bss_start = ALIGN(0x0008);
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    _bss_end = .;
  } > sram
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  /* _heap_start = _sram_start;
  _heap_end = _sram_start + 0x1000; */
  _stack_pointer = _sram_start + _stack_offt;
  . = _stack_pointer;
  /* 堆区分配在 PSRAM(0x80000000, 可缓存 4MB)。阶段A: 4KB 验收(mem-test);
   * 后续阶段扩到完整 4MB(microbench/RT-Thread)。 */
  _heap_start = 0x80000000;
  _heap_end = 0x80001000;   /* 4KB */
  end = .;
  _end = .;
}
