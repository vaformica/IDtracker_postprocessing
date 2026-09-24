#!/usr/bin/env python3
"""Recover student TOMLs that requested interactive segmentation checking.

Only the execution-stop flag changes; video, ROI, thresholds, tracking interval,
animal count, and background subtraction remain identical. The original and
submitted TOMLs and the failed segmentation outputs remain untouched.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path

from dyadic_batch_worker import IDTRACKER, valid_sessions


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(folder: Path) -> None:
    original = folder / 'input/submitted.toml'
    old = tomllib.loads(original.read_text())
    if old.get('check_segmentation') is not True:
        raise ValueError('This recovery applies only to check_segmentation=true')
    if old.get('use_bkg') is not True:
        raise ValueError('Background subtraction must remain on')
    revised = re.sub(r'(?m)^check_segmentation[ \t]*=[ \t]*true[ \t]*$',
                     'check_segmentation = false', original.read_text(), count=1)
    if revised == original.read_text():
        raise ValueError('Could not replace the exact stop flag')
    retry = folder / 'input/submitted_check_off.toml'
    if retry.exists() and retry.read_text() != revised:
        raise FileExistsError(retry)
    if not retry.exists():
        retry.write_text(revised)
    new = tomllib.loads(retry.read_text())
    changed = [key for key in old if old[key] != new.get(key)]
    if changed != ['check_segmentation']:
        raise ValueError(f'Unexpected TOML changes: {changed}')
    output = folder / 'tracking_output/recovery_check_off'
    if output.exists():
        raise FileExistsError(f'Recovery output already exists: {output}')
    output.mkdir(parents=True)
    receipt = dict(schema='dyadic-segmentation-stop-recovery-v1',
                   utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   original_submitted_toml=str(original),
                   original_submitted_sha256=digest(original),
                   retry_toml=str(retry), retry_sha256=digest(retry),
                   changed_field='check_segmentation', old_value=True, new_value=False,
                   original_tracking_output=str(folder / 'tracking_output'),
                   recovery_tracking_output=str(output),
                   reason='Unattended IDtracker stopped at the segmentation-check gate after a few extra-blob frames.')
    (folder / 'recovery_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    command = [str(IDTRACKER), '--track', '--load', str(retry),
               '--output_dir', str(output), '--number_of_parallel_workers', '8',
               '--device', 'cuda', '--data_policy', 'all']
    log = folder / 'idtracker_recovery_check_off.log'
    with log.open('x') as stream:
        result = subprocess.run(command, cwd=folder, stdout=stream,
                                stderr=subprocess.STDOUT, check=False)
    sessions = valid_sessions(output)
    status = dict(stage='TRACKING_COMPLETE' if len(sessions) == 1 else 'FAILED',
                  utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                  slurm_job_id=os.environ.get('SLURM_JOB_ID'),
                  idtracker_exit_code=result.returncode,
                  sessions=[str(session) for session in sessions], log=str(log))
    (folder / 'recovery_status.json').write_text(json.dumps(status, indent=2) + '\n')
    print(json.dumps(status), flush=True)
    if len(sessions) != 1:
        raise RuntimeError(f'Recovery produced {len(sessions)} valid sessions')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--task-id', required=True)
    args = parser.parse_args()
    run(args.root / 'tasks' / args.task_id)


if __name__ == '__main__':
    main()
