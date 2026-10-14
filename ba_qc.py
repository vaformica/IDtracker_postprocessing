"""Descriptive BA QC: provisional review flags, never automatic exclusions."""
import numpy as np
import processor

VERSION='ba-qc-pilot-v1'
THRESHOLDS=dict(missing_fraction=.05,longest_missing_frames=120,rejected_jump_fraction=.01,
                outside_arena_fraction=.01,exact_stationary_run_frames=600)

def longest(mask):
    return max((e['frames'] for e in processor._events_from_mask(np.asarray(mask,bool))),default=0)

def summarize(frames,summary):
    known=np.array([r['location_known'] for r in frames],bool)
    jumps=np.array([r['rejected_jump_step'] for r in frames],bool)
    outside=np.array([r['location_known'] and not r['in_arena'] for r in frames],bool)
    stationary=np.array([r['step_from_previous_accepted'] and r['step_distance_px']==0 for r in frames],bool)
    possible=sum(known[:-1]&known[1:])
    metrics=dict(frame_count=len(frames),missing_fraction=float((~known).mean()),
        longest_missing_frames=longest(~known),missing_bouts=len(processor._events_from_mask(~known)),
        rejected_jump_steps=int(jumps.sum()),rejected_jump_fraction=float(jumps.sum()/possible) if possible else None,
        outside_arena_fraction=float(outside.sum()/known.sum()) if known.any() else None,
        exact_stationary_run_frames=longest(stationary)+1 if stationary.any() else 0,
        baseline_missing=not bool(known[0]),wake_status=summary['wake_status'] if 'wake_status' in summary else summary.get('latency_status',''),
        turtling_candidate_frames=sum(r['turtling_candidate'] for r in frames))
    flags=[name.upper() for name,limit in THRESHOLDS.items() if metrics[name] is not None and metrics[name]>limit]
    if metrics['baseline_missing']:flags.append('BASELINE_MISSING')
    if summary.get('threshold_crossing_global_frame','')=='':flags.append('NO_RELIABLE_WAKE')
    episodes=[]
    for kind,mask in [('MISSING',~known),('REJECTED_JUMP',jumps),('OUTSIDE_ARENA',outside),('EXACT_STATIONARY',stationary)]:
        for e in processor._events_from_mask(mask):
            if kind=='EXACT_STATIONARY' and e['frames']+1<=THRESHOLDS['exact_stationary_run_frames']:continue
            episodes.append(dict(kind=kind,start_global_frame=frames[e['start_offset']]['global_frame'],
                end_global_frame_inclusive=frames[e['end_offset']]['global_frame'],frames=e['frames']))
    return dict(schema=VERSION,qc_status='UNREVIEWED',thresholds=THRESHOLDS,metrics=metrics,flags=flags,
        interpretation='Provisional review thresholds, not validated exclusion criteria. Stationarity and absent wake can be real behavior. Trajectory flags do not establish defective source video.',episodes=episodes)
