#!/usr/bin/env python3
from pathlib import Path
import hashlib,json,subprocess
P=Path(__file__).resolve().parent;B=P.parent;R=P.parents[5]
assert json.loads((P/'validation.json').read_text())['gate']=='PASS'
paths=set(p for p in P.rglob('*') if p.is_file() and p.name!='manifest.json')
paths|={B/p for p in ['P9.md','CROSS_LAYER_P9.md','INTERFACES.md','interfaces_current.json','COVERAGE.md','coverage.jsonl','CONTRACTS.md','FINDINGS.md','findings.json']}
paths|={R/p for p in ['README.md','npc/README.md','npc/verif/README.md','npc/verif/records/README.md','npc/verif/records/process/README.md','npc/verif/docs/CODE_CORRECTNESS_REVIEW_PLAN.md','.agent/CURRENT_STATE.md','.agent/TASK_QUEUE.md','.agent/CHANGELOG_AGENT.md','.agent/DOCUMENT_INDEX.md']}
files=[{'path':str(p.relative_to(R)),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
(P/'manifest.json').write_text(json.dumps({'phase':'CCR-P9','date':'2026-10-17','head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),'count':len(files),'files':files,'excludes':['self: p9/manifest.json'],'meaning':'local evidence bytes; most are ignored, not guaranteed by Git commit'},ensure_ascii=False,indent=2)+'\n')
errors=[x['path'] for x in files if hashlib.sha256((R/x['path']).read_bytes()).hexdigest()!=x['sha256']]
print('manifest',len(files),'mismatches',errors);assert not errors
