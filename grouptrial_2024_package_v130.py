#!/usr/bin/env python3
"""Package only model-1.3.0 GroupTrial reviews with versioned provenance."""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

FFPROBE = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def count_frames(path: Path) -> int:
    raw = subprocess.check_output([FFPROBE, '-v', 'error', '-select_streams', 'v:0',
                                   '-show_entries', 'stream=nb_frames', '-of', 'json', str(path)])
    return int(json.loads(raw)['streams'][0]['nb_frames'])


def main(root: Path) -> None:
    plan = json.loads((root/'plan.json').read_text())
    destination = root/'portable_v130'
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir()
    rows = []
    for task in plan['tasks']:
        label = Path(task['source_toml']).stem
        source = root/'tasks'/label
        state = json.loads((source/'status.json').read_text())
        if state['stage'] != 'COMPLETE_UNREVIEWED':
            raise RuntimeError(f'Incomplete: {label}: {state["stage"]}')
        analysis_manifest = json.loads((source/'analysis/manifest.json').read_text())
        if analysis_manifest.get('persistent_model_version') != '1.3.0':
            raise RuntimeError(f'Wrong PSC model version: {label}')
        if analysis_manifest.get('qc_status') != 'UNREVIEWED':
            raise RuntimeError(f'Unexpected review status: {label}')
        target = destination/label
        target.mkdir()
        (target/'analysis').mkdir()
        (target/'review').mkdir()
        shutil.copy2(task['source_toml'], target/'source.toml')
        shutil.copy2(task['submitted_toml'], target/'submitted.toml')
        for path in (source/'analysis').iterdir():
            if path.is_file():
                shutil.copy2(path, target/'analysis'/path.name)
        if not (target/'analysis'/'OUTPUT_MANIFEST.md').is_file():
            raise RuntimeError(f'Missing student-facing manifest: {label}')
        shutil.copy2(target/'analysis'/'OUTPUT_MANIFEST.md', target/'OUTPUT_MANIFEST.md')
        for name in ('analysis.pipeline_receipt.json','analysis.blob_evidence.json','status.json'):
            optional = source/name
            if optional.is_file():
                shutil.copy2(optional, target/name)
        review = source/'review'
        shutil.copy2(review/'interaction_review.html', target/'review'/'interaction_review.html')
        copied_video = target/'review'/'review_video.mp4'
        shutil.copy2(review/'review_video.mp4', copied_video)
        original_frames = count_frames(review/'review_video.mp4')
        copied_frames = count_frames(copied_video)
        if original_frames != copied_frames or original_frames != task['frame_count']:
            raise ValueError(f'Frame mismatch for {label}: {original_frames}, {copied_frames}, {task["frame_count"]}')
        manifest = json.loads((review/'source_manifest.json').read_text())
        if manifest['copied_video_sha256'] != digest(copied_video):
            raise ValueError(f'Video hash mismatch: {label}')
        manifest['video_source'] = 'review_video.mp4'
        (target/'review'/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        rows.append(dict(source_toml=task['source_toml'], selected_run=task['run_dir'],
                         psc_model_version='1.3.0', review_status='UNREVIEWED',
                         choice_reason=task['choice_reason'], source_sha256=task['source_sha256'],
                         submitted_toml_sha256=task['submitted_toml_sha256'],
                         trajectory_sha256=task['trajectory_sha256'],
                         start_frame=task['start'], end_frame_inclusive=task['end_exclusive']-1,
                         raw_missing_percent=task['raw_missing_percent'],
                         run_folder_label_mismatch=task['run_folder_label_mismatch'],
                         session_label_mismatch=task['session_label_mismatch'],
                         original_video_bytes=(review/'review_video.mp4').stat().st_size,
                         portable_video_bytes=copied_video.stat().st_size))
        print('Packaged',label,copied_video.stat().st_size,flush=True)
    fields = list(rows[0])
    with (destination/'selection_manifest.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fields)
        writer.writeheader()
        writer.writerows(rows)
    (destination/'README.txt').write_text(
        '2024 GroupTrial six-beetle PSC model 1.3.0 reviews.\n'
        'These outputs supersede the withdrawn model-1.2.0 batch. Do not mix versions.\n'
        '13 original GUI submissions represented 11 distinct source TOMLs; original IDtracker tracking sessions remain on Firebird.\n'
        'Selections and PSC identity assignments remain UNREVIEWED for biological interpretation.\n'
        'Each folder contains original/submitted TOMLs, every analysis file (CSV/PDF/NPZ/JSON), a student-facing OUTPUT_MANIFEST.md, provenance sidecars, and portable HTML plus synchronized MP4.\n'
        'MP4 files are full-resolution copies with every frame and the original SHA-256 preserved.\n'
        'Start frame is preserved; end_frame_inclusive is TOML end minus one.\n'
        'Source and processed trajectory hashes and name mismatches are in selection_manifest.csv.\n'
        'See VERSION_CONTROL.json and SIX_BEETLE_METHODS.html for model provenance and rules.\n')
    for name in ('SIX_BEETLE_METHODS.html', 'INVALIDATED_SIX_BEETLE_OUTPUTS_20260924.md',
                 'VERSION_CONTROL.json'):
        source = root/name
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, destination/name)
    hashes = []
    for path in sorted(destination.rglob('*')):
        if path.is_file():
            hashes.append(f'{digest(path)}  {path.relative_to(destination)}')
    (destination/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n')
    archive = root/'GroupTrial_2024_PSC_v1.3.0_11_reviews.zip'
    if archive.exists():
        raise FileExistsError(archive)
    with zipfile.ZipFile(archive,'w',allowZip64=True) as stream:
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                method = zipfile.ZIP_STORED if path.suffix in ('.mp4','.pdf') else zipfile.ZIP_DEFLATED
                stream.write(path,path.relative_to(destination),compress_type=method)
    with zipfile.ZipFile(archive) as stream:
        bad = stream.testzip()
        if bad:
            raise ValueError(f'Archive corruption: {bad}')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,sha256=digest(archive),
                          review_count=len(rows)),indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
