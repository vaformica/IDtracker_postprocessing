#!/usr/bin/env python3
"""Collect Firebird dyadic batch status and tracking-quality metrics.

This reads staged source receipts and completed derived outputs. It never
changes IDtracker trajectories or source TOMLs.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from pathlib import Path

from dyadic_quality import summary as quality_summary


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def collect(root: Path) -> dict:
    plan = json.loads((root/'plan.json').read_text())
    report = root/'reports'
    report.mkdir(exist_ok=True)
    status_rows = []
    quality_rows = []
    for task in plan['tasks']:
        folder = root/'tasks'/task['id']
        final_file = folder/'final_status.json'
        preliminary_file = folder/'status.json'
        state = json.loads(final_file.read_text()) if final_file.is_file() else {}
        preliminary = json.loads(preliminary_file.read_text()) if preliminary_file.is_file() else {}
        if state:
            stage = state['stage']
        else:
            stage = preliminary.get('stage', 'STAGED')
            if stage == 'COMPLETE_UNREVIEWED':
                stage = 'FINAL_PENDING'
            elif stage == 'FAILED':
                stage = 'PRELIMINARY_FAILED'
        status_rows.append(dict(task_id=task['id'], stage=stage,
                                source_path=task['source_path'], source_sha256=task['source_sha256'],
                                source_copy_count=len(task['all_source_paths']),
                                existing_session_reused=bool(task['reused_session']),
                                preliminary_stage=preliminary.get('stage',''),
                                slurm_job_id=state.get('slurm_job_id', preliminary.get('slurm_job_id','')),
                                error=state.get('error', preliminary.get('error',''))))
        if stage != 'COMPLETE_UNREVIEWED':
            continue
        quality_path = folder/'quality_final.json'
        data = json.loads(quality_path.read_text())
        if any('screened_without_pscp_missing_percent' not in item for item in data['animals']):
            revised = folder/'quality_v2.json'
            if not revised.is_file():
                data = quality_summary(Path(state['analysis']), Path(state['session']),
                                       task['source_path'], task['source_sha256'])
                revised.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
            else:
                data = json.loads(revised.read_text())
        for animal in data['animals']:
            quality_rows.append(dict(task_id=task['id'], source_path=task['source_path'],
                                     source_sha256=task['source_sha256'],
                                     idtracker_version=data.get('idtracker_version'),
                                     idtracker_estimated_accuracy=data.get('idtracker_estimated_accuracy'),
                                     idtracker_silhouette_score=data.get('idtracker_silhouette_score'),
                                     **animal))
    write_csv(report/'batch_status.csv', status_rows,
              ['task_id','stage','preliminary_stage','source_path','source_sha256','source_copy_count',
               'existing_session_reused','slurm_job_id','error'])
    metric_fields = ['task_id','source_path','source_sha256','idtracker_version',
                     'idtracker_estimated_accuracy','idtracker_silhouette_score',
                     'animal_id','analyzed_frames','raw_missing_frames','raw_missing_percent',
                     'screened_without_pscp_missing_frames','screened_without_pscp_missing_percent',
                     'after_pscp_missing_frames','after_pscp_missing_percent',
                     'pscp_missingness_reduction_percentage_points',
                     'raw_missing_frames_recovered_by_pscp','pscp_frames','pscp_percent',
                     'unresolved_pile_frames','independently_assigned_frames',
                     'independently_assigned_percent','longest_raw_missing_run_frames',
                     'longest_after_pscp_missing_run_frames','raw_adjacent_jumps_over_100px',
                     'identity_score_n','identity_score_mean','identity_score_median',
                     'identity_score_under_0_5_percent','identity_score_zero_percent']
    write_csv(report/'beetle_quality.csv', quality_rows, metric_fields)
    counts = Counter(row['stage'] for row in status_rows)
    overview = {'schema': 'dyadic-batch-quality-summary-v1',
                'source_file_count': plan['source_file_count'],
                'eligible_source_file_count': plan['eligible_source_file_count'],
                'distinct_task_count': len(plan['tasks']),
                'exception_count': len(plan['exceptions']),
                'status_counts': counts,
                'completed_beetle_count': len(quality_rows),
                'identity_score_note': 'Exported IDtracker scores are not calibrated probabilities of correct identity. High scores do not rule out merged blobs or swaps.',
                'missingness_note': 'Raw missingness uses original IDtracker coordinates. Screened without PSC excludes rejected assignments and inferred social positions. After PSC includes detection-supported social positions; no-detection pile frames remain missing.',
                'medians_across_completed_beetles': {key: statistics.median(row[key] for row in quality_rows)
                    for key in ('raw_missing_percent','screened_without_pscp_missing_percent',
                                'after_pscp_missing_percent','pscp_percent',
                                'independently_assigned_percent') } if quality_rows else {}}
    (report/'summary.json').write_text(json.dumps(overview, indent=2)+'\n')
    (report/'exceptions.json').write_text(json.dumps(plan['exceptions'], indent=2)+'\n')
    return overview


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    print(json.dumps(collect(args.root), indent=2))


if __name__ == '__main__':
    main()
