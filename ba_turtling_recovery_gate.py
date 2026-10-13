"""Experimental BA turtling eligibility after sustained departure from start.

This is separate from the prototype's exact-start continuous-chain wake metric.
It can confirm later eligibility after tracking resumes, without changing that
metric or declaring uncertain frames to be observed non-turtling posture.
"""
import numpy as np

VERSION = "0.1.0-development"


def recovery_gate(xy, start, fps=30, distance_px=30., hold_seconds=1., max_step_px=200.,
                  initial_camera_artifact_frames=()):
    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 2 or xy.shape[1] != 2 or not len(xy):
        raise ValueError("Nonempty N by 2 coordinates required")
    if any(not np.isfinite(x) or x <= 0 for x in [fps, distance_px, hold_seconds, max_step_px]):
        raise ValueError("Positive finite parameters required")
    hold = max(2, int(np.ceil(fps * hold_seconds)))
    artifacts = set(initial_camera_artifact_frames)
    if any(not isinstance(f, (int, np.integer)) or not start <= f < start+len(xy) for f in artifacts):
        raise ValueError("Camera artifact frames must be global integers inside the window")
    valid = np.isfinite(xy).all(axis=1)
    steps = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    # A bad incoming step cannot establish departure; later stable positions
    # may start a fresh confirmation period anchored to the original position.
    incoming = np.r_[True, valid[:-1] & valid[1:] & (steps <= max_step_px)]
    eligible = np.zeros(len(xy), bool)
    state = np.full(len(xy), "pre_recovery_not_eligible", object)
    state[~valid | ~incoming] = "tracking_uncertain"
    result = dict(version=VERSION, status="RECOVERY_NOT_CONFIRMED", start_global_frame=start,
                  distance_px=distance_px, hold_seconds=hold_seconds, hold_frames=hold,
                  max_step_px=max_step_px, confirmation_global_frame=None,
                  sustained_departure_start_global_frame=None,
                  missing_frames=(np.flatnonzero(~valid)+start).tolist(),
                  excessive_step_landing_frames=(np.flatnonzero(steps > max_step_px)+start+1).tolist(),
                  initial_camera_artifact_frames=sorted(int(f) for f in artifacts),
                  reference_reacquired_global_frame=None,
                  interpretation="Eligibility hypothesis only; does not replace the legacy wake metric or establish posture.")
    if not valid[0]:
        state[:] = "tracking_uncertain"
        result["status"] = "UNKNOWN_MISSING_START_POSITION"
    else:
        distance = np.linalg.norm(xy-xy[0], axis=1)
        streak = 0
        # If an initial camera artifact is known, do not let a lasting offset
        # masquerade as departure. Require a stable return near the reference
        # after the last marked artifact before evaluating animal departure.
        reference_ready = not artifacts
        reference_streak = 0
        last_artifact = max(artifacts) if artifacts else None
        for i in range(len(xy)):
            if not reference_ready:
                state[i] = "camera_reference_unconfirmed"
                if start+i > last_artifact and valid[i] and incoming[i] and distance[i] < distance_px:
                    reference_streak += 1
                else:
                    reference_streak = 0
                if reference_streak >= hold:
                    reference_ready = True
                    result['reference_reacquired_global_frame'] = int(start+i)
                continue
            if valid[i] and incoming[i] and distance[i] >= distance_px:
                streak += 1
                state[i] = "recovery_confirmation_pending"
            else:
                streak = 0
            if streak >= hold:
                eligible[i:] = True
                state[i:] = "eligible_after_recovery"
                state[i:][~valid[i:]] = "tracking_uncertain"
                result.update(status="RECOVERY_CONFIRMED_EXPERIMENTALLY",
                              confirmation_global_frame=int(start+i),
                              sustained_departure_start_global_frame=int(start+i-hold+1))
                break
        if not reference_ready:
            result['status'] = 'UNKNOWN_CAMERA_REFERENCE_NOT_REACQUIRED'
    result.update(eligible_mask=eligible.tolist(), state=state.tolist())
    return result


def gate_candidates(candidate_mask, xy, start, **kwargs):
    candidate = np.asarray(candidate_mask, dtype=bool)
    if candidate.ndim != 1 or len(candidate) != len(xy):
        raise ValueError("Candidate mask must match coordinates")
    result = recovery_gate(xy, start, **kwargs)
    eligible = np.asarray(result['eligible_mask'])
    observed = np.isfinite(np.asarray(xy, dtype=float)).all(axis=1)
    mask = candidate & eligible & observed
    result.update(candidate_mask=mask.tolist(),
                  suppressed_candidate_frames=int((candidate & ~mask).sum()),
                  confirmed_overturned_seconds=None)
    return result
