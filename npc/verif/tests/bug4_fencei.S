# Test fence.i behaviour in the MMIO-bypassed cache design.
# icachectrl FENCEI state waits on I_dcache_clean; dcachectrl must sweep its
# (empty) dirty_table and raise clean. Watch whether the core ever completes
# the fence.i and reaches the trailing ebreak.
	.section .text
	.globl _start
_start:
	li   t0, 0x0f000000
	li   t1, 0x42
	sb   t1, 0(t0)         # a store so dcache has something to do
	fence.i
	li   t2, 0x4c
	sb   t2, 4(t0)
	ebreak