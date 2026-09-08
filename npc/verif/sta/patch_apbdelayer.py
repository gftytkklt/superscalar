#!/usr/bin/env python3
# E1c：把 apb_delayer 拼接入 generated/ysyxSoCFull.v 的 AXI4ToAPB(axi42apb) 与
# APBFanout(apbxbar) 之间（讲义"APB Xbar 上游"，覆盖所有 APB 外设访问）。
#
# 连接关系（幂等，可重复执行；网表若重新生成，重跑本脚本即恢复）：
#   请求: _axi42apb_auto_out_*            → delayer.in_*   （原线直连，不动）
#         delayer.out_*                   → 新线 _apbdly_out_* → APBFanout.auto_in_*
#   响应: _apbxbar_auto_in_*（fanout 驱动）→ delayer.out_*  （原线直连，不动）
#         delayer.in_pready/pslverr/prdata→ 新线 _apbdly_in_* → AXI4ToAPB.auto_out_*
import sys, re

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'generated/ysyxSoCFull.v'
    src = open(path).read()
    if 'apb_delayer' in src:
        print('patch_apbdelayer: already patched, skip'); return

    # 1) 新线声明：挂在 _apbxbar_auto_in_prdata 声明之后
    decl_anchor = re.search(r'^  wire \[31:0\] _apbxbar_auto_in_prdata;.*$', src, re.M)
    assert decl_anchor, 'anchor (prdata decl) not found'
    decls = ('  wire        _apbdly_out_psel;  wire        _apbdly_out_penable;\n'
             '  wire        _apbdly_out_pwrite; wire [31:0] _apbdly_out_paddr;\n'
             '  wire [31:0] _apbdly_out_pwdata; wire [3:0]  _apbdly_out_pstrb;\n'
             '  wire [2:0]  _apbdly_out_pprot;\n'
             '  wire        _apbdly_in_pready;  wire        _apbdly_in_pslverr;\n'
             '  wire [31:0] _apbdly_in_prdata;  // E1c apb_delayer splice\n')
    src = src[:decl_anchor.end()] + '\n' + decls + src[decl_anchor.end():]

    # 2) 实例化：插在 APBFanout apbxbar 实例之前
    inst_anchor = re.search(r'^  APBFanout apbxbar \(', src, re.M)
    assert inst_anchor, 'anchor (APBFanout inst) not found'
    inst = ('  apb_delayer apb_dly (  // E1c: 延迟校准（in=桥侧, out=外设侧）\n'
            '    .clock(clock), .reset(reset),\n'
            '    .in_paddr(_axi42apb_auto_out_paddr), .in_psel(_axi42apb_auto_out_psel),\n'
            '    .in_penable(_axi42apb_auto_out_penable), .in_pwrite(_axi42apb_auto_out_pwrite),\n'
            '    .in_pwdata(_axi42apb_auto_out_pwdata), .in_pstrb(_axi42apb_auto_out_pstrb),\n'
            '    .in_pprot(3\'b000),\n'
            '    .in_pready(_apbdly_in_pready), .in_prdata(_apbdly_in_prdata),\n'
            '    .in_pslverr(_apbdly_in_pslverr),\n'
            '    .out_paddr(_apbdly_out_paddr), .out_psel(_apbdly_out_psel),\n'
            '    .out_penable(_apbdly_out_penable), .out_pwrite(_apbdly_out_pwrite),\n'
            '    .out_pwdata(_apbdly_out_pwdata), .out_pstrb(_apbdly_out_pstrb),\n'
            '    .out_pprot(_apbdly_out_pprot),\n'
            '    .out_pready(_apbxbar_auto_in_pready), .out_prdata(_apbxbar_auto_in_prdata),\n'
            '    .out_pslverr(_apbxbar_auto_in_pslverr)\n'
            '  );\n')
    src = src[:inst_anchor.start()] + inst + src[inst_anchor.start():]

    # 3) 改线：APBFanout 请求入口 ← delayer 输出
    for sig in ['psel', 'penable', 'pwrite', 'paddr', 'pwdata', 'pstrb']:
        src = re.sub(r'(\.auto_in_%s\s*)\(_axi42apb_auto_out_%s\)' % (sig, sig),
                     r'\1(_apbdly_out_%s)' % sig, src, count=1)
    # 4) 改线：AXI4ToAPB 响应入口 ← delayer 输出
    for sig in ['pready', 'pslverr', 'prdata']:
        src = re.sub(r'(\.auto_out_%s\s*)\(_apbxbar_auto_in_%s\)' % (sig, sig),
                     r'\1(_apbdly_in_%s)' % sig, src, count=1)

    open(path, 'w').write(src)
    n = len(re.findall(r'_apbdly_', src))
    print(f'patch_apbdelayer: patched {path} (_apbdly_ refs={n})')

if __name__ == '__main__':
    main()
