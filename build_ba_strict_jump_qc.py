"""Add versioned strict BA sidecars without changing existing scores or inputs."""
from pathlib import Path
import hashlib,json
import numpy as np
from ba_strict_jump_qc import gate
ROOT=Path(__file__).resolve().parent
R=ROOT/'outputs/ba_human_qc_20261013'; OUT=R/'strict_v1';OUT.mkdir(exist_ok=True)
B=Path('/Users/New/Downloads/BA_additional100_recovery_20261012')
rows=[]
for r in json.loads((R/'index.json').read_text())['runs']:
 p=B/r['id']/'FINAL.npz';z=np.load(p);track,movement,q=gate(z['proposed'],int(z['start']))
 q.update(id=r['id'],source_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 q['analysis']=[[float(v) if np.isfinite(v) else None for v in xy] for xy in track]
 np.savez_compressed(OUT/(r['id']+'.npz'),analysis=track,movement_step_px=movement,start=z['start'],end=z['end'])
 (OUT/(r['id']+'.json')).write_text(json.dumps(q,separators=(',',':')))
 rows.append({k:v for k,v in q.items() if k!='analysis'})
receipt={'version':'0.1.0','status':'UNREVIEWED','runs':rows,'blocked_runs':sum(r['human_run_review_required'] for r in rows),'remaining_pairs':sum(len(r['jump_pairs']) for r in rows),'scope':'Separate BA analysis sidecars only. Historical scientific outputs unchanged. No new image recovery. No inferred interval boundaries.'}
(OUT/'RECEIPT.json').write_text(json.dumps(receipt,indent=2))
print({k:v for k,v in receipt.items() if k!='runs'})
