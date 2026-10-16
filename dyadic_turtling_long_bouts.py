"""Frozen 300-frame fight-dashboard screen; candidates are not posture labels.

Replays context_300 from the October 16 experiment. This is an offline,
raw-coordinate screen, selected for dashboard review, not a production
behavior measurement or a replacement for the BA detector.
"""
import math
import numpy as np

VERSION = '0.1.0-long300-qc'
PARAMETERS = dict(minimum_frames=300, feature_window=120, quiet_tail_frames=300,
                  initial_window_suppression=100, fungus_suppression=True,
                  loop_max_step=20, loop_radius90=35, loop_min_path=20,
                  loop_max_net_path_ratio=.35, loop_min_turns=1.5,
                  quiet_max_step=5, quiet_radius90=3, path_step_floor=.5,
                  required_fps=30)
POLICY = ('Possible turtling only; confirm ID and posture in video. No flag and '
          'unannotated footage do not mean no turtling. Candidate boundaries '
          'are not measured flip/righting times. Rules were developed on the '
          'annotated set, not independently validated. Wall/fall proximity is '
          'not required by the selected context_300 rule.')


def runs(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return [(int(a), int(b)) for a, b in
            zip(np.where(edges == 1)[0], np.where(edges == -1)[0])]


def sustain(mask, minimum=300):
    out = np.zeros(len(mask), bool)
    for a, b in runs(mask):
        if b - a >= minimum:
            out[a:b] = True
    return out


def recent(mask, window):
    if not len(mask):
        return np.zeros(0, bool)
    return np.convolve(mask.astype(int), np.ones(window, int), 'full')[:len(mask)] > 0


def spread(supported, window, length):
    delta = np.zeros(length + 1, int)
    starts = np.flatnonzero(supported)
    np.add.at(delta, starts, 1)
    np.add.at(delta, starts + window, -1)
    return np.cumsum(delta[:-1]) > 0


def features(xy):
    """Union of fully observed 120-frame loop/quiet windows, as frozen."""
    xy = np.asarray(xy, dtype=float)
    n = len(xy)
    w = PARAMETERS['feature_window']
    valid = np.isfinite(xy).all(1)
    if n < w:
        return np.zeros(n, bool), np.zeros(n, bool), valid
    z = np.nan_to_num(xy)
    vec = np.diff(z, axis=0)
    steps = np.linalg.norm(vec, axis=1)
    steps[~(valid[1:] & valid[:-1])] = np.nan
    win = np.lib.stride_tricks.sliding_window_view(z, w, axis=0).transpose(0, 2, 1)
    center = np.median(win, axis=1)
    radius = np.quantile(np.linalg.norm(win - center[:, None, :], axis=2), .9, axis=1)
    sw = np.lib.stride_tricks.sliding_window_view(np.nan_to_num(steps, nan=1e6), w - 1)
    known = np.convolve(valid.astype(int), np.ones(w, int), 'valid') == w
    path = np.where(sw >= .5, sw, 0).sum(1)
    mx = sw.max(1)
    net = np.linalg.norm(win[:, -1] - win[:, 0], axis=1)
    angle = np.arctan2(vec[:, 1], vec[:, 0])
    turn = np.abs(np.arctan2(np.sin(np.diff(angle)), np.cos(np.diff(angle))))
    turn[(np.nan_to_num(steps[:-1]) < .5) | (np.nan_to_num(steps[1:]) < .5)] = 0
    turn = np.convolve(turn, np.ones(w - 2), 'valid') / (2 * np.pi)
    loop = known & (mx <= 20) & (radius <= 35) & (path >= 20) & (net / np.maximum(path, 1) <= .35) & (turn >= 1.5)
    quiet = known & (mx <= 5) & (radius <= 3)
    return spread(loop, w, n) & valid, spread(quiet, w, n) & valid, valid


def candidate_mask(xy, raw_fungus):
    fungus = np.asarray(raw_fungus, dtype=float)
    if fungus.shape != (len(xy),):
        raise ValueError('Fungus evidence must match every observation')
    loop, quiet, valid = features(xy)
    context = loop | (quiet & recent(loop, 300))
    context[:100] = False  # First 100 observations of this TOML window.
    context[(fungus > 0) | ~np.isfinite(fungus)] = False
    return sustain(context, 300), loop, quiet, valid


def summarize(raw, raw_fungus, start, fps):
    raw = np.asarray(raw, dtype=float)
    fungus = np.asarray(raw_fungus, dtype=float)
    if raw.ndim != 3 or raw.shape[1:] != (2, 2):
        raise ValueError('Exactly two raw identities with x/y coordinates are required')
    if fungus.shape != raw.shape[:2]:
        raise ValueError('Raw fungus evidence must have shape (observations, 2)')
    result = dict(version=VERSION, screen_version=VERSION, parameters=PARAMETERS.copy(),
                  policy=POLICY, status='CANDIDATES_UNREVIEWED',
                  identity_numbering='raw IDs 0 and 1', first_global_frame=int(start),
                  frames=len(raw), fps=float(fps) if math.isfinite(fps) else None,
                  events=[], per_id=[])
    if not math.isfinite(fps) or abs(fps - 30) > 1e-6:
        result.update(status='NOT_ASSESSED', reason='Frozen rules support 30 fps only; no threshold rescaling.')
        return result
    for ident in (0, 1):
        mask, loop, quiet, valid = candidate_mask(raw[:, ident], fungus[:, ident])
        intervals = runs(mask)
        for a, b in intervals:
            result['events'].append(dict(animal_id=ident, first_global_frame=int(start + a),
                last_global_frame_inclusive=int(start + b - 1), candidate_frames=b - a,
                quiet_support=bool(quiet[a:b].any()), loop_support=bool(loop[a:b].any()),
                status='POSSIBLE_TURTLING_REVIEW'))
        result['per_id'].append(dict(animal_id=ident, candidate_frames=int(mask.sum()),
            candidate_bouts=len(intervals), tracking_unknown_frames=int((~valid).sum()),
            fungus_unknown_frames=int((~np.isfinite(fungus[:, ident])).sum()),
            no_candidate_frames=int((valid & ~mask).sum())))
    result['events'].sort(key=lambda e: (e['first_global_frame'], e['animal_id']))
    return result
