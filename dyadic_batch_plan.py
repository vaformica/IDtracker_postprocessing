#!/usr/bin/env python3
"""Plan one immutable background-on 2026 fight run per distinct dyadic TOML.

Inputs are fresh read-only Firebird inventories. Byte-identical source TOMLs
share one computation but every source path remains in the plan.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import defaultdict
from pathlib import Path


def plan(audit: list[dict], matches: list[dict]) -> dict:
    matched = {row['path']: row for row in matches}
    grouped = defaultdict(list)
    exceptions = []
    for row in audit:
        if row.get('error') or row.get('animals') != 2 or row.get('roi_count') != 2 or not row.get('video_exists'):
            exceptions.append({k: row.get(k) for k in ('path', 'sha256', 'animals', 'roi_count', 'video_exists', 'error')})
            continue
        grouped[row['sha256']].append(row)
    tasks = []
    for source_hash, variants in sorted(grouped.items()):
        variants.sort(key=lambda item: item['path'])
        known = [(row, matched.get(row['path'], {}).get('matches', [])) for row in variants]
        reused = next(((row, found[0]) for row, found in known if found), None)
        chosen = reused[0] if reused else variants[0]
        tasks.append({
            'id': source_hash[:16],
            'source_path': chosen['path'],
            'source_sha256': source_hash,
            'all_source_paths': [row['path'] for row in variants],
            'reused_session': reused[1]['session'] if reused else None,
            'original_use_bkg': chosen['use_bkg'],
            'video_paths': chosen['videos'],
            'tracking_intervals': chosen['intervals'],
            'number_of_animals': 2,
            'roi_count': 2,
        })
    return {'schema': 'dyadic-fight-batch-plan-v1',
            'created_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
            'scope': '2026_Videos/2026_Fights, excluding debug folders',
            'source_file_count': len(audit),
            'eligible_source_file_count': sum(len(task['all_source_paths']) for task in tasks),
            'distinct_task_count': len(tasks),
            'reused_task_count': sum(bool(task['reused_session']) for task in tasks),
            'new_tracking_task_count': sum(not task['reused_session'] for task in tasks),
            'exceptions': exceptions, 'tasks': tasks}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--matches', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = plan(json.loads(args.audit.read_text()), json.loads(args.matches.read_text()))
    if args.output.exists():
        raise FileExistsError(args.output)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: value for k, value in result.items() if k.endswith('_count')}, indent=2))


if __name__ == '__main__':
    main()
