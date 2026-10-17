#!/usr/bin/env python3
"""Reuse a verified isolated build; mutate only new input copies, bounded guest runs."""
from pathlib import Path
import argparse,json,tempfile,subprocess,hashlib,os
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=json.loads((a.build/'results.json').read_text());W=Path(r['work']);O=a.output.resolve();O.mkdir(parents=True,exist_ok=False)
for f,v in r['artifacts'].items():assert hashlib.sha256((W/f).read_bytes()).hexdigest()==v['sha256']
report={'base_evidence':str(a.build),'artifacts':r['artifacts'],'cases':[]};image=(W/'navy-runtime/build/ramdisk.img').read_bytes()
for name,mode in [('loader_bad_magic','legacy'),('disk_absent','legacy'),('mtimer_mode','mtimer')]:
 T=Path(tempfile.mkdtemp(prefix='ccr-p9-'+name+'-'));(T/'build').mkdir();data=image
 if name=='loader_bad_magic':data=b'BAD!'+data[4:]
 if name!='disk_absent':(T/'build/ramdisk.img').write_bytes(data)
 env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',NAVY_HOME=str(T));cmd=[str(W/'nemu-current'),'-b','--timer-source='+mode,str(W/'kernel.bin')]
 try:
  q=subprocess.run(cmd,cwd=W,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20);rc=q.returncode;out=q.stdout
 except subprocess.TimeoutExpired as e:rc='TIMEOUT';out=(e.stdout or b'').decode(errors='replace')
 (O/(name+'.log')).write_text(out)
 report['cases'].append({'name':name,'command':cmd,'cwd':str(W),'env':{k:env[k] for k in ['NAVY_HOME','SDL_VIDEODRIVER','SDL_AUDIODRIVER']},'returncode':rc,'timeout':20,'input_sha256':hashlib.sha256(data).hexdigest() if name!='disk_absent' else None,'good_trap':'HIT GOOD TRAP' in out,'bad_trap':'HIT BAD TRAP' in out,'user_started':'P9_USER_START' in out,'exit_reloaded':'P9_EXIT_RELOADED_NTERM' in out,'log':name+'.log'});print(name,rc,flush=True)
 (O/'results.json').write_text(json.dumps(report,indent=2)+'\n')
