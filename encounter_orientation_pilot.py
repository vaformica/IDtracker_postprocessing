"""Read-only-input encounter/orientation feasibility pilot; not production science.

Codex/AI-authored, 2026-10-09. No posture, intent, identity correction, or
biological validation is implied by these geometric measurements.
"""
from pathlib import Path
import argparse, csv, hashlib, itertools, json, shutil
import numpy as np

VERSION = '0.1.0-development'
NAMES = [
 'Camera_1_40169154_20260702_1535_FIGHT_ACT2_A2',
 'Camera_1_40169154_20260702_1310_FIGHT_ACT1_A2',
 'groupagetrial01_062024_Box02_MIX',
 'groupagetrial06_062224_Box2_OLD',
]
WINDOWS = (7, 13, 25)
RULES = dict(velocity_windows_frames=list(WINDOWS), default_window_frames=13,
 max_adjacent_step_px=20, centroid_match_px=5, minimum_axis_ratio=1.4,
 proximity_px=60, minimum_bout_frames=15, context_seconds=1,
 minimum_context_coverage=.7, radial_speed_floor_px_s=5,
 motion_aligned_end_minimum_speed_px_s=10,
 motion_aligned_end_maximum_angle_degrees=30)

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()

def clean(x):
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,(np.integer,)):return int(x)
 if isinstance(x,(float,np.floating)):return round(float(x),3) if np.isfinite(x) else None
 if isinstance(x,np.bool_):return bool(x)
 return x

def dump(p,x):Path(p).write_text(json.dumps(clean(x),allow_nan=False,separators=(',',':')))

def bouts(mask):
 e=np.diff(np.r_[False,mask,False].astype(int))
 return list(zip(np.flatnonzero(e==1),np.flatnonzero(e==-1)))

def velocity(raw,supported,fps,window):
 """Centered OLS derivative, only wholly supported windows without large steps.

No interpolation. All windows retain exact global-frame alignment; edge
windows remain unknown. Centered estimates are retrospective, not causal.
"""
 out=np.full_like(raw,np.nan,dtype=float);h=window//2
 t=np.arange(-h,h+1)/fps;den=t@t
 for a in range(raw.shape[1]):
  valid=supported[:,a]&np.isfinite(raw[:,a]).all(1)
  for i in range(h,len(raw)-h):
   block=raw[i-h:i+h+1,a]
   if valid[i-h:i+h+1].all() and np.max(np.linalg.norm(np.diff(block,axis=0),axis=1))<=RULES['max_adjacent_step_px']:
    out[i,a]=(t[:,None]*block).sum(0)/den
 return out

def radial(raw,vel,supported,a,b):
 r=raw[:,b]-raw[:,a];dist=np.linalg.norm(r,axis=1)
 good=supported[:,a]&supported[:,b]&(dist>0)
 u=np.divide(r,dist[:,None],out=np.full_like(r,np.nan),where=dist[:,None]>0)
 ca=np.sum(vel[:,a]*u,axis=1);cb=-np.sum(vel[:,b]*u,axis=1)
 ca[~good]=np.nan;cb[~good]=np.nan
 return dist,ca,cb

def attribution(ca,cb,lo,hi,kind,fps):
 expected=int(round(fps));n=max(0,hi-lo)
 if n<expected:return dict(label='Unknown: window boundary',coverage=0)
 x=ca[lo:hi];y=cb[lo:hi];ok=np.isfinite(x)&np.isfinite(y)
 coverage=float(ok.mean())
 if coverage<RULES['minimum_context_coverage']:return dict(label='Unknown: insufficient detection support',coverage=coverage)
 x=float(np.mean(x[ok]));y=float(np.mean(y[ok]));floor=RULES['radial_speed_floor_px_s']
 sx,sy=(x,y) if kind=='approach' else (-x,-y)
 if sx+sy<=floor:label='No sustained net '+('closing' if kind=='approach' else 'separation')
 elif sx>floor and sy>floor:label='Both'
 elif sx>floor:label='A'
 elif sy>floor:label='B'
 else:label='Ambiguous: small individual contributions'
 return dict(label=label,coverage=coverage,a_mean_px_s=x,b_mean_px_s=y)

