"""Separate strict movement gate and frozen posture hints for combined BA QC.
Posture uses recovered coordinates BEFORE interpolation. Unknowns remain explicit.
"""
import json,sys
from pathlib import Path
import numpy as np
from ba_frozen_batch import digest,write
from ba_strict_jump_qc import gate
from ba_turtling_diagnostics import window_features,gate_passes,mask_from_windows
from ba_turtling_episode_experiment import experiment
from ba_turtling_recovery_gate import gate_candidates
from ba_turtling_continuity_experiment import refine,segments
from ba_turtling_boundary_experiment import refine_boundaries

def layers(p):
 p=Path(p);z=np.load(p/'COORDINATES.npz');start=int(z['start']);end=int(z['end']);n=len(z['analysis']);assert n==7200
 strict,movement,meta=gate(z['analysis'],start)
 np.savez_compressed(p/'STRICT_ANALYSIS.npz',analysis=strict,movement_step_px=movement,start=start,end=end,method=z['method'],protected=z['protected'])
 write(p/'STRICT_QC.json',meta)
 xy=z['baseline'];mask=np.zeros(n,bool);state=np.full(n,'not_assessed_tracking',object)
 if meta['human_run_review_required']:state[:]='not_assessed_jump_block'
 else:
  f=window_features(xy);base=mask_from_windows(xy,gate_passes(f).all(1));exp=experiment(xy,base,start,features=f);g=gate_candidates(exp['episode_mask'],xy,start)
  prev=refine(xy,g['candidate_mask'],g['eligible_mask'],start);result=refine_boundaries(xy,prev['candidate_mask'],g['eligible_mask'],start)
  finite=np.isfinite(xy).all(1);eligible=np.asarray(g['eligible_mask'])&finite
  state[finite&~eligible]='not_assessed_recovery';state[eligible]='no_candidate_detected';mask=np.asarray(result['candidate_mask'])&eligible;state[mask]='candidate_detected'
 state[z['method']=='interpolated']='not_assessed_interpolated';state[z['protected']]='not_assessed_excluded';mask[z['protected']|(z['method']=='interpolated')]=False
 turtle=dict(version='frozen-0.4-on-recovered-before-interpolation-v1',status='UNREVIEWED',input_sha256=digest(p/'COORDINATES.npz'),input_layer='baseline (recovered, before interpolation)',candidate_mask=mask.tolist(),state=state.tolist(),bouts=[[start+int(a),start+int(b)-1] for a,b in segments(mask)],warning='Screening only; may miss quiet on-back episodes. Interpolated frames are not posture evidence.')
 write(p/'TURTLING_SCREENING.json',turtle)
 q=json.loads((p/'QC.json').read_text());q.update(strict_uncertain_frames=len(meta['uncertain_frames']),movement_status=meta['movement_status'],turtling_status='UNREVIEWED_SCREENING',turtling_candidate_frames=int(mask.sum()),turtling_assessed_frames=int(np.isin(state,['candidate_detected','no_candidate_detected']).sum()));write(p/'QC.json',q)
 data=json.loads((p/'data.js').read_text()[len('window.loadRun('):-2]);data.update(q);data['strict']={**meta,'analysis':[v.tolist() if np.isfinite(v).all() else [None,None] for v in strict]};data['turtling']=turtle
 (p/'data.js').write_text('window.loadRun('+json.dumps(data,separators=(',',':'),allow_nan=False)+');')
 m=json.loads((p/'MANIFEST.json').read_text());m['files']={f.name:digest(f) for f in p.iterdir() if f.is_file() and f.name!='MANIFEST.json'};m['separate_layers']=['strict movement gate 0.1.0','frozen turtling screening on pre-interpolation recovery'];write(p/'MANIFEST.json',m)
 return q
if __name__=='__main__':
 root=Path(sys.argv[1]);r=json.loads((root/'PLAN.json').read_text())['runs'][int(sys.argv[2])];print(layers(root/'runs'/r['id']))
