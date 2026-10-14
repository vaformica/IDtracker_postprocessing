"""Prepare a deterministic, scoped review queue from frozen BA pilot results."""
from pathlib import Path
import json,hashlib,random,csv,sys
from ba_large_pilot import load,save,sha,permit

def spans(mask,start=0):
 out=[];a=None
 for i,v in enumerate([*mask,False]):
  if v and a is None:a=i
  if not v and a is not None:out.append([start+a,start+i-1]);a=None
 return out

def build(root):
 plan=load(root/'PLAN.json');results=[load(root/'results'/f"{x['id']}.json") for x in plan['sources']]
 assert len(results)==101 and sum(x['cohort']=='new_run_pilot' for x in results)==100
 good=[x for x in results if x['status']=='ANALYSIS_COMPLETE_UNREVIEWED'];byid={s['id']:s for s in good};rng=random.Random(plan['seed']+1);prediction={}
 for s in good:
  p=root/'runs_v2'/s['id']/'predictions.json';assert sha(p)==s['analysis_output_sha256']['predictions.json'];prediction[s['id']]=load(p)
 blind=[s for s in good if s['blind_full_run']];guided=[s for s in good if not s['blind_full_run'] and s['cohort']=='new_run_pilot'];clips=[]
 def new(s,a,b,mode,reason):
  a=max(s['start'],int(a));b=min(s['end'],int(b));assert a<=b
  c=dict(source_id=s['id'],label=s['id'].upper()+' / '+Path(s['toml']).stem.split('_')[-1],start=a,end=b,frames=b-a+1,fps=30,mode=mode,selection=reason)
  clips.append(c);return c
 blindclips=[new(s,s['start'],s['end'],'blind','preselected_complete_run') for s in blind]
 follow=byid.get('followup_01');followclips=[]
 if follow:followclips=[new(follow,max(follow['start'],7310),follow['end'],'guided','prior_positive_continuation')]
 candidateclips=[]
 for s in sorted(guided,key=lambda s:(-s['candidate_seconds'],s['id'])):
  windows=[]
  for bout in prediction[s['id']]['account']['bouts']:
   a,b=bout['start_global_frame'],bout['end_global_frame_inclusive']
   if b-a+1<=1800:windows.append((max(s['start'],a-150),min(s['end'],b+150)))
   else:
    for center in [a,(a+b)//2,b]:
     start=max(s['start'],min(s['end']-599,center-300));windows.append((start,start+599))
  merged=[]
  for a,b in sorted(windows):
   if merged and a<=merged[-1][1]+1:merged[-1][1]=max(merged[-1][1],b)
   else:merged.append([a,b])
  candidateclips.extend(new(s,a,b,'guided','candidate_boundaries_or_continuity') for a,b in merged)
 # QC remains a review priority, not an exclusion gate.
 qcclips=[];used_recordings=set()
 for s in sorted(guided,key=lambda s:(-s['qc_metrics']['missing_fraction'],-s['qc_metrics']['rejected_jump_steps'],s['id'])):
  if not s['qc_flags'] or s['video'] in used_recordings:continue
  q=load(root/'runs_v2'/s['id']/'qc.json');episodes=q['episodes'];episodes=sorted(episodes,key=lambda e:({'MISSING':0,'REJECTED_JUMP':1,'OUTSIDE_ARENA':2}.get(e['kind'],3),-e['frames']))
  target=(episodes[0]['start_global_frame']+episodes[0]['end_global_frame_inclusive'])//2 if episodes else s['start']+300
  a=max(s['start'],min(s['end']-599,target-300));b=a+599
  if any(c['source_id']==s['id'] and not (b<c['start'] or a>c['end']) for c in clips):continue
  qcclips.append(new(s,a,b,'guided','tracking_or_recovery_qc'));used_recordings.add(s['video'])
  if len(qcclips)>=6:break
 controls=[];controlruns=guided[:];rng.shuffle(controlruns)
 used_runs={c['source_id'] for c in clips}
 for s in controlruns:
  if s['id'] in used_runs:continue
  g=prediction[s['id']]['gate'];mask=g['candidate_mask'];eligible=g['eligible_mask'];unknown=set(g['missing_frames'])
  offsets=[i for i in range(0,6601,30) if not any(mask[i:i+600]) and all(eligible[i:i+600]) and not any(s['start']+j in unknown for j in range(i,i+600))]
  if not offsets:continue
  a=s['start']+rng.choice(offsets);controls.append(new(s,a,a+599,'guided','random_eligible_unflagged_control'))
  if len(controls)>=4:break
 # Four preselected complete runs anchor separate rounds; guided clips fill the shorter rounds.
 rounds=[[c] for c in blindclips] or [[]];queue=followclips[:]
 groups=[candidateclips,qcclips,controls];pos=[0,0,0]
 while any(pos[i]<len(groups[i]) for i in range(3)):
  for i in [0,1,0,2]:
   if pos[i]<len(groups[i]):queue.append(groups[i][pos[i]]);pos[i]+=1
 for c in queue:
  durations=[sum(x['frames'] for x in batch)/30 for batch in rounds];best=min(range(len(rounds)),key=lambda i:durations[i])
  if durations[best]+c['frames']/30>600:rounds.append([c])
  else:rounds[best].append(c)
 clips=[]
 for ri,batch in enumerate(rounds,1):
  for j,c in enumerate(batch,1):
   c.update(id=f'r{ri:02d}_clip_{j:02d}',round=ri);s=byid[c['source_id']];g=prediction[s['id']]['gate'];lo=c['start']-s['start'];hi=lo+c['frames']
   c['suggestions']=spans(g['candidate_mask'][lo:hi],c['start']) if c['mode']=='guided' else []
   c['not_eligible_ranges']=spans([not v for v in g['eligible_mask'][lo:hi]],c['start']) if c['mode']=='guided' else []
   c['tracking_uncertain_ranges']=spans([v=='tracking_uncertain' or v=='camera_reference_unconfirmed' for v in g['state'][lo:hi]],c['start']) if c['mode']=='guided' else []
   c['source_prediction_sha256']=s['analysis_output_sha256']['predictions.json'];clips.append(c)
 # No double-counted review windows within any run.
 for s in good:
  windows=sorted((c['start'],c['end']) for c in clips if c['source_id']==s['id'])
  assert all(b<a2 for (a,b),(a2,b2) in zip(windows,windows[1:])),s['id']
 stats=dict(selected_new_runs=100,completed_new_runs=sum(s['cohort']=='new_run_pilot' for s in good),blocked_new_runs=sum(s['status']!='ANALYSIS_COMPLETE_UNREVIEWED' and s['cohort']=='new_run_pilot' for s in results),new_runs_with_candidates=sum(s['candidate_seconds']>0 and s['cohort']=='new_run_pilot' for s in good),new_runs_with_qc_flags=sum(bool(s['qc_flags']) and s['cohort']=='new_run_pilot' for s in good),source_recordings=len({s['video'] for s in good if s['cohort']=='new_run_pilot'}),clips=len(clips),rounds=len(rounds),viewing_seconds=sum(c['frames']/30 for c in clips),blind_full_runs=len(blindclips),candidate_clips=len(candidateclips),qc_clips=len(qcclips),random_controls=len(controls),prior_followup_clips=len(followclips))
 save(root/'ANALYSIS_INDEX.json',dict(status='FROZEN_ANALYSIS_UNREVIEWED',stats=stats,runs=results))
 save(root/'REVIEW_QUEUE.json',dict(schema='ba-large-review-queue-v1',seed=plan['seed']+1,stats=stats,clips=clips,rounds=[[c['id'] for c in r] for r in rounds],limitations='Cell-level development check across previously represented recordings; short scenes approve only displayed frames. Guided selection is not an unbiased accuracy sample.'))
 fields=['id','status','toml','candidate_seconds','bout_count','longest_bout_seconds','recovery_status','qc_flags','reason']
 with (root/'RUN_INDEX.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for s in results:
   row={k:s.get(k,'') for k in fields};row['qc_flags']=';'.join(row['qc_flags']) if isinstance(row['qc_flags'],list) else row['qc_flags'];w.writerow(row)
 permit(root/'RUN_INDEX.csv');print(json.dumps(stats,indent=2),flush=True)
if __name__=='__main__':build(Path(sys.argv[1]))