def events_for_pair(raw,supported,velocities,a,b,fps,start):
 dist=np.linalg.norm(raw[:,b]-raw[:,a],axis=1);known=np.isfinite(dist)
 events=[];ctx=int(round(fps))
 for lo,hi in bouts(known&(dist<=RULES['proximity_px'])):
  if hi-lo<RULES['minimum_bout_frames']:continue
  ev=dict(a=a,b=b,first_global_frame=start+lo,last_global_frame=start+hi-1,
          duration_seconds=(hi-lo)/fps,entry_observed=bool(lo>0 and known[lo-1] and dist[lo-1]>60),
          exit_observed=bool(hi<len(raw) and known[hi] and dist[hi]>60),estimates={})
  for w,v in velocities.items():
   _,ca,cb=radial(raw,v,supported,a,b)
   approach=attribution(ca,cb,max(0,lo-ctx),lo,'approach',fps) if ev['entry_observed'] else dict(label='Unknown: censored entry',coverage=0)
   departure=attribution(ca,cb,hi,min(len(raw),hi+ctx),'departure',fps) if ev['exit_observed'] else dict(label='Unknown: censored exit',coverage=0)
   ev['estimates'][str(w)]=dict(approach=approach,departure=departure)
  for kind in ('approach','departure'):
   labels=[ev['estimates'][str(w)][kind]['label'] for w in WINDOWS]
   ev[kind+'_stable']=len(set(labels))==1 and labels[0] in ('A','B','Both')
  events.append(ev)
 return events

def extract_axes(session,raw,start):
 from idtrackerai import ListOfBlobs
 import cv2
 blobs=ListOfBlobs.load(Path(session)/'preprocessing/list_of_blobs.pickle')
 supported=np.zeros(raw.shape[:2],bool);axes=np.full((*raw.shape[:2],4),np.nan)
 ratio=np.full(raw.shape[:2],np.nan);reason=np.full(raw.shape[:2],1,np.uint8)
 for i in range(len(raw)):
  candidates={a:[] for a in range(raw.shape[1])}
  for b in blobs.blobs_in_video[start+i]:
   ids=list(b.final_identities)
   if b.is_an_individual and len(ids)==1 and ids[0] not in (None,0) and 0<int(ids[0])<=raw.shape[1]:candidates[int(ids[0])-1].append(b)
  for a,bs in candidates.items():
   if not np.isfinite(raw[i,a]).all():continue
   if len(bs)!=1:reason[i,a]=2;continue
   blob=bs[0];center=np.array(blob.centroid)
   if np.linalg.norm(center-raw[i,a])>RULES['centroid_match_px']:reason[i,a]=3;continue
   supported[i,a]=True
   m=cv2.moments(blob.contour)
   if m['m00']<=0:reason[i,a]=4;continue
   cov=np.array([[m['mu20'],m['mu11']],[m['mu11'],m['mu02']]])/m['m00']
   vals,vecs=np.linalg.eigh(cov);ratio[i,a]=np.sqrt(max(0,vals[1])/max(1e-9,vals[0]))
   if ratio[i,a]<RULES['minimum_axis_ratio']:reason[i,a]=4;continue
   axis=vecs[:,1];proj=(blob.contour-center)@axis
   ends=center+np.quantile(proj,[.05,.95])[:,None]*axis
   axes[i,a]=ends.ravel();reason[i,a]=0
 return supported,axes,ratio,reason

