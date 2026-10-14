from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R/'code'))
from ba_frozen_batch import digest,write
p=json.loads((R/'TRACKING_PLAN.json').read_text());delivery=R/'delivery';delivery.mkdir(exist_ok=True)
for r in p['runs']:
 s=json.loads((R/'tracking'/r['id']/'status.json').read_text());assert s['stage']=='COMPLETE_UNREVIEWED'
 r.update({k:s[k] for k in ['session','trajectory','trajectory_sha256','session_sha256']})
 r['idtracker_exit_warning']=s['exit_warning']
write(R/'PLAN.json',p);write(delivery/'PLAN.json',p)
old=json.loads(Path('/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/ba_combined_recovery_221_20261013/SOURCE_VIDEO_HASHES.json').read_text());records=[]
for video in sorted({r['video'] for r in p['runs']}):
 f=Path(video);s=f.stat();prior=next((v for v in old if v['path']==video and v['bytes']==s.st_size and v['mtime_ns']==s.st_mtime_ns),None)
 records.append(prior or dict(path=video,bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=digest(f)))
write(R/'SOURCE_VIDEO_HASHES.json',records);write(delivery/'SOURCE_VIDEO_HASHES.json',records)
shutil.copy2(R/'CODE_FREEZE.json',delivery/'CODE_FREEZE.json')
prior={}
for r in p['runs']:
 prior[r['id']]=[dict(reviewer=v['reviewer'],at=v['reviewed_at'],status=v['review_status'],scope=v['review_scope'],errors=v['possible_flags'].split(';') if v['possible_flags'] else [],notes=v['review_comments'],original_registry_record=v) for v in r['prior_reviews']]
write(delivery/'PRIOR_REVIEWS.json',prior)
print('Processing plan prepared',len(p['runs']))
