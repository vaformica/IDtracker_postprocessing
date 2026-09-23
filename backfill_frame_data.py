"""Export frame_data.csv from an older canonical bundle, unchanged."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

from frame_data import write_frame_data


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def backfill(source, output):
    source, output = Path(source), Path(output)
    manifest = json.loads((source/'manifest.json').read_text())
    state_file = source/'canonical_states.npz'
    original_hash = manifest.get('output_sha256', {}).get(state_file.name)
    if not original_hash or sha256(state_file) != original_hash:
        raise ValueError('Source canonical_states.npz hash does not match its manifest')
    with np.load(state_file, allow_pickle=False) as state:
        raw, xy = state['raw'], state['xy']
        group = {key: state[key] for key in ('xy','source','inferred','group_ids','ambiguous')}
    if raw.shape != xy.shape or raw.ndim != 3 or raw.shape[1] < 2 or raw.shape[2] != 2:
        raise ValueError('Expected matching multi-animal raw and canonical arrays')
    animals = raw.shape[1]
    ids, inferred = group['group_ids'], group['inferred']
    limit = manifest['settings']['social_distance_threshold_px']
    masks, group_masks = {}, {}
    for a,b in itertools.combinations(range(animals),2):
        assigned = (group['source'][:,a]=='ASSIGNED') & (group['source'][:,b]=='ASSIGNED')
        masks[a,b] = assigned & (np.linalg.norm(xy[:,a]-xy[:,b],axis=1)<=limit)
        group_masks[a,b] = ((ids[:,a]>=0) & (ids[:,a]==ids[:,b])
            & np.isfinite(xy[:,a]).all(axis=1) & np.isfinite(xy[:,b]).all(axis=1)
            & (inferred[:,a] | inferred[:,b]))
    group['masks'] = group_masks
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    frame_csv = output/'frame_data.csv'
    write_frame_data(dict(xy=raw, group=group, masks=masks, metadata=manifest), frame_csv)
    (output/'manifest.json').write_text(json.dumps(dict(
        qc_status=manifest.get('qc_status','UNREVIEWED'), settings=manifest['settings'],
        source_bundle=str(source.resolve()), source_canonical_sha256=original_hash,
        output_sha256={'frame_data.csv':sha256(frame_csv)},
        note='Frame data reconstructed from the source canonical arrays and saved ROI/settings; source bundle unchanged.'),
        indent=2)+'\n')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Older canonical analysis bundle')
    parser.add_argument('output', type=Path, help='New output folder')
    args = parser.parse_args()
    print(backfill(args.source,args.output))


if __name__ == '__main__':
    main()
