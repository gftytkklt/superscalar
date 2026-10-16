"""Lexical placeholder navigation only. No defect or approved-gap inference."""
import json,re,hashlib
from pathlib import Path
R=Path('/home/gftyt/ysyx-workbench'); O=R/'npc/verif/records/process/code_correctness_review'
roots=['nemu/src','nemu/include','abstract-machine/am/src','abstract-machine/klib','nanos-lite/src','nanos-lite/include','navy-apps/libs/libam','navy-apps/libs/libos','navy-apps/libs/libndl','navy-apps/libs/libminiSDL','navy-apps/libs/libc/src/platform','navy-apps/apps/nanos-lite-guest','navy-apps/apps/nterm','navy-apps/apps/nwm']
rows=[]
def phase(p):
 if p.startswith('nemu/'):
  return 'CCR-P2' if '/isa/' in p or '/memory/' in p or '/engine/' in p else 'CCR-P3'
 if p.startswith('abstract-machine/'):
  return 'CCR-P5' if '/klib/' in p or '/libgcc/' in p or '/ioe/' in p or Path(p).name in ('ioe.c','input.c','timer.c','video.c','gpu.c','audio.c','disk.c') else 'CCR-P4'
 if p.startswith('nanos-lite/'): return 'CCR-P6'
 return 'CCR-P7' if any(k in p for k in ['/libs/libam/','/libs/libos/','/libs/libc/']) else 'CCR-P8'
for root in roots:
 for p in sorted((R/root).rglob('*')):
  if not p.is_file() or p.is_symlink() or 'build' in p.parts or 'generated' in p.parts or 'config' in p.parts or p.suffix.lower() not in ('.c','.h','.cc','.cpp','.s'): continue
  data=p.read_bytes(); text=data.decode(errors='replace'); path=str(p.relative_to(R)); digest=hashlib.sha256(data).hexdigest()
  matches=[]
  for i,line in enumerate(text.splitlines(),1):
   if re.search(r'TODO|FIXME|please implement|not[ -]?implement(?:ed)?|unimplemented|\bstub\b',line,re.I): matches.append((i,i,line.strip(),'explicit text marker'))
  # Only syntactically tiny bodies; normal intentional no-op functions are possible.
  for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{\s*(?:return\s*(?:false|NULL|0)?\s*;)?\s*\}',text):
   if m[1] in ('if','while','for','switch'): continue
   a=text[:m.start()].count('\n')+1; b=text[:m.end()].count('\n')+1
   matches.append((a,b,m[0].strip(),'empty or single return false/NULL/0 body'))
  for a,b,marker,kind in matches:
   rid='PH-'+hashlib.sha256(f'{path}:{a}:{b}:{kind}'.encode()).hexdigest()[:16]
   rows.append({'placeholder_id':rid,'path':path,'canonical_path':str(p.resolve().relative_to(R)),'line_range':[a,b],'source_sha256':digest,'marker':marker,'marker_kind':kind,'certainty':'lexical candidate','review_status':'Enumerated','phase':phase(path),'scope_approval':'No teaching waiver inferred; S01-S05 do not approve every stub','limits':['标记/极简函数仅是定位候选；可能是合法no-op/返回路径；后续按契约和调用上下文判定；不是Confirmed Finding或已批准Gap']})
rows.sort(key=lambda x:(x['path'],x['line_range'],x['placeholder_id']))
(O/'p1/placeholder-candidates.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows))
print(json.dumps({'rows':len(rows),'files':len(set(x['path'] for x in rows))}))
