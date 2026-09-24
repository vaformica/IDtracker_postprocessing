#!/usr/bin/env python3
"""Flag sustained conflicts between raw IDtracker detections and PSC output.

This is a review aid, not an identity correction: raw IDs can themselves be
wrong in fights. It works for any number of animals in frame_data.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def xy(row: dict, prefix: str) -> tuple[float, float] | None:
    try:
        point = (float(row[prefix + 'x']), float(row[prefix + 'y']))
        return point if all(math.isfinite(v) for v in point) else None
    except (KeyError, ValueError, TypeError):
        return None


def nearest(point: tuple[float, float], blobs: list[dict], radius: float) -> int | None:
    if not blobs:
        return None
    distances = [math.dist(point, blob['centroid']) for blob in blobs]
    index = min(range(len(distances)), key=distances.__getitem__)
    return index if distances[index] <= radius else None


def longest_consecutive(frames: list[int]) -> int:
    longest = current = 0
    previous = None
    for frame in sorted(frames):
        current = current + 1 if previous is not None and frame == previous + 1 else 1
        longest = max(longest, current)
        previous = frame
    return longest


def audit(frame_data: Path, blob_evidence: Path, trajectory: Path,
          output: Path, radius: float) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    blobs = json.loads(blob_evidence.read_text())['frames']
    trajectory_data = np.load(trajectory, allow_pickle=True)
    if trajectory_data.shape == ():
        trajectory_data = trajectory_data.item()
    probabilities = np.asarray(trajectory_data.get('id_probabilities'))
    by_frame = defaultdict(dict)
    raw_conflicts = []
    with frame_data.open(newline='') as stream:
        for row in csv.DictReader(stream):
            frame = int(row['global_frame'])
            animal = int(row['animal_id'])
            by_frame[frame][animal] = row
            if row['location_source'] != 'PSCP_BLOB':
                continue
            raw, corrected = xy(row, 'raw_'), xy(row, '')
            if raw is None or corrected is None:
                continue
            distance = math.dist(raw, corrected)
            if distance <= radius:
                continue
            frame_blobs = blobs.get(str(frame), [])
            raw_blob = nearest(raw, frame_blobs, radius)
            psc_blob = nearest(corrected, frame_blobs, radius)
            if raw_blob is None or psc_blob is None or raw_blob == psc_blob:
                continue
            score = float(probabilities[frame, animal, 0]) if probabilities.ndim == 3 else None
            raw_conflicts.append(dict(global_frame=frame, animal_id=animal,
                                      raw_x=raw[0], raw_y=raw[1],
                                      psc_x=corrected[0], psc_y=corrected[1],
                                      distance_px=round(distance, 3),
                                      raw_blob_identities=';'.join(map(str, frame_blobs[raw_blob].get('identities', []))),
                                      psc_blob_identities=';'.join(map(str, frame_blobs[psc_blob].get('identities', []))),
                                      group_id=row['group_id'],
                                      pscp_partners=row['pscp_partners'],
                                      idtracker_identity_score=score if math.isfinite(score) else ''))
    multi_blob_conflicts = []
    for frame, rows in by_frame.items():
        for blob in blobs.get(str(frame), []):
            ids = sorted(set(int(i) - 1 for i in blob.get('identities', []) if i is not None))
            if len(ids) < 3 or any(animal not in rows for animal in ids):
                continue
            groups = {rows[animal]['group_id'] for animal in ids}
            corrected = [xy(rows[animal], '') for animal in ids]
            distances = [math.dist(point, blob['centroid']) if point else math.inf
                         for point in corrected]
            if len(groups) == 1 and all(distance <= radius for distance in distances):
                continue
            multi_blob_conflicts.append(dict(global_frame=frame,
                raw_identity_ids=';'.join(str(animal) for animal in ids),
                blob_x=blob['centroid'][0], blob_y=blob['centroid'][1],
                model_group_ids=';'.join(rows[animal]['group_id'] for animal in ids),
                model_distances_px=';'.join(f'{distance:.1f}' for distance in distances)))
    def save(name: str, records: list[dict]) -> None:
        with (output / name).open('w', newline='') as stream:
            if records:
                writer = csv.DictWriter(stream, records[0].keys())
                writer.writeheader()
                writer.writerows(records)
    save('pscp_raw_conflicts.csv', raw_conflicts)
    save('three_plus_identity_blob_conflicts.csv', multi_blob_conflicts)
    per_animal = {}
    for animal in sorted({row['animal_id'] for row in raw_conflicts}):
        group = [row for row in raw_conflicts if row['animal_id'] == animal]
        per_animal[str(animal)] = dict(conflict_frames=len(group),
            longest_consecutive_conflict_frames=longest_consecutive([row['global_frame'] for row in group]),
            median_displacement_px=float(np.median([row['distance_px'] for row in group])))
    result = dict(schema='psc-disagreement-audit-v1',
                  definition='PSC_BLOB coordinate differs from a separate raw IDtracker blob by more than the social radius; both blobs are detected. Flags require video review, not automatic identity correction.',
                  social_radius_px=radius,
                  total_pscp_raw_conflict_frames=len(raw_conflicts),
                  per_animal=per_animal,
                  three_plus_identity_blob_conflict_frames=len(multi_blob_conflicts),
                  three_plus_identity_blob_examples=multi_blob_conflicts[:10])
    (output / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frame-data', required=True, type=Path)
    parser.add_argument('--blob-evidence', required=True, type=Path)
    parser.add_argument('--trajectory', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--radius', type=float, default=60)
    args = parser.parse_args()
    print(json.dumps(audit(args.frame_data, args.blob_evidence,
                           args.trajectory, args.output, args.radius), indent=2))


if __name__ == '__main__':
    main()
