#!/usr/bin/env python3
"""Finish verified GroupTrial outputs after the output-dictionary field mismatch.

The numerical PSC analysis and source video review are reused unchanged. This
script writes the corrected student guide, comparison viewer, outlined PDF,
and explicit recovery provenance into new/previously absent files.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

from grouptrial_2024_selected_postprocess import candidate
from output_manifest import render, write_output_manifest
from psc_release_validation import validate_bundle

ROOT = Path('/data/labs/vformic1-swat-lab/idtracker_pipeline_runs/grouptrial_2024_additional_psc_v1_5_1_processor_0_8_1_20260925_1337utc')
CODE = Path(__file__).resolve().parent
PYTHON = '/home/vformic1-swat/miniconda3/envs/idtrackerai_6_0_14/bin/python'
FFPROBE = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def atomic(path: Path, data: dict) -> None:
    temporary = path.with_name(path.name+'.partial')
    temporary.write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    temporary.replace(path)


def frame_count(video: Path) -> int:
    raw = subprocess.check_output([FFPROBE,'-v','error','-select_streams','v:0',
                                   '-show_entries','stream=nb_frames','-of','json',str(video)])
    return int(json.loads(raw)['streams'][0]['nb_frames'])


def recover() -> None:
    task = json.loads((ROOT/'plan.json').read_text())['tasks'][int(os.environ['SLURM_ARRAY_TASK_ID'])]
    folder = ROOT/'tasks'/Path(task['source_toml']).stem
    analysis, review = folder/'analysis', folder/'review'
    analysis_status = folder/'analysis_status.json'
    old_status = json.loads(analysis_status.read_text())
    if old_status['stage'] == 'COMPLETE_UNREVIEWED':
        print('Already recovered', folder, flush=True)
        return
    if old_status['stage'] != 'FAILED':
        raise ValueError(f'Unexpected analysis state: {old_status["stage"]}')
    if sha(Path(task['source_toml'])) != task['source_sha256'] or sha(Path(task['submitted_toml'])) != task['submitted_toml_sha256']:
        raise ValueError('Source or submitted TOML hash changed')
    selected = candidate(folder)
    if selected is None:
        raise ValueError('No valid IDtracker trajectory')
    meta = json.loads((analysis/'manifest.json').read_text())
    source = json.loads((review/'source_manifest.json').read_text())
    if (meta.get('persistent_model_version') != '1.5.1' or
            meta.get('script_version') != '0.8.1-group' or
            meta.get('qc_status') != 'UNREVIEWED'):
        raise ValueError('Wrong analysis version or QC state')
    if (source.get('analysis_manifest_sha256') != sha(analysis/'manifest.json') or
            source.get('copied_video_sha256') != sha(review/'review_video.mp4') or
            source.get('analysis_frame_count') != task['end_exclusive']-task['start'] or
            frame_count(review/'review_video.mp4') != task['end_exclusive']-task['start']):
        raise ValueError('Source review does not match numerical analysis')
    validate_bundle(analysis, '1.5.1', '0.8.1-group')
    guide = analysis/'OUTPUT_MANIFEST.md'
    if not (folder/'analysis_status_initial_failure.json').exists():
        shutil.copy2(analysis_status, folder/'analysis_status_initial_failure.json')
    if not (folder/'tracking_status.json').exists():
        shutil.copy2(folder/'status.json', folder/'tracking_status.json')
    if guide.exists():
        if guide.read_text() != render(analysis, review, source_toml=Path(task['source_toml'])):
            raise ValueError('Existing output guide differs from the corrected renderer')
    else:
        write_output_manifest(analysis, review, source_toml=Path(task['source_toml']))
    if not guide.is_file() or not guide.stat().st_size:
        raise RuntimeError('Documentation repair did not write a guide')
    receipt = dict(schema='grouptrial-documented-recovery-v1',
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   cause='output_manifest.py lacked PDF style and viewer-v3 JSON field definitions',
                   original_pipeline_log=str(folder/'pipeline.log'),
                   original_failure_sha256=sha(folder/'analysis_status_initial_failure.json'),
                   numerical_analysis_untouched=True,
                   source_review_untouched=True,
                   analysis_manifest_sha256=sha(analysis/'manifest.json'),
                   source_review_manifest_sha256=sha(review/'source_manifest.json'),
                   output_guide_sha256=sha(guide),
                   output_manifest_code_sha256=sha(CODE/'output_manifest.py'),
                   trajectory_sha256=selected['trajectory_sha256'],
                   psc_model_version='1.5.1',processor_version='0.8.1-group',
                   review_status='UNREVIEWED')
    atomic(folder/'analysis.pipeline_receipt.json', receipt)
    # The v3 builder gates on this status; keep the original tracker state above.
    atomic(folder/'status.json', dict(stage='COMPLETE_UNREVIEWED',
                                     recovered_documentation=True,
                                     tracking_status_file=str(folder/'tracking_status.json')))
    subprocess.run([PYTHON,str(CODE/'rebuild_raw_psc_compare_reviews.py'),
                    'grouptrial',str(ROOT),'--task-id',folder.name],check=True)
    outlined = folder/'pdf_outline_v1'
    if outlined.exists():
        prior = json.loads((outlined/'render_manifest.json').read_text())
        if (prior.get('source_manifest_sha256') != sha(analysis/'manifest.json') or
                prior.get('pdf_sha256') != sha(outlined/prior['pdf_filename'])):
            raise ValueError('Existing outlined PDF differs from this analysis')
    else:
        subprocess.run([PYTHON,str(CODE/'render_psc_outlined_pdf.py'),
                        str(analysis),str(outlined)],check=True)
    atomic(folder/'documentation_recovery.json', {**receipt,
           'comparison_review_manifest_sha256':sha(folder/'review_compare_v3/source_manifest.json'),
           'outlined_pdf_manifest_sha256':sha(folder/'pdf_outline_v1/render_manifest.json')})
    atomic(analysis_status,dict(stage='COMPLETE_UNREVIEWED',
                                candidate=selected,
                                psc_model_version='1.5.1',
                                processor_version='0.8.1-group',
                                viewer_version='raw-psc-compare-v3',
                                pdf_track_style='outlined-psc-v1',
                                recovered_documentation=True))
    print('Recovered', folder, flush=True)


if __name__ == '__main__':
    recover()
