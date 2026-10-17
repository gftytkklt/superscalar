#!/usr/bin/env python3
"""Verify current newlib build's low-call prototypes, no production edits."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[6];HERE=Path(__file__).resolve().parent
W=Path(tempfile.mkdtemp(prefix='ccr-p7-width-work-'));O=Path(tempfile.mkdtemp(prefix='ccr-p7-width-evidence-'));rs=[]
shutil.copytree(ROOT/'navy-apps/libs/libc/include',W/'include')
srcs=[]
for n in ['readr','writer','lseekr']:
 p=ROOT/'navy-apps/libs/libc/src/reent'/(n+'.c');q=W/p.name;q.write_text(re.sub(r'\berrno\b','p7_low_errno',p.read_text()));srcs.append(q)
def run(n,a):
 r=subprocess.run(list(map(str,a)),cwd=W,env=dict(os.environ,CCACHE_DISABLE='1'),capture_output=True,timeout=30);(O/(n+'.log')).write_bytes(r.stdout+r.stderr);rs.append(dict(name=n,argv=list(map(str,a)),cwd=str(W),exit=r.returncode,expected_exit=0,log=n+'.log'));return r.returncode
if run('host-width-build',['/usr/bin/gcc','-O2','-D__riscv','-I'+str(W/'include'),*srcs,HERE/'width-probe.c','-o',W/'probe'])==0:run('host-width',[W/'probe'])
for n in ['readr','writer','lseekr']:
 run('rv-width-'+n,['/usr/bin/riscv64-linux-gnu-gcc','-O2','-march=rv64g','-mcmodel=medany','-fno-pic','-D__NAVY__','-I'+str(W/'include'),'-S',ROOT/'navy-apps/libs/libc/src/reent'/(n+'.c'),'-o',W/(n+'.s')]);shutil.copy2(W/(n+'.s'),O/(n+'.s'))
(O/'results.json').write_text(json.dumps(rs,indent=2)+'\n');(O/'manifest.json').write_text(json.dumps({'work':str(W),'transform':'host copies only rename low-layer errno; original RV64 units unchanged','outputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in W.iterdir() if p.is_file()}},indent=2)+'\n');print(O)
