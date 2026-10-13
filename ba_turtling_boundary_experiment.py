"""BA 0.4 development: bounded onset search and directed-exit evidence.

Consumes the frozen 0.3 result, not human scores. All added/removed frames retain
separate evidence. This is an offline movement hypothesis, not observed posture.
"""
from dataclasses import dataclass,asdict
import numpy as np
from ba_turtling_continuity_experiment import segments
VERSION='0.4.0-development'
@dataclass(frozen=True)
class Rules:
    onset_lookback_frames:int=300
    onset_reference_frames:int=30
    onset_radius_px:float=35.
    max_step_px:float=20.
    exit_window_frames:int=30
    exit_net_px:float=30.
    exit_efficiency:float=.85
    exit_confirmation_windows:int=5
    exit_search_frames:int=120

def refine_boundaries(xy,previous_mask,eligible_mask,start=0,rules=Rules()):
    a=np.asarray(xy,float);old=np.asarray(previous_mask,bool);eligible=np.asarray(eligible_mask,bool)
    if a.ndim!=2 or a.shape[1]!=2 or old.shape!=(len(a),) or eligible.shape!=old.shape:raise ValueError('Mismatched inputs')
    params=asdict(rules)
    if any(not np.isfinite(v) or v<=0 for v in params.values()) or rules.exit_efficiency>1:raise ValueError('Invalid parameters')
    for key in ['onset_lookback_frames','onset_reference_frames','exit_window_frames','exit_confirmation_windows','exit_search_frames']:
        if type(params[key]) is not int:raise ValueError('Frame settings must be integers')
    if rules.exit_window_frames<3:raise ValueError('Exit window too short')
    known=np.isfinite(a).all(1)
    if np.any(old&(~known|~eligible)):raise ValueError('Prior mask violates tracking/recovery gate')
    mask=old.copy();evidence=np.full(len(a),'unchanged_03',object);audit=[]
    # Backward extension stops at the earliest tracking gap, jump or spatial
    # departure; it cannot backfill the death feint or follow a drifting center.
    for lo,hi in segments(old):
        if hi-lo<120:continue
        center=np.median(a[lo:min(hi,lo+rules.onset_reference_frames)],axis=0)
        j=lo-1;lower=max(0,lo-rules.onset_lookback_frames)
        while j>=lower and not old[j]:
            if (not known[j] or not eligible[j] or np.linalg.norm(a[j]-center)>rules.onset_radius_px
                or np.linalg.norm(a[j+1]-a[j])>rules.max_step_px):break
            mask[j]=True;evidence[j]='bounded_pre_anchor_continuation_hypothesis';j-=1
        if j+1<lo:audit.append(dict(kind='onset_extension',first_global_frame=int(start+j+1),last_global_frame=int(start+lo-1)))
    # A sustained efficient departure near the prior episode end is evidence
    # against continuing the on-back hypothesis. The search is retrospective.
    for lo,hi in segments(old):
        streak=0;first=None
        for j in range(max(lo,hi-rules.exit_search_frames),min(len(a)-rules.exit_window_frames+1,hi+1)):
            b=a[j:j+rules.exit_window_frames];steps=np.linalg.norm(np.diff(b,axis=0),axis=1)
            net=np.linalg.norm(b[-1]-b[0]);path=steps.sum()
            passed=(np.isfinite(b).all() and np.max(steps)<=rules.max_step_px and net>=rules.exit_net_px and path>0 and net/path>=rules.exit_efficiency)
            streak=streak+1 if passed else 0
            if streak>=rules.exit_confirmation_windows:first=j-streak+1;break
        if first is not None:
            end=hi
            while end<len(mask) and mask[end] and not old[end]:end+=1
            mask[first:end]=False;evidence[first:end]='directed_departure_boundary_hypothesis'
            audit.append(dict(kind='directed_departure_trim',first_global_frame=int(start+first),last_global_frame=int(start+end-1)))
    evidence[~known]='tracking_unknown';evidence[~eligible&known]='recovery_not_established'
    return dict(version=VERSION,status='DEVELOPMENT_FIT_UNVALIDATED',rules=params,candidate_mask=mask.tolist(),evidence=evidence.tolist(),adjustments=audit,confirmed_overturned_seconds=None)
