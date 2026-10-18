ENTRY(_start)

MEMORY {
  sram (rwx) : ORIGIN = 0x0f000000, LENGTH = 8K
  psram (rw) : ORIGIN = 0x80000000, LENGTH = 4M
  flash (rx) : ORIGIN = 0x30000000, LENGTH = 16M
}

SECTIONS {
  /* bootloader：VMA=LMA=flash，NPC 复位后从 flash 取指执行。
   * 它把下面各段的 LMA(flash) 内容搬到 VMA(sram)，再跳转 SRAM 执行。 */
  . = ORIGIN(flash);
  .bootloader : {
    *(entry)
    *(.bootloader)
    *(.text.bootloader)
    *(.text.*.bootloader)
    *(.rodata.bootloader)
    *(.data.bootloader)
  } > flash

  /* 主程序：VMA=SRAM，LMA=flash（-O binary 按 LMA 输出，故 .bin 是连续 flash 镜像）。 */
  . = ORIGIN(sram);
  .text : ALIGN(0x8) {
    *(.text*)
  } > sram AT> flash
  _text_vma = ADDR(.text);
  _text_lma = LOADADDR(.text);
  _text_end = ADDR(.text) + SIZEOF(.text);
  etext = .;
  _etext = .;
  .rodata : ALIGN(0x8) {
    *(.rodata*)
    *(.srodata*)
  } > sram AT> flash
  _rodata_vma = ADDR(.rodata);
  _rodata_lma = LOADADDR(.rodata);
  _rodata_end = ADDR(.rodata) + SIZEOF(.rodata);
  .data : ALIGN(0x8) {
    _sdata = .;
    *(.data*)
    *(.sdata*)
    _edata = .;
  } > sram AT> flash
  _sidata = LOADADDR(.data);
  _sidata_end = LOADADDR(.data) + SIZEOF(.data);
  .bss : ALIGN(0x8) {
    _bss_start = .;
    *(.bss*)
    *(.sbss*)
    *(.scommon)
    _bss_end = .;
  } > sram

  /* 栈：SRAM 内（bootloader 用绝对地址 la sp, _stack_pointer 设定）。 */
  _stack_pointer = _sram_start + _stack_offt;

  /* 堆区：PSRAM（可缓存 4MB），大小由 --defsym=_heap_size 指定。 */
  . = _stack_pointer;
  _heap_start = ORIGIN(psram);
  /* Check the size before addition so a wrapped end cannot pass the bound. */
  ASSERT(_heap_start <= ORIGIN(psram) + LENGTH(psram), "heap start exceeds psram")
  ASSERT(_heap_size <= ORIGIN(psram) + LENGTH(psram) - _heap_start, "heap size exceeds psram")
  _heap_end = _heap_start + _heap_size;
  end = .;
  _end = .;
}