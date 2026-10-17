#!/usr/bin/env python3
from pathlib import Path
import json,gzip,hashlib
H=Path(__file__).resolve().parent;B=H.parent;R=H.parents[5]
base=json.loads(gzip.decompress((H/'findings.json.before.gz').read_bytes()));out=[]
def add(num,title,status,severity,loc,fn,basis,actual,impact,validation,fix,regression,limit,evidence):
 out.append(dict(id=f'CCR-F{num:04}',phase='CCR-P9',title=title,status=status,severity=severity,locations=[dict(path=p,lines=lines,sha256=hashlib.sha256((R/p).read_bytes()).hexdigest()) for p,lines in loc],functions=fn,expected_contract_and_basis=basis,actual_and_root_cause=actual,reachability_and_impact=impact,validation=validation,minimal_fix=fix,recommended_regression=regression,evidence=evidence,conclusion=status,upstream_downstream_contracts='P9 L01–L09逐链表；项目公开接口/实际双方调用，未扩充完整POSIX/SDL支持承诺',existing_test_coverage='旧P2–P8未登记此根因；P9本次探针及静态定位见validation',missing_evidence=limit,unconfirmed_assumptions_and_limits=limit,severity_rationale='Medium：条件成立时状态/时序或设备工作不正确；Low：当前影响局限于诊断参数，未证实执行结果错误',evidence_origin='本次当前源静态配对与明确标注的host seam probe；不冒充NPC/GUI实际运行'))
add(116,'REF显式中断注入丢弃trap目标PC','Confirmed','Medium',[
 ('nemu/src/cpu/difftest/ref.c',[95,97]),('nemu/src/isa/riscv32/system/intr.c',[50,58,61,62]),('nemu/src/cpu/cpu-exec.c',[100]),('npc/csrc/util/difftest.cpp',[34,35])],
 'difftest_raise_intr → isa_raise_intr/riscv_raise_exception',
 'C-N11/C-N03、L08：显式注入应使下一次exec从trap入口执行；正常cpu-exec消费isa_raise_intr返回值，Spike同名入口take_trap_public也转入handler。',
 'REF只调用isa_raise_intr(NO,cpu.pc)，该函数修改CSR/priv但以返回值提供新PC；REF没有赋回cpu.pc。',
 '调用导出的difftest_raise_intr后CSR是陷入后状态、PC仍为被中断指令；下一次exec走错误位置。NPC当前仅dlsym而未调用该导出，故这是被保留接口的潜在路径，不声称当前NPC定向回归失败。',
 'probes2/ref-run.log：PC=80000080而目标80000100；mepc=80000080、mcause=8000000000000007。原ref.c和intr.c，host LP64；探针退出0表示观察到缺陷。',
 '将isa_raise_intr返回值写回cpu.pc；校对delegation/vectored入口及DUT同步契约。',
 'M/S委托、direct/vectored、不同cause、注入后首条handler指令；不只比较CSR。',
 '没有本轮NPC IRQ注入或完整REF动态加载；当前NPC调用者不自动用此入口。', ['p9/probes2/ref-run.log','p9/probes2/results.json','p9/probe-ref.c','p9/L08.md'])
add(117,'libam微秒uptime继承NDL的32位毫秒回绕','Confirmed','Low',[
 ('navy-apps/libs/libam/src/ioe.c',[37,39]),('navy-apps/libs/libndl/NDL.c',[18,20]),('abstract-machine/am/include/amdev.h',[15])],
 'libam ioe_read(AM_TIMER_UPTIME) → NDL_GetTicks',
 'C-A02/C-U04/C-U05、L04：AM_TIMER_UPTIME_T.us为64位累计微秒；适配不能把NDL明确的32位毫秒周期冒充64位累计值。',
 '先经uint32_t NDL_GetTicks截断，再转uint64_t乘1000；没有跨回绕累计状态。',
 '经过2^32 ms（约49.7天）时AM值从4294967295000us降为0。直接SDL的32位ticks模减语义不受此新问题判定；仅libam桥接。',
 'probes2/uptime-run.log：给NDL受控输入ffffffff→0，原libam返回4294967295000→0。',
 '直接从64位gettimeofday转换，或维护可靠的回绕扩展状态并定义初始化/调用间隔。',
 '边界前后与多次调用、重复初始化；明确不把SDL合法32位回绕判成错误。',
 '未连续运行49.7天；host输入注入复现转换，实际guest/libam链另受F0086/F0113限制。', ['p9/probes2/uptime-run.log','p9/probes2/results.json','p9/probe-uptime.c','p9/L04.md'])
