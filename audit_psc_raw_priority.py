#!/usr/bin/env python3
"""Replay preserved dyadic/six-beetle inputs into a NEW audit root; no video rewrite."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import numpy as np
from persistent_groups import MODEL_VERSION, persistent_groups


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, required=True)
    p.add_argument('--dyadic-root', type=Path, required=True)
    p.add_argument('--six-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    tasks = []
    for r in json.loads(args.plan.read_text())['tasks']:
        tasks.append(dict(stem=r['stem'], kind='dyadic', trajectory=r['trajectory'],
                          blob=r['blob_evidence'], start=r['first_global_frame'],
                          end=r['last_global_frame_inclusive'],
                          old=args.dyadic_root/'runs'/r['stem']/'analysis'))
    for manifest in sorted((args.six_root/'runs').glob('*/analysis/manifest.json')):
        m = json.loads(manifest.read_text())
        tasks.append(dict(stem=manifest.parent.parent.name, kind='six_beetle',
                          trajectory=m['trajectory_file'], blob=m['blob_evidence_file'],
                          start=m['settings']['start'], end=m['settings']['start']+m['settings']['window'],
                          old=manifest.parent))
    if len(tasks) != 51:
        raise ValueError(f'Expected 25 dyadic and 26 six-beetle runs, got {len(tasks)}')
    records = []
    for r in tasks:
        oldm = json.loads((r['old']/'manifest.json').read_text())
        blob_hash = sha(r['blob'])
        if blob_hash != oldm['blob_evidence_sha256']:
            raise ValueError(f'Blob hash changed: {r["stem"]}')
        loaded = np.load(r['trajectory'], allow_pickle=True)
        data = loaded.item()['trajectories'] if loaded.shape == () else loaded
        raw = np.asarray(data[:r['end']+1], float)
        blobs = json.loads(Path(r['blob']).read_text())['frames']
        result = persistent_groups(raw, blobs)
        sl = slice(r['start'], r['end']+1)
        selected = raw[sl]
        known = np.isfinite(selected).all(axis=2)
        xy, source, inferred = (result[k][sl] for k in ('xy', 'source', 'inferred'))
        with np.load(r['old']/'canonical_states.npz', allow_pickle=False) as old:
            if not np.array_equal(selected, old['raw'], equal_nan=True):
                raise ValueError(f'Raw trajectory no longer matches frozen run: {r["stem"]}')
            old_xy, old_source = old['xy'], old['source']
        changed_old = known & (~np.isfinite(old_xy).all(axis=2) |
                              np.any(old_xy != selected, axis=2) | (old_source != 'ASSIGNED'))
        changed_new = known & (~np.isfinite(xy).all(axis=2) |
                              np.any(xy != selected, axis=2) | (source != 'ASSIGNED') | inferred)
        if changed_new.any():
            raise ValueError(f'Available raw ID changed: {r["stem"]}')
        invalid_psc = sum(int((mask[sl] & known[:, a] & known[:, b]).sum())
                          for (a,b), mask in result['masks'].items())
        if invalid_psc:
            raise ValueError('PSC assigned to two available IDs')
        peak_inferred = 0.
        for a in range(raw.shape[1]):
            located = np.flatnonzero(np.isfinite(result['xy'][:, a]).all(axis=1))
            rates = np.linalg.norm(np.diff(result['xy'][located, a], axis=0), axis=1)/np.diff(located)
            rates = rates[result['inferred'][located[1:], a]]
            if rates.size:
                peak_inferred = max(peak_inferred, float(rates.max()))
        if peak_inferred > 100+1e-6:
            raise ValueError(f'Impossible inferred movement: {r["stem"]}')
        output = args.output/(r['stem']+'.npz')
        np.savez_compressed(output, raw=selected, xy=xy, source=source, inferred=inferred,
                            ambiguous=result['ambiguous'][sl], group_ids=result['group_ids'][sl])
        record = dict(stem=r['stem'], kind=r['kind'], first_global_frame=r['start'],
                      last_global_frame_inclusive=r['end'], frames=len(selected), animals=raw.shape[1],
                      available_raw_animal_frames=int(known.sum()),
                      old_available_raw_assignments_changed=int(changed_old.sum()),
                      new_available_raw_assignments_changed=int(changed_new.sum()),
                      new_psc_pairs_with_two_raw_ids=invalid_psc,
                      new_missing_id_pscp_frames=int((source=='PSCP_BLOB').sum()),
                      new_missing_id_continuity_frames=int((source=='BLOB_CONTINUITY').sum()),
                      peak_inferred_speed_px_per_elapsed_frame=peak_inferred,
                      trajectory=str(r['trajectory']), trajectory_sha256=sha(r['trajectory']),
                      blob_evidence=str(r['blob']), blob_evidence_sha256=blob_hash,
                      previous_manifest=str(r['old']/'manifest.json'), previous_manifest_sha256=sha(r['old']/'manifest.json'),
                      output_sha256=sha(output))
        records.append(record)
        (args.output/'progress.json').write_text(json.dumps(records, indent=2)+'\n')
        print(f'{len(records)}/{len(tasks)} {r["stem"]}: {int(changed_old.sum())} old raw-assignment changes -> 0', flush=True)
    receipt = dict(status='COMPLETED_UNREVIEWED', purpose='Regression replay only; existing videos and reviews unchanged',
                   created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), model_version=MODEL_VERSION,
                   code_sha256={p.name:sha(p) for p in [Path(__file__), Path(__file__).with_name('persistent_groups.py')]},
                   plan_sha256=sha(args.plan), runs=records)
    (args.output/'AUDIT_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')


if __name__ == '__main__':
    main()
