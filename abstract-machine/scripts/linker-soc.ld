ENTRY(_start)
/* PHDRS { text PT_LOAD; data PT_LOAD; } */

MEMORY {
  mrom (rx) : ORIGIN = 0x20000000, LENGTH = 4K
  sram (rw) : ORIGIN = 0x0f000000, LENGTH = MIN(8K, _stack_offt)
  psram (rw) : ORIGIN = 0x80000000, LENGTH = 4M
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
  .bss : ALIGN(0x8) {
	  _bss_start = .;
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
  /* 堆区分配在 PSRAM(0x80000000, 可缓存 4MB)。大小由 LDFLAGS --defsym=_heap_size 指定
   * （npc.mk 的 HEAP_SIZE，默认 32KB；microbench 等大堆程序传 HEAP_SIZE=0x400000）。
   * 不要写死整个 4MB，否则 mem-test(用 _heap_start~_heap_end) 会扫描 4MB 极慢。 */
  _heap_start = ORIGIN(psram);
  /* Check the size before addition so a wrapped end cannot pass the bound. */
  ASSERT(_heap_start <= ORIGIN(psram) + LENGTH(psram), "heap start exceeds psram")
  ASSERT(_heap_size <= ORIGIN(psram) + LENGTH(psram) - _heap_start, "heap size exceeds psram")
  _heap_end = _heap_start + _heap_size;
  end = .;
  _end = .;
}

/* SRAM is physically 8 KiB. Bound static placement by the existing initial SP;
 * this reserves no fixed stack budget and does not detect runtime stack growth. */
ASSERT(_sram_start == ORIGIN(sram), "stack SRAM base does not match SRAM origin")
ASSERT(_stack_offt > 0 && _stack_offt <= 8K, "initial stack pointer is outside SRAM")
ASSERT((_stack_pointer & 0xf) == 0, "initial stack pointer must be 16-byte aligned")
