"""Provisional major-jump repair gate; never changes production/raw tracking.

Consumes frozen, image-supported bidirectional recovery candidates. It does not
infer positions from trajectories alone, interpolate gaps, or validate identity.
"""
import numpy as np
VERSION = '0.2.0-major-jumps-development'
RULES = dict(version=VERSION, jump_px=100., minimum_replacement_distance_px=50.,
             maximum_join_step_px=30.)

def segments(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return [(int(a), int(b)) for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1))]

def propose(raw, candidates, statuses):
    raw = np.asarray(raw, dtype=float)
    candidates = np.asarray(candidates, dtype=float)
    if raw.shape != candidates.shape or raw.ndim != 2 or raw.shape[1] != 2:
        raise ValueError('Expected matching N x 2 arrays')
    if len(statuses) != len(raw):
        raise ValueError('Status count mismatch')
    finite = np.isfinite(raw).all(axis=1)
    candidate_ok = np.isfinite(candidates).all(axis=1)
    supported = np.isin(statuses, ['proposed_blob', 'proposed_image'])
    eligible = finite & candidate_ok & supported & (
        np.linalg.norm(raw - candidates, axis=1) >= RULES['minimum_replacement_distance_px'])
    raw_steps = np.linalg.norm(np.diff(raw, axis=0), axis=1)
    output = raw.copy()
    changed = np.zeros(len(raw), dtype=bool)
    audit = []
    for a, b in segments(eligible):
        # Both original flanks must be observed. A patch cannot create a gap,
        # bridge an unknown flank, or silently alter an initial/final position.
        reason = None
        if a == 0 or b == len(raw) or not finite[a-1] or not finite[b]:
            reason = 'unobserved_flank'
        elif not np.any(raw_steps[a-1:b] > RULES['jump_px']):
            reason = 'no_major_original_jump'
        else:
            patch = np.vstack([raw[a-1], candidates[a:b], raw[b]])
            if np.max(np.linalg.norm(np.diff(patch, axis=0), axis=1)) > RULES['maximum_join_step_px']:
                reason = 'replacement_does_not_rejoin_original'
        if reason is None:
            output[a:b] = candidates[a:b]
            changed[a:b] = True
        audit.append(dict(start_index=int(a), end_index=int(b-1),
                          accepted=reason is None, reason=reason or 'major_jump_with_supported_rejoining_patch'))
    assert np.array_equal(output[~changed], raw[~changed], equal_nan=True)
    assert np.array_equal(np.isfinite(output).all(axis=1), finite)
    return output, changed, audit
