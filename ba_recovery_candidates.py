"""Frozen bidirectional recovery candidates; CLI: run_id work_root.
Numerical rules unchanged from the protected-gap additional100 engine.
Source-video hashes may reuse size/mtime-bound prior verification.
"""
from pathlib import Path
import sys
import json,hashlib,subprocess,os
import cv2,numpy as np
from idtrackerai import ListOfBlobs
ROOT=Path(sys.argv[2])
R=ROOT/sys.argv[1];CONFIG=json.loads((R/'CONFIG.json').read_text())
EXCLUDED=set(CONFIG.get('excluded_frames',[]))
START,END=CONFIG['start'],CONFIG['end'];N=END-START+1
VIDEO=Path(CONFIG['video']);SESSION=Path(CONFIG['session'])
FF='/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg';FP=str(Path(FF).with_name('ffprobe'))
info=json.loads(subprocess.check_output([FP,'-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,avg_frame_rate,start_time','-of','json',str(VIDEO)]))['streams'][0]
assert info['r_frame_rate']=='30/1' and info['avg_frame_rate']=='30/1' and abs(float(info.get('start_time',0)))<1e-6
roi=np.array(CONFIG['roi']);X=max(0,int(roi[:,0].min())-25)//2*2;Y=max(0,int(roi[:,1].min())-25)//2*2
W=(min(info['width'],int(roi[:,0].max())+25)-X)//2*2;H=(min(info['height'],int(roi[:,1].max())+25)-Y)//2*2
ORIGIN=np.array([X,Y]);RAD=15
RULES=dict(version='D4-recovery-0.1-development',area_min=300,area_max=4000,maximum_step_px=30,blob_similarity_min=.45,image_similarity_min=.80,image_only_max_frames=15,bidirectional_agreement_px=8,anchor_stable_frames=10,anchor_maximum_step_px=20,template_radius_px=RAD)
def sha(p):
 p=Path(p)
 if p==VIDEO:
  records=json.loads((ROOT.parent/'SOURCE_VIDEO_HASHES.json').read_text());record=next(v for v in records if v['path']==str(p));st=p.stat()
  if st.st_size==record['bytes'] and st.st_mtime_ns==record['mtime_ns']:return record['sha256']
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
blobpath=SESSION/'preprocessing/list_of_blobs.pickle';trajpath=SESSION/'trajectories/trajectories.npy'
raw=np.load(trajpath,allow_pickle=True).item()['trajectories'][START:END+1,0,:].astype(float)
bs=ListOfBlobs.load(blobpath);candidates=[];allcounts=[]
for f in range(START,END+1):
 row=[]
 for b in bs.blobs_in_video[f]:
  p=np.array(b.centroid,float)-ORIGIN
  if RULES['area_min']<=float(b.area)<=RULES['area_max'] and RAD<=p[0]<W-RAD and RAD<=p[1]<H-RAD:
   row.append(dict(xy=p.tolist(),area=float(b.area)))
 candidates.append(row);allcounts.append(len(bs.blobs_in_video[f]))
