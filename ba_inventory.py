#!/usr/bin/env python3
"""Read-only BA inventory and reproducible, video-stratified pilot selection."""
import argparse
import ast
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
try:
    import tomllib
except ImportError:
    import tomli as tomllib

ROOT='/data/labs/vformic1-swat-lab'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def polygon(raw):
    if isinstance(raw,str):
        match=re.search(r'(\[\s*\[.*\]\s*\])',raw)
        if not match:return None
        raw=ast.literal_eval(match.group(1))
    return raw

def key(d):
    videos=d.get('video_paths',[]);rois=d.get('roi_list',[])
    if len(videos)!=1 or len(rois)!=1 or d.get('number_of_animals')!=1:return None
    return Path(videos[0]).name,json.dumps(polygon(rois[0]),sort_keys=True)

def inventory(root=ROOT,seed=20260929,sample_size=6):
    root=Path(root);ba=root/'2026_Videos/2026_BA'
    sessions=defaultdict(list)
    roots=[ba,root/'idtracker_session_archive/2026',root/'idtracker_pipeline_runs/runs']
    for base in roots:
        for path in sorted(base.rglob('session.json')):
            try:
                d=json.loads(path.read_text());k=key(d)
                if k is None:continue
                trajectories=list(path.parent.glob('trajectories/trajectories.npy'))
                if not trajectories:trajectories=list(path.parent.glob('trajectories.npy'))
                if len(trajectories)!=1:continue
                sessions[k].append(dict(session=str(path.parent),session_sha256=digest(path),trajectory=str(trajectories[0]),settings=d))
            except (ValueError,TypeError,OSError):continue
    rows=[]
    compared=('intensity_ths','area_ths','use_bkg','background_subtraction_stat','track_wo_identities')
    for path in sorted(ba.rglob('*.toml')):
        row=dict(toml=str(path),toml_sha256=digest(path),flags=[])
        try:
            d=tomllib.loads(path.read_text());k=key(d)
            row.update(video=d.get('video_paths',[''])[0],animal_count=d.get('number_of_animals'),roi_count=len(d.get('roi_list',[])),intervals=d.get('tracking_intervals'))
            if k is None:row['flags'].append('INVALID_BA_STRUCTURE')
            intervals=d.get('tracking_intervals',[])
            if len(intervals)!=1:row['flags'].append('AMBIGUOUS_INTERVAL')
            else:
                start,stop=intervals[0];row.update(start=start,end_inclusive=start+7199)
                if start<=0:row['flags'].append('ZERO_OR_NEGATIVE_START')
                if start+7200>stop:row['flags'].append('SOURCE_INTERVAL_TOO_SHORT')
            if not Path(row['video']).is_file():row['flags'].append('SOURCE_VIDEO_MISSING')
            matches=[]
            for candidate in sessions.get(k,[]):
                c=dict(candidate);settings=c.pop('settings')
                c['settings_differences']={name:dict(toml=repr(d.get(name)),session=repr(settings.get(name))) for name in compared if d.get(name)!=settings.get(name)}
                c['covers_window']=(any(lo<=row['start'] and hi>=row['end_inclusive']+1 for lo,hi in settings.get('tracking_intervals',[])) if 'start' in row else None)
                matches.append(c)
            row['sessions']=matches
            if not matches:row['flags'].append('NO_MATCHING_TRACKING')
            elif len(matches)>1:row['flags'].append('MULTIPLE_MATCHING_SESSIONS')
            if matches and 'start' in row and not any(c['covers_window'] for c in matches):row['flags'].append('TRACKING_INTERVAL_TOO_SHORT')
            if matches and all(c['settings_differences'] for c in matches):row['flags'].append('TRACKING_SETTINGS_DIFFER')
        except Exception as exc:row['flags'].append('CONFIG_PARSE_ERROR');row['error']=str(exc)
        rows.append(row)
    by_video=defaultdict(list)
    for row in rows:by_video[row.get('video','UNKNOWN')].append(row)
    rng=random.Random(seed)
    videos=rng.sample(sorted(by_video),min(sample_size,len(by_video)))
    selected=[rng.choice(by_video[v])['toml'] for v in videos]
    return dict(schema='ba-inventory-v1',seed=seed,sampling='Uniform sample of source videos, then one uniformly selected TOML per video; selected before QC exclusions.',toml_count=len(rows),video_count=len(by_video),flags=dict(Counter(f for r in rows for f in r['flags'])),pilot_tomls=selected,rows=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=ROOT);p.add_argument('--seed',type=int,default=20260929);p.add_argument('--sample-size',type=int,default=6)
    a=p.parse_args();print(json.dumps(inventory(a.root,a.seed,a.sample_size),indent=2,allow_nan=False))
