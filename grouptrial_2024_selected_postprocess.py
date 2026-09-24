#!/usr/bin/env python3
"""Select and process the 2024 GroupTrial GUI runs without rerunning IDtracker.

Run ``plan BATCH_ROOT`` once on Firebird, then use a CPU-only Slurm array to
invoke ``run BATCH_ROOT``. Array index selects one immutable plan entry.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import numpy as np

SOURCE_ROOT = Path('/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024')
MANAGED = SOURCE_ROOT / 'managed_idtracker_runs'
PAIRED = MANAGED / 'paired_20260922_004953_utc'
PYTHON = '/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python'
FFMPEG = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg'
FFPROBE = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'
CODE = Path(__file__).resolve().parent
EXPECTED_PSC_MODEL = '1.3.0'
EXPECTED_GROUP_PROCESSOR = '0.8.1-group'
VARIANTS = {
    'groupagetrial01_062024_Box02_MIX.toml': 'shared_50_400_bkg_on',
    'groupagetrial02_062024_Box01_YOUNG.toml': 'human_bkg_on',
    'groupagetrial02_062024_Box03_OLD.toml': 'human_bkg_on',
    'groupagetrial03_062124_Box03_OLD.toml': 'human_bkg_on',
    'groupagetrial04_062124_Box01_MIX.toml': 'human_bkg_on',
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def trajectory(session: Path) -> Path:
    files = list((session / 'trajectories').glob('trajectories.npy'))
    if len(files) != 1 or not (session / 'session.json').is_file():
        raise ValueError(f'Missing complete session: {session}')
    return files[0]


def positions(path: Path) -> np.ndarray:
    result = np.load(path, allow_pickle=True)
    if result.shape == ():
        result = result.item()
    if isinstance(result, dict):
        result = result['trajectories']
    result = np.asarray(result)
    if result.ndim != 3 or result.shape[1:] != (6, 2):
        raise ValueError(f'Expected 6 trajectories: {path}: {result.shape}')
    return result


def candidate(run: Path) -> dict | None:
    request = run / 'submission_request.json'
    submitted = run / 'input/submitted.toml'
    if not request.is_file() or not submitted.is_file():
        return None
    receipt = json.loads(request.read_text())
    source = Path(receipt['source_toml'])
    source_hash = receipt['source_sha256']
    if digest(source) != source_hash:
        raise ValueError(f'Source TOML changed: {source}')
    toml = tomllib.loads(submitted.read_text())
    if toml['number_of_animals'] != 6 or len(toml['roi_list']) != 4 or not toml['use_bkg']:
        raise ValueError(f'Not background-on six-animal/four-ROI: {submitted}')
    if len(toml['tracking_intervals']) != 1 or len(toml['video_paths']) != 1:
        raise ValueError(f'Unexpected intervals/videos: {submitted}')
    start, end_exclusive = toml['tracking_intervals'][0]
    sessions = [path.parent for path in (run / 'idtracker_output').rglob('session.json')
                if (path.parent / 'trajectories/trajectories.npy').is_file()]
    if len(sessions) != 1:
        return None
    session = sessions[0]
    path = trajectory(session)
    data = positions(path)
    if start < 0 or start >= end_exclusive or end_exclusive > len(data):
        raise ValueError(f'Invalid interval for trajectory: {submitted}: {len(data)}')
    window = data[start:end_exclusive]
    raw_missing = 100 * (1 - np.isfinite(window).all(axis=-1).mean())
    return dict(source_toml=str(source), source_sha256=source_hash,
                submitted_toml=str(submitted), submitted_toml_sha256=digest(submitted),
                run_dir=str(run), session=str(session), trajectory=str(path),
                trajectory_sha256=digest(path), start=start,
                end_exclusive=end_exclusive, frame_count=end_exclusive-start,
                video=toml['video_paths'][0], fps=json.loads((session/'session.json').read_text()).get('frames_per_second', 30),
                raw_missing_percent=float(raw_missing),
                run_folder_label_mismatch=source.stem not in run.name and run.parent != PAIRED,
                session_label_mismatch=source.stem not in session.name)


def make_plan(root: Path) -> None:
    if (root/'plan.json').exists() or (root/'tasks').exists():
        raise FileExistsError(f'Batch already planned: {root}')
    originals: dict[str, list[dict]] = {}
    for run in sorted(MANAGED.glob('20260922_*')):
        item = candidate(run)
        if item:
            originals.setdefault(Path(item['source_toml']).name, []).append(item)
    chosen = []
    for filename in sorted(set(originals) | set(VARIANTS)):
        if filename in VARIANTS:
            run = PAIRED / (Path(filename).stem + '__' + VARIANTS[filename])
            selected = candidate(run)
            if selected is None:
                raise ValueError(f'Paired choice lacks trajectory: {run}')
            reason = f'Paired comparison: {VARIANTS[filename]} selected provisionally from raw missingness and all-six presence.'
        else:
            selected = min(originals[filename], key=lambda x: x['raw_missing_percent'])
            reason = 'Only original usable candidate, or lowest raw missingness among duplicate GUI attempts.'
        selected = {**selected, 'choice_reason': reason,
                    'alternative_runs': [item['run_dir'] for item in originals.get(filename, [])
                                         if item['run_dir'] != selected['run_dir']]}
        chosen.append(selected)
    if len(chosen) != 11:
        raise ValueError(f'Expected 11 distinct GUI TOMLs, found {len(chosen)}')
    root.mkdir(parents=True, exist_ok=True)
    (root/'logs').mkdir()
    (root/'tasks').mkdir()
    payload = dict(schema='grouptrial-2024-selected-postprocess-v1',
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   purpose='One CPU-only six-beetle postprocessing output per distinct GUI source TOML.',
                   source_submission_count=13, distinct_source_count=len(chosen),
                   review_status='UNREVIEWED; tracking-quality choice is provisional.',
                   tasks=chosen)
    (root/'plan.json').write_text(json.dumps(payload, indent=2)+'\n')
    print(json.dumps({'root':str(root),'distinct':len(chosen),
                      'selected':[(Path(x['source_toml']).name,round(x['raw_missing_percent'],2)) for x in chosen]}, indent=2))


def write_status(folder: Path, stage: str, **details: object) -> None:
    data = dict(stage=stage, utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                slurm_job_id=os.environ.get('SLURM_JOB_ID'), **details)
    partial = folder/'status.json.partial'
    partial.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    partial.replace(folder/'status.json')
    print(json.dumps(data), flush=True)


def process(root: Path) -> None:
    tasks = json.loads((root/'plan.json').read_text())['tasks']
    task = tasks[int(os.environ['SLURM_ARRAY_TASK_ID'])]
    label = Path(task['source_toml']).stem
    folder = root/'tasks'/label
    folder.mkdir(exist_ok=True)
    if (folder/'status.json').is_file() and json.loads((folder/'status.json').read_text())['stage'] == 'COMPLETE_UNREVIEWED':
        print('Already complete:',folder)
        return
    try:
        if digest(Path(task['trajectory'])) != task['trajectory_sha256'] or digest(Path(task['submitted_toml'])) != task['submitted_toml_sha256']:
            raise ValueError('Input hash changed after plan creation')
        end_inclusive = task['end_exclusive'] - 1
        command = [PYTHON, str(CODE/'run_group_pipeline.py'),
                   '--session', task['session'], '--source-toml', task['source_toml'], '--source-video', task['video'],
                   '--analysis-output', str(folder/'analysis'),
                   '--review-output', str(folder/'review'),
                   '--start', str(task['start']), '--end', str(end_inclusive),
                   '--fps', str(task['fps']), '--label', label,
                   '--pdf-name', f'{label}.pdf', '--idtracker-python', PYTHON,
                   '--ffmpeg', FFMPEG, '--ffprobe', FFPROBE]
        write_status(folder, 'RUNNING', command=command, source_toml=task['source_toml'],
                     selected_run=task['run_dir'], trajectory_sha256=task['trajectory_sha256'],
                     analyzed_interval_inclusive=[task['start'], end_inclusive])
        with (folder/'pipeline.log').open('x') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False)
        if result.returncode:
            raise RuntimeError(f'Pipeline exited {result.returncode}; see pipeline.log')
        needed = [folder/'analysis'/f'{label}.pdf', folder/'analysis'/'frame_data.csv',
                  folder/'review'/'interaction_review.html', folder/'review'/'review_video.mp4']
        if any(not path.is_file() or not path.stat().st_size for path in needed):
            raise RuntimeError('Pipeline returned without every requested PDF/CSV/HTML/video')
        manifest = json.loads((folder/'analysis'/'manifest.json').read_text())
        if (manifest.get('persistent_model_version') != EXPECTED_PSC_MODEL or
                manifest.get('script_version') != EXPECTED_GROUP_PROCESSOR):
            raise RuntimeError('Pipeline used an outdated PSC model or group processor')
        for name in ('window_comparison.csv','region_comparison.csv','fungus_comparison.csv'):
            if not (folder/'analysis'/name).is_file():
                raise RuntimeError(f'Missing paired raw/PSC summary: {name}')
        write_status(folder, 'COMPLETE_UNREVIEWED', source_toml=task['source_toml'],
                     selected_run=task['run_dir'], analyzed_interval_inclusive=[task['start'],end_inclusive],
                     pdf=str(needed[0]), frame_data_csv=str(needed[1]),
                     html=str(needed[2]), video=str(needed[3]))
    except BaseException as exc:
        write_status(folder, 'FAILED', error=repr(exc))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('plan','run'))
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    (make_plan if args.mode == 'plan' else process)(args.root)


if __name__ == '__main__':
    main()
