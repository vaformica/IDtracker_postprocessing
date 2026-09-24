#!/usr/bin/env python3
"""Per-identity tracking-quality audit for a dyadic post-processing bundle.

Exported ID probabilities are IDtracker scores, not calibrated probabilities
that the identity is correct. Missingness denominators include every analyzed
frame, including those with no tracked position.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path


def present(row: dict, prefix: str) -> bool:
    try:
        return math.isfinite(float(row[prefix + 'x'])) and math.isfinite(float(row[prefix + 'y']))
    except (KeyError, TypeError, ValueError):
        return False


def longest_run(flags: list[bool]) -> int:
    best = current = 0
    for flag in flags:
        current = current + 1 if flag else 0
        best = max(best, current)
    return best


def summary(analysis: Path, session: Path, source_toml: str, source_hash: str) -> dict:
    with (analysis / 'frame_data.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    by_id = defaultdict(list)
    for row in rows:
        by_id[int(row['animal_id'])].append(row)
    config = json.loads((session / 'session.json').read_text())
    probability_path = session / 'trajectories/trajectories_csv/id_probabilities.csv'
    probabilities = []
    if probability_path.is_file():
        with probability_path.open(newline='') as stream:
            probabilities = list(csv.DictReader(stream))
    manifest = json.loads((analysis/'manifest.json').read_text())
    fungus_count = len(manifest['roi_order'])-1
    result = dict(schema='dyadic-tracking-quality-v2', source_toml=source_toml,
                  source_toml_sha256=source_hash, analysis_bundle=str(analysis),
                  session=str(session), model_version=manifest.get('persistent_model_version'),
                  group_processor_version=manifest.get('script_version'),
                  idtracker_version=config.get('version'), idtracker_estimated_accuracy=config.get('estimated_accuracy'),
                  idtracker_silhouette_score=config.get('silhouette_score'),
                  idtracker_ratio_accumulated_images=config.get('ratio_accumulated_images'),
                  identity_probability_definition='Mean and median of exported id_probabilitiesN scores on frames with a raw coordinate; scores are not calibrated correctness probabilities.',
                  animals=[])
    for animal, animal_rows in sorted(by_id.items()):
        animal_rows.sort(key=lambda row: int(row['global_frame']))
        total = len(animal_rows)
        raw = [present(row, 'raw_') for row in animal_rows]
        canonical = [present(row, '') for row in animal_rows]
        without_pscp = [known and row['location_source'] != 'PSCP_BLOB'
                        for known, row in zip(canonical, animal_rows)]
        pscp = [bool(row['pscp_partners']) for row in animal_rows]
        unresolved = [bool(row['unresolved_contact_partners']) for row in animal_rows]
        assigned = [row['location_source'] == 'ASSIGNED' for row in animal_rows]
        probs = []
        for row, located in zip(animal_rows, raw):
            frame = int(row['global_frame'])
            if not located or frame >= len(probabilities):
                continue
            try:
                value = float(probabilities[frame][f'id_probabilities{animal+1}'])
                if math.isfinite(value):
                    probs.append(value)
            except (KeyError, TypeError, ValueError):
                pass
        raw_jumps = 0
        for previous, current in zip(animal_rows, animal_rows[1:]):
            if int(current['global_frame']) != int(previous['global_frame']) + 1 or not present(previous, 'raw_') or not present(current, 'raw_'):
                continue
            distance = math.hypot(float(current['raw_x'])-float(previous['raw_x']),
                                  float(current['raw_y'])-float(previous['raw_y']))
            raw_jumps += distance > 100
        raw_missing = total - sum(raw)
        canonical_missing = total - sum(canonical)
        screened_missing = total - sum(without_pscp)
        recovered = sum(not original and corrected for original, corrected in zip(raw, canonical))
        fungus_comparison = {}
        for fungus in range(1,fungus_count+1):
            fungus_comparison[f'fungus_{fungus}'] = dict(
                raw_frames=sum(int(row[f'raw_fungus_{fungus}']) for row in animal_rows),
                pscp_frames=sum(int(row[f'fungus_{fungus}']) for row in animal_rows),
                raw_distance_px=sum(float(row['raw_step_distance_px']) for row in animal_rows
                    if row['raw_step_distance_px']!='' and int(row[f'raw_step_midpoint_fungus_{fungus}'])),
                pscp_distance_px=sum(float(row['step_distance_px']) for row in animal_rows
                    if row['step_distance_px']!='' and int(row[f'step_midpoint_fungus_{fungus}'])))
        result['animals'].append(dict(
            animal_id=animal, analyzed_frames=total, raw_missing_frames=raw_missing,
            raw_missing_percent=100*raw_missing/total,
            screened_without_pscp_missing_frames=screened_missing,
            screened_without_pscp_missing_percent=100*screened_missing/total,
            after_pscp_missing_frames=canonical_missing,
            after_pscp_missing_percent=100*canonical_missing/total,
            pscp_missingness_reduction_percentage_points=100*(screened_missing-canonical_missing)/total,
            raw_missing_frames_recovered_by_pscp=recovered,
            pscp_frames=sum(pscp), pscp_percent=100*sum(pscp)/total,
            unresolved_pile_frames=sum(unresolved),
            independently_assigned_frames=sum(assigned),
            independently_assigned_percent=100*sum(assigned)/total,
            longest_raw_missing_run_frames=longest_run([not value for value in raw]),
            longest_after_pscp_missing_run_frames=longest_run([not value for value in canonical]),
            raw_adjacent_jumps_over_100px=raw_jumps,
            raw_total_distance_px=sum(float(row['raw_step_distance_px']) for row in animal_rows
                                      if row['raw_step_distance_px']!=''),
            pscp_total_distance_px=sum(float(row['step_distance_px']) for row in animal_rows
                                       if row['step_distance_px']!=''),
            fungus_comparison=fungus_comparison,
            identity_score_n=len(probs),
            identity_score_mean=statistics.fmean(probs) if probs else None,
            identity_score_median=statistics.median(probs) if probs else None,
            identity_score_under_0_5_percent=100*sum(p<0.5 for p in probs)/len(probs) if probs else None,
            identity_score_zero_percent=100*sum(p==0 for p in probs)/len(probs) if probs else None))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', required=True, type=Path)
    parser.add_argument('--session', required=True, type=Path)
    parser.add_argument('--source-toml', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    data = summary(args.analysis, args.session, args.source_toml, args.source_sha256)
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
