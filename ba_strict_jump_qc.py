"""BA-only conservative analysis gate; does not infer bad-interval boundaries."""
import numpy as np
VERSION = '0.1.0'
def gate(proposed, start, threshold=100):
    source = np.asarray(proposed, dtype=float)
    track = source.copy()
    distance = np.linalg.norm(np.diff(source, axis=0), axis=1)
    edges = np.flatnonzero(distance >= threshold)
    # Both endpoints are uncertain: the second may be a correct reappearance.
    uncertain = np.zeros(len(source), dtype=bool)
    uncertain[edges] = True
    uncertain[edges + 1] = True
    track[uncertain] = np.nan
    # Without independent anchors, no automatic claim about episode boundaries.
    # Block this run's movement analysis, not merely the visible jump edges.
    movement = np.full(max(0, len(source)-1), np.nan)
    if not len(edges):
        movement[:] = distance
    return track, movement, dict(version=VERSION, threshold_px=threshold,
        jump_pairs=[[int(start+i),int(start+i+1)] for i in edges],
        uncertain_frames=(np.flatnonzero(uncertain)+start).tolist(),
        movement_status='BLOCKED_UNRESOLVED_JUMPS' if len(edges) else 'NO_LARGE_JUMP_BLOCK',
        boundaries='UNRESOLVED' if len(edges) else 'NOT_APPLICABLE',
        human_run_review_required=bool(len(edges)),
        status='UNREVIEWED', automatic_exclusion=False)
