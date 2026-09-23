#!/usr/bin/env python3
"""Replay a portable human review log into new, auditable CSV and HTML outputs.

The automatic bundle and IDtracker files are read-only. A reviewed result is a
derived layer, not a replacement for the original tracking analysis.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np

from build_canonical_review import build
from frame_data import aggregate, write_frame_data, _write_rows

SCHEMA = 'beetle-review-v1'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(bundle, review):
    bundle = Path(bundle)
    manifest_path = bundle / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    state_path = bundle / 'canonical_states.npz'
    expected = manifest.get('output_sha256', {}).get(state_path.name)
    if not expected or digest(state_path) != expected:
        raise ValueError('Canonical state hash does not match the source manifest')
    data = np.load(state_path)
    raw = data['raw']
    start = int(manifest['settings']['start'])
    end = start + len(raw) - 1
    if (review.get('schema') != SCHEMA or
            review.get('analysis_manifest_sha256') != digest(manifest_path) or
            review.get('canonical_sha256') != expected or
            review.get('frame_start') != start or
            review.get('frame_end_inclusive') != end or
            not isinstance(review.get('decisions'), list)):
        raise ValueError('Review log does not match this exact source bundle')
    animals = raw.shape[1]
    fungi = len(manifest['rois']) - 1
    allowed = dict(pscp={'yes','no','unresolved','automatic'},
                   proximity={'yes','no','automatic'},
                   location={'partner','missing','raw','automatic'},
                   fungus={'automatic'} | {str(i) for i in range(fungi+1)})
    for index, decision in enumerate(review['decisions']):
        try:
            kind, value = decision['kind'], decision['value']
            a, lo, hi = decision['animal_id'], decision['start_frame'], decision['end_frame_inclusive']
            if (kind not in allowed or value not in allowed[kind] or
                    not isinstance(a, int) or not 0 <= a < animals or
                    not isinstance(lo, int) or not isinstance(hi, int) or
                    not start <= lo <= hi <= end or
                    not str(decision['reviewer']).strip() or not str(decision['reason']).strip() or
                    not str(decision['created_utc']).strip()):
                raise ValueError('invalid fields')
            if kind != 'fungus':
                b = decision['partner_id']
                if not isinstance(b, int) or not 0 <= b < animals or b == a:
                    raise ValueError('invalid partner')
            if kind == 'location' and value == 'raw' and not np.isfinite(raw[lo-start:hi-start+1,a]).all():
                raise ValueError('raw coordinate absent in selected range')
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'Invalid decision {index}: {exc}') from exc
    return manifest, data


def _replay_into(bundle, review, output, source_review=None):
    """Build the reviewed layer inside a new staging directory."""
    bundle, output = Path(bundle), Path(output)
    manifest, data = validate(bundle, review)
    review_meta = None
    if source_review:
        review_meta=json.loads((Path(source_review)/'source_manifest.json').read_text())
        if review_meta['analysis_manifest_sha256'] != digest(bundle/'manifest.json'):
            raise ValueError('Review video is not linked to the source bundle')
        if digest(Path(source_review)/review_meta['video']) != review_meta['copied_video_sha256']:
            raise ValueError('Review video hash does not match its source manifest')
    start = int(manifest['settings']['start'])
    raw = data['raw']
    xy = data['xy'].copy()
    source = data['source'].copy().astype('<U32')
    inferred = data['inferred'].copy()
    group_ids = data['group_ids'].copy()
    ambiguous = data['ambiguous'].copy()
    frames, animals, _ = xy.shape
    pairs = list(itertools.combinations(range(animals), 2))
    pair_states = np.zeros((len(pairs), frames), dtype=np.uint8)
    threshold = float(manifest['settings'].get('social_distance_threshold_px', 60))
    for k, (a, b) in enumerate(pairs):
        shared = (group_ids[:,a] >= 0) & (group_ids[:,a] == group_ids[:,b])
        known = np.isfinite(xy[:,[a,b]]).all(axis=(1,2))
        pscp = shared & known & (inferred[:,a] | inferred[:,b])
        unresolved = shared & ~known
        assigned = (source[:,a] == 'ASSIGNED') & (source[:,b] == 'ASSIGNED')
        near = assigned & (np.linalg.norm(xy[:,a]-xy[:,b],axis=1) <= threshold)
        pair_states[k] = np.where(pscp, 2, np.where(unresolved, 4, np.where(near, 1, 0)))
    baseline = dict(xy=xy.copy(), source=source.copy(), inferred=inferred.copy(),
                    group_ids=group_ids.copy(), pair_states=pair_states.copy())
    fungus_override = np.full((frames,animals), -1, int)
    human = np.zeros((frames,animals), bool)
    audit = []
    for decision in review['decisions']:
        a = decision['animal_id'];b = decision.get('partner_id')
        k = pairs.index(tuple(sorted((a,b)))) if b is not None else None
        lo = decision['start_frame']-start;hi=decision['end_frame_inclusive']-start+1
        kind,value = decision['kind'],decision['value']
        before = dict(location_source_counts={s:int(n) for s,n in zip(*np.unique(source[lo:hi,a],return_counts=True))},
                      pair_state_counts=({str(s):int(n) for s,n in zip(*np.unique(pair_states[k,lo:hi],return_counts=True))} if k is not None else {}))
        for t in range(lo,hi):
            if kind == 'location' or kind == 'pscp' and value in {'yes','unresolved'}:
                mode = ('missing' if value == 'unresolved' else 'partner') if kind == 'pscp' else value
                if mode == 'automatic':
                    xy[t,a] = baseline['xy'][t,a];source[t,a] = baseline['source'][t,a]
                    inferred[t,a] = baseline['inferred'][t,a];group_ids[t,a] = baseline['group_ids'][t,a]
                elif mode == 'raw':
                    xy[t,a] = raw[t,a];source[t,a] = 'HUMAN_RAW';inferred[t,a] = False
                    pair_states[k,t] = baseline['pair_states'][k,t]
                elif mode == 'missing':
                    xy[t,a] = np.nan;source[t,a] = 'HUMAN_UNRESOLVED' if kind == 'pscp' else 'HUMAN_MISSING'
                    inferred[t,a] = False
                    pair_states[k,t] = 4 if kind == 'pscp' or baseline['pair_states'][k,t] in (2,4) else 0
                else:
                    xy[t,a] = xy[t,b] if np.isfinite(xy[t,b]).all() else np.nan
                    source[t,a] = 'HUMAN_PSCP' if np.isfinite(xy[t,a]).all() else 'HUMAN_UNRESOLVED'
                    inferred[t,a] = np.isfinite(xy[t,a]).all()
                    group_ids[t,a] = group_ids[t,b]
                    pair_states[k,t] = 3 if inferred[t,a] else 4
                human[t,a] = True
            if kind == 'fungus':
                fungus_override[t,a] = -1 if value == 'automatic' else int(value)
                human[t,a] = True
            if kind == 'proximity':pair_states[k,t] = baseline['pair_states'][k,t] if value == 'automatic' else 1 if value == 'yes' else 0
            if kind == 'pscp':pair_states[k,t] = baseline['pair_states'][k,t] if value == 'automatic' else 0 if value == 'no' else 4 if value == 'unresolved' else 3 if np.isfinite(xy[t,[a,b]]).all() else 4
            if kind in {'proximity','pscp'}:human[t,a]=True;human[t,b]=True
        audit.append(dict(**decision,before=before))
    for t,a in np.argwhere(fungus_override >= 0):
        if not np.isfinite(xy[t,a]).all():
            raise ValueError(f'Fungus correction needs a known coordinate: frame {start+t}, beetle {a}')
    for k,(a,b) in enumerate(pairs):
        invalid=(pair_states[k] == 1) & ~np.isfinite(xy[:,[a,b]]).all(axis=(1,2))
        if invalid.any():
            raise ValueError(f'Visible proximity requires two located beetles: frame {start+int(np.flatnonzero(invalid)[0])}, pair {a}-{b}')
    masks = {pair:pair_states[k] == 1 for k,pair in enumerate(pairs)}
    group_masks = {pair:np.isin(pair_states[k],(2,3)) for k,pair in enumerate(pairs)}
    unresolved_masks = {pair:pair_states[k] == 4 for k,pair in enumerate(pairs)}
    result = dict(xy=raw,group=dict(xy=xy,source=source,inferred=inferred,group_ids=group_ids,human=human,
                  ambiguous=ambiguous,masks=group_masks,unresolved_masks=unresolved_masks),
                  masks=masks,metadata=dict(settings=dict(start=start),rois=manifest['rois'],
                  reconstruction=dict(max_speed_px_per_frame=float(manifest.get('reconstruction',{}).get('max_speed_px_per_frame',100)))))
    frame_file = output/'reviewed_frame_data.csv'
    write_frame_data(result, frame_file)
    with frame_file.open(newline='') as stream:rows=list(csv.DictReader(stream));columns=list(rows[0])
    fungi=len(manifest['rois'])-1
    for row in rows:
        t=int(row['global_frame'])-start;a=int(row['animal_id']);f=fungus_override[t,a]
        if f>=0:
            row['any_fungus']=str(int(f>0))
            for i in range(1,fungi+1):row[f'fungus_{i}']=str(int(i==f))
        if t>0 and (f>=0 or fungus_override[t-1,a]>=0):
            previous=rows[(t-1)*animals+a]
            for i in range(1,fungi+1):
                row[f'step_midpoint_fungus_{i}']=str(int(
                    row[f'step_distance_px'] != '' and
                    row[f'fungus_{i}']=='1' and previous[f'fungus_{i}']=='1'))
    with frame_file.open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    beetles, pair_rows = aggregate(frame_file,start,start+frames-1)
    _write_rows(output/'reviewed_beetle_summary.csv',beetles)
    _write_rows(output/'reviewed_pair_summary.csv',pair_rows)
    np.savez_compressed(output/'reviewed_states.npz',raw=raw,xy=xy,source=source,inferred=inferred,
                        group_ids=group_ids,pair_states=pair_states,human=human,fungus_override=fungus_override)
    (output/'review_decisions.json').write_text(json.dumps(review,indent=2)+'\n')
    (output/'audit_log.json').write_text(json.dumps(audit,indent=2)+'\n')
    if review_meta:
        build(bundle,Path(source_review)/review_meta['video'],output/'review',review_meta['crop'],
              review_meta['fps'],label=review_meta['label']+' · human review',
              initial_decisions=review['decisions'])
    files={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()}
    (output/'review_manifest.json').write_text(json.dumps(dict(schema='beetle-reviewed-layer-v1',
        source_bundle=str(bundle.resolve()),source_manifest_sha256=digest(bundle/'manifest.json'),
        decision_log_sha256=digest(output/'review_decisions.json'),decision_count=len(audit),
        status='HUMAN_REVIEWED_UNVERIFIED',outputs_sha256=files),indent=2)+'\n')
    return output


def replay(bundle, review, output, source_review=None):
    """Publish a reviewed layer atomically without altering source artifacts."""
    destination=Path(output)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.beetle-review-',dir=destination.parent))
    try:
        _replay_into(bundle,review,staging,source_review)
        if destination.exists():
            raise FileExistsError(destination)
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path)
    parser.add_argument('review_log',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--source-review',type=Path,help='Original HTML/video folder; also make a portable reviewed viewer')
    args=parser.parse_args()
    review=json.loads(args.review_log.read_text())
    print(replay(args.bundle,review,args.output,args.source_review))


if __name__=='__main__':main()
