"""Freeze version-bound BA approvals without choosing scientific outcome variables.

Use a closed registry snapshot and explicit packet locations. Historical approvals
never transfer across lineage; a rejected replacement never falls back to its
parent. The catalog retains approval and movement eligibility separately.
"""
import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

from ba_review_registry import canonical, read_index

VERSION = '1.0.0'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def attach_source_audit(out, audit_path):
    """Add a completed read-only source audit to an existing selection catalog."""
    out, audit_path = Path(out), Path(audit_path)
    audit = json.loads(audit_path.read_text())
    if audit['status'] != 'PASS' or audit['failures']:
        raise ValueError('Cannot attach a failed source audit')
    fingerprints = {r['path']: r['sha256'] for r in audit['results']}
    for path in out.glob('*CELLS.csv'):
        with path.open() as f:
            reader = csv.DictReader(f); fields = list(reader.fieldnames); rows = list(reader)
        if 'source_video_sha256' not in fields:
            fields.append('source_video_sha256')
        for row in rows:
            row['source_video_sha256'] = fingerprints[row['source_video']]
            if row['trajectory_sha256'] != fingerprints[row['tracking_trajectory']]:
                raise ValueError('Selected trajectory differs from audited source')
        with path.open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    if audit_path.resolve() != (out/'FULL_SOURCE_AUDIT.json').resolve():
        shutil.copy2(audit_path, out/'FULL_SOURCE_AUDIT.json')
    receipt_path = out/'SELECTION_RECEIPT.json'
    receipt = json.loads(receipt_path.read_text())
    receipt['source_video_hash_status'] = 'PASS; see FULL_SOURCE_AUDIT.json for historical matches versus newly fingerprinted recordings'
    receipt_path.write_text(json.dumps(receipt, indent=2)+'\n')


def select_versions(runs, lineage):
    """Return terminal versions, refusing ambiguous forks and cycles."""
    keys = {(r['dataset'], r['run_id']) for r in runs}
    children = {}
    parents = {}
    for edge in lineage:
        a = (edge['parent_dataset'], edge['parent_run'])
        b = (edge['child_dataset'], edge['child_run'])
        if a not in keys or b not in keys:
            raise ValueError('Lineage references an unregistered version')
        if a in children or b in parents:
            raise ValueError('Ambiguous version lineage')
        children[a] = b
        parents[b] = a
    for key in keys:
        seen = set()
        while key in children:
            if key in seen:
                raise ValueError('Cyclic version lineage')
            seen.add(key)
            key = children[key]
    return sorted(keys - children.keys())


def eligibility(decision, strict_status):
    approved = decision['status'] == 'usable_skim'
    # Only the explicit, dataset-bound override mechanism can clear a hold.
    override = (decision.get('movement_override') is True
                and decision.get('effective_movement_status') == 'HUMAN_OVERRIDE_USE_STRICT_TRACK'
                and decision.get('review_does_not_clear_analysis_hold') is False)
    ready = approved and not decision.get('rerun_idtracker', False) and (
        strict_status == 'NO_LARGE_JUMP_BLOCK' or override)
    return approved, ready


