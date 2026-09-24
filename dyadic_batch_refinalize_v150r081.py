#!/usr/bin/env python3
"""Reprocess 2026 dyadic tracking with PSC 1.5.0 and paired reports 0.8.1-group.

Writes only new suffixed outputs; the older analysis is never overwritten.
The IDtracker interval ends exclusively, while postprocessing ends inclusively.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

from dyadic_batch_finalize import session_for
from dyadic_batch_worker import FFMPEG, FFPROBE, IDTRACKER_PYTHON, trajectory_frame_count
from persistent_groups import MODEL_VERSION
from psc_release_validation import validate_bundle
from six_beetle_processor import SCRIPT_VERSION

EXPECTED_MODEL = '1.5.0'
EXPECTED_PROCESSOR = '0.8.1-group'
CODE = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def status(folder: Path, stage: str, **details: object) -> None:
    target = folder / 'status_v150r081.json'
    partial = folder / 'status_v150r081.json.partial'
    payload = dict(stage=stage, model_version=MODEL_VERSION,
                   utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   slurm_job_id=os.environ.get('SLURM_JOB_ID'), **details)
    partial.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    partial.replace(target)
    print(json.dumps(payload), flush=True)


def run(root: Path, index: int) -> None:
    if MODEL_VERSION != EXPECTED_MODEL or SCRIPT_VERSION != EXPECTED_PROCESSOR:
        raise RuntimeError(f'Wrong deployed versions: model={MODEL_VERSION} processor={SCRIPT_VERSION}')
    task_id = json.loads((root / 'v130_ids.json').read_text())[index]
    folder = root / 'tasks' / task_id
    task = json.loads((folder / 'task.json').read_text())
    previous = folder / 'status_v150r081.json'
    if previous.is_file() and json.loads(previous.read_text()).get('stage') == 'COMPLETE_UNREVIEWED':
        print('Already complete', task_id)
        return
    analysis = folder / 'analysis_v150r081'
    review = folder / 'review_v150r081'
    quality = folder / 'quality_v150r081.json'
    if any(p.exists() for p in (analysis, review, quality)):
        raise FileExistsError(f'Inspect existing v1.4 outputs before retry: {task_id}')
    try:
        submitted_path = folder / 'input/submitted.toml'
        if digest(Path(task['source_path'])) != task['source_sha256']:
            raise ValueError('Source TOML changed')
        submitted = tomllib.loads(submitted_path.read_text())
        session = session_for(task, folder)
        trajectory = session / 'trajectories/trajectories.npy'
        start, end_exclusive = submitted['tracking_intervals'][0]
        frame_count = trajectory_frame_count(session)
        end_inclusive = min(end_exclusive - 1, frame_count - 1)
        if start > end_inclusive:
            raise ValueError(f'Empty interval: {start}, {end_exclusive}, {frame_count}')
        config = json.loads((session / 'session.json').read_text())
        label = submitted.get('name') or config.get('name') or Path(task['source_path']).stem
        command = [sys.executable, str(CODE / 'run_group_pipeline.py'),
                   '--session', str(session), '--source-toml', task['source_path'],
                   '--source-video', submitted['video_paths'][0],
                   '--analysis-output', str(analysis), '--review-output', str(review),
                   '--start', str(start), '--end', str(end_inclusive),
                   '--fps', str(config.get('frames_per_second', 30)),
                   '--label', label, '--pdf-name', f'{task_id}.pdf',
                   '--idtracker-python', str(IDTRACKER_PYTHON),
                   '--ffmpeg', FFMPEG, '--ffprobe', FFPROBE]
        status(folder, 'RUNNING', command=command, session=str(session),
               source_sha256=task['source_sha256'], submitted_sha256=digest(submitted_path),
               trajectory_sha256=digest(trajectory), interval_inclusive=[start, end_inclusive],
               code_sha256=digest(CODE / 'persistent_groups.py'))
        with (folder / 'postprocess_v150r081.log').open('x') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=folder, check=True)
        manifest = json.loads((analysis / 'manifest.json').read_text())
        if manifest['persistent_model_version'] != EXPECTED_MODEL or manifest['script_version'] != EXPECTED_PROCESSOR:
            raise ValueError('Analysis manifest has wrong model or processor version')
        validate_bundle(analysis, EXPECTED_MODEL, EXPECTED_PROCESSOR)
        qc_command = [sys.executable, str(CODE / 'dyadic_quality.py'),
                      '--analysis', str(analysis), '--session', str(session),
                      '--source-toml', task['source_path'],
                      '--source-sha256', task['source_sha256'], '--output', str(quality)]
        with (folder / 'quality_v150r081.log').open('x') as log:
            subprocess.run(qc_command, stdout=log, stderr=subprocess.STDOUT, cwd=folder, check=True)
        needed = [analysis / f'{task_id}.pdf', analysis / 'frame_data.csv',
                  review / 'interaction_review.html', review / 'review_video.mp4', quality]
        if any(not p.is_file() or p.stat().st_size == 0 for p in needed):
            raise RuntimeError('Missing v1.4 PDF, frame CSV, HTML, video, or quality report')
        status(folder, 'COMPLETE_UNREVIEWED', session=str(session),
               source_sha256=task['source_sha256'], submitted_sha256=digest(submitted_path),
               trajectory_sha256=digest(trajectory), interval_inclusive=[start, end_inclusive],
               code_sha256=digest(CODE / 'persistent_groups.py'),
               analysis=str(analysis), review=str(review), quality=str(quality))
    except BaseException as exc:
        status(folder, 'FAILED', error=repr(exc))
        raise


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: dyadic_batch_refinalize_v150r081.py BATCH_ROOT')
    run(Path(sys.argv[1]), int(os.environ['SLURM_ARRAY_TASK_ID']))
