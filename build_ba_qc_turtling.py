"""Versioned frozen-rule BA screening on strict review tracks, not production."""
from pathlib import Path
import json,hashlib
import numpy as np
from ba_turtling_diagnostics import window_features,gate_passes,mask_from_windows
from ba_turtling_episode_experiment import experiment
from ba_turtling_recovery_gate import gate_candidates
from ba_turtling_continuity_experiment import refine,segments
from ba_turtling_boundary_experiment import refine_boundaries
R=Path(__file__).resolve().parent/'outputs/ba_human_qc_20261013'
O=R/'turtling_v1';O.mkdir(exist_ok=True)
summary=[]
for row in json.loads((R/'index.json').read_text())['runs']:
 rid=row['id'];p=R/'strict_v1'/f'{rid}.npz';z=np.load(p);xy=z['analysis'];start=int(z['start']);n=len(xy)
 strict=json.loads((R/'strict_v1'/f'{rid}.json').read_text())
 state=np.full(n,'not_assessed_tracking',object);mask=np.zeros(n,bool)
 if not strict['human_run_review_required']:
  f=window_features(xy);base=mask_from_windows(xy,gate_passes(f).all(1))
  exp=experiment(xy,base,start,features=f);g=gate_candidates(exp['episode_mask'],xy,start)
  prev=refine(xy,g['candidate_mask'],g['eligible_mask'],start)
  result=refine_boundaries(xy,prev['candidate_mask'],g['eligible_mask'],start)
  eligible=np.array(g['eligible_mask'])&np.isfinite(xy).all(1)
  state[eligible]='no_candidate_detected';mask=np.array(result['candidate_mask']);state[mask]='candidate_detected'
  state[np.isfinite(xy).all(1)&~np.array(g['eligible_mask'])]='not_assessed_recovery'
 else:state[:]='not_assessed_jump_block'
 out=dict(version='frozen-0.4-rules-on-strict-track-v1',status='UNREVIEWED',input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),start=start,end=int(z['end']),candidate_mask=mask.tolist(),state=state.tolist(),bouts=[[start+int(a),start+int(b)-1] for a,b in segments(mask)],warning='Fresh application of frozen development rules to proposed strict coordinates; no candidate is not proof of upright posture.')
 (O/f'{rid}.json').write_text(json.dumps(out,separators=(',',':')))
 summary.append(dict(id=rid,bouts=out['bouts'],candidate_frames=int(mask.sum()),assessed_frames=int(np.isin(state,['candidate_detected','no_candidate_detected']).sum())))
 print(rid,len(out['bouts']),flush=True)
(O/'SUMMARY.json').write_text(json.dumps(summary,indent=2))