def build(db_path, packets, out, data_out):
    import numpy as np
    out, data_out = Path(out), Path(data_out)
    if out.exists() or data_out.exists():
        raise ValueError('Use new output directories; never overwrite a frozen selection')
    db = sqlite3.connect(f'file:{Path(db_path).resolve()}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    runs = [dict(r) for r in db.execute('SELECT * FROM runs')]
    lineage = [dict(r) for r in db.execute('SELECT * FROM lineage')]
    selected = select_versions(runs, lineage)
    locations = {}
    for packet in map(Path, packets):
        index = read_index(packet)
        hashes = [(r['id'], sha(packet/'runs'/r['id']/'MANIFEST.json')) for r in index['runs']]
        if hashlib.sha256(json.dumps(hashes).encode()).hexdigest() != index['hash']:
            raise ValueError('Packet fingerprint mismatch')
        if index['hash'] in locations:
            raise ValueError('Duplicate packet version')
        locations[index['hash']] = packet
    records = []
    manifests = {}
    identities = set()
    for dataset, rid in selected:
        opinions = list(db.execute('SELECT * FROM current_reviews WHERE dataset=? AND run_id=?', (dataset, rid)))
        if len(opinions) != 1:
            raise ValueError(f'{rid}: unresolved or absent current review')
        review = dict(opinions[0]); decision = json.loads(review['decision_json'])
        run = next(r for r in runs if (r['dataset'], r['run_id']) == (dataset, rid))
        packet = locations[dataset]; folder = packet/'runs'/rid
        if sha(folder/'MANIFEST.json') != run['manifest_sha256']:
            raise ValueError('Registry/packet manifest mismatch')
        manifest = json.loads((folder/'MANIFEST.json').read_text())
        if canonical(manifest) != run['manifest_json']:
            raise ValueError('Registry/packet contents mismatch')
        source = manifest['source']
        identity = (source['video'], source['census_id'])
        if identity in identities:
            raise ValueError('Duplicate source cell; reconcile explicitly')
        identities.add(identity)
        # Check every frozen run artifact, including the actual reviewed video.
        for name, expected in manifest['files'].items():
            if sha(folder/name) != expected:
                raise ValueError(f'{rid}: changed artifact {name}')
        strict = json.loads((folder/'STRICT_QC.json').read_text())
        qc = json.loads((folder/'QC.json').read_text())
        approved, ready = eligibility(decision, strict['movement_status'])
        with np.load(folder/'STRICT_ANALYSIS.npz') as a:
            positions = a['analysis']; steps = a['movement_step_px']
            n = source['end'] - source['start'] + 1
            if positions.shape != (n, 2) or steps.shape != (n-1,):
                raise ValueError('Frame/coordinate shape mismatch')
            if int(a['start']) != source['start'] or int(a['end']) != source['end']:
                raise ValueError('Frame origin mismatch')
            if np.any(np.linalg.norm(np.diff(positions, axis=0), axis=1) >= 100):
                raise ValueError('Strict track contains an ungated jump')
            if strict['movement_status'].startswith('BLOCKED') and np.isfinite(steps).any():
                raise ValueError('Blocked automatic movement must remain unknown')
            if np.isfinite(positions[a['protected']]).any():
                raise ValueError('Protected exclusions must remain unknown')
            finite = int(np.isfinite(positions).all(axis=1).sum())
        imports = [r[0] for r in db.execute('SELECT DISTINCT import_sha256 FROM review_imports WHERE review_id=? ORDER BY import_sha256', (review['id'],))]
        rec = dict(run_id=rid, census_id=source['census_id'], source_label=source['label'],
            source_video=source['video'], source_toml=source['source_toml'],
            tracking_trajectory=source['trajectory'], dataset_sha256=dataset,
            manifest_sha256=run['manifest_sha256'], review_id=review['id'],
            review_import_sha256=';'.join(imports), reviewer=review['reviewer'],
            reviewed_at=review['at'], review_scope=review['scope'], review_status=review['status'],
            approved_for_extraction=approved, movement_extraction_eligible=ready,
            movement_status=strict['movement_status'], movement_override=bool(decision.get('movement_override')),
            flags=';'.join(decision['errors']), notes=decision['notes'],
            start_global_frame=source['start'], end_global_frame=source['end'], observations=n,
            coordinate_units='original_image_pixels', frame_numbering='zero_based_global_inclusive',
            strict_finite_positions=finite, strict_unknown_positions=n-finite,
            recovered_positions=qc.get('recovered_frames', qc.get('prior_recovery_frames')),
            interpolated_positions=qc['interpolated_frames'],
            human_excluded_frames=json.dumps(source.get('excluded_frames', [])),
            source_toml_sha256=manifest['input_hashes']['toml'],
            trajectory_sha256=manifest['input_hashes']['trajectory'],
            coordinates_sha256=manifest['files']['COORDINATES.npz'],
            strict_coordinates_sha256=manifest['files']['STRICT_ANALYSIS.npz'],
            reviewed_video_sha256=manifest['files']['video.mp4'],
            packet_location=str(packet.resolve()),
            frozen_data_relative_path=f'runs/{rid}' if approved else '',
            automatic_posture_status='SCREENING_ONLY_NOT_VALIDATED_DURATION')
        records.append(rec)
        manifests[rid] = dict(manifest=manifest, decision=decision, review_id=review['id'],
                             review_import_sha256=imports, original_packet=str(packet.resolve()))
    out.mkdir(parents=True); data_out.mkdir(parents=True)
    for name, subset in [('ALL_SELECTED_CELLS.csv', records),
                         ('APPROVED_CELLS.csv', [r for r in records if r['approved_for_extraction']]),
                         ('MOVEMENT_READY_CELLS.csv', [r for r in records if r['movement_extraction_eligible']]),
                         ('EXCLUDED_CELLS.csv', [r for r in records if not r['approved_for_extraction']])]:
        with (out/name).open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(records[0])); w.writeheader(); w.writerows(subset)
    write = lambda name, data: (out/name).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    write('SELECTED_PROVENANCE.json', dict(schema='ba-science-selection-v1', version=VERSION,
        policy='Terminal explicit lineage version; no approval inheritance or fallback; one current opinion required',
        authorization='VAF 2026-10-14: commit approvals/rejections and prepare approved cells for scientific extraction; variables undecided',
        lineage=lineage, runs=manifests))
    (out/'original_reviews').mkdir()
    for row in db.execute('SELECT sha256,raw FROM imports'):
        raw = row['raw']; assert hashlib.sha256(raw).hexdigest() == row['sha256']
        (out/'original_reviews'/f"{row['sha256']}.json").write_bytes(raw)
    for dataset, packet in locations.items():
        dest = data_out/'frozen_code'/dataset; shutil.copytree(packet/'code', dest)
        shutil.copy2(packet/'CODE_FREEZE.json', dest/'PACKET_CODE_FREEZE.json')
    for rec in records:
        if not rec['approved_for_extraction']:
            continue
        src = locations[rec['dataset_sha256']]/'runs'/rec['run_id']
        dest = data_out/'runs'/rec['run_id']; dest.mkdir(parents=True)
        # Immutable numerical/evidence inputs; videos remain in their hashed packets.
        for p in src.iterdir():
            if p.suffix in ('.npz', '.csv', '.json'):
                shutil.copy2(p, dest/p.name)
    data_hashes = {str(p.relative_to(data_out)): sha(p) for p in sorted(data_out.rglob('*')) if p.is_file()}
    write('FROZEN_DATA_SHA256.json', data_hashes)
    summary = dict(schema='ba-science-selection-receipt-v1', version=VERSION,
        selected_cells=len(records), approved_cells=sum(r['approved_for_extraction'] for r in records),
        excluded_cells=sum(not r['approved_for_extraction'] for r in records),
        movement_ready_cells=sum(r['movement_extraction_eligible'] for r in records),
        approved_movement_hold=[r['run_id'] for r in records if r['approved_for_extraction'] and not r['movement_extraction_eligible']],
        review_scopes=dict(Counter(r['review_scope'] for r in records if r['approved_for_extraction'])),
        unique_source_recordings=len({r['source_video'] for r in records if r['approved_for_extraction']}),
        verified_run_manifests=len(records), frozen_data_files=len(data_hashes),
        registry_snapshot_sha256=sha(db_path), analysis_variables='NOT_YET_DEFINED',
        biological_individual_ids='SOURCE_CELL_LOCATORS_ONLY; animal metadata join remains to be defined',
        source_video_hash_status='SEE_REMOTE_SOURCE_AUDIT', frozen_data_location=str(data_out.resolve()))
    write('SELECTION_RECEIPT.json', summary)
    db.close()
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', required=True); p.add_argument('--packet', action='append', required=True)
    p.add_argument('--out', required=True); p.add_argument('--data-out', required=True)
    p.add_argument('--source-audit', help='Optional completed audit; normally generated after the initial selection')
    a = p.parse_args(); print(json.dumps(build(a.db, a.packet, a.out, a.data_out), indent=2))
    if a.source_audit:
        attach_source_audit(a.out, a.source_audit)


if __name__ == '__main__':
    main()