def build(source,qc,out,template):
 import cv2
 source,qc,out=map(Path,(source,qc,out));out.mkdir(parents=True,exist_ok=False)
 plan=json.loads((source/'plan.json').read_text());quality={r['run']:r for r in json.loads((qc/'QC_RUN_INDEX.json').read_text())}
 summaries=[]
 for order,name in enumerate(NAMES):
  r=next(r for r in plan['tasks'] if r['stem']==name);src=source/'runs'/name
  dst=out/name;dst.mkdir();meta=json.loads((src/'analysis/manifest.json').read_text());rm=json.loads((src/'review/source_manifest.json').read_text())
  canonical=src/'analysis/canonical_states.npz';assert sha(canonical)==rm['canonical_sha256']
  with np.load(canonical) as n:raw=n['raw'].copy()
  start=int(r['first_global_frame']);fps=float(r['fps']);assert len(raw)==r['frames']
  blob_path=Path(r['session'])/'preprocessing/list_of_blobs.pickle'
  inputs={str(p):sha(p) for p in (canonical,blob_path,src/'analysis/manifest.json',src/'review/source_manifest.json')}
  supported,axes,ratios,reasons=extract_axes(r['session'],raw,start)
  velocities={w:velocity(raw,supported,fps,w) for w in WINDOWS}
  pairs=list(itertools.combinations(range(raw.shape[1]),2));events=[]
  for a,b in pairs:events.extend(events_for_pair(raw,supported,velocities,a,b,fps,start))
  events.sort(key=lambda e:(e['first_global_frame'],e['a'],e['b']))
  for i,e in enumerate(events):e['id']=i+1
  np.savez_compressed(dst/'measurements.npz',raw=raw,independent_detection_supported=supported,axis_endpoints=axes,axis_ratio=ratios,axis_reason=reasons,**{f'velocity_{w}':v for w,v in velocities.items()})
  dump(dst/'events.json',events)
  with (dst/'events.csv').open('w',newline='') as f:
   rows=[]
   for e in events:
    row={k:v for k,v in e.items() if k!='estimates'}
    for w,x in e['estimates'].items():
     for kind,est in x.items():
      for k,v in est.items():row[f'{kind}_{w}_{k}']=v
    rows.append(row)
   keys=sorted(set().union(*(row.keys() for row in rows))) if rows else ['id','a','b']
   wr=csv.DictWriter(f,keys);wr.writeheader();wr.writerows(rows)
  with (dst/'animal_frames.csv').open('w',newline='') as f:
   wr=csv.writer(f);wr.writerow(['global_frame','animal_id','raw_x','raw_y','independent_detection_supported','axis_x1','axis_y1','axis_x2','axis_y2','axis_ratio','axis_reason','vx_px_s','vy_px_s'])
   for i in range(len(raw)):
    for a in range(raw.shape[1]):wr.writerow(clean([start+i,a,*raw[i,a],supported[i,a],*axes[i,a],ratios[i,a],reasons[i,a],*velocities[13][i,a]]))
  video=src/'review'/rm['video'];shutil.copy2(video,dst/'video.mp4')
  summary=dict(name=name,collection=r['collection'],frames=len(raw),fps=fps,start=start,animals=raw.shape[1],qc=quality[name],event_count=len(events),
   supported_percent=100*supported.mean(),axis_percent=100*np.isfinite(axes).all(2).mean(),velocity_percent=100*np.isfinite(velocities[13]).all(2).mean(),
   stable_approaches=sum(e['approach_stable'] for e in events),stable_departures=sum(e['departure_stable'] for e in events))
  data=dict(**summary,geometry=rm['video_geometry'],raw=raw,supported=supported.astype(int),axes=axes,velocities={str(w):v for w,v in velocities.items()},pairs=pairs,events=events,rules=RULES,source_kind=meta['trajectory_source_kind'])
  text=Path(template).read_text().replace('__DATA__',json.dumps(clean(data),allow_nan=False,separators=(',',':')).replace('</','<\\/'))
  (dst/'review.html').write_text(text)
  provenance=dict(author='Codex / AI',version=VERSION,status='UNREVIEWED_FEASIBILITY_PILOT',rules=RULES,inputs=inputs,source_session=r['session'],source_video=r['source_video'],source_trajectory_kind=meta['trajectory_source_kind'],source_video_geometry=rm['video_geometry'],video_sha256=sha(video),output_video_sha256=sha(dst/'video.mp4'),source_rules_unchanged=True,axis_reason_codes={'0':'usable undirected silhouette axis','1':'raw coordinate absent','2':'no unique individual blob','3':'centroid mismatch','4':'degenerate or insufficient elongation'},selection='Two distinct recordings per collection; zero >100px jumps, low missingness among zero-jump choices; known WRONG dyadic recording excluded. QC is not identity validation.')
  assert all(sha(p)==h for p,h in inputs.items());assert provenance['video_sha256']==provenance['output_video_sha256']
  dump(dst/'PROVENANCE.json',provenance)
  # Representative full-arena frames from the unchanged review video.
  cap=cv2.VideoCapture(str(dst/'video.mp4'));thumbs=[]
  selected=[len(raw)//5,len(raw)//2,4*len(raw)//5]
  good=[e for e in events if e['approach_stable'] or e['departure_stable']]
  if good:selected=[max(0,good[0]['first_global_frame']-start-15),(good[0]['first_global_frame']+good[0]['last_global_frame'])//2-start,min(len(raw)-1,good[0]['last_global_frame']-start+15)]
  for frame in selected:
   cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,img=cap.read();assert ok
   img=cv2.resize(img,(640,460));cv2.putText(img,f'Global frame {start+frame}',(15,28),cv2.FONT_HERSHEY_SIMPLEX,.65,(255,255,255),2);thumbs.append(img)
  cap.release();cv2.imwrite(str(dst/'sample_frames.jpg'),np.concatenate(thumbs,axis=1))
  dump(dst/'SUMMARY.json',summary);summaries.append(summary);print(json.dumps(clean(summary)),flush=True)
 dump(out/'SUMMARY.json',summaries)
 shutil.copy2(Path(__file__).with_name('encounter_orientation_methods.html'),out/'METHODS.html')
 links=''.join(f'<article><h2>{s["collection"].replace("_"," ").title()} {i+1 if i<2 else i-1}</h2><p>{s["name"]}</p><p>{s["qc"]["raw_missing_percent"]}% raw missing · 0 jumps over 100 px · {s["event_count"]} proximity bouts</p><a href="{s["name"]}/review.html">Open synchronized review →</a></article>' for i,s in enumerate(summaries))
 (out/'START_HERE.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Beetle approaches and departures</title><style>body{font:17px/1.5 system-ui;max-width:1100px;margin:40px auto;padding:0 22px;background:#f7f8fa;color:#172c39}article{padding:20px 0;border-top:1px solid #bcc8cf;overflow-wrap:anywhere}a{color:#075e99}small{color:#445966}</style><h1>Who approaches—and who leaves?</h1><p>Four-video feasibility pilot · Codex / AI · 9 October 2026 · <strong>UNREVIEWED</strong></p><p>Movement arrows describe travel. Plain lines describe the silhouette axis, without identifying the head. Select a beetle pair and jump to a proximity bout to compare their contributions to closing and separation.</p><p>Videos and original trajectories are unchanged. Quality-based selection is not biological validation. The six-beetle examples have more occlusion than the dyadic examples; uncertain movement is left unknown.</p>'+links+'<p><a href="METHODS.html">How to interpret the measurements and limitations</a></p></html>')
 dump(out/'RELEASE_RECEIPT.json',dict(status='COMPLETE_UNREVIEWED',version=VERSION,runs=4,author='Codex / AI',production_changed=False,source_hashes_verified=True))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('qc');p.add_argument('output');p.add_argument('--template',default=str(Path(__file__).with_name('encounter_orientation_review.html')));a=p.parse_args();build(a.source,a.qc,a.output,a.template)
