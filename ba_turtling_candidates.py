"""Experimental BA-only candidate continuity. Coordinates do not establish posture.

Existing loop candidates are anchors. Added frames have separate, explicit evidence;
no human labels or recording/frame identifiers enter this function.
"""
from dataclasses import asdict, dataclass
import numpy as np
import ba_turtling

VERSION = '0.1.0-experimental'

@dataclass(frozen=True)
class Rules:
    onset_lookback_seconds: float = 4.0
    anchor_seconds: float = 4.0
    quiet_gap_seconds: float = 1.0
    gap_context_seconds: float = 1.0
    local_radius_px: float = 35.0
    transition_step_px: float = 20.0
    maximum_transition_px: float = 200.0


def candidate_episodes(xy, baseline_mask, start, fps, rules=Rules()):
    """Return a distinct UNVALIDATED candidate mask, preserving every baseline flag.

    Onset hypothesis: a bounded centroid displacement, followed by localized motion,
    shortly before a sustained baseline anchor. Such a displacement can ALSO be a
    tracking artifact; this is a review cue, never a confirmed flip.
    Quiet-pause hypothesis: a short, observed, spatially localized gap bounded by
    baseline candidates. Missing data, jumps, long gaps and trailing immobility are
    not filled. Analysis must run on the full window before excerpting its results.
    """
    a=np.asarray(xy,dtype=float); base=np.asarray(baseline_mask,dtype=bool)
    if a.ndim!=2 or a.shape[1]!=2 or base.shape!=(len(a),):
        raise ValueError('Expected aligned (frames, 2) positions and 1D mask')
    if any(not np.isfinite(v) or v<=0 for v in asdict(rules).values()):
        raise ValueError('Rules must be positive and finite')
    if rules.maximum_transition_px<=rules.transition_step_px:
        raise ValueError('Maximum transition must exceed transition threshold')
    known=np.isfinite(a).all(1)
    baseline=ba_turtling.summarize(base,known,start,fps)
    mask=base.copy(); evidence=np.where(base,'baseline_candidate','unassessed').astype(object)
    steps=np.linalg.norm(np.diff(a,axis=0),axis=1)
    lookback=max(1,round(rules.onset_lookback_seconds*fps))
    anchor_n=max(1,round(rules.anchor_seconds*fps))
    context=max(1,round(rules.gap_context_seconds*fps))
    additions=[]
    bouts=baseline['bouts']
    for b in bouts:
        lo=b['start_global_frame']-start; hi=b['end_global_frame_inclusive']-start+1
        if hi-lo<anchor_n:continue
        # A nearby earlier bout is a continuity question, not a fresh onset.
        if base[max(0,lo-lookback):lo].any():continue
        # Search landing frames; a missing transition is never evidence of a flip.
        lower=max(1,lo-lookback)
        landings=[j for j in range(lower,lo+1)
                  if rules.transition_step_px<steps[j-1]<=rules.maximum_transition_px]
        if not landings:continue
        onset=landings[-1]
        if onset==lo:continue
        stop=lo+anchor_n
        if not known[onset-1:stop].all() or base[onset:lo].any():continue
        if (steps[onset:stop-1]>rules.transition_step_px).any():continue
        center=np.median(a[lo:stop],axis=0)
        if np.max(np.linalg.norm(a[onset:stop]-center,axis=1))>rules.local_radius_px:continue
        mask[onset:lo]=True; evidence[onset:lo]='onset_transition_hypothesis'
        additions.append(dict(kind='onset_transition_hypothesis',first_global_frame=start+onset,
            last_global_frame=start+lo-1,transition_step_px=float(steps[onset-1]),
            warning='Centroid displacement may reflect tracking or segmentation error, not posture.'))
    # Only original baseline anchors can justify a pause; no recursive propagation.
    for left,right in zip(bouts,bouts[1:]):
        lo=left['end_global_frame_inclusive']-start+1; hi=right['start_global_frame']-start
        if not 0<hi-lo<=round(rules.quiet_gap_seconds*fps):continue
        first=max(left['start_global_frame']-start,lo-context)
        stop=min(right['end_global_frame_inclusive']-start+1,hi+context)
        if not known[first:stop].all():continue
        if (steps[first:stop-1]>rules.transition_step_px).any():continue
        center=np.median(a[first:stop],axis=0)
        if np.max(np.linalg.norm(a[first:stop]-center,axis=1))>rules.local_radius_px:continue
        mask[lo:hi]=True; evidence[lo:hi]='quiet_pause_hypothesis'
        additions.append(dict(kind='quiet_pause_hypothesis',first_global_frame=start+lo,last_global_frame=start+hi-1))
    result=ba_turtling.summarize(mask,known,start,fps)
    result.update(schema='ba-experimental-turtling-candidates-v1',version=VERSION,
        status='EXPERIMENTAL_CANDIDATE_UNVALIDATED',rules=asdict(rules),
        definition='Baseline looping anchors plus bounded transition and quiet-pause hypotheses; not confirmed posture.',
        baseline=baseline,episode_mask=mask.tolist(),evidence=evidence.tolist(),additions=additions,
        added_candidate_frames=int((mask & ~base).sum()),
        confirmed_overturned_seconds=None)
    return result


def pdf_pages(pdf, result):
    """Append the separate experimental account; never relabel it human review."""
    import math
    import matplotlib.pyplot as plt
    bouts=result['bouts']
    for page in range(max(1,math.ceil(len(bouts)/20))):
        fig=plt.figure(figsize=(8.5,11))
        lines=['BA experimental turtling candidates | '+VERSION,
               'EXPERIMENTAL / UNVALIDATED - posture is not confirmed',
               result.get('display_label','BA analysis window'),
               f"Baseline candidate time: {result['baseline']['candidate_seconds']:.3f} s",
               f"Experimental candidate time: {result['candidate_seconds']:.3f} s",
               f"Added candidate time: {result['added_candidate_frames']/result['fps']:.3f} s",
               'Start: bounded transition before a sustained loop candidate.',
               'Pause: <=1 second, localized, observed, between loop candidates.',
               'Missing tracking, large steps and trailing stillness are not filled.',
               'A centroid transition can be a tracking error; inspect the video.',
               'This rule was developed on reviewed examples, not held-out data.',
               '', 'Start frame    End frame      Seconds   Clip boundary']
        for b in bouts[page*20:(page+1)*20]:
            boundary='both' if b['left_censored'] and b['right_censored'] else 'start' if b['left_censored'] else 'end' if b['right_censored'] else 'neither'
            lines.append(f"{b['start_global_frame']:11d} {b['end_global_frame_inclusive']:12d} {b['seconds']:12.3f}   {boundary}")
        fig.text(.07,.94,'\n'.join(lines),va='top',fontsize=10,family='monospace',linespacing=1.6)
        fig.text(.07,.05,'Automatic hypotheses and attributed posture decisions remain separate.',fontsize=9)
        pdf.savefig(fig);plt.close(fig)
