#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,re,struct,subprocess,mmap
H=Path(__file__).resolve().parent;R=next(p for p in H.parents if (p/'AGENTS.md').exists());base=json.loads((H/'baseline.json').read_text());out=[]
for x in base['inputs']:
 p=R/x['path'];rec={**x,'size':p.stat().st_size,'pairing':'Unknown: historical binary to current source/config/flags is not proven'}
 if p.suffix in ['.o','.elf']:
  r=subprocess.run(['riscv64-linux-gnu-readelf','-h',str(p)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);rec['elf_header']=r.stdout;rec['exit']=r.returncode
 elif p.suffix=='.bin':rec['producer_consumer']='objcopy historical raw kernel image; not executed or paired to current sources'
 elif p.suffix=='.d':rec['dependencies']=p.read_text();rec['producer_consumer']='compiler dependency sidecar, historical target selection only'
 elif p.name=='files.h':rec['producer_consumer']='navy build/ramdisk.h symlink; fixed Finfo initializer consumed by fs.c'
 elif p.name=='syscall.h':rec['producer_consumer']='libos syscall enum symlink; exact shared syscall numbers'
 elif p.name=='ramdisk.img':rec['producer_consumer']='navy image symlink; NEMU disk host file / NPC .incbin'
 elif p.name.endswith('.txt') and '/build/' in str(p):
  t=p.read_text(errors='replace');rec['first_lines']=t.splitlines()[:12];rec['last_lines']=t.splitlines()[-8:];rec['producer_consumer']='historical disassembly/log; no run or PASS inherited'
 else:continue
 out.append(rec)
(H/'artifact-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
rows=[]
for line in (R/'nanos-lite/src/files.h').read_text().splitlines():
 m=re.match(r'\{"([^"]+)", (\d+), (\d+)\}',line)
 if m:rows.append({'name':m[1],'size':int(m[2]),'offset':int(m[3])})
image=R/'nanos-lite/build/ramdisk.img'
with image.open('rb') as f:
 mm=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
 for x in rows:
  data=mm[x['offset']:x['offset']+x['size']];x['sha256']=hashlib.sha256(data).hexdigest();x['within_image']=x['offset']+x['size']<=len(mm)
  if data[:4]==b'\x7fELF':
   x['elf_class']=data[4];x['machine']=struct.unpack_from('<H',data,18)[0]
   if data[4]==2:
    _,_,_,entry,phoff,_,_,_,entsz,num,*_=struct.unpack_from('<HHIQQQIHHHHHH',data,16);x['entry']=hex(entry);x['segments']=[]
    for i in range(num):
     typ,flags,off,va,pa,fs,ms,align=struct.unpack_from('<IIQQQQQQ',data,phoff+i*entsz)
     if typ==1:x['segments'].append({'vaddr':hex(va),'offset':off,'filesz':fs,'memsz':ms,'flags':flags,'align':align,'within_file':off+fs<=len(data),'range_ok':fs<=ms and va+ms<=0x7fff8000 and va>=0x40000000})
    x['shared_load_pages']=any((int(a['vaddr'],16)+a['memsz']+4095)//4096>int(b['vaddr'],16)//4096 for a,b in zip(x['segments'],x['segments'][1:]))
 mm.close()
res={'count':len(rows),'image_size':image.stat().st_size,'table_end':max(x['offset']+x['size'] for x in rows),'unique_names':len({x['name'] for x in rows}),'contiguous':all(a['offset']+a['size']==b['offset'] for a,b in zip(rows,rows[1:])),'entries':rows,'limit':'All fixed table entries checked for extents; ELF headers inspected only as loader inputs, not navy implementation review or source/binary pairing.'}
(H/'ramdisk-review.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'assets':len(out),'files':res['count'],'image_size':res['image_size'],'table_end':res['table_end'],'unique':res['unique_names'],'contiguous':res['contiguous'],'elfs':sum('elf_class'in x for x in rows),'bad_elf_ranges':[x['name'] for x in rows if any(not s['range_ok'] for s in x.get('segments',[]))],'shared_pages':[x['name'] for x in rows if x.get('shared_load_pages')]},ensure_ascii=False))
