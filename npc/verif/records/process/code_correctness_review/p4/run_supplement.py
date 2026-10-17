#!/usr/bin/env python3
"""Link alignment probe, using existing P4 isolated source copy; no guest run."""
import json,pathlib,subprocess,hashlib
P=pathlib.Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=pathlib.Path);args=parser.parse_args()
if args.evidence:P=args.evidence.resolve()
if (P/'supplement-results.json').exists():raise SystemExit('Refusing to overwrite supplementary evidence')
r=json.loads((P/'probe-results.json').read_text());w=pathlib.Path(r['workdir']);commands=[]
fixture=(P/'fixture.S').read_text().replace(' la a1, test_data',' la a1, test_data\n la a2, aligned_rodata')+'''\n.section .rodata,"a"
.balign 64
.global aligned_rodata
aligned_rodata: .quad 0x1122334455667788
'''
(w/'aligned.S').write_text(fixture);(P/'aligned.S').write_text(fixture)
def run(args,name):
 p=subprocess.run(args,cwd=w,text=True,capture_output=True,timeout=30);(P/(name+'.log')).write_text(p.stdout+p.stderr)
 commands.append({'argv':args,'cwd':str(w),'exit_code':p.returncode,'log':name+'.log'});assert p.returncode==0;return p.stdout
run(['/usr/bin/riscv64-linux-gnu-gcc','-march=rv64g','-mcmodel=medany','-fno-pic','-c','aligned.S','-o','aligned.o'],'aligned-compile')
for mode in ['sram','psram','psram-ssbl','sdram','sdram-rt']:
 cmd=next(c['argv'] for c in r['commands'] if c['name']==mode+'-link')[:];cmd=[x.replace('fixture.o','aligned.o').replace(mode+'.elf',mode+'-aligned.elf') for x in cmd]
 run(cmd,mode+'-aligned-link')
 run(['/usr/bin/riscv64-linux-gnu-objdump','-h',mode+'-aligned.elf'],mode+'-aligned-sections')
 run(['/usr/bin/riscv64-linux-gnu-readelf','-sW',mode+'-aligned.elf'],mode+'-aligned-symbols')
(P/'supplement-results.json').write_text(json.dumps({'date':'2026-10-17','workdir':str(w),'commands':commands,'fixture_sha256':hashlib.sha256(fixture.encode()).hexdigest(),'limits':'Link observation, not executing loaders.'},indent=2)+'\n')
print('recorded',len(commands),'commands')
