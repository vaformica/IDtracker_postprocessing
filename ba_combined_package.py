"""Verify uniform recovery, package portable trace-first BA QC, preserve prior release."""
import json,sys,shutil,zipfile,hashlib,os,grp
from pathlib import Path
import numpy as np
from ba_frozen_batch import digest,write
from ba_interpolation import frozen_interpolate

def svg(arrays,crop,method,mask):
 x,y,w,h=crop;s=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="white"/>'
 for a,color in arrays:
  pieces=[];pen=False
  for p in a:
   if not np.isfinite(p).all():pen=False;continue
   pieces.append(('L' if pen else 'M')+f'{p[0]:.2f},{p[1]:.2f}');pen=True
  s+=f'<path d="{" ".join(pieces)}" fill="none" stroke="{color}" stroke-width=".8"/>'
 if arrays:
  a=arrays[-1][0]
  for i,p in enumerate(a):
   if np.isfinite(p).all() and (mask[i] or method[i]=='interpolated'):
    color='#a32dc4' if mask[i] else '#e98c00';s+=f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r=".9" fill="{color}"/>'
 return s+'</svg>' 

def package(root,code):
 root=Path(root);code=Path(code);plan=json.loads((root/'PLAN.json').read_text());rows=[];summaries=[]
 frozen=json.loads((root/'CODE_FREEZE.json').read_text())
 for name,h in frozen['files'].items():assert digest(code/name)==h,name
 assert json.loads((root/'REPRESENTATIVE_ALIGNMENT.json').read_text())['status']=='PASS'
 for source in json.loads((root/'SOURCE_VIDEO_HASHES.json').read_text()):
  st=Path(source['path']).stat();assert st.st_size==source['bytes']
  if st.st_mtime_ns!=source['mtime_ns']:assert digest(source['path'])==source['sha256']
 prior=json.loads((root/'PRIOR_REVIEWS.json').read_text()) if (root/'PRIOR_REVIEWS.json').exists() else {}
 for r in plan['runs']:
  p=root/'runs'/r['id'];m=json.loads((p/'MANIFEST.json').read_text());assert m['encoded_frames']==7200
  assert m['processing_order']==['raw_tracking','frozen_jump_recovery','frozen_BA_interpolation']
  for n,h in m['files'].items():assert digest(p/n)==h,(r['id'],n)
  assert digest(r['trajectory'])==m['input_hashes']['trajectory'];assert digest(r['source_toml'])==r['toml_sha256']
  z=np.load(p/'COORDINATES.npz');xy,method,events,audit=frozen_interpolate(z['baseline'],r['start'],z['protected'],r,collection='BA',number_of_animals=1);assert np.array_equal(xy,z['analysis'],equal_nan=True)
  rec=json.loads((p/'RECOVERY_SUMMARY.json').read_text());assert rec['all_cells_same_recovery_rules'];assert rec['cached_cohort_exact_parity'] is not False
  q=json.loads((p/'QC.json').read_text());strict=np.load(p/'STRICT_ANALYSIS.npz');meta=json.loads((p/'STRICT_QC.json').read_text());assert not (np.linalg.norm(np.diff(strict['analysis'],axis=0),axis=1)>=100).any()
  if q['remaining_jumps']:assert np.isnan(strict['movement_step_px']).all()
  td=json.loads((p/'TURTLING_SCREENING.json').read_text());mask=np.array(td['candidate_mask']);assert not mask[z['protected']|(z['method']=='interpolated')].any()
  if q['remaining_jumps']:assert not mask.any()
  # Full coordinates, no thumbnail decimation. Eight matching layer combinations.
  for k in range(8):
   arrays=[]
   if k&1:arrays.append((z['raw'],'#a4a9ad'))
   if k&2:arrays.append((z['baseline'],'#2583df'))
   if k&4:arrays.append((strict['analysis'],'#008672'))
   (p/f'trace_{k}.svg').write_text(svg(arrays,q['crop'],z['method'],mask))
  shutil.copy2(p/'trace_4.svg',p/'trace.svg')
  d=json.loads((p/'data.js').read_text()[len('window.loadRun('):-2]);d['prior_reviews']=prior.get(r['id'],[])
  if d['prior_reviews']:d['prior_note']=(d.get('prior_note','')+' Earlier attributed review: '+(', '.join(v['reviewer']+' '+v['status'] for v in d['prior_reviews'][:1])+'; '+str(len(d['prior_reviews']))+' earlier records in review notes')+'; applies to the earlier dataset.').strip()
  if r['id']=='ba_030':d['prior_note']=(d.get('prior_note','')+' Known human-scored turtling 1547–8179; earlier frozen detector missed this episode.').strip()
  if r['id']=='ba_060':d['prior_note']=(d.get('prior_note','')+' Known human-scored turtling 3942–7499; earlier frozen detector missed most of this episode.').strip()
  if r['start']==10 and r['label'].endswith('_C5') and r['excluded_frames']:d['prior_note']+=' Source TOML starts at frame10, unlike the other light-exclusion cells; inspect initial setup.'
  (p/'data.js').write_text('window.loadRun('+json.dumps(d,separators=(',',':'),allow_nan=False)+');')
  m['files']={f.name:digest(f) for f in p.iterdir() if f.is_file() and f.name!='MANIFEST.json'};write(p/'MANIFEST.json',m)
  row={**q,'jumps':q['remaining_jumps'],'missing':q['missing_frames'],'excluded':len(q['excluded_frames']),'media':f'runs/{r["id"]}/video.mp4','reasons':[]}
  rows.append(row);summaries.append(rec)
 rows.sort(key=lambda r:(-r['priority'],r['id']))
 fingerprint=hashlib.sha256(json.dumps([(r['id'],digest(root/'runs'/r['id']/'MANIFEST.json')) for r in rows]).encode()).hexdigest()
 index=dict(id='ba-combined221-qc-20261013',hash=fingerprint,runs=rows,status='UNREVIEWED');write(root/'QC_INDEX.json',index);(root/'COMBINED_INDEX.js').write_text('window.COMBINED_INDEX='+json.dumps(index,separators=(',',':'))+';')
 shutil.copy2(code/'ba_combined_review.html',root/'START_HERE.html');shutil.copy2(code/'ba_combined_qc.js',root/'ba_combined_qc.js');(root/'REVIEW_HISTORY.js').write_text('window.QC_REGISTRY_HISTORY={};');shutil.copy2(code/'ba_review_workflow.html',root/'REVIEW_WORKFLOW.html')
 receipt=dict(status='COMPLETE_UNREVIEWED',runs=len(rows),frames=len(rows)*7200,dataset_hash=fingerprint,uniform_recovery_all_cells=True,cached_cohort_exact_parity_runs=sum(s['cached_cohort_exact_parity'] is True for s in summaries),raw_jumps=sum(s['raw_jumps'] for s in summaries),remaining_jumps=sum(r['remaining_jumps'] for r in rows),movement_blocked_runs=sum(r['remaining_jumps']>0 for r in rows),recovered_frames=sum(s['recovered_frames'] for s in summaries),interpolated_frames=sum(r['interpolated_frames'] for r in rows),unexpected_missing_frames=sum(r['missing_frames'] for r in rows),human_excluded_frames=sum(r['excluded'] for r in rows),turtling='FROZEN_0.4_SCREENING_PRE_INTERPOLATION_UNREVIEWED',biological_validation=False,browser_playback='NOT_TOOL_VERIFIED',source_hashes_and_interpolation_replay='PASS')
 assert len(rows)==221 and receipt['cached_cohort_exact_parity_runs']==100
 write(root/'RELEASE_RECEIPT.json',receipt)
 (root/'READ_ME.txt').write_text('BA combined recovery and interpolation QC\n\nExtract this whole folder. Open START_HERE.html. Review traces first; use short or full video when needed. Coverage radio buttons record what you inspected. Request IDTracker rerun records a request, never submits a job. Save a verdict and download ALL QC JSON, including drafts and history. Prior scores remain separate.\n\nEvery cell uses the same frozen jump recovery followed by BA-only interpolation 1.0.0. Raw, recovered and interpolated arrays are retained. STRICT_ANALYSIS.npz masks unresolved jump endpoints and blocks all movement steps for affected runs. It is a separate safety layer, not a verified correction. Never calculate movement on an unapproved jump-blocked run. Human exclusions remain unknown. Automatic turtling uses recovery BEFORE interpolation and is not assessed on jump-blocked runs or interpolated frames. No candidate is not proof of upright posture. Originals and earlier releases remain unchanged.\n')
 zip_path=root.parent/'BA_combined_221_QC.zip'
 with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for p in root.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,'BA_combined_221_QC/'+str(p.relative_to(root)))
 with zipfile.ZipFile(zip_path) as z:assert z.testzip() is None
 write(root.parent/'PACKAGE_RECEIPT.json',dict(zip=zip_path.name,bytes=zip_path.stat().st_size,sha256=digest(zip_path),zip_integrity=True))
 gid=grp.getgrnam('vformic1-swat-lab').gr_gid
 for p in [root,*root.rglob('*'),zip_path,root.parent/'PACKAGE_RECEIPT.json']:os.chown(p,-1,gid);os.chmod(p,0o2770 if p.is_dir() else 0o660)
 print(receipt,flush=True)
if __name__=='__main__':package(sys.argv[1],sys.argv[2])
