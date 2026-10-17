#!/usr/bin/env python3
"""Confirm initial default-dialect probes also compile with repository GNU11/Werror flags."""
import pathlib,json,subprocess,hashlib
P=pathlib.Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=pathlib.Path);args=parser.parse_args()
if args.evidence:P=args.evidence.resolve()
if (P/'gnu11-results.json').exists():raise SystemExit('Refusing to overwrite GNU11 evidence')
r=json.loads((P/'probe-results.json').read_text());w=pathlib.Path(r['workdir']);out=[]
for cmd in r['commands']:
 a=cmd['argv']
 if a[0]!='/usr/bin/riscv64-linux-gnu-gcc' or '-c' not in a or not any(x.endswith('.c') for x in a):continue
 b=a[:];old=b[b.index('-o')+1];new=old+'.gnu11.o';b[b.index('-o')+1]=new
 b[1:1]=['-std=gnu11','-static','-Wall','-Werror']
 p=subprocess.run(b,cwd=w,text=True,capture_output=True,timeout=30)
 out.append({'argv':b,'cwd':str(w),'exit_code':p.returncode,'output':p.stdout+p.stderr,'same_object_bytes':p.returncode==0 and (w/old).read_bytes()==(w/new).read_bytes(),'sha256':hashlib.sha256((w/new).read_bytes()).hexdigest() if p.returncode==0 else None})
 assert p.returncode==0
(P/'gnu11-results.json').write_text(json.dumps({'date':'2026-10-17','commands':out},indent=2)+'\n')
print(len(out),'GNU11 compiles; object-byte equality',all(x['same_object_bytes'] for x in out))
