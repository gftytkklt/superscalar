# Test Bug2 (CSR RAW hazard) revisited.
# part A: csrw writes mepc; IMMEDIATELY following csrr must read the NEW value
#         (0x12345678) but the core forwards the stale decode-time value (0),
#         AND because CSRRS also writes back the stale value, it even clobbers
#         mepc back to 0. t1 captures the hazard read.
# part B: re-write mepc, let it commit through the pipeline, then read again.
#         t3 must equal 0x12345678 (control: proves the write path works when
#         there is no in-flight hazard).
	.section .text
	.globl _start
_start:
	li   t0, 0x0f000000
	li   a0, 0x12345678
	csrw mepc, a0          # (2)
	csrr t1, mepc          # (3) RAW hazard: correct 0x12345678, HW stale 0
	sd   t1, 0(t0)         # 0x0f000000  (bug)
	csrw mepc, a0          # repair clobber
	li   t2, 1
	add  t2, t2, t2
	add  t2, t2, t2
	add  t2, t2, t2
	add  t2, t2, t2
	add  t2, t2, t2
	csrr t3, mepc          # after commit -> 0x12345678
	sd   t3, 8(t0)         # 0x0f000008  (control)
	ebreak