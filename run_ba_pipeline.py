#!/usr/bin/env python3
"""BA: one animal, one arena, prototype metrics and synchronized video review."""
from __future__ import annotations
import argparse
import ast
import csv
from datetime import datetime, timezone
from fractions import Fraction
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import numpy as np
import processor
import unified_qc
import ba_qc
import ba_turtling
from run_six_beetle_pipeline import find_trajectory, session_json, sha256, arena_crop, probe_video, make_review_video
from review_geometry import plan_review_geometry

VERSION = '0.4.0-unified-100px-jump'


def source_config(toml_path, session, frame_count=7200):
    config = tomllib.loads(Path(toml_path).read_text())
    if config.get('number_of_animals') != 1 or len(config.get('roi_list', [])) != 1:
        raise ValueError('BA requires exactly one animal and one arena ROI in the TOML')
    intervals = config.get('tracking_intervals', [])
    if len(intervals) != 1 or len(intervals[0]) != 2:
        raise ValueError('BA requires one unambiguous TOML tracking interval')
    start, stop = intervals[0]
    if any(isinstance(v, bool) or not isinstance(v, int) for v in (start, stop)) or start <= 0:
        raise ValueError('Tracking interval must use integer frames with a positive start')
    if frame_count < 2 or start + frame_count > stop:
        raise ValueError('Requested inclusive frame window does not fit the TOML tracking interval')
    metadata = json.loads(session_json(Path(session)).read_text())
    if metadata.get('number_of_animals') != 1:
        raise ValueError('Tracking session must contain one animal')
    rois = processor.load_rois(Path(session))
    raw = config['roi_list'][0]
    if isinstance(raw, str):
        match = re.search(r'(\[\s*\[.*\]\s*\])', raw)
        if not match or not raw.lstrip().startswith('+'):
            raise ValueError('BA expects an inclusion polygon')
        raw = ast.literal_eval(match.group(1))
    polygon = np.asarray(raw, dtype=float)
    if (len(rois) != 1 or polygon.shape != rois[0].shape or
            not np.isfinite(polygon).all() or not np.allclose(polygon, rois[0], rtol=0, atol=1e-6)):
        raise ValueError('Source TOML and tracked-session arena do not match')
    area = abs(np.sum(polygon[:, 0]*np.roll(polygon[:, 1], -1)-polygon[:, 1]*np.roll(polygon[:, 0], -1)))/2
    if area <= 0:
        raise ValueError('Arena must have positive area')
    videos = config.get('video_paths', [])
    session_videos = metadata.get('video_paths', [])
    if len(videos) != 1 or len(session_videos) != 1 or Path(videos[0]).name != Path(session_videos[0]).name:
        raise ValueError('Expected matching single source video in TOML and session')
    tracked = metadata.get('tracking_intervals', [])
    if not any(lo <= start and hi >= start+frame_count for lo, hi in tracked):
        raise ValueError('Session tracking interval does not cover the requested BA window')
    return config, start, start+frame_count-1, polygon


def frame_rows(xy, arena, start, jump_threshold=100., wall_buffer=30.):
    """Same accepted adjacent steps and exact wall geometry as prototype."""
    raw_xy=xy.copy()
    qc = processor.repair_jump_locations(xy, jump_threshold)
    xy=qc['cleaned_xy']
    valid = np.isfinite(xy).all(axis=1)
    inside = np.zeros(len(xy), bool)
    wall = np.zeros(len(xy), bool)
    inside[valid] = processor.points_inside_polygon(xy[valid], arena)
    wall[valid] = inside[valid] & (processor.distance_to_polygon_boundary(xy[valid], arena) <= wall_buffer)
    turtle = processor.compute_turtling_candidates(raw_xy)['mask']
    for t, point in enumerate(xy):
        possible = t > 0 and valid[t-1] and valid[t]
        rejected = bool(t > 0 and qc['rejected_step_mask'][t-1])
        accepted = bool(possible and not rejected)
        yield dict(global_frame=start+t, animal_id=0,
                   raw_x=float(raw_xy[t,0]) if np.isfinite(raw_xy[t,0]) else '', raw_y=float(raw_xy[t,1]) if np.isfinite(raw_xy[t,1]) else '',
                   location_edit=qc['location_source'][t], jump_policy_version=qc['jump_policy']['version'],
                   x=float(point[0]) if valid[t] else '', y=float(point[1]) if valid[t] else '',
                   location_known=int(valid[t]), in_arena=int(inside[t]),
                   in_wall_buffer=int(wall[t]), in_arena_interior=int(inside[t] and not wall[t]),
                   step_from_previous_accepted=int(accepted), rejected_jump_step=int(rejected),
                   step_distance_px=float(qc['step_distance_px'][t-1]) if accepted else '',
                   turtling_candidate=int(turtle[t]))


