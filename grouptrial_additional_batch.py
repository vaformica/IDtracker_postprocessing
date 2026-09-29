#!/usr/bin/env python3
"""Stage and run additional GroupTrial TOMLs without changing their sources.

The ``stage`` command creates an immutable plan and one tracking directory per
TOML. Submit the printed Slurm scripts in order. ``process`` runs only when a
valid six-animal IDtracker trajectory exists and produces PSC 1.5.1 outputs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from grouptrial_2024_selected_postprocess import candidate
from psc_release_validation import validate_bundle

SOURCE = Path('/data/labs/vformic1-swat-lab/2024_Videos/Groupagetrial_2024')
PREVIOUS = Path('/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_pscp_v1_5_1_processor_0_8_1_release_20260924_2130utc/plan.json')
PYTHON = '/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python'
FFMPEG = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffmpeg'
FFPROBE = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'
CODE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def audit() -> tuple[list[dict], list[dict]]:
    previous = {Path(x['source_toml']).name for x in json.loads(PREVIOUS.read_text())['tasks']}
    eligible, excluded = [], []
    for path in sorted(SOURCE.glob('*.toml')):
        if path.name in previous:
            continue
        raw = path.read_bytes()
        record = dict(source_toml=str(path), source_sha256=hashlib.sha256(raw).hexdigest())
        try:
            data = tomllib.loads(raw.decode('utf-8'))
            videos = data.get('video_paths')
            intervals = data.get('tracking_intervals')
            if data.get('number_of_animals') != 6 or len(data.get('roi_list', [])) != 4:
                raise ValueError('requires six animals and arena plus three fungus ROIs')
            if not data.get('use_bkg'):
                raise ValueError('background subtraction is off')
            if not isinstance(videos, list) or len(videos) != 1 or not Path(videos[0]).is_file():
                raise ValueError('exactly one existing source video is required')
            if not isinstance(intervals, list) or len(intervals) != 1 or len(intervals[0]) != 2:
                raise ValueError('tracking interval absent or malformed; start frame cannot be inferred')
            start, end = intervals[0]
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end:
                raise ValueError('invalid tracking start/end')
            if data.get('check_segmentation') is True:
                raise ValueError('interactive check_segmentation would stop unattended batch')
            if not isinstance(data.get('area_ths'), list) or len(data['area_ths']) != 2 or not all(type(x) is float for x in data['area_ths']):
                raise ValueError('area_ths must be two TOML floats for installed IDtracker')
            probe = json.loads(subprocess.check_output([FFPROBE, '-v', 'error', '-select_streams', 'v:0',
                                                         '-show_entries', 'stream=nb_frames,r_frame_rate',
                                                         '-of', 'json', videos[0]]))['streams'][0]
            if end > int(probe['nb_frames']):
                raise ValueError('tracking interval exceeds video length')
            record.update(start=start, end_exclusive=end, video=videos[0],
                          video_frames=int(probe['nb_frames']), fps=probe['r_frame_rate'],
                          original_name=data.get('name'), area_ths=data['area_ths'],
                          intensity_ths=data.get('intensity_ths'))
            eligible.append(record)
        except Exception as exc:
            excluded.append({**record, 'reason': str(exc)})
    return eligible, excluded


def stage(root: Path) -> None:
    if (root/'plan.json').exists() or (root/'tasks').exists():
        raise FileExistsError(root)
    eligible, excluded = audit()
    if not eligible:
        raise ValueError('No eligible additional TOMLs')
    root.mkdir(parents=True, exist_ok=True)
    (root/'tasks').mkdir()
    (root/'logs').mkdir()
    for index, task in enumerate(eligible):
        source = Path(task['source_toml'])
        folder = root/'tasks'/source.stem
        (folder/'input').mkdir(parents=True)
        submitted = folder/'input'/'submitted.toml'
        shutil.copyfile(source, submitted)
        if sha(submitted) != task['source_sha256']:
            raise RuntimeError(f'Copied TOML hash mismatch: {source}')
        task.update(index=index, run_dir=str(folder), submitted_toml=str(submitted),
                    submitted_toml_sha256=sha(submitted),
                    idtracker_output=str(folder/'idtracker_output'))
        atomic_json(folder/'submission_request.json', dict(
            schema_version=2, source_toml=task['source_toml'],
            source_sha256=task['source_sha256'], submitted_toml=str(submitted),
            submitted_toml_sha256=task['submitted_toml_sha256'],
            modified=False, edit_origin='source_unchanged', run_dir=str(folder),
            version_target={'psc_model':'1.5.1','processor':'0.8.1-group'},
            created_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    plan = dict(schema='grouptrial-additional-v1',
                created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                parent_release=str(PREVIOUS.parent),
                code_snapshot=str(CODE),
                review_status='UNREVIEWED',
                tasks=eligible, excluded=excluded)
    atomic_json(root/'plan.json', plan)
    count = len(eligible)
    (root/'track.slurm').write_text(f'''#!/bin/bash
#SBATCH --job-name=group_add_track
#SBATCH --partition=gpu
#SBATCH --gres=gpu:l40s:1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --array=0-{count-1}%4
#SBATCH --output={root}/logs/track-%A_%a.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
exec {PYTHON} {CODE/'grouptrial_additional_batch.py'} track {root}
''')
    (root/'process.slurm').write_text(f'''#!/bin/bash
#SBATCH --job-name=group_add_psc151
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --array=0-{count-1}%4
#SBATCH --output={root}/logs/process-%A_%a.log
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
exec {PYTHON} {CODE/'grouptrial_additional_batch.py'} process {root}
''')
    print(json.dumps({'root':str(root),'eligible':count,'excluded':excluded},indent=2))


def task_for_array(root: Path) -> tuple[dict, Path]:
    task = json.loads((root/'plan.json').read_text())['tasks'][int(os.environ['SLURM_ARRAY_TASK_ID'])]
    return task, root/'tasks'/Path(task['source_toml']).stem


def track(root: Path) -> None:
    task, folder = task_for_array(root)
    if sha(Path(task['source_toml'])) != task['source_sha256'] or sha(Path(task['submitted_toml'])) != task['submitted_toml_sha256']:
        raise ValueError('Source or submitted TOML hash drift')
    command = [PYTHON, str(CODE/'firebird_idtracker_runner.py'), '--toml', task['submitted_toml'],
               '--output', task['idtracker_output'], '--workers', '16', '--device', 'cuda', '--data-policy', 'all']
    os.chdir(folder)
    subprocess.run(command, check=True)


def process(root: Path) -> None:
    task, folder = task_for_array(root)
    status = folder/'analysis_status.json'
    if status.is_file() and json.loads(status.read_text()).get('stage') == 'COMPLETE_UNREVIEWED':
        print('Already complete:', folder, flush=True)
        return
    try:
        selected = candidate(folder)
        if selected is None:
            raise ValueError('No valid IDtracker trajectory; inspect tracking status and log')
        command = [PYTHON, str(CODE/'run_group_pipeline.py'), '--session', selected['session'],
                   '--source-toml', task['source_toml'], '--source-video', task['video'],
                   '--analysis-output', str(folder/'analysis'), '--review-output', str(folder/'review'),
                   '--start', str(task['start']), '--end', str(task['end_exclusive']-1),
                   '--fps', str(selected['fps']), '--label', Path(task['source_toml']).stem,
                   '--pdf-name', Path(task['source_toml']).stem+'.pdf', '--idtracker-python', PYTHON,
                   '--ffmpeg', FFMPEG, '--ffprobe', FFPROBE]
        atomic_json(status, dict(stage='RUNNING', command=command, candidate=selected))
        with (folder/'pipeline.log').open('x') as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        manifest = json.loads((folder/'analysis'/'manifest.json').read_text())
        if manifest.get('persistent_model_version') != '1.5.1' or manifest.get('script_version') != '0.8.1-group':
            raise ValueError('Wrong PSC or processor version')
        validate_bundle(folder/'analysis', '1.5.1', '0.8.1-group')
        # The established viewer builder reads the batch plan and normal status.
        atomic_json(folder/'status.json', dict(stage='COMPLETE_UNREVIEWED', selected_run=str(folder)))
        subprocess.run([PYTHON, str(CODE/'rebuild_raw_psc_compare_reviews.py'), 'grouptrial', str(root),
                        '--task-id', Path(task['source_toml']).stem], check=True)
        subprocess.run([PYTHON, str(CODE/'render_psc_outlined_pdf.py'), str(folder/'analysis'),
                        str(folder/'pdf_outline_v1')], check=True)
        atomic_json(status, dict(stage='COMPLETE_UNREVIEWED', candidate=selected,
                                 psc_model_version='1.5.1', processor_version='0.8.1-group',
                                 viewer_version='raw-psc-compare-v3', pdf_track_style='outlined-psc-v1'))
    except BaseException as exc:
        atomic_json(status, dict(stage='FAILED', error=repr(exc)))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('audit','stage','track','process'))
    parser.add_argument('root', type=Path, nargs='?')
    args = parser.parse_args()
    if args.mode == 'audit':
        eligible, excluded = audit()
        print(json.dumps({'eligible':eligible,'excluded':excluded},indent=2))
    else:
        if args.root is None:
            parser.error('root required')
        {'stage':stage,'track':track,'process':process}[args.mode](args.root)


if __name__ == '__main__':
    main()
