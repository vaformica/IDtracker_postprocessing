from pathlib import Path
import sys,json,shutil,os,grp,zipfile,html as html_module
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'code'))
import cv2,numpy as np
from ba_frozen_batch import digest,write
from package_reruns import package
D=R/'delivery';plan=json.loads((D/'PLAN.json').read_text());samples=[]
for r in plan['runs']:
 p=D/'runs'/r['id'];q=json.loads((p/'QC.json').read_text());x,y,w,h=q['crop'];src=cv2.VideoCapture(r['video']);dst=cv2.VideoCapture(str(p/'video.mp4'))
 for i in [0,3600,7199]:
  src.set(cv2.CAP_PROP_POS_FRAMES,r['start']+i);ok,a=src.read();dst.set(cv2.CAP_PROP_POS_FRAMES,i);ok2,b=dst.read();assert ok and ok2
  crop=a[y:y+h,x:x+w];assert crop.shape==b.shape
  mae=float(np.abs(crop.astype(float)-b.astype(float)).mean());assert mae<12,(r['id'],i,mae)
  samples.append(dict(id=r['id'],global_frame=r['start']+i,mean_absolute_pixel_difference=mae))
 src.release();dst.release()
write(D/'REPRESENTATIVE_ALIGNMENT.json',dict(status='PASS',samples=samples))
shutil.copytree(R/'code',D/'code')
package(D,R/'code')
# Add an exact rerun crosswalk and historical decisions without applying them.
write(D/'RERUN_CROSSWALK.json',dict(new_dataset=json.loads((D/'QC_INDEX.json').read_text())['hash'],runs=[dict(id=r['id'],source_toml=r['savannah_source_path'],source_sha256=r['savannah_source_sha256'],submitted_toml=r['submission_toml'],submitted_sha256=r['submission_sha256'],prior_source=r['prior_source'],prior_reviews=r['prior_reviews'],new_window=[r['start'],r['end']],tracking_status=json.loads((R/'tracking_v2'/r['id']/'status.json').read_text())) for r in plan['runs']],skipped=plan['blocked'],missing=plan['missing']))
html=(D/'START_HERE.html').read_text().replace('BA_combined221_QC_20261013','BA_Savannah_reruns11_QC_20261014')
html=html.replace('<h1>BA combined recovery + interpolation QC</h1>','<h1>Savannah’s BA reruns · 14 October 2026</h1>')
html=html.replace('<header>', '<header><p>11 new tracking runs from Savannah’s revised TOMLs. Earlier decisions are history; each replacement needs fresh QC. BA_065 was skipped at Vince’s request; NEW_093 has no revised TOML. <a href="RERUN_CROSSWALK.json">TOMLs, prior decisions and tracking records</a></p>',1)
oldroot=Path('/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_combined_recovery_221_20261013/delivery/runs')
comparison=['<!doctype html><meta charset="utf-8"><title>BA reruns: previous and new</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto}article{border-top:1px solid #aaa;padding:20px 0}.plots{display:flex;gap:20px}.plots figure{width:45%;margin:0}img{width:100%;max-height:380px}</style><h1>Previous and replacement BA traces</h1><p>Historical decisions are context, not approval of new tracking. Both plots show strict tracks, which omit unresolved jump endpoints. Check counts and video before judging a trace. Windows and arena geometry may differ.</p><p><a href="START_HERE.html">Open new QC queue</a> · <a href="RERUN_CROSSWALK.json">Full source and reviewer provenance</a></p>']
for r in plan['runs']:
 rid=r['id'];old=oldroot/rid;dest=D/'previous'/rid;dest.mkdir(parents=True,exist_ok=True)
 for name in ['trace.svg','QC.json','MANIFEST.json']:shutil.copy2(old/name,dest/name)
 before=json.loads((old/'QC.json').read_text());after=json.loads((D/'runs'/rid/'QC.json').read_text())
 review='; '.join(v['reviewer']+': '+v['review_status']+' — '+v['review_comments'] for v in r['prior_reviews'])
 comparison.append(f'<article><h2>{html_module.escape(rid.upper()+" — "+r["label"])}</h2><p>Earlier decision: {html_module.escape(review)}</p><div class="plots"><figure><figcaption>Previous: frames {before["start"]}–{before["end"]}; {before["missing_frames"]} missing; {before["remaining_jumps"]} large jumps</figcaption><img src="previous/{rid}/trace.svg"></figure><figure><figcaption>Replacement: frames {after["start"]}–{after["end"]}; {after["missing_frames"]} missing; {after["remaining_jumps"]} large jumps</figcaption><img src="runs/{rid}/trace.svg"></figure></div></article>')
(D/'BEFORE_AFTER.html').write_text('\n'.join(comparison))
html=html.replace('<header>','<header><p><a href="BEFORE_AFTER.html">Compare previous and new traces and decisions</a></p>',1)
(D/'START_HERE.html').write_text(html)
shutil.copytree(R/'inputs',D/'input_tomls')
(D/'orchestration').mkdir()
for p in [*R.glob('*.py'),*R.glob('*.sbatch')]:shutil.copy2(p,D/'orchestration'/p.name)
for name in ['TRACKING_PLAN.json','DISCOVERY.json','SUBMISSION_RECEIPT.json','SUBMISSION_RECEIPT_v2.json','PREFLIGHT.json']:shutil.copy2(R/name,D/name)
write(D/'DELIVERY_HASHES.json',{str(p.relative_to(D)):digest(p) for p in D.rglob('*') if p.is_file() and p.name!='DELIVERY_HASHES.json' and '__pycache__' not in p.parts})
zp=R/'BA_Savannah_reruns11_QC_20261014.zip'
with zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for p in D.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:z.write(p,'BA_Savannah_reruns11_QC_20261014/'+str(p.relative_to(D)))
with zipfile.ZipFile(zp) as z:assert z.testzip() is None
write(R/'PACKAGE_RECEIPT.json',dict(status='COMPLETE_UNREVIEWED',zip=zp.name,sha256=digest(zp),bytes=zp.stat().st_size,runs=11))
gid=grp.getgrnam('vformic1-swat-lab').gr_gid
for p in [R,*R.rglob('*')]:
 os.chown(p,-1,gid);os.chmod(p,0o2770 if p.is_dir() else 0o660)
print('RERUNS READY FOR HUMAN QC',flush=True)
