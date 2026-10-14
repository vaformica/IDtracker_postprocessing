"""Build trace-first screening from immutable additional-100 BA review inputs."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
ROOT=Path(__file__).resolve().parent;R=ROOT/'outputs/ba_human_qc_20261013';B=Path('/Users/New/Downloads/BA_additional100_recovery_20261012')
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def spans(m,start):
 d=np.diff(np.r_[False,m,False].astype(int));return [[int(start+a),int(start+b-1)] for a,b in zip(np.where(d==1)[0],np.where(d==-1)[0])]
def clean(a):return [[round(float(v),2) if np.isfinite(v) else None for v in row] for row in a]
R.mkdir(exist_ok=True);(R/'data').mkdir(exist_ok=True);(R/'media').mkdir(exist_ok=True);runs=[];inputs=[]
prior=load(ROOT/'outputs/ba_additional100_combined_feedback_20261013/NORMALIZED_DECISIONS.json')
for q in load(B/'QC_INDEX.json')['runs']:
 rid=q['id'];p=B/rid;cfg=load(p/'CONFIG.json');z=np.load(p/'FINAL.npz');raw=z['raw'];pro=z['proposed'];start=int(z['start']);end=int(z['end']);assert len(raw)==len(pro)==end-start+1
 crop=load(p/'review/REVIEW_DATA.json')['clips'][0]['crop'];ex=np.isin(np.arange(start,end+1),q.get('excluded_frames',[]));gaps=~np.isfinite(pro).all(1)&~ex;jumps=np.r_[False,np.linalg.norm(np.diff(pro,axis=0),axis=1)>100]
 # Display complete lines, breaking missing observations; no gap interpolation.
 events=[dict(kind='missing tracking',bounds=b) for b in spans(gaps,start)]+[dict(kind='jump >100 px',bounds=b) for b in spans(jumps,start)]+[dict(kind='human-excluded',bounds=b) for b in spans(ex,start)]
 detail=dict(id=rid,start=start,end=end,crop=crop,raw=clean(raw),proposed=clean(pro),events=events,prior_reviews=[x for x in prior if x['decision']['run_id']==rid],excluded=q.get('excluded_frames',[]),coordinate_status='Raw baseline and unreviewed proposed recovery; not approved',input_sha256=sha(p/'FINAL.npz'))
 (R/'data'/f'{rid}.json').write_text(json.dumps(detail,separators=(',',':')))
 link=R/'media'/f'{rid}.mp4'
 if not link.exists():link.symlink_to(p/'full_window.mp4')
 assert link.resolve()==(p/'full_window.mp4').resolve() and link.stat().st_size>0
 # Gallery preview samples include discontinuity separators, avoiding false gap joins.
 thumb=[]
 for a,b in spans(np.isfinite(pro).all(1),0):
  if thumb:thumb.append([None,None])
  thumb.extend(clean(pro[a:b+1: max(1,(b-a+1)//180)]))
 row=dict(id=rid,label=q['label'],start=start,end=end,rank=q.get('qc_rank',999),reasons=q.get('qc_reasons',[]),missing=int(gaps.sum()),excluded=int(ex.sum()),jumps=int(jumps.sum()),crop=crop,thumb=thumb,data=f'data/{rid}.json',media=f'media/{rid}.mp4',input_sha256=detail['input_sha256'])
 runs.append(row);inputs.append(dict(id=rid,config_sha256=sha(p/'CONFIG.json'),tracking_sha256=detail['input_sha256'],media=str(link.resolve()),media_bytes=link.stat().st_size))
index=dict(id='ba-human-qc-additional100-20261013',runs=sorted(runs,key=lambda x:(x['rank'],x['id'])),status='UNREVIEWED',description='Human trace screening of 100 additional BA runs; not automatic biological approval')
index['hash']=hashlib.sha256(json.dumps(index,sort_keys=True).encode()).hexdigest();(R/'index.json').write_text(json.dumps(index));(R/'INPUT_MANIFEST.json').write_text(json.dumps(inputs,indent=2))
for src,dst in [('ba_human_qc_template.html','START_HERE.html'),('ba_human_qc.js','ba_human_qc.js')]:shutil.copy2(ROOT/src,R/dst)
print('Built',len(runs),'runs',index['hash'])
