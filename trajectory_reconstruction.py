"""Conservative speed screening and explicitly estimated gap reconstruction.

Does not resolve identity swaps whose motion remains physically plausible.
Reacquisition is a candidate, not proof that the correct individual was found.
"""
import numpy as np


def reconstruct(xy, max_speed_px=100., confirmation_frames=3):
    xy = np.asarray(xy, dtype=float)
    if xy.ndim != 3 or xy.shape[2] != 2:
        raise ValueError('Expected frames x animals x 2')
    if not np.isfinite(max_speed_px) or max_speed_px <= 0:
        raise ValueError('Speed must be finite and positive')
    if not isinstance(confirmation_frames, int) or confirmation_frames < 1:
        raise ValueError('Confirmation must be a positive integer')
    valid = np.isfinite(xy).all(axis=2)
    accepted = np.zeros(valid.shape, dtype=bool)
    rejected = np.zeros(valid.shape, dtype=bool)
    screened = np.full_like(xy, np.nan)
    held = np.full_like(xy, np.nan)
    bridge = np.full_like(xy, np.nan)
    connections = []
    for a in range(xy.shape[1]):
        last = None
        for t in range(len(xy)):
            if valid[t,a]:
                reachable = last is None or np.linalg.norm(xy[t,a]-xy[last,a]) <= max_speed_px*(t-last)
                # After loss (and at initialization), require consecutive,
                # bounded steps. Never confirm a truncated end-of-file tail.
                confirm = True
                if last is None or t-last > 1:
                    end = t+confirmation_frames
                    confirm = end <= len(xy) and valid[t:end,a].all()
                    if confirm:
                        confirm = (np.linalg.norm(np.diff(xy[t:end,a],axis=0),axis=1) <= max_speed_px).all()
                if reachable and confirm:
                    accepted[t,a] = True
                    screened[t,a] = xy[t,a]
                    if last is not None and t-last > 1:
                        bridge[last:t+1,a] = np.linspace(xy[last,a],xy[t,a],t-last+1)
                        connections.append(dict(animal_id=a,last_accepted_frame=last,
                            reacquired_frame=t,gap_frames=t-last-1,
                            endpoint_distance_px=float(np.linalg.norm(xy[t,a]-xy[last,a]))))
                    last = t
                else:
                    rejected[t,a] = True
            if last is not None:
                held[t,a] = xy[last,a]
    states = np.full(valid.shape, 'UNLOCATED',dtype='<U24')
    states[np.isfinite(held).all(axis=2)] = 'HELD_LAST_POSITION'
    states[accepted] = 'SCREENED_ASSIGNED'
    return dict(raw=xy.copy(),screened=screened,held=held,bridge=bridge,
        accepted=accepted,rejected=rejected,states=states,connections=connections)
