"""BA-only review warnings; never posture labels or trajectory corrections."""
import numpy as np
from ba_turtling_diagnostics import window_features, gate_passes, mask_from_windows
from ba_turtling_continuity_experiment import segments
VERSION='0.1.0-development'
def warnings(xy, eligible, start=0):
    xy=np.asarray(xy,float);eligible=np.asarray(eligible,bool)
    if xy.ndim!=2 or xy.shape[1]!=2 or eligible.shape!=(len(xy),):
        raise ValueError('Expected aligned N by 2 coordinates and eligibility')
    known=np.isfinite(xy).all(1)
    f=window_features(xy);g=gate_passes(f)
    g[:,2]=True # No minimum qualifying path.
    g[:,3]=f[:,3]<=35 # Preserve upper radius; remove lower radius.
    accepted=g.all(1)
    for i in np.flatnonzero(accepted):
        accepted[i]=bool(known[i:i+120].all() and eligible[i:i+120].all())
    candidate=mask_from_windows(xy,accepted)
    sustained=np.zeros(len(xy),bool)
    for lo,hi in segments(candidate):
        if hi-lo>=600:sustained[lo:hi]=True
    def bounds(mask):
        return [[int(start+lo),int(start+hi-1)] for lo,hi in segments(mask)]
    return dict(version=VERSION,status='UNREVIEWED_QC_ONLY',confirmed_turtling_seconds=None,
                localized_irregular_motion=bounds(sustained),tracking_unknown=bounds(~known),
                warning_mask=sustained.tolist(),
                rules=dict(window_frames=120,minimum_continuous_frames=600,fully_finite_eligible_windows=True),
                meaning='Review posture; neither a confirmed flip nor a duration estimate. Gaps remain unknown.')
