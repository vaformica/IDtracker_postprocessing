#!/usr/bin/env python3
"""Create corrected, immutable dyadic analysis and review from a completed session.

IDtracker TOML tracking intervals use an exclusive end; the postprocessor's
--end is inclusive. This worker records the conversion in final_status.json.
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

from dyadic_batch_worker import (CODE, FFMPEG, FFPROBE, IDTRACKER_PYTHON,
                                 trajectory_frame_count, valid_sessions)


def write_status(folder: Path, stage: str, **details: object) -> None:
    data = dict(stage=stage, utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                slurm_job_id=os.environ.get('SLURM_JOB_ID'), **details)
    target = folder / 'final_status.json'
    partial = folder / 'final_status.json.partial'
    partial.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    partial.replace(target)
    print(json.dumps(data), flush=True)


def session_for(task: dict, folder: Path) -> Path:
    if task['reused_session']:
        session = Path(task['reused_session'])
        if not (session / 'trajectories/trajectories.npy').is_file():
            raise FileNotFoundError(session)
        return session
    sessions = valid_sessions(folder / 'tracking_output')
    if len(sessions) != 1:
        raise RuntimeError(f'Expected one completed trajectory session, found {len(sessions)}')
    return sessions[0]


def run(task: dict, folder: Path) -> None:
    if (folder / 'final_status.json').is_file():
        previous = json.loads((folder / 'final_status.json').read_text())
        if previous['stage'] == 'COMPLETE_UNREVIEWED':
            print('Already complete', folder)
            return
    session = session_for(task, folder)
    submitted = tomllib.loads((folder / 'input/submitted.toml').read_text())
    start, end_exclusive = submitted['tracking_intervals'][0]
    frame_count = trajectory_frame_count(session)
    end_inclusive = min(end_exclusive - 1, frame_count - 1)
    if start > end_inclusive:
        raise ValueError(f'Empty analysis window: {start=} {end_exclusive=} {frame_count=}')
    config = json.loads((session / 'session.json').read_text())
    label = submitted.get('name') or config.get('name') or Path(task['source_path']).stem
    analysis = folder / 'analysis_final'
    review = folder / 'review_final'
    if analysis.exists() or review.exists():
        raise FileExistsError('Existing final outputs need inspection before retry')
    command = [sys.executable, str(CODE / 'run_group_pipeline.py'),
               '--session', str(session), '--source-video', submitted['video_paths'][0],
               '--analysis-output', str(analysis), '--review-output', str(review),
               '--start', str(start), '--end', str(end_inclusive),
               '--fps', str(config.get('frames_per_second', 30)),
               '--label', label, '--pdf-name', f'{task["id"]}.pdf',
               '--idtracker-python', str(IDTRACKER_PYTHON),
               '--ffmpeg', FFMPEG, '--ffprobe', FFPROBE]
    write_status(folder, 'FINAL_POSTPROCESSING', session=str(session),
                 toml_interval=[start, end_exclusive],
                 processed_inclusive_interval=[start, end_inclusive],
                 trajectory_frame_count=frame_count, command=command)
    with (folder / 'postprocess_final.log').open('x') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=folder, check=True)
    quality = folder / 'quality_final.json'
    command = [sys.executable, str(CODE / 'dyadic_quality.py'),
               '--analysis', str(analysis), '--session', str(session),
               '--source-toml', task['source_path'],
               '--source-sha256', task['source_sha256'], '--output', str(quality)]
    with (folder / 'quality_final.log').open('x') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=folder, check=True)
    write_status(folder, 'COMPLETE_UNREVIEWED', session=str(session),
                 toml_interval=[start, end_exclusive],
                 processed_inclusive_interval=[start, end_inclusive],
                 trajectory_frame_count=frame_count, analysis=str(analysis),
                 review=str(review), quality=str(quality))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--kind', choices=['new', 'reuse'], required=True)
    args = parser.parse_args()
    index = int(os.environ['SLURM_ARRAY_TASK_ID'])
    task_id = json.loads((args.root / f'{args.kind}_ids.json').read_text())[index]
    folder = args.root / 'tasks' / task_id
    task = json.loads((folder / 'task.json').read_text())
    try:
        run(task, folder)
    except BaseException as exc:
        write_status(folder, 'FAILED', error=repr(exc))
        raise


if __name__ == '__main__':
    main()
