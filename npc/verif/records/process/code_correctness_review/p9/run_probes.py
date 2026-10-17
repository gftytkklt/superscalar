#!/usr/bin/env python3
"""Bounded host seam probes using production functions; not full RV64/GUI tests."""
from pathlib import Path
import subprocess,tempfile,json,hashlib,argparse,shutil
P=Path(__file__).resolve().parent;R=P.parents[5]
a=argparse.ArgumentParser();a.add_argument('--output',type=Path,required=True);args=a.parse_args();O=args.output.resolve();O.mkdir(parents=True,exist_ok=False);W=Path(tempfile.mkdtemp(prefix='ccr-p9-probes-'))
report={'commands':[],'production_sources':{},'scope':'Host LP64, production ref+trap and libam routines; audio original AM and NEMU drivers joined with synchronous MMIO shim and deterministic SDL failures. No real audio/thread/guest claim.'}
inputs=['nemu/src/cpu/difftest/ref.c','nemu/src/isa/riscv32/system/intr.c','navy-apps/libs/libam/src/ioe.c','nemu/src/device/audio.c','abstract-machine/am/src/platform/nemu/ioe/audio.c','nemu/include/generated/autoconf.h']
for s in inputs:report['production_sources'][s]=hashlib.sha256((R/s).read_bytes()).hexdigest()
def run(label,cmd):
 q=subprocess.run([str(c) for c in cmd],cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30);(O/(label+'.log')).write_text(q.stdout);report['commands'].append({'label':label,'argv':[str(c) for c in cmd],'cwd':str(R),'returncode':q.returncode,'log':label+'.log'});(O/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0
common=['/usr/bin/gcc','-O2','-g','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-I'+str(R)]
nemu=['-D__GUEST_ISA__=riscv64','-Inemu/include','-Inemu/src/isa/riscv32/include']
am=['-DARCH_H="arch/riscv.h"','-Iabstract-machine/am/include','-Inavy-apps/libs/libndl/include']
run('ref-build',common+nemu+[P/'probe-ref.c',R/inputs[0],R/inputs[1],'-o',W/'ref']);run('ref-run',[W/'ref'])
run('uptime-build',common+am+[P/'probe-uptime.c',R/inputs[2],'-o',W/'uptime']);run('uptime-run',[W/'uptime'])
run('audio-build',common+nemu+am+['-I'+str(P/'host-include'),P/'probe-audio.c','-o',W/'audio']);run('audio-run',[W/'audio'])
report['binaries']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in W.iterdir() if p.is_file()};(O/'results.json').write_text(json.dumps(report,indent=2)+'\n')
