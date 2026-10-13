"""Apply the same frozen recovery gates to every BA cell, before interpolation."""
import json,sys,subprocess,shutil,tomllib,hashlib
from pathlib import Path
import numpy as np,cv2
from ba_excursion_recovery import propose as excursions
from ba_stationary_reacquisition import propose as stationary
from ba_major_jump_recovery import segments
from ba_frozen_batch import digest,write,run as export_run

def recovery_policy(raw,start,protected):
 windows=[]
 for i in np.flatnonzero(np.linalg.norm(np.diff(raw,axis=0),axis=1)>100):
  lo=max(0,int(i)-30);hi=min(len(raw)-1,int(i)+31)
  if windows and lo<=windows[-1][1]+1:windows[-1][1]=max(hi,windows[-1][1])
  else:windows.append([lo,hi])
 keep=[];skipped=[]
 for lo,hi in windows:
  if hi-lo+1>180:skipped.append([start+lo,start+hi]);continue
  for a,b in segments(~protected[lo:hi+1]):keep.append([lo+a,lo+b])
 return keep,skipped

def recover(raw,candidates,forward,backward,statuses,images,origin,start,protected):
 out,changed,audit=excursions(raw,candidates,forward,backward,statuses,images,origin);episode=out.copy();windows,skipped=recovery_policy(raw,start,protected);checks=[]
 for lo,hi in windows:
  if np.isfinite(raw[lo:hi]).all(1).mean()<.95:checks.append(dict(start=start+lo,end=start+hi-1,status='insufficient_original_coverage'));continue
  proposed,check=stationary(out[lo:hi],images[lo:hi],origin,protected=changed[lo:hi]);out[lo:hi]=proposed;checks.append(dict(start=start+lo,end=start+hi-1,audit=check))
 assert np.array_equal(out[changed],episode[changed],equal_nan=True)
 assert np.array_equal(np.isfinite(out).all(1),np.isfinite(raw).all(1))
 assert not np.isfinite(out[protected]).any()
 old=np.linalg.norm(np.diff(raw,axis=0),axis=1)>100;new=np.linalg.norm(np.diff(out,axis=0),axis=1)>100
 assert not np.any(new&~old)
 return out,dict(excursion=audit,stationary=checks,skipped_long_stationary_windows=skipped)

def run(root,index):
 root=Path(root);config=json.loads((root/'PLAN.json').read_text())['runs'][index];rid=config['id'];p=root/'work'/rid;p.mkdir(parents=True,exist_ok=True)
 assert not (root/'delivery'/'runs'/rid/'MANIFEST.json').exists(),'Completed outputs are immutable'
 assert digest(config['source_toml'])==config['toml_sha256'];t=tomllib.loads(Path(config['source_toml']).read_text());assert type(t['number_of_animals']) is int and t['number_of_animals']==1 and len(t['roi_list'])==1
 raw_all=np.load(config['trajectory'],allow_pickle=True).item()['trajectories'];assert raw_all.shape[1:]==(1,2);raw=raw_all[config['start']:config['end']+1,0].astype(float);assert raw.shape==(7200,2)
 protected=np.isin(np.arange(config['start'],config['end']+1),config['excluded_frames']);assert not np.isfinite(raw[protected]).any();write(p/'CONFIG.json',config)
 source_hash=digest(config['trajectory']);blob=Path(config['session'])/'preprocessing/list_of_blobs.pickle';assert blob.is_file()
 cache=config.get('candidate_cache');cache_hashes={}
 if cache:
  cache=Path(cache);oldreceipt=json.loads((cache/'RECEIPT.json').read_text());assert oldreceipt['trajectory_sha256']==source_hash and oldreceipt['blobs_sha256']==digest(blob)
  for name,key in [('full_window.mp4','media_sha256'),('RESULTS.json','results_sha256')]:assert digest(cache/name)==oldreceipt[key],name
  for name in ['proposals.npz','RESULTS.json','full_window.mp4','RECEIPT.json']:
   cache_hashes[name]=digest(cache/name);shutil.copy2(cache/name,p/name)
 else:subprocess.run([sys.executable,str(Path(__file__).with_name('ba_recovery_candidates.py')),rid,str(root/'work')],check=True)
 a=np.load(p/'proposals.npz');d=json.loads((p/'RESULTS.json').read_text());assert np.array_equal(raw,a['raw'],equal_nan=True);assert d['start']==config['start'] and d['end']==config['end']
 cap=cv2.VideoCapture(str(p/'full_window.mp4'));images=[]
 while True:
  ok,im=cap.read()
  if not ok:break
  images.append(cv2.cvtColor(im,cv2.COLOR_BGR2GRAY))
 cap.release();assert len(images)==7200
 out,audit=recover(raw,a['proposed'],a['forward'],a['backward'],[f['status'] for f in d['frames']],images,d['crop'][:2],config['start'],protected)
 parity=None
 if cache:
  old=np.load(cache/'FINAL.npz');parity=bool(np.array_equal(out,old['proposed'],equal_nan=True));assert parity,'Cached-cohort recovery replay changed'
 np.savez_compressed(p/'FINAL.npz',raw=raw,proposed=out,start=config['start'],end=config['end']);write(p/'RECOVERY_AUDIT.json',audit)
 summary=dict(id=rid,status='RECOVERY_COMPLETE_UNREVIEWED',raw_jumps=int((np.linalg.norm(np.diff(raw,axis=0),axis=1)>=100).sum()),recovered_jumps=int((np.linalg.norm(np.diff(out,axis=0),axis=1)>=100).sum()),recovered_frames=int((np.isfinite(out).all(1)&np.any(out!=raw,axis=1)).sum()),cached_cohort_exact_parity=parity,source_trajectory_sha256=source_hash,blob_sha256=digest(blob),cache_hashes=cache_hashes,all_cells_same_recovery_rules=True)
 write(p/'RECOVERY_SUMMARY.json',summary);(p/'review').mkdir(exist_ok=True);write(p/'review/REVIEW_DATA.json',dict(clips=[dict(crop=d['crop'])]));del images
 export_run(root/'delivery',index)
 dest=root/'delivery'/'runs'/rid
 for name in ['RECOVERY_AUDIT.json','RECOVERY_SUMMARY.json']:shutil.copy2(p/name,dest/name)
 # Output method names distinguish this new recovery pass from the previous package.
 q=json.loads((dest/'QC.json').read_text());q['recovery_applied']=True;q['recovered_frames']=summary['recovered_frames'];q['prior_note']=q.get('prior_note','');write(dest/'QC.json',q)
 data=json.loads((dest/'data.js').read_text()[len('window.loadRun('):-2]);data.update(q);(dest/'data.js').write_text('window.loadRun('+json.dumps(data,separators=(',',':'))+');')
 m=json.loads((dest/'MANIFEST.json').read_text());m.update(processing_order=['raw_tracking','frozen_jump_recovery','frozen_BA_interpolation'],recovery_summary=summary);m['files']={f.name:digest(f) for f in dest.iterdir() if f.is_file() and f.name!='MANIFEST.json'};write(dest/'MANIFEST.json',m)
 assert digest(config['trajectory'])==source_hash
 print('COMBINED',summary,flush=True)
if __name__=='__main__':run(sys.argv[1],int(sys.argv[2]))
