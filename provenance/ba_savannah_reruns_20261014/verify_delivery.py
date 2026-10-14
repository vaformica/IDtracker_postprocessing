from pathlib import Path
import sys,json,hashlib,csv
import numpy as np,cv2
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from ba_interpolation import frozen_interpolate
R=Path(__file__).resolve().parent;D=R/'BA_Savannah_reruns11_QC_20261014'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes=json.loads((D/'DELIVERY_HASHES.json').read_text())
for name,h in hashes.items():assert sha(D/name)==h,name
index=json.loads((D/'QC_INDEX.json').read_text());plan=json.loads((D/'PLAN.json').read_text());lookup={x['id']:x for x in plan['runs']};finger=[];rows=[]
for row in index['runs']:
 rid=row['id'];p=D/'runs'/rid;r=lookup[rid];finger.append((rid,sha(p/'MANIFEST.json')))
 m=json.loads((p/'MANIFEST.json').read_text())
 for name,h in m['files'].items():assert sha(p/name)==h,(rid,name)
 z=np.load(p/'COORDINATES.npz');out,method,events,audit=frozen_interpolate(z['baseline'],r['start'],z['protected'],r,collection='BA',number_of_animals=1)
 assert np.array_equal(out,z['analysis'],equal_nan=True)
 s=np.load(p/'STRICT_ANALYSIS.npz');assert not (np.linalg.norm(np.diff(s['analysis'],axis=0),axis=1)>=100).any()
 if row['remaining_jumps']:assert np.isnan(s['movement_step_px']).all()
 t=json.loads((p/'TURTLING_SCREENING.json').read_text());mask=np.array(t['candidate_mask']);assert len(mask)==7200 and not mask[z['protected']|(z['method']=='interpolated')].any()
 if row['remaining_jumps']:assert not mask.any()
 with (p/'FRAMES.csv').open() as f:
  vals=list(csv.DictReader(f));assert len(vals)==7200;assert [int(v['global_frame']) for v in vals]==list(range(r['start'],r['end']+1))
 cap=cv2.VideoCapture(str(p/'video.mp4'));n=0
 while True:
  ok,_=cap.read()
  if not ok:break
  n+=1
 cap.release();assert n==7200
 rows.append(dict(id=rid,encoded_frames=n,missing=row['missing_frames'],jumps=row['remaining_jumps'],interpolated=row['interpolated_frames']))
assert hashlib.sha256(json.dumps(finger).encode()).hexdigest()==index['hash']
result=dict(status='PASS',verified_files=len(hashes),runs=rows,dataset_hash=index['hash'],frames=len(rows)*7200,exact_interpolation_replay=True,strict_gate_safety=True,posture_unknown_masks=True,biological_validation=False)
(R/'LOCAL_DELIVERY_VERIFICATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
