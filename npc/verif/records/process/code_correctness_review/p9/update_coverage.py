#!/usr/bin/env python3
"""Add P9 interface obligations without rewriting P2–P8 review facts."""
from pathlib import Path
import json,gzip,collections
H=Path(__file__).resolve().parent;B=H.parent
before=[json.loads(s) for s in gzip.decompress((H/'coverage.jsonl.before.gz').read_bytes()).decode().splitlines()]
interfaces=json.loads(gzip.decompress((H/'interfaces_current.json.before.gz').read_bytes()))
chains=json.loads((H/'chains.json').read_text());endpoints=json.loads((H/'endpoints.json').read_text())['checks'];support={e['path'] for e in endpoints};linked=collections.defaultdict(set)
for l in interfaces['interfaces']:
 for e in l['endpoints']:linked[e['path']].add(l['interface_id'])
for l in chains:
 for r in l['references']:linked[r['path']].add(l['id'])
module_links={'U14':['L02','L09'],'N01':['L08','L09'],'N02':['L01','L07','L08','L09'],'N03':['L01','L04','L07','L08'],'A14':['L08','L09'],'A02':['L01','L03','L04','L05','L06','L07'],'A07':['L02','L03','L04','L05','L06','L09'],'X02':['L08'],'X03':['L04','L08','L09']}
out=[];reviews=[]
for r in before:
 obligation='CCR-P9' in r.get('effective_phase_responsibilities',[])
 supplemental=r['row_kind']=='file' and r['path'] in support
 if obligation or supplemental:
  ids=sorted(linked[r['path']] or set(module_links.get(r['module_id'],['L09'])))
  depth='CrossLayerEndpoint'
  if r['row_kind']!='file':depth='InterfaceConditionNavigation'
  elif r['module_id'] in ['U14','A14']:depth='AssetIdentityAndProducerConsumer'
  elif r['module_id']=='X03':depth='DerivedIdentity' if r['path'].endswith('.pyc') else 'LinuxSupportInterface'
  ev=[f'p9/{i}.md' for i in ids]+['p9/source-check.json']
  if r['module_id']=='U14':ev+=['p9/fsimg-match.json']
  if r['module_id']=='X03':ev+=['p9/X03_SUPPORT.md']
  record={'phase':'CCR-P9','depth':depth,'status':'ReviewedStatic','chain_ids':ids,'scope':'仅接口字段/配置与失败传播义务；不覆盖先前文件实现审阅结论','evidence':ev,'dynamic_validation':'逐链区分见p9/chains.json；非逐文件运行通过','limits':'P8缺源、历史binary配对Unknown、未决CQ与实际功能缺陷不消除；资源/条件数量不是功能覆盖率','origin':'scheduled responsibility' if obligation else 'supplementary seam endpoint'}
  r['p9_review']=record
  # Only the new X03 primary responsibility changes top-level status.
  if r.get('effective_phase')=='CCR-P9' and r['module_id']=='X03':r['review_status']='BoundaryReviewed' if depth=='DerivedIdentity' else 'ReviewedStatic'
  reviews.append({'row_id':r['row_id'],'row_kind':r['row_kind'],'module_id':r['module_id'],'path':r['path'],'line_range':r.get('line_range'),'source_sha256':r.get('source_sha256'),**record})
 out.append(r)
(B/'coverage.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in out))
(H/'cross-layer-coverage.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n' for r in reviews))
for l in interfaces['interfaces']:
 c=next(x for x in chains if x['id']==l['interface_id']);l['review_status']=c['review_status'];l['dynamic_validation']=c['dynamic_validation'];l['contract_dimensions']={x['name']:x['assessment'] for x in c['dimensions']};l['p9_evidence']='p9/'+c['id']+'.md';l['issue_ids']=c['issue_ids'];l['limits']=c['limits'];l['supplementary_references']=c['references']
interfaces['p9_summary']={'phase':'CCR-P9','nine_chains_static_reviewed':True,'fields_per_chain':15,'meaning':'接口审阅闭合，含已定位断点/缺陷/未决CQ；不是九条实现功能PASS','p8_missing_sources':'保留Unavailable，用户暂缓','evidence':'p9/README.md'}
(B/'interfaces_current.json').write_text(json.dumps(interfaces,ensure_ascii=False,indent=2)+'\n')
summary={'stable_rows':len(out),'scheduled_rows':sum('CCR-P9' in x.get('effective_phase_responsibilities',[]) for x in out),'review_rows':len(reviews),'file_rows':sum(x['row_kind']=='file' for x in reviews),'condition_rows':sum(x['row_kind']!='file' for x in reviews),'depth':dict(collections.Counter(x['depth'] for x in reviews)),'global_status':dict(collections.Counter(x['review_status'] for x in out)),'fields':len(chains)*15,'new_findings':4}
(H/'review-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(summary)
