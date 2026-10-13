"""BA episode experiment 0.2.0; development only, not pipeline default.

Lower-motion looping can extend a connected region containing an original
baseline candidate. It cannot independently initiate a new region. Posture
is still unobserved by this centroid-only model.
"""
import numpy as np
from ba_turtling_diagnostics import window_features, gate_passes, mask_from_windows
from ba_turtling_candidates import candidate_episodes, Rules
from ba_turtling import summarize

VERSION = "0.2.0-development"


def segments(mask):
    edges = np.diff(np.r_[False, np.asarray(mask, bool), False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def experiment(xy, baseline_mask, start_global_frame, fps=30, features=None):
    xy = np.asarray(xy, dtype=float)
    base = np.asarray(baseline_mask, dtype=bool)
    if fps != 30 or xy.shape != (len(base), 2):
        raise ValueError("This development experiment requires 30 fps and matching N by 2 coordinates")
    f = window_features(xy) if features is None else np.asarray(features)
    if f.shape != (max(0, len(xy)-119), 6):
        raise ValueError("Features must describe every 120-frame window")
    gates = gate_passes(f)
    strict = mask_from_windows(xy, gates.all(axis=1))
    if not np.array_equal(strict, base):
        raise ValueError("Original baseline mask does not match diagnostic reconstruction")
    gates[:, 2] = f[:, 2] >= 60
    relaxed = mask_from_windows(xy, gates.all(axis=1))
    supported = base.copy()
    for lo, hi in segments(relaxed):
        if base[lo:hi].any():
            supported[lo:hi] = True
    previous = candidate_episodes(xy, supported, start_global_frame, fps,
                                  Rules(maximum_transition_px=100))
    mask = np.asarray(previous["episode_mask"], bool)
    evidence = np.asarray(previous["evidence"], object)
    evidence[supported & ~base] = "lower_motion_looping_hypothesis"
    additions = list(previous["additions"])
    for lo, hi in segments(supported & ~base):
        additions.append(dict(kind="lower_motion_looping_hypothesis",
                              first_global_frame=int(start_global_frame+lo),
                              last_global_frame=int(start_global_frame+hi-1)))
    # At the truncated observation boundary only: up to one second, with four
    # seconds of preceding support and the same radius/step guard as gap fills.
    bouts = segments(mask)
    if bouts:
        lo, hi = bouts[-1]
        tail = len(mask)-hi
        if 0 < tail <= 30 and hi-lo >= 120:
            block = xy[hi-30:]
            if (np.isfinite(block).all()
                    and np.max(np.linalg.norm(np.diff(block,axis=0),axis=1)) <= 20
                    and np.max(np.linalg.norm(block-np.median(block,axis=0),axis=1)) <= 35):
                mask[hi:] = True
                evidence[hi:] = "short_terminal_continuation_hypothesis"
                additions.append(dict(kind="short_terminal_continuation_hypothesis",
                                      first_global_frame=int(start_global_frame+hi),
                                      last_global_frame=int(start_global_frame+len(mask)-1),
                                      right_censored=True))
    known = np.isfinite(xy).all(axis=1)
    result = summarize(mask, known, start_global_frame, fps)
    result.update(schema="ba-experimental-turtling-candidates-v1", version=VERSION,
                  status="DEVELOPMENT_FIT_UNVALIDATED", episode_mask=mask.tolist(),
                  evidence=evidence.tolist(), additions=additions,
                  baseline=summarize(base,known,start_global_frame,fps),
                  added_candidate_frames=int((mask & ~base).sum()),
                  confirmed_overturned_seconds=None,
                  rules=dict(window_frames=120, continuation_min_path_px=60,
                             original_candidate_required=True, maximum_transition_px=100,
                             gap_seconds=1, terminal_seconds=1),
                  warning="Centroid evidence cannot establish posture or recovery; the 12 scored runs informed this revision.")
    return result
