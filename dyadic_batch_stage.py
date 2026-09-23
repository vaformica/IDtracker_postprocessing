#!/usr/bin/env python3
"""Stage and submit the audited 2026 dyadic fight batch on Firebird.

This is run on Firebird after uploading the plan and versioned code archive.
Source TOMLs and prior IDtracker sessions are only read, never changed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
import tarfile
import tomllib
from pathlib import Path

FIELDS = ('name', 'video_paths', 'intensity_ths', 'area_ths',
          'tracking_intervals', 'number_of_animals', 'use_bkg',
          'check_segmentation', 'track_wo_identities', 'roi_list',
          'background_subtraction_stat')
PYTHON = '/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python'


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def submitted_text(raw: str) -> str:
    text, count = re.subn(r'(?m)^([ \t]*use_bkg[ \t]*=[ \t]*)(true|false)[ \t]*$',
                          r'\g<1>true', raw, count=1)
    if count != 1:
        raise ValueError('Expected one top-level use_bkg setting')
    return text


def submit(root: Path, kind: str, count: int) -> str | None:
    if not count:
        return None
    is_new = kind == 'new'
    command = [PYTHON, str(root/'code/dyadic_batch_worker.py'), '--root', str(root), '--kind', kind]
    options = ['sbatch', '--parsable', f'--job-name=dyad_{kind}_review',
               '--partition=gpu' if is_new else '--partition=compute',
               '--gres=gpu:1' if is_new else '--gres=gpu:0',
               '--cpus-per-task=8' if is_new else '--cpus-per-task=4',
               '--mem=48G' if is_new else '--mem=24G',
               '--time=08:00:00' if is_new else '--time=03:00:00',
               f'--array=0-{count-1}%{3 if is_new else 4}',
               f'--chdir={root}', f'--output={root}/logs/%A_%a.log',
               '--wrap', 'export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1; '
                         + 'export MPLCONFIGDIR=' + shlex.quote(str(root/'mpl_cache')) + '; '
                         + 'exec ' + shlex.join(command)]
    if not is_new:
        options = [part for part in options if part != '--gres=gpu:0']
    result = subprocess.run(options, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f'{kind} sbatch failed: {result.stderr}')
    return result.stdout.strip().split(';', 1)[0]


def stage(plan_path: Path, archive: Path, root: Path, do_submit: bool) -> dict:
    plan = json.loads(plan_path.read_text())
    if plan['schema'] != 'dyadic-fight-batch-plan-v1' or root.exists():
        raise ValueError('Invalid plan or batch root already exists')
    tasks = []
    for task in plan['tasks']:
        for path_text in task['all_source_paths']:
            if digest(Path(path_text).read_bytes()) != task['source_sha256']:
                raise ValueError(f'Source TOML hash changed: {path_text}')
        raw = Path(task['source_path']).read_text()
        data = tomllib.loads(raw)
        new = tomllib.loads(submitted_text(raw))
        if (new['number_of_animals'] != 2 or len(new['roi_list']) != 2 or
                new['use_bkg'] is not True or
                any(new.get(key) != data.get(key) for key in data if key != 'use_bkg') or
                not all(Path(video).is_file() for video in new['video_paths'])):
            raise ValueError(f'Unsafe derived TOML: {task["source_path"]}')
        if task['reused_session']:
            session = Path(task['reused_session'])
            trajectory = session/'trajectories/trajectories.npy'
            if not trajectory.is_file():
                raise ValueError(f'Reused session lost trajectory: {session}')
            config = json.loads((session/'session.json').read_text())
            if any(new.get(key) != config.get(key) for key in FIELDS if key in new):
                raise ValueError(f'Reused session settings changed: {session}')
        tasks.append((task, raw, submitted_text(raw)))
    root.mkdir(parents=True, exist_ok=False)
    (root/'code').mkdir()
    (root/'logs').mkdir()
    with tarfile.open(archive, 'r:gz') as stream:
        stream.extractall(root/'code', filter='data')
    (root/'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
    ids = {'new': [], 'reuse': []}
    for task, original, derived in tasks:
        folder = root/'tasks'/task['id']
        (folder/'input').mkdir(parents=True)
        (folder/'input/source.toml').write_text(original)
        (folder/'input/submitted.toml').write_text(derived)
        task = {**task, 'submitted_sha256': digest(derived.encode()),
                'staged_utc': dt.datetime.now(dt.timezone.utc).isoformat()}
        (folder/'task.json').write_text(json.dumps(task, indent=2) + '\n')
        ids['reuse' if task['reused_session'] else 'new'].append(task['id'])
    for kind, values in ids.items():
        (root/f'{kind}_ids.json').write_text(json.dumps(values, indent=2) + '\n')
    receipt = {'schema': 'dyadic-fight-batch-receipt-v1', 'root': str(root),
               'staged_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'new_count': len(ids['new']), 'reuse_count': len(ids['reuse']),
               'source_file_count': plan['source_file_count'],
               'new_job_id': None, 'reuse_job_id': None}
    (root/'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    if do_submit:
        for kind in ('reuse', 'new'):
            receipt[f'{kind}_job_id'] = submit(root, kind, len(ids[kind]))
            (root/'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--submit', action='store_true')
    args = parser.parse_args()
    print(json.dumps(stage(args.plan, args.archive, args.root, args.submit), indent=2))


if __name__ == '__main__':
    main()
