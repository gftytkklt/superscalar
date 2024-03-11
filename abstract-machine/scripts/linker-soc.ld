ENTRY(_start)
/* PHDRS { text PT_LOAD; data PT_LOAD; } */

MEMORY {
  mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
  sram (rw) : ORIGIN = 0x0f000000, LENGTH = 8K
}

SECTIONS {
  /* _pmem_start and _entry_offset are defined in LDFLAGS */
  . = ORIGIN(mrom);
  .text : {
    *(entry)
    *(.text*)
  } > mrom AT> mrom
  etext = .;
  _etext = .;
  .rodata : {
    *(.rodata*)
  } > mrom
  .data : {
    _sdata = .;
    *(.data*)
    *(.sdata*)
    _edata = .;
  } > sram AT> mrom
  /* .data : AT(ADDR(.rodata) + SIZEOF(.rodata)){
    *(.data)
  } > sram */
  /* _edata = .; */
  _data = .;
  .bss : {
	_bss_start = .;
    *(.bss*)
    *(.sbss*)
    *(.scommon)
  } > sram
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  /* _heap_start = _sram_start;
  _heap_end = _sram_start + 0x1000; */
  _heap_start = ALIGN(0x0008);
  _heap_end = _heap_start;
  _stack_pointer = _sram_start + _stack_offt;
  . = _stack_pointer;
  end = .;
  _end = .;
}
