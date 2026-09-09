# S3 mem-test: 程序本体在 SRAM 运行(由 bootloader 从 flash 搬运), 测试 PSRAM 访存。
# 讲义语义: 依次 8/16/32/64 位写"地址相关"模式到 PSRAM [0x80000000, +N), 再读回校验。
# 错误计数写 SRAM 0x0f000000(与 tb dump 区一致), 然后 ebreak。
# 程序在 SRAM(不可缓存取指); 访存目标 PSRAM(可缓存区, dcache/axiburst 通路)。
.section .text
.globl _start
.type _start, @function
_start:
  li   s0, 0x80000000        # PSRAM base
  li   s1, N_BYTES           # 测试区字节数(宏)
  li   s9, 0                 # err 计数
  li   s11, 0x12345678       # 地址异或常量

  # ================= 64 位轮 =================
  li   s2, 0                 # i
w64:
  bgeu s2, s1, r64
  add  t0, s0, s2
  xor  t1, t0, s11           # data = addr ^ const
  sd   t1, 0(t0)             # 64 位写
  addi s2, s2, 8
  j    w64
r64:
  li   s2, 0
r64l:
  bgeu s2, s1, w32
  add  t0, s0, s2
  xor  t1, t0, s11
  ld   t2, 0(t0)
  bne  t2, t1, e64
  addi s2, s2, 8
  j    r64l
e64:
  addi s9, s9, 1
  addi s2, s2, 8
  j    r64l

  # ================= 32 位轮 =================
w32:
  li   s2, 0
w32l:
  bgeu s2, s1, r32
  add  t0, s0, s2
  xor  t1, t0, s11
  sw   t1, 0(t0)
  addi s2, s2, 4
  j    w32l
r32:
  li   s2, 0
r32l:
  bgeu s2, s1, w16
  add  t0, s0, s2
  xor  t1, t0, s11
  lw   t2, 0(t0)
  xor  t3, t2, t1
  slli t3, t3, 32
  srli t3, t3, 32          # 只比低 32 位
  bnez t3, e32
  addi s2, s2, 4
  j    r32l
e32:
  addi s9, s9, 1
  addi s2, s2, 4
  j    r32l

  # ================= 16 位轮 =================
w16:
  li   s2, 0
w16l:
  bgeu s2, s1, r16
  add  t0, s0, s2
  xor  t1, t0, s11
  sh   t1, 0(t0)
  addi s2, s2, 2
  j    w16l
r16:
  li   s2, 0
r16l:
  bgeu s2, s1, w8
  add  t0, s0, s2
  xor  t1, t0, s11
  lhu  t2, 0(t0)
  xor  t3, t2, t1
  slli t3, t3, 48
  srli t3, t3, 48          # 只比低 16 位
  bnez t3, e16
  addi s2, s2, 2
  j    r16l
e16:
  addi s9, s9, 1
  addi s2, s2, 2
  j    r16l

  # ================= 8 位轮 =================
w8:
  li   s2, 0
w8l:
  bgeu s2, s1, r8
  add  t0, s0, s2
  xor  t1, t0, s11
  sb   t1, 0(t0)
  addi s2, s2, 1
  j    w8l
r8:
  li   s2, 0
r8l:
  bgeu s2, s1, done
  add  t0, s0, s2
  xor  t1, t0, s11
  lbu  t2, 0(t0)
  xor  t3, t2, t1
  andi t3, t3, 0xff         # 只比低 8 位
  bnez t3, e8
  addi s2, s2, 1
  j    r8l
e8:
  addi s9, s9, 1
  addi s2, s2, 1
  j    r8l

done:
  li   t0, 0x0f000000         # SRAM dump 区(低 4KB 空闲)
  sd   s9, 0(t0)
  ebreak
  .size _start, .-_start