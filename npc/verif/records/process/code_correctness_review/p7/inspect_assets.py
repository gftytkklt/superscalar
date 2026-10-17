#!/usr/bin/env python3
"""Read-only identity/ELF/file-table inspection of frozen P7 assets."""
from pathlib import Path
import collections, hashlib, json, re, struct, subprocess
ROOT=Path(__file__).resolve().parents[6]; HERE=Path(__file__).resolve().parent; BASE=HERE.parent
rows=[json.loads(l) for l in (BASE/'coverage.jsonl').open()]
rows=[r for r in rows if r.get('effective_phase')=='CCR-P7' and r['row_kind']=='file' and r['module_id']=='U14']
assets=[]
for r in rows:
 p=ROOT/r['path']
 if p.is_dir():
  assets.append(dict(row_id=r['row_id'],path=r['path'],kind='directory-alias',link=str(p.readlink()),resolved=str(p.resolve()),sha256=hashlib.sha256(str(p.readlink()).encode()).hexdigest(),pairing='Alias identity; nested file bytes checked through ramdisk extents, not duplicate recursive inventory'));continue
 b=p.read_bytes(); x=dict(row_id=r['row_id'],path=r['path'],size=len(b),sha256=hashlib.sha256(b).hexdigest(),pairing='Unknown: historical bytes not bound to full current source/config/flags')
 if b.startswith(b'\x7fELF'):
  x.update(kind='ELF',elf_class=b[4],endian=b[5]);
  if b[4:6]==b'\x02\x01':
   x.update(elf_type=struct.unpack_from('<H',b,16)[0],machine=struct.unpack_from('<H',b,18)[0],entry=hex(struct.unpack_from('<Q',b,24)[0]),flags=struct.unpack_from('<I',b,48)[0]);phoff=struct.unpack_from('<Q',b,32)[0];phsize,phnum=struct.unpack_from('<HH',b,54);loads=[]
   for i in range(phnum):
    vals=struct.unpack_from('<IIQQQQQQ',b,phoff+i*phsize)
    if vals[0]==1:loads.append(dict(offset=vals[2],vaddr=hex(vals[3]),filesz=vals[5],memsz=vals[6],align=vals[7],flags=vals[1]))
   x['load_segments']=loads
 elif b.startswith((b'!<arch>\n',b'!<thin>\n')):
  x.update(kind='archive',thin=b.startswith(b'!<thin>'),members=subprocess.check_output(['ar','t',str(p)],text=True).splitlines())
 elif '/fsimg/' in str(p):x['kind']='resource-or-alias'
 elif p.suffix=='.d':x.update(kind='dependency-metadata',dependency_text=b.decode(errors='replace'))
 else:x['kind']='metadata-or-resource'
 assets.append(x)
(HERE/'asset-review.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n')
table=(ROOT/'navy-apps/build/ramdisk.h').read_text(); img=ROOT/'navy-apps/build/ramdisk.img'; extents=[];end=0
with img.open('rb') as f:
 for name,size,off in re.findall(r'\{"([^"]+)",\s*(\d+),\s*(\d+)\}',table):
  size=int(size);off=int(off);f.seek(off);data=f.read(size);fs=ROOT/'navy-apps/fsimg'/name.lstrip('/');h=hashlib.sha256(data).hexdigest()
  extents.append(dict(name=name,size=size,offset=off,contiguous=off==end,complete=len(data)==size,image_sha256=h,fsimg_sha256=hashlib.sha256(fs.read_bytes()).hexdigest() if fs.is_file() else None,source_link=str(fs.readlink()) if fs.is_symlink() else None));end=off+size
res=dict(file_count=len(extents),image_size=img.stat().st_size,padding=img.stat().st_size-end,extents=extents)
(HERE/'fsimg-match.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n')
print('assets',len(assets),collections.Counter(x['kind'] for x in assets));print('ramdisk entries',len(extents),'mismatches',[x['name'] for x in extents if x['image_sha256']!=x['fsimg_sha256']])
