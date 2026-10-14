"""Shared review-only QC for source recordings and raw animal trajectories.

No flag changes coordinates, tracking intervals, behavior labels, or approval.
Image hypotheses are deliberately distinct from attributed human exclusions.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import os
import subprocess
import tempfile

import numpy as np

VERSION = '0.1.0-development'
THRESHOLDS = dict(brightness_delta=8., affected_tiles=6, translation_pixels=2.,
                  phase_peak=.15, raw_jump_pixels=100., stationary_seconds=20.)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def bouts(mask):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)-1))


def image_pair(previous, current):
    """Global image evidence, not a physical cause classification."""
    a, b = np.asarray(previous, float), np.asarray(current, float)
    if a.shape != (90, 160) or b.shape != a.shape:
        raise ValueError('Expected 160x90 grayscale images')
    delta = b-a
    tiles = [float(np.median(delta[y:y+30, x:x+40]))
             for y in range(0, 90, 30) for x in range(0, 160, 40)]
    win = np.outer(np.hanning(90), np.hanning(160))
    cross = np.fft.fft2((b-b.mean())*win)*np.conj(np.fft.fft2((a-a.mean())*win))
    corr = np.fft.ifft2(cross/np.maximum(abs(cross), 1e-8)).real
    y, x = np.unravel_index(corr.argmax(), corr.shape)
    x, y = int(x if x <= 80 else x-160), int(y if y <= 45 else y-90)
    peak = float(corr.max())
    up = sum(v >= THRESHOLDS['brightness_delta'] for v in tiles)
    down = sum(v <= -THRESHOLDS['brightness_delta'] for v in tiles)
    lighting = max(up, down) >= THRESHOLDS['affected_tiles']
    motion = np.hypot(x, y) >= THRESHOLDS['translation_pixels'] and peak >= THRESHOLDS['phase_peak']
    return dict(brightness=float(np.median(b)), brightness_change=float(np.median(delta)),
                tile_changes=tiles, shift_x=x, shift_y=y, phase_peak=peak,
                lighting_candidate=bool(lighting), camera_motion_candidate=bool(motion))


def scan_video(video, ffmpeg='ffmpeg', cache_dir=None):
    """Every original frame is decoded; cache is content/version/threshold bound."""
    video = Path(video)
    source_hash = digest(video)
    settings = dict(version=VERSION, thresholds=THRESHOLDS, size=[160, 90], stride=1)
    key = hashlib.sha256(json.dumps([source_hash, settings], sort_keys=True).encode()).hexdigest()
    cached = Path(cache_dir)/f'{key}.json' if cache_dir else None
    if cached and cached.exists():
        result = json.loads(cached.read_text())
        if result.get('source_sha256') != source_hash or result.get('settings') != settings:
            raise ValueError('QC cache identity mismatch')
        return result
    cmd = [ffmpeg, '-v', 'error', '-threads', '2', '-i', str(video), '-map', '0:v:0',
           '-vf', 'scale=160:90,format=gray', '-vsync', '0', '-threads', '1', '-f', 'rawvideo', '-']
    metrics = []
    previous = None
    count = 0
    with tempfile.TemporaryFile() as errors:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=errors)
        try:
            while True:
                raw = proc.stdout.read(160*90)
                if not raw:
                    break
                if len(raw) != 160*90:
                    raise ValueError('Incomplete decoded QC frame')
                current = np.frombuffer(raw, np.uint8).reshape(90, 160)
                if previous is not None:
                    metrics.append(dict(frame=count, previous_frame=count-1, **image_pair(previous, current)))
                previous = current
                count += 1
            if proc.wait():
                errors.seek(0)
                raise RuntimeError(errors.read().decode(errors='replace')[-2000:])
        finally:
            proc.stdout.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    if count < 2:
        raise ValueError('Insufficient decoded frames')
    if digest(video) != source_hash:
        raise ValueError('Video changed during QC')
    result = dict(status='ASSESSED', source_sha256=source_hash, settings=settings,
                  decoded_frames=count, metrics=metrics,
                  interpretation='Full-image low-resolution candidates; cannot identify a light switch, person, identity swap, or subtle camera motion reliably.')
    if cached:
        cached.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=cached.parent, delete=False) as f:
            json.dump(result, f, allow_nan=False)
            temp = f.name
        os.replace(temp, cached)
    return result


def summarize(raw, start, fps, arena=None, excluded=(), video_scan=None):
    raw = np.asarray(raw, float)
    if raw.ndim != 3 or raw.shape[2] != 2 or not len(raw) or raw.shape[1] < 1:
        raise ValueError('Expected nonempty frame x animal x 2 raw coordinates')
    if type(start) is not int or start < 0 or not np.isfinite(fps) or fps <= 0:
        raise ValueError('Invalid global start or frame rate')
    n, animals, _ = raw.shape
    eligible = np.ones(n, bool)
    for pair in excluded:
        if len(pair) != 2 or any(type(x) is not int for x in pair) or pair[0] < start or pair[1] < pair[0] or pair[1] >= start+n:
            raise ValueError('Exclusion must be an inclusive range within this window')
        eligible[pair[0]-start:pair[1]-start+1] = False
    known = np.isfinite(raw).all(axis=2)
    steps = np.linalg.norm(np.diff(raw, axis=0), axis=2)
    adjacent = known[:-1] & known[1:] & eligible[:-1, None] & eligible[1:, None]
    jumps = adjacent & (steps > THRESHOLDS['raw_jump_pixels'])
    events = []
    def add(kind, scope, lo, hi, evidence, animal=None):
        events.append(dict(kind=kind, scope=scope, animal_id=animal,
                           first_global_frame=int(lo), last_global_frame_inclusive=int(hi),
                           review_status='UNREVIEWED', evidence=evidence))
    for lo, hi in bouts(~eligible):
        add('INTENTIONAL_EXCLUSION', 'run', start+lo, start+hi,
            'Attributed exclusion supplied separately; never a negative behavior label.')
    per_animal = []
    for a in range(animals):
        missing = ~known[:, a] & eligible
        outside = np.zeros(n, bool)
        if arena is not None:
            from matplotlib.path import Path as Polygon
            polygon = np.asarray(arena, float)
            if polygon.ndim != 2 or polygon.shape[1] != 2 or len(polygon) < 3 or not np.isfinite(polygon).all():
                raise ValueError('Invalid arena polygon')
            outside = known[:, a] & eligible & ~Polygon(polygon).contains_points(raw[:, a], radius=1e-7)
        for kind, mask in [('MISSING_TRACKING', missing), ('OUTSIDE_ARENA', outside),
                           ('RAW_JUMP', np.r_[False, jumps[:, a]])]:
            for lo, hi in bouts(mask):
                add(kind, 'animal', start+lo, start+hi,
                    'Raw positions only; original-image pixels. Missing IDs may reflect normal occlusion.', a+1)
        stationary = adjacent[:, a] & (steps[:, a] == 0)
        for lo, hi in bouts(stationary):
            if hi-lo+2 >= int(np.ceil(fps*THRESHOLDS['stationary_seconds'])):
                add('EXACT_STATIONARITY', 'animal', start+lo, start+hi+1,
                    'May be real immobility or a tracking problem; posture unassessed.', a+1)
        denom = int(eligible.sum())
        per_animal.append(dict(animal_id=a+1, eligible_frames=denom, missing_frames=int(missing.sum()),
                               missing_percent=100*float(missing.sum())/denom if denom else None,
                               longest_missing_frames=int(max((hi-lo+1 for lo, hi in bouts(missing)), default=0)),
                               raw_jump_steps=int(jumps[:, a].sum()), outside_arena_frames=int(outside.sum()) if arena is not None else None))
    shared = jumps.sum(axis=1) >= max(2, int(np.ceil(animals/2)))
    for lo, hi in bouts(shared):
        add('SYNCHRONOUS_RAW_JUMPS', 'run', start+lo+1, start+hi+1,
            'Multiple IDs jump together; shared disturbance is a hypothesis, not a cause diagnosis.')
    scan = video_scan or dict(status='NOT_ASSESSED', reason='No source-video scan supplied')
    if scan['status'] == 'ASSESSED':
        if scan['decoded_frames'] < start+n:
            raise ValueError('Video does not cover analysis window')
        for key, kind in [('lighting_candidate', 'LIGHTING_CHANGE'), ('camera_motion_candidate', 'POSSIBLE_CAMERA_MOTION')]:
            candidates = [m for m in scan['metrics'] if start <= m['frame'] < start+n and m[key]]
            for m in candidates:
                add(kind, 'recording', m['previous_frame'], m['frame'],
                    {k:m[k] for k in ['brightness_change','tile_changes','shift_x','shift_y','phase_peak']})
    return dict(schema='unified-video-qc-v1', version=VERSION, status='UNREVIEWED',
                assessment_complete=scan['status']=='ASSESSED', thresholds=THRESHOLDS,
                window=dict(start=start, end_inclusive=start+n-1, frames=n), animal_count=animals,
                intentionally_excluded_frames=int((~eligible).sum()), per_animal=per_animal,
                recording_scan={k:v for k,v in scan.items() if k!='metrics'},
                events=sorted(events, key=lambda e:(e['first_global_frame'], e['kind'])),
                unassessed=['Animal identity correctness','Anatomical posture/turtling','Person versus shadow','Subtle or local camera distortion'],
                policy='Review hypotheses only. No automatic exclusion, correction, interpolation or approval. Rates use eligible animal observations; flags are not measured error rates.')


def write_report(output, report, raw, scan=None, review_link=None):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name in ['unified_qc.json', 'unified_qc.html']:
        if (output/name).exists():
            raise FileExistsError(output/name)
    (output/'unified_qc.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    esc = lambda x: html.escape(str(x))
    body = '<h1>Video and tracking review</h1><p><b>UNREVIEWED · automatic evidence, not an exclusion decision.</b></p>'
    body += '<p>'+esc(report['source']['video'])+'</p><p>'+esc(report['policy'])+'</p>'
    body += '<p>Recording check: <b>'+esc(report['recording_scan']['status'])+'</b>. '+esc(report['recording_scan'].get('reason',''))+'</p>'
    if review_link:
        body += '<p><a href="'+esc(review_link)+'">Open synchronized review video</a></p>'
    body += '<h2>Tracking by animal</h2><table><tr><th>Animal</th><th>Eligible frames</th><th>Missing %</th><th>Longest gap</th><th>Jumps &gt;100 px</th></tr>'
    for a in report['per_animal']:
        body += '<tr>'+''.join('<td>'+esc(a[k])+'</td>' for k in ['animal_id','eligible_frames','missing_percent','longest_missing_frames','raw_jump_steps'])+'</tr>'
    body += '</table><p>Intentionally excluded frames per animal: '+str(report['intentionally_excluded_frames'])+'. These do not enter missing percentages.</p>'
    # Raw XY traces never bridge missing frames or intentional exclusions.
    points = np.array(raw, copy=True)
    for e in report['events']:
        if e['kind']=='INTENTIONAL_EXCLUSION':
            points[e['first_global_frame']-report['window']['start']:e['last_global_frame_inclusive']-report['window']['start']+1] = np.nan
    good = np.isfinite(points).all(axis=2)
    if good.any():
        lo = points[good].min(axis=0);span = np.maximum(points[good].max(axis=0)-lo, 1)
        body += '<h2>Raw position traces</h2><p>Each panel is one animal. Missing/excluded gaps are disconnected; long jumps remain visible. These traces do not establish identity or posture.</p>'
        for a in range(points.shape[1]):
            body += '<span>Animal '+str(a+1)+'</span><svg viewBox="0 0 320 220" width="320" height="220" role="img" aria-label="Raw animal trajectory">'
            for first,last in bouts(good[:,a]):
                coords=(points[first:last+1,a]-lo)/span*[300,200]+10
                body += '<polyline fill="none" stroke="#236d81" stroke-width="1" points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in coords)+'"/>'
            body += '</svg>'
    if scan and scan.get('status') == 'ASSESSED':
        samples=[m for m in scan['metrics'] if report['window']['start'] <= m['frame'] <= report['window']['end_inclusive']]
        if samples:
            width=max(1,report['window']['frames']-1)
            xy=' '.join(f"{(m['frame']-report['window']['start'])/width*980+10:.2f},{140-m['brightness']/255*130:.2f}" for m in samples)
            body += '<h2>Recording brightness</h2><p>Full-image median gray level (0–255); horizontal range is original frames '+str(report['window']['start'])+'–'+str(report['window']['end_inclusive'])+'. Local disturbances can be missed by this summary.</p><svg viewBox="0 0 1000 150" style="width:100%;height:150px" role="img" aria-label="Recording brightness over original frames"><polyline fill="none" stroke="#986000" points="'+xy+'"/></svg>'
    body += '<h2>Reasons to inspect</h2><p>Open a reason below for its frame ranges. Frames are original global frames, inclusive. Image transitions span the compared pair; they are not exact bad-frame boundaries. Camera shifts use the reduced 160×90 image. Counts overlap and must not be added as independent errors.</p>'
    kinds=sorted({e['kind'] for e in report['events']})
    for kind in kinds:
        group=[e for e in report['events'] if e['kind']==kind]
        body += '<details><summary>'+esc(kind)+' — '+str(len(group))+' evidence intervals</summary><table><tr><th>Scope / animal</th><th>Frames</th><th>Evidence</th></tr>'
        for e in group:
            body += '<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [f"{e['scope']} / {e['animal_id'] or 'all'}",f"{e['first_global_frame']}–{e['last_global_frame_inclusive']}",e['evidence']])+'</tr>'
        body += '</table></details>'
    if not kinds:
        body += '<p>No implemented threshold flags. This is not approval, and unassessed checks remain unknown.</p>'
    body += '<h2>Still needs separate review</h2><p>'+esc('; '.join(report['unassessed']))+'</p>'
    if report.get('existing_review_reports'):
        body += '<p>Existing behavior / PSC / QC reports: '+', '.join('<a href="'+esc(x)+'">'+esc(x)+'</a>' for x in report['existing_review_reports'])+'. Their labels remain separate.</p>'
    page='<!doctype html><meta charset="utf-8"><title>Unified QC review</title><style>body{font:16px system-ui;max-width:1200px;margin:30px auto;padding:0 20px;line-height:1.5}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:8px;text-align:left;overflow-wrap:anywhere}svg{border:1px solid #ddd;margin:10px}td:last-child{max-width:500px}</style>'+body
    (output/'unified_qc.html').write_text(page)


def run_qc(output, trajectory, video, start, end, fps, arena=None, ffmpeg='ffmpeg',
           cache_dir=None, skip_video=False, review_link=None, existing_reports=()):
    from processor import load_trajectories, validate_trajectory_source
    validate_trajectory_source(Path(trajectory))
    a = load_trajectories(Path(trajectory))
    if start < 0 or end < start or end >= len(a):
        raise ValueError('QC window outside raw trajectory')
    raw = a[start:end+1]
    if skip_video:
        scan = dict(status='NOT_ASSESSED', reason='Source scan explicitly skipped; disturbance status is unknown')
    else:
        print('Unified QC: checking source recording at every frame (or reusing a content-matched cache)', flush=True)
        try:
            scan = scan_video(video, ffmpeg, cache_dir)
        except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
            scan = dict(status='FAILED', reason=str(exc))
    report = summarize(raw, int(start), fps, arena, video_scan=scan)
    report['source'] = dict(video=str(video), trajectory=str(trajectory), trajectory_sha256=digest(trajectory))
    report['code_sha256'] = digest(__file__)
    report['existing_review_reports'] = list(existing_reports)
    write_report(output, report, raw, scan, review_link)
    return dict(version=VERSION, assessment_complete=report['assessment_complete'],
                recording_status=scan['status'], json='unified_qc.json', html='unified_qc.html',
                json_sha256=digest(Path(output)/'unified_qc.json'), html_sha256=digest(Path(output)/'unified_qc.html'))


def add_arguments(parser):
    parser.add_argument('--qc-cache-dir', help='Shared content-bound source-video QC cache')
    parser.add_argument('--skip-qc-video', action='store_true', help='Mark disturbance screening NOT_ASSESSED; raw trajectory QC still runs')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['trajectory','video','output']:p.add_argument('--'+name,required=True)
    p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True)
    p.add_argument('--fps',type=float,required=True);p.add_argument('--ffmpeg',default='ffmpeg')
    add_arguments(p);a=p.parse_args()
    if Path(a.output).exists():raise FileExistsError(a.output)
    print(json.dumps(run_qc(a.output,a.trajectory,a.video,a.start,a.end,a.fps,
                           ffmpeg=a.ffmpeg,cache_dir=a.qc_cache_dir,skip_video=a.skip_qc_video),indent=2))

if __name__=='__main__':main()
