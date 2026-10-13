"""BA development experiment: distinguish smooth loops and preserve local pauses.

This consumes a frozen recovery-gated candidate mask. It is not a production
classifier and never establishes posture. No human labels or source identifiers
enter the algorithm. Missing coordinates remain unknown, never interpolated.
"""
from dataclasses import asdict, dataclass
import numpy as np

VERSION = '0.3.0-development'

@dataclass(frozen=True)
class Rules:
    smooth_frames: int = 11
    maximum_smooth_path_ratio: float = .65
    minimum_reversal_fraction: float = .10
    minimum_anchor_frames: int = 120
    context_frames: int = 30
    continuation_radius_px: float = 35.
    maximum_step_px: float = 20.


def segments(mask):
    e = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(e == 1), np.flatnonzero(e == -1)))


def motion_signature(xy, smooth_frames=11):
    """Path remaining after centered smoothing and fraction of >90-degree turns.

    Turns use adjacent steps >=1 pixel, matching the original motion floor.
    Smoothing uses edge padding inside this observed segment, never missing data.
    """
    a = np.asarray(xy, float)
    if len(a) < 3 or not np.isfinite(a).all():
        return dict(smooth_path_ratio=None, reversal_fraction=None, moving_turns=0)
    v = np.diff(a, axis=0); lengths = np.linalg.norm(v, axis=1)
    pad = smooth_frames // 2
    smooth = np.column_stack([np.convolve(np.pad(a[:, j], (pad, pad), mode='edge'),
                                         np.ones(smooth_frames)/smooth_frames, mode='valid')
                              for j in range(2)])
    path = lengths.sum()
    ratio = float(np.linalg.norm(np.diff(smooth, axis=0), axis=1).sum()/path) if path else 0.
    moving = lengths >= 1.
    headings = np.arctan2(v[:, 1], v[:, 0])
    turn = np.arctan2(np.sin(np.diff(headings)), np.cos(np.diff(headings)))
    usable = moving[:-1] & moving[1:]
    reversal = float(np.mean(np.abs(turn[usable]) > np.pi/2)) if usable.any() else 0.
    return dict(smooth_path_ratio=ratio, reversal_fraction=reversal, moving_turns=int(usable.sum()))


def refine(xy, frozen_mask, eligible_mask, start=0, rules=Rules()):
    a = np.asarray(xy, float)
    base = np.asarray(frozen_mask, bool); eligible = np.asarray(eligible_mask, bool)
    if a.ndim != 2 or a.shape[1] != 2 or base.shape != (len(a),) or eligible.shape != base.shape:
        raise ValueError('Expected aligned coordinates and masks')
    ints = [rules.smooth_frames, rules.minimum_anchor_frames, rules.context_frames]
    if any(type(v) is not int or v < 3 for v in ints) or rules.smooth_frames % 2 != 1:
        raise ValueError('Frame parameters must be positive integers; smoothing must be odd')
    if not 0 <= rules.maximum_smooth_path_ratio <= 1 or not 0 <= rules.minimum_reversal_fraction <= 1:
        raise ValueError('Ratios must be between zero and one')
    if any(not np.isfinite(v) or v <= 0 for v in [rules.continuation_radius_px, rules.maximum_step_px]):
        raise ValueError('Distance parameters must be finite and positive')
    known = np.isfinite(a).all(axis=1)
    if np.any(base & (~known | ~eligible)):
        raise ValueError('Input candidates must already respect tracking and recovery eligibility')
    anchor = np.zeros(len(a), bool); ambiguous = np.zeros(len(a), bool); audit = []
    for lo, hi in segments(base):
        s = motion_signature(a[lo:hi], rules.smooth_frames)
        supported = (hi-lo >= rules.minimum_anchor_frames and
                     (s['smooth_path_ratio'] <= rules.maximum_smooth_path_ratio or
                      s['reversal_fraction'] >= rules.minimum_reversal_fraction))
        (anchor if supported else ambiguous)[lo:hi] = True
        audit.append(dict(first_global_frame=int(start+lo), last_global_frame=int(start+hi-1),
                          frames=int(hi-lo), retained_anchor=bool(supported), **s))
    mask = anchor.copy()
    evidence = np.full(len(a), 'no_candidate_not_posture_label', object)
    evidence[ambiguous] = 'ambiguous_loop_requires_review'
    evidence[anchor] = 'irregular_motion_anchor_hypothesis'
    evidence[~eligible] = 'recovery_not_established'
    evidence[~known] = 'tracking_unknown'
    # A fixed local reference prevents slow propagation across the arena. Only
    # original retained anchors can renew it. Stop on missing data, jumps, loss of
    # eligibility or spatial departure. A quiet pause is not evidence of righting.
    for lo, hi in segments(anchor):
        center = np.median(a[max(lo, hi-rules.context_frames):hi], axis=0)
        j = hi
        while j < len(a) and not anchor[j]:
            if (not eligible[j] or not known[j] or not known[j-1]
                    or np.linalg.norm(a[j]-a[j-1]) > rules.maximum_step_px
                    or np.linalg.norm(a[j]-center) > rules.continuation_radius_px):
                break
            mask[j] = True
            evidence[j] = 'localized_continuation_hypothesis'
            j += 1
    return dict(version=VERSION, status='DEVELOPMENT_FIT_UNVALIDATED', rules=asdict(rules),
                candidate_mask=mask.tolist(), retained_anchor_mask=anchor.tolist(),
                ambiguous_loop_mask=(ambiguous & ~mask).tolist(), evidence=evidence.tolist(),
                anchor_audit=audit, confirmed_overturned_seconds=None,
                warning='Continuation and smooth-loop rejection are movement hypotheses, not observed posture. Quiet upright stops remain a risk.')
