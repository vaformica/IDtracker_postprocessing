#!/usr/bin/env python3
"""Firebird Slurm worker for one immutable 2026 fight TOML and its review.

Usage: python dyadic_batch_worker.py --root BATCH --kind new|reuse
The Slurm array index selects a task from new_ids.json or reuse_ids.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np

IDTRACKER = Path('/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/idtrackerai')
IDTRACKER_PYTHON = IDTRACKER.with_name('python')
FFMPEG = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg'
FFPROBE = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'
CODE = Path(__file__).resolve().parent


def status(folder: Path, stage: str, **details) -> None:
    payload = {'stage': stage, 'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'slurm_job_id': os.environ.get('SLURM_JOB_ID'), **details}
    target = folder / 'status.json'
    partial = target.with_suffix('.json.partial')
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    partial.replace(target)
    print(json.dumps(payload), flush=True)


def valid_sessions(output: Path) -> list[Path]:
    sessions = []
    for path in output.rglob('session.json'):
        trajectory = path.parent / 'trajectories/trajectories.npy'
        if not trajectory.is_file():
            continue
        try:
            array = np.load(trajectory, allow_pickle=True)
            if array.shape == ():
                array = array.item()
            if isinstance(array, dict):
                array = array.get('trajectories')
            array = np.asarray(array)
            if array.ndim == 3 and array.shape[1:] == (2, 2) and np.isfinite(array).any():
                sessions.append(path.parent)
        except Exception:
            pass
    return sessions


def trajectory_frame_count(session: Path) -> int:
    array = np.load(session / 'trajectories/trajectories.npy', allow_pickle=True)
    if array.shape == ():
        array = array.item()
    if isinstance(array, dict):
        array = array['trajectories']
    return len(array)


def run(task: dict, root: Path) -> None:
    folder = root / 'tasks' / task['id']
    submitted = folder / 'input/submitted.toml'
    data = tomllib.loads(submitted.read_text())
    if data['number_of_animals'] != 2 or len(data['roi_list']) != 2 or data['use_bkg'] is not True:
        raise ValueError('Submitted configuration is not background-on dyadic with arena and fungus')
    if task['reused_session']:
        session = Path(task['reused_session'])
        if not (session / 'trajectories/trajectories.npy').is_file():
            raise FileNotFoundError(f'Reused trajectory disappeared: {session}')
        status(folder, 'REUSED_EXACT_SETTINGS', session=str(session))
    else:
        output = folder / 'tracking_output'
        if output.exists():
            sessions = valid_sessions(output)
            if len(sessions) != 1:
                raise RuntimeError('Tracking output exists without one valid session; inspect before retrying')
            session = sessions[0]
        else:
            output.mkdir(parents=True, exist_ok=False)
            command = [str(IDTRACKER), '--track', '--load', str(submitted),
                       '--output_dir', str(output), '--number_of_parallel_workers', '8',
                       '--device', 'cuda', '--data_policy', 'all']
            status(folder, 'TRACKING', command=command)
            log_path = folder/f'idtracker_attempt_{len(list(folder.glob("idtracker_attempt_*.log")))+1}.log'
            with log_path.open('x') as stream:
                result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                        cwd=folder, check=False)
            sessions = valid_sessions(output)
            if len(sessions) != 1:
                raise RuntimeError(f'IDtracker exit {result.returncode}; found {len(sessions)} valid sessions; inspect {log_path}')
            if result.returncode and 'Success' not in log_path.read_text(errors='replace'):
                raise RuntimeError(f'IDtracker exit {result.returncode} without success marker')
            session = sessions[0]
            status(folder, 'TRACKING_COMPLETE', session=str(session), idtracker_exit_code=result.returncode)
    config = json.loads((session/'session.json').read_text())
    start, end_exclusive = data['tracking_intervals'][0]
    end = min(end_exclusive - 1, trajectory_frame_count(session) - 1)
    if start > end:
        raise ValueError(f'Empty analysis window after IDtracker interval conversion: {start=}, {end_exclusive=}')
    video = Path(data['video_paths'][0])
    label = data.get('name') or config.get('name') or Path(task['source_path']).stem
    pipeline = [sys.executable, str(CODE/'run_group_pipeline.py'),
                '--session', str(session), '--source-video', str(video),
                '--analysis-output', str(folder/'analysis'),
                '--review-output', str(folder/'review'),
                '--start', str(start), '--end', str(end),
                '--fps', str(config.get('frames_per_second', 30)),
                '--label', label, '--pdf-name', f'{task["id"]}.pdf',
                '--idtracker-python', str(IDTRACKER_PYTHON),
                '--ffmpeg', FFMPEG, '--ffprobe', FFPROBE]
    status(folder, 'POSTPROCESSING', session=str(session),
           toml_interval=[start, end_exclusive], processed_inclusive_interval=[start, end],
           command=pipeline)
    with (folder/'postprocess.log').open('x') as stream:
        subprocess.run(pipeline, stdout=stream, stderr=subprocess.STDOUT,
                       cwd=folder, check=True)
    quality = [sys.executable, str(CODE/'dyadic_quality.py'),
               '--analysis', str(folder/'analysis'), '--session', str(session),
               '--source-toml', task['source_path'], '--source-sha256', task['source_sha256'],
               '--output', str(folder/'quality.json')]
    with (folder/'quality.log').open('x') as stream:
        subprocess.run(quality, stdout=stream, stderr=subprocess.STDOUT,
                       cwd=folder, check=True)
    status(folder, 'COMPLETE_UNREVIEWED', session=str(session),
           analysis=str(folder/'analysis'), review=str(folder/'review'),
           quality=str(folder/'quality.json'))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--kind', choices=('new', 'reuse'), required=True)
    args = parser.parse_args()
    index = int(os.environ['SLURM_ARRAY_TASK_ID'])
    task_id = json.loads((args.root/f'{args.kind}_ids.json').read_text())[index]
    task = json.loads((args.root/'tasks'/task_id/'task.json').read_text())
    try:
        run(task, args.root)
    except BaseException as exc:
        status(args.root/'tasks'/task_id, 'FAILED', error=repr(exc))
        raise


if __name__ == '__main__':
    main()
