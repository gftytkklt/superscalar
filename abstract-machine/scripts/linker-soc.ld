ENTRY(_start)
PHDRS { text PT_LOAD; data PT_LOAD; }

MEMORY {
  mrom : ORIGIN = 0x20000000, LENGTH = 4K
  sram : ORIGIN = 0x0f000000, LENGTH = 8K
}

SECTIONS {
  /* _pmem_start and _entry_offset are defined in LDFLAGS */
  . = _pmem_start + _entry_offset;
  .text : {
    *(entry)
    *(.text*)
  } > mrom AT> mrom : text
  etext = .;
  _etext = .;
  .rodata : {
    *(.rodata*)
  } > mrom AT> mrom
  .data : {
    *(.data)
  } > mrom AT> sram : data
  edata = .;
  _data = .;
  .bss : {
	_bss_start = .;
    *(.bss*)
    *(.sbss*)
    *(.scommon)
  } > sram
  /* _heap_start = _sram_start; */
  /* _heap_end = _sram_start + 0x1000; */
  _heap_start = ALIGN(0x0008);
  _heap_end = _heap_start;
  _stack_pointer = _sram_start + _stack_offt;
  . = _stack_pointer;
  end = .;
  _end = .;
}
