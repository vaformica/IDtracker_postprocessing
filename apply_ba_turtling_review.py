#!/usr/bin/env python3
"""Validate a BA viewer decision export and write a separate reviewed time summary."""
import argparse,json,hashlib,csv
from pathlib import Path
from ba_turtling import apply_posture_review

def apply(bundle, decisions, output):
    manifest=json.loads((bundle/'manifest.json').read_text())
    review=json.loads(decisions.read_text())
    if review.get('schema')!='ba-review-notes-v2':raise ValueError('Expected BA v2 decisions')
    if review.get('source_sha256')!=manifest['source_sha256']:raise ValueError('Source hashes do not match this bundle')
    expected=Path(manifest['source_paths']['toml']).stem
    if review.get('label')!=expected:raise ValueError('Source label mismatch')
    with (bundle/'frame_data.csv').open() as stream: frames=list(csv.DictReader(stream))
    start=manifest['start_global_frame']; end=manifest['end_global_frame_inclusive']
    if [int(f['global_frame']) for f in frames]!=list(range(start,end+1)):
        raise ValueError('Frame data does not match the manifest window')
    result=apply_posture_review([int(f['turtling_candidate']) for f in frames],
        [int(f['location_known']) for f in frames],start,manifest['fps'],review['notes'])
    result.update(schema='ba-reviewed-episodes-v1',source_sha256=manifest['source_sha256'],
                  review_sha256=hashlib.sha256(decisions.read_bytes()).hexdigest(),notes=review['notes'])
    with output.open('x') as stream:json.dump(result,stream,indent=2)
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','decisions','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(json.dumps(apply(a.bundle,a.decisions,a.output),indent=2))
