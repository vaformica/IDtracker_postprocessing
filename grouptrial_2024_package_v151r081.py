#!/usr/bin/env python3
"""Package only PSC 1.5.1 / processor 0.8.1-group reviews."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from psc_release_validation import validate_bundle
from rebuild_raw_psc_compare_reviews import VIEW_VERSION

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
    for task in plan['tasks']:
        label = Path(task['source_toml']).stem
        source = root/'tasks'/label
        state = json.loads((source/'status.json').read_text())
        manifest = json.loads((source/'analysis/manifest.json').read_text())
        if (state.get('stage') != 'COMPLETE_UNREVIEWED' or
                manifest.get('persistent_model_version') != '1.5.1' or
                manifest.get('script_version') != '0.8.1-group' or
                manifest.get('qc_status') != 'UNREVIEWED'):
            raise RuntimeError(f'Incomplete or wrong-version review: {label}')
        validate_bundle(source/'analysis', '1.5.1', '0.8.1-group')
        for name in ('window_comparison.csv','region_comparison.csv','fungus_comparison.csv',
                     'frame_data.csv','OUTPUT_MANIFEST.md'):
            if not (source/'analysis'/name).is_file():
                raise FileNotFoundError(source/'analysis'/name)
    destination = root/'portable_v151r081'
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
        if analysis_manifest.get('persistent_model_version') != '1.5.1':
            raise RuntimeError(f'Wrong PSC model version: {label}')
        if analysis_manifest.get('script_version') != '0.8.1-group':
            raise RuntimeError(f'Wrong group processor version: {label}')
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
        if any(not (target/'analysis'/name).is_file() for name in
               ('window_comparison.csv','region_comparison.csv','fungus_comparison.csv')):
            raise RuntimeError(f'Missing paired raw/PSC summaries: {label}')
        if not (target/'analysis'/'OUTPUT_MANIFEST.md').is_file():
            raise RuntimeError(f'Missing student-facing manifest: {label}')
        shutil.copy2(target/'analysis'/'OUTPUT_MANIFEST.md', target/'OUTPUT_MANIFEST.md')
        for name in ('analysis.pipeline_receipt.json','analysis.blob_evidence.json','status.json'):
            optional = source/name
            if optional.is_file():
                shutil.copy2(optional, target/name)
        review = source/'review_compare'
        review_meta = json.loads((review/'source_manifest.json').read_text())
        if (review_meta.get('review_view_version') != VIEW_VERSION or
                review_meta.get('analysis_manifest_sha256') != digest(source/'analysis'/'manifest.json') or
                not review_meta.get('video_geometry', {}).get('aspect_preserved') or
                review_meta.get('status') != 'UNREVIEWED'):
            raise RuntimeError(f'Comparison viewer is missing or bound to a different analysis: {label}')
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
        (target/'review'/'source_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
        rows.append(dict(source_toml=task['source_toml'], selected_run=task['run_dir'],
                         psc_model_version='1.5.1', group_processor_version='0.8.1-group',
                         review_view_version=VIEW_VERSION,
                         review_status='UNREVIEWED',
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
        '2024 GroupTrial six-beetle PSC model 1.5.1 / processor 0.8.1-group reviews.\n'
        'These outputs supersede the withdrawn model-1.2.0, model-1.3.0, model-1.4.0, and preliminary model-1.5.0 batches. Do not mix versions.\n'
        '13 original GUI submissions represented 11 distinct source TOMLs; original IDtracker tracking sessions remain on Firebird.\n'
        'Selections and PSC identity assignments remain UNREVIEWED for biological interpretation.\n'
        'The HTML switch compares source IDtracker coordinates and PSC-model positions at the same frame; display changes do not alter CSV or PDF statistics. Review videos preserve arena proportions and put fungus 1 on the left when ROI geometry supports a clear orientation.\n'
        'Each folder contains original/submitted TOMLs, every analysis file (CSV/PDF/NPZ/JSON), a student-facing OUTPUT_MANIFEST.md, provenance sidecars, and portable HTML plus synchronized MP4.\n'
        'MP4 files are full-resolution copies with every frame and the original SHA-256 preserved.\n'
        'Start frame is preserved; end_frame_inclusive is TOML end minus one.\n'
        'Source and processed trajectory hashes and name mismatches are in selection_manifest.csv.\n'
        'See VERSION_CONTROL.json and SIX_BEETLE_METHODS.html for model provenance and rules.\n')
    code = root/'code'
    snapshot = json.loads((code/'RELEASE_VERSION.json').read_text())
    if snapshot.get('psc_model_version') != '1.5.1':
        raise RuntimeError('Code snapshot is not PSC 1.5.1')
    code_files = ('persistent_groups.py','six_beetle_processor.py','frame_data.py',
                  'psc_release_validation.py',
                  'output_manifest.py','run_six_beetle_pipeline.py')
    version = dict(schema='grouptrial-psc-release-v1',
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   psc_model_version='1.5.1',group_processor_version='0.8.1-group',
                   review_view_version=VIEW_VERSION,
                   code_commit=snapshot['git_commit'],
                   qc_status='UNREVIEWED',plan_sha256=digest(root/'plan.json'),
                   source_tomls_untouched=True,
                   code_sha256={name:digest(code/name) for name in code_files},
                   viewer_code_sha256={name:digest(Path(__file__).with_name(name)) for name in
                       ('review_geometry.py','build_canonical_review.py',
                        'interaction_review_template.html','rebuild_raw_psc_compare_reviews.py')})
    (destination/'VERSION_CONTROL.json').write_text(json.dumps(version,indent=2)+'\n')
    for name in ('SIX_BEETLE_METHODS.html', 'DATA_DICTIONARY.md',
                 'INVALIDATED_SIX_BEETLE_OUTPUTS_20260924.md',
                 ):
        source = root/name
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, destination/name)
    hashes = []
    for path in sorted(destination.rglob('*')):
        if path.is_file():
            hashes.append(f'{digest(path)}  {path.relative_to(destination)}')
    (destination/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n')
    archive = root/'GroupTrial_2024_PSC_v1.5.1_processor0.8.1_11_reviews.zip'
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