add(118,'NEMU音频打开失败未反馈且控制状态继续被接受','Robustness','Medium',[
 ('nemu/src/device/audio.c',[71,81,83,84,88,90]),('abstract-machine/am/src/platform/nemu/ioe/audio.c',[23,26]),('nanos-lite/src/device.c',[105,108,110,113,115]),('navy-apps/libs/libminiSDL/src/audio.c',[42,45,49])],
 'SDL_audio_init → AM_AUDIO_CTRL → audio_ctrl_write → SDL_OpenAudio',
 'C-N09/C-A07/C-O06/C-U06、L06：后端开启失败不得作为已建立播放链的成功；频率/声道/缓冲配置与实际设备应一致。',
 'NEMU忽略SDL_OpenAudio返回值并无条件PauseAudio(0)，既不恢复寄存器也不暴露失败。AM控制无状态返回，nanos返回len，miniSDL返回0；重开无关闭也会进入失败分支。',
 '宿主无法开设备或第二次开音频失败时，上层继续提交PCM。首次失败后无消费会填满ring；重开失败则硬件旧配置可能与新寄存器不同。与F0010触发offset、F0043 count竞争、F0094 callback关闭残留为不同根因。',
 'probes2/audio-run.log：实际AM init写16不打开，ctrl写8首次打开1次；第二次注入OpenAudio=-1仍Pause第2次、接受4字节/count=4、新freq=22050。使用实际AM/NEMU源码与同步MMIO、SDL失败桩。',
 '检查后端初始化结果，原子提交配置并提供可查询失败状态/错误传播；定义close/reopen行为。',
 '首次失败、重开失败、格式变化、失败后写入/查询/关闭/重试；消费者停滞有界处理。',
 '未运行真实声卡失败、未证明实际声音异常；桩不模拟线程竞争，后续填满/等待结论为静态推导。首次正常打开序列已证明会触发，不能套用F0010称首次必败。', ['p9/probes2/audio-run.log','p9/probes2/results.json','p9/probe-audio.c','p9/L06.md'])
add(119,'NPC对NEMU REF初始化函数的参数签名不一致','Confirmed','Low',[
 ('npc/csrc/util/difftest.cpp',[36,41]),('nemu/src/cpu/difftest/ref.c',[104,105])],
 'init_difftest dlsym → difftest_init(int port)',
 'C-N11/C-X02、L08：动态符号两端必须使用一致的函数参数签名；导出明确接收int port。',
 'NPC强制转换为void(*)(void)，随后无参数调用；NEMU导出void(int)并读取port打印。',
 'CONFIG_DIFFTEST下每次初始化可达，port没有调用方定义的输入。当前被调函数只用于日志，故Low；当前npc配置DIFF=0，不声称正在运行的比较出错。',
 '双方声明、dlsym cast、call和参数使用逐行静态配对；无动态UB或特定随机port值断言。',
 '共享带版本的函数原型；调用方以void(*)(int)解析并传明确port。',
 '类型一致性编译检查及实际dlopen参数哨兵；同时验证memcpy/regcpy双方签名。',
 '仅此不推定PC/GPR对拍失败；memcpy uint64/paddr32是独立的地址域/类型限制，L08单列并关联F0002/F0014。', ['p9/endpoints.json','p9/L08.md'])
(H/'findings.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(B/'findings.json').write_text(json.dumps(base+out,ensure_ascii=False,indent=2)+'\n')
p=B/'FINDINGS.md';s=p.read_text();start=s.index('当前状态（');end=s.index('\n\n',start);s=s[:start]+'当前状态（2026-10-17）：P9新增4项F0116–F0119（3 Confirmed/1 Robustness；Medium2/Low2），累计119项（86 Confirmed/28 Robustness/5 CQ；High13/Medium79/Low27），均未修。[P9](P9.md) / [跨层证据](p9/README.md)。P8 Partial已按用户豁免提交5f88749；两个缺源仍保留未审。下方旧阶段正文保留历史截面。'+s[end:]
s+='\n\n<a id="ccr-p9-findings-20261017"></a>\n## CCR-P9 新问题及旧结论限定\n\nF0010只证明单写init的实现差异；当前AM实际顺序为init=1后freq/channels/samples，最后写offset8会触发NEMU开启。不得据F0010推导当前首次音频打开必败；本轮原函数桥接日志已限定。旧115问题对象及历史证据不改写。\n'
labels={'functions':'路径','expected_contract_and_basis':'契约','actual_and_root_cause':'根因','reachability_and_impact':'触发与影响','validation':'本次验证','minimal_fix':'修复建议（未实施）','recommended_regression':'建议回归','unconfirmed_assumptions_and_limits':'限制'}
for x in out:
 s+=f'\n<a id="{x["id"].lower()}"></a>\n### {x["id"]} — {x["title"]}\n\n- 状态/等级：{x["status"]} / {x["severity"]}\n'
 s+='- 位置：'+'；'.join('`'+v['path']+':'+','.join(map(str,v['lines']))+'`' for v in x['locations'])+'；逐位置SHA见p9/findings.json。\n'
 for k,v in labels.items():s+=f'- {v}：{x[k]}\n'
 s+='- 证据：'+', '.join(f'[{e}]({e})' for e in x['evidence'])+'\n'
p.write_text(s)
