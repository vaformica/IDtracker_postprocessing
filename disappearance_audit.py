"""Frame-based review index for original coordinates and presumed group losses."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
from six_beetle_processor import presumed_groups


def build(source, output, start=250, stop=16998, threshold=60):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    xy = np.load(source, allow_pickle=True).item()['trajectories'][:stop]
    group = presumed_groups(xy, threshold)
    valid = np.isfinite(xy).all(axis=2)
    rows = []
    for animal in range(xy.shape[1]):
        missing = ~valid[start:stop, animal]
        edges = np.diff(np.r_[False, missing, False].astype(int))
        for lo, hi in zip(np.flatnonzero(edges == 1)+start,
                          np.flatnonzero(edges == -1)+start):
            prior = np.flatnonzero(valid[:lo, animal])
            last = int(prior[-1]) if len(prior) else -1
            pos = xy[last, animal] if last >= 0 else [np.nan, np.nan]
            inferred = group['inferred'][lo:hi, animal]
            anchors = group['anchors'][lo:hi, animal]
            near = []
            if lo > 0 and valid[lo-1, animal]:
                near = [int(b) for b in range(xy.shape[1]) if b != animal
                        and valid[lo-1, b] and valid[lo, b]
                        and np.linalg.norm(xy[lo-1, b]-xy[lo-1, animal]) <= threshold]
            rows.append(dict(animal_id=animal, first_missing_frame=int(lo),
                last_missing_frame=int(hi-1), missing_frames=int(hi-lo),
                last_assigned_frame=last, last_x=float(pos[0]), last_y=float(pos[1]),
                return_frame=int(hi) if hi < stop else '',
                presumed_frames=int(inferred.sum()), unresolved_frames=int((~inferred).sum()),
                ambiguous_frames=int(group['ambiguous'][lo:hi, animal].sum()),
                visible_anchor_ids=';'.join(map(str, sorted(set(anchors)-{-1}))),
                nearby_visible_ids_at_loss=';'.join(map(str, near)),
                classification='presumed_social_disappearance' if inferred.all() else
                    'unresolved' if not inferred.any() else 'mixed_presumed_and_unresolved',
                visual_review='NOT_REVIEWED'))
    rows.sort(key=lambda r: (r['first_missing_frame'], r['animal_id']))
    with (output/'disappearances.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    np.savez_compressed(output/'audit_states.npz', xy=xy, anchors=group['anchors'],
        inferred=group['inferred'], ambiguous=group['ambiguous'], estimated=group['xy'])
    summary = dict(source=str(source.resolve()), sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        first_frame=start, last_frame=stop-1, threshold_px=threshold,
        missing_coordinate_frames=int((~valid[start:stop]).sum()),
        presumed_coordinate_frames=int(group['inferred'][start:stop].sum()),
        unresolved_coordinate_frames=int(((~valid)&~group['inferred'])[start:stop].sum()),
        disappearance_episodes=len(rows),
        caveat='Presumed contact is an inference. Unresolved loss does not establish tracker failure. Original IDtracker coordinates may include gap filling; identity swaps with coordinates present are not counted here.')
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('source'); p.add_argument('output')
    a=p.parse_args(); build(a.source, a.output)
