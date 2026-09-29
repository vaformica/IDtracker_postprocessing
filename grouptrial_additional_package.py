#!/usr/bin/env python3
"""Verify and package additional GroupTrial PSC 1.5.1 reviews on Firebird."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from psc_release_validation import validate_bundle

FFPROBE = '/home/vformic1-swat/miniconda3/envs/ffmpeg_env/bin/ffprobe'
MODEL = '1.5.1'
PROCESSOR = '0.8.1-group'
VIEWER = 'raw-psc-compare-v3'
PDF_STYLE = 'outlined-psc-v1'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def frames(path: Path) -> int:
    output = subprocess.check_output([FFPROBE, '-v', 'error', '-select_streams', 'v:0',
                                      '-show_entries', 'stream=nb_frames', '-of', 'json', str(path)])
    return int(json.loads(output)['streams'][0]['nb_frames'])


def validated(root: Path, task: dict) -> dict:
    label = Path(task['source_toml']).stem
    folder = root/'tasks'/label
    if sha(Path(task['source_toml'])) != task['source_sha256']:
        raise ValueError(f'Source TOML changed: {label}')
    if sha(Path(task['submitted_toml'])) != task['submitted_toml_sha256']:
        raise ValueError(f'Submitted TOML changed: {label}')
    status = json.loads((folder/'analysis_status.json').read_text())
    if status.get('stage') != 'COMPLETE_UNREVIEWED':
        raise ValueError(f'Incomplete postprocessing: {label}: {status.get("stage")}')
    analysis = folder/'analysis'
    meta = json.loads((analysis/'manifest.json').read_text())
    if (meta.get('persistent_model_version') != MODEL or
            meta.get('script_version') != PROCESSOR or
            meta.get('qc_status') != 'UNREVIEWED'):
        raise ValueError(f'Wrong PSC/processor/QC version: {label}')
    validate_bundle(analysis, MODEL, PROCESSOR)
    recovery = json.loads((folder/'documentation_recovery.json').read_text())
    if (recovery.get('numerical_analysis_untouched') is not True or
            recovery.get('analysis_manifest_sha256') != sha(analysis/'manifest.json') or
            recovery.get('output_guide_sha256') != sha(analysis/'OUTPUT_MANIFEST.md')):
        raise ValueError(f'Documentation recovery provenance mismatch: {label}')
    for name in ('frame_data.csv','window_comparison.csv','region_comparison.csv',
                 'fungus_comparison.csv','OUTPUT_MANIFEST.md'):
        if not (analysis/name).is_file():
            raise FileNotFoundError(analysis/name)
    start = int(meta['settings']['start'])
    expected = int(meta['settings']['window'])+1
    if start != task['start'] or expected != task['end_exclusive']-task['start']:
        raise ValueError(f'TOML frame window mismatch: {label}')
    review = folder/'review_compare_v3'
    review_meta = json.loads((review/'source_manifest.json').read_text())
    video = review/'review_video.mp4'
    if (review_meta.get('review_view_version') != VIEWER or
            review_meta.get('status') != 'UNREVIEWED' or
            review_meta.get('analysis_manifest_sha256') != sha(analysis/'manifest.json') or
            review_meta.get('analysis_frame_count') != expected or
            review_meta.get('copied_video_sha256') != sha(video) or
            not review_meta.get('video_geometry',{}).get('aspect_preserved') or
            frames(video) != expected):
        raise ValueError(f'Viewer provenance or frame mismatch: {label}')
    pdf_dir = folder/'pdf_outline_v1'
    pdf_meta = json.loads((pdf_dir/'render_manifest.json').read_text())
    outlined_pdf = pdf_dir/pdf_meta['pdf_filename']
    if (pdf_meta.get('psc_model_version') != MODEL or
            pdf_meta.get('processor_version') != PROCESSOR or
            pdf_meta.get('pdf_track_style_version') != PDF_STYLE or
            pdf_meta.get('raw_and_psc_states_matched') is not True or
            pdf_meta.get('source_manifest_sha256') != sha(analysis/'manifest.json') or
            pdf_meta.get('pdf_sha256') != sha(outlined_pdf)):
        raise ValueError(f'Outlined PDF provenance mismatch: {label}')
    return dict(label=label, folder=folder, analysis=analysis, review=review,
                pdf_dir=pdf_dir, outlined_pdf=outlined_pdf, video=video,
                start_frame=start, end_frame_inclusive=start+expected-1,
                frame_count=expected, source_toml=task['source_toml'],
                source_sha256=task['source_sha256'],
                submitted_toml_sha256=task['submitted_toml_sha256'],
                trajectory_sha256=status['candidate']['trajectory_sha256'],
                review_video_sha256=review_meta['copied_video_sha256'],
                outlined_pdf_sha256=pdf_meta['pdf_sha256'])


def package(root: Path) -> Path:
    plan = json.loads((root/'plan.json').read_text())
    records = [validated(root, task) for task in plan['tasks']]
    if not records:
        raise ValueError('No completed reviews')
    target = root/'portable_additional_v151r081_view_v3_outline_v1'
    archive = root/f'GroupTrial_additional_PSC_v1.5.1_processor0.8.1_{len(records)}_reviews.zip'
    if target.exists() or archive.exists():
        raise FileExistsError('Portable collection or archive already exists')
    target.mkdir()
    rows = []
    for row in records:
        out = target/row['label']
        (out/'analysis').mkdir(parents=True)
        (out/'review').mkdir()
        (out/'outlined_pdf').mkdir()
        shutil.copy2(row['source_toml'], out/'source.toml')
        shutil.copy2(row['folder']/'input/submitted.toml', out/'submitted.toml')
        for source in row['analysis'].iterdir():
            if source.is_file():
                shutil.copy2(source, out/'analysis'/source.name)
        for name in ('interaction_review.html','source_manifest.json','review_video.mp4'):
            shutil.copy2(row['review']/name, out/'review'/name)
        for name in ('render_manifest.json',row['outlined_pdf'].name):
            shutil.copy2(row['pdf_dir']/name, out/'outlined_pdf'/name)
        for name in ('submission_request.json','submission_receipt.json',
                     'analysis_status.json','status.json','tracking_status.json',
                     'analysis_status_initial_failure.json',
                     'analysis.pipeline_receipt.json','documentation_recovery.json'):
            if (row['folder']/name).is_file():
                shutil.copy2(row['folder']/name, out/name)
        if sha(out/'review/review_video.mp4') != row['review_video_sha256']:
            raise ValueError(f'Copied video hash mismatch: {row["label"]}')
        if sha(out/'outlined_pdf'/row['outlined_pdf'].name) != row['outlined_pdf_sha256']:
            raise ValueError(f'Copied PDF hash mismatch: {row["label"]}')
        rows.append({key:value for key,value in row.items() if key not in
                     ('folder','analysis','review','pdf_dir','outlined_pdf','video')})
    with (target/'run_manifest.csv').open('w',newline='') as stream:
        writer = csv.DictWriter(stream,list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for name in ('plan.json','batch_submission.json','tracking_retry.json',
                 'tracking_retry_h200_array.json','processing_resubmission_v2.json'):
        if (root/name).is_file():
            shutil.copy2(root/name,target/name)
    for name in ('SIX_BEETLE_METHODS.html','DATA_DICTIONARY.md'):
        shutil.copy2(root/'code_v151r081'/name,target/name)
    (target/'DOCUMENTATION_RECOVERY.txt').write_text(
        'The original postprocessing command completed numerical PSC analyses and source reviews, '
        'then stopped while writing the student-facing output dictionary because its field list '
        'did not include the new PDF style and viewer-v3 manifest fields. A separate, versioned '
        'documentation recovery verified each analysis and source review without altering their '
        'numeric files, wrote the corrected dictionary, and generated the comparison viewer '
        'and outlined PDF. Each run carries the original failure and recovery receipts.\n')
    version = dict(schema='grouptrial-additional-release-v1',
                   created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                   psc_model_version=MODEL, group_processor_version=PROCESSOR,
                   review_view_version=VIEWER, pdf_track_style_version=PDF_STYLE,
                   qc_status='UNREVIEWED', review_count=len(records),
                   plan_sha256=sha(root/'plan.json'),
                   source_tomls_untouched=True,
                   numerical_analysis_untouched_during_documentation_recovery=True,
                   output_manifest_code_sha256=sha(root/'code_docfix_v151r081/output_manifest.py'),
                   recovery_code_sha256=sha(root/'code_docfix_v151r081/grouptrial_additional_recover_docs.py'),
                   excluded_tomls=plan['excluded'],
                   code_sha256={name:sha(root/'code_v151r081'/name) for name in
                                ('persistent_groups.py','six_beetle_processor.py',
                                 'rebuild_raw_psc_compare_reviews.py',
                                 'render_psc_outlined_pdf.py')})
    (target/'VERSION_CONTROL.json').write_text(json.dumps(version,indent=2)+'\n')
    (target/'README.txt').write_text(
        'Additional 2024 GroupTrial recordings processed with PSC 1.5.1 and group processor 0.8.1-group.\n'
        'Source TOMLs are unchanged. See plan.json for seven excluded unrun drafts and their reasons.\n'
        'IDtracker trajectories and full source videos remain on Firebird. Each folder contains\n'
        'raw/PSC frame data and summaries, an HTML review with synchronized video, and an outlined-PSC PDF.\n'
        'PSC identities and biological interpretations are UNREVIEWED. Do not mix older PSC releases.\n')
    checksums = [f'{sha(path)}  {path.relative_to(target)}' for path in sorted(target.rglob('*')) if path.is_file()]
    (target/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n')
    with zipfile.ZipFile(archive,'w',allowZip64=True) as stream:
        for path in sorted(target.rglob('*')):
            if path.is_file():
                compression = zipfile.ZIP_STORED if path.suffix in ('.mp4','.pdf') else zipfile.ZIP_DEFLATED
                stream.write(path,path.relative_to(target),compress_type=compression)
    with zipfile.ZipFile(archive) as stream:
        bad = stream.testzip()
        if bad:
            raise ValueError(f'Corrupt ZIP member: {bad}')
    print(json.dumps({'archive':str(archive),'sha256':sha(archive),
                      'bytes':archive.stat().st_size,'reviews':len(records)},indent=2))
    return archive


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args = parser.parse_args()
    package(args.root)
