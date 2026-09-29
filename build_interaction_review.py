"""Build a local frame-synchronized review with separate raw and inferred evidence."""
import csv,json,itertools
from pathlib import Path
import numpy as np
from trajectory_reconstruction import reconstruct
from reviewed_contacts import apply_reviewed_contacts,follow_detected_pile
from six_beetle_processor import presumed_groups,regions
import processor

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results/OLD_review_moving_piles'
OUT.mkdir(exist_ok=True)
source=ROOT/'results/firebird_inputs/Box01_OLD/trajectories.npy'
xy=np.load(source,allow_pickle=True).item()['trajectories']
r=reconstruct(xy)
g=presumed_groups(r['screened'],60)
annotations=json.loads((ROOT/'annotations/OLD_reviewed_contacts.json').read_text())
display,reviewed,review_partners=apply_reviewed_contacts(g['xy'],annotations,r['accepted'])
blobs=json.loads((ROOT/'results/firebird_inputs/Box01_OLD/blobs_6600_7600.json').read_text())
pile_status=np.full(r['accepted'].shape,'',dtype='<U24')
pile_evidence=[]
reviewed_intervals=[dict(members=[2,5],start=6686,end=6901,seed_frame=6686),
                    dict(members=[4,5],start=7229,end=7506,seed_frame=7227)]
for interval in reviewed_intervals:
 members=interval['members'];start=interval['start'];end=interval['end']
 seed=np.mean(xy[interval['seed_frame'],members],axis=0)
 pile,states,evidence=follow_detected_pile(r['screened'],blobs,members,start,end,seed)
 pile_evidence.extend(dict(members=members,**e) for e in evidence)
 for k,a in enumerate(members):
  display[start:end+1,a]=pile[:,k]
  reviewed[start:end+1,a]=True
  pile_status[start:end+1,a]=states[:,k]
  review_partners[start:end+1,a]=np.where(np.isfinite(pile[:,k]).all(axis=1)&(states[:,k]!='SCREENED_ASSIGNED'),members[1-k],-1)
(OUT/'pile_detection_evidence.json').write_text(json.dumps(pile_evidence,indent=2))
(OUT/'reviewed_pile_intervals.json').write_text(json.dumps(reviewed_intervals,indent=2))
rois=processor.load_rois(ROOT/'results/firebird_inputs/Box01_OLD')
fungus=np.zeros(xy.shape[:2],int)
for a in range(6):
 membership=regions(display[:,a],rois,30,30)
 for f in range(1,4):
  fungus[membership[f'fungus_{f}'],a]=f
pairs=list(itertools.combinations(range(6),2))
pm=[]
for a,b in pairs:
 d=np.linalg.norm(r['screened'][:,a]-r['screened'][:,b],axis=1)
 state=np.where(g['masks'][a,b],2,np.where(d<=60,1,0))
 state[reviewed[:,a]|reviewed[:,b]]=0
 state[((review_partners[:,a]==b)|(review_partners[:,b]==a))&np.isfinite(display[:,a]).all(axis=1)&np.isfinite(display[:,b]).all(axis=1)]=3
 pm.append(state)
def clean(a):
 if isinstance(a,np.ndarray):return clean(a.tolist())
 if isinstance(a,list):return [clean(v) for v in a]
 if isinstance(a,float):return round(a,2) if np.isfinite(a) else None
 return a
payload=dict(start=250,end=16997,fps=30,raw=clean(xy[250:]),held=clean(display[250:]),reviewed=reviewed[250:].astype(int).tolist(),reviewPartners=review_partners[250:].tolist(),annotations=annotations,pileStatus=pile_status[250:].tolist(),
 accepted=r['accepted'][250:].astype(int).tolist(),rejected=r['rejected'][250:].astype(int).tolist(),
 bridge=clean(r['bridge'][250:]),anchors=g['anchors'][250:].tolist(),inferred=g['inferred'][250:].astype(int).tolist(),
 fungus=fungus[250:].tolist(),pairs=pairs,pairStates=np.array(pm)[:,250:].tolist(),rois=clean(rois))
with (OUT/'legacy_hold_positions.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['global_frame','animal_id','accepted','rejected_candidate','held_x','held_y','bridge_x','bridge_y'])
 for t in range(250,len(xy)):
  for a in range(6):w.writerow([t,a,int(r['accepted'][t,a]),int(r['rejected'][t,a]),*r['held'][t,a],*r['bridge'][t,a]])
with (OUT/'display_positions.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['global_frame','animal_id','display_x','display_y','manual_review','manual_partner'])
 for t in range(250,len(xy)):
  for a in range(6):w.writerow([t,a,*display[t,a],int(reviewed[t,a]),review_partners[t,a]])
with (OUT/'reconnections.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(r['connections'][0]));w.writeheader();w.writerows(r['connections'])
summary=dict(speed_limit_px_per_frame=100,confirmation_frames=3,original_step_cutoff_px=200,
 rejected_candidate_frames=int(r['rejected'][250:].sum()),display_missing_coordinate_frames=int((~np.isfinite(display[250:]).all(axis=2)).sum()),
 reviewed_pile_intervals=reviewed_intervals,pile_frame_sources={kind:sum(e['source']==kind for e in pile_evidence) for kind in sorted(set(e['source'] for e in pile_evidence))},
 note='Display uses PSCP detected partner or unique blob; unsupported frames are missing. No held or linearly interpolated positions are displayed. 2-5 frames 6686-6901 and 4-5 frames 7229-7506 are user reviewed; original blob identity labels retained as evidence.')
(OUT/'reconstruction_summary.json').write_text(json.dumps(summary,indent=2))
html=(ROOT/'interaction_review_template.html').read_text().replace('__DATA__',json.dumps(payload,separators=(',',':'),allow_nan=False))
(OUT/'OLD_interaction_review.html').write_text(html)
print(json.dumps(summary,indent=2));print(OUT/'OLD_interaction_review.html')
