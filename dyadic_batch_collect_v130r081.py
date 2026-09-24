#!/usr/bin/env python3
"""Collect only 2026 dyadic PSC-1.3.0 / processor-0.8.1 reviews."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

MODEL = '1.3.0'
PROCESSOR = '0.8.1-group'
TAG = 'v130r081'


def write_rows(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def collect(root: Path) -> dict:
    plan = json.loads((root/'plan.json').read_text())
    report = root/f'reports_{TAG}'
    report.mkdir(exist_ok=True)
    statuses, beetles = [], []
    for task in plan['tasks']:
        folder = root/'tasks'/task['id']
        old = folder/'final_status.json'
        old_state = json.loads(old.read_text()) if old.is_file() else {}
        status_file = folder/f'status_{TAG}.json'
        state = json.loads(status_file.read_text()) if status_file.is_file() else {}
        excluded = old_state.get('stage') == 'EXCLUDED_TRACKING_NO_BLOBS'
        stage = 'EXCLUDED_TRACKING_NO_BLOBS' if excluded else state.get('stage','PENDING')
        statuses.append(dict(task_id=task['id'], stage=stage, source_path=task['source_path'],
                             source_sha256=task['source_sha256'],
                             error=old_state.get('error','') if excluded else state.get('error',''),
                             slurm_job_id=state.get('slurm_job_id','')))
        if stage != 'COMPLETE_UNREVIEWED':
            continue
        analysis = folder/f'analysis_{TAG}'
        review = folder/f'review_{TAG}'
        quality = folder/f'quality_{TAG}.json'
        manifest = json.loads((analysis/'manifest.json').read_text())
        if (manifest.get('persistent_model_version') != MODEL or
                manifest.get('script_version') != PROCESSOR or
                manifest.get('qc_status') != 'UNREVIEWED'):
            raise ValueError(f'Wrong version or QC state: {task["id"]}')
        for required in ('window_comparison.csv','region_comparison.csv','fungus_comparison.csv',
                         'frame_data.csv',f'{task["id"]}.pdf','OUTPUT_MANIFEST.md'):
            if not (analysis/required).is_file():
                raise FileNotFoundError(analysis/required)
        for required in ('interaction_review.html','review_video.mp4'):
            if not (review/required).is_file():
                raise FileNotFoundError(review/required)
        data = json.loads(quality.read_text())
        if data.get('model_version') != MODEL or data.get('group_processor_version') != PROCESSOR:
            raise ValueError(f'Quality version mismatch: {task["id"]}')
        for animal in data['animals']:
            row = dict(task_id=task['id'], source_path=task['source_path'],
                       source_sha256=task['source_sha256'],
                       model_version=MODEL, group_processor_version=PROCESSOR,
                       idtracker_version=data.get('idtracker_version'),
                       idtracker_estimated_accuracy=data.get('idtracker_estimated_accuracy'),
                       idtracker_silhouette_score=data.get('idtracker_silhouette_score'))
            row.update({k:v for k,v in animal.items() if k!='fungus_comparison'})
            for fungus, values in animal['fungus_comparison'].items():
                row.update({f'{fungus}_{key}':value for key,value in values.items()})
            beetles.append(row)
    write_rows(report/'batch_status.csv', statuses)
    write_rows(report/'beetle_quality.csv', beetles)
    counts = dict(Counter(row['stage'] for row in statuses))
    summary = dict(schema='dyadic-batch-psc-v130r081', model_version=MODEL,
                   group_processor_version=PROCESSOR, task_count=len(statuses),
                   animal_quality_rows=len(beetles), status_counts=counts,
                   source_tomls_untouched=True)
    (report/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__ == '__main__':
    print(json.dumps(collect(Path(sys.argv[1])),indent=2))
