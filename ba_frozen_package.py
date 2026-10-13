"""Verify and package a completed frozen BA batch; no source changes."""
from pathlib import Path
import argparse,json,hashlib,shutil,zipfile,grp,os
from ba_frozen_batch import digest,write

def package(root,template):
 root=Path(root);freeze=json.loads((root/'CODE_FREEZE.json').read_text())
 for name in ['ba_interpolation.py','ba_frozen_batch.py','ba_frozen_package.py','ba_frozen_review.html']:
  assert digest(root/'code'/name)==freeze['files'][name],('code changed',name)
 assert (root/'SOURCE_VIDEO_HASHES.json').exists() and (root/'REPRESENTATIVE_ALIGNMENT.json').exists()
 plan=json.loads((root/'PLAN.json').read_text());runs=[];blocked=[]
 for r in plan['runs']:
  p=root/'runs'/r['id'];m=p/'MANIFEST.json'
  if not m.exists():blocked.append(r['id']);continue
  d=json.loads(m.read_text());assert d['encoded_frames']==7200
  for name,h in d['files'].items():assert digest(p/name)==h,(r['id'],name)
  q=json.loads((p/'QC.json').read_text())
  if r['start']==10 and r['label'].endswith('_C5') and r['excluded_frames']:
   q['prior_note']+=' Source TOML starts at frame 10, unlike the other light-exclusion cells; inspect initial setup.'
   q['priority']+=100
  runs.append(q)
 assert not blocked,blocked
 runs.sort(key=lambda r:(-r['priority'],r['id']));fingerprint=hashlib.sha256(json.dumps([dict(id=r['id'],manifest=digest(root/'runs'/r['id']/'MANIFEST.json')) for r in runs],sort_keys=True).encode()).hexdigest()
 write(root/'QC_INDEX.json',dict(dataset_hash=fingerprint,runs=runs))
 (root/'INDEX.js').write_text('const INDEX='+json.dumps(dict(hash=fingerprint,runs=runs),separators=(',',':'))+';')
 shutil.copy2(template,root/'START_HERE.html')
 receipt=dict(status='COMPLETE_UNREVIEWED',runs=len(runs),frames=len(runs)*7200,rules_version='1.0.0',dataset_hash=fingerprint,remaining_jump_runs=sum(r['remaining_jumps']>0 for r in runs),remaining_jumps=sum(r['remaining_jumps'] for r in runs),unexpected_missing_frames=sum(r['missing_frames'] for r in runs),interpolated_frames=sum(r['interpolated_frames'] for r in runs),interpolated_gaps=sum(r['interpolated_gaps'] for r in runs),human_excluded_frames=sum(len(r['excluded_frames']) for r in runs),all_per_run_file_hashes_verified=True,all_mp4s_fully_decoded=True,biological_validation=False,turtling='NOT_ASSESSED',browser_playback='NOT_TOOL_VERIFIED')
 write(root/'RELEASE_RECEIPT.json',receipt)
 (root/'READ_ME.txt').write_text('BA single-animal tracking QC — 13 October 2026\n\nExtract the entire ZIP, then open START_HERE.html. Keep all folders together.\nEnter your name. Runs are sorted by remaining jumps, missing tracking and brightness flags. Skim the trace first; watch footage when needed. Select coverage honestly and record a verdict/category. Download ALL scores before closing and return the JSON file. Other reviewers should keep separate exports. Importing conflicting decisions is blocked so they can be reconciled without overwriting.\n\nOrange positions are interpolated, not observed. Raw, baseline and analysis coordinates remain separate in each run. Human-excluded global frames1608–1609 are never filled. Long gaps remain missing. A usable skim is not a frame-by-frame certification. Flags are not automatic exclusions. This package does not assess turtling.\n\n221 windows span14 recordings; the older121 use raw tracking while the additional100 retain prior recovery proposals. Treat comparisons with that provenance in mind.\n')
 files=[p for p in root.rglob('*') if p.is_file() and p.suffix!='.zip' and 'logs' not in p.parts and '__pycache__' not in p.parts]
 zipfile_path=root/'BA_frozen_221_QC.zip'
 with zipfile.ZipFile(zipfile_path,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
  for p in files:z.write(p,'BA_frozen_221_QC/'+str(p.relative_to(root)))
 with zipfile.ZipFile(zipfile_path) as z:assert z.testzip() is None
 write(root/'PACKAGE_RECEIPT.json',dict(zip=zipfile_path.name,sha256=digest(zipfile_path),bytes=zipfile_path.stat().st_size,zip_integrity=True))
 try:
  gid=grp.getgrnam('vformic1-swat-lab').gr_gid
  for p in [root,*root.rglob('*')]:os.chown(p,-1,gid);os.chmod(p,0o2770 if p.is_dir() else 0o660)
 except KeyError:pass
 print(json.dumps(receipt),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('template');a=p.parse_args();package(a.root,a.template)
