#!/usr/bin/env python3
"""Read-only P9 identity, generated extent and RV64 ABI verification. Outputs here."""
from pathlib import Path
import json,gzip,hashlib,os,re,collections,subprocess,tempfile
H=Path(__file__).resolve().parent;B=H.parent;R=H.parents[5]
def sha(b):return hashlib.sha256(b).hexdigest()
def write(n,x):(H/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
rows=[json.loads(s) for s in gzip.decompress((H/'coverage.jsonl.before.gz').read_bytes()).decode().splitlines()]
ints=json.loads(gzip.decompress((H/'interfaces_current.json.before.gz').read_bytes()))
selected=[r for r in rows if 'CCR-P9' in r.get('effective_phase_responsibilities',[])]
ends={e['path'] for l in ints['interfaces'] for e in l['endpoints']}
extras=['nemu/src/cpu/difftest/dut.c','nemu/src/isa/riscv32/difftest/dut.c','nemu/tools/spike-diff/difftest.cc','nemu/tools/spike-diff/Makefile','abstract-machine/scripts/isa/riscv.mk','navy-apps/scripts/riscv/common.mk','nanos-lite/include/common.h','abstract-machine/am/include/am.h','abstract-machine/am/src/platform/dummy/vme.c','abstract-machine/am/src/riscv/npc/ioe.c','abstract-machine/am/src/platform/nemu/include/nemu.h','abstract-machine/am/src/platform/nemu/ioe/ioe.c','abstract-machine/am/src/platform/nemu/ioe/disk.c','nemu/src/device/disk.c','nemu/include/common.h','nemu/src/device/io/map.c','nemu/src/device/io/mmio.c','npc/csrc/include/common.h','npc/csrc/util/memory.cpp','navy-apps/libs/libc/src/reent/execr.c','navy-apps/libs/libc/src/stdlib/exit.c','navy-apps/libs/libc/src/misc/init.c','navy-apps/libs/libc/src/reent/impure.c','navy-apps/libs/libc/src/reent/lseekr.c','navy-apps/libs/libc/src/syscalls/sysopen.c','navy-apps/libs/libc/src/reent/openr.c','navy-apps/libs/libminiSDL/src/general.c','navy-apps/libs/libSDL_mixer/src/mixer.c','navy-apps/libs/libc/include/elf.h']
paths=ends|set(extras)|{r['path'] for r in selected};index={r['path']:r for r in rows if r['row_kind']=='file'};checks=[]
for s in sorted(paths):
 p=R/s;r=index.get(s,{});h=sha(os.readlink(p).encode()) if p.is_symlink() else sha(p.read_bytes()) if p.is_file() else None
 checks.append({'path':s,'row_id':r.get('row_id'),'endpoint':s in ends,'direct_support':s in extras,'p1_sha256':r.get('source_sha256'),'current_sha256':h,'matches':h==r.get('source_sha256') if r else None,'link_text':os.readlink(p) if p.is_symlink() else None,'resolved_sha256':sha(p.read_bytes()) if p.is_file() else None,'semantics':'symlink-text' if p.is_symlink() else 'bytes'})
write('source-check.json',{'checks':checks,'count':len(checks),'mismatch':[x for x in checks if x['matches'] is False],'unindexed':[x['path'] for x in checks if x['row_id'] is None]})
write('endpoints.json',{'original_endpoint_occurrences':sum(len(l['endpoints']) for l in ints['interfaces']),'original_unique':len(ends),'checks':[x for x in checks if x['endpoint'] or x['direct_support']]})
write('responsibility-summary.json',{'rows':len(selected),'by_module':dict(collections.Counter(r['module_id'] for r in selected)),'by_kind':dict(collections.Counter(r['row_kind'] for r in selected))})
# Recheck every generated file-table extent; distinct from rebuilding unknown historical binaries.
table=(R/'navy-apps/build/ramdisk.h').read_text();img=R/'navy-apps/build/ramdisk.img';entries=[];end=0
with img.open('rb') as f:
 for name,size,off in re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+)',table):
  size=int(size);off=int(off);f.seek(off);data=f.read(size);target=R/'navy-apps/fsimg'/name.lstrip('/');b=target.read_bytes();d={'name':name,'offset':off,'size':size,'contiguous':off==end,'complete':len(data)==size,'image_sha256':sha(data),'fsimg_sha256':sha(b),'matches':data==b}
  if data[:4]==b'\x7fELF':d['elf_class']=data[4];d['machine']=int.from_bytes(data[18:20],'little');d['entry']=hex(int.from_bytes(data[24:32],'little'))
  entries.append(d);end=off+size
write('fsimg-match.json',{'image_size':img.stat().st_size,'image_sha256':sha(img.read_bytes()),'count':len(entries),'padding':img.stat().st_size-end,'entries':entries})
# Key symbols are values only because all three enum lists begin with NONE=0 and no explicit gaps.
keys=[]
for path,macro,letter in [('abstract-machine/am/include/amdev.h','AM_KEYS','_'),('navy-apps/libs/libminiSDL/include/sdl-event.h','_KEYS','_'),('nemu/src/device/keyboard.c','NEMU_KEYS','f')]:
 s=(R/path).read_text().split('#define '+macro+'(',1)[1].split('\n\n',1)[0];keys.append({'path':path,'keys':re.findall(r'\b'+letter+r'\((\w+)\)',s)})
write('key-match.json',{'lists':keys,'equal':keys[0]['keys']==keys[1]['keys']==keys[2]['keys'],'non_none_count':len(keys[0]['keys'])})
if (H/'layout-result.json').exists():
 print('source checks',len(checks),'mismatches',sum(x['matches'] is False for x in checks),'layout evidence reused');raise SystemExit(0)
W=Path(tempfile.mkdtemp(prefix='ccr-p9-layout-'));cmd=['/usr/bin/riscv64-linux-gnu-gcc','-std=gnu11','-march=rv64g','-DARCH_H="arch/riscv.h"','-D__NAVY__','-Iabstract-machine/am/include','-Inavy-apps/libs/libc/include','-Inavy-apps/libs/libminiSDL/include','-c',str(H/'layout.c'),'-o',str(W/'layout.o')];q=subprocess.run(cmd,cwd=R,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(H/'layout.log').write_text(q.stdout);write('layout-result.json',{'command':cmd,'cwd':str(R),'returncode':q.returncode,'source_sha256':sha((H/'layout.c').read_bytes()),'object_sha256':sha((W/'layout.o').read_bytes()) if q.returncode==0 else None})
print('source checks',len(checks),'mismatch',[(x['path'],x['matches']) for x in checks if x['matches'] is False]);print('fsimg',len(entries),'mismatches',sum(not x['matches'] for x in entries));print('keys',len(keys[0]['keys']),keys[0]['keys']==keys[1]['keys']==keys[2]['keys']);print('layout',q.returncode)
