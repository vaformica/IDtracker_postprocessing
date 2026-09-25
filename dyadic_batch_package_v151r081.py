#!/usr/bin/env python3
"""Build a portable ZIP of PSC-1.5.1 / processor-0.8.1 dyadic reviews.

Run only after final analysis has completed. The source video and original
IDtracker trajectories remain on Firebird; review MP4s are smaller derivatives
with frame count and frame rate preserved for the synchronized HTML viewer.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from dyadic_batch_collect_v151r081 import collect
from dyadic_batch_worker import FFMPEG, FFPROBE
from rebuild_raw_psc_compare_reviews import VIEW_VERSION

CODE = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def video_frames(path: Path) -> tuple[str, str]:
    result = subprocess.check_output([FFPROBE, '-v', 'error', '-select_streams', 'v:0',
                                      '-show_entries', 'stream=nb_frames,r_frame_rate',
                                      '-of', 'json', str(path)], text=True)
    stream = json.loads(result)['streams'][0]
    return stream['nb_frames'], stream['r_frame_rate']


def package(root: Path, destination: Path) -> dict:
    plan = json.loads((root / 'plan.json').read_text())
    status = collect(root)
    counts = status['status_counts']
    complete_count = counts.get('COMPLETE_UNREVIEWED', 0)
    excluded_count = counts.get('EXCLUDED_TRACKING_NO_BLOBS', 0)
    if complete_count + excluded_count != len(plan['tasks']):
        raise RuntimeError(f'Only {complete_count} completed reviews and {excluded_count} documented tracking exclusions among {len(plan["tasks"])} tasks')
    if destination.exists():
        raise FileExistsError(destination)
    with tempfile.TemporaryDirectory(prefix='dyad-package-', dir=root) as temporary:
        stage = Path(temporary)
        (stage / 'reports').mkdir()
        for source in (root / 'reports_v151r081').iterdir():
            if source.is_file():
                shutil.copy2(source, stage / 'reports' / source.name)
        shutil.copy2(root / 'plan.json', stage / 'plan.json')
        for name in ('SIX_BEETLE_METHODS.html','DATA_DICTIONARY.md',
                     'INVALIDATED_DYADIC_OUTPUTS_20260924.md'):
            source = CODE/name
            if not source.is_file():
                raise FileNotFoundError(source)
            shutil.copy2(source,stage/name)
        code_files=('persistent_groups.py','six_beetle_processor.py','frame_data.py',
                    'output_manifest.py','psc_release_validation.py','dyadic_quality.py',
                    'dyadic_batch_refinalize_v151r081.py')
        snapshot=json.loads((CODE/'RELEASE_VERSION.json').read_text())
        if snapshot.get('psc_model_version') != '1.5.1':
            raise RuntimeError('Code snapshot is not PSC 1.5.1')
        version=dict(schema='dyadic-psc-release-v1',
                     created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                     psc_model_version='1.5.1',group_processor_version='0.8.1-group',
                     review_view_version=VIEW_VERSION,
                     code_commit=snapshot['git_commit'],qc_status='UNREVIEWED',
                     plan_sha256=sha256(root/'plan.json'),source_tomls_untouched=True,
                     code_sha256={name:sha256(CODE/name) for name in code_files})
        (stage/'VERSION_CONTROL.json').write_text(json.dumps(version,indent=2)+'\n')
        readme = ('2026 dyadic fight IDtracker and presumed social contact reviews\n'
                  'PSC model 1.5.1; group processor 0.8.1-group. Older PSC outputs are withdrawn.\n\n'
                  'Open each tasks/<id>/review/interaction_review.html next to its review_video.mp4.\n'
                  'Use the RAW IDtracker switch to compare source assignments with PSC positions at the same frame; the switch does not alter CSV or PDF statistics.\n'
                  'The MP4 is a compact derivative of the full-resolution Firebird review; '
                  'frame count and frame rate match the original. Source TOMLs are unchanged.\n'
                  'submitted.toml is the exact immutable tracking input with background subtraction on.\n'
                  'The original TOML interval ends exclusively; final analysis converts it to an inclusive end.\n'
                  'Completed outputs are UNREVIEWED computational suggestions, not human-verified identities.\n'
                  'Any failed original-settings tracking run is retained as an excluded receipt and log, without an invented PDF.\n'
                  'See reports/beetle_quality.csv for raw, screened-without-PSC and after-PSC missingness, paired movement and fungus metrics.\n'
                  'Each analysis has paired raw/PSC window, region, and fungus CSVs and a paired PDF.\n'
                  'IDtracker identity scores are self-reported scores, not calibrated correctness probabilities.\n')
        (stage / 'README.txt').write_text(readme)
        manifests = []
        for index, task in enumerate(plan['tasks'], 1):
            folder = root / 'tasks' / task['id']
            old_state = json.loads((folder / 'final_status.json').read_text()) if (folder/'final_status.json').is_file() else {}
            excluded = old_state.get('stage') == 'EXCLUDED_TRACKING_NO_BLOBS'
            state = old_state if excluded else json.loads((folder/'status_v151r081.json').read_text())
            out = stage / 'tasks' / task['id']
            (out / 'input').mkdir()
            for name in ('source.toml', 'submitted.toml'):
                shutil.copy2(folder / 'input' / name, out / 'input' / name)
            for name in ('task.json', 'final_status.json', 'status.json', 'status_v151r081.json'):
                if (folder/name).is_file():
                    shutil.copy2(folder / name, out / name)
            if state['stage'] == 'EXCLUDED_TRACKING_NO_BLOBS':
                for log in folder.glob('idtracker_attempt_*.log'):
                    shutil.copy2(log, out / log.name)
                print(f'{index}/{len(plan["tasks"])} {task["id"]}: excluded tracking input', flush=True)
                continue
            (out / 'analysis').mkdir()
            (out / 'review').mkdir()
            shutil.copy2(folder / 'quality_v151r081.json', out / 'quality_v151r081.json')
            for source in (folder / 'analysis_v151r081').iterdir():
                if source.is_file():
                    shutil.copy2(source, out / 'analysis' / source.name)
            review = folder / 'review_compare_v151r081'
            review_meta = json.loads((review / 'source_manifest.json').read_text())
            if (review_meta.get('review_view_version') != VIEW_VERSION or
                    review_meta.get('analysis_manifest_sha256') != sha256(folder / 'analysis_v151r081' / 'manifest.json') or
                    review_meta.get('status') != 'UNREVIEWED'):
                raise RuntimeError(f'Comparison viewer is missing or bound to a different analysis: {task["id"]}')
            shutil.copy2(review / 'interaction_review.html', out / 'review' / 'interaction_review.html')
            original = review / 'review_video.mp4'
            compact = out / 'review' / 'review_video.mp4'
            command = [FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(original),
                       '-an', '-vf', 'scale=960:-2', '-c:v', 'libx264', '-preset', 'veryfast',
                       '-crf', '36', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(compact)]
            subprocess.run(command, check=True)
            if video_frames(original) != video_frames(compact):
                raise RuntimeError(f'Video frame or rate mismatch: {task["id"]}')
            source_manifest = json.loads((review / 'source_manifest.json').read_text())
            source_manifest['original_review_video_sha256'] = source_manifest.get('copied_video_sha256')
            source_manifest['copied_video_sha256'] = sha256(compact)
            source_manifest['portable_video_transcode'] = command[:-1] + ['review_video.mp4']
            (out / 'review' / 'source_manifest.json').write_text(json.dumps(source_manifest, indent=2) + '\n')
            manifests.append(dict(task_id=task['id'], original_bytes=original.stat().st_size,
                                  compact_bytes=compact.stat().st_size,
                                  compact_sha256=sha256(compact)))
            print(f'{index}/{len(plan["tasks"])} {task["id"]}: {compact.stat().st_size} bytes', flush=True)
        (stage / 'reports' / 'portable_videos.json').write_text(json.dumps(manifests, indent=2) + '\n')
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6, allowZip64=True) as archive:
            for path in sorted(stage.rglob('*')):
                if path.is_file():
                    archive.write(path, path.relative_to(stage))
    return dict(zip=str(destination), bytes=destination.stat().st_size,
                sha256=sha256(destination), completed_review_count=len(manifests),
                excluded_tracking_count=excluded_count)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.root, args.destination), indent=2))


if __name__ == '__main__':
    main()