def write_csv(path, rows, fields=None):
    with Path(path).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(args):
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(f'Refusing existing output: {output}')
    session = Path(args.session).resolve()
    toml = Path(args.toml).resolve()
    trajectory = Path(args.trajectory).resolve() if args.trajectory else find_trajectory(session)
    sources = {'toml':toml, 'session':session_json(session), 'trajectory':trajectory}
    hashes = {name:sha256(path) for name,path in sources.items()}
    config, start, end, arena = source_config(toml, session, args.frames)
    video = Path(args.source_video or config['video_paths'][0]).resolve()
    if video.name != Path(config['video_paths'][0]).name:
        raise ValueError('Local source video must retain its TOML basename')
    sources['video'] = video
    hashes['video'] = sha256(video)
    processor.validate_trajectory_source(trajectory)
    arr = processor.load_trajectories(trajectory)
    if arr.ndim != 3 or arr.shape[1:] != (1, 2) or end >= len(arr):
        raise ValueError('Expected global-frame trajectories with exactly one animal covering the BA window')
    for value in (args.threshold, args.jump_threshold, args.wall_buffer):
        if not np.isfinite(value) or value < 0:
            raise ValueError('Thresholds must be finite and nonnegative')
    if args.threshold == 0 or args.jump_threshold == 0:
        raise ValueError('Movement and jump thresholds must be positive')
    probe = json.loads(subprocess.run([args.ffprobe,'-v','error','-select_streams','v:0',
        '-show_entries','stream=avg_frame_rate','-of','json',str(video)],check=True,capture_output=True,text=True).stdout)
    fps = float(Fraction(probe['streams'][0]['avg_frame_rate']))
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError('Source video needs a valid frame rate')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.ba-', dir=output.parent))
    try:
        rows = processor.analyze(trajectory, session, start, end-start, args.threshold,
            wall_buffer_px=args.wall_buffer, analysis_type='BA',
            one_frame_jump_threshold_px=args.jump_threshold,
            analysis_start_source='SOURCE_TOML_TRACKING_START')
        write_csv(staging/'summary.csv', rows, processor.OUTPUT_COLUMNS)
        frames = list(frame_rows(arr[start:end+1,0], arena, start, args.jump_threshold, args.wall_buffer))
        write_csv(staging/'frame_data.csv', frames)
        from jump_policy import repair
        (staging/'jump_corrections.json').write_text(json.dumps(repair(arr[start:end+1,0].tolist(),start),indent=2)+'\n')
        turtle = ba_turtling.summarize([f['turtling_candidate'] for f in frames], [f['location_known'] for f in frames], start, fps)
        experimental = None
        if getattr(args, 'experimental_turtling', False):
            from ba_turtling_candidates import candidate_episodes
            experimental = candidate_episodes(arr[start:end+1,0],
                [f['turtling_candidate'] for f in frames], start, fps)
            (staging/'turtling_experimental.json').write_text(json.dumps(experimental,indent=2)+'\n')
            turtle['experimental'] = experimental
        (staging/'turtling_bouts.json').write_text(json.dumps(turtle, indent=2)+'\n')
        pdf_name = toml.stem+'.pdf'
        processor.write_plot_pdf(staging/pdf_name,trajectory,session,rows,'BA',video.name,toml.stem,'UNREVIEWED',ba_turtling_report=turtle)
        (staging/'qc.json').write_text(json.dumps(ba_qc.summarize(frames,rows[0]),indent=2)+'\n')
        unified = unified_qc.run_qc(staging, trajectory, video, start, end, fps, arena,
            ffmpeg=args.ffmpeg, cache_dir=getattr(args, 'qc_cache_dir', None) or output.parent/'.unified_qc_cache',
            skip_video=getattr(args, 'skip_qc_video', False), review_link='review.html',
            existing_reports=['qc.json', 'turtling_bouts.json'])
        width,height = probe_video(video,args.ffprobe)
        crop = arena_crop([arena],width,height)
        geometry = plan_review_geometry([arena],crop)
        make_review_video(video,staging/'review_video.mp4',start,end,crop,args.ffmpeg,geometry)
        shutil.copy2(toml,staging/'source.toml')
        manifest = dict(schema='ba-pipeline-run-v1', experiment_type='BA',pipeline_version=VERSION,
            base_processor_version=processor.SCRIPT_VERSION, qc_status='UNREVIEWED',
            created_utc=datetime.now(timezone.utc).isoformat(), animal_count=1, roi_count=1,
            start_global_frame=start,end_global_frame_inclusive=end,frame_count=end-start+1,fps=fps,
            source_paths={name:str(path) for name,path in sources.items()}, source_sha256=hashes,
            settings=dict(movement_threshold_px=args.threshold,wall_buffer_px=args.wall_buffer,
                          one_frame_jump_threshold_px=args.jump_threshold),
            coordinate_policy='Jump locations marked interpolated or jump_removed; raw_x/raw_y retained; bounded interpolation <=15 frames with anchors <=100px apart. No social PSC.',
            turtling_policy='Prototype movement-pattern candidate only; does not establish posture.',
            pdf_style='prototype-0.8.1',viewer_version='ba-review-v3',turtling_module_version=ba_turtling.VERSION,video_geometry=geometry)
        manifest['unified_qc'] = unified
        code_names = ['jump_policy.py','unified_qc.py','run_ba_pipeline.py','ba_qc.py','ba_turtling.py','ba_review_template.html','processor.py','review_geometry.py','run_six_beetle_pipeline.py']
        if experimental is not None:
            code_names.append('ba_turtling_candidates.py')
            manifest['experimental_turtling'] = dict(version=experimental['version'],
                status=experimental['status'],rules=experimental['rules'])
        manifest['code_sha256'] = {name:sha256(Path(__file__).with_name(name)) for name in code_names}
        payload = dict(label=toml.stem,start=start,end=end,fps=fps,frames=frames,
                       arena=arena.tolist(),geometry=geometry,jumpThreshold=args.jump_threshold,
                       sourceHashes=hashes,turtling=turtle)
        if experimental is not None:
            payload['experimental'] = experimental
        template = Path(__file__).with_name('ba_review_template.html').read_text()
        template = template.replace('__TITLE__',html.escape(toml.stem))
        template = template.replace('__PAYLOAD__',json.dumps(payload,allow_nan=False,separators=(',',':')).replace('<','\\u003c'))
        (staging/'review.html').write_text(template)
        for name,path in sources.items():
            if sha256(path) != hashes[name]:
                raise RuntimeError(f'Source changed during analysis: {path}')
        manifest['output_sha256'] = {p.name:sha256(p) for p in staging.iterdir() if p.is_file()}
        (staging/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        if output.exists():
            raise FileExistsError(output)
        os.rename(staging,output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('toml','session','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--trajectory')
    parser.add_argument('--source-video',help='Optional local copy with the same basename as the TOML video')
    parser.add_argument('--frames',type=int,default=7200,help='Inclusive observation count, not end minus start')
    parser.add_argument('--threshold',type=float,default=30.)
    parser.add_argument('--wall-buffer',type=float,default=30.)
    parser.add_argument('--jump-threshold',type=float,default=100.)
    parser.add_argument('--ffmpeg',default='ffmpeg')
    parser.add_argument('--ffprobe',default='ffprobe')
    unified_qc.add_arguments(parser)
    parser.add_argument('--experimental-turtling',action='store_true',
        help='Add separate UNVALIDATED onset/quiet-pause candidates; retain baseline metrics')
    print(run(parser.parse_args()))

if __name__=='__main__':
    main()
