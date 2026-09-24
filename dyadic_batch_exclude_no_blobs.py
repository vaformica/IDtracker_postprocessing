#!/usr/bin/env python3
"""Document a tracking input that cannot produce a review with its given settings."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--task-id', required=True)
    args = parser.parse_args()
    folder = args.root / 'tasks' / args.task_id
    log = folder / 'idtracker_attempt_1.log'
    if 'No animals detected in the video' not in log.read_text(errors='replace'):
        raise ValueError('Cannot mark exclusion without IDtracker no-animal evidence')
    if list((folder / 'tracking_output').rglob('trajectories.npy')):
        raise ValueError('Tracking trajectory exists; do not exclude')
    target = folder / 'final_status.json'
    if target.exists():
        raise FileExistsError(target)
    task = json.loads((folder / 'task.json').read_text())
    payload = dict(stage='EXCLUDED_TRACKING_NO_BLOBS',
                   utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   source_toml=task['source_path'],
                   source_sha256=task['source_sha256'],
                   submitted_toml=str(folder / 'input/submitted.toml'),
                   idtracker_log=str(log),
                   reason='IDtracker 6.0.10 detected zero animal blobs using the source intensity and area thresholds with requested background subtraction. No trajectories exist, so PSC, PDF, and identity statistics cannot be generated without a separately labeled threshold change.')
    target.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps(payload))


if __name__ == '__main__':
    main()
