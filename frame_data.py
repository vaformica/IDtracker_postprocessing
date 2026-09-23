"""Auditable per-frame export and window recalculation for tracked animals."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import re

import numpy as np
import processor as legacy


BASE_FIELDS = [
    'global_frame', 'animal_id', 'raw_x', 'raw_y', 'x', 'y',
    'location_source', 'inferred', 'group_id', 'ambiguous', 'location_known',
    'in_arena', 'any_fungus',
    'observed_proximity_partners', 'pscp_partners',
    'step_from_previous_accepted', 'step_distance_px',
]


def fields_for_fungi(count):
    if count < 1:
        raise ValueError('At least one fungus ROI is required')
    return (BASE_FIELDS + [f'fungus_{i}' for i in range(1, count+1)]
            + [f'step_midpoint_fungus_{i}' for i in range(1, count+1)])


def _inside(points, polygon):
    valid = np.isfinite(points).all(axis=1)
    result = np.zeros(len(points), dtype=bool)
    result[valid] = legacy.points_inside_polygon(points[valid], polygon)
    return result


def write_frame_data(result, destination):
    """Export one row per animal and global frame from the canonical analysis."""
    raw = result['xy']
    group = result['group']
    xy = group['xy']
    nframes, animals, _ = xy.shape
    rois = [np.asarray(p, dtype=float) for p in result['metadata']['rois']]
    fungi = len(rois)-1
    if animals < 2 or fungi < 1 or raw.shape != xy.shape or nframes < 1:
        raise ValueError('Frame export requires matching paths, at least two animals, and arena plus fungus ROIs')
    speed = float(result['metadata']['reconstruction']['max_speed_px_per_frame'])
    if not math.isfinite(speed) or speed <= 0:
        raise ValueError('Invalid canonical step limit')
    membership = np.stack([_inside(xy[:, a], polygon) for a in range(animals)
                           for polygon in rois]).reshape(animals, len(rois), nframes).transpose(2, 0, 1)
    midpoints = (xy[:-1] + xy[1:]) / 2
    mid_fungus = np.stack([_inside(midpoints[:, a], polygon) for a in range(animals)
                           for polygon in rois[1:]]).reshape(animals, fungi, nframes-1).transpose(2, 0, 1)
    lengths = np.linalg.norm(np.diff(xy, axis=0), axis=2)
    accepted = np.isfinite(xy[:-1]).all(axis=2) & np.isfinite(xy[1:]).all(axis=2) & (lengths <= speed)
    observed = [[[] for _ in range(animals)] for _ in range(nframes)]
    pscp = [[[] for _ in range(animals)] for _ in range(nframes)]
    for a, b in itertools.combinations(range(animals), 2):
        for t in np.flatnonzero(result['masks'][a, b]):
            observed[t][a].append(b); observed[t][b].append(a)
        for t in np.flatnonzero(group['masks'][a, b]):
            pscp[t][a].append(b); pscp[t][b].append(a)
    start = result['metadata']['settings']['start']
    with Path(destination).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields_for_fungi(fungi))
        writer.writeheader()
        for t in range(nframes):
            for a in range(animals):
                known = bool(np.isfinite(xy[t, a]).all())
                row = dict(global_frame=start+t, animal_id=a,
                           raw_x=raw[t,a,0], raw_y=raw[t,a,1], x=xy[t,a,0], y=xy[t,a,1],
                           location_source=group['source'][t,a], inferred=int(group['inferred'][t,a]),
                           group_id=int(group['group_ids'][t,a]), ambiguous=int(group['ambiguous'][t,a]),
                           location_known=int(known), in_arena=int(membership[t,a,0]),
                           any_fungus=int(membership[t,a,1:].any()),
                           observed_proximity_partners=';'.join(map(str, observed[t][a])),
                           pscp_partners=';'.join(map(str, pscp[t][a])),
                           step_from_previous_accepted=int(t > 0 and accepted[t-1,a]))
                for fungus in range(1, fungi+1):
                    row[f'fungus_{fungus}'] = int(membership[t,a,fungus])
                    row[f'step_midpoint_fungus_{fungus}'] = int(t > 0 and mid_fungus[t-1,a,fungus-1])
                row['step_distance_px'] = float(lengths[t-1,a]) if t > 0 and accepted[t-1,a] else ''
                writer.writerow({key: '' if isinstance(value, (float, np.floating)) and not math.isfinite(value)
                                 else value for key, value in row.items()})


def aggregate(frame_csv, start, end):
    """Return per-beetle and per-pair counts for inclusive global frames."""
    if start > end:
        raise ValueError('Start frame must be at or before end frame')
    by_frame = {}
    with Path(frame_csv).open(newline='') as stream:
        reader = csv.DictReader(stream)
        header = reader.fieldnames or []
        fungus_ids = sorted(int(match.group(1)) for name in header
            if (match := re.fullmatch(r'fungus_(\d+)', name)))
        if fungus_ids != list(range(1, len(fungus_ids)+1)) or not fungus_ids:
            raise ValueError('Fungus columns must be numbered consecutively from 1')
        missing = set(fields_for_fungi(len(fungus_ids))) - set(header)
        if missing:
            raise ValueError(f'Missing frame-data columns: {sorted(missing)}')
        for row in reader:
            frame = int(row['global_frame'])
            if start <= frame <= end:
                animal = int(row['animal_id'])
                frame_rows = by_frame.setdefault(frame, {})
                if animal in frame_rows:
                    raise ValueError(f'Duplicate beetle {animal} in frame {frame}')
                frame_rows[animal] = row
    expected = set(range(start, end+1))
    animals = set(by_frame.get(start, {}))
    if (not animals or animals != set(range(len(animals))) or set(by_frame) != expected
            or any(set(rows) != animals for rows in by_frame.values())):
        raise ValueError('Requested window lacks complete per-animal frame coverage')
    frames = end-start+1
    beetles = []
    for a in sorted(animals):
        rows = [by_frame[t][a] for t in range(start, end+1)]
        known = sum(int(r['location_known']) for r in rows)
        inferred = sum(int(r['inferred']) for r in rows)
        item = dict(animal_id=a, start_global_frame=start, end_global_frame_inclusive=end,
                    frame_observations=frames, known_location_frames=known,
                    missing_location_frames=frames-known, inferred_location_frames=inferred,
                    observed_assigned_frames=sum(r['location_source']=='ASSIGNED' for r in rows),
                    any_fungus_frames=sum(int(r['any_fungus']) for r in rows),
                    any_fungus_percent_all_frames=100*sum(int(r['any_fungus']) for r in rows)/frames,
                    any_fungus_percent_known_frames=(100*sum(int(r['any_fungus']) for r in rows)/known if known else ''),
                    distance_px=sum(float(r['step_distance_px']) for r in rows[1:] if r['step_distance_px']!=''))
        for fungus in fungus_ids:
            count = sum(int(r[f'fungus_{fungus}']) for r in rows)
            item[f'fungus_{fungus}_frames'] = count
            item[f'fungus_{fungus}_percent_all_frames'] = 100*count/frames
            item[f'fungus_{fungus}_percent_known_frames'] = 100*count/known if known else ''
            item[f'fungus_{fungus}_distance_px'] = sum(float(r['step_distance_px']) for r in rows[1:]
                if r['step_distance_px']!='' and int(r[f'step_midpoint_fungus_{fungus}']))
        beetles.append(item)
    pairs = []
    for a, b in itertools.combinations(sorted(animals), 2):
        observed = sum(str(b) in by_frame[t][a]['observed_proximity_partners'].split(';') for t in expected)
        presumed = sum(str(b) in by_frame[t][a]['pscp_partners'].split(';') for t in expected)
        pairs.append(dict(animal_a=a, animal_b=b, start_global_frame=start,
                          end_global_frame_inclusive=end, frame_observations=frames,
                          observed_proximity_frames=observed, pscp_frames=presumed))
    return beetles, pairs


def _write_rows(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description='Recalculate fungus and proximity summaries from frame_data.csv')
    parser.add_argument('bundle', type=Path, help='Completed canonical analysis bundle')
    parser.add_argument('--start', type=int, required=True, help='First global frame, inclusive')
    parser.add_argument('--end', type=int, required=True, help='Last global frame, inclusive')
    parser.add_argument('--output', type=Path, required=True, help='New output folder')
    args = parser.parse_args()
    source = args.bundle/'frame_data.csv'
    manifest = json.loads((args.bundle/'manifest.json').read_text())
    expected_hash = manifest.get('output_sha256', {}).get('frame_data.csv')
    if not expected_hash or hashlib.sha256(source.read_bytes()).hexdigest() != expected_hash:
        parser.error('frame_data.csv is absent from the manifest or its SHA-256 does not match')
    beetles, pairs = aggregate(source, args.start, args.end)
    args.output.mkdir(parents=True, exist_ok=False)
    _write_rows(args.output/'beetle_summary.csv', beetles)
    _write_rows(args.output/'pair_summary.csv', pairs)
    (args.output/'reaggregation.json').write_text(json.dumps(dict(
        source_bundle=str(args.bundle.resolve()), source_frame_data=str(source.resolve()),
        source_sha256=expected_hash,
        start_global_frame=args.start, end_global_frame_inclusive=args.end,
        source_qc_status=manifest.get('qc_status'), settings=manifest.get('settings')),
        indent=2)+'\n')
    print(args.output)


if __name__ == '__main__':
    main()