assert sha(Path(CONFIG['source_toml']))==CONFIG['toml_sha256'];print('DETECTIONS_READY',W,H,flush=True)
# Every analyzed original frame, full-resolution arena crop. No spatial rescaling.
media=R/'full_window.mp4'
filters=f'[0:v]trim=start_frame={START%30}:end_frame={START%30+N},setpts=PTS-STARTPTS,crop={W}:{H}:{X}:{Y},split=2[g][color];[g]format=gray[gray]'
cmd=[FF,'-v','error','-y','-threads','2','-ss',str(START//30),'-i',str(VIDEO),'-filter_complex',filters,'-map','[gray]','-frames:v',str(N),'-threads','2','-pix_fmt','gray','-f','rawvideo','pipe:1','-map','[color]','-frames:v',str(N),'-an','-c:v','libx264','-threads','2','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(media)]
p=subprocess.Popen(cmd,stdout=subprocess.PIPE);frames=np.empty((N,H,W),np.uint8)
for i in range(N):
 data=p.stdout.read(W*H)
 if len(data)!=W*H:raise RuntimeError(f'Incomplete source decode {i}')
 frames[i]=np.frombuffer(data,np.uint8).reshape(H,W)
assert p.wait()==0;print('DECODED',N,flush=True)
def patch(im,xy):
 x,y=np.round(xy).astype(int);return im[y-RAD:y+RAD+1,x-RAD:x+RAD+1]
def sim(a,b):
 if a.shape!=b.shape or a.shape!=(2*RAD+1,2*RAD+1):return -1.
 return float(cv2.matchTemplate(a,b,cv2.TM_CCOEFF_NORMED)[0,0])
# Anchor requires ten consecutive uniquely segmented detections that agree with raw.
anchor=np.zeros(N,bool)
for i in range(N-9):
 q=candidates[i:i+10]
 if not all(len(x)==1 for x in q):continue
 xy=np.array([x[0]['xy'] for x in q]);rr=raw[i:i+10]-ORIGIN
 if np.isfinite(rr).all() and np.max(np.linalg.norm(xy-rr,axis=1))<2 and np.max(np.linalg.norm(np.diff(xy,axis=0),axis=1))<=20:anchor[i:i+10]=True
print('ANCHOR_FRAMES',int(anchor.sum()),flush=True)
def walk(direction):
 out=np.full((N,2),np.nan);method=['unknown']*N;scores=np.full(N,np.nan);point=None;template=None;lastarea=None;fallback=0
 for i in (range(N) if direction==1 else range(N-1,-1,-1)):
  if START+i in EXCLUDED:
   point=None;template=None;lastarea=None;fallback=0;continue
  # Reinitialize only at independently stable unique-detection anchors.
  if anchor[i]:
   point=np.array(candidates[i][0]['xy']);template=patch(frames[i],point).copy();lastarea=candidates[i][0]['area'];fallback=0
   out[i]=point;method[i]='anchor_blob';scores[i]=1;continue
  if point is None:continue
  choices=[]
  for b in candidates[i]:
   q=np.array(b['xy']);d=float(np.linalg.norm(q-point));s=sim(patch(frames[i],q),template)
   if d<=30 and s>=.45 and .35<=b['area']/lastarea<=2.8:choices.append((s-d/100,q,b,s))
  choices.sort(key=lambda x:x[0],reverse=True)
  if choices and (len(choices)==1 or choices[0][0]-choices[1][0]>.15):
   _,point,b,s=choices[0];template=patch(frames[i],point).copy();lastarea=b['area'];fallback=0;out[i]=point;method[i]='selected_blob';scores[i]=s;continue
  if fallback>=15:point=None;continue
  x,y=np.round(point).astype(int);left=max(0,x-30-RAD);top=max(0,y-30-RAD);right=min(W,x+30+RAD+1);bottom=min(H,y+30+RAD+1)
  res=cv2.matchTemplate(frames[i,top:bottom,left:right],template,cv2.TM_CCOEFF_NORMED)
  _,s,_,loc=cv2.minMaxLoc(res);q=np.array([left+loc[0]+RAD,top+loc[1]+RAD],float)
  if s>=.80 and np.linalg.norm(q-point)<=30:
   point=q;fallback+=1;out[i]=point;method[i]='image_estimate';scores[i]=s
  else:point=None
 return out,method,scores
fw,fm,fs=walk(1);bw,bm,ss=walk(-1);agreement=np.linalg.norm(fw-bw,axis=1);proposal=np.full_like(raw,np.nan);status=[];reasons=[]
for i in range(N):
 if np.isfinite(agreement[i]) and agreement[i]<=8:
  if fm[i]!='image_estimate' and bm[i]!='image_estimate':
   # Same centroid is required: do not average two different detections.
   if np.linalg.norm(fw[i]-bw[i])<.01:proposal[i]=fw[i]+ORIGIN;kind='blob'
   else:status.append('unknown');reasons.append('competing_blob_detections');continue
  else:
   # Explicit image estimate, not a newly observed segmentation centroid.
   proposal[i]=(fw[i]+bw[i])/2+ORIGIN;kind='image'
  delta=np.linalg.norm(proposal[i]-raw[i])
  if kind=='blob' and np.isfinite(delta) and delta<.01:status.append('unchanged');reasons.append('bidirectional_blob_support')
  else:status.append('proposed_'+kind);reasons.append('image_estimate_bidirectional' if kind=='image' else 'alternative_blob_bidirectional')
 else:status.append('unknown');reasons.append('missing_or_disagreeing_recovery')
# Break any newly introduced large step conservatively.
for i in np.where(np.linalg.norm(np.diff(proposal,axis=0),axis=1)>30)[0]+1:
 if not (status[i]=='unchanged' and status[i-1]=='unchanged'):
  proposal[i]=np.nan;status[i]='unknown';reasons[i]='proposal_step_limit'
def clean(v):return [float(x) for x in v] if np.isfinite(v).all() else None
rows=[dict(frame=START+i,raw=clean(raw[i]),proposed=clean(proposal[i]),status=status[i],reason=reasons[i],blob_count=allcounts[i],eligible_blob_count=len(candidates[i]),forward=clean(fw[i]+ORIGIN),backward=clean(bw[i]+ORIGIN),agreement_px=float(agreement[i]) if np.isfinite(agreement[i]) else None) for i in range(N)]
# Merge changed/unknown frames into review episodes with nearby flags combined (<=30 frames).
flag=np.array([s!='unchanged' for s in status]);inds=np.where(flag)[0];episodes=[]
for i in inds:
 if episodes and i-episodes[-1]['last_index']<=30:episodes[-1]['last_index']=int(i)
 else:episodes.append(dict(first_index=int(i),last_index=int(i)))
for k,e in enumerate(episodes):
 lo=e.pop('first_index');hi=e.pop('last_index');e.update(id=f'D4_{k+1:03d}',start=START+lo,end=START+hi,view_start=max(START,START+lo-30),view_end=min(END,START+hi+30),changed_frames=int(sum(s.startswith('proposed') for s in status[lo:hi+1])),unknown_frames=status[lo:hi+1].count('unknown'))
result=dict(run_id=CONFIG['id'],label=CONFIG['label'],selection_reason=CONFIG['reason'],status='COMPLETE_UNREVIEWED' if anchor.any() else 'NO_SUPPORTED_ANCHOR_UNREVIEWED',source_video=str(VIDEO),source_session=str(SESSION),start=START,end=END,fps=30,crop=[X,Y,W,H],rules=RULES,counts={s:status.count(s) for s in sorted(set(status))},anchor_frames=int(anchor.sum()),frames=rows,episodes=episodes)
(R/'RESULTS.json').write_text(json.dumps(result,separators=(',',':')));np.savez_compressed(R/'proposals.npz',raw=raw,proposed=proposal,forward=fw+ORIGIN,backward=bw+ORIGIN,start=START,end=END)
print('RESULTS',result['counts'],'episodes',len(episodes),flush=True)
probe=json.loads(subprocess.check_output([FP,'-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=nb_read_frames,r_frame_rate','-of','json',str(media)]));assert int(probe['streams'][0]['nb_read_frames'])==N
receipt=dict(status=result['status'],config_sha256=sha(R/'CONFIG.json'),source_sha256=sha(VIDEO),blobs_sha256=sha(blobpath),trajectory_sha256=sha(trajpath),code_sha256=sha(Path(__file__)),media_sha256=sha(media),results_sha256=sha(R/'RESULTS.json'),probe=probe,source_inputs_modified=False,limitations=['Development thresholds; not validated','Appearance matching can follow stationary texture','No human decisions or existing releases altered','Unknown proposal does not delete raw position','No new IDtracker job or production correction'])
(R/'RECEIPT.json').write_text(json.dumps(receipt,indent=2));print('COMPLETE',flush=True)
