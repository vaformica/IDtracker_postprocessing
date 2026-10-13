"""Versioned BA interpolation batch; immutable source tracking, portable QC sidecars."""
import argparse,csv,hashlib,json,os,shutil,subprocess,tomllib
from pathlib import Path
import cv2,numpy as np
from ba_interpolation import frozen_interpolate,spans,VERSION,RULES

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False))
def run(root,index):
 root=Path(root);r=json.loads((root/'PLAN.json').read_text())['runs'][index];out=root/'runs'/r['id'];out.mkdir(parents=True,exist_ok=True)
 assert not (out/'MANIFEST.json').exists(),'Completed runs are immutable'
 assert digest(r['source_toml'])==r['toml_sha256'],'Source TOML changed'
 t=tomllib.loads(Path(r['source_toml']).read_text());assert t['number_of_animals']==1 and len(t['roi_list'])==1
 sh=digest(Path(r['session'])/'session.json');assert not r['session_sha256'] or sh==r['session_sha256']
 th=digest(r['trajectory']);assert not r.get('trajectory_sha256') or th==r['trajectory_sha256']
 obj=np.load(r['trajectory'],allow_pickle=True).item();xyz=obj['trajectories'];assert xyz.ndim==3 and xyz.shape[1:]==(1,2) and len(xyz)>r['end']
 raw=xyz[r['start']:r['end']+1,0].copy();baseline=raw.copy();input_hashes=dict(toml=r['toml_sha256'],session=sh,trajectory=th)
 if r['baseline_npz']:
  z=np.load(r['baseline_npz']);assert np.array_equal(z['raw'],raw,equal_nan=True);baseline=z['proposed'].copy();input_hashes['baseline_npz']=digest(r['baseline_npz'])
 protected=np.isin(np.arange(r['start'],r['end']+1),r['excluded_frames']);assert not np.isfinite(raw[protected]).any()
 xy,method,events,audit=frozen_interpolate(baseline,r['start'],protected,r,collection='BA',number_of_animals=1)
 finite=np.isfinite(baseline).all(1);assert np.array_equal(xy[finite],baseline[finite]);assert not np.isfinite(xy[protected]).any()
 changed=finite & (~np.isfinite(raw).all(1)|np.any(baseline!=raw,axis=1));method[(method=='existing')&changed]='prior_recovery'
 np.savez_compressed(out/'COORDINATES.npz',raw=raw,baseline=baseline,analysis=xy,method=method,protected=protected,start=r['start'],end=r['end'])
 with (out/'FRAMES.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['run_id','global_frame','raw_x','raw_y','baseline_x','baseline_y','analysis_x','analysis_y','method','human_excluded'])
  for i in range(7200):w.writerow([r['id'],r['start']+i,*[float(v) if np.isfinite(v) else '' for v in np.r_[raw[i],baseline[i],xy[i]]],str(method[i]),int(protected[i])])
 write(out/'GAPS.json',audit)
 video=out/'video.mp4';cap=cv2.VideoCapture(r['video']);assert cap.isOpened();fps=cap.get(cv2.CAP_PROP_FPS);width=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH));height=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT));cap.release();assert abs(fps-30)<.001
 if r.get('clean_video'):
  crop=json.loads(Path(r['review_data']).read_text())['clips'][0]['crop'];shutil.copy2(r['clean_video'],video)
 else:
  roi=np.asarray(r['roi']);x=max(0,int(roi[:,0].min())-20)//2*2;y=max(0,int(roi[:,1].min())-20)//2*2;w=(min(width,int(roi[:,0].max())+22)-x)//2*2;h=(min(height,int(roi[:,1].max())+22)-y)//2*2;crop=[x,y,w,h]
  ff=os.environ.get('BA_FFMPEG','/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg');seek=r['start']//30;offset=r['start']%30
  subprocess.run([ff,'-v','error','-nostdin','-threads','2','-ss',str(seek),'-i',r['video'],'-vf',f'trim=start_frame={offset}:end_frame={offset+7200},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y}','-frames:v','7200','-an','-c:v','libx264','-threads','2','-preset','veryfast','-crf','27','-pix_fmt','yuv420p','-movflags','+faststart',str(video)],check=True)
 cap=cv2.VideoCapture(str(video));count=0;brightness=[]
 while True:
  ok,im=cap.read()
  if not ok:break
  if count==0:cv2.imwrite(str(out/'first_frame.jpg'),im)
  brightness.append(float(np.median(cv2.resize(im,(64,64)))));count+=1
 cap.release();assert count==7200
 missing=~np.isfinite(xy).all(1)&~protected;gaps=spans(missing);jumps=np.flatnonzero(np.linalg.norm(np.diff(xy,axis=0),axis=1)>=100)+1;rawj=np.flatnonzero(np.linalg.norm(np.diff(raw,axis=0),axis=1)>=100)+1
 delta=np.abs(np.diff(brightness));threshold=max(12.,float(np.median(delta)+10*np.median(np.abs(delta-np.median(delta)))));lights=np.flatnonzero(delta>threshold)+1
 outside=[i for i,p in enumerate(xy) if np.isfinite(p).all() and cv2.pointPolygonTest(np.asarray(r['roi'],np.float32),tuple(map(float,p)),False)<0]
 q=dict(id=r['id'],census_id=r['census_id'],label=r['label'],start=r['start'],end=r['end'],crop=crop,baseline_kind=r['baseline_kind'],missing_frames=int(missing.sum()),missing_percent=round(float(missing.sum()/((~protected).sum())*100),3),longest_gap=max([b-a for a,b in gaps] or [0]),interpolated_frames=int((method=='interpolated').sum()),interpolated_gaps=len(events),prior_recovery_frames=int(changed.sum()),excluded_frames=r['excluded_frames'],raw_jumps=len(rawj),remaining_jumps=len(jumps),jump_frames=(jumps+r['start']).tolist(),brightness_frames=(lights+r['start']).tolist(),outside_roi_frames=len(outside),review_status='UNREVIEWED',turtling_status='NOT_ASSESSED',prior_note='VAF marked prior full-run interpolation test needs work' if r['id']=='new_021' else '')
 q['priority']=int(min(10000,len(jumps)*100)+q['missing_percent']*10+min(100,len(lights)*10)+min(100,len(outside)))
 write(out/'QC.json',q)
 def clean(a):return [p.tolist() if np.isfinite(p).all() else None for p in a]
 data=dict(**q,raw=clean(raw),baseline=clean(baseline),analysis=clean(xy),method=method.tolist(),gaps=audit,video=r['video'],roi=r['roi'])
 (out/'data.js').write_text('window.loadRun('+json.dumps(data,separators=(',',':'),allow_nan=False)+');')
 # SVG traces keep coordinate axes and missing breaks; orange points are inferred.
 def path(a):
  parts=[];pen=False
  for p in a:
   if not np.isfinite(p).all():pen=False;continue
   parts.append(('L' if pen else 'M')+f'{p[0]:.2f},{p[1]:.2f}');pen=True
  return ' '.join(parts)
 x,y,w,h=crop
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/><path d="{path(xy)}" fill="none" stroke="#226688" stroke-width=".8"/>'
 svg+=''.join(f'<circle cx="{p[0]}" cy="{p[1]}" r="1.4" fill="#e58c00"/>' for p in xy[method=='interpolated']);svg+='</svg>'; (out/'trace.svg').write_text(svg)
 write(out/'MANIFEST.json',dict(status='COMPLETE_UNREVIEWED',rules=RULES,source=r,input_hashes=input_hashes,encoded_frames=count,existing_finite_positions_changed=0,files={p.name:digest(p) for p in out.iterdir() if p.is_file()},scientific_approval=False))
 print(r['id'],q['missing_percent'],q['interpolated_frames'],flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('index',type=int);a=p.parse_args();run(a.root,a.index)
