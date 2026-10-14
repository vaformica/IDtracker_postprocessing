"""Read-only BA review sidecars. Heuristic priorities, not error probabilities.

Consumes raw coordinates and frozen 0.3/0.4 evidence. Does not reconstruct paths,
classify posture, or exclude runs. Frame intervals are inclusive global frames.
"""
from dataclasses import dataclass, asdict
import numpy as np

VERSION = 'ba-review-priority-0.1.0'

@dataclass(frozen=True)
class Rules:
    missing_fraction: float = .05
    missing_gap_frames: int = 120
    jump_px: float = 100.
    severe_jump_px: float = 200.
    repeated_jumps: int = 3
    candidate_fraction: float = .25
    long_candidate_frames: int = 1800
    long_continuation_frames: int = 300
    stationary_frames: int = 600


def intervals(mask, start):
    e = np.diff(np.r_[False, np.asarray(mask, bool), False].astype(int))
    return [[int(a+start), int(b+start-1)] for a,b in zip(np.flatnonzero(e==1),np.flatnonzero(e==-1))]


def assess(xy, start, eligible, previous, current, *, fps=30, camera_artifacts=(), rules=Rules()):
    xy=np.asarray(xy,float);n=len(xy)
    if xy.shape!=(n,2) or not n or not np.isfinite(fps) or fps<=0:raise ValueError('Expected nonempty Nx2 coordinates and positive fps')
    if type(start) is not int:raise ValueError('Integer global start required')
    if any(not np.isfinite(v) or v<=0 for v in asdict(rules).values()) or rules.severe_jump_px<rules.jump_px:raise ValueError('Invalid review thresholds')
    if rules.missing_fraction>1 or rules.candidate_fraction>1:raise ValueError('Fractions exceed one')
    for key in ['missing_gap_frames','repeated_jumps','long_candidate_frames','long_continuation_frames','stationary_frames']:
        if type(getattr(rules,key)) is not int:raise ValueError('Frame/count thresholds must be integers')
    if previous.get('version')!='0.3.0-development' or current.get('version')!='0.4.0-development':raise ValueError('Expected frozen 0.3 and 0.4 evidence')
    eligible=np.asarray(eligible,bool);p3=np.asarray(previous['candidate_mask'],bool);p4=np.asarray(current['candidate_mask'],bool);amb=np.asarray(previous['ambiguous_loop_mask'],bool);e3=np.asarray(previous['evidence'],object);e4=np.asarray(current['evidence'],object)
    if any(x.shape!=(n,) for x in [eligible,p3,p4,amb,e3,e4]):raise ValueError('Misaligned evidence')
    known=np.isfinite(xy).all(1)
    if np.any(p4&(~known|~eligible)):raise ValueError('Candidate violates known/eligible gate')
    missing=intervals(~known,start);candidate=intervals(p4,start);step=np.full(n,np.nan)
    pairs=known[:-1]&known[1:];offsets=np.flatnonzero(pairs)+1
    step[offsets]=np.linalg.norm(xy[offsets]-xy[offsets-1],axis=1)
    jumps=[dict(from_global_frame=int(start+i-1),to_global_frame=int(start+i),distance_px=float(step[i])) for i in np.flatnonzero(step>rules.jump_px)]
    gap_returns=[]
    for a,b in missing:
        left=a-start-1;right=b-start+1
        if left>=0 and right<n and known[left] and known[right]:
            distance=float(np.linalg.norm(xy[right]-xy[left]))
            if distance>rules.jump_px:gap_returns.append(dict(before_gap_frame=start+left,after_gap_frame=start+right,missing_start=a,missing_end=b,displacement_px=distance))
    continuation=p4&((e3=='localized_continuation_hypothesis')|(e4=='bounded_pre_anchor_continuation_hypothesis'))
    continuation_spans=intervals(continuation,start);amb_spans=intervals(amb,start);changed=p3!=p4
    capped=[];trimmed=[]
    for a in current.get('adjustments',[]):
        lo=a['first_global_frame'];hi=a['last_global_frame'];assert start<=lo<=hi<start+n
        if a['kind']=='onset_extension' and hi-lo+1>=current['rules']['onset_lookback_frames']:
            capped.append(dict(first_candidate_frame=lo,review_earlier_than=lo,search_limit_frames=current['rules']['onset_lookback_frames']))
        elif a['kind']=='directed_departure_trim':trimmed.append([lo,hi])
    # Evidence at an event edge can be truncated by tracking/recovery rather than righting.
    edges=[]
    for a,b in candidate:
        lo=a-start;hi=b-start;reasons=[]
        if lo==0:reasons.append('analysis_start')
        elif not known[lo-1]:reasons.append('missing_before_onset')
        elif not eligible[lo-1]:reasons.append('recovery_gate_before_onset')
        elif step[lo]>rules.jump_px:reasons.append('jump_at_onset')
        if hi==n-1:reasons.append('analysis_end')
        elif not known[hi+1]:reasons.append('missing_after_end')
        elif not eligible[hi+1]:reasons.append('recovery_gate_after_end')
        elif step[hi+1]>rules.jump_px:reasons.append('jump_after_end')
        if reasons:edges.append(dict(first_global_frame=a,last_global_frame=b,reasons=reasons))
    stationary=[]
    for a,b in intervals(np.isfinite(step)&(step==0),start):
        if b-a+2>=rules.stationary_frames:stationary.append([a-1,b])
    longest=lambda xs:max((b-a+1 for a,b in xs),default=0)
    behavior_proxy=amb|continuation|changed
    metrics=dict(frame_count=n,known_frames=int(known.sum()),missing_frames=int((~known).sum()),missing_percent=float(100*(~known).mean()),longest_missing_frames=longest(missing),missing_bouts=len(missing),jump_count=len(jumps),severe_jump_count=sum(j['distance_px']>rules.severe_jump_px for j in jumps),max_adjacent_step_px=float(np.nanmax(step)) if offsets.size else None,available_adjacent_steps=int(pairs.sum()),jump_percent_of_available_steps=100*len(jumps)/int(pairs.sum()) if pairs.any() else None,gap_return_displacements=len(gap_returns),candidate_frames=int(p4.sum()),candidate_percent=float(100*p4.mean()),candidate_seconds=float(p4.sum()/fps),candidate_bouts=len(candidate),longest_candidate_frames=longest(candidate),ambiguous_loop_frames=int(amb.sum()),continuation_hypothesis_frames=int(continuation.sum()),longest_continuation_frames=longest(continuation_spans),version_disagreement_frames=int(changed.sum()),behavior_review_proxy_frames=int(behavior_proxy.sum()),behavior_review_proxy_percent=float(100*behavior_proxy.mean()),recovery_ever_established=bool(eligible.any()),capped_onsets=len(capped))
    flags=[]
    def flag(code,domain,priority,reason,spans=()):flags.append(dict(code=code,domain=domain,priority=priority,reason=reason,intervals=list(spans)))
    if missing:flag('MISSING_TRACKING','tracking','high' if (~known).mean()>=rules.missing_fraction or longest(missing)>=rules.missing_gap_frames else 'check',f'{metrics["missing_frames"]} missing frames; longest gap {longest(missing)} frames.',missing)
    if jumps:flag('LARGE_JUMPS','tracking','high' if len(jumps)>=rules.repeated_jumps or metrics['severe_jump_count'] else 'check',f'{len(jumps)} adjacent jumps exceed {rules.jump_px:g} px; camera motion and true tracking errors are not distinguished.',[[j['from_global_frame'],j['to_global_frame']] for j in jumps])
    if gap_returns:flag('DISPLACEMENT_ACROSS_GAP','tracking','check','Large displacement after missing tracking; this is not a measured single-frame jump.',[[g['before_gap_frame'],g['after_gap_frame']] for g in gap_returns])
    if camera_artifacts:flag('RECORDED_CAMERA_ARTIFACT','tracking','high','Previously recorded camera-artifact frames; not newly detected camera motion.',[[int(f),int(f)] for f in camera_artifacts if start<=f<start+n])
    if not eligible.any():flag('RECOVERY_UNRESOLVED','tracking_behavior','high','No sustained departure established; absent candidates do not establish no turtling.',[[start,start+n-1]])
    if p4.mean()>=rules.candidate_fraction or longest(candidate)>=rules.long_candidate_frames:flag('LONG_TURTLING_CANDIDATE','behavior','high','Large candidate duration is a review priority, not an error or a confirmed posture measure.',candidate)
    if amb_spans:flag('AMBIGUOUS_CIRCLING','behavior','check','Motion anchor rejected as smooth/short loop; posture remains unresolved.',amb_spans)
    if capped:flag('ONSET_SEARCH_LIMIT','behavior','high','Backward search reached its limit. Review earlier footage; flagged onset is not an observed flip.',[[x['first_candidate_frame'],x['first_candidate_frame']] for x in capped])
    if edges:flag('CENSORED_EVENT_BOUNDARY','behavior','check','Candidate boundary touches missing tracking, a jump, recovery gate or analysis limit. Onset/righting may lie outside the detected interval.',[[e['first_global_frame'],e['last_global_frame']] for e in edges])
    if longest(continuation_spans)>=rules.long_continuation_frames:flag('LONG_INFERRED_CONTINUATION','behavior','check','Extended posture relies on localized trajectory continuity, not visual confirmation.',continuation_spans)
    if changed.any():flag('VERSION_DISAGREEMENT','behavior','check','Frozen 0.3 and 0.4 disagree; an engineering review signal, not a calibrated confidence estimate.',intervals(changed,start))
    if stationary:flag('EXACT_STATIONARITY','tracking_behavior','check','Long exact-coordinate plateau may be real immobility or a tracking artifact.',stationary)
    priority='high' if any(f['priority']=='high' for f in flags) else 'check' if flags else 'spot_check'
    return dict(schema=VERSION,status='UNREVIEWED_HEURISTIC_PRIORITIES',start_global_frame=start,end_global_frame_inclusive=start+n-1,fps=fps,rules=asdict(rules),metrics=metrics,priority=priority,flags=flags,missing_intervals=missing,jumps=jumps,gap_returns=gap_returns,candidate_intervals=candidate,ambiguous_intervals=amb_spans,continuation_intervals=continuation_spans,onset_search_limits=capped,boundary_concerns=edges,directed_departure_adjustments=trimmed,behavior_review_proxy_intervals=intervals(behavior_proxy,start),automatic_confidence_probability=None,confirmed_turtling_seconds=None,interpretation='Review heuristics only. No flag does not mean trustworthy tracking or no turtling. Initial death feint and immobility can be real. Missing coordinates stay unknown; raw x/y and candidate masks are unchanged.')
